from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union, Literal
from datetime import datetime, date


class IndicatorConfig(BaseModel):
    indicator: Literal['VWAP', 'SMA', 'EMA', 'RSI', 'MACD']
    period: Optional[int] = None
    offset_std: Optional[float] = None
    std_mult: Optional[float] = None


class RightSide(BaseModel):
    indicator: Optional[IndicatorConfig] = None
    value: Optional[float] = None
    std_mult: Optional[float] = None


class IndicatorCondition(BaseModel):
    type: Literal['indicator_condition']
    left: IndicatorConfig
    operator: Literal['cross_above', 'cross_below', 'cross_below_or_equal', 'lt', 'gt']
    right: RightSide


class OrderflowCondition(BaseModel):
    type: Literal['orderflow_condition']
    name: Literal['seller_absorption', 'buyer_absorption']
    lookback_bars: int
    threshold: float
    approximation: Optional[str] = None


class TakeProfit(BaseModel):
    type: Literal['take_profit']
    rr: Optional[float] = None
    target_pct: Optional[float] = None


class StopLoss(BaseModel):
    type: Literal['stop_loss']
    atr_mult: Optional[float] = None
    pct: Optional[float] = None


class Universe(BaseModel):
    type: Literal['single', 'universe']
    symbol: Optional[str] = None
    asset_class: Optional[Literal['Equity', 'Forex', 'Crypto']] = None


class Timeframe(BaseModel):
    start: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    end: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    resolution: Literal['Minute', 'Second', 'Hour', 'Daily']


class Positioning(BaseModel):
    side: Literal['long_only', 'short_only', 'both']
    risk_per_trade_pct: float = Field(..., ge=0.1, le=10.0)
    max_concurrent_positions: int = Field(..., ge=1, le=10)


class TradingStrategyDSL(BaseModel):
    universe: Universe
    timeframe: Timeframe
    entry_rules: List[Union[IndicatorCondition, OrderflowCondition]]
    exit_rules: List[Union[TakeProfit, StopLoss]]
    positioning: Positioning

    @validator('entry_rules')
    def validate_entry_rules(cls, v):
        if not v:
            raise ValueError('At least one entry rule is required')
        return v

    @validator('exit_rules')
    def validate_exit_rules(cls, v):
        if not v:
            raise ValueError('At least one exit rule is required')
        return v


class NLToStrategyRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=1000)
    defaults: Optional[dict] = None


class NLToStrategyResponse(BaseModel):
    dsl: TradingStrategyDSL
    lean_code: str
    warnings: List[str] = []


class BacktestRequest(BaseModel):
    dsl: Optional[TradingStrategyDSL] = None
    lean_code: Optional[str] = None


class BacktestResponse(BaseModel):
    success: bool
    backtest_id: str
    results: Optional[dict] = None
    error: Optional[str] = None
