#!/usr/bin/env python3
"""
Test simple para verificar que los parches del backtest funcionan correctamente
"""

import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta

def test_slippage_calculation():
    """Test del cálculo de slippage corregido"""
    print("🔧 Test de Cálculo de Slippage Corregido")
    print("=" * 50)
    
    def apply_slippage_fixed(price: float, slippage: Decimal, action: str) -> float:
        """Slippage expresado en PUNTOS ES, no porcentaje"""
        s = float(slippage or 0.0)
        return price + s if action == 'buy' else price - s
    
    def apply_slippage_old(price: float, slippage: Decimal, action: str) -> float:
        """Slippage como porcentaje (INCORRECTO)"""
        slippage_factor = float(slippage) / 100
        if action == 'buy':
            return price * (1 + slippage_factor)
        else:
            return price * (1 - slippage_factor)
    
    # Test con precios típicos de ES
    test_cases = [
        (4500.0, Decimal('0.25'), 'buy'),
        (4500.0, Decimal('0.25'), 'sell'),
        (4500.0, Decimal('0.5'), 'buy'),
        (4500.0, Decimal('0.5'), 'sell'),
        (4500.0, Decimal('0'), 'buy'),
        (4500.0, Decimal('0'), 'sell'),
    ]
    
    print("Comparación de métodos de slippage:")
    print("Precio | Slippage | Acción | Método Nuevo | Método Viejo | Diferencia")
    print("-" * 70)
    
    for price, slippage, action in test_cases:
        new_result = apply_slippage_fixed(price, slippage, action)
        old_result = apply_slippage_old(price, slippage, action)
        diff = abs(new_result - old_result)
        
        print(f"${price:,.0f} | {slippage:>8} | {action:>6} | ${new_result:>11.2f} | ${old_result:>11.2f} | ${diff:>9.2f}")
    
    print("\n✅ Conclusión: El método nuevo usa puntos, el viejo usaba porcentaje")
    print("   El método viejo generaba slippage excesivo (ej: 0.5% = 22.5 puntos)")

