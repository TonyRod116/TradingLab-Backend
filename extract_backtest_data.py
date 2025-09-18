#!/usr/bin/env python3
"""
Script para extraer datos específicos del último backtest problemático
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.append('/home/tonirod/code/ga/projects/TradingLab-Backend-Clean')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from strategies.models import Strategy, BacktestResult, Trade
from users.models import User

def extract_backtest_data():
    """Extraer datos del último backtest problemático"""
    print("🔍 Extrayendo datos del último backtest problemático")
    print("=" * 60)
    
    # Buscar el último backtest
    latest_backtest = BacktestResult.objects.order_by('-created_at').first()
    
    if not latest_backtest:
        print("❌ No se encontraron backtests")
        return None
    
    print(f"📊 Backtest encontrado: ID {latest_backtest.id}")
    
    # Extraer datos de la estrategia
    strategy = latest_backtest.strategy
    strategy_data = {
        'id': strategy.id,
        'name': strategy.name,
        'description': strategy.description,
        'symbol': strategy.symbol,
        'timeframe': strategy.timeframe,
        'entry_rules': strategy.entry_rules,
        'exit_rules': strategy.exit_rules,
        'stop_loss_type': strategy.stop_loss_type,
        'stop_loss_value': float(strategy.stop_loss_value) if strategy.stop_loss_value else None,
        'take_profit_type': strategy.take_profit_type,
        'take_profit_value': float(strategy.take_profit_value) if strategy.take_profit_value else None,
        'initial_capital': float(strategy.initial_capital),
        'status': strategy.status,
        'created_at': strategy.created_at.isoformat(),
        'user_id': strategy.user.id
    }
    
    # Extraer datos del backtest
    backtest_data = {
        'id': latest_backtest.id,
        'strategy_id': latest_backtest.strategy.id,
        'start_date': latest_backtest.start_date.isoformat(),
        'end_date': latest_backtest.end_date.isoformat(),
        'initial_capital': float(latest_backtest.initial_capital),
        'commission': float(latest_backtest.commission),
        'slippage': float(latest_backtest.slippage),
        'execution_time': latest_backtest.execution_time,
        'data_source': latest_backtest.data_source,
        'created_at': latest_backtest.created_at.isoformat(),
        'performance': {
            'total_return': float(latest_backtest.total_return),
            'total_return_percent': float(latest_backtest.total_return_percent),
            'total_trades': latest_backtest.total_trades,
            'winning_trades': latest_backtest.winning_trades,
            'losing_trades': latest_backtest.losing_trades,
            'win_rate': float(latest_backtest.win_rate),
            'profit_factor': float(latest_backtest.profit_factor),
            'avg_win': float(latest_backtest.avg_win),
            'avg_loss': float(latest_backtest.avg_loss),
            'largest_win': float(latest_backtest.largest_win),
            'largest_loss': float(latest_backtest.largest_loss),
            'sharpe_ratio': float(latest_backtest.sharpe_ratio) if latest_backtest.sharpe_ratio else None,
            'max_drawdown': float(latest_backtest.max_drawdown),
            'max_drawdown_percent': float(latest_backtest.max_drawdown_percent),
            'rating': latest_backtest.rating,
            'rating_color': latest_backtest.rating_color,
            'summary_description': latest_backtest.summary_description
        }
    }
    
    # Extraer trades (limitado a los primeros 100 para no sobrecargar)
    trades = Trade.objects.filter(backtest=latest_backtest).order_by('entry_date')[:100]
    trades_data = []
    
    for trade in trades:
        trade_data = {
            'id': trade.id,
            'action': trade.action,
            'entry_price': float(trade.entry_price),
            'exit_price': float(trade.exit_price),
            'entry_date': trade.entry_date.isoformat(),
            'exit_date': trade.exit_date.isoformat(),
            'quantity': trade.quantity,
            'pnl': float(trade.pnl),
            'commission': float(trade.commission),
            'slippage': float(trade.slippage),
            'net_pnl': float(trade.net_pnl),
            'reason': trade.reason,
            'duration': trade.duration
        }
        trades_data.append(trade_data)
    
    # Crear estructura completa
    complete_data = {
        'backtest_id': latest_backtest.id,
        'extraction_timestamp': datetime.now().isoformat(),
        'strategy': strategy_data,
        'backtest': backtest_data,
        'trades': trades_data,
        'trades_count': len(trades_data),
        'total_trades_in_backtest': latest_backtest.total_trades
    }
    
    return complete_data

def save_data_to_file(data, filename):
    """Guardar datos en archivo JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"✅ Datos guardados en: {filename}")

