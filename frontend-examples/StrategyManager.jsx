import React, { useState, useEffect } from 'react';
import axios from 'axios';
import StrategyRuleBuilder from './StrategyRuleBuilder';

const StrategyManager = () => {
  const [strategies, setStrategies] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showRuleBuilder, setShowRuleBuilder] = useState(false);
  const [newStrategy, setNewStrategy] = useState({
    name: '',
    description: '',
    strategy_type: 'custom',
    symbol: 'ES',
    timeframe: '1m',
    position_size: '1.00',
    max_positions: 1,
    stop_loss_pips: 50,
    take_profit_pips: 100,
    backtest_enabled: true
  });

  useEffect(() => {
    loadStrategies();
    loadTemplates();
  }, []);

  const loadStrategies = async () => {
    try {
      const response = await axios.get('/api/strategies/strategies/');
      setStrategies(response.data);
    } catch (error) {
      console.error('Error loading strategies:', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await axios.get('/api/strategies/templates/');
      setTemplates(response.data);
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  const handleCreateStrategy = async () => {
    try {
      const response = await axios.post('/api/strategies/strategies/', newStrategy);
      setStrategies(prev => [...prev, response.data]);
      setShowCreateForm(false);
      setNewStrategy({
        name: '',
        description: '',
        strategy_type: 'custom',
        symbol: 'ES',
        timeframe: '1m',
        position_size: '1.00',
        max_positions: 1,
        stop_loss_pips: 50,
        take_profit_pips: 100,
        backtest_enabled: true
      });
    } catch (error) {
      console.error('Error creating strategy:', error);
      alert('Error creating strategy');
    }
  };

  const createFromTemplate = async (templateName) => {
    try {
      const response = await axios.post('/api/strategies/create-from-template/', {
        template_name: templateName,
        name: `${templateName} - Custom`,
        description: `Custom version of ${templateName}`,
        symbol: 'ES',
        timeframe: '1m'
      });
      
      setStrategies(prev => [...prev, response.data]);
      alert('Strategy created from template successfully!');
    } catch (error) {
      console.error('Error creating from template:', error);
      alert('Error creating from template');
    }
  };

  const updateStrategyStatus = async (strategyId, status) => {
    try {
      const response = await axios.post(`/api/strategies/strategies/${strategyId}/${status}/`);
      
      setStrategies(prev => 
        prev.map(strategy => 
          strategy.id === strategyId 
            ? { ...strategy, status: response.data.status }
            : strategy
        )
      );
    } catch (error) {
      console.error(`Error ${status} strategy:`, error);
    }
  };

  const runBacktest = async (strategyId) => {
    try {
      const response = await axios.post(`/api/strategies/strategies/${strategyId}/backtest/run/`, {
        start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days ago
        end_date: new Date().toISOString(),
        initial_capital: 10000.00,
        commission: 0.00,
        slippage: 0.00
      });
      
      alert(`Backtest completed! Win Rate: ${response.data.win_rate}%`);
      
      // Refresh strategies to get updated metrics
      loadStrategies();
    } catch (error) {
      console.error('Error running backtest:', error);
      alert('Error running backtest');
    }
  };

  const deleteStrategy = async (strategyId) => {
    if (window.confirm('Are you sure you want to delete this strategy?')) {
      try {
        await axios.delete(`/api/strategies/strategies/${strategyId}/`);
        setStrategies(prev => prev.filter(strategy => strategy.id !== strategyId));
        if (selectedStrategy?.id === strategyId) {
          setSelectedStrategy(null);
          setShowRuleBuilder(false);
        }
      } catch (error) {
        console.error('Error deleting strategy:', error);
        alert('Error deleting strategy');
      }
    }
  };

  return (
    <div className="strategy-manager">
      <div className="header">
        <h2>Trading Strategy Manager</h2>
        <div className="header-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setShowCreateForm(true)}
          >
            Create New Strategy
          </button>
          <button 
            className="btn btn-secondary"
            onClick={() => setShowCreateForm(false)}
          >
            Show Templates
          </button>
        </div>
      </div>

      {/* Create Strategy Form */}
      {showCreateForm && (
        <div className="create-strategy-form">
          <h3>Create New Strategy</h3>
          <div className="form-grid">
            <input
              type="text"
              placeholder="Strategy Name"
              value={newStrategy.name}
              onChange={(e) => setNewStrategy(prev => ({ ...prev, name: e.target.value }))}
            />
            
            <textarea
              placeholder="Description"
              value={newStrategy.description}
              onChange={(e) => setNewStrategy(prev => ({ ...prev, description: e.target.value }))}
            />
            
            <select
              value={newStrategy.strategy_type}
              onChange={(e) => setNewStrategy(prev => ({ ...prev, strategy_type: e.target.value }))}
            >
              <option value="trend_following">Trend Following</option>
              <option value="mean_reversion">Mean Reversion</option>
              <option value="breakout">Breakout</option>
              <option value="scalping">Scalping</option>
              <option value="swing">Swing Trading</option>
              <option value="custom">Custom</option>
            </select>
            
            <input
              type="text"
              placeholder="Symbol (e.g., ES)"
              value={newStrategy.symbol}
              onChange={(e) => setNewStrategy(prev => ({ ...prev, symbol: e.target.value }))}
            />
            
            <select
              value={newStrategy.timeframe}
              onChange={(e) => setNewStrategy(prev => ({ ...prev, timeframe: e.target.value }))}
            >
              <option value="1m">1 Minute</option>
              <option value="5m">5 Minutes</option>
              <option value="15m">15 Minutes</option>
              <option value="1h">1 Hour</option>
              <option value="4h">4 Hours</option>
              <option value="1d">1 Day</option>
            </select>
            
            <input
              type="number"
              placeholder="Position Size"
              value={newStrategy.position_size}
              onChange={(e) => setNewStrategy(prev => ({ ...prev, position_size: e.target.value }))}
            />
            
            <input
              type="number"
              placeholder="Stop Loss (pips)"
              value={newStrategy.stop_loss_pips}
              onChange={(e) => setNewStrategy(prev => ({ ...prev, stop_loss_pips: parseInt(e.target.value) }))}
            />
            
            <input
              type="number"
              placeholder="Take Profit (pips)"
              value={newStrategy.take_profit_pips}
              onChange={(e) => setNewStrategy(prev => ({ ...prev, take_profit_pips: parseInt(e.target.value) }))}
            />
          </div>
          
          <div className="form-actions">
            <button 
              className="btn btn-success"
              onClick={handleCreateStrategy}
              disabled={!newStrategy.name}
            >
              Create Strategy
            </button>
            <button 
              className="btn btn-secondary"
              onClick={() => setShowCreateForm(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Strategy Templates */}
      {!showCreateForm && (
        <div className="strategy-templates">
          <h3>Strategy Templates</h3>
          <div className="templates-grid">
            {templates.map((template, index) => (
              <div key={index} className="template-card">
                <h4>{template.name}</h4>
                <p>{template.description}</p>
                <span className="template-type">{template.strategy_type}</span>
                <button 
                  className="btn btn-primary"
                  onClick={() => createFromTemplate(template.name)}
                >
                  Use Template
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Strategies List */}
      <div className="strategies-list">
        <h3>Your Strategies ({strategies.length})</h3>
        
        {strategies.map(strategy => (
          <div key={strategy.id} className="strategy-card">
            <div className="strategy-header">
              <h4>{strategy.name}</h4>
              <span className={`status status-${strategy.status}`}>
                {strategy.status}
              </span>
            </div>
            
            <div className="strategy-info">
              <p>{strategy.description}</p>
              <div className="strategy-metrics">
                <span>Symbol: {strategy.symbol}</span>
                <span>Timeframe: {strategy.timeframe}</span>
                <span>Type: {strategy.strategy_type}</span>
              </div>
              
              {strategy.total_trades > 0 && (
                <div className="performance-metrics">
                  <span>Win Rate: {strategy.win_rate}%</span>
                  <span>Total Trades: {strategy.total_trades}</span>
                  <span>Profit Factor: {strategy.profit_factor}</span>
                </div>
              )}
            </div>
            
            <div className="strategy-actions">
              <button 
                className="btn btn-sm btn-primary"
                onClick={() => {
                  setSelectedStrategy(strategy);
                  setShowRuleBuilder(true);
                }}
              >
                Edit Rules
              </button>
              
              <button 
                className="btn btn-sm btn-secondary"
                onClick={() => runBacktest(strategy.id)}
              >
                Run Backtest
              </button>
              
              {strategy.status === 'draft' && (
                <button 
                  className="btn btn-sm btn-success"
                  onClick={() => updateStrategyStatus(strategy.id, 'activate')}
                >
                  Activate
                </button>
              )}
              
              {strategy.status === 'active' && (
                <button 
                  className="btn btn-sm btn-warning"
                  onClick={() => updateStrategyStatus(strategy.id, 'pause')}
                >
                  Pause
                </button>
              )}
              
              {strategy.status === 'paused' && (
                <button 
                  className="btn btn-sm btn-success"
                  onClick={() => updateStrategyStatus(strategy.id, 'activate')}
                >
                  Resume
                </button>
              )}
              
              <button 
                className="btn btn-sm btn-danger"
                onClick={() => deleteStrategy(strategy.id)}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
        
        {strategies.length === 0 && (
          <p className="no-strategies">
            No strategies created yet. Create your first strategy or use a template above.
          </p>
        )}
      </div>

      {/* Rule Builder Modal */}
      {showRuleBuilder && selectedStrategy && (
        <div className="rule-builder-modal">
          <div className="modal-header">
            <h3>Rule Builder - {selectedStrategy.name}</h3>
            <button 
              className="btn btn-secondary"
              onClick={() => {
                setShowRuleBuilder(false);
                setSelectedStrategy(null);
              }}
            >
              Close
            </button>
          </div>
          
          <StrategyRuleBuilder 
            strategyId={selectedStrategy.id}
            onRuleCreated={() => {
              loadStrategies();
              setShowRuleBuilder(false);
              setSelectedStrategy(null);
            }}
          />
        </div>
      )}
    </div>
  );
};

export default StrategyManager;
