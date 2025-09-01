# Strategy Rule Builder API Documentation

## Descripción General

El Strategy Rule Builder es un sistema completo para crear, gestionar y ejecutar estrategias de trading automatizadas. Permite a los usuarios construir estrategias complejas usando un motor de reglas basado en indicadores técnicos, acción de precio y volumen.

## Estructura de la API

### Base URL
```
/api/strategies/
```

## Endpoints Principales

### 1. Gestión de Estrategias

#### Listar Estrategias
```http
GET /api/strategies/strategies/
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Moving Average Crossover",
    "description": "Estrategia de cruce de medias móviles",
    "strategy_type": "trend_following",
    "status": "active",
    "symbol": "ES",
    "timeframe": "1m",
    "position_size": "1.00",
    "max_positions": 1,
    "stop_loss_pips": 50,
    "take_profit_pips": 100,
    "total_trades": 25,
    "winning_trades": 18,
    "losing_trades": 7,
    "win_rate": "72.00",
    "profit_factor": "2.15",
    "max_drawdown": "8.50",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T15:45:00Z"
  }
]
```

#### Crear Estrategia
```http
POST /api/strategies/strategies/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Mi Estrategia",
  "description": "Descripción de la estrategia",
  "strategy_type": "custom",
  "symbol": "ES",
  "timeframe": "1m",
  "position_size": "1.00",
  "max_positions": 1,
  "stop_loss_pips": 50,
  "take_profit_pips": 100,
  "backtest_enabled": true
}
```

#### Crear desde Plantilla
```http
POST /api/strategies/create-from-template/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "template_name": "Moving Average Crossover",
  "name": "Mi MA Crossover",
  "description": "Versión personalizada",
  "symbol": "ES",
  "timeframe": "5m"
}
```

#### Obtener Plantillas Disponibles
```http
GET /api/strategies/templates/
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "name": "Moving Average Crossover",
    "description": "Estrategia de cruce de medias móviles",
    "strategy_type": "trend_following",
    "rules": [
      {
        "name": "SMA 20 > SMA 50",
        "rule_type": "condition",
        "condition_type": "indicator",
        "left_operand": "sma_20",
        "operator": "gt",
        "right_operand": "sma_50",
        "priority": 1,
        "order": 1
      },
      {
        "name": "Buy Signal",
        "rule_type": "action",
        "action_type": "buy",
        "priority": 2,
        "order": 1
      }
    ]
  }
]
```

### 2. Gestión de Reglas