def create_summary_report(data):
    """Crear reporte resumido"""
    if not data:
        return
    
    print(f"\n📋 RESUMEN DEL BACKTEST PROBLEMÁTICO")
    print("=" * 50)
    
    strategy = data['strategy']
    backtest = data['backtest']
    performance = backtest['performance']
    
    print(f"🎯 Estrategia: {strategy['name']}")
    print(f"   Símbolo: {strategy['symbol']}")
    print(f"   Timeframe: {strategy['timeframe']}")
    print(f"   Reglas de entrada: {strategy['entry_rules']}")
    print(f"   Stop Loss: {strategy['stop_loss_type']} = {strategy['stop_loss_value']}")
    print(f"   Take Profit: {strategy['take_profit_type']} = {strategy['take_profit_value']}")
    
    print(f"\n📊 Resultados del Backtest:")
    print(f"   Período: {backtest['start_date']} a {backtest['end_date']}")
    print(f"   Capital inicial: ${backtest['initial_capital']:,}")
    print(f"   Total return: ${performance['total_return']:,}")
    print(f"   Total return %: {performance['total_return_percent']:.2f}%")
    print(f"   Total trades: {performance['total_trades']:,}")
    print(f"   Win rate: {performance['win_rate']:.1f}%")
    print(f"   Profit factor: {performance['profit_factor']:.2f}")
    print(f"   Max drawdown: ${performance['max_drawdown']:,}")
    print(f"   Max drawdown %: {performance['max_drawdown_percent']:.2f}%")
    print(f"   Rating: {performance['rating']}")
    
    print(f"\n📈 Análisis de Trades (primeros {len(data['trades'])}):")
    if data['trades']:
        pnl_values = [t['net_pnl'] for t in data['trades']]
        print(f"   P&L mínimo: ${min(pnl_values):,.2f}")
        print(f"   P&L máximo: ${max(pnl_values):,.2f}")
        print(f"   P&L promedio: ${sum(pnl_values)/len(pnl_values):,.2f}")
        
        # Trades extremos
        extreme_trades = [t for t in data['trades'] if abs(t['net_pnl']) > 10000]
        if extreme_trades:
            print(f"   Trades con P&L extremo (>$10,000): {len(extreme_trades)}")
            for trade in extreme_trades[:3]:
                print(f"     Trade {trade['id']}: P&L=${trade['net_pnl']:,.2f}, Cantidad={trade['quantity']}")

def main():
    print("🚀 Extrayendo datos del backtest problemático")
    print("=" * 60)
    
    try:
        # Extraer datos
        data = extract_backtest_data()
        
        if not data:
            print("❌ No se pudieron extraer los datos")
            return
        
        # Crear reporte resumido
        create_summary_report(data)
        
        # Guardar datos completos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_data_{timestamp}.json"
        save_data_to_file(data, filename)
        
        # Crear archivo de resumen para ChatGPT
        summary_filename = f"backtest_summary_{timestamp}.txt"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write("DATOS DEL BACKTEST PROBLEMÁTICO\n")
            f.write("=" * 50 + "\n\n")
            
            strategy = data['strategy']
            backtest = data['backtest']
            performance = backtest['performance']
            
            f.write(f"Estrategia: {strategy['name']}\n")
            f.write(f"Símbolo: {strategy['symbol']}\n")
            f.write(f"Timeframe: {strategy['timeframe']}\n")
            f.write(f"Reglas de entrada: {strategy['entry_rules']}\n")
            f.write(f"Stop Loss: {strategy['stop_loss_type']} = {strategy['stop_loss_value']}\n")
            f.write(f"Take Profit: {strategy['take_profit_type']} = {strategy['take_profit_value']}\n\n")
            
            f.write(f"Resultados:\n")
            f.write(f"Total return: ${performance['total_return']:,}\n")
            f.write(f"Total return %: {performance['total_return_percent']:.2f}%\n")
            f.write(f"Total trades: {performance['total_trades']:,}\n")
            f.write(f"Win rate: {performance['win_rate']:.1f}%\n")
            f.write(f"Max drawdown: ${performance['max_drawdown']:,}\n")
            f.write(f"Max drawdown %: {performance['max_drawdown_percent']:.2f}%\n\n")
            
            f.write("PROBLEMA IDENTIFICADO:\n")
            f.write("El motor de backtest limita valores a ±999,999 para evitar overflow de base de datos.\n")
            f.write("Esto ocurre en backtest_engine.py líneas 647-655.\n")
            f.write("Los valores reales de P&L son mucho mayores pero se truncan artificialmente.\n")
        
        print(f"✅ Archivos creados:")
        print(f"   - {filename} (datos completos)")
        print(f"   - {summary_filename} (resumen para ChatGPT)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
