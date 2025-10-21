"""
TradeLab Engine Pro - Advanced Trading Engine with Multi-Position Support
Integrated from ChatGPT Pro version
"""

import math
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import itertools
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp


# ---------- Data Loading ----------
def load_parquet(symbol: str, timeframe: str, base_path: str) -> pd.DataFrame:
    """
    Load parquet data for symbol/timeframe
    Expected format: {base_path}/{symbol}/{timeframe}.parquet
    Required columns: ['timestamp','open','high','low','close','volume']
    """
    path = f"{base_path}/{symbol}/{timeframe}.parquet"
    df = pd.read_parquet(path)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df = df.set_index("timestamp").sort_index()
    else:
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("Se requiere timestamp o índice datetime")
        df = df.sort_index()
    return df[["open","high","low","close","volume"]].dropna()


# ---------- Advanced Indicators ----------
class ProIndicators:
    """Advanced technical indicators for Pro engine"""
    
    @staticmethod
    def SMA(series: pd.Series, length: int) -> pd.Series:
        return series.rolling(length, min_periods=length).mean()

    @staticmethod
    def EMA(series: pd.Series, length: int) -> pd.Series:
        return series.ewm(span=length, adjust=False, min_periods=length).mean()

    @staticmethod
    def RSI(series: pd.Series, length: int=14) -> pd.Series:
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.ewm(alpha=1/length, adjust=False).mean()
        roll_down = down.ewm(alpha=1/length, adjust=False).mean()
        rs = roll_up / (roll_down.replace(0, np.nan))
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    @staticmethod
    def ATR(high: pd.Series, low: pd.Series, close: pd.Series, length: int=14) -> pd.Series:
        prev_close = close.shift(1)
        tr = pd.concat([
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs()
        ], axis=1).max(axis=1)
        return tr.ewm(alpha=1/length, adjust=False).mean()

    @staticmethod
    def Bollinger(series: pd.Series, length: int=20, mult: float=2.0) -> Tuple[pd.Series,pd.Series,pd.Series]:
        m = ProIndicators.SMA(series, length)
        sd = series.rolling(length, min_periods=length).std()
        upper = m + mult*sd
        lower = m - mult*sd
        return upper, m, lower

    @staticmethod
    def VWAP(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        typical = (high + low + close)/3.0
        cum_vol = volume.cumsum()
        cum_tpv = (typical*volume).cumsum()
        return cum_tpv / cum_vol.replace(0, np.nan)

    @staticmethod
    def CCI(high: pd.Series, low: pd.Series, close: pd.Series, length: int=20, c: float=0.015) -> pd.Series:
        """Commodity Channel Index with configurable constant"""
        typical = (high + low + close) / 3
        sma = typical.rolling(length, min_periods=length).mean()
        mad = typical.rolling(length, min_periods=length).apply(lambda x: np.mean(np.abs(x - x.mean())))
        cci = (typical - sma) / (c * mad)
        return cci.fillna(0)

    @staticmethod
    def Stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_len: int=14, d_len: int=3) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator with configurable periods"""
        lowest_low = low.rolling(k_len, min_periods=k_len).min()
        highest_high = high.rolling(k_len, min_periods=k_len).max()
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(d_len, min_periods=d_len).mean()
        return k_percent.fillna(50), d_percent.fillna(50)

    @staticmethod
    def OBV(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On Balance Volume"""
        price_change = close.diff()
        obv = np.where(price_change > 0, volume, 
                      np.where(price_change < 0, -volume, 0)).cumsum()
        return pd.Series(obv, index=close.index)


# ---------- Logic Engine ----------
CMP_FUN = {
    ">":  lambda a,b: a >  b,
    "<":  lambda a,b: a <  b,
    "==": lambda a,b: a == b,
    ">=": lambda a,b: a >= b,
    "<=": lambda a,b: a <= b,
}

def ensure_series(x, index):
    if isinstance(x, (int,float,np.floating)) or x is None:
        return pd.Series(x, index=index)
    return x

