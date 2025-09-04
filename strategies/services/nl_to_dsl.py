import os
import json
from typing import Dict, Any, List
from openai import OpenAI
from pydantic import ValidationError
import logging

from ..schemas import TradingStrategyDSL, NLToStrategyResponse

logger = logging.getLogger(__name__)


class NLToDSLService:
    """
    Service that converts natural language trading descriptions into structured DSL
    using OpenAI GPT with strict JSON schema validation
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"
        
    def convert_to_dsl(self, text: str, defaults: Dict[str, Any] = None) -> NLToStrategyResponse:
        """
        Convert natural language to DSL with validation and error handling
        """
        if defaults is None:
            defaults = {}
            
        warnings = []
        
        try:
            # Check if OpenAI API key is available
            if not os.getenv('OPENAI_API_KEY'):
                warnings.append("OpenAI API key not configured, using rule-based parsing")
                dsl_json = self._parse_with_rules(text, defaults)
            else:
                # First attempt with GPT
                dsl_json = self._call_openai(text, defaults)
            
            # Validate with Pydantic
            try:
                dsl = TradingStrategyDSL(**dsl_json)
            except ValidationError as e:
                logger.warning(f"Validation failed: {e}")
                warnings.append(f"Validation failed, using fallback: {str(e)}")
                
                # Use fallback parsing
                dsl_json = self._parse_with_rules(text, defaults)
                dsl = TradingStrategyDSL(**dsl_json)
            
            # Generate LEAN code
            from .dsl_to_lean import DSLToLeanService
            lean_service = DSLToLeanService()
            lean_code = lean_service.generate_lean(dsl.dict())
            
            return NLToStrategyResponse(
                dsl=dsl,
                lean_code=lean_code,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Error in convert_to_dsl: {e}")
            raise ValueError(f"Failed to convert natural language to DSL: {str(e)}")
    
    def _call_openai(self, text: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Call OpenAI with the main prompt"""
        
        system_prompt = """You translate trading natural language into a constrained JSON DSL for QuantConnect LEAN strategies. 

OUTPUT ONLY valid JSON per the provided schema. If information is missing, add sensible defaults and list warnings.

SCHEMA:
{
  "universe": {"type": "single|universe", "symbol": "string", "asset_class": "Equity|Forex|Crypto"},
  "timeframe": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "resolution": "Minute|Second|Hour|Daily"},
  "entry_rules": [
    {
      "type": "indicator_condition",
      "left": {"indicator": "VWAP|SMA|EMA|RSI|MACD", "period": int, "offset_std": float},
      "operator": "cross_above|cross_below|cross_below_or_equal|lt|gt",
      "right": {"indicator": {...}, "value": float, "std_mult": float}
    },
    {
      "type": "orderflow_condition", 
      "name": "seller_absorption|buyer_absorption",
      "lookback_bars": int,
      "threshold": float,
      "approximation": "string"
    }
  ],
  "exit_rules": [
    {"type": "take_profit", "rr": float, "target_pct": float},
    {"type": "stop_loss", "atr_mult": float, "pct": float}
  ],
  "positioning": {
    "side": "long_only|short_only|both",
    "risk_per_trade_pct": float,
    "max_concurrent_positions": int
  }
}

EXAMPLES:

User: "comprar SP500 cuando vwap esta en -1.5 standard deviation y hay absorción de vendedores"
{
  "universe": {"type": "single", "symbol": "SPY", "asset_class": "Equity"},
  "timeframe": {"start": "2022-01-01", "end": "2022-12-31", "resolution": "Minute"},
  "entry_rules": [
    {"type": "indicator_condition", "left": {"indicator": "VWAP", "offset_std": -1.5}, "operator": "cross_below_or_equal", "right": {"indicator": {"indicator": "VWAP", "std_mult": 1.5}}},
    {"type": "orderflow_condition", "name": "seller_absorption", "lookback_bars": 3, "threshold": 0.7, "approximation": "use_negative_delta_volume_absorption"}
  ],
  "exit_rules": [{"type": "take_profit", "rr": 2.0}, {"type": "stop_loss", "atr_mult": 1.5}],
  "positioning": {"side": "long_only", "risk_per_trade_pct": 1.0, "max_concurrent_positions": 1}
}

User: "ir corto en SPY si RSI(14) > 70 y cruzo SMA20 por debajo SMA50; stop 1% y tp 2%"
{
  "universe": {"type": "single", "symbol": "SPY", "asset_class": "Equity"},
  "timeframe": {"start": "2021-01-01", "end": "2023-01-01", "resolution": "Minute"},
  "entry_rules": [
    {"type": "indicator_condition", "left": {"indicator": "RSI", "period": 14}, "operator": "gt", "right": {"value": 70}},
    {"type": "indicator_condition", "left": {"indicator": "SMA", "period": 20}, "operator": "cross_below", "right": {"indicator": {"indicator": "SMA", "period": 50}}}
  ],
  "exit_rules": [{"type": "stop_loss", "pct": 1.0}, {"type": "take_profit", "target_pct": 2.0}],
  "positioning": {"side": "short_only", "risk_per_trade_pct": 1.0, "max_concurrent_positions": 1}
}

DEFAULTS TO USE:
- If no symbol mentioned: use "SPY" for Equity
- If no dates: use last 2 years from today
- If no resolution: use "Minute" 
- If no risk: use 1.0%
- If no positioning: use "long_only", 1 position max
- If no exit rules: add basic stop_loss 2% and take_profit 2:1 RR

OUTPUT ONLY JSON, NO EXPLANATIONS."""

        user_prompt = f"Convert this trading strategy to DSL: {text}"
        if defaults:
            user_prompt += f"\n\nAdditional context: {json.dumps(defaults)}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent JSON
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up the response (remove any markdown formatting)
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from OpenAI: {e}")
            raise ValueError(f"OpenAI returned invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise ValueError(f"OpenAI API error: {str(e)}")
    
    def _call_openai_repair(self, text: str, invalid_json: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Call OpenAI to repair invalid JSON"""
        
        repair_prompt = f"""
The following JSON failed validation with error: {error_msg}

Invalid JSON:
{json.dumps(invalid_json, indent=2)}

Please fix the JSON to match the schema exactly. Output ONLY the corrected JSON, no explanations.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a JSON repair expert. Fix JSON to match the exact schema provided."},
                    {"role": "user", "content": repair_prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up the response
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Repair attempt failed: {e}")
            raise ValueError(f"Could not repair JSON: {str(e)}")
    
    def _parse_with_rules(self, text: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Parse natural language using rule-based approach"""
        text_lower = text.lower()
        
        # Extract symbol
        symbol = "SPY"  # Default
        if "spy" in text_lower or "sp500" in text_lower or "s&p" in text_lower:
            symbol = "SPY"
        elif "qqq" in text_lower or "nasdaq" in text_lower:
            symbol = "QQQ"
        elif "dow" in text_lower or "dia" in text_lower:
            symbol = "DIA"
        
        # Extract timeframe
        start_date = defaults.get('start_date', '2021-01-01')
        end_date = defaults.get('end_date', '2023-01-01')
        resolution = defaults.get('resolution', 'Minute')
        
        # Extract entry rules based on indicators mentioned
        entry_rules = []
        
        # RSI rules
        if "rsi" in text_lower:
            if "below" in text_lower and "30" in text_lower:
                entry_rules.append({
                    "type": "indicator_condition",
                    "left": {"indicator": "RSI", "period": 14},
                    "operator": "lt",
                    "right": {"value": 30}
                })
            elif "above" in text_lower and "70" in text_lower:
                entry_rules.append({
                    "type": "indicator_condition",
                    "left": {"indicator": "RSI", "period": 14},
                    "operator": "gt",
                    "right": {"value": 70}
                })
        
        # SMA rules
        if "sma" in text_lower or "moving average" in text_lower:
            if "cross" in text_lower and "above" in text_lower:
                entry_rules.append({
                    "type": "indicator_condition",
                    "left": {"indicator": "SMA", "period": 20},
                    "operator": "cross_above",
                    "right": {"indicator": {"indicator": "SMA", "period": 50}}
                })
            elif "cross" in text_lower and "below" in text_lower:
                entry_rules.append({
                    "type": "indicator_condition",
                    "left": {"indicator": "SMA", "period": 20},
                    "operator": "cross_below",
                    "right": {"indicator": {"indicator": "SMA", "period": 50}}
                })
        
        # VWAP rules
        if "vwap" in text_lower:
            if "below" in text_lower and "standard deviation" in text_lower:
                entry_rules.append({
                    "type": "indicator_condition",
                    "left": {"indicator": "VWAP", "offset_std": -1.5},
                    "operator": "cross_below_or_equal",
                    "right": {"indicator": {"indicator": "VWAP", "std_mult": 1.5}}
                })
        
        # If no specific rules found, create a basic RSI strategy
        if not entry_rules:
            entry_rules.append({
                "type": "indicator_condition",
                "left": {"indicator": "RSI", "period": 14},
                "operator": "lt",
                "right": {"value": 30}
            })
        
        # Extract exit rules
        exit_rules = []
        
        # Look for stop loss
        if "stop" in text_lower and "loss" in text_lower:
            if "1%" in text_lower:
                exit_rules.append({"type": "stop_loss", "pct": 1.0})
            elif "2%" in text_lower:
                exit_rules.append({"type": "stop_loss", "pct": 2.0})
            else:
                exit_rules.append({"type": "stop_loss", "atr_mult": 1.5})
        
        # Look for take profit
        if "take profit" in text_lower or "tp" in text_lower:
            if "2%" in text_lower:
                exit_rules.append({"type": "take_profit", "target_pct": 2.0})
            elif "2:1" in text_lower or "2.0" in text_lower:
                exit_rules.append({"type": "take_profit", "rr": 2.0})
            else:
                exit_rules.append({"type": "take_profit", "rr": 2.0})
        
        # Default exit rules if none found
        if not exit_rules:
            exit_rules = [
                {"type": "take_profit", "rr": 2.0},
                {"type": "stop_loss", "atr_mult": 1.5}
            ]
        
        # Determine position side
        side = "long_only"  # Default
        if "short" in text_lower or "sell" in text_lower:
            side = "short_only"
        elif "both" in text_lower or "long and short" in text_lower:
            side = "both"
        
        # Build the DSL
        dsl = {
            "universe": {
                "type": "single",
                "symbol": symbol,
                "asset_class": "Equity"
            },
            "timeframe": {
                "start": start_date,
                "end": end_date,
                "resolution": resolution
            },
            "entry_rules": entry_rules,
            "exit_rules": exit_rules,
            "positioning": {
                "side": side,
                "risk_per_trade_pct": 1.0,
                "max_concurrent_positions": 1
            }
        }
        
        return dsl
