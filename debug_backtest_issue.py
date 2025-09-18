#!/usr/bin/env python3
"""
Debug específico para identificar por qué los resultados siguen siendo imposibles
"""

import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta

def debug_slippage_issue():
    """Debug del problema de slippage"""
    print("🔍 Debug del Problema de Slippage")
    print("=" * 50)
    
    # Simular el método actual
    def apply_slippage_current(price: float, slippage: Decimal, action: str) -> float:
        s = float(slippage or 0.0)
        return price + s if action == 'buy' else price - s
    
    # Simular el método viejo (incorrecto)
    def apply_slippage_old(price: float, slippage: Decimal, action: str) -> float:
        slippage_factor = float(slippage) / 100
        if action == 'buy':
            return price * (1 + slippage_factor)
        else:
            return price * (1 - slippage_factor)
    
    # Test con valores típicos
    price = 4500.0
    slippage_values = [0.25, 0.5, 1.0, 2.0]
    
    print(f"Precio base: ${price}")
    print(f"Slippage | Acción | Método Actual | Método Viejo | Diferencia")
    print("-" * 60)
    
    for slippage in slippage_values:
        for action in ['buy', 'sell']:
            current = apply_slippage_current(price, Decimal(str(slippage)), action)
            old = apply_slippage_old(price, Decimal(str(slippage)), action)
            diff = abs(current - old)
            print(f"{slippage:>8} | {action:>6} | ${current:>12.2f} | ${old:>12.2f} | ${diff:>9.2f}")

def debug_pnl_calculation():
    """Debug del cálculo de P&L"""
    print(f"\n🔍 Debug del Cálculo de P&L")
    print("=" * 50)
    
    # Simular trade con parámetros típicos
    entry_price = 4500.0
    exit_price = 4504.0  # +4 puntos (TP)
    quantity = 5  # 5 contratos
    commission = 4.0
    
    # Cálculo correcto
    side_sign = 1.0  # buy
    raw_points = (exit_price - entry_price) * side_sign
    ES_POINT_VALUE = 50.0
    pnl = raw_points * ES_POINT_VALUE * quantity
    net_pnl = pnl - commission
    
    print(f"Trade de ejemplo:")
    print(f"  Entry: ${entry_price}")
    print(f"  Exit: ${exit_price}")
    print(f"  Movimiento: {raw_points} puntos")
    print(f"  Cantidad: {quantity} contratos")
    print(f"  P&L: {raw_points} × ${ES_POINT_VALUE} × {quantity} = ${pnl}")
    print(f"  Comisión: ${commission}")
    print(f"  Net P&L: ${net_pnl}")
    
    # ¿Qué pasaría con 20 contratos?
    quantity_20 = 20
    pnl_20 = raw_points * ES_POINT_VALUE * quantity_20
    net_pnl_20 = pnl_20 - commission
    
    print(f"\nCon 20 contratos:")
    print(f"  P&L: {raw_points} × ${ES_POINT_VALUE} × {quantity_20} = ${pnl_20}")
    print(f"  Net P&L: ${net_pnl_20}")

