"""
Advanced metrics calculator for backtesting results
"""

import numpy as np
import pandas as pd
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta


def calculate_all_metrics(trades_data: List[Dict], initial_capital: float, 
                         start_date: datetime, end_date: datetime, 
                         risk_free_rate: float = 0.02) -> Dict:
    """
    Calculate all performance, risk, and trading metrics
    
    Args:
        trades_data: List of trade dictionaries
        initial_capital: Starting capital amount
        start_date: Backtest start date
        end_date: Backtest end date
        risk_free_rate: Risk-free rate for Sharpe/Sortino calculations
    
    Returns:
        Dictionary with all calculated metrics
    """
    if not trades_data:
        return create_empty_metrics(initial_capital)
    
    # Convert to DataFrame for easier calculations
    df = pd.DataFrame(trades_data)
    
    # Basic trade statistics
    total_trades = len(df)
    winning_trades = len(df[df['net_pnl'] > 0])
    losing_trades = len(df[df['net_pnl'] < 0])
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # P&L metrics
    total_return = float(df['net_pnl'].sum())
    total_return_percent = (total_return / initial_capital) * 100
    
    # Win/Loss averages
    winning_trades_df = df[df['net_pnl'] > 0]
    losing_trades_df = df[df['net_pnl'] < 0]
    
    avg_win = float(winning_trades_df['net_pnl'].mean()) if len(winning_trades_df) > 0 else 0
    avg_loss = float(losing_trades_df['net_pnl'].mean()) if len(losing_trades_df) > 0 else 0
    largest_win = float(df['net_pnl'].max())
    largest_loss = float(df['net_pnl'].min())
    
    # Profit Factor
    gross_profit = float(winning_trades_df['net_pnl'].sum()) if len(winning_trades_df) > 0 else 0
    gross_loss = abs(float(losing_trades_df['net_pnl'].sum())) if len(losing_trades_df) > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Calculate equity curve
    equity_curve = initial_capital + df['net_pnl'].cumsum()
    
    # Risk metrics
    sharpe_ratio = calculate_sharpe_ratio(equity_curve, risk_free_rate)
    sortino_ratio = calculate_sortino_ratio(equity_curve, risk_free_rate)
    volatility = calculate_volatility(equity_curve)
    max_drawdown, max_drawdown_percent = calculate_max_drawdown(equity_curve, initial_capital)
    calmar_ratio = calculate_calmar_ratio(total_return_percent, max_drawdown_percent)
    recovery_factor = calculate_recovery_factor(total_return, max_drawdown)
    
    # Trading metrics
    max_consecutive_wins = calculate_max_consecutive_wins(df)
    max_consecutive_losses = calculate_max_consecutive_losses(df)
    avg_trade_duration = calculate_avg_trade_duration(df)
    trades_per_month = calculate_trades_per_month(df, start_date, end_date)
    expectancy = calculate_expectancy(df)
    
    return {
        # Performance metrics
        'total_return': total_return,
        'total_return_percent': total_return_percent,
        'win_rate': win_rate,
        'winning_trades': winning_trades,
        'total_trades': total_trades,
        'losing_trades': losing_trades,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'largest_win': largest_win,
        'largest_loss': largest_loss,
        'profit_factor': profit_factor,
        
        # Risk metrics
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'calmar_ratio': calmar_ratio,
        'volatility': volatility,
        'max_drawdown': max_drawdown,
        'max_drawdown_percent': max_drawdown_percent,
        'recovery_factor': recovery_factor,
        
        # Trading metrics
        'max_consecutive_wins': max_consecutive_wins,
        'max_consecutive_losses': max_consecutive_losses,
        'avg_trade_duration': avg_trade_duration,
        'trades_per_month': trades_per_month,
        'expectancy': expectancy,
    }


def calculate_sharpe_ratio(equity_curve: pd.Series, risk_free_rate: float = 0.02) -> Optional[float]:
    """Calculate Sharpe Ratio"""
    if len(equity_curve) < 2:
        return None
    
    returns = equity_curve.pct_change().dropna()
    if len(returns) == 0 or returns.std() == 0:
        return None
    
    # Annualize the risk-free rate (assuming 252 trading days)
    daily_risk_free = risk_free_rate / 252
    excess_returns = returns - daily_risk_free
    
    return float((excess_returns.mean() / returns.std()) * np.sqrt(252))


def calculate_sortino_ratio(equity_curve: pd.Series, risk_free_rate: float = 0.02) -> Optional[float]:
    """Calculate Sortino Ratio (only considers downside volatility)"""
    if len(equity_curve) < 2:
        return None
    
    returns = equity_curve.pct_change().dropna()
    if len(returns) == 0:
        return None
    
    daily_risk_free = risk_free_rate / 252
    excess_returns = returns - daily_risk_free
    negative_returns = returns[returns < 0]
    
    if len(negative_returns) == 0 or negative_returns.std() == 0:
        return None
    
    return float((excess_returns.mean() / negative_returns.std()) * np.sqrt(252))


