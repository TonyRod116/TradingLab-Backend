import pytest
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

from strategies.services.nl_to_dsl import NLToDSLService
from strategies.services.dsl_to_lean import DSLToLeanService
from strategies.schemas import TradingStrategyDSL


class TestNLToDSLService(TestCase):
    """Test the natural language to DSL conversion service"""
    
    def setUp(self):
        self.service = NLToDSLService()
    
    @patch('strategies.services.nl_to_dsl.OpenAI')
    def test_convert_simple_rsi_strategy(self, mock_openai):
        """Test converting a simple RSI strategy"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "universe": {"type": "single", "symbol": "SPY", "asset_class": "Equity"},
            "timeframe": {"start": "2021-01-01", "end": "2023-01-01", "resolution": "Minute"},
            "entry_rules": [
                {
                    "type": "indicator_condition",
                    "left": {"indicator": "RSI", "period": 14},
                    "operator": "lt",
                    "right": {"value": 30}
                }
            ],
            "exit_rules": [
                {"type": "take_profit", "rr": 2.0},
                {"type": "stop_loss", "atr_mult": 1.5}
            ],
            "positioning": {"side": "long_only", "risk_per_trade_pct": 1.0, "max_concurrent_positions": 1}
        })
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test conversion
        result = self.service.convert_to_dsl("Buy SPY when RSI is below 30")
        
        # Verify result structure
        self.assertIsInstance(result.dsl, TradingStrategyDSL)
        self.assertIsInstance(result.lean_code, str)
        self.assertIsInstance(result.warnings, list)
        
        # Verify DSL content
        self.assertEqual(result.dsl.universe.symbol, "SPY")
        self.assertEqual(result.dsl.universe.asset_class, "Equity")
        self.assertEqual(len(result.dsl.entry_rules), 1)
        self.assertEqual(len(result.dsl.exit_rules), 2)
    
    @patch('strategies.services.nl_to_dsl.OpenAI')
    def test_convert_vwap_absorption_strategy(self, mock_openai):
        """Test converting the VWAP absorption strategy from the examples"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "universe": {"type": "single", "symbol": "SPY", "asset_class": "Equity"},
            "timeframe": {"start": "2022-01-01", "end": "2022-12-31", "resolution": "Minute"},
            "entry_rules": [
                {
                    "type": "indicator_condition",
                    "left": {"indicator": "VWAP", "offset_std": -1.5},
                    "operator": "cross_below_or_equal",
                    "right": {"indicator": {"indicator": "VWAP", "std_mult": 1.5}}
                },
                {
                    "type": "orderflow_condition",
                    "name": "seller_absorption",
                    "lookback_bars": 3,
                    "threshold": 0.7,
                    "approximation": "use_negative_delta_volume_absorption"
                }
            ],
            "exit_rules": [
                {"type": "take_profit", "rr": 2.0},
                {"type": "stop_loss", "atr_mult": 1.5}
            ],
            "positioning": {"side": "long_only", "risk_per_trade_pct": 1.0, "max_concurrent_positions": 1}
        })
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test conversion
        result = self.service.convert_to_dsl(
            "comprar SP500 cuando vwap esta en -1.5 standard deviation y hay absorción de vendedores"
        )
        
        # Verify result structure
        self.assertIsInstance(result.dsl, TradingStrategyDSL)
        self.assertEqual(len(result.dsl.entry_rules), 2)
        
        # Verify entry rules
        entry_rules = result.dsl.entry_rules
        self.assertEqual(entry_rules[0].type, "indicator_condition")
        self.assertEqual(entry_rules[0].left.indicator, "VWAP")
        self.assertEqual(entry_rules[0].left.offset_std, -1.5)
        
        self.assertEqual(entry_rules[1].type, "orderflow_condition")
        self.assertEqual(entry_rules[1].name, "seller_absorption")
    
    @patch('strategies.services.nl_to_dsl.OpenAI')
    def test_convert_with_missing_dates(self, mock_openai):
        """Test conversion with missing dates - should apply defaults and warnings"""
        # Mock OpenAI response with missing dates
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "universe": {"type": "single", "symbol": "SPY", "asset_class": "Equity"},
            "timeframe": {"start": "2021-01-01", "end": "2023-01-01", "resolution": "Minute"},
            "entry_rules": [
                {
                    "type": "indicator_condition",
                    "left": {"indicator": "RSI", "period": 14},
                    "operator": "lt",
                    "right": {"value": 30}
                }
            ],
            "exit_rules": [
                {"type": "take_profit", "rr": 2.0},
                {"type": "stop_loss", "atr_mult": 1.5}
            ],
            "positioning": {"side": "long_only", "risk_per_trade_pct": 1.0, "max_concurrent_positions": 1}
        })
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test conversion
        result = self.service.convert_to_dsl("Buy when RSI is oversold")
        
        # Verify defaults were applied
        self.assertEqual(result.dsl.universe.symbol, "SPY")
        self.assertEqual(result.dsl.timeframe.resolution, "Minute")
        self.assertEqual(result.dsl.positioning.side, "long_only")
    
    def test_fallback_code_generation(self):
        """Test fallback code generation when OpenAI fails"""
        with patch('strategies.services.nl_to_dsl.OpenAI') as mock_openai:
            # Mock OpenAI to raise an exception
            mock_openai.side_effect = Exception("API Error")
            
            # Test conversion should still work with fallback
            result = self.service.convert_to_dsl("Buy SPY when RSI is below 30")
            
            # Verify fallback code was generated
            self.assertIsInstance(result.lean_code, str)
            self.assertIn("class TradingStrategy", result.lean_code)
            self.assertIn("RSI", result.lean_code)


