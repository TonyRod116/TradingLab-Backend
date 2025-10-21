"""
Pro Engine Views - Django REST API for advanced Pro engine features
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Strategy
from .tradelab_engine_pro import (
    ProBacktester, PortfolioBacktester, RiskConfig, StopTarget, TrailingStop,
    load_parquet, ProIndicators
)
from .serializers import StrategySerializer


class ProBacktestView(APIView):
    """Pro engine single symbol backtest endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Run Pro engine backtest with multi-position and trailing stop support
        
        Expected payload:
        {
            "symbol": "ES",
            "timeframe": "5m",
            "base_path": "/data/ohlcv",
            "strategy": {
                "risk": {
                    "initial_capital": 100000,
                    "position_size": 1,
                    "max_positions": 3,
                    "commission_round_turn": 4.0,
                    "slippage_ticks": 0.5,
                    "tick_value": 12.5,
                    "tick_size": 0.25
                },
                "stops_targets": {
                    "stop_loss": {"type": "ATR", "value": 2.0},
                    "take_profit": {"type": "Points", "value": 4.0}
                },
                "trailing_stop": {
                    "active": true,
                    "type": "ATR",
                    "value": 1.0,
                    "use_high_low": true
                },
                "entries": [...],
                "exits": [...]
            }
        }
        """
        try:
            data = request.data
            
            # Validate required fields
            symbol = data.get('symbol')
            timeframe = data.get('timeframe')
            base_path = data.get('base_path')
            strategy_config = data.get('strategy')
            
            if not all([symbol, timeframe, base_path, strategy_config]):
                return Response(
                    {"error": "symbol, timeframe, base_path, and strategy are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Load market data
            df = load_parquet(symbol, timeframe, base_path)
            
            # Extract configuration
            risk_config = RiskConfig(**strategy_config["risk"])
            stops = StopTarget(**strategy_config["stops_targets"]["stop_loss"]) if strategy_config["stops_targets"].get("stop_loss") else None
            targets = StopTarget(**strategy_config["stops_targets"]["take_profit"]) if strategy_config["stops_targets"].get("take_profit") else None
            trailing = TrailingStop(**strategy_config.get("trailing_stop", {})) if strategy_config.get("trailing_stop", {}).get("active", False) else None
            
            # Run Pro backtest
            bt = ProBacktester(df, risk_config, stops, targets, trailing)
            result = bt.run(strategy_config["entries"], strategy_config["exits"])
            
            return Response({
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "trades": result["trades"],
                "equity_curve": result["equity_curve"],
                "metrics": result["metrics"],
                "total_trades": len(result["trades"]),
                "max_positions_used": risk_config.max_positions
            })
            
        except Exception as e:
            return Response(
                {"error": f"Pro backtest failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PortfolioBacktestView(APIView):
    """Pro engine portfolio backtest endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Run Pro engine portfolio backtest across multiple symbols
        
        Expected payload:
        {
            "base_path": "/data/ohlcv",
            "metas": [
                {"symbol": "ES", "timeframe": "5m"},
                {"symbol": "NQ", "timeframe": "5m"},
                {"symbol": "CL", "timeframe": "15m"}
            ],
            "strategy": { ... strategy configuration ... },
            "weights": [0.5, 0.3, 0.2]  // optional, defaults to equal weights
        }
        """
        try:
            data = request.data
            
            # Validate required fields
            base_path = data.get('base_path')
            metas = data.get('metas')
            strategy_config = data.get('strategy')
            weights = data.get('weights')
            
            if not all([base_path, metas, strategy_config]):
                return Response(
                    {"error": "base_path, metas, and strategy are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not isinstance(metas, list) or len(metas) == 0:
                return Response(
                    {"error": "metas must be a non-empty list"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate metas format
            for meta in metas:
                if not all(key in meta for key in ["symbol", "timeframe"]):
                    return Response(
                        {"error": "Each meta must have 'symbol' and 'timeframe'"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Run portfolio backtest
            portfolio_bt = PortfolioBacktester(base_path)
            result = portfolio_bt.run_portfolio_backtest(metas, strategy_config, weights)
            
            return Response({
                "success": True,
                "portfolio_metrics": result["portfolio_metrics"],
                "legs": result["legs"],
                "portfolio_equity_curve": result["portfolio_equity_curve"],
                "number_of_symbols": len(metas),
                "weights": weights or [1.0 / len(metas)] * len(metas)
            })
            
        except Exception as e:
            return Response(
                {"error": f"Portfolio backtest failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProIndicatorsView(APIView):
    """Get Pro engine indicators endpoint"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of all Pro engine indicators with their parameters"""
        try:
            indicators = {
                "SMA": {"params": ["length"], "defaults": {"length": 20}},
                "EMA": {"params": ["length"], "defaults": {"length": 20}},
                "RSI": {"params": ["length"], "defaults": {"length": 14}},
                "ATR": {"params": ["length"], "defaults": {"length": 14}},
                "BOLLINGER_UPPER": {"params": ["length", "mult"], "defaults": {"length": 20, "mult": 2.0}},
                "BOLLINGER_MIDDLE": {"params": ["length", "mult"], "defaults": {"length": 20, "mult": 2.0}},
                "BOLLINGER_LOWER": {"params": ["length", "mult"], "defaults": {"length": 20, "mult": 2.0}},
                "VWAP": {"params": [], "defaults": {}},
                "CCI": {"params": ["length", "c"], "defaults": {"length": 20, "c": 0.015}},
                "STOCH_K": {"params": ["k_len", "d_len"], "defaults": {"k_len": 14, "d_len": 3}},
                "STOCH_D": {"params": ["k_len", "d_len"], "defaults": {"k_len": 14, "d_len": 3}},
                "OBV": {"params": [], "defaults": {}},
                "CLOSE": {"params": [], "defaults": {}},
                "OPEN": {"params": [], "defaults": {}},
                "HIGH": {"params": [], "defaults": {}},
                "LOW": {"params": [], "defaults": {}},
                "VOLUME": {"params": [], "defaults": {}}
            }
            
            return Response({
                "success": True,
                "indicators": indicators,
                "total_count": len(indicators),
                "pro_features": {
                    "multi_position": True,
                    "trailing_stop": True,
                    "portfolio_backtest": True,
                    "advanced_indicators": True
                }
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to get Pro indicators: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProEngineStatusView(APIView):
    """Get Pro engine status and capabilities"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get Pro engine status and capabilities"""
        try:
            return Response({
                "success": True,
                "status": "active",
                "engine_version": "Pro",
                "capabilities": {
                    "multi_position_support": True,
                    "trailing_stop": True,
                    "portfolio_backtesting": True,
                    "advanced_indicators": True,
                    "cci_indicator": True,
                    "stochastic_oscillator": True,
                    "obv_indicator": True
                },
                "supported_features": {
                    "max_positions": "Up to configurable limit per strategy",
                    "trailing_stop_types": ["Percentage", "Points", "Ticks", "ATR"],
                    "trailing_anchors": ["high/low", "close"],
                    "portfolio_weights": "Custom or equal weights",
                    "multi_timeframe": "Different timeframes per symbol"
                },
                "example_configs": {
                    "trailing_stop": {
                        "active": True,
                        "type": "ATR",
                        "value": 1.5,
                        "use_high_low": True
                    },
                    "multi_position": {
                        "max_positions": 3,
                        "position_size": 1,
                        "accumulation": "Same side only"
                    },
                    "portfolio": {
                        "symbols": ["ES", "NQ", "CL"],
                        "timeframes": ["5m", "5m", "15m"],
                        "weights": [0.4, 0.4, 0.2]
                    }
                }
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to get Pro engine status: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProStrategyExamplesView(APIView):
    """Get Pro engine strategy examples"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get example strategies for Pro engine"""
        try:
            examples = {
                "trend_following": {
                    "name": "EMA Trend Following with Trailing Stop",
                    "description": "Long when EMA(12) > EMA(26) and RSI < 30, with ATR trailing stop",
                    "config": {
                        "risk": {
                            "initial_capital": 100000,
                            "position_size": 1,
                            "max_positions": 2,
                            "commission_round_turn": 4.0,
                            "slippage_ticks": 0.5,
                            "tick_value": 12.5,
                            "tick_size": 0.25
                        },
                        "stops_targets": {
                            "stop_loss": {"type": "ATR", "value": 2.0},
                            "take_profit": {"type": "Points", "value": 6.0}
                        },
                        "trailing_stop": {
                            "active": True,
                            "type": "ATR",
                            "value": 1.0,
                            "use_high_low": True
                        },
                        "entries": [{
                            "side": "LONG",
                            "logic": {
                                "op": "AND",
                                "clauses": [
                                    {
                                        "left": {"type": "indicator", "id": "EMA", "params": {"length": 12}},
                                        "cmp": ">",
                                        "right": {"type": "indicator", "id": "EMA", "params": {"length": 26}}
                                    },
                                    {
                                        "left": {"type": "indicator", "id": "RSI", "params": {"length": 14}},
                                        "cmp": "<=",
                                        "right": {"type": "value", "value": 30}
                                    }
                                ]
                            }
                        }],
                        "exits": [{
                            "side": "LONG",
                            "logic": {
                                "left": {"type": "indicator", "id": "RSI", "params": {"length": 14}},
                                "cmp": ">=",
                                "right": {"type": "value", "value": 70}
                            }
                        }]
                    }
                },
                "mean_reversion": {
                    "name": "Bollinger Mean Reversion with Stochastic Filter",
                    "description": "Long when price touches lower Bollinger band and Stochastic %D < 20",
                    "config": {
                        "risk": {
                            "initial_capital": 100000,
                            "position_size": 1,
                            "max_positions": 1,
                            "commission_round_turn": 4.0,
                            "slippage_ticks": 0.5,
                            "tick_value": 12.5,
                            "tick_size": 0.25
                        },
                        "stops_targets": {
                            "stop_loss": {"type": "Points", "value": 2.0},
                            "take_profit": {"type": "Points", "value": 4.0}
                        },
                        "trailing_stop": {
                            "active": False
                        },
                        "entries": [{
                            "side": "LONG",
                            "logic": {
                                "op": "AND",
                                "clauses": [
                                    {
                                        "left": {"type": "indicator", "id": "CLOSE"},
                                        "cmp": "<=",
                                        "right": {"type": "indicator", "id": "BOLLINGER_LOWER", "params": {"length": 20}}
                                    },
                                    {
                                        "left": {"type": "indicator", "id": "STOCH_D", "params": {"k_len": 14, "d_len": 3}},
                                        "cmp": "<",
                                        "right": {"type": "value", "value": 20}
                                    }
                                ]
                            }
                        }],
                        "exits": [{
                            "side": "LONG",
                            "logic": {
                                "left": {"type": "indicator", "id": "CLOSE"},
                                "cmp": ">=",
                                "right": {"type": "indicator", "id": "BOLLINGER_MIDDLE", "params": {"length": 20}}
                            }
                        }]
                    }
                },
                "cci_reversal": {
                    "name": "CCI Reversal Strategy",
                    "description": "Short when CCI > 100, close when CCI < 0, with trailing stop",
                    "config": {
                        "risk": {
                            "initial_capital": 100000,
                            "position_size": 1,
                            "max_positions": 1,
                            "commission_round_turn": 4.0,
                            "slippage_ticks": 0.5,
                            "tick_value": 12.5,
                            "tick_size": 0.25
                        },
                        "stops_targets": {
                            "stop_loss": {"type": "Points", "value": 3.0},
                            "take_profit": {"type": "Ticks", "value": 8.0}
                        },
                        "trailing_stop": {
                            "active": True,
                            "type": "Percentage",
                            "value": 1.0,
                            "use_high_low": False
                        },
                        "entries": [{
                            "side": "SHORT",
                            "logic": {
                                "left": {"type": "indicator", "id": "CCI", "params": {"length": 20, "c": 0.015}},
                                "cmp": ">",
                                "right": {"type": "value", "value": 100}
                            }
                        }],
                        "exits": [{
                            "side": "SHORT",
                            "logic": {
                                "left": {"type": "indicator", "id": "CCI", "params": {"length": 20, "c": 0.015}},
                                "cmp": "<",
                                "right": {"type": "value", "value": 0}
                            }
                        }]
                    }
                }
            }
            
            return Response({
                "success": True,
                "examples": examples,
                "total_examples": len(examples)
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to get Pro strategy examples: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