#### Listar Reglas de una Estrategia
```http
GET /api/strategies/strategies/{strategy_id}/rules/
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "SMA 20 > SMA 50",
    "rule_type": "condition",
    "condition_type": "indicator",
    "action_type": null,
    "parameters": {},
    "left_operand": "sma_20",
    "operator": "gt",
    "right_operand": "sma_50",
    "logical_operator": "and",
    "priority": 1,
    "order": 1,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

#### Crear Nueva Regla
```http
POST /api/strategies/strategies/{strategy_id}/rules/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "RSI < 30",
  "rule_type": "condition",
  "condition_type": "indicator",
  "left_operand": "rsi",
  "operator": "lt",
  "right_operand": "30",
  "priority": 1,
  "order": 1,
  "is_active": true
}
```

#### Actualizar Regla
```http
PUT /api/strategies/strategies/{strategy_id}/rules/{rule_id}/
Authorization: Bearer <token>
Content-Type: application/json
```

#### Activar/Desactivar Regla
```http
POST /api/strategies/strategies/{strategy_id}/rules/{rule_id}/toggle_active/
Authorization: Bearer <token>
```

#### Mover Regla (Prioridad)
```http
POST /api/strategies/strategies/{strategy_id}/rules/{rule_id}/move_up/
POST /api/strategies/strategies/{strategy_id}/rules/{rule_id}/move_down/
Authorization: Bearer <token>
```

### 3. Rule Builder

#### Indicadores Disponibles
```http
GET /api/strategies/strategies/{strategy_id}/rule-builder/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "price_indicators": [
    {"name": "close_price", "label": "Close Price", "type": "price"},
    {"name": "open_price", "label": "Open Price", "type": "price"},
    {"name": "high_price", "label": "High Price", "type": "price"},
    {"name": "low_price", "label": "Low Price", "type": "price"},
    {"name": "volume", "label": "Volume", "type": "volume"}
  ],
  "trend_indicators": [
    {"name": "sma_20", "label": "SMA 20", "type": "trend", "parameters": {"period": 20}},
    {"name": "sma_50", "label": "SMA 50", "type": "trend", "parameters": {"period": 50}},
    {"name": "ema_20", "label": "EMA 20", "type": "trend", "parameters": {"period": 20}},
    {"name": "ema_50", "label": "EMA 50", "type": "trend", "parameters": {"period": 50}},
    {"name": "vwap", "label": "VWAP", "type": "trend"}
  ],
  "momentum_indicators": [
    {"name": "rsi", "label": "RSI", "type": "momentum", "parameters": {"period": 14}},
    {"name": "macd_line", "label": "MACD Line", "type": "momentum"},
    {"name": "macd_signal", "label": "MACD Signal", "type": "momentum"},
    {"name": "macd_histogram", "label": "MACD Histogram", "type": "momentum"},
    {"name": "stoch_k", "label": "Stochastic %K", "type": "momentum"},
    {"name": "stoch_d", "label": "Stochastic %D", "type": "momentum"}
  ],
  "volatility_indicators": [
    {"name": "atr", "label": "ATR", "type": "volatility", "parameters": {"period": 14}},
    {"name": "bb_upper", "label": "Bollinger Bands Upper", "type": "volatility"},
    {"name": "bb_middle", "label": "Bollinger Bands Middle", "type": "volatility"},
    {"name": "bb_lower", "label": "Bollinger Bands Lower", "type": "volatility"}
  ]
}
```

#### Operadores Disponibles
```http
GET /api/strategies/strategies/{strategy_id}/rule-builder/operators/
Authorization: Bearer <token>
```

**Response:**
```json
[
  {"value": "gt", "label": "Greater Than >", "description": "Mayor que"},
  {"value": "gte", "label": "Greater Than or Equal >=", "description": "Mayor o igual que"},
  {"value": "lt", "label": "Less Than <", "description": "Menor que"},
  {"value": "lte", "label": "Less Than or Equal <=", "description": "Menor o igual que"},
  {"value": "eq", "label": "Equal ==", "description": "Igual a"},
  {"value": "ne", "label": "Not Equal !=", "description": "Diferente de"},
  {"value": "crosses_above", "label": "Crosses Above", "description": "Cruza por encima"},
  {"value": "crosses_below", "label": "Crosses Below", "description": "Cruza por debajo"},
  {"value": "above", "label": "Above", "description": "Por encima de"},
  {"value": "below", "label": "Below", "description": "Por debajo de"}
]
```

#### Acciones Disponibles
```http
GET /api/strategies/strategies/{strategy_id}/rule-builder/actions/
Authorization: Bearer <token>
```

**Response:**
```json
[
  {"value": "buy", "label": "Buy", "description": "Comprar"},
  {"value": "sell", "label": "Sell", "description": "Vender"},
  {"value": "close", "label": "Close Position", "description": "Cerrar posición"},
  {"value": "modify", "label": "Modify Position", "description": "Modificar posición"},
  {"value": "wait", "label": "Wait", "description": "Esperar"}
]
```

#### Probar Regla
```http
POST /api/strategies/strategies/{strategy_id}/rule-builder/test/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "rule": {
    "name": "Test RSI Rule",
    "rule_type": "condition",
    "condition_type": "indicator",
    "left_operand": "rsi",
    "operator": "lt",
    "right_operand": "30",
    "logical_operator": "and"
  }
}
```

**Response:**
```json
{
  "rule_name": "Test RSI Rule",
  "rule_type": "condition",
  "test_passed": true,
  "message": "Regla válida y lista para usar",
  "suggestions": []
}
```

### 4. Backtesting

#### Ejecutar Backtest
```http
POST /api/strategies/strategies/{strategy_id}/backtest/run/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "initial_capital": 10000.00,
  "commission": 0.00,
  "slippage": 0.00
}
```

**Response:**
```json
{
  "strategy_id": 1,
  "strategy_name": "Moving Average Crossover",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "initial_capital": 10000.00,
  "final_capital": 11250.00,
  "total_return": 12.50,
  "total_trades": 25,
  "winning_trades": 18,
  "losing_trades": 7,
  "win_rate": 72.00,
  "profit_factor": 2.15,
  "max_drawdown": 8.50,
  "trades": [],
  "equity_curve": [],
  "execution_time": 2.45
}
```

#### Historial de Backtests
```http
GET /api/strategies/strategies/{strategy_id}/backtest/history/
Authorization: Bearer <token>
```

### 5. Gestión de Estado

#### Activar Estrategia
```http
POST /api/strategies/strategies/{strategy_id}/activate/
Authorization: Bearer <token>
```

#### Pausar Estrategia
```http
POST /api/strategies/strategies/{strategy_id}/pause/
Authorization: Bearer <token>
```

#### Archivar Estrategia
```http
POST /api/strategies/strategies/{strategy_id}/archive/
Authorization: Bearer <token>
```

#### Métricas de Rendimiento
```http
GET /api/strategies/strategies/{strategy_id}/performance/
Authorization: Bearer <token>
```

### 6. Ejecuciones

#### Últimas Ejecuciones
```http
GET /api/strategies/strategies/{strategy_id}/executions/latest/
Authorization: Bearer <token>
```

#### Ejecuciones Fallidas
```http
GET /api/strategies/strategies/{strategy_id}/executions/failed/
Authorization: Bearer <token>
```

## Tipos de Reglas

### 1. Reglas de Condición
Las reglas de condición evalúan si se cumplen ciertas condiciones en el mercado:

```json
{
  "name": "RSI Oversold",
  "rule_type": "condition",
  "condition_type": "indicator",
  "left_operand": "rsi",
  "operator": "lt",
  "right_operand": "30",
  "logical_operator": "and",
  "priority": 1,
  "order": 1
}
```

### 2. Reglas de Acción
Las reglas de acción definen qué hacer cuando se cumplen las condiciones:

```json
{
  "name": "Buy Signal",
  "rule_type": "action",
  "action_type": "buy",
  "parameters": {
    "position_size": "1.00",
    "stop_loss": "50",
    "take_profit": "100"
  },
  "priority": 2,
  "order": 1
}
```

### 3. Reglas de Filtro
Las reglas de filtro pueden modificar o cancelar acciones:

```json
{
  "name": "Volume Filter",
  "rule_type": "filter",
  "condition_type": "volume",
  "left_operand": "volume",
  "operator": "gt",
  "right_operand": "avg_volume_20",
  "priority": 1,
  "order": 2
}
```

## Ejemplos de Estrategias

### 1. Moving Average Crossover
```json
{
  "name": "MA Crossover Strategy",
  "strategy_type": "trend_following",
  "rules": [
    {
      "name": "SMA 20 > SMA 50",
      "rule_type": "condition",
      "condition_type": "indicator",
      "left_operand": "sma_20",
      "operator": "gt",
      "right_operand": "sma_50",
      "priority": 1,
      "order": 1
    },
    {
      "name": "Buy Signal",
      "rule_type": "action",
      "action_type": "buy",
      "priority": 2,
      "order": 1
    }
  ]
}
```

### 2. RSI Mean Reversion
```json
{
  "name": "RSI Mean Reversion",
  "strategy_type": "mean_reversion",
  "rules": [
    {
      "name": "RSI < 30",
      "rule_type": "condition",
      "condition_type": "indicator",
      "left_operand": "rsi",
      "operator": "lt",
      "right_operand": "30",
      "priority": 1,
      "order": 1
    },
    {
      "name": "Buy Signal",
      "rule_type": "action",
      "action_type": "buy",
      "priority": 2,
      "order": 1
    }
  ]
}
```

### 3. Breakout Strategy
```json
{
  "name": "Breakout Strategy",
  "strategy_type": "breakout",
  "rules": [
    {
      "name": "Price > High 20",
      "rule_type": "condition",
      "condition_type": "price",
      "left_operand": "close_price",
      "operator": "gt",
      "right_operand": "high_20",
      "priority": 1,
      "order": 1
    },
    {
      "name": "Volume > Avg Volume",
      "rule_type": "condition",
      "condition_type": "volume",
      "left_operand": "volume",
      "operator": "gt",
      "right_operand": "avg_volume_20",
      "priority": 1,
      "order": 2
    },
    {
      "name": "Buy Signal",
      "rule_type": "action",
      "action_type": "buy",
      "priority": 2,
      "order": 1
    }
  ]
}
```

## Implementación del Frontend

### 1. Estructura del Rule Builder

El frontend debe implementar un interface que permita:

1. **Selector de Indicadores**: Dropdown con todos los indicadores disponibles
2. **Selector de Operadores**: Dropdown con operadores de comparación
3. **Campo de Valor**: Input para el valor de comparación
4. **Gestor de Prioridades**: Sistema para ordenar reglas
5. **Preview de Reglas**: Vista previa de cómo se verá la regla
6. **Testing de Reglas**: Botón para probar reglas antes de guardar

### 2. Flujo de Creación

1. Usuario selecciona "Crear Nueva Estrategia"
2. Completa información básica (nombre, descripción, símbolo, timeframe)
3. Agrega reglas usando el rule builder:
   - Selecciona tipo de regla (condición, acción, filtro)
   - Configura parámetros de la regla
   - Define prioridad y orden
4. Guarda la estrategia
5. Opcionalmente ejecuta un backtest

### 3. Validaciones

- Las reglas de condición deben tener operando izquierdo, operador y operando derecho
- Las reglas de acción deben tener un tipo de acción válido
- Las prioridades deben ser únicas dentro de una estrategia
- Al menos debe haber una regla de condición y una de acción

### 4. Estados de la Estrategia

- **Draft**: En construcción, no se ejecuta
- **Active**: Activa y ejecutándose
- **Paused**: Pausada temporalmente
- **Archived**: Archivada, no se puede ejecutar

## Consideraciones Técnicas

### 1. Autenticación
Todas las endpoints requieren autenticación JWT:
```http
Authorization: Bearer <token>
```

### 2. Paginación
Para endpoints que retornan listas, considerar implementar paginación:
```json
{
  "count": 100,
  "next": "http://api.example.com/strategies/?page=2",
  "previous": null,
  "results": [...]
}
```

### 3. Filtros
Implementar filtros por:
- Tipo de estrategia
- Estado
- Símbolo
- Timeframe
- Fecha de creación

### 4. Ordenamiento
Permitir ordenar por:
- Nombre
- Fecha de creación
- Rendimiento
- Número de trades

## Próximos Pasos

1. **Implementar Backtesting Real**: Conectar con datos históricos reales
2. **Optimización de Estrategias**: Algoritmos genéticos para optimizar parámetros
3. **Paper Trading**: Simulación en tiempo real sin dinero real
4. **Live Trading**: Conexión con brokers reales
5. **Alertas y Notificaciones**: Sistema de notificaciones para señales
6. **Análisis de Riesgo**: Métricas avanzadas de riesgo (VaR, Sharpe ratio, etc.)
7. **Portfolio Management**: Gestión de múltiples estrategias simultáneamente