def compute_indicator(df: pd.DataFrame, id: str, params: Dict[str,Any]) -> pd.Series:
    """Compute indicator with Pro engine support"""
    idu = id.upper()
    if idu == "CLOSE": return df["close"]
    if idu == "OPEN":  return df["open"]
    if idu == "HIGH":  return df["high"]
    if idu == "LOW":   return df["low"]
    if idu == "VOLUME":return df["volume"]

    if idu == "SMA":   return ProIndicators.SMA(df["close"], int(params.get("length",20)))
    if idu == "EMA":   return ProIndicators.EMA(df["close"], int(params.get("length",20)))
    if idu == "RSI":   return ProIndicators.RSI(df["close"], int(params.get("length",14)))
    if idu == "ATR":   return ProIndicators.ATR(df["high"], df["low"], df["close"], int(params.get("length",14)))
    if idu == "BOLLINGER_UPPER":
        u,_,_ = ProIndicators.Bollinger(df["close"], int(params.get("length",20)), float(params.get("mult",2.0))); return u
    if idu == "BOLLINGER_MIDDLE":
        _,m,_ = ProIndicators.Bollinger(df["close"], int(params.get("length",20)), float(params.get("mult",2.0))); return m
    if idu == "BOLLINGER_LOWER":
        _,_,l = ProIndicators.Bollinger(df["close"], int(params.get("length",20)), float(params.get("mult",2.0))); return l
    if idu == "VWAP":  return ProIndicators.VWAP(df["high"], df["low"], df["close"], df["volume"])
    if idu == "CCI":   return ProIndicators.CCI(df["high"], df["low"], df["close"], 
                                               int(params.get("length",20)), float(params.get("c",0.015)))
    if idu == "STOCH_K":
        k, _ = ProIndicators.Stochastic(df["high"], df["low"], df["close"], 
                                       int(params.get("k_len",14)), int(params.get("d_len",3)))
        return k
    if idu == "STOCH_D":
        _, d = ProIndicators.Stochastic(df["high"], df["low"], df["close"], 
                                       int(params.get("k_len",14)), int(params.get("d_len",3)))
        return d
    if idu == "OBV":   return ProIndicators.OBV(df["close"], df["volume"])
    
    raise ValueError(f"Indicador no soportado: {id}")

def materialize_operand(df: pd.DataFrame, operand: Dict[str,Any]) -> pd.Series:
    if operand["type"] == "indicator":
        return compute_indicator(df, operand["id"], operand.get("params",{}))
    elif operand["type"] == "value":
        return pd.Series(float(operand["value"]), index=df.index)
    else:
        raise ValueError("operand.type debe ser indicator|value")

def eval_logic(df: pd.DataFrame, node: Dict[str,Any]) -> pd.Series:
    """Evaluate logic tree with AND/OR support"""
    if "op" in node:
        op = node["op"].upper()
        masks = [eval_logic(df, c) for c in node.get("clauses",[])]
        if not masks:
            return pd.Series(False, index=df.index)
        out = masks[0].astype(bool)
        for m in masks[1:]:
            if op == "AND": out = out & m.astype(bool)
            elif op == "OR": out = out | m.astype(bool)
            else: raise ValueError("op debe ser AND/OR")
        return out
    else:
        left = materialize_operand(df, node["left"])
        right = materialize_operand(df, node["right"])
        cmp_fn = CMP_FUN[node["cmp"]]
        return cmp_fn(left, right).fillna(False)


# ---------- Risk Management ----------
@dataclass
class RiskConfig:
    initial_capital: float
    position_size: int
    max_positions: int  # NEW: Multiple positions support
    commission_round_turn: float
    slippage_ticks: float
    tick_value: float
    tick_size: float

@dataclass
class StopTarget:
    type: str   # "Percentage"|"Points"|"Ticks"|"ATR"
    value: float

@dataclass
class TrailingStop:
    """NEW: Trailing stop configuration"""
    active: bool
    type: str   # "Percentage"|"Points"|"Ticks"|"ATR"
    value: float
    use_high_low: bool = True  # True = anchor with high/low, False = with close

def price_with_slippage(fill_price: float, side: str, slippage_ticks: float, tick_size: float, direction: int) -> float:
    slip = slippage_ticks * tick_size
    if side.upper() == "LONG":
        return fill_price + direction*slip
    else:
        return fill_price - direction*slip

