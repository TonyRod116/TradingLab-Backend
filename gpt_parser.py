import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from datetime import datetime

class GPTQuantConnectParser:
    """
    Parser que usa GPT para convertir descripciones en lenguaje natural
    a código QuantConnect Python
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"  # Usar modelo más económico
        
    def parse_strategy_description(self, description: str, backtest_params: Dict[str, Any] = None) -> str:
        """
        Convierte una descripción en lenguaje natural a código QuantConnect
        """
        if not backtest_params:
            backtest_params = {}
            
        # Parámetros por defecto
        symbol = backtest_params.get('symbol', 'SPY')
        initial_capital = backtest_params.get('initial_capital', 100000)
        start_date = backtest_params.get('start_date', '2021-01-01')
        end_date = backtest_params.get('end_date', '2024-01-01')
        benchmark = backtest_params.get('benchmark', 'SPY')
        
        # Crear el prompt para GPT
        prompt = self._create_quantconnect_prompt(
            description, symbol, initial_capital, start_date, end_date, benchmark
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en QuantConnect y trading algorítmico. Tu trabajo es convertir descripciones de estrategias de trading en código Python válido para QuantConnect."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Baja temperatura para código más consistente
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Si falla GPT, devolver código básico
            return self._generate_fallback_code(description, symbol, initial_capital, start_date, end_date, benchmark)
    
    def _create_quantconnect_prompt(self, description: str, symbol: str, initial_capital: int, 
                                  start_date: str, end_date: str, benchmark: str) -> str:
        """Crea el prompt específico para QuantConnect"""
        
        return f"""
Eres un experto en QuantConnect y trading algorítmico. Convierte la siguiente descripción de estrategia de trading en código Python funcional para QuantConnect.

DESCRIPCIÓN: "{description}"

PARÁMETROS:
- Símbolo: {symbol}
- Capital: ${initial_capital:,}
- Período: {start_date} a {end_date}
- Benchmark: {benchmark}

INSTRUCCIONES:
1. Analiza la descripción e identifica todos los indicadores técnicos mencionados
2. Identifica las condiciones de entrada y salida exactas
3. Implementa la gestión de riesgo si se menciona (stop loss, take profit)
4. Genera código Python completo y funcional para QuantConnect
5. Usa los períodos correctos de los indicadores (5-day, 10-day, 20-day, etc.)
6. Incluye logging para debugging

FORMATO DE CÓDIGO REQUERIDO:
```python
from AlgorithmImports import *

class TradingStrategy(QCAlgorithm):
    def Initialize(self):
        # Configuración básica
        self.SetStartDate({start_date.replace('-', ', ')})
        self.SetEndDate({end_date.replace('-', ', ')})
        self.SetCash({initial_capital})
        self.symbol = self.AddEquity("{symbol}", Resolution.Daily).Symbol
        self.SetBenchmark("{benchmark}")
        
        # Indicadores técnicos
        # (agregar aquí los indicadores necesarios)
        
        # Warm up
        self.SetWarmUp(20)
    
    def OnData(self, data):
        if self.IsWarmingUp:
            return
        
        # Lógica de trading aquí
        # (implementar las condiciones de entrada y salida)
    
    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Debug(f"Order filled: {{orderEvent}}")
    
    def OnEndOfAlgorithm(self):
        self.Debug("Algorithm completed")
```

IMPORTANTE:
- Solo devuelve el código Python completo
- No incluyas explicaciones ni markdown
- El código debe ser ejecutable directamente en QuantConnect
- Implementa exactamente lo que se describe en la estrategia
"""
    
    def _generate_fallback_code(self, description: str, symbol: str, initial_capital: int,
                              start_date: str, end_date: str, benchmark: str) -> str:
        """Genera código básico si GPT falla"""
        
        start_year, start_month, start_day = start_date.split('-')
        end_year, end_month, end_day = end_date.split('-')
        
        return f'''from AlgorithmImports import *

class TradingStrategy(QCAlgorithm):
    def Initialize(self):
        # Set start and end dates
        self.SetStartDate({start_year}, {start_month}, {start_day})
        self.SetEndDate({end_year}, {end_month}, {end_day})
        self.SetCash({initial_capital})
        
        # Add equity data
        self.symbol = self.AddEquity("{symbol}", Resolution.Daily).Symbol
        
        # Set benchmark
        self.SetBenchmark("{benchmark}")
        
        # Initialize indicators
        self.rsi = self.RSI(self.symbol, 14)
        self.sma20 = self.SMA(self.symbol, 20)
        
        # Set up warm up period
        self.SetWarmUp(20)
        
    def OnData(self, data):
        # Skip if warming up
        if self.IsWarmingUp:
            return
            
        if not self.rsi.IsReady or not self.sma20.IsReady:
            return
            
        # Basic RSI strategy
        if not self.Portfolio.Invested:
            if self.rsi.Current.Value < 30:
                self.SetHoldings(self.symbol, 1.0)
        else:
            if self.rsi.Current.Value > 70:
                self.Liquidate(self.symbol)
                
    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Debug(f"Order filled: {{orderEvent}}")
            
    def OnEndOfAlgorithm(self):
        self.Debug("Algorithm completed")'''
    
    def generate_strategy_templates(self) -> list:
        """Genera templates de estrategias usando GPT"""
        
        templates = [
            {
                'id': 'rsi_mean_reversion',
                'name': 'RSI Mean Reversion',
                'description': 'Buy when RSI is below 30, sell when RSI is above 70',
                'category': 'Mean Reversion'
            },
            {
                'id': 'moving_average_crossover',
                'name': 'Moving Average Crossover',
                'description': 'Buy when price crosses above 20-day SMA, sell when it crosses below',
                'category': 'Trend Following'
            },
            {
                'id': 'bollinger_bands',
                'name': 'Bollinger Bands',
                'description': 'Buy when price touches lower band, sell when it touches upper band',
                'category': 'Mean Reversion'
            },
            {
                'id': 'macd_crossover',
                'name': 'MACD Crossover',
                'description': 'Buy when MACD crosses above signal line, sell when it crosses below',
                'category': 'Trend Following'
            },
            {
                'id': 'momentum_strategy',
                'name': 'Momentum Strategy',
                'description': 'Buy when price is above 50-day SMA and RSI > 50, sell when conditions reverse',
                'category': 'Momentum'
            }
        ]
        
        return templates
    
    def analyze_strategy_complexity(self, description: str) -> Dict[str, Any]:
        """Analiza la complejidad de una estrategia usando GPT"""
        
        prompt = f"""
Analiza la siguiente descripción de estrategia de trading y determina su complejidad:

DESCRIPCIÓN: "{description}"

Proporciona un análisis en formato JSON con:
- complexity_level: "basic", "intermediate", "advanced"
- required_indicators: lista de indicadores necesarios
- risk_level: "low", "medium", "high"
- estimated_performance: estimación de rendimiento esperado
- recommended_timeframe: timeframe recomendado
- market_conditions: condiciones de mercado ideales

Solo devuelve el JSON, sin explicaciones adicionales.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un analista de trading experto. Analiza estrategias y proporciona métricas de complejidad y riesgo."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            return json.loads(response.choices[0].message.content.strip())
            
        except Exception as e:
            # Fallback analysis
            return {
                "complexity_level": "basic",
                "required_indicators": ["RSI", "SMA"],
                "risk_level": "medium",
                "estimated_performance": "moderate",
                "recommended_timeframe": "daily",
                "market_conditions": "trending"
            }
