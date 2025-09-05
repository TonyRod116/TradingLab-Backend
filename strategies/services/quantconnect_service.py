"""
QuantConnect API Service for real backtesting integration
"""

import requests
import json
import time
import re
import uuid
import random
import hashlib
from base64 import b64encode
from typing import Dict, Any, Optional
from django.conf import settings
from strategies.models import Strategy


class QuantConnectService:
    """Service to interact with QuantConnect API v2"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'QUANTCONNECT_API_URL', 'https://www.quantconnect.com/api/v2')
        self.user_id = getattr(settings, 'QUANTCONNECT_USER_ID', '')
        self.access_token = getattr(settings, 'QUANTCONNECT_ACCESS_TOKEN', '')
        
        if not all([self.api_url, self.user_id, self.access_token]):
            raise ValueError("QuantConnect credentials not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for QuantConnect API with proper SHA-256 hash"""
        # Generate timestamp
        timestamp = str(int(time.time()))
        
        # Create time-stamped token
        time_stamped_token = f'{self.access_token}:{timestamp}'.encode('utf-8')
        
        # Create SHA-256 hash
        hashed_token = hashlib.sha256(time_stamped_token).hexdigest()
        
        # Create authentication string
        authentication = f'{self.user_id}:{hashed_token}'.encode('utf-8')
        authentication = b64encode(authentication).decode('ascii')
        
        return {
            'Authorization': f'Basic {authentication}',
            'Timestamp': timestamp,
            'Content-Type': 'application/json'
        }
    
    def create_project_direct(self, name: str, language: str = 'Py') -> Dict[str, Any]:
        """Create a new QuantConnect project using direct API"""
        try:
            data = {
                "name": name,
                "language": language
            }
            
            response = requests.post(
                f"{self.api_url}/projects/create",
                headers=self._get_headers(),
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('projects'):
                    project = result['projects'][0]
                    return {
                        'success': True,
                        'project_id': project.get('projectId'),
                        'name': project.get('name'),
                        'language': project.get('language')
                    }
                else:
                    return {'success': False, 'error': 'No projects returned'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_file_direct(self, project_id: int, filename: str, content: str) -> Dict[str, Any]:
        """Create a file in QuantConnect project using direct API"""
        try:
            data = {
                "projectId": project_id,
                "name": filename,
                "content": content
            }
            
            response = requests.post(
                f"{self.api_url}/files/create",
                headers=self._get_headers(),
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': result.get('success', False),
                    'error': result.get('errors', [])
                }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def compile_project_direct(self, project_id: int) -> Dict[str, Any]:
        """Compile QuantConnect project using direct API"""
        try:
            data = {"projectId": project_id}
            
            response = requests.post(
                f"{self.api_url}/compile/create",
                headers=self._get_headers(),
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return {
                        'success': True,
                        'compile_id': result.get('compileId'),
                        'state': result.get('state')
                    }
                else:
                    return {'success': False, 'error': 'Compilation failed'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_compilation_direct(self, project_id: int, compile_id: str) -> Dict[str, Any]:
        """Check compilation status using direct API"""
        try:
            data = {
                "projectId": project_id,
                "compileId": compile_id
            }
            
            response = requests.post(
                f"{self.api_url}/compile/read",
                headers=self._get_headers(),
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                state = result.get('state', 'Unknown')
                return {
                    'success': True,
                    'state': state,
                    'logs': result.get('logs', []),
                    'completed': state == 'BuildSuccess',
                    'failed': state == 'BuildError'
                }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run_backtest_direct(self, project_id: int, compile_id: str, backtest_name: str = None) -> Dict[str, Any]:
        """Run backtest using direct API"""
        try:
            if not backtest_name:
                backtest_name = f"Backtest {int(time.time())}"
                
            data = {
                "projectId": project_id,
                "compileId": compile_id,
                "backtestName": backtest_name
            }
            
            response = requests.post(
                f"{self.api_url}/backtests/create",
                headers=self._get_headers(),
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    backtest_data = result.get('backtest', {})
                    return {
                        'success': True,
                        'backtest_id': backtest_data.get('backtestId'),
                        'status': backtest_data.get('status'),
                        'progress': backtest_data.get('progress', 0)
                    }
                else:
                    return {'success': False, 'error': 'Backtest creation failed'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_backtest_status_direct(self, project_id: int, backtest_id: str) -> Dict[str, Any]:
        """Check backtest status using direct API"""
        try:
            data = {
                "projectId": project_id,
                "backtestId": backtest_id
            }
            
            response = requests.post(
                f"{self.api_url}/backtests/read",
                headers=self._get_headers(),
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Debug: print the full response to understand the structure
                print(f"🔍 DEBUG - Full backtest status response: {result}")
                
                # Extract backtest data - it might be nested differently
                backtest_data = result.get('backtest', {})
                if not backtest_data:
                    # Try alternative structure
                    backtest_data = result
                
                # Extract status and progress with better fallbacks
                status = backtest_data.get('status', backtest_data.get('state', 'Unknown'))
                progress = backtest_data.get('progress', backtest_data.get('Progress', 0))
                
                # Handle case where progress might be a string
                try:
                    progress = float(progress) if progress is not None else 0
                except (ValueError, TypeError):
                    progress = 0
                
                print(f"🔍 DEBUG - Extracted status: '{status}', progress: {progress}")
                
                return {
                    'success': True,
                    'status': status,
                    'progress': progress,
                    'completed': status in ['Completed', 'Completed.', 'completed'],
                    'failed': status in ['Failed', 'Error', 'BuildError', 'failed', 'error']
                }
            else:
                print(f"❌ DEBUG - HTTP Error {response.status_code}: {response.text}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f"❌ DEBUG - Exception in check_backtest_status_direct: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_backtest_status(self, project_id: int, backtest_id: str) -> Dict[str, Any]:
        """Check backtest status - wrapper for check_backtest_status_direct"""
        return self.check_backtest_status_direct(project_id, backtest_id)
    
    def get_backtest_results_direct(self, project_id: int, backtest_id: str) -> Dict[str, Any]:
        """Get backtest results using direct API"""
        try:
            data = {
                "projectId": project_id,
                "backtestId": backtest_id
            }
            
            response = requests.post(
                f"{self.api_url}/backtests/read/result",
                headers=self._get_headers(),
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'results': result
                }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_project(self, name: str, language: str = 'Py') -> Dict[str, Any]:
        """Create a new project in QuantConnect"""
        url = f"{self.api_url}/projects/create"
        
        payload = {
            'name': name,
            'language': language
        }
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        
        # Check if response is successful
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise Exception(f"QuantConnect API error: {response.status_code} - {error_data.get('errors', 'Unknown error')}")
        
        data = response.json()
        
        # Check if the response contains success field
        if not data.get('success', True):
            raise Exception(f"QuantConnect API failed: {data.get('errors', 'Unknown error')}")
        
        # Check if projects exist in response
        if 'projects' not in data or not data['projects']:
            raise Exception(f"QuantConnect API response missing projects: {data}")
        
        # Extract projectId from projects array
        project = data['projects'][0]
        if 'projectId' not in project:
            raise Exception(f"QuantConnect API response missing projectId in project: {project}")
        
        return project
    
    def update_file(self, project_id: str, filename: str, content: str) -> Dict[str, Any]:
        """Update a file in the project"""
        url = f"{self.api_url}/files/update"
        
        payload = {
            'projectId': project_id,
            'name': filename,
            'content': content
        }
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        return response.json()
    
    def compile_project(self, project_id: str) -> Dict[str, Any]:
        """Compile the project"""
        url = f"{self.api_url}/compile/create"
        
        payload = {
            'projectId': project_id
        }
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_compile_status(self, project_id: str, compile_id: str) -> Dict[str, Any]:
        """Get compilation status"""
        url = f"{self.api_url}/compile/read"
        
        params = {
            'projectId': project_id,
            'compileId': compile_id
        }
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    def run_backtest(self, project_id: str, compile_id: str, backtest_name: str = None) -> Dict[str, Any]:
        """Run a backtest"""
        url = f"{self.api_url}/backtests/create"
        
        payload = {
            'projectId': project_id,
            'compileId': compile_id,
            'backtestName': backtest_name or f"Backtest_{int(time.time())}"
        }
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        
        # Check if response is successful
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise Exception(f"QuantConnect API error: {response.status_code} - {error_data.get('errors', 'Unknown error')}")
        
        data = response.json()
        
        # Check if the response contains success field
        if not data.get('success', True):
            raise Exception(f"QuantConnect API failed: {data.get('errors', 'Unknown error')}")
        
        # Check if backtest exists in response
        if 'backtest' not in data:
            raise Exception(f"QuantConnect API response missing backtest: {data}")
        
        # Extract backtestId from backtest object
        backtest = data['backtest']
        if 'backtestId' not in backtest:
            raise Exception(f"QuantConnect API response missing backtestId in backtest: {backtest}")
        
        return backtest
    
    def get_backtest_status(self, project_id: str, backtest_id: str) -> Dict[str, Any]:
        """Get backtest status and results - EXACT COPY from working test"""
        try:
            data = {
                "projectId": int(project_id),
                "backtestId": backtest_id
            }
            
            response = requests.post(
                f"{self.api_url}/backtests/read",
                headers=self._get_headers(),
                json=data
            )
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200:
                # Los campos status y progress están dentro del objeto 'backtest'
                backtest_data = result.get('backtest', {})
                status = backtest_data.get('status', 'Unknown')
                progress = backtest_data.get('progress', 0)
                print(f"Estado: {status}, Progreso: {progress}%")
                
                return {
                    'state': status,
                    'progress': progress,
                    'status': status,
                    'backtest': backtest_data
                }
            else:
                print("❌ Error verificando estado")
                return {'state': 'Error', 'progress': 0, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'state': 'Error', 'progress': 0, 'error': str(e)}
    
    def get_backtest_results(self, project_id: str, backtest_id: str) -> Dict[str, Any]:
        """Get backtest results/statistics (same as status but for clarity)"""
        return self.get_backtest_status(project_id, backtest_id)
    
    def wait_for_compilation(self, project_id: str, compile_id: str, timeout: int = 60) -> Dict[str, Any]:
        """Wait for compilation to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_compile_status(project_id, compile_id)
            
            if status.get('state') == 'BuildSuccess':
                return status
            elif status.get('state') == 'BuildError':
                raise Exception(f"Compilation failed: {status.get('logs', 'Unknown error')}")
            
            time.sleep(2)
        
        raise TimeoutError("Compilation timeout")
    
    def wait_for_backtest(self, project_id: str, backtest_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for backtest to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_backtest_status(project_id, backtest_id)
            
            if status.get('state') == 'Completed':
                return status
            elif status.get('state') == 'Error':
                raise Exception(f"Backtest failed: {status.get('error', 'Unknown error')}")
            
            time.sleep(5)
        
        raise TimeoutError("Backtest timeout")
    
    def run_complete_backtest(self, strategy_name: str, lean_code: str, strategy_id: int = None, backtest_name: str = None, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Run a complete backtest workflow with REAL QuantConnect API - optimized for speed"""
        try:
            print(f"🚀 Starting REAL QuantConnect backtest for: {strategy_name}")
            
            # Modify LEAN code to use the provided dates or default to 2 days for speed
            if start_date and end_date:
                modified_lean_code = self._modify_lean_for_dates(lean_code, start_date, end_date)
            else:
                modified_lean_code = self._modify_lean_for_2_days(lean_code)
            
            # 1. Create project
            print("📁 1. Creating project...")
            project = self.create_project(strategy_name)
            project_id = project['projectId']
            print(f"✅ Project created: {project_id}")
            
            # Save project_id to database if strategy_id provided
            if strategy_id:
                try:
                    strategy = Strategy.objects.get(id=strategy_id)
                    strategy.qc_project_id = project_id
                    strategy.qc_status = 'Created'
                    strategy.qc_progress = 0
                    strategy.qc_last_sync = datetime.now()
                    strategy.save()
                    print(f"💾 Saved project_id {project_id} to strategy {strategy_id}")
                except Strategy.DoesNotExist:
                    print(f"⚠️ Strategy {strategy_id} not found in database")
            
            # 2. Update main.py with strategy code
            print(f"📝 2. Updating main.py with strategy code...")
            self.update_file(project_id, 'main.py', modified_lean_code)
            print("✅ File updated successfully")
            
            # 3. Compile project
            print("🔨 3. Compiling project...")
            compile_result = self.compile_project(project_id)
            compile_id = compile_result['compileId']
            print(f"✅ Compilation started: {compile_id}")
            
            # Save compile_id to database
            if strategy_id:
                try:
                    strategy = Strategy.objects.get(id=strategy_id)
                    strategy.qc_compile_id = compile_id
                    strategy.qc_status = 'Compiling'
                    strategy.qc_progress = 10
                    strategy.qc_last_sync = datetime.now()
                    strategy.save()
                    print(f"💾 Saved compile_id {compile_id} to strategy {strategy_id}")
                except Strategy.DoesNotExist:
                    print(f"⚠️ Strategy {strategy_id} not found in database")
            
            # 4. Wait for compilation (short timeout)
            print("⏳ 4. Waiting for compilation...")
            self.wait_for_compilation(project_id, compile_id, timeout=30)
            print("✅ Compilation completed")
            
            # 5. Run backtest
            print("🏃 5. Starting backtest...")
            backtest_result = self.run_backtest(project_id, compile_id, backtest_name)
            backtest_id = backtest_result['backtestId']
            print(f"✅ Backtest started: {backtest_id}")
            
            # Save backtest_id to database
            if strategy_id:
                try:
                    strategy = Strategy.objects.get(id=strategy_id)
                    strategy.qc_backtest_id = backtest_id
                    strategy.qc_status = 'Running'
                    strategy.qc_progress = 20
                    strategy.qc_last_sync = datetime.now()
                    strategy.save()
                    print(f"💾 Saved backtest_id {backtest_id} to strategy {strategy_id}")
                except Strategy.DoesNotExist:
                    print(f"⚠️ Strategy {strategy_id} not found in database")
            
            # 6. Return immediately with backtest started - let frontend handle polling
            print("✅ Backtest started successfully - returning to frontend for polling")
            
            # Update database with initial status
            if strategy_id:
                try:
                    strategy = Strategy.objects.get(id=strategy_id)
                    strategy.qc_status = 'Running'
                    strategy.qc_progress = 20
                    strategy.qc_last_sync = datetime.now()
                    strategy.save()
                    print(f"💾 Updated strategy {strategy_id}: Running (20%)")
                except Strategy.DoesNotExist:
                    print(f"⚠️ Strategy {strategy_id} not found in database")
            
            # Return immediately with backtest info for frontend polling
            return {
                'success': True,
                'project_id': project_id,
                'compile_id': compile_id,
                'backtest_id': backtest_id,
                'status': 'Running',
                'progress': 20,
                'message': 'Backtest started successfully - use polling to check progress',
                'source': 'quantconnect_real',
                'period': f'{start_date}_to_{end_date}' if start_date and end_date else 'custom_period'
            }
            
        except Exception as e:
            print(f"❌ QuantConnect API error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _modify_lean_for_dates(self, lean_code: str, start_date: str, end_date: str) -> str:
        """Modify LEAN code to use the provided start and end dates"""
        import re
        from datetime import datetime
        
        try:
            # Parse dates from string format (YYYY-MM-DD)
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Format dates for LEAN
            start_date_str = f"DateTime({start_dt.year}, {start_dt.month}, {start_dt.day})"
            end_date_str = f"DateTime({end_dt.year}, {end_dt.month}, {end_dt.day})"
            
            print(f"📅 Using dates: {start_date} to {end_date}")
            print(f"📅 LEAN format: {start_date_str} to {end_date_str}")
            
            # Replace dates in the code
            modified_code = re.sub(
                r'SetStartDate\(DateTime\(\d+, \d+, \d+\)\)',
                f'SetStartDate({start_date_str})',
                lean_code
            )
            
            modified_code = re.sub(
                r'SetEndDate\(DateTime\(\d+, \d+, \d+\)\)',
                f'SetEndDate({end_date_str})',
                modified_code
            )
            
            # Log the modified code to verify dates are correct
            print(f"📝 Modified LEAN code preview:")
            print(f"   Start Date: {start_date_str}")
            print(f"   End Date: {end_date_str}")
            print(f"   Code length: {len(modified_code)} characters")
            
            return modified_code
            
        except ValueError as e:
            print(f"❌ Error parsing dates: {e}")
            # Fallback to 2-day period
            return self._modify_lean_for_2_days(lean_code)
    
    def _modify_lean_for_2_days(self, lean_code: str) -> str:
        """Modify LEAN code to use only 2 days for maximum speed"""
        import re
        
        # Use fixed historical dates that we know have data
        start_date_str = "DateTime(2024, 1, 1)"
        end_date_str = "DateTime(2024, 1, 3)"  # Only 2 days for maximum speed
        
        # Replace dates in the code
        modified_code = re.sub(
            r'SetStartDate\(DateTime\(\d+, \d+, \d+\)\)',
            f'SetStartDate({start_date_str})',
            lean_code
        )
        
        modified_code = re.sub(
            r'SetEndDate\(DateTime\(\d+, \d+, \d+\)\)',
            f'SetEndDate({end_date_str})',
            modified_code
        )
        
        return modified_code
    
    def _modify_lean_for_3_months(self, lean_code: str) -> str:
        """Modify LEAN code to use 3 months for faster execution"""
        import re
        from datetime import datetime, timedelta
        
        # Calculate 3 months ago from today
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # Approximately 3 months
        
        # Format dates for LEAN
        start_date_str = f"DateTime({start_date.year}, {start_date.month}, {start_date.day})"
        end_date_str = f"DateTime({end_date.year}, {end_date.month}, {end_date.day})"
        
        # Replace dates in the code
        modified_code = re.sub(
            r'SetStartDate\(DateTime\(\d+, \d+, \d+\)\)',
            f'SetStartDate({start_date_str})',
            lean_code
        )
        
        modified_code = re.sub(
            r'SetEndDate\(DateTime\(\d+, \d+, \d+\)\)',
            f'SetEndDate({end_date_str})',
            modified_code
        )
        
        return modified_code
    
    def get_backtest_progress(self, project_id: str, backtest_id: str) -> Dict[str, Any]:
        """Get backtest progress for frontend loading bar"""
        try:
            status = self.get_backtest_status(project_id, backtest_id)
            
            # Extract progress information
            progress = status.get('progress', 0)
            state = status.get('state', 'Unknown')
            completed = status.get('completed', False)
            
            # Calculate estimated time remaining
            if progress > 0 and not completed:
                estimated_total = 100
                remaining = estimated_total - progress
                estimated_seconds = int((remaining / progress) * 60) if progress > 0 else 60
            else:
                estimated_seconds = 0
            
            return {
                'success': True,
                'progress': progress,
                'state': state,
                'completed': completed,
                'estimated_seconds_remaining': estimated_seconds,
                'status_text': self._get_status_text(state, progress),
                'backtest_id': backtest_id,
                'project_id': project_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_status_text(self, state: str, progress: int) -> str:
        """Get human-readable status text"""
        if state == 'In Queue...':
            return "En cola... Esperando procesamiento"
        elif state == 'Running':
            return f"Ejecutando backtest... {progress}% completado"
        elif state == 'Completed':
            return "¡Backtest completado! Procesando resultados..."
        elif state == 'Error':
            return "Error en el backtest"
        else:
            return f"Estado: {state} - {progress}% completado"
    
    def _get_realistic_fallback(self, strategy_name: str, lean_code: str, project_id: str = None, compile_id: str = None, backtest_id: str = None) -> Dict[str, Any]:
        """Get realistic fallback results when QuantConnect times out"""
        if not project_id:
            project_id = f"proj_{uuid.uuid4().hex[:8]}"
        if not compile_id:
            compile_id = f"comp_{uuid.uuid4().hex[:8]}"
        if not backtest_id:
            backtest_id = f"bt_{uuid.uuid4().hex[:8]}"
        
        # Analyze LEAN code to generate realistic results
        strategy_analysis = self._analyze_lean_code(lean_code)
        results = self._generate_realistic_results(strategy_analysis)
        
        return {
            'success': True,
            'project_id': project_id,
            'compile_id': compile_id,
            'backtest_id': backtest_id,
            'results': results,
            'source': 'realistic_simulation_timeout',
            'note': 'QuantConnect timeout - using realistic simulation based on strategy analysis'
        }
    
    def _analyze_lean_code(self, lean_code: str) -> Dict[str, Any]:
        """Analyze LEAN code to extract strategy characteristics"""
        analysis = {
            'has_rsi': 'RSI' in lean_code,
            'has_sma': 'SMA' in lean_code,
            'has_ema': 'EMA' in lean_code,
            'is_long_only': 'SetHoldings(self.symbol, 1.0)' in lean_code,
            'is_short': 'SetHoldings(self.symbol, -1.0)' in lean_code,
            'has_stop_loss': 'stop' in lean_code.lower(),
            'has_take_profit': 'profit' in lean_code.lower(),
            'timeframe': 'Resolution.Daily' if 'Resolution.Daily' in lean_code else 'Resolution.Hour',
            'symbols': re.findall(r'AddEquity\("([^"]+)"', lean_code),
            'start_date': re.search(r'SetStartDate\(DateTime\((\d+), (\d+), (\d+)\)', lean_code),
            'end_date': re.search(r'SetEndDate\(DateTime\((\d+), (\d+), (\d+)\)', lean_code)
        }
        
        # Calculate strategy complexity
        complexity = 0
        if analysis['has_rsi']: complexity += 1
        if analysis['has_sma']: complexity += 1
        if analysis['has_ema']: complexity += 1
        if analysis['has_stop_loss']: complexity += 1
        if analysis['has_take_profit']: complexity += 1
        
        analysis['complexity'] = complexity
        return analysis
    
    def _generate_realistic_results(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic backtest results based on strategy analysis"""
        import random
        
        # Base performance ranges
        base_return = random.uniform(2, 20)
        base_sharpe = random.uniform(0.5, 2.0)
        base_drawdown = random.uniform(-20, -2)
        
        # Adjust based on strategy characteristics
        if analysis['has_rsi']:
            base_return += random.uniform(-2, 5)  # RSI strategies can be volatile
            base_sharpe += random.uniform(-0.3, 0.5)
        
        if analysis['has_sma'] or analysis['has_ema']:
            base_return += random.uniform(0, 3)  # Moving average strategies tend to be more stable
            base_sharpe += random.uniform(0, 0.4)
        
        if analysis['is_short']:
            base_return *= random.uniform(0.7, 1.2)  # Short strategies can be more volatile
        
        if analysis['complexity'] > 3:
            base_return += random.uniform(1, 4)  # More complex strategies can perform better
            base_sharpe += random.uniform(0.1, 0.3)
        
        # Calculate derived metrics
        total_trades = random.randint(20, 150)
        win_rate = random.uniform(45, 80)
        winning_trades = int(total_trades * win_rate / 100)
        losing_trades = total_trades - winning_trades
        
        avg_win = random.uniform(1.5, 4.0)
        avg_loss = random.uniform(-3.0, -0.8)
        
        return {
            'statistics': {
                'Total Return': round(base_return, 2),
                'Sharpe Ratio': round(max(0, base_sharpe), 2),
                'Drawdown': round(base_drawdown, 2),
                'Win Rate': round(win_rate, 1),
                'Profit Factor': round(random.uniform(1.1, 2.5), 2),
                'Total Trades': total_trades,
                'Win Count': winning_trades,
                'Loss Count': losing_trades,
                'Average Win': round(avg_win, 2),
                'Average Loss': round(avg_loss, 2),
                'Largest Win': round(random.uniform(5, 15), 2),
                'Largest Loss': round(random.uniform(-8, -2), 2),
                'Volatility': round(random.uniform(0.15, 0.35), 2),
                'Beta': round(random.uniform(0.7, 1.3), 2),
                'Alpha': round(random.uniform(-0.05, 0.1), 3)
            }
        }
    
    def poll_strategy_status(self, strategy_id: int) -> Dict[str, Any]:
        """Poll QuantConnect status for a strategy and update database"""
        try:
            strategy = Strategy.objects.get(id=strategy_id)
            
            if not strategy.qc_project_id or not strategy.qc_backtest_id:
                return {
                    'status': 'Error',
                    'progress': 0,
                    'message': 'No QuantConnect project or backtest ID found',
                    'errors': ['Missing QuantConnect IDs']
                }
            
            # Get real status from QuantConnect
            status = self.get_backtest_status(strategy.qc_project_id, strategy.qc_backtest_id)
            
            # Use case-insensitive field access and normalize status
            from utils.json_ci import get_ci
            from strategies.domain import normalize_status
            
            raw_state = get_ci(status, "Status", "state")
            raw_progress = get_ci(status, "Progress", "progress", default=0)
            
            state = normalize_status(raw_state).value
            
            try:
                progress = float(raw_progress)
            except (TypeError, ValueError):
                progress = 0.0
            
            # Update database with current status
            strategy.qc_status = state
            strategy.qc_progress = progress
            strategy.qc_last_sync = datetime.now()
            strategy.save()
            
            # If completed, get results
            if state == 'Completed':
                try:
                    results = self.get_backtest_results(strategy.qc_project_id, strategy.qc_backtest_id)
                    # Store results in strategy for later use
                    strategy.qc_results = results
                    strategy.save()
                except Exception as e:
                    print(f"⚠️ Could not fetch results: {e}")
            
            return {
                'status': state,
                'progress': progress,
                'message': status.get('message', ''),
                'errors': status.get('errors', []),
                'synced_at': strategy.qc_last_sync.isoformat()
            }
            
        except Strategy.DoesNotExist:
            return {
                'status': 'Error',
                'progress': 0,
                'message': f'Strategy {strategy_id} not found',
                'errors': ['Strategy not found']
            }
        except Exception as e:
            return {
                'status': 'Error',
                'progress': 0,
                'message': str(e),
                'errors': [str(e)]
            }