def to_points(value: float, typ: str, context: Dict[str,Any]) -> float:
    """Convert stop/target to price points"""
    typu = typ.upper()
    if typu == "PERCENTAGE":
        return context["entry"] * (value/100.0)
    if typu == "POINTS":
        return value
    if typu == "TICKS":
        return value * context["tick_size"]
    if typu == "ATR":
        return value * context["atr"]
    raise ValueError("Tipo de stop/target no soportado")


# ---------- Position Management ----------
class Position:
    """Individual position with independent stop/target/trailing"""
    def __init__(self, side: str, entry_price: float, entry_time, size: int, 
                 stop_target: Optional[StopTarget], take_target: Optional[StopTarget],
                 trailing: Optional[TrailingStop], tick_size: float, tick_value: float):
        self.side = side
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.size = size
        self.stop_target = stop_target
        self.take_target = take_target
        self.trailing = trailing
        self.tick_size = tick_size
        self.tick_value = tick_value
        
        # Trailing stop state
        self.trailing_activated = False
        self.trailing_level = None
        self.highest_price = entry_price if side == "LONG" else entry_price
        self.lowest_price = entry_price if side == "SHORT" else entry_price
    
    def update_trailing(self, high: float, low: float, close: float, atr: float):
        """Update trailing stop levels"""
        if not self.trailing or not self.trailing.active:
            return
        
        # Update highest/lowest prices
        if self.side == "LONG":
            self.highest_price = max(self.highest_price, high)
            anchor_price = self.highest_price if self.trailing.use_high_low else close
        else:  # SHORT
            self.lowest_price = min(self.lowest_price, low)
            anchor_price = self.lowest_price if self.trailing.use_high_low else close
        
        # Calculate trailing level
        context = {"entry": self.entry_price, "atr": atr, "tick_size": self.tick_size}
        trail_points = to_points(self.trailing.value, self.trailing.type, context)
        
        if self.side == "LONG":
            self.trailing_level = anchor_price - trail_points
        else:
            self.trailing_level = anchor_price + trail_points
    
    def check_exit(self, high: float, low: float, close: float, atr: float) -> Optional[Tuple[str, float]]:
        """Check if position should exit and return (reason, exit_price)"""
        context = {"entry": self.entry_price, "atr": atr, "tick_size": self.tick_size}
        
        # Check stop loss
        if self.stop_target:
            stop_points = to_points(self.stop_target.value, self.stop_target.type, context)
            if self.side == "LONG":
                stop_price = self.entry_price - stop_points
                if low <= stop_price:
                    return "Stop Loss", stop_price
            else:
                stop_price = self.entry_price + stop_points
                if high >= stop_price:
                    return "Stop Loss", stop_price
        
        # Check take profit
        if self.take_target:
            target_points = to_points(self.take_target.value, self.take_target.type, context)
            if self.side == "LONG":
                target_price = self.entry_price + target_points
                if high >= target_price:
                    return "Take Profit", target_price
            else:
                target_price = self.entry_price - target_points
                if low <= target_price:
                    return "Take Profit", target_price
        
        # Check trailing stop
        if self.trailing and self.trailing.active and self.trailing_level is not None:
            if self.side == "LONG":
                if low <= self.trailing_level:
                    return "Trailing Stop", self.trailing_level
            else:
                if high >= self.trailing_level:
                    return "Trailing Stop", self.trailing_level
        
        return None
    
    def calculate_pnl(self, exit_price: float) -> float:
        """Calculate P&L for this position"""
        if self.side == "LONG":
            points = exit_price - self.entry_price
        else:
            points = self.entry_price - exit_price
        
        return points / self.tick_size * self.tick_value * self.size