def calculate_volatility(equity_curve: pd.Series) -> Optional[float]:
    """Calculate annualized volatility"""
    if len(equity_curve) < 2:
        return None
    
    returns = equity_curve.pct_change().dropna()
    if len(returns) == 0:
        return None
    
    return float(returns.std() * np.sqrt(252))


def calculate_max_drawdown(equity_curve: pd.Series, initial_capital: float) -> Tuple[float, float]:
    """Calculate maximum drawdown in dollars and percentage"""
    if len(equity_curve) == 0:
        return 0.0, 0.0
    
    peak = equity_curve.expanding().max()
    dd_series = (equity_curve - peak) / peak
    max_dd_percent = float(dd_series.min() * 100)
    max_dd_dollars = float((peak - equity_curve).max())
    
    return max_dd_dollars, max_dd_percent


def calculate_calmar_ratio(annual_return_percent: float, max_drawdown_percent: float) -> Optional[float]:
    """Calculate Calmar Ratio"""
    if max_drawdown_percent == 0:
        return None
    return float(annual_return_percent / abs(max_drawdown_percent))


def calculate_recovery_factor(total_return: float, max_drawdown: float) -> Optional[float]:
    """Calculate Recovery Factor"""
    if max_drawdown == 0:
        return None
    return float(total_return / abs(max_drawdown))


def calculate_max_consecutive_wins(df: pd.DataFrame) -> int:
    """Calculate maximum consecutive winning trades"""
    if df.empty:
        return 0
    
    wins = (df['net_pnl'] > 0).astype(int)
    max_consecutive = 0
    current_consecutive = 0
    
    for win in wins:
        if win:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return int(max_consecutive)


def calculate_max_consecutive_losses(df: pd.DataFrame) -> int:
    """Calculate maximum consecutive losing trades"""
    if df.empty:
        return 0
    
    losses = (df['net_pnl'] < 0).astype(int)
    max_consecutive = 0
    current_consecutive = 0
    
    for loss in losses:
        if loss:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return int(max_consecutive)


def calculate_avg_trade_duration(df: pd.DataFrame) -> Optional[float]:
    """Calculate average trade duration in days"""
    if df.empty or 'entry_date' not in df.columns or 'exit_date' not in df.columns:
        return None
    
    try:
        entry_dates = pd.to_datetime(df['entry_date'])
        exit_dates = pd.to_datetime(df['exit_date'])
        durations = (exit_dates - entry_dates).dt.total_seconds() / (24 * 3600)  # Convert to days
        return float(durations.mean())
    except:
        return None