class TestDSLToLeanService(TestCase):
    """Test the DSL to LEAN code generation service"""
    
    def setUp(self):
        self.service = DSLToLeanService()
    
    def test_generate_lean_basic_strategy(self):
        """Test generating LEAN code for a basic strategy"""
        dsl = {
            "universe": {"type": "single", "symbol": "SPY", "asset_class": "Equity"},
            "timeframe": {"start": "2021-01-01", "end": "2023-01-01", "resolution": "Minute"},
            "entry_rules": [
                {
                    "type": "indicator_condition",
                    "left": {"indicator": "RSI", "period": 14},
                    "operator": "lt",
                    "right": {"value": 30}
                }
            ],
            "exit_rules": [
                {"type": "take_profit", "rr": 2.0},
                {"type": "stop_loss", "atr_mult": 1.5}
            ],
            "positioning": {"side": "long_only", "risk_per_trade_pct": 1.0, "max_concurrent_positions": 1}
        }
        
        lean_code = self.service.generate_lean(dsl)
        
        # Verify basic structure
        self.assertIn("class TradingStrategy", lean_code)
        self.assertIn("def Initialize", lean_code)
        self.assertIn("def OnData", lean_code)
        self.assertIn("SPY", lean_code)
        self.assertIn("AUTO-GENERATED", lean_code)
    
    def test_generate_lean_with_vwap(self):
        """Test generating LEAN code with VWAP indicators"""
        dsl = {
            "universe": {"type": "single", "symbol": "SPY", "asset_class": "Equity"},
            "timeframe": {"start": "2021-01-01", "end": "2023-01-01", "resolution": "Minute"},
            "entry_rules": [
                {
                    "type": "indicator_condition",
                    "left": {"indicator": "VWAP", "period": 20},
                    "operator": "cross_above",
                    "right": {"indicator": {"indicator": "SMA", "period": 50}}
                }
            ],
            "exit_rules": [
                {"type": "stop_loss", "pct": 2.0}
            ],
            "positioning": {"side": "long_only", "risk_per_trade_pct": 1.0, "max_concurrent_positions": 1}
        }
        
        lean_code = self.service.generate_lean(dsl)
        
        # Verify VWAP is mentioned in the code
        self.assertIn("VWAP", lean_code)
        self.assertIn("SMA", lean_code)


class TestNLToStrategyAPI(APITestCase):
    """Test the API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('strategies.services.nl_to_dsl.OpenAI')
    def test_nl_to_strategy_endpoint(self, mock_openai):
        """Test the /api/nl-to-strategy/ endpoint"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "universe": {"type": "single", "symbol": "SPY", "asset_class": "Equity"},
            "timeframe": {"start": "2021-01-01", "end": "2023-01-01", "resolution": "Minute"},
            "entry_rules": [
                {
                    "type": "indicator_condition",
                    "left": {"indicator": "RSI", "period": 14},
                    "operator": "lt",
                    "right": {"value": 30}
                }
            ],
            "exit_rules": [
                {"type": "take_profit", "rr": 2.0},
                {"type": "stop_loss", "atr_mult": 1.5}
            ],
            "positioning": {"side": "long_only", "risk_per_trade_pct": 1.0, "max_concurrent_positions": 1}
        })
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test API call
        url = reverse('nl-to-strategy')
        data = {
            "text": "Buy SPY when RSI is below 30, sell when RSI is above 70"
        }
        
        response = self.client.post(url, data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('dsl', response.data)
        self.assertIn('lean_code', response.data)
        self.assertIn('warnings', response.data)
        
        # Verify DSL structure
        dsl = response.data['dsl']
        self.assertEqual(dsl['universe']['symbol'], 'SPY')
        self.assertEqual(len(dsl['entry_rules']), 1)
        self.assertEqual(len(dsl['exit_rules']), 2)
    
    def test_nl_to_strategy_validation(self):
        """Test validation of the nl-to-strategy endpoint"""
        url = reverse('nl-to-strategy')
        
        # Test with empty text
        data = {"text": ""}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with text too short
        data = {"text": "short"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_run_backtest_endpoint(self):
        """Test the /api/run-backtest/ endpoint"""
        url = reverse('run-backtest')
        data = {
            "dsl": {
                "universe": {"type": "single", "symbol": "SPY", "asset_class": "Equity"},
                "timeframe": {"start": "2021-01-01", "end": "2023-01-01", "resolution": "Minute"},
                "entry_rules": [
                    {
                        "type": "indicator_condition",
                        "left": {"indicator": "RSI", "period": 14},
                        "operator": "lt",
                        "right": {"value": 30}
                    }
                ],
                "exit_rules": [
                    {"type": "take_profit", "rr": 2.0},
                    {"type": "stop_loss", "atr_mult": 1.5}
                ],
                "positioning": {"side": "long_only", "risk_per_trade_pct": 1.0, "max_concurrent_positions": 1}
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertIn('backtest_id', response.data)
        self.assertIn('results', response.data)
        
        # Verify mock results
        results = response.data['results']
        self.assertIn('total_return', results)
        self.assertIn('sharpe_ratio', results)
        self.assertIn('win_rate', results)
