import React, { useState, useEffect } from 'react';
import axios from 'axios';

const StrategyRuleBuilder = ({ strategyId, onRuleCreated }) => {
  const [indicators, setIndicators] = useState({});
  const [operators, setOperators] = useState([]);
  const [actions, setActions] = useState([]);
  const [rules, setRules] = useState([]);
  const [currentRule, setCurrentRule] = useState({
    name: '',
    rule_type: 'condition',
    condition_type: 'indicator',
    action_type: '',
    left_operand: '',
    operator: '',
    right_operand: '',
    logical_operator: 'and',
    priority: 1,
    order: 1,
    is_active: true
  });

  useEffect(() => {
    loadRuleBuilderData();
  }, [strategyId]);

  const loadRuleBuilderData = async () => {
    try {
      const [indicatorsRes, operatorsRes, actionsRes] = await Promise.all([
        axios.get(`/api/strategies/strategies/${strategyId}/rule-builder/`),
        axios.get(`/api/strategies/strategies/${strategyId}/rule-builder/operators/`),
        axios.get(`/api/strategies/strategies/${strategyId}/rule-builder/actions/`)
      ]);
      
      setIndicators(indicatorsRes.data);
      setOperators(operatorsRes.data);
      setActions(actionsRes.data);
    } catch (error) {
      console.error('Error loading rule builder data:', error);
    }
  };

  const handleInputChange = (field, value) => {
    setCurrentRule(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const addRule = () => {
    if (validateRule(currentRule)) {
      const newRule = {
        ...currentRule,
        id: Date.now(), // Temporary ID for frontend
        priority: rules.length + 1
      };
      
      setRules(prev => [...prev, newRule]);
      setCurrentRule({
        name: '',
        rule_type: 'condition',
        condition_type: 'indicator',
        action_type: '',
        left_operand: '',
        operator: '',
        right_operand: '',
        logical_operator: 'and',
        priority: 1,
        order: 1,
        is_active: true
      });
    }
  };

  const validateRule = (rule) => {
    if (rule.rule_type === 'condition') {
      return rule.name && rule.left_operand && rule.operator && rule.right_operand;
    } else if (rule.rule_type === 'action') {
      return rule.name && rule.action_type;
    }
    return false;
  };

  const removeRule = (ruleId) => {
    setRules(prev => prev.filter(rule => rule.id !== ruleId));
  };

  const moveRule = (ruleId, direction) => {
    setRules(prev => {
      const newRules = [...prev];
      const currentIndex = newRules.findIndex(rule => rule.id === ruleId);
      
      if (direction === 'up' && currentIndex > 0) {
        [newRules[currentIndex], newRules[currentIndex - 1]] = 
        [newRules[currentIndex - 1], newRules[currentIndex]];
      } else if (direction === 'down' && currentIndex < newRules.length - 1) {
        [newRules[currentIndex], newRules[currentIndex + 1]] = 
        [newRules[currentIndex + 1], newRules[currentIndex]];
      }
      
      return newRules;
    });
  };

  const saveRules = async () => {
    try {
      // Save each rule to the backend
      for (const rule of rules) {
        await axios.post(`/api/strategies/strategies/${strategyId}/rules/`, rule);
      }
      
      onRuleCreated && onRuleCreated(rules);
      alert('Rules saved successfully!');
    } catch (error) {
      console.error('Error saving rules:', error);
      alert('Error saving rules');
    }
  };

  const testRule = async (rule) => {
    try {
      const response = await axios.post(
        `/api/strategies/strategies/${strategyId}/rule-builder/test/`,
        { rule }
      );
      
      if (response.data.test_passed) {
        alert(`Rule "${rule.name}" is valid!`);
      } else {
        alert(`Rule "${rule.name}" failed: ${response.data.message}`);
      }
    } catch (error) {
      console.error('Error testing rule:', error);
      alert('Error testing rule');
    }
  };

  return (
    <div className="strategy-rule-builder">
      <h3>Strategy Rule Builder</h3>
      
      {/* Rule Creation Form */}
      <div className="rule-form">
        <h4>Create New Rule</h4>
        
        <div className="form-row">
          <input
            type="text"
            placeholder="Rule Name"
            value={currentRule.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
          />
          
          <select
            value={currentRule.rule_type}
            onChange={(e) => handleInputChange('rule_type', e.target.value)}
          >
            <option value="condition">Condition</option>
            <option value="action">Action</option>
            <option value="filter">Filter</option>
          </select>
        </div>

        {currentRule.rule_type === 'condition' && (
          <>
            <div className="form-row">
              <select
                value={currentRule.condition_type}
                onChange={(e) => handleInputChange('condition_type', e.target.value)}
              >
                <option value="indicator">Technical Indicator</option>
                <option value="price">Price Action</option>
                <option value="volume">Volume</option>
                <option value="time">Time</option>
                <option value="custom">Custom</option>
              </select>
              
              <select
                value={currentRule.left_operand}
                onChange={(e) => handleInputChange('left_operand', e.target.value)}
              >
                <option value="">Select Indicator</option>
                {indicators.trend_indicators?.map(indicator => (
                  <option key={indicator.name} value={indicator.name}>
                    {indicator.label}
                  </option>
                ))}
                {indicators.momentum_indicators?.map(indicator => (
                  <option key={indicator.name} value={indicator.name}>
                    {indicator.label}
                  </option>
                ))}
                {indicators.price_indicators?.map(indicator => (
                  <option key={indicator.name} value={indicator.name}>
                    {indicator.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <select
                value={currentRule.operator}
                onChange={(e) => handleInputChange('operator', e.target.value)}
              >
                <option value="">Select Operator</option>
                {operators.map(op => (
                  <option key={op.value} value={op.value}>
                    {op.label}
                  </option>
                ))}
              </select>
              
              <input
                type="text"
                placeholder="Value (e.g., 50, sma_20)"
                value={currentRule.right_operand}
                onChange={(e) => handleInputChange('right_operand', e.target.value)}
              />
            </div>
          </>
        )}

        {currentRule.rule_type === 'action' && (
          <div className="form-row">
            <select
              value={currentRule.action_type}
              onChange={(e) => handleInputChange('action_type', e.target.value)}
            >
              <option value="">Select Action</option>
              {actions.map(action => (
                <option key={action.value} value={action.value}>
                  {action.label}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="form-row">
          <select
            value={currentRule.logical_operator}
            onChange={(e) => handleInputChange('logical_operator', e.target.value)}
          >
            <option value="and">AND</option>
            <option value="or">OR</option>
          </select>
          
          <button 
            className="btn btn-primary"
            onClick={addRule}
            disabled={!validateRule(currentRule)}
          >
            Add Rule
          </button>
        </div>
      </div>

      {/* Rules List */}
      <div className="rules-list">
        <h4>Strategy Rules ({rules.length})</h4>
        
        {rules.map((rule, index) => (
          <div key={rule.id} className="rule-item">
            <div className="rule-header">
              <span className="rule-priority">#{rule.priority}</span>
              <span className="rule-name">{rule.name}</span>
              <span className="rule-type">{rule.rule_type}</span>
            </div>
            
            <div className="rule-content">
              {rule.rule_type === 'condition' && (
                <span>
                  {rule.left_operand} {rule.operator} {rule.right_operand}
                </span>
              )}
              
              {rule.rule_type === 'action' && (
                <span>{rule.action_type}</span>
              )}
            </div>
            
            <div className="rule-actions">
              <button 
                className="btn btn-sm btn-secondary"
                onClick={() => testRule(rule)}
              >
                Test
              </button>
              
              <button 
                className="btn btn-sm btn-secondary"
                onClick={() => moveRule(rule.id, 'up')}
                disabled={index === 0}
              >
                ↑
              </button>
              
              <button 
                className="btn btn-sm btn-secondary"
                onClick={() => moveRule(rule.id, 'down')}
                disabled={index === rules.length - 1}
              >
                ↓
              </button>
              
              <button 
                className="btn btn-sm btn-danger"
                onClick={() => removeRule(rule.id)}
              >
                Remove
              </button>
            </div>
          </div>
        ))}
        
        {rules.length === 0 && (
          <p className="no-rules">No rules created yet. Add your first rule above.</p>
        )}
      </div>

      {/* Save Button */}
      {rules.length > 0 && (
        <div className="save-section">
          <button 
            className="btn btn-success btn-lg"
            onClick={saveRules}
          >
            Save All Rules
          </button>
        </div>
      )}
    </div>
  );
};

export default StrategyRuleBuilder;