def calculate_trades_per_month(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> Optional[float]:
    """Calculate trading frequency (trades per month)"""
    if df.empty:
        return None
    
    try:
        total_days = (end_date - start_date).days
        if total_days == 0:
            return None
        
        months = total_days / 30.44  # Average days per month
        return float(len(df) / months) if months > 0 else None
    except:
        return None


def calculate_expectancy(df: pd.DataFrame) -> Optional[float]:
    """Calculate expected value per trade"""
    if df.empty:
        return None
    
    return float(df['net_pnl'].mean())


def calculate_strategy_rating(metrics: Dict) -> str:
    """Calculate strategy rating based on multiple metrics"""
    score = 0
    
    # Sharpe Ratio (0-3 points)
    sharpe = metrics.get('sharpe_ratio')
    if sharpe:
        if sharpe > 2.0:
            score += 3
        elif sharpe > 1.5:
            score += 2
        elif sharpe > 1.0:
            score += 1
    
    # Win Rate (0-2 points)
    win_rate = metrics.get('win_rate')
    if win_rate:
        if win_rate > 60:
            score += 2
        elif win_rate > 50:
            score += 1
    
    # Profit Factor (0-2 points)
    profit_factor = metrics.get('profit_factor')
    if profit_factor:
        if profit_factor > 2.0:
            score += 2
        elif profit_factor > 1.5:
            score += 1
    
    # Max Drawdown (0-2 points)
    max_dd = metrics.get('max_drawdown_percent')
    if max_dd:
        if max_dd > -10:
            score += 2
        elif max_dd > -20:
            score += 1
    
    # Total Return (0-1 point)
    total_return = metrics.get('total_return_percent')
    if total_return and total_return > 0:
        score += 1
    
    # Rating assignment
    if score >= 8:
        return 'Excellent'
    elif score >= 6:
        return 'Very Good'
    elif score >= 4:
        return 'Good'
    elif score >= 2:
        return 'Fair'
    else:
        return 'Poor'


def get_rating_color(rating: str) -> str:
    """Get color for strategy rating"""
    colors = {
        'Excellent': '#00ff88',
        'Very Good': '#4ecdc4',
        'Good': '#ffe66d',
        'Fair': '#ffa726',
        'Poor': '#ff6b6b'
    }
    return colors.get(rating, '#4ecdc4')


def create_empty_metrics(initial_capital: float) -> Dict:
    """Create empty metrics for strategies with no trades"""
    return {
        'total_return': 0.0,
        'total_return_percent': 0.0,
        'win_rate': 0.0,
        'winning_trades': 0,
        'total_trades': 0,
        'losing_trades': 0,
        'avg_win': 0.0,
        'avg_loss': 0.0,
        'largest_win': 0.0,
        'largest_loss': 0.0,
        'profit_factor': 0.0,
        'sharpe_ratio': None,
        'sortino_ratio': None,
        'calmar_ratio': None,
        'volatility': None,
        'max_drawdown': 0.0,
        'max_drawdown_percent': 0.0,
        'recovery_factor': None,
        'max_consecutive_wins': 0,
        'max_consecutive_losses': 0,
        'avg_trade_duration': None,
        'trades_per_month': None,
        'expectancy': None,
    }


def calculate_advanced_metrics(equity_curve: pd.Series, trades_data: List[Dict], 
                              risk_free_rate: float = 0.0) -> Dict[str, Any]:
    """
    Calculate advanced metrics from engine_v2.py integration
    
    Args:
        equity_curve: Equity curve as pandas Series
        trades_data: List of trade dictionaries
        risk_free_rate: Risk-free rate for calculations
    
    Returns:
        Dictionary with advanced metrics
    """
    if len(equity_curve) < 2:
        return {}
    
    ret = equity_curve.pct_change().fillna(0.0)
    
    # Calculate time period
    if (equity_curve.index[-1] - equity_curve.index[0]).days <= 0:
        years = 1.0
    else:
        years = (equity_curve.index[-1] - equity_curve.index[0]).days / 365.25
    
    # Basic performance metrics
    total_return = equity_curve.iloc[-1] / equity_curve.iloc[0] - 1.0
    cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else total_return
    vol = ret.std() * np.sqrt(252)
    sharpe = (ret.mean() * 252 - risk_free_rate) / vol if vol > 0 else 0.0
    
    # Drawdown calculation
    peak = equity_curve.cummax()
    dd = (equity_curve / peak - 1.0)
    maxdd = dd.min()
    
    # Advanced trade-based metrics
    if trades_data:
        pnls = [t.get("pnl", 0) for t in trades_data]
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]
        
        win_rate = len(winning_trades) / len(trades_data) if trades_data else 0
        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0
        profit_factor = abs(sum(winning_trades) / sum(losing_trades)) if losing_trades and sum(losing_trades) != 0 else float('inf')
        expectancy = np.mean(pnls) if pnls else 0
        avg_trade = expectancy  # Alias for compatibility
        
        largest_win = max(winning_trades) if winning_trades else 0
        largest_loss = min(losing_trades) if losing_trades else 0
        
        # Consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for pnl in pnls:
            if pnl > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
    else:
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        profit_factor = 0
        expectancy = 0
        avg_trade = 0
        largest_win = 0
        largest_loss = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
    
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
        "Avg Trade": avg_trade,
        "Average Win": avg_win,
        "Average Loss": avg_loss,
        "Largest Win": largest_win,
        "Largest Loss": largest_loss,
        "Total Trades": len(trades_data),
        "Winning Trades": len(winning_trades) if trades_data else 0,
        "Losing Trades": len(losing_trades) if trades_data else 0,
        "Max Consecutive Wins": max_consecutive_wins,
        "Max Consecutive Losses": max_consecutive_losses,
        "Volatility": vol,
        "Volatility %": vol * 100
    }


def calculate_walk_forward_metrics(train_results: List[Dict], test_results: List[Dict]) -> Dict[str, Any]:
    """
    Calculate walk-forward optimization metrics
    
    Args:
        train_results: Training period results
        test_results: Testing period results
    
    Returns:
        Dictionary with walk-forward metrics
    """
    if not test_results:
        return {}
    
    # Calculate out-of-sample performance
    all_returns = []
    all_sharpes = []
    all_drawdowns = []
    all_trades = []
    
    for result in test_results:
        metrics = result.get("metrics", {})
        all_returns.append(metrics.get("Total Return", 0))
        all_sharpes.append(metrics.get("Sharpe Ratio", 0))
        all_drawdowns.append(metrics.get("Max Drawdown", 0))
        all_trades.append(result.get("trades", 0))
    
    oos_performance = {
        "Average Return": np.mean(all_returns),
        "Total Return": np.sum(all_returns),
        "Sharpe Ratio": np.mean(all_sharpes),
        "Max Drawdown": np.mean(all_drawdowns),
        "Total Trades": sum(all_trades),
        "Consistency": len([r for r in all_returns if r > 0]) / len(all_returns) if all_returns else 0,
        "Best Period": max(all_returns) if all_returns else 0,
        "Worst Period": min(all_returns) if all_returns else 0
    }
    
    return oos_performance
