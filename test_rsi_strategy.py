#!/usr/bin/env python3
"""
Test específico para estrategia RSI con regla lógica
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

def test_rsi_strategy():
    """Test estrategia RSI con regla lógica"""
    print("🧪 Test Estrategia RSI con Regla Lógica")
    print("=" * 50)
    
    # Crear usuario
    user, _ = User.objects.get_or_create(username='test_user')
    
    # Crear estrategia con regla lógica
    strategy_data = {
        'name': 'test_rsi_oversold',
        'description': 'RSI oversold strategy - rsi_30 < 30',
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
    print(f"   Stop Loss: {strategy.stop_loss_value} puntos")
    print(f"   Take Profit: {strategy.take_profit_value} puntos")
    
    # Ejecutar backtest
    try:
        engine = BacktestEngine()
        start_date = timezone.make_aware(datetime(2024, 12, 1))
        end_date = timezone.make_aware(datetime(2024, 12, 31))  # 1 mes completo
        
        print(f"\n🚀 Ejecutando backtest: {start_date.date()} a {end_date.date()}")
        result = engine.run_backtest(strategy, start_date, end_date)
        
        print(f"\n📊 Resultados del Backtest:")
        print(f"   Total trades: {result.total_trades}")
        print(f"   Total return: ${result.total_return}")
        print(f"   Win rate: {result.win_rate}%")
        print(f"   Profit factor: {result.profit_factor}")
        print(f"   Max drawdown: {result.max_drawdown_percent}%")
        
        # Verificar trades
        trades = result.trades.all()
        if trades:
            print(f"\n📈 Primeros 5 trades:")
            for i, trade in enumerate(trades[:5]):
                print(f"   Trade {i+1}: {trade.action} {trade.quantity} @ ${trade.entry_price} -> ${trade.exit_price}")
                print(f"     P&L: ${trade.pnl} | Net: ${trade.net_pnl} | Reason: {trade.reason}")
        
        # Verificar equity curve
        if hasattr(result, 'equitycurvepoint_set'):
            equity_points = result.equitycurvepoint_set.all()
            if equity_points:
                print(f"\n📊 Equity Curve (últimos 5 puntos):")
                for point in equity_points[-5:]:
                    print(f"   ${point.equity_value} (DD: {point.drawdown:.2%})")
        
        return result
        
    except Exception as e:
        print(f"❌ Error en backtest: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("🚀 Test Estrategia RSI con Regla Lógica")
    print("=" * 60)
    
    result = test_rsi_strategy()
    
    print("\n" + "=" * 60)
    if result:
        print("✅ Test completado exitosamente")
    else:
        print("❌ Test falló")

if __name__ == "__main__":
    main()


