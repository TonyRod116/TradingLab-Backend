#!/usr/bin/env python3
"""
Script para analizar el problema del backtest con RSI
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

def analyze_latest_backtest():
    """Analizar el último backtest con problemas"""
    print("🔍 Analizando último backtest con problemas")
    print("=" * 60)
    
    # Buscar el último backtest
    latest_backtest = BacktestResult.objects.order_by('-created_at').first()
    
    if not latest_backtest:
        print("❌ No se encontraron backtests")
        return
    
    print(f"📊 Backtest ID: {latest_backtest.id}")
    print(f"   Estrategia: {latest_backtest.strategy.name}")
    print(f"   Fecha: {latest_backtest.created_at}")
    print(f"   Capital inicial: ${latest_backtest.initial_capital}")
    print(f"   Total return: ${latest_backtest.total_return}")
    print(f"   Total return %: {latest_backtest.total_return_percent}%")
    print(f"   Win rate: {latest_backtest.win_rate}%")
    print(f"   Total trades: {latest_backtest.total_trades}")
    print(f"   Max drawdown: ${latest_backtest.max_drawdown}")
    print(f"   Max drawdown %: {latest_backtest.max_drawdown_percent}%")
    
    # Analizar trades
    trades = Trade.objects.filter(backtest=latest_backtest).order_by('entry_date')
    print(f"\n📈 Análisis de Trades ({len(trades)} total):")
    
    if trades:
        # Primeros 5 trades
        print("\n🔍 Primeros 5 trades:")
        for i, trade in enumerate(trades[:5]):
            print(f"   Trade {i+1}:")
            print(f"     Fecha: {trade.entry_date}")
            print(f"     Acción: {trade.action}")
            print(f"     Cantidad: {trade.quantity}")
            print(f"     Precio entrada: ${trade.entry_price}")
            print(f"     Precio salida: ${trade.exit_price}")
            print(f"     P&L: ${trade.pnl}")
            print(f"     Net P&L: ${trade.net_pnl}")
            print(f"     Comisión: ${trade.commission}")
            print(f"     Slippage: ${trade.slippage}")
            print(f"     Razón: {trade.reason}")
            print()
        
        # Estadísticas de P&L
        pnl_values = [float(trade.pnl) for trade in trades]
        net_pnl_values = [float(trade.net_pnl) for trade in trades]
        
        print(f"📊 Estadísticas de P&L:")
        print(f"   P&L mínimo: ${min(pnl_values)}")
        print(f"   P&L máximo: ${max(pnl_values)}")
        print(f"   P&L promedio: ${sum(pnl_values)/len(pnl_values):.2f}")
        print(f"   Net P&L mínimo: ${min(net_pnl_values)}")
        print(f"   Net P&L máximo: ${max(net_pnl_values)}")
        print(f"   Net P&L promedio: ${sum(net_pnl_values)/len(net_pnl_values):.2f}")
        
        # Verificar valores problemáticos
        problem_trades = [t for t in trades if abs(float(t.pnl)) > 500000]
        if problem_trades:
            print(f"\n⚠️  Trades con P&L extremo ({len(problem_trades)}):")
            for trade in problem_trades[:3]:
                print(f"   Trade {trade.id}: P&L=${trade.pnl}, Net=${trade.net_pnl}")
    
    # Analizar la estrategia
    strategy = latest_backtest.strategy
    print(f"\n🎯 Análisis de la Estrategia:")
    print(f"   Nombre: {strategy.name}")
    print(f"   Símbolo: {strategy.symbol}")
    print(f"   Timeframe: {strategy.timeframe}")
    print(f"   Reglas de entrada: {strategy.entry_rules}")
    print(f"   Reglas de salida: {strategy.exit_rules}")
    print(f"   Stop loss: {strategy.stop_loss_type} = {strategy.stop_loss_value}")
    print(f"   Take profit: {strategy.take_profit_type} = {strategy.take_profit_value}")
    
    return latest_backtest

def test_rsi_calculation():
    """Probar el cálculo de RSI manualmente"""
    print("\n🧮 Probando cálculo de RSI:")
    print("=" * 40)
    
    # Crear datos de prueba
    import pandas as pd
    import numpy as np
    
    # Datos de ejemplo para RSI
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    df = pd.DataFrame({
        'close': prices,
        'date': pd.date_range('2024-01-01', periods=100, freq='30min')
    })
    
    # Calcular RSI manualmente
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    
    # RSI 30
    roll_up = up.ewm(alpha=1/30, adjust=False).mean()
    roll_dn = down.ewm(alpha=1/30, adjust=False).mean()
    rs = roll_up / (roll_dn.replace(0, 1e-12))
    rsi_30 = 100 - (100/(1+rs))
    
    print(f"   RSI 30 valores:")
    print(f"   Min: {rsi_30.min():.2f}")
    print(f"   Max: {rsi_30.max():.2f}")
    print(f"   Promedio: {rsi_30.mean():.2f}")
    print(f"   Valores < 30: {(rsi_30 < 30).sum()}")
    
    # Simular condición de entrada
    entry_signals = rsi_30 < 30
    print(f"   Señales de entrada: {entry_signals.sum()}")
    
    return df, rsi_30

def main():
    print("🚀 Análisis del Problema de Backtest RSI")
    print("=" * 60)
    
    # Analizar último backtest
    backtest = analyze_latest_backtest()
    
    # Probar cálculo de RSI
    df, rsi = test_rsi_calculation()
    
    print("\n" + "=" * 60)
    print("✅ Análisis completado")
    print("\n📋 Resumen del problema:")
    print("   1. El motor limita valores a ±999999 para evitar overflow")
    print("   2. Los cálculos de P&L pueden estar generando valores extremos")
    print("   3. Necesita revisión del cálculo de position size y P&L")

if __name__ == "__main__":
    main()
