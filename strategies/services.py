"""
Servicios para estrategias de trading y rule builder
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q

from .models import Strategy, StrategyRule, StrategyExecution
from indicators.services import TechnicalAnalysisService


class StrategyRuleEngine:
    """Motor de reglas para evaluar estrategias de trading"""
    
    def __init__(self, strategy: Strategy):
        self.strategy = strategy
        self.rules = strategy.strategy_rules.filter(is_active=True).order_by('priority', 'order')
    
    def evaluate_conditions(self, market_data: pd.DataFrame) -> Dict[str, bool]:
        """
        Evalúa todas las condiciones de la estrategia
        
        Args:
            market_data: DataFrame con datos de mercado e indicadores
            
        Returns:
            Dict con el resultado de cada condición
        """
        results = {}
        
        for rule in self.rules.filter(rule_type='condition'):
            try:
                result = self._evaluate_condition(rule, market_data)
                results[rule.name] = result
            except Exception as e:
                results[rule.name] = False
                print(f"Error evaluando regla {rule.name}: {e}")
        
        return results
    
    def _evaluate_condition(self, rule: StrategyRule, market_data: pd.DataFrame) -> bool:
        """
        Evalúa una condición individual
        
        Args:
            rule: Regla a evaluar
            market_data: Datos de mercado
            
        Returns:
            True si la condición se cumple, False en caso contrario
        """
        if rule.rule_type != 'condition':
            return False
        
        # Obtener valores de los operandos
        left_value = self._get_operand_value(rule.left_operand, market_data)
        right_value = self._get_operand_value(rule.right_operand, market_data)
        
        if left_value is None or right_value is None:
            return False
        
        # Aplicar operador
        return self._apply_operator(left_value, right_value, rule.operator)
    
    def _get_operand_value(self, operand: str, market_data: pd.DataFrame) -> Optional[float]:
        """
        Obtiene el valor de un operando desde los datos de mercado
        
        Args:
            operand: Nombre del operando (ej: 'close_price', 'rsi', '50')
            market_data: DataFrame con datos de mercado
            
        Returns:
            Valor del operando o None si no se encuentra
        """
        # Si es un número, devolverlo directamente
        try:
            return float(operand)
        except ValueError:
            pass
        
        # Si es un campo de precio, usar el último valor
        if operand in ['open_price', 'high_price', 'low_price', 'close_price', 'volume']:
            if not market_data.empty:
                return float(market_data[operand].iloc[-1])
        
        # Si es un indicador técnico, usar el último valor
        if operand in market_data.columns:
            if not market_data.empty:
                return float(market_data[operand].iloc[-1])
        
        # Si es un indicador con parámetros (ej: 'sma_20')
        if operand.startswith('sma_') or operand.startswith('ema_'):
            if not market_data.empty:
                return float(market_data[operand].iloc[-1])
        
        return None
    
    def _apply_operator(self, left: float, right: float, operator: str) -> bool:
        """
        Aplica un operador de comparación
        
        Args:
            left: Valor izquierdo
            right: Valor derecho
            operator: Operador a aplicar
            
        Returns:
            Resultado de la comparación
        """
        if operator == 'gt':
            return left > right
        elif operator == 'gte':
            return left >= right
        elif operator == 'lt':
            return left < right
        elif operator == 'lte':
            return left <= right
        elif operator == 'eq':
            return abs(left - right) < 0.0001  # Tolerancia para floats
        elif operator == 'ne':
            return abs(left - right) >= 0.0001
        elif operator == 'above':
            return left > right
        elif operator == 'below':
            return left < right
        else:
            return False
    
    def get_actions(self, conditions_results: Dict[str, bool]) -> List[Dict[str, Any]]:
        """
        Obtiene las acciones a ejecutar basadas en los resultados de las condiciones
        
        Args:
            conditions_results: Resultados de la evaluación de condiciones
            
        Returns:
            Lista de acciones a ejecutar
        """
        actions = []
        
        for rule in self.rules.filter(rule_type='action'):
            try:
                # Verificar si las condiciones previas se cumplen
                if self._should_execute_action(rule, conditions_results):
                    action = {
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'action_type': rule.action_type,
                        'parameters': rule.parameters,
                        'priority': rule.priority
                    }
                    actions.append(action)
            except Exception as e:
                print(f"Error procesando acción {rule.name}: {e}")
        
        # Ordenar por prioridad
        actions.sort(key=lambda x: x['priority'])
        return actions


class StrategyBacktestService:
    """Servicio para ejecutar backtests de estrategias"""
    
    def __init__(self, strategy: Strategy):
        self.strategy = strategy
        self.rule_engine = StrategyRuleEngine(strategy)
    
    def run_backtest(self, start_date: datetime, end_date: datetime, 
                    initial_capital: float = 10000.0, 
                    commission: float = 0.0, 
                    slippage: float = 0.0) -> Dict[str, Any]:
        """
        Ejecuta un backtest de la estrategia
        
        Args:
            start_date: Fecha de inicio del backtest
            end_date: Fecha de fin del backtest
            initial_capital: Capital inicial
            commission: Comisión por trade
            slippage: Slippage por trade
            
        Returns:
            Resultados del backtest
        """
        # TODO: Implementar lógica de backtesting
        # Por ahora retornamos estructura básica
        
        results = {
            'strategy_id': self.strategy.id,
            'strategy_name': self.strategy.name,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital,
            'final_capital': initial_capital,
            'total_return': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'trades': [],
            'equity_curve': [],
            'execution_time': 0.0
        }
        
        return results


class StrategyExecutionService:
    """Servicio para ejecutar estrategias en tiempo real"""
    
    def __init__(self, strategy: Strategy):
        self.strategy = strategy
        self.rule_engine = StrategyRuleEngine(strategy)
    
    def evaluate_strategy(self, market_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Evalúa la estrategia con datos de mercado actuales
        
        Args:
            market_data: Datos de mercado actuales
            
        Returns:
            Lista de acciones a ejecutar
        """
        # Evaluar condiciones
        conditions_results = self.rule_engine.evaluate_conditions(market_data)
        
        # Obtener acciones
        actions = self.rule_engine.get_actions(conditions_results)
        
        # Registrar ejecución
        self._log_execution(conditions_results, actions, market_data)
        
        return actions
    
    def _log_execution(self, conditions_results: Dict[str, bool], 
                      actions: List[Dict[str, Any]], 
                      market_data: pd.DataFrame):
        """
        Registra la ejecución de la estrategia
        
        Args:
            conditions_results: Resultados de las condiciones
            actions: Acciones a ejecutar
            market_data: Datos de mercado utilizados
        """
        for action in actions:
            rule = StrategyRule.objects.get(id=action['rule_id'])
            
            # Crear registro de ejecución
            execution = StrategyExecution.objects.create(
                strategy=self.strategy,
                rule=rule,
                status='executed' if actions else 'pending',
                market_data=market_data.to_dict('records')[-1] if not market_data.empty else {},
                result={
                    'conditions_results': conditions_results,
                    'action': action,
                    'executed_at': timezone.now().isoformat()
                }
            )


