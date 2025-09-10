#!/usr/bin/env python
"""
Script to generate equity curve data for existing backtests
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from strategies.models import BacktestResult, EquityCurvePoint
import random

def generate_equity_curve_for_backtest(backtest):
    """Generate sample equity curve data for a backtest"""
    if not backtest.start_date or not backtest.end_date:
        print(f"❌ Skipping backtest {backtest.id} - missing dates")
        return
    
    # Clear existing equity curve data
    backtest.equity_curve.all().delete()
    
    # Generate equity curve points
    start_date = backtest.start_date
    end_date = backtest.end_date
    initial_capital = float(backtest.initial_capital)
    total_return = float(backtest.total_return) if backtest.total_return else 0
    
    # Create daily points
    current_date = start_date
    equity_value = initial_capital
    max_equity = initial_capital
    points = []
    
    while current_date <= end_date:
        # Simulate daily equity changes
        daily_change = random.uniform(-0.02, 0.03)  # -2% to +3% daily change
        equity_value = equity_value * (1 + daily_change)
        
        # Calculate drawdown
        if equity_value > max_equity:
            max_equity = equity_value
        drawdown = (equity_value - max_equity) / max_equity if max_equity > 0 else 0
        
        points.append(EquityCurvePoint(
            backtest=backtest,
            timestamp=current_date,
            equity_value=Decimal(str(round(equity_value, 2))),
            drawdown=Decimal(str(round(drawdown, 4)))
        )
        
        current_date += timedelta(days=1)
    
    # Ensure final value matches total return
    if points:
        final_value = initial_capital + total_return
        points[-1].equity_value = Decimal(str(round(final_value, 2)))
        points[-1].drawdown = Decimal(str(round((final_value - max_equity) / max_equity, 4))) if max_equity > 0 else Decimal('0')
    
    # Bulk create points
    EquityCurvePoint.objects.bulk_create(points)
    print(f"✅ Generated {len(points)} equity curve points for backtest {backtest.id}")

def main():
    """Generate equity curves for all backtests"""
    print("🚀 Starting equity curve generation...")
    
    backtests = BacktestResult.objects.all()
    print(f"📊 Found {backtests.count()} backtests")
    
    for backtest in backtests:
        try:
            generate_equity_curve_for_backtest(backtest)
        except Exception as e:
            print(f"❌ Error generating equity curve for backtest {backtest.id}: {e}")
    
    print("✅ Equity curve generation completed!")

if __name__ == "__main__":
    main()