# ---------- Pro Backtester ----------
class ProBacktester:
    """Advanced backtester with multi-position and trailing stop support"""
    
    def __init__(self, df: pd.DataFrame, risk: RiskConfig, stops: Optional[StopTarget], 
                 targets: Optional[StopTarget], trailing: Optional[TrailingStop] = None):
        self.df = df.copy()
        self.risk = risk
        self.stops = stops
        self.targets = targets
        self.trailing = trailing
        
        # Precompute ATR for trailing stops
        self.df["_ATR14"] = ProIndicators.ATR(df["high"], df["low"], df["close"], 14)
    
    def run(self, entries: List[Dict[str,Any]], exits: List[Dict[str,Any]]) -> Dict[str, Any]:
        """Run backtest with multi-position support"""
        df = self.df
        
        # Generate signals
        long_entry = pd.Series(False, index=df.index)
        short_entry = pd.Series(False, index=df.index)
        long_exit = pd.Series(False, index=df.index)
        short_exit = pd.Series(False, index=df.index)

        for r in entries:
            side = r["side"].upper()
            mask = eval_logic(df, r["logic"])
            if side == "LONG": long_entry |= mask
            if side == "SHORT": short_entry |= mask

        for r in exits:
            side = r["side"].upper()
            mask = eval_logic(df, r["logic"])
            if side == "LONG": long_exit |= mask
            if side == "SHORT": short_exit |= mask

        # Initialize state
        equity = []
        trades = []
        cash = self.risk.initial_capital
        positions = []  # List of Position objects
        commission = self.risk.commission_round_turn
        tick_size = self.risk.tick_size
        tick_value = self.risk.tick_value

        for ts, row in df.iterrows():
            price = row["close"]
            high = row["high"]
            low = row["low"]
            atr = row["_ATR14"]

            # Update trailing stops for all positions
            for pos in positions:
                pos.update_trailing(high, low, price, atr)

            # Check exits for all positions
            positions_to_close = []
            for i, pos in enumerate(positions):
                exit_signal = pos.check_exit(high, low, price, atr)
                if exit_signal:
                    reason, exit_price = exit_signal
                    fill_price = price_with_slippage(exit_price, pos.side, self.risk.slippage_ticks, tick_size, direction=-1)
                    
                    # Calculate P&L
                    pnl = pos.calculate_pnl(fill_price)
                    cash += pnl - commission
                    
                    trades.append({
                        "entry_time": pos.entry_time,
                        "entry_price": pos.entry_price,
                        "exit_time": ts,
                        "exit_price": fill_price,
                        "side": pos.side,
                        "size": pos.size,
                        "pnl": pnl,
                        "reason": reason
                    })
                    
                    positions_to_close.append(i)
            
            # Close positions (in reverse order to maintain indices)
            for i in reversed(positions_to_close):
                positions.pop(i)

            # Check signal exits
            for pos in positions:
                if ((pos.side == "LONG" and long_exit.loc[ts]) or 
                    (pos.side == "SHORT" and short_exit.loc[ts])):
                    fill_price = price_with_slippage(price, pos.side, self.risk.slippage_ticks, tick_size, direction=-1)
                    pnl = pos.calculate_pnl(fill_price)
                    cash += pnl - commission
                    
                    trades.append({
                        "entry_time": pos.entry_time,
                        "entry_price": pos.entry_price,
                        "exit_time": ts,
                        "exit_price": fill_price,
                        "side": pos.side,
                        "size": pos.size,
                        "pnl": pnl,
                        "reason": "Signal Exit"
                    })
            
            # Remove signal-exited positions
            positions = [pos for pos in positions if not (
                (pos.side == "LONG" and long_exit.loc[ts]) or 
                (pos.side == "SHORT" and short_exit.loc[ts])
            )]

            # Check entries (only if we have capacity)
            if len(positions) < self.risk.max_positions:
                if long_entry.loc[ts]:
                    # Check if we already have a LONG position (accumulation)
                    existing_long = any(pos.side == "LONG" for pos in positions)
                    if not existing_long or self.risk.max_positions > 1:
                        fill_price = price_with_slippage(price, "LONG", self.risk.slippage_ticks, tick_size, direction=+1)
                        new_pos = Position(
                            side="LONG", entry_price=fill_price, entry_time=ts,
                            size=self.risk.position_size, stop_target=self.stops,
                            take_target=self.targets, trailing=self.trailing,
                            tick_size=tick_size, tick_value=tick_value
                        )
                        positions.append(new_pos)
                        cash -= commission
                
                elif short_entry.loc[ts]:
                    # Check if we already have a SHORT position (accumulation)
                    existing_short = any(pos.side == "SHORT" for pos in positions)
                    if not existing_short or self.risk.max_positions > 1:
                        fill_price = price_with_slippage(price, "SHORT", self.risk.slippage_ticks, tick_size, direction=+1)
                        new_pos = Position(
                            side="SHORT", entry_price=fill_price, entry_time=ts,
                            size=self.risk.position_size, stop_target=self.stops,
                            take_target=self.targets, trailing=self.trailing,
                            tick_size=tick_size, tick_value=tick_value
                        )
                        positions.append(new_pos)
                        cash -= commission

            # Calculate current equity (mark-to-market)
            mtm = 0.0
            for pos in positions:
                if pos.side == "LONG":
                    mtm += (price - pos.entry_price) / tick_size * tick_value * pos.size
                else:
                    mtm += (pos.entry_price - price) / tick_size * tick_value * pos.size
            
            equity.append({"timestamp": ts, "equity": cash + mtm})

        # Calculate metrics
        eq = pd.Series([e["equity"] for e in equity], index=[e["timestamp"] for e in equity])
        metrics = self._compute_metrics(eq, trades)
        
        return {
            "trades": trades,
            "equity_curve": [{"timestamp": str(t), "equity": float(v)} for t,v in eq.items()],
            "metrics": metrics
        }
    
    def _compute_metrics(self, equity: pd.Series, trades: List[Dict[str,Any]]) -> Dict[str,Any]:
        """Compute comprehensive metrics"""
        if len(equity) < 2:
            return {}
        
        ret = equity.pct_change().fillna(0.0)
        
        # Calculate time period
        if (equity.index[-1] - equity.index[0]).days <= 0:
            years = 1.0
        else:
            years = (equity.index[-1] - equity.index[0]).days / 365.25
        
        # Basic performance metrics
        total_return = equity.iloc[-1] / equity.iloc[0] - 1.0
        cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else total_return
        vol = ret.std() * np.sqrt(252)
        sharpe = (ret.mean() * 252) / vol if vol > 0 else 0.0
        
        # Drawdown calculation
        peak = equity.cummax()
        dd = (equity / peak - 1.0)
        maxdd = dd.min()
        
        # Trade-based metrics
        if trades:
            pnls = [t["pnl"] for t in trades]
            winning_trades = [p for p in pnls if p > 0]
            losing_trades = [p for p in pnls if p < 0]
            
            win_rate = len(winning_trades) / len(trades) if trades else 0
            avg_win = np.mean(winning_trades) if winning_trades else 0
            avg_loss = np.mean(losing_trades) if losing_trades else 0
            profit_factor = abs(sum(winning_trades) / sum(losing_trades)) if losing_trades and sum(losing_trades) != 0 else float('inf')
            expectancy = np.mean(pnls) if pnls else 0
            
            largest_win = max(winning_trades) if winning_trades else 0
            largest_loss = min(losing_trades) if losing_trades else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
            expectancy = 0
            largest_win = 0
            largest_loss = 0
        
        return {
            "Total Return": total_return,
            "Total Return %": total_return * 100,
            "CAGR": cagr,
            "CAGR %": cagr * 100,
            "Sharpe Ratio": sharpe,
            "Max Drawdown": float(maxdd),
            "Max Drawdown %": float(maxdd) * 100,
            "Win Rate": win_rate,
            "Win Rate %": win_rate * 100,
            "Profit Factor": profit_factor,
            "Expectancy": expectancy,
            "Average Win": avg_win,
            "Average Loss": avg_loss,
            "Largest Win": largest_win,
            "Largest Loss": largest_loss,
            "Total Trades": len(trades),
            "Winning Trades": len(winning_trades) if trades else 0,
            "Losing Trades": len(losing_trades) if trades else 0,
            "Volatility": vol,
            "Volatility %": vol * 100
        }


