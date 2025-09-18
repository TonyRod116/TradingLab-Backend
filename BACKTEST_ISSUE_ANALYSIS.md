# Análisis del Problema de Backtest RSI

## Resumen del Problema

Has obtenido resultados de backtest imposibles con una estrategia RSI:
- **Total Return**: -$999,999.00 (-139,269.32%)
- **Win Rate**: 11.9% (1,269/10,666 trades)
- **Max Drawdown**: -$153,302.37 (-153.30%)

## Motor de Backtest

### Ubicación del Código
- **Archivo principal**: `/home/tonirod/code/ga/projects/TradingLab-Backend-Clean/strategies/backtest_engine.py`
- **Calculadora de métricas**: `/home/tonirod/code/ga/projects/TradingLab-Backend-Clean/strategies/metrics_calculator.py`

### Problemas Identificados

#### 1. **Limitación de Valores a ±999,999** (CRÍTICO)
**Ubicación**: `backtest_engine.py`, líneas 647-655
```python
# Limit values to prevent database overflow (max 999999.9999)
if abs(value) > 999999:
    value = 999999 if value > 0 else -999999
```

**Problema**: El motor limita automáticamente cualquier valor mayor a ±999,999 para evitar overflow de la base de datos. Esto significa que pérdidas reales de -$1,000,000+ se muestran como -$999,999.

#### 2. **Cálculo de Position Size Excesivo**
**Ubicación**: `backtest_engine.py`, líneas 987-1016
```python
def _position_size(self, strategy, row, entry_price):
    # ...
    MAX_CONTRACTS = 20  # límite de seguridad en dev
    risk_pct = 0.01  # 1% risk per trade
    # ...
    qty = max(1, int(budget // per_contract_risk))
    return min(qty, MAX_CONTRACTS)
```

**Problema**: Con un stop loss pequeño (ej: 2 puntos) y capital alto ($100,000), el cálculo puede generar hasta 20 contratos, lo que amplifica enormemente el P&L.

#### 3. **Cálculo de P&L para ES**
**Ubicación**: `backtest_engine.py`, líneas 238-249
```python
# P&L monetario correcto para ES (sin doble slippage)
side_sign = 1.0 if current_position['action'] == 'buy' else -1.0
raw_points = (exit_price - current_position['entry_price']) * side_sign

# ES: 1 punto = $50
pnl = raw_points * ES_POINT_VALUE * current_position['quantity']
```

**Problema**: P&L = puntos × $50 × cantidad. Con 20 contratos y 100 puntos de movimiento = $100,000 de P&L.

#### 4. **Cálculo de RSI**
**Ubicación**: `backtest_engine.py`, líneas 907-915
```python
# RSI (Wilder)
delta = close.diff()
up = delta.clip(lower=0); down = -delta.clip(upper=0)
for p in sorted(rsi_ps):
    roll_up = up.ewm(alpha=1/p, adjust=False).mean()
    roll_dn = down.ewm(alpha=1/p, adjust=False).mean()
    rs = roll_up / (roll_dn.replace(0, 1e-12))
    df[f"rsi_{p}"] = 100 - (100/(1+rs))
```

**Problema**: El RSI puede generar demasiadas señales de entrada si no se valida correctamente.

## Datos de Entrada del Backtest

### Estrategia RSI
- **Condición de entrada**: RSI 30 < 30
- **Timeframe**: 30 minutos
- **Símbolo**: ES (E-mini S&P 500)
- **Stop Loss**: 2 puntos
- **Take Profit**: 4 puntos
- **Capital inicial**: $100,000

### Parámetros de ES
- **Valor por punto**: $50
- **Tick size**: 0.25 puntos
- **Comisión**: $4 por round turn
- **Slippage**: 0.5 puntos

## Análisis de Simulación

He creado una simulación con datos realistas que muestra:
- **19 señales de entrada** en 1000 períodos (30min)
- **P&L normal**: entre -$157 y +$168 por trade
- **Retorno realista**: 0.11% en el período de prueba

## Soluciones Recomendadas

### 1. **Eliminar Limitación de Valores**
```python
# En lugar de limitar a ±999999, usar valores reales
def _safe_decimal(self, value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value == float('inf') or value == float('-inf'):
            return Decimal('0')
        if np.isnan(value):
            return Decimal('0')
        # Remover la limitación artificial
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, OverflowError):
        return Decimal('0')
```

### 2. **Revisar Cálculo de Position Size**
```python
def _position_size(self, strategy, row, entry_price):
    # Límites más conservadores
    MAX_CONTRACTS = 5  # Reducir de 20 a 5
    risk_pct = 0.005  # Reducir de 1% a 0.5%
    
    # Validación adicional
    if stop_val <= 0 or stop_val > 50:  # Stop loss máximo 50 puntos
        return 1
```

### 3. **Añadir Validación de Datos**
```python
def _validate_backtest_data(self, df, strategy):
    # Validar que RSI se calculó correctamente
    if 'rsi_30' in df.columns:
        rsi_values = df['rsi_30'].dropna()
        if len(rsi_values) == 0 or rsi_values.isna().all():
            raise ValueError("RSI calculation failed")
    
    # Validar precios realistas
    if df['close'].min() < 1000 or df['close'].max() > 10000:
        raise ValueError("Unrealistic price data")
```

### 4. **Mejorar Logging**
```python
def _process_chunk(self, chunk_df, strategy, ...):
    # Añadir logging detallado
    if len(trades) > 0 and abs(trades[-1]['pnl']) > 10000:
        print(f"WARNING: Large P&L detected: ${trades[-1]['pnl']}")
        print(f"  Position size: {current_position['quantity']}")
        print(f"  Price movement: {raw_points} points")
```

## Archivos para Revisar

1. **`strategies/backtest_engine.py`** - Motor principal
2. **`strategies/metrics_calculator.py`** - Cálculo de métricas
3. **`strategies/models.py`** - Modelos de datos
4. **`market_data/parquet_service.py`** - Servicio de datos

## Próximos Pasos

1. Revisar el cálculo de position size
2. Eliminar la limitación artificial de ±999,999
3. Añadir validación de datos de entrada
4. Implementar logging detallado para debugging
5. Probar con datos reales de ES

El problema principal es que el motor está generando position sizes excesivos (hasta 20 contratos) que, combinados con movimientos de precio normales, generan P&L extremos que luego se limitan artificialmente a ±999,999.
