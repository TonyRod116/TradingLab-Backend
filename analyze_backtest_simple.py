#!/usr/bin/env python3
"""
Análisis simple del problema de backtest sin Django
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def analyze_rsi_calculation():
    """Analizar el cálculo de RSI y posibles problemas"""
    print("🔍 Análisis del Problema de Backtest RSI")
    print("=" * 60)
    
    # Crear datos de prueba realistas para ES (E-mini S&P 500)
    np.random.seed(42)
    n_periods = 1000
    
    # Precios base para ES (alrededor de 4000-5000)
    base_price = 4500
    price_changes = np.random.randn(n_periods) * 2.0  # Volatilidad típica de ES
    prices = base_price + np.cumsum(price_changes)
    
    df = pd.DataFrame({
        'close': prices,
        'high': prices + np.random.uniform(0, 1, n_periods),
        'low': prices - np.random.uniform(0, 1, n_periods),
        'volume': np.random.randint(1000, 10000, n_periods),
        'date': pd.date_range('2024-01-01', periods=n_periods, freq='30min')
    })
    
    print(f"📊 Datos de prueba creados:")
    print(f"   Períodos: {len(df)}")
    print(f"   Precio inicial: ${df['close'].iloc[0]:.2f}")
    print(f"   Precio final: ${df['close'].iloc[-1]:.2f}")
    print(f"   Rango de precios: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    # Calcular RSI 30
    print(f"\n🧮 Calculando RSI 30:")
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    
    # RSI 30 (usando Wilder's smoothing)
    roll_up = up.ewm(alpha=1/30, adjust=False).mean()
    roll_dn = down.ewm(alpha=1/30, adjust=False).mean()
    rs = roll_up / (roll_dn.replace(0, 1e-12))
    rsi_30 = 100 - (100/(1+rs))
    
    print(f"   RSI 30 estadísticas:")
    print(f"   Min: {rsi_30.min():.2f}")
    print(f"   Max: {rsi_30.max():.2f}")
    print(f"   Promedio: {rsi_30.mean():.2f}")
    print(f"   Valores < 30: {(rsi_30 < 30).sum()}")
    print(f"   Valores < 20: {(rsi_30 < 20).sum()}")
    
    # Simular estrategia de compra cuando RSI < 30
    entry_signals = rsi_30 < 30
    print(f"\n🎯 Señales de entrada (RSI < 30): {entry_signals.sum()}")
    
    if entry_signals.sum() > 0:
        entry_dates = df[entry_signals]['date']
        print(f"   Fechas de entrada: {len(entry_dates)}")
        print(f"   Primera entrada: {entry_dates.iloc[0]}")
        print(f"   Última entrada: {entry_dates.iloc[-1]}")
    
    return df, rsi_30, entry_signals

def simulate_trading_logic(df, rsi_30, entry_signals):
    """Simular la lógica de trading para identificar problemas"""
    print(f"\n💰 Simulando lógica de trading:")
    print("=" * 40)
    
    # Parámetros de ES
    ES_POINT_VALUE = 50.0  # $50 por punto
    ES_TICK = 0.25         # 0.25 puntos por tick
    COMMISSION = 4.00      # $4 por round turn
    SLIPPAGE = 0.5         # 0.5 puntos de slippage
    
    initial_capital = 100000
    portfolio_value = initial_capital
    current_position = None
    trades = []
    
    print(f"   Capital inicial: ${initial_capital:,}")
    print(f"   Valor por punto ES: ${ES_POINT_VALUE}")
    print(f"   Comisión: ${COMMISSION}")
    print(f"   Slippage: {SLIPPAGE} puntos")
    
    # Simular trading
    for i, (idx, row) in enumerate(df.iterrows()):
        current_price = row['close']
        current_date = row['date']
        current_rsi = rsi_30.iloc[i]
        
        # Verificar entrada
        if current_position is None and entry_signals.iloc[i]:
            # Calcular tamaño de posición (simplificado)
            position_size = 1  # 1 contrato por simplicidad
            
            # Aplicar slippage
            entry_price = current_price + (SLIPPAGE * ES_TICK)
            
            current_position = {
                'action': 'buy',
                'entry_price': entry_price,
                'entry_date': current_date,
                'quantity': position_size,
                'rsi_entry': current_rsi
            }
            
            print(f"   📈 ENTRADA #{len(trades)+1}: {current_date}")
            print(f"      Precio: ${current_price:.2f} -> ${entry_price:.2f} (con slippage)")
            print(f"      RSI: {current_rsi:.2f}")
            print(f"      Cantidad: {position_size} contratos")
        
        # Verificar salida (simplificado: salir después de 1 período)
        elif current_position is not None:
            # Aplicar slippage
            exit_price = current_price - (SLIPPAGE * ES_TICK)
            
            # Calcular P&L
            side_sign = 1.0 if current_position['action'] == 'buy' else -1.0
            raw_points = (exit_price - current_position['entry_price']) * side_sign
            
            # P&L en dólares
            pnl = raw_points * ES_POINT_VALUE * current_position['quantity']
            net_pnl = pnl - COMMISSION
            
            # Crear trade
            trade = {
                'entry_date': current_position['entry_date'],
                'exit_date': current_date,
                'action': current_position['action'],
                'entry_price': current_position['entry_price'],
                'exit_price': exit_price,
                'quantity': current_position['quantity'],
                'raw_points': raw_points,
                'pnl': pnl,
                'commission': COMMISSION,
                'net_pnl': net_pnl,
                'rsi_entry': current_position['rsi_entry'],
                'rsi_exit': current_rsi
            }
            
            trades.append(trade)
            
            print(f"   📉 SALIDA #{len(trades)}: {current_date}")
            print(f"      Precio: ${current_price:.2f} -> ${exit_price:.2f} (con slippage)")
            print(f"      RSI: {current_rsi:.2f}")
            print(f"      Puntos: {raw_points:.2f}")
            print(f"      P&L: ${pnl:.2f}")
            print(f"      Net P&L: ${net_pnl:.2f}")
            
            # Actualizar portfolio
            portfolio_value += net_pnl
            
            # Reset position
            current_position = None
    
    return trades, portfolio_value

def analyze_trades(trades, initial_capital, final_value):
    """Analizar los trades generados"""
    print(f"\n📊 Análisis de Trades:")
    print("=" * 30)
    
    if not trades:
        print("   No se generaron trades")
        return
    
    df_trades = pd.DataFrame(trades)
    
    print(f"   Total trades: {len(trades)}")
    print(f"   Capital inicial: ${initial_capital:,}")
    print(f"   Capital final: ${final_value:,.2f}")
    print(f"   Ganancia total: ${final_value - initial_capital:,.2f}")
    print(f"   Retorno %: {((final_value - initial_capital) / initial_capital) * 100:.2f}%")
    
    # Estadísticas de P&L
    pnl_values = df_trades['net_pnl'].values
    print(f"\n   P&L estadísticas:")
    print(f"   Min: ${pnl_values.min():.2f}")
    print(f"   Max: ${pnl_values.max():.2f}")
    print(f"   Promedio: ${pnl_values.mean():.2f}")
    print(f"   Mediana: ${np.median(pnl_values):.2f}")
    
    # Trades ganadores/perdedores
    winning_trades = df_trades[df_trades['net_pnl'] > 0]
    losing_trades = df_trades[df_trades['net_pnl'] < 0]
    
    print(f"\n   Trades ganadores: {len(winning_trades)} ({len(winning_trades)/len(trades)*100:.1f}%)")
    print(f"   Trades perdedores: {len(losing_trades)} ({len(losing_trades)/len(trades)*100:.1f}%)")
    
    if len(winning_trades) > 0:
        print(f"   Ganancia promedio: ${winning_trades['net_pnl'].mean():.2f}")
    if len(losing_trades) > 0:
        print(f"   Pérdida promedio: ${losing_trades['net_pnl'].mean():.2f}")
    
    # Verificar valores extremos
    extreme_trades = df_trades[abs(df_trades['net_pnl']) > 10000]
    if len(extreme_trades) > 0:
        print(f"\n   ⚠️  Trades con P&L extremo (>$10,000): {len(extreme_trades)}")
        for i, trade in extreme_trades.iterrows():
            print(f"      Trade {i+1}: P&L=${trade['net_pnl']:.2f}, Puntos={trade['raw_points']:.2f}")
    
    return df_trades

def identify_problems():
    """Identificar problemas potenciales en el motor de backtest"""
    print(f"\n🔍 Identificación de Problemas:")
    print("=" * 40)
    
    problems = []
    
    # Problema 1: Limitación de valores
    problems.append({
        'issue': 'Limitación de valores a ±999999',
        'location': 'backtest_engine.py:_safe_decimal()',
        'description': 'El motor limita valores extremos a ±999999 para evitar overflow de base de datos',
        'impact': 'Pérdidas reales de -$1,000,000+ se muestran como -$999,999'
    })
    
    # Problema 2: Cálculo de position size
    problems.append({
        'issue': 'Cálculo de position size',
        'location': 'backtest_engine.py:_position_size()',
        'description': 'El cálculo de position size puede generar cantidades muy grandes',
        'impact': 'Posiciones de 20+ contratos pueden generar P&L extremos'
    })
    
    # Problema 3: Cálculo de P&L
    problems.append({
        'issue': 'Cálculo de P&L para ES',
        'location': 'backtest_engine.py:_process_chunk()',
        'description': 'P&L = puntos * $50 * cantidad, puede ser muy grande',
        'impact': 'Con 20 contratos y 100 puntos de movimiento = $100,000'
    })
    
    # Problema 4: RSI calculation
    problems.append({
        'issue': 'Cálculo de RSI',
        'location': 'backtest_engine.py:_ensure_indicators()',
        'description': 'RSI puede no calcularse correctamente o tener valores NaN',
        'impact': 'Señales de entrada incorrectas o excesivas'
    })
    
    for i, problem in enumerate(problems, 1):
        print(f"\n   {i}. {problem['issue']}")
        print(f"      Ubicación: {problem['location']}")
        print(f"      Descripción: {problem['description']}")
        print(f"      Impacto: {problem['impact']}")
    
    return problems

def main():
    print("🚀 Análisis del Problema de Backtest RSI")
    print("=" * 60)
    
    # Analizar cálculo de RSI
    df, rsi_30, entry_signals = analyze_rsi_calculation()
    
    # Simular lógica de trading
    trades, final_value = simulate_trading_logic(df, rsi_30, entry_signals)
    
    # Analizar trades
    df_trades = analyze_trades(trades, 100000, final_value)
    
    # Identificar problemas
    problems = identify_problems()
    
    print(f"\n" + "=" * 60)
    print("✅ Análisis completado")
    print(f"\n📋 Resumen de problemas identificados:")
    print(f"   1. El motor limita valores a ±999999 (líneas 647-655 en backtest_engine.py)")
    print(f"   2. Position size puede ser muy grande (máximo 20 contratos)")
    print(f"   3. P&L = puntos × $50 × cantidad puede ser extremo")
    print(f"   4. RSI puede generar demasiadas señales de entrada")
    
    print(f"\n🔧 Soluciones recomendadas:")
    print(f"   1. Revisar el cálculo de position size")
    print(f"   2. Implementar límites más realistas de P&L")
    print(f"   3. Mejorar la validación de datos de entrada")
    print(f"   4. Añadir logging detallado para debugging")

if __name__ == "__main__":
    main()
