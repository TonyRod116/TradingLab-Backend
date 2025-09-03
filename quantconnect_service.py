import hashlib
import base64
import time
import requests
import json
from typing import Dict, Any, Optional


class QuantConnectService:
    """
    Service class to handle QuantConnect API v2 calls from Django backend
    """
    
    def __init__(self):
        self.base_url = 'https://www.quantconnect.com/api/v2'
        self.user_id = 414810
        self.api_token = '79b91dd67dbbbfa4129888180d2de06d773de7eb4c8df86761bb7926d0d6d8cf'
    
    def _generate_auth_headers(self) -> Dict[str, str]:
        """
        Generate QuantConnect authentication headers
        """
        timestamp = str(int(time.time()))
        time_stamped_token = f'{self.api_token}:{timestamp}'
        
        # Create SHA-256 hash
        hashed_token = hashlib.sha256(time_stamped_token.encode('utf-8')).hexdigest()
        authentication = f'{self.user_id}:{hashed_token}'
        authentication_b64 = base64.b64encode(authentication.encode('utf-8')).decode('ascii')
        
        return {
            'Authorization': f'Basic {authentication_b64}',
            'Timestamp': timestamp,
            'Content-Type': 'application/json'
        }
    
    def test_authentication(self) -> Dict[str, Any]:
        """
        Test QuantConnect authentication
        """
        try:
            headers = self._generate_auth_headers()
            
            response = requests.post(
                f'{self.base_url}/authenticate',
                headers=headers,
                json={},
                timeout=30
            )
            
            result = response.json()
            
            return {
                'success': response.ok and result.get('success', False),
                'data': result,
                'status': response.status_code,
                'error': None if response.ok else result.get('message', 'Authentication failed')
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def create_project(self, name: str, language: str = 'Python') -> Dict[str, Any]:
        """
        Create a new project in QuantConnect
        """
        try:
            headers = self._generate_auth_headers()
            
            payload = {
                'name': name,
                'language': language
            }
            
            response = requests.post(
                f'{self.base_url}/projects/create',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            return {
                'success': response.ok and result.get('success', False),
                'data': result,
                'status': response.status_code,
                'error': None if response.ok else result.get('message', f'Project creation failed. Status: {response.status_code}, Response: {result}')
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def test_project_creation(self) -> Dict[str, Any]:
        """
        Test project creation (simplified test)
        """
        try:
            project_name = f'Test_Project_{int(time.time())}'
            project_result = self.create_project(project_name, 'Python')
            
            if not project_result['success']:
                return {
                    'success': False,
                    'error': f'Project creation failed: {project_result["error"]}'
                }
            
            project_id = project_result['data']['projects'][0]['projectId']
            
            return {
                'success': True,
                'data': {
                    'projectId': project_id,
                    'projectName': project_name,
                    'message': 'Project created successfully'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Project creation test error: {str(e)}'
            }
    
    def run_complete_workflow(self, strategy_data: Dict[str, Any], description: str = '') -> Dict[str, Any]:
        """
        Run a complete backtest workflow
        """
        try:
            # Step 1: Create project
            project_name = f'Backtest_{int(time.time())}'
            project_result = self.create_project(project_name, 'Python')
            
            if not project_result['success']:
                return {
                    'success': False,
                    'error': f'Project creation failed: {project_result["error"]}'
                }
            
            project_id = project_result['data']['projects'][0]['projectId']
            
            # Step 2: Generate strategy code (placeholder for now)
            strategy_code = self._generate_strategy_code(strategy_data, description)
            
            # Step 3: Compile and run backtest (placeholder for now)
            backtest_result = {
                'projectId': project_id,
                'projectName': project_name,
                'strategyCode': strategy_code,
                'status': 'created',
                'message': 'Project created successfully. Backtest implementation pending.'
            }
            
            return {
                'success': True,
                'data': backtest_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Workflow error: {str(e)}'
            }
    
    def _generate_strategy_code(self, strategy_data: Dict[str, Any], description: str) -> str:
        """
        Generate QuantConnect strategy code from strategy data
        """
        # Placeholder implementation - will be expanded later
        base_code = """
from AlgorithmImports import *

class TradingAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)
        
        # Add strategy logic here
        self.AddEquity("SPY", Resolution.Daily)
        
    def OnData(self, data):
        # Strategy implementation
        pass
"""
        return base_code
