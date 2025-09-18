# Fixes para Variabilidad en Trades - Basados en ChatGPT

## Problema Identificado
Los trades salían **exactamente iguales** porque:
1. **Sizing fijo** - siempre usaba `strategy.initial_capital`
2. **Salida exacta** - siempre salía al nivel exacto de TP/SL
3. **Comisión fija** - no escalaba con la cantidad
4. **Unidades inconsistentes** - UI enviaba ticks, backend esperaba puntos

## ✅ Cambios Implementados

### 1. **Sizing con Capital Dinámico (Compounding)**
**Archivo**: `strategies/backtest_engine.py`

- **Método `_position_size`**: Ahora usa `current_equity` en lugar de `strategy.initial_capital`
- **Efecto**: El tamaño de posición varía con las ganancias/pérdidas
- **Resultado**: Los P&L ya no serán todos iguales

```python
def _position_size(self, strategy, row, entry_price, current_equity: float):
    # 👉 Compounding: usa el equity actual, no el inicial
    budget = float(current_equity) * risk_pct
    qty = max(1, int(budget // per_contract_risk))
    return min(qty, MAX_CONTRACTS)
```

### 2. **Salidas Intra-barra con High/Low**
**Archivo**: `strategies/backtest_engine.py`

- **Método `_check_exit_conditions`**: Ahora usa `high/low` para determinar salidas
- **Política de prioridad**: Si ambos se tocan, prioriza Stop Loss
- **Slippage aplicado**: Se aplica al precio de salida real

```python
def _check_exit_conditions(self, row, position, exit_rules, ...):
    # Usa high/low para determinar si se tocó TP/SL
    # Prioriza Stop Loss si ambos se tocan
    # Aplica slippage al precio real de salida
```

### 3. **Comisión por Contrato**
**Archivo**: `strategies/backtest_engine.py`

- **Cálculo**: `trade_commission = float(commission) * int(current_position['quantity'])`
- **Efecto**: La comisión escala con la cantidad de contratos
- **Resultado**: Trades con más contratos pagan más comisión

### 4. **Unidades de Slippage Consistentes**
**Frontend**: Convierte ticks a puntos antes de enviar
- **StrategyCreator.jsx**: `slippage: strategyData.slippage * 0.25`
- **StrategyCreator2.jsx**: `slippage: strategyData.slippage * 0.25`
- **StrategyDetails.jsx**: `slippage: 0.25 * 0.25`

**Backend**: Mantiene `_apply_slippage` en puntos

## 🎯 Resultados Esperados

### **Variabilidad en Trades**
- **Tamaño variable**: 1-5 contratos según equity actual
- **Precios de salida variables**: No siempre exacto TP/SL
- **Comisión variable**: Escala con cantidad
- **P&L variable**: Ya no todos iguales

### **Métricas Realistas**
- **Average Win/Loss**: Variará según el tamaño de posición
- **Total Return**: Más realista con compounding
- **Max Drawdown**: Reflejará la variabilidad real

## 🚀 Próximo Paso

**Ejecuta tu backtest de RSI nuevamente**. Ahora deberías ver:

1. **Trades variables**: Diferentes cantidades y P&L
2. **Logs de debugging**: Mostrarán la variabilidad real
3. **Métricas realistas**: No más valores exactamente iguales

### **Verificación**
- **Logs**: Verás diferentes cantidades y precios de salida
- **P&L por trade**: Debería variar según el tamaño de posición
- **Curva de equity**: Debería mostrar crecimiento/declive realista

**¡El motor de backtest ahora debería generar trades realistas y variables!**
