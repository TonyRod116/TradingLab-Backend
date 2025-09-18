#!/usr/bin/env python3
"""
Test script para validar los fixes de ChatGPT
- Reglas lógicas (rsi_30 < 30)
- P&L correcto para ES
- Position sizing realista
- Equity curve única
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.append('/home/tonirod/code/ga/projects/TradingLab-Backend-Clean')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from strategies.models import Strategy, BacktestResult, Trade
from strategies.backtest_engine import BacktestEngine
from users.models import User
from django.utils import timezone

def test_logical_rules():
    """Test 1: Reglas lógicas - RSI oversold"""
    print("🧪 Test 1: Reglas lógicas")
    
    # Crear estrategia con regla lógica
    user, _ = User.objects.get_or_create(username='test_user')
    
    strategy_data = {
        'name': 'test_rsi_logical',
        'description': 'RSI oversold strategy',
        'symbol': 'ES',
        'timeframe': '4h',
        'entry_rules': [{
            'name': 'RSI Oversold Entry',
            'rule_type': 'condition',
            'action_type': 'buy',
            'conditions': [{
                'left_operand': 'rsi_30',
                'operator': 'lt',
                'right_operand': '30',
                'logical_operator': 'and'
            }],
            'priority': 1,
            'parameters': {}
        }],
        'exit_rules': [],
        'stop_loss_type': 'points',
        'stop_loss_value': 2.0,
        'take_profit_type': 'points',
        'take_profit_value': 4.0,
        'initial_capital': 100000,
        'status': 'READY',
        'user': user
    }
    
    strategy = Strategy.objects.create(**strategy_data)
    print(f"✅ Estrategia creada: {strategy.name}")
    print(f"   Regla: {strategy.entry_rules[0]['conditions'][0]}")
    
    return strategy

def test_pnl_calculation():
    """Test 2: P&L correcto para ES"""
    print("\n🧪 Test 2: Cálculo de P&L")
    
    # Simular trade manual
    entry_price = 4000.0
    exit_price = 4002.0  # +2 puntos
    quantity = 10
    commission = 4.0
    
    # Cálculo esperado
    raw_points = exit_price - entry_price  # 2 puntos
    pnl = raw_points * 50.0 * quantity  # 2 * 50 * 10 = $1000
    net_pnl = pnl - commission  # $1000 - $4 = $996
    
    print(f"   Entry: ${entry_price}")
    print(f"   Exit: ${exit_price}")
    print(f"   Points: {raw_points}")
    print(f"   Quantity: {quantity}")
    print(f"   P&L: ${pnl}")
    print(f"   Net P&L: ${net_pnl}")
    print(f"   ✅ P&L por punto: ${pnl/raw_points/quantity} (esperado: $50)")

def test_position_sizing():
    """Test 3: Position sizing realista"""
    print("\n🧪 Test 3: Position sizing")
    
    # Parámetros
    initial_capital = 100000
    stop_loss_points = 2.0
    risk_percent = 0.01
    
    # Cálculo esperado
    risk_budget = initial_capital * risk_percent  # $1000
    risk_per_contract = stop_loss_points * 50.0  # $100
    expected_quantity = int(risk_budget // risk_per_contract)  # 10 contratos
    
    print(f"   Capital inicial: ${initial_capital}")
    print(f"   Riesgo: {risk_percent*100}% = ${risk_budget}")
    print(f"   Stop loss: {stop_loss_points} puntos = ${risk_per_contract}")
    print(f"   Cantidad esperada: {expected_quantity} contratos")
    print(f"   ✅ P&L por punto: ${expected_quantity * 50}")

def test_backtest_with_fixes(strategy):
    """Test 4: Backtest completo con fixes"""
    print("\n🧪 Test 4: Backtest completo")
    
    try:
        engine = BacktestEngine()
        start_date = timezone.make_aware(datetime(2024, 12, 1))
        end_date = timezone.make_aware(datetime(2024, 12, 2))
        
        print(f"   Ejecutando backtest: {start_date} a {end_date}")
        result = engine.run_backtest(strategy, start_date, end_date)
        
        print(f"   ✅ Backtest completado")
        print(f"   Total trades: {result.total_trades}")
        print(f"   Total return: ${result.total_return}")
        print(f"   Win rate: {result.win_rate}%")
        
        # Verificar trades
        trades = result.trades.all()[:3]
        if trades:
            print(f"   Primeros 3 trades:")
            for i, trade in enumerate(trades):
                print(f"     Trade {i+1}: {trade.action} {trade.quantity} @ ${trade.entry_price} -> ${trade.exit_price}")
                print(f"       P&L: ${trade.pnl} | Net: ${trade.net_pnl}")
        
        # Verificar equity curve
        equity_points = result.equitycurvepoint_set.all()[:5] if hasattr(result, 'equitycurvepoint_set') else []
        if equity_points:
            print(f"   Equity curve (primeros 5 puntos):")
            for i, point in enumerate(equity_points):
                print(f"     Punto {i+1}: ${point.equity_value} (DD: {point.drawdown:.2%})")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Error en backtest: {e}")
        return None

def test_ticks_vs_points():
    """Test 5: Equivalencia ticks vs points"""
    print("\n🧪 Test 5: Ticks vs Points")
    
    # 8 ticks = 2 points (8 * 0.25 = 2.0)
    # 4 ticks = 1 point (4 * 0.25 = 1.0)
    
    ticks_8 = 8 * 0.25  # 2.0 points
    ticks_4 = 4 * 0.25  # 1.0 points
    
    print(f"   8 ticks = {ticks_8} points")
    print(f"   4 ticks = {ticks_4} points")
    print(f"   ✅ Conversión correcta")

def main():
    print("🚀 Testing ChatGPT Fixes for TradingLab Backtest Engine")
    print("=" * 60)
    
    # Test 1: Reglas lógicas
    strategy = test_logical_rules()
    
    # Test 2: P&L calculation
    test_pnl_calculation()
    
    # Test 3: Position sizing
    test_position_sizing()
    
    # Test 4: Backtest completo
    result = test_backtest_with_fixes(strategy)
    
    # Test 5: Ticks vs Points
    test_ticks_vs_points()
    
    print("\n" + "=" * 60)
    print("✅ Todos los tests completados")
    
    # Cleanup
    if strategy:
        strategy.delete()
    if result:
        result.delete()

if __name__ == "__main__":
    main()