# ---------- Portfolio Backtesting ----------
class PortfolioBacktester:
    """Multi-symbol portfolio backtester"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
    
    def run_portfolio_backtest(self, metas: List[Dict[str,str]], strategy_json: Dict[str,Any], 
                              weights: Optional[List[float]] = None) -> Dict[str,Any]:
        """
        Run portfolio backtest across multiple symbols
        
        Args:
            metas: List of {"symbol": "ES", "timeframe": "5m"}
            strategy_json: Strategy configuration
            weights: Optional weights for each symbol (default: equal weights)
        """
        if not metas:
            raise ValueError("At least one symbol required")
        
        if weights is None:
            weights = [1.0 / len(metas)] * len(metas)
        
        if len(weights) != len(metas):
            raise ValueError("Weights must match number of symbols")
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Run individual backtests
        individual_results = []
        for i, meta in enumerate(metas):
            # Load data
            df = load_parquet(meta["symbol"], meta["timeframe"], self.base_path)
            
            # Create strategy with this symbol's meta
            symbol_strategy = strategy_json.copy()
            symbol_strategy["meta"] = meta
            
            # Extract configuration
            risk_config = RiskConfig(**symbol_strategy["risk"])
            stops = StopTarget(**symbol_strategy["stops_targets"]["stop_loss"]) if symbol_strategy["stops_targets"].get("stop_loss") else None
            targets = StopTarget(**symbol_strategy["stops_targets"]["take_profit"]) if symbol_strategy["stops_targets"].get("take_profit") else None
            trailing = TrailingStop(**symbol_strategy.get("trailing_stop", {})) if symbol_strategy.get("trailing_stop", {}).get("active", False) else None
            
            # Run backtest
            bt = ProBacktester(df, risk_config, stops, targets, trailing)
            result = bt.run(symbol_strategy["entries"], symbol_strategy["exits"])
            
            individual_results.append({
                "symbol": meta["symbol"],
                "timeframe": meta["timeframe"],
                "weight": weights[i],
                "result": result
            })
        
        # Combine results
        portfolio_equity = self._combine_equity_curves(individual_results)
        portfolio_metrics = self._compute_portfolio_metrics(portfolio_equity, individual_results)
        
        return {
            "portfolio_metrics": portfolio_metrics,
            "legs": [{"symbol": r["symbol"], "weight": r["weight"], "metrics": r["result"]["metrics"]} for r in individual_results],
            "portfolio_equity_curve": portfolio_equity
        }
    
    def _combine_equity_curves(self, individual_results: List[Dict]) -> List[Dict[str,Any]]:
        """Combine individual equity curves into portfolio curve"""
        if not individual_results:
            return []
        
        # Get all timestamps
        all_timestamps = set()
        for result in individual_results:
            for point in result["result"]["equity_curve"]:
                all_timestamps.add(point["timestamp"])
        
        # Sort timestamps
        sorted_timestamps = sorted(all_timestamps)
        
        # Interpolate and combine
        portfolio_equity = []
        for ts in sorted_timestamps:
            portfolio_value = 0.0
            for result in individual_results:
                # Find closest equity value for this timestamp
                equity_curve = result["result"]["equity_curve"]
                closest_value = None
                closest_ts = None
                
                for point in equity_curve:
                    if point["timestamp"] <= ts:
                        closest_value = point["equity"]
                        closest_ts = point["timestamp"]
                    else:
                        break
                
                if closest_value is not None:
                    portfolio_value += closest_value * result["weight"]
            
            portfolio_equity.append({
                "timestamp": ts,
                "equity": portfolio_value
            })
        
        return portfolio_equity
    
    def _compute_portfolio_metrics(self, portfolio_equity: List[Dict], individual_results: List[Dict]) -> Dict[str,Any]:
        """Compute portfolio-level metrics"""
        if not portfolio_equity:
            return {}
        
        # Convert to pandas Series
        equity_values = [point["equity"] for point in portfolio_equity]
        equity_series = pd.Series(equity_values)
        
        # Calculate basic metrics
        total_return = equity_series.iloc[-1] / equity_series.iloc[0] - 1.0
        ret = equity_series.pct_change().fillna(0.0)
        vol = ret.std() * np.sqrt(252)
        sharpe = (ret.mean() * 252) / vol if vol > 0 else 0.0
        
        # Drawdown
        peak = equity_series.cummax()
        dd = (equity_series / peak - 1.0)
        maxdd = dd.min()
        
        return {
            "Total Return": total_return,
            "Total Return %": total_return * 100,
            "Sharpe Ratio": sharpe,
            "Max Drawdown": float(maxdd),
            "Max Drawdown %": float(maxdd) * 100,
            "Volatility": vol,
            "Volatility %": vol * 100,
            "Number of Symbols": len(individual_results)
        }