class StrategyTemplateService:
    """Servicio para crear plantillas de estrategias predefinidas"""
    
    @staticmethod
    def get_strategy_templates() -> List[Dict[str, Any]]:
        """
        Retorna plantillas de estrategias predefinidas
        
        Returns:
            Lista de plantillas disponibles
        """
        templates = [
            {
                'name': 'Moving Average Crossover',
                'description': 'Estrategia de cruce de medias móviles',
                'strategy_type': 'trend_following',
                'rules': [
                    {
                        'name': 'SMA 20 > SMA 50',
                        'rule_type': 'condition',
                        'condition_type': 'indicator',
                        'left_operand': 'sma_20',
                        'operator': 'gt',
                        'right_operand': 'sma_50',
                        'priority': 1,
                        'order': 1
                    },
                    {
                        'name': 'Buy Signal',
                        'rule_type': 'action',
                        'action_type': 'buy',
                        'priority': 2,
                        'order': 1
                    }
                ]
            },
            {
                'name': 'RSI Oversold/Overbought',
                'description': 'Estrategia de reversión basada en RSI',
                'strategy_type': 'mean_reversion',
                'rules': [
                    {
                        'name': 'RSI < 30',
                        'rule_type': 'condition',
                        'condition_type': 'indicator',
                        'left_operand': 'rsi',
                        'operator': 'lt',
                        'right_operand': '30',
                        'priority': 1,
                        'order': 1
                    },
                    {
                        'name': 'Buy Signal',
                        'rule_type': 'action',
                        'action_type': 'buy',
                        'priority': 2,
                        'order': 1
                    }
                ]
            },
            {
                'name': 'Breakout Strategy',
                'description': 'Estrategia de breakout con volumen',
                'strategy_type': 'breakout',
                'rules': [
                    {
                        'name': 'Price > High 20',
                        'rule_type': 'condition',
                        'condition_type': 'price',
                        'left_operand': 'close_price',
                        'operator': 'gt',
                        'right_operand': 'high_20',
                        'priority': 1,
                        'order': 1
                    },
                    {
                        'name': 'Volume > Avg Volume',
                        'rule_type': 'condition',
                        'condition_type': 'volume',
                        'left_operand': 'volume',
                        'operator': 'gt',
                        'right_operand': 'avg_volume_20',
                        'priority': 1,
                        'order': 2
                    },
                    {
                        'name': 'Buy Signal',
                        'rule_type': 'action',
                        'action_type': 'buy',
                        'priority': 2,
                        'order': 1
                    }
                ]
            }
        ]
        
        return templates
    
    @staticmethod
    def create_strategy_from_template(template_name: str, user, **kwargs) -> Strategy:
        """
        Crea una estrategia basada en una plantilla
        
        Args:
            template_name: Nombre de la plantilla
            user: Usuario que crea la estrategia
            **kwargs: Parámetros adicionales
            
        Returns:
            Estrategia creada
        """
        templates = StrategyTemplateService.get_strategy_templates()
        template = next((t for t in templates if t['name'] == template_name), None)
        
        if not template:
            raise ValueError(f"Plantilla '{template_name}' no encontrada")
        
        # Crear estrategia
        strategy_data = {
            'user': user,
            'name': kwargs.get('name', template['name']),
            'description': kwargs.get('description', template['description']),
            'strategy_type': template['strategy_type'],
            'symbol': kwargs.get('symbol', 'ES'),
            'timeframe': kwargs.get('timeframe', '1m'),
            'rules': template['rules']
        }
        
        strategy = Strategy.objects.create(**strategy_data)
        
        # Crear reglas
        for rule_data in template['rules']:
            rule_data['strategy'] = strategy
            StrategyRule.objects.create(**rule_data)
        
        return strategy