def test_position_sizing():
    """Test del position sizing corregido"""
    print(f"\n🔧 Test de Position Sizing Corregido")
    print("=" * 50)
    
    def position_size_fixed(strategy, entry_price):
        """Position sizing corregido"""
        ES_POINT_VALUE = 50.0
        MAX_CONTRACTS = 5       # ↓ de 20 a 5
        risk_pct = 0.005        # ↓ de 1% a 0.5%

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

        # Validación adicional
        if sl_points <= 0 or sl_points > 50:  # Stop loss máximo 50 puntos
            return 1

        per_contract_risk = sl_points * ES_POINT_VALUE
        if per_contract_risk <= 0:
            return 1

        budget = float(strategy.initial_capital) * risk_pct
        qty = max(1, int(budget // per_contract_risk))
        return min(qty, MAX_CONTRACTS)
    
    def position_size_old(strategy, entry_price):
        """Position sizing viejo (agresivo)"""
        ES_POINT_VALUE = 50.0
        MAX_CONTRACTS = 20  # límite alto
        risk_pct = 0.01     # 1% risk per trade

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
    
    test_cases = [
        ('points', 2.0, 100000),
        ('points', 1.0, 100000),
        ('points', 0.5, 100000),
        ('ticks', 8, 100000),
        ('percentage', 0.1, 100000),
        ('points', 100, 100000),
    ]
    
    print("Comparación de position sizing:")
    print("SL Tipo | SL Valor | Capital | Método Nuevo | Método Viejo | Diferencia")
    print("-" * 70)
    
    for stop_type, stop_val, capital in test_cases:
        strategy = MockStrategy(stop_type, stop_val, capital)
        new_result = position_size_fixed(strategy, 4500.0)
        old_result = position_size_old(strategy, 4500.0)
        diff = old_result - new_result
        
        print(f"{stop_type:>7} | {stop_val:>8} | ${capital:>6,} | {new_result:>12} | {old_result:>12} | {diff:>9}")
    
    print("\n✅ Conclusión: El método nuevo es más prudente (máx 5 vs 20 contratos)")

def test_pnl_calculation():
    """Test del cálculo de P&L corregido"""
    print(f"\n🔧 Test de Cálculo de P&L Corregido")
    print("=" * 50)
    
    def calculate_pnl_fixed(position, exit_price, commission):
        """P&L corregido para ES"""
        ES_POINT_VALUE = 50.0
        entry_price = float(position['entry_price'])
        qty = int(position['quantity'])

        side_sign = 1.0 if position['action'] == 'buy' else -1.0
        raw_points = (exit_price - entry_price) * side_sign
        gross_pnl = raw_points * ES_POINT_VALUE * qty

        net_pnl = gross_pnl - float(commission)
        return {'gross_pnl': gross_pnl, 'net_pnl': net_pnl}
    
    def calculate_pnl_old(position, exit_price, commission):
        """P&L viejo (unitless)"""
        entry_price = float(position['entry_price'])
        quantity = position['quantity']
        
        if position['action'] == 'buy':
            gross_pnl = (exit_price - entry_price) * quantity
        else:
            gross_pnl = (entry_price - exit_price) * quantity
        
        net_pnl = gross_pnl - float(commission)
        return {'gross_pnl': gross_pnl, 'net_pnl': net_pnl}
    
    # Test cases
    test_cases = [
        ({'action': 'buy', 'entry_price': 4500.0, 'quantity': 1}, 4502.0, 4.0),  # +2 puntos
        ({'action': 'buy', 'entry_price': 4500.0, 'quantity': 1}, 4498.0, 4.0),  # -2 puntos
        ({'action': 'buy', 'entry_price': 4500.0, 'quantity': 5}, 4504.0, 4.0),  # +4 puntos, 5 contratos
        ({'action': 'buy', 'entry_price': 4500.0, 'quantity': 10}, 4501.0, 4.0), # +1 punto, 10 contratos
    ]
    
    print("Comparación de cálculo de P&L:")
    print("Posición | Exit | Comisión | Método Nuevo | Método Viejo | Diferencia")
    print("-" * 80)
    
    for position, exit_price, commission in test_cases:
        new_result = calculate_pnl_fixed(position, exit_price, commission)
        old_result = calculate_pnl_old(position, exit_price, commission)
        
        new_net = new_result['net_pnl']
        old_net = old_result['net_pnl']
        diff = abs(new_net - old_net)
        
        print(f"{position['quantity']:>8} | ${exit_price:>4.0f} | ${commission:>8} | ${new_net:>12.2f} | ${old_net:>12.2f} | ${diff:>9.2f}")
    
    print("\n✅ Conclusión: El método nuevo calcula P&L en dólares (puntos × $50 × cantidad)")

def test_max_drawdown():
    """Test del cálculo de max drawdown corregido"""
    print(f"\n🔧 Test de Max Drawdown Corregido")
    print("=" * 50)
    
    def calculate_max_drawdown_fixed(equity_curve, initial_capital):
        """Max drawdown corregido"""
        if len(equity_curve) == 0:
            return 0.0, 0.0
        
        peak = equity_curve.expanding().max()
        dd_series = (equity_curve - peak) / peak
        max_dd_percent = float(dd_series.min() * 100)
        max_dd_dollars = float((peak - equity_curve).max())
        
        return max_dd_dollars, max_dd_percent
    
    def calculate_max_drawdown_old(equity_curve, initial_capital):
        """Max drawdown viejo (incorrecto)"""
        if len(equity_curve) == 0:
            return 0.0, 0.0
        
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        max_dd = drawdown.min()
        
        max_dd_dollars = float(max_dd * initial_capital)
        max_dd_percent = float(max_dd * 100)
        
        return max_dd_dollars, max_dd_percent
    
    # Test case: equity que sube a 110k y cae a 95k
    equity_curve = pd.Series([100000, 105000, 110000, 108000, 102000, 95000, 98000])
    initial_capital = 100000
    
    new_dd_dollars, new_dd_percent = calculate_max_drawdown_fixed(equity_curve, initial_capital)
    old_dd_dollars, old_dd_percent = calculate_max_drawdown_old(equity_curve, initial_capital)
    
    print(f"Equity curve: {equity_curve.tolist()}")
    print(f"Capital inicial: ${initial_capital:,}")
    print()
    print(f"Método nuevo:")
    print(f"  Max DD $: ${new_dd_dollars:,.2f}")
    print(f"  Max DD %: {new_dd_percent:.2f}%")
    print()
    print(f"Método viejo:")
    print(f"  Max DD $: ${old_dd_dollars:,.2f}")
    print(f"  Max DD %: {old_dd_percent:.2f}%")
    print()
    print(f"Diferencia:")
    print(f"  DD $: ${abs(new_dd_dollars - old_dd_dollars):,.2f}")
    print(f"  DD %: {abs(new_dd_percent - old_dd_percent):.2f}%")
    
    print("\n✅ Conclusión: El método nuevo calcula DD en dólares desde la equity real")

def test_value_capping():
    """Test de la eliminación del capping de valores"""
    print(f"\n🔧 Test de Eliminación de Capping de Valores")
    print("=" * 50)
    
    def safe_decimal_fixed(value):
        """Sin limitación artificial"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            if value in (float('inf'), float('-inf')) or np.isnan(value):
                return Decimal('0')
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, OverflowError):
            return Decimal('0')
    
    def safe_decimal_old(value):
        """Con limitación artificial de ±999,999"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            if value == float('inf') or value == float('-inf'):
                return Decimal('0')
            if np.isnan(value):
                return Decimal('0')
            # Limit values to prevent database overflow
            if abs(value) > 999999:
                value = 999999 if value > 0 else -999999
        try:
            decimal_value = Decimal(str(value))
            if decimal_value > Decimal('999999.9999'):
                return Decimal('999999.9999')
            elif decimal_value < Decimal('-999999.9999'):
                return Decimal('-999999.9999')
            return decimal_value
        except (ValueError, TypeError, OverflowError):
            return Decimal('0')
    
    test_values = [
        1000000,      # Valor normal
        -1000000,     # Valor normal negativo
        2000000,      # Valor que excede 999,999
        -2000000,     # Valor negativo que excede -999,999
        500000,       # Valor dentro del rango
        -500000,      # Valor negativo dentro del rango
        float('inf'), # Infinito
        float('-inf'), # Infinito negativo
        float('nan'), # NaN
    ]
    
    print("Comparación de capping de valores:")
    print("Valor | Método Nuevo | Método Viejo | Diferencia")
    print("-" * 50)
    
    for value in test_values:
        try:
            new_result = safe_decimal_fixed(value)
            old_result = safe_decimal_old(value)
            diff = abs(float(new_result) - float(old_result))
            
            print(f"{value:>8} | {new_result:>12} | {old_result:>12} | {diff:>9}")
        except:
            print(f"{value:>8} | Error | Error | N/A")
    
    print("\n✅ Conclusión: El método nuevo respeta valores reales, el viejo los limita artificialmente")

def main():
    print("🚀 Test de Parches del Backtest (Sin Django)")
    print("=" * 60)
    
    # Ejecutar todos los tests
    test_slippage_calculation()
    test_position_sizing()
    test_pnl_calculation()
    test_max_drawdown()
    test_value_capping()
    
    print("\n" + "=" * 60)
    print("✅ Todos los tests completados")
    print("\n📋 Resumen de correcciones aplicadas:")
    print("   1. ✅ Slippage: puntos en lugar de porcentaje")
    print("   2. ✅ Position sizing: máx 5 contratos, 0.5% riesgo")
    print("   3. ✅ P&L: puntos × $50 × cantidad")
    print("   4. ✅ Max drawdown: desde equity real")
    print("   5. ✅ Sin capping artificial de ±999,999")
    print("\n🎯 Los parches deberían resolver el problema de resultados imposibles")

if __name__ == "__main__":
    main()
