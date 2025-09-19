# strategies/normalizers.py
from .enums import (
    SUPPORTED_SYMBOLS, SUPPORTED_TIMEFRAMES, SUPPORTED_INDICATORS, SUPPORTED_OPERATORS,
    STOP_LOSS_TYPES, TAKE_PROFIT_TYPES,
    SYMBOL_ALIASES, TIMEFRAME_ALIASES, INDICATOR_ALIASES, OPERATOR_ALIASES, STOP_TP_ALIASES
)

class NormalizationResult:
    def __init__(self, value, warnings=None):
        self.value = value
        self.warnings = warnings or []

def _w(msg): 
    return [msg]

def normalize_symbol(s: str) -> NormalizationResult:
    raw = (s or '').strip()
    key = raw.lower()
    val = SYMBOL_ALIASES.get(key, raw.upper())
    if val not in SUPPORTED_SYMBOLS:
        return NormalizationResult(raw, _w(f"Símbolo '{raw}' no soportado. Soportados: {', '.join(SUPPORTED_SYMBOLS[:8])}…"))
    return NormalizationResult(val)

def normalize_timeframe(tf: str) -> NormalizationResult:
    raw = (tf or '').strip()
    key = raw.lower()
    val = TIMEFRAME_ALIASES.get(key, raw)
    # normaliza mayúsculas para sufijo letra solo si es necesario
    if val and val[-1].isalpha() and val not in SUPPORTED_TIMEFRAMES: 
        val = val[:-1] + val[-1].upper()
    if val not in SUPPORTED_TIMEFRAMES:
        return NormalizationResult(raw, _w(f"Timeframe '{raw}' no soportado. Usa uno de: {', '.join(SUPPORTED_TIMEFRAMES)}"))
    return NormalizationResult(val)

def normalize_indicator_name(name: str) -> str:
    return INDICATOR_ALIASES.get((name or '').strip().lower(), (name or '').strip().upper())

def normalize_operator(op: str) -> str:
    opn = OPERATOR_ALIASES.get((op or '').strip().lower(), (op or '').strip().lower())
    return opn if opn in SUPPORTED_OPERATORS else (op or '').strip().lower()

def normalize_stop_take(name: str, is_tp=False) -> NormalizationResult:
    raw = (name or '').strip().lower()
    
    # Los tipos válidos son percentage, points, ticks, atr
    # No necesitamos normalizar 'stop_loss' o 'take_profit' como tipos
    types = TAKE_PROFIT_TYPES if is_tp else STOP_LOSS_TYPES
    
    # Si el input es un tipo válido, devolverlo tal como está
    if raw in types:
        return NormalizationResult(raw)
    
    # Si no es un tipo válido, devolver error
    return NormalizationResult(raw, _w(f"{'take_profit' if is_tp else 'stop_loss'} '{raw}' no soportado. Tipos: {', '.join(types)}"))

def coerce_float(x, field, warnings):
    try:
        return float(x)
    except Exception:
        warnings.append(f"Campo '{field}' no es numérico ('{x}').")
        return None

def validate_indicator_params(name: str, params: dict, warnings: list, errors: dict):
    n = normalize_indicator_name(name)
    p = params or {}
    if n in ('SMA','EMA','RSI','ATR'):
        win = p.get('window') or p.get('period') or p.get('n')
        if win is None:
            errors.setdefault('indicators', []).append(f"{n}: falta parámetro 'window/period'.")
        else:
            try:
                win = int(win)
                if win < 2: 
                    errors.setdefault('indicators', []).append(f"{n}: window debe ser ≥ 2.")
            except Exception:
                errors.setdefault('indicators', []).append(f"{n}: window inválido '{win}'.")
    # MACD
    if n == 'MACD':
        fast, slow, signal = p.get('fast',12), p.get('slow',26), p.get('signal',9)
        try:
            fast, slow, signal = int(fast), int(slow), int(signal)
            if not (1 <= fast < slow and 1 <= signal):
                errors.setdefault('indicators', []).append("MACD: parámetros inconsistentes (fast < slow, signal ≥ 1).")
        except Exception:
            errors.setdefault('indicators', []).append("MACD: parámetros inválidos.")

def preflight_feasibility(payload: dict) -> tuple:
    """Devuelve (warnings, errors)"""
    warnings, errors = [], {}

    # símbolo / timeframe
    sym = normalize_symbol(payload.get('symbol'))
    warnings += sym.warnings
    tf = normalize_timeframe(payload.get('timeframe'))
    warnings += tf.warnings

    # stop/take
    if payload.get('stop_loss_type'):
        warnings += normalize_stop_take(payload['stop_loss_type']).warnings
    if payload.get('take_profit_type'):
        warnings += normalize_stop_take(payload['take_profit_type'], is_tp=True).warnings

    # montos y costes
    ic = payload.get('initial_capital', 10000)
    icf = coerce_float(ic, 'initial_capital', warnings)
    if icf is None or icf <= 0:
        errors.setdefault('initial_capital', []).append("Debe ser > 0.")

    for f in ('commission','slippage','fees_bps'):
        if f in payload:
            v = coerce_float(payload[f], f, warnings)
            if v is None: 
                continue
            if v < 0:
                warnings.append(f"'{f}' negativo → se usará valor absoluto.")
                payload[f] = abs(v)

    # periodo
    start, end = payload.get('start'), payload.get('end')
    if start and end:
        try:
            from datetime import datetime
            s = datetime.fromisoformat(str(start).replace('Z',''))
            e = datetime.fromisoformat(str(end).replace('Z',''))
            if s >= e:
                errors.setdefault('period', []).append("start debe ser < end.")
        except Exception:
            warnings.append("Fechas no ISO → intenta 'YYYY-MM-DD'.")

    # reglas
    for kind in ('entry_rules','exit_rules'):
        rules = payload.get(kind) or []
        for i, r in enumerate(rules):
            rtype = (r.get('rule_type') or 'condition').lower()
            if rtype == 'condition':
                conds = r.get('conditions') or []
                if not conds:
                    errors.setdefault(kind, []).append(f"Regla {i+1}: falta al menos 1 condición.")
                for c in conds:
                    left = normalize_indicator_name(c.get('left_operand'))
                    right = normalize_indicator_name(c.get('right_operand')) if isinstance(c.get('right_operand'), str) else c.get('right_operand')
                    op = normalize_operator(c.get('operator'))
                    if op not in SUPPORTED_OPERATORS:
                        errors.setdefault(kind, []).append(f"Operador '{c.get('operator')}' no soportado.")
                    # valida parámetros si hay indicadores declarados arriba
            elif rtype == 'action':
                act = (r.get('action') or '').lower()
                if act not in ('buy','sell','close','modify','wait'):
                    errors.setdefault(kind, []).append(f"Acción '{act}' no soportada.")
            # filtros: aquí podrías añadir más

    # indicadores
    for ind in (payload.get('indicators') or []):
        validate_indicator_params(ind.get('name'), ind.get('params'), warnings, errors)

    # compatibilidad timeframe con units
    # ticks/points sólo si aportas 'tick_size' o timeframe intradía
    unit_fields = []
    if (payload.get('take_profit_type') in ('ticks','points') or
        payload.get('stop_loss_type') in ('ticks','points')):
        unit_fields.append('tick_size')
    if unit_fields and payload.get('timeframe') in ('1D','1W','1M'):
        if not payload.get('tick_size'):
            errors.setdefault('risk', []).append("Para 'ticks/points' en stops/TP aporta 'tick_size' o usa timeframe intradía.")

    return warnings, errors
