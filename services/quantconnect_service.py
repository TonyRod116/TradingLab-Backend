import hashlib
import base64
import time
import requests
import json
from typing import Dict, Any, Optional
from .quantconnect_parser import QuantConnectNaturalLanguageParser


class QuantConnectService:
    """
    Service class to handle QuantConnect API v2 calls from Django backend
    """
    
    def __init__(self):
        self.base_url = 'https://www.quantconnect.com/api/v2'
        self.user_id = 414810
        self.api_token = '79b91dd67dbbbfa4129888180d2de06d773de7eb4c8df86761bb7926d0d6d8cf'
        self.parser = QuantConnectNaturalLanguageParser()
    
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
        Run a complete backtest workflow with natural language parsing and compilation
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
            
            # Step 2: Generate strategy code using natural language parser
            if description:
                strategy_code = self.parser.parse_strategy_description(description, strategy_data)
            elif strategy_data:
                strategy_code = self.parser.parse_advanced_strategy(strategy_data)
            else:
                strategy_code = self.parser._generate_default_code()
            
            # Step 3: Create main.py file in the project
            file_result = self.create_file(project_id, 'main.py', strategy_code)
            
            if not file_result['success']:
                return {
                    'success': False,
                    'error': f'File creation failed: {file_result["error"]}'
                }
            
            # Step 4: Create compilation job
            compile_result = self.create_compilation_job(project_id)
            
            if not compile_result['success']:
                return {
                    'success': False,
                    'error': f'Compilation job creation failed: {compile_result["error"]}'
                }
            
            compile_id = compile_result['data']['compileId']
            
            # Step 5: Check compilation result (with retry logic)
            compilation_status = self._wait_for_compilation(project_id, compile_id)
            
            if not compilation_status['success']:
                return {
                    'success': False,
                    'error': f'Compilation failed: {compilation_status["error"]}'
                }
            
            # Step 6: Return complete result
            backtest_result = {
                'projectId': project_id,
                'projectName': project_name,
                'compileId': compile_id,
                'strategyCode': strategy_code,
                'compilationStatus': compilation_status['data']['state'],
                'status': 'compiled',
                'message': 'Project created, code generated, and compiled successfully.'
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
    
    def _wait_for_compilation(self, project_id: int, compile_id: str, max_attempts: int = 10) -> Dict[str, Any]:
        """
        Wait for compilation to complete with retry logic
        """
        import time
        
        for attempt in range(max_attempts):
            result = self.read_compilation_result(project_id, compile_id)
            
            if not result['success']:
                return result
            
            state = result['data'].get('state', '')
            
            if state == 'BuildSuccess':
                return result
            elif state == 'BuildError':
                return {
                    'success': False,
                    'error': f'Compilation failed: {result["data"].get("logs", [])}'
                }
            elif state == 'InQueue':
                # Still compiling, wait and retry
                time.sleep(2)
                continue
            else:
                # Unknown state, wait and retry
                time.sleep(2)
                continue
        
        return {
            'success': False,
            'error': 'Compilation timeout - maximum attempts reached'
        }
    
    def parse_natural_language_strategy(self, description: str, strategy_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Parse natural language strategy description to QuantConnect code
        """
        try:
            if not description:
                return {
                    'success': False,
                    'error': 'Description is required'
                }
            
            # Parse the description to generate code
            strategy_code = self.parser.parse_strategy_description(description, strategy_data)
            
            return {
                'success': True,
                'data': {
                    'strategyCode': strategy_code,
                    'description': description,
                    'message': 'Strategy parsed successfully'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Parsing error: {str(e)}'
            }
    
    def create_and_compile_strategy(self, description: str, strategy_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create project, parse strategy, and compile in one step
        """
        try:
            # Parse the strategy first
            parse_result = self.parse_natural_language_strategy(description, strategy_data)
            
            if not parse_result['success']:
                return parse_result
            
            strategy_code = parse_result['data']['strategyCode']
            
            # Create project
            project_name = f'Strategy_{int(time.time())}'
            project_result = self.create_project(project_name, 'Python')
            
            if not project_result['success']:
                return {
                    'success': False,
                    'error': f'Project creation failed: {project_result["error"]}'
                }
            
            project_id = project_result['data']['projects'][0]['projectId']
            
            # Create main.py file
            file_result = self.create_file(project_id, 'main.py', strategy_code)
            
            if not file_result['success']:
                return {
                    'success': False,
                    'error': f'File creation failed: {file_result["error"]}'
                }
            
            # Compile the project
            compile_result = self.create_compilation_job(project_id)
            
            if not compile_result['success']:
                return {
                    'success': False,
                    'error': f'Compilation failed: {compile_result["error"]}'
                }
            
            compile_id = compile_result['data']['compileId']
            
            # Wait for compilation
            compilation_status = self._wait_for_compilation(project_id, compile_id)
            
            return {
                'success': True,
                'data': {
                    'projectId': project_id,
                    'projectName': project_name,
                    'compileId': compile_id,
                    'strategyCode': strategy_code,
                    'compilationStatus': compilation_status['data']['state'] if compilation_status['success'] else 'Failed',
                    'message': 'Strategy created and compiled successfully'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Strategy creation error: {str(e)}'
            }
    
    def create_compilation_job(self, project_id: int) -> Dict[str, Any]:
        """
        Create a compilation job for a QuantConnect project
        """
        try:
            headers = self._generate_auth_headers()
            
            payload = {
                'projectId': project_id
            }
            
            response = requests.post(
                f'{self.base_url}/compile/create',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            return {
                'success': response.ok and result.get('success', False),
                'data': result,
                'status': response.status_code,
                'error': None if response.ok else result.get('message', f'Compilation job creation failed. Status: {response.status_code}, Response: {result}')
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
    
    def read_compilation_result(self, project_id: int, compile_id: str) -> Dict[str, Any]:
        """
        Read compilation result for a specific project and compile ID
        """
        try:
            headers = self._generate_auth_headers()
            
            payload = {
                'projectId': project_id,
                'compileId': compile_id
            }
            
            response = requests.post(
                f'{self.base_url}/compile/read',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            return {
                'success': response.ok and result.get('success', False),
                'data': result,
                'status': response.status_code,
                'error': None if response.ok else result.get('message', f'Compilation result read failed. Status: {response.status_code}, Response: {result}')
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
    
    def create_file(self, project_id: int, name: str, content: str) -> Dict[str, Any]:
        """
        Create a file in a QuantConnect project
        """
        try:
            headers = self._generate_auth_headers()
            
            payload = {
                'projectId': project_id,
                'name': name,
                'content': content
            }
            
            response = requests.post(
                f'{self.base_url}/files/create',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            return {
                'success': response.ok and result.get('success', False),
                'data': result,
                'status': response.status_code,
                'error': None if response.ok else result.get('message', f'File creation failed. Status: {response.status_code}, Response: {result}')
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