def debug_position_sizing():
    """Debug del position sizing"""
    print(f"\n🔍 Debug del Position Sizing")
    print("=" * 50)
    
    def position_size_corrected(strategy, entry_price):
        ES_POINT_VALUE = 50.0
        MAX_CONTRACTS = 5
        risk_pct = 0.005  # 0.5%
        
        stop_type = getattr(strategy, "stop_loss_type", "points")
        stop_val = float(getattr(strategy, "stop_loss_value", 0) or 0)
        
        if stop_val <= 0:
            return 1
        
        ES_TICK = 0.25
        if stop_type == "percentage":
            sl_points = entry_price * (stop_val / 100.0)
        elif stop_type == "points":
            sl_points = stop_val
        elif stop_type == "ticks":
            sl_points = stop_val * ES_TICK
        else:
            sl_points = stop_val
        
        if sl_points <= 0 or sl_points > 50:
            return 1
        
        per_contract_risk = sl_points * ES_POINT_VALUE
        if per_contract_risk <= 0:
            return 1
        
        budget = float(strategy.initial_capital) * risk_pct
        qty = max(1, int(budget // per_contract_risk))
        return min(qty, MAX_CONTRACTS)
    
    class MockStrategy:
        def __init__(self, stop_loss_type, stop_loss_value, initial_capital):
            self.stop_loss_type = stop_loss_type
            self.stop_loss_value = stop_loss_value
            self.initial_capital = initial_capital
    
    # Test cases
    test_cases = [
        ("points", 2.0, 100000),  # 2 puntos SL
        ("points", 1.0, 100000),  # 1 punto SL
        ("points", 0.5, 100000),  # 0.5 puntos SL
        ("ticks", 8, 100000),     # 8 ticks = 2 puntos
    ]
    
    print(f"Position Sizing con parámetros corregidos:")
    print(f"SL Tipo | SL Valor | Capital | Contratos | Riesgo por contrato | Presupuesto")
    print("-" * 80)
    
    for stop_type, stop_val, capital in test_cases:
        strategy = MockStrategy(stop_type, stop_val, capital)
        qty = position_size_corrected(strategy, 4500.0)
        
        # Calcular riesgo por contrato
        if stop_type == "points":
            sl_points = stop_val
        elif stop_type == "ticks":
            sl_points = stop_val * 0.25
        else:
            sl_points = stop_val
        
        per_contract_risk = sl_points * 50.0
        budget = capital * 0.005
        
        print(f"{stop_type:>7} | {stop_val:>8} | ${capital:>6,} | {qty:>9} | ${per_contract_risk:>18.2f} | ${budget:>10.2f}")

def debug_impossible_trades():
    """Debug para identificar trades imposibles"""
    print(f"\n🔍 Debug de Trades Imposibles")
    print("=" * 50)
    
    # Con TP=4, SL=2, slippage=0.25, el movimiento máximo debería ser:
    tp_points = 4.0
    sl_points = 2.0
    slippage = 0.25
    
    max_expected = max(tp_points, sl_points) + 2 * slippage + 0.25
    print(f"Con TP={tp_points}, SL={sl_points}, slippage={slippage}:")
    print(f"  Movimiento máximo esperado: {max_expected} puntos")
    print(f"  P&L máximo esperado (1 contrato): {max_expected * 50} dólares")
    print(f"  P&L máximo esperado (5 contratos): {max_expected * 50 * 5} dólares")
    
    # ¿Qué pasaría si el slippage fuera porcentaje?
    slippage_percent = 0.5  # 0.5%
    slippage_points = 4500 * (slippage_percent / 100)  # ≈ 22.5 puntos
    max_expected_wrong = max(tp_points, sl_points) + 2 * slippage_points + 0.25
    print(f"\nSi slippage fuera porcentaje (0.5% = {slippage_points:.1f} puntos):")
    print(f"  Movimiento máximo esperado: {max_expected_wrong} puntos")
    print(f"  P&L máximo esperado (1 contrato): {max_expected_wrong * 50} dólares")
    print(f"  P&L máximo esperado (5 contratos): {max_expected_wrong * 50 * 5} dólares")

def debug_actual_results():
    """Debug de los resultados actuales"""
    print(f"\n🔍 Debug de Resultados Actuales")
    print("=" * 50)
    
    # Datos de la imagen
    total_trades = 5888
    winning_trades = 2698
    losing_trades = 3190
    avg_win = 181486.18
    avg_loss = -190986.23
    largest_win = 1201621.00
    largest_loss = -1439566.50
    
    print(f"Resultados actuales:")
    print(f"  Total trades: {total_trades}")
    print(f"  Winning trades: {winning_trades}")
    print(f"  Losing trades: {losing_trades}")
    print(f"  Average win: ${avg_win:,.2f}")
    print(f"  Average loss: ${avg_loss:,.2f}")
    print(f"  Largest win: ${largest_win:,.2f}")
    print(f"  Largest loss: ${largest_loss:,.2f}")
    
    # Calcular puntos necesarios para estos P&L
    print(f"\nAnálisis de puntos necesarios:")
    print(f"  Para average win ${avg_win:,.2f} con 5 contratos:")
    print(f"    Puntos necesarios: {avg_win / (50 * 5):.1f}")
    print(f"  Para average loss ${avg_loss:,.2f} con 5 contratos:")
    print(f"    Puntos necesarios: {abs(avg_loss) / (50 * 5):.1f}")
    print(f"  Para largest win ${largest_win:,.2f} con 5 contratos:")
    print(f"    Puntos necesarios: {largest_win / (50 * 5):.1f}")
    print(f"  Para largest loss ${largest_loss:,.2f} con 5 contratos:")
    print(f"    Puntos necesarios: {abs(largest_loss) / (50 * 5):.1f}")
    
    print(f"\n❌ CONCLUSIÓN: Estos movimientos son imposibles con TP=4, SL=2")
    print(f"   El problema está en el slippage o en el position sizing")

def main():
    print("🚀 Debug del Problema de Backtest")
    print("=" * 60)
    
    debug_slippage_issue()
    debug_pnl_calculation()
    debug_position_sizing()
    debug_impossible_trades()
    debug_actual_results()
    
    print(f"\n" + "=" * 60)
    print("🎯 DIAGNÓSTICO:")
    print("   1. Los resultados actuales son imposibles con TP=4, SL=2")
    print("   2. Los P&L sugieren movimientos de 700+ puntos por trade")
    print("   3. El problema está en slippage o position sizing")
    print("   4. Necesitamos verificar que los parches se aplicaron correctamente")

if __name__ == "__main__":
    main()
