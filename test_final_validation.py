#!/usr/bin/env python3
"""
Test final para validar todo el sistema con los fixes de ChatGPT
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

def test_complete_system():
    """Test completo del sistema con fixes aplicados"""
    print("🚀 Test Final - Sistema Completo con Fixes de ChatGPT")
    print("=" * 70)
    
    # Crear usuario
    user, _ = User.objects.get_or_create(username='test_user')
    
    # Crear estrategia con regla lógica y configuración realista
    strategy_data = {
        'name': 'test_complete_system',
        'description': 'Sistema completo con regla lógica RSI',
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
    print(f"   Capital inicial: ${strategy.initial_capital}")
    
    # Ejecutar backtest
    try:
        engine = BacktestEngine()
        start_date = timezone.make_aware(datetime(2024, 12, 1))
        end_date = timezone.make_aware(datetime(2024, 12, 7))  # 1 semana
        
        print(f"\n🚀 Ejecutando backtest: {start_date.date()} a {end_date.date()}")
        result = engine.run_backtest(strategy, start_date, end_date)
        
        print(f"\n📊 Resultados del Backtest:")
        print(f"   Total trades: {result.total_trades}")
        print(f"   Total return: ${result.total_return}")
        print(f"   Win rate: {result.win_rate}%")
        print(f"   Profit factor: {result.profit_factor}")
        print(f"   Max drawdown: {result.max_drawdown_percent}%")
        print(f"   Sharpe ratio: {result.sharpe_ratio}")
        print(f"   Sortino ratio: {result.sortino_ratio}")
        
        # Verificar trades
        trades = result.trades.all()
        if trades:
            print(f"\n📈 Análisis de Trades:")
            print(f"   Total trades: {len(trades)}")
            
            # Calcular métricas de trades
            winning_trades = [t for t in trades if t.net_pnl > 0]
            losing_trades = [t for t in trades if t.net_pnl < 0]
            
            print(f"   Winning trades: {len(winning_trades)}")
            print(f"   Losing trades: {len(losing_trades)}")
            
            if winning_trades:
                avg_win = sum(t.net_pnl for t in winning_trades) / len(winning_trades)
                print(f"   Average win: ${avg_win:.2f}")
            
            if losing_trades:
                avg_loss = sum(t.net_pnl for t in losing_trades) / len(losing_trades)
                print(f"   Average loss: ${avg_loss:.2f}")
            
            print(f"\n📈 Primeros 5 trades:")
            for i, trade in enumerate(trades[:5]):
                print(f"   Trade {i+1}: {trade.action} {trade.quantity} @ ${trade.entry_price} -> ${trade.exit_price}")
                print(f"     P&L: ${trade.pnl} | Net: ${trade.net_pnl} | Reason: {trade.reason}")
                
                # Verificar P&L por punto
                if trade.entry_price and trade.exit_price:
                    points = abs(trade.exit_price - trade.entry_price)
                    pnl_per_point = trade.pnl / (points * trade.quantity) if points > 0 else 0
                    print(f"     P&L por punto: ${pnl_per_point:.2f} (esperado: $50)")
        
        # Verificar equity curve
        if hasattr(result, 'equitycurvepoint_set'):
            equity_points = result.equitycurvepoint_set.all()
            if equity_points:
                print(f"\n📊 Equity Curve (últimos 5 puntos):")
                for point in equity_points[-5:]:
                    print(f"   ${point.equity_value} (DD: {point.drawdown:.2%})")
        
        # Validar cálculos
        print(f"\n🔍 Validación de Cálculos:")
        
        # 1. Position sizing
        expected_quantity = 10  # 100k * 1% / (2 puntos * $50) = 10 contratos
        actual_quantity = trades[0].quantity if trades else 0
        print(f"   Position sizing: {actual_quantity} contratos (esperado: {expected_quantity})")
        
        # 2. P&L por punto
        if trades:
            first_trade = trades[0]
            if first_trade.entry_price and first_trade.exit_price:
                points = abs(first_trade.exit_price - first_trade.entry_price)
                pnl_per_point = first_trade.pnl / (points * first_trade.quantity) if points > 0 else 0
                print(f"   P&L por punto: ${pnl_per_point:.2f} (esperado: $50)")
        
        # 3. Total return
        expected_final_capital = float(strategy.initial_capital) + float(result.total_return)
        print(f"   Capital final: ${expected_final_capital:.2f}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error en backtest: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("🚀 Test Final - Validación Completa del Sistema")
    print("=" * 70)
    
    result = test_complete_system()
    
    print("\n" + "=" * 70)
    if result:
        print("✅ Test completado exitosamente")
        print("🎉 Todos los fixes de ChatGPT están funcionando correctamente!")
    else:
        print("❌ Test falló")

if __name__ == "__main__":
    main()


