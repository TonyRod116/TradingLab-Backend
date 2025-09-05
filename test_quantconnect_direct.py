#!/usr/bin/env python3
"""
Script para hacer backtest completo en QuantConnect directamente desde Python
"""

import requests
import json
import time
import hashlib
import base64
from datetime import datetime

class QuantConnectDirectAPI:
    def __init__(self, user_id, access_token):
        self.user_id = user_id
        self.access_token = access_token
        self.base_url = "https://www.quantconnect.com/api/v2"
        
    def _get_headers(self):
        """Generar headers de autenticación para QuantConnect"""
        timestamp = str(int(time.time()))
        time_stamped_token = f'{self.access_token}:{timestamp}'
        hashed_token = hashlib.sha256(time_stamped_token.encode('utf-8')).hexdigest()
        auth_string = f'{self.user_id}:{hashed_token}'
        encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('ascii')
        
        return {
            'Authorization': f'Basic {encoded_auth}',
            'Timestamp': timestamp,
            'Content-Type': 'application/json'
        }
    
    def test_authentication(self):
        """Paso 0: Probar autenticación"""
        print("🔐 PASO 0: Probando autenticación...")
        try:
            response = requests.get(f"{self.base_url}/authenticate", headers=self._get_headers())
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200 and response.json().get('success'):
                print("✅ Autenticación exitosa!")
                return True
            else:
                print("❌ Error en autenticación")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def create_project(self):
        """Paso 1: Crear proyecto"""
        print("\n📁 PASO 1: Creando proyecto...")
        try:
            data = {
                "name": f"Test Strategy {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "language": "Py"
            }
            
            response = requests.post(
                f"{self.base_url}/projects/create",
                headers=self._get_headers(),
                json=data
            )
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200 and result.get('success'):
                # QuantConnect devuelve una lista de proyectos
                projects = result.get('projects', [])
                if projects:
                    project_id = projects[0].get('projectId')
                    print(f"✅ Proyecto creado exitosamente! Project ID: {project_id}")
                    return project_id
                else:
                    print("❌ No se encontró el proyecto en la respuesta")
                    return None
            else:
                print("❌ Error creando proyecto")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def create_file(self, project_id):
        """Paso 2: Crear archivo Python"""
        print(f"\n📝 PASO 2: Creando archivo en proyecto {project_id}...")
        try:
            python_code = '''from AlgorithmImports import *

class SimpleStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2024, 1, 1)
        self.SetEndDate(2024, 2, 1)
        self.SetCash(10000)
        self.AddEquity("SPY", Resolution.DAILY)
        
    def OnData(self, data):
        if not self.Portfolio.Invested:
            self.SetHoldings("SPY", 1)'''
            
            data = {
                "projectId": project_id,
                "name": f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
                "content": python_code
            }
            
            response = requests.post(
                f"{self.base_url}/files/create",
                headers=self._get_headers(),
                json=data
            )
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200 and result.get('success'):
                print("✅ Archivo creado exitosamente!")
                return True
            else:
                print("❌ Error creando archivo")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def compile_project(self, project_id):
        """Paso 3: Compilar proyecto"""
        print(f"\n🔨 PASO 3: Compilando proyecto {project_id}...")
        try:
            data = {
                "projectId": project_id
            }
            
            response = requests.post(
                f"{self.base_url}/compile/create",
                headers=self._get_headers(),
                json=data
            )
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200 and result.get('success'):
                compile_id = result.get('compileId')
                print(f"✅ Compilación iniciada! Compile ID: {compile_id}")
                return compile_id
            else:
                print("❌ Error en compilación")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def read_compilation(self, project_id, compile_id):
        """Paso 4: Leer resultado de compilación"""
        print(f"📖 Verificando compilación {compile_id}...")
        try:
            # CORRECCIÓN: POST con body JSON que incluye projectId y compileId
            data = {
                "projectId": project_id,
                "compileId": compile_id
            }
            
            response = requests.post(
                f"{self.base_url}/compile/read",
                headers=self._get_headers(),
                json=data
            )
            
            print(f"Status Code: {response.status_code}")
            
            # Manejar diferentes tipos de respuesta
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                    
                    # Verificar estado de compilación según la API de QuantConnect
                    state = result.get('state', 'Unknown')
                    if state == 'BuildSuccess':
                        print("✅ Compilación exitosa!")
                        return True
                    elif state == 'BuildError':
                        print("❌ Error en compilación")
                        if 'logs' in result:
                            print(f"Logs de error: {result['logs']}")
                        return False
                    elif state == 'InQueue':
                        print("⏳ Compilación en cola...")
                        return False
                    elif state == 'BuildInProgress':
                        print("⏳ Compilación en progreso...")
                        return False
                    else:
                        print(f"⏳ Estado desconocido: {state}")
                        return False
                except json.JSONDecodeError:
                    print("❌ Error: Respuesta no es JSON válido")
                    return False
            elif response.status_code == 500:
                print(f"❌ Error 500 en compilación. Response: {response.text}")
                return False
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_backtest(self, project_id, compile_id):
        """Paso 5: Ejecutar backtest"""
        print(f"\n🏃 PASO 5: Ejecutando backtest...")
        try:
            data = {
                "projectId": project_id,
                "compileId": compile_id,
                "backtestName": f"Test Backtest {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            response = requests.post(
                f"{self.base_url}/backtests/create",
                headers=self._get_headers(),
                json=data
            )
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200 and result.get('success'):
                # El backtestId está dentro del objeto 'backtest'
                backtest_data = result.get('backtest', {})
                backtest_id = backtest_data.get('backtestId')
                print(f"✅ Backtest iniciado! Backtest ID: {backtest_id}")
                return backtest_id
            else:
                print("❌ Error iniciando backtest")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def check_backtest_status(self, project_id, backtest_id):
        """Paso 6: Verificar estado del backtest"""
        print(f"\n📊 PASO 6: Verificando estado del backtest {backtest_id}...")
        try:
            data = {
                "projectId": project_id,
                "backtestId": backtest_id
            }
            
            response = requests.post(
                f"{self.base_url}/backtests/read",
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
                return status, progress
            else:
                print("❌ Error verificando estado")
                return None, 0
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None, 0
    
    def get_backtest_results(self, project_id, backtest_id):
        """Paso 7: Obtener resultados del backtest"""
        print(f"\n📈 PASO 7: Obteniendo resultados del backtest {backtest_id}...")
        try:
            data = {
                "projectId": project_id,
                "backtestId": backtest_id
            }
            
            response = requests.post(
                f"{self.base_url}/backtests/read/result",
                headers=self._get_headers(),
                json=data
            )
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200:
                print("✅ Resultados obtenidos exitosamente!")
                return result
            else:
                print("❌ Error obteniendo resultados")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

def main():
    """Función principal que ejecuta todo el flujo"""
    print("🚀 INICIANDO BACKTEST COMPLETO EN QUANTCONNECT")
    print("=" * 60)
    
    # Cargar credenciales desde Django settings
    import os
    import sys
    import django
    
    # Configurar Django
    sys.path.append('/home/tonirod/code/ga/projects/TradingLab-Backend-Clean')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    django.setup()
    
    from django.conf import settings
    
    USER_ID = getattr(settings, 'QUANTCONNECT_USER_ID', None)
    ACCESS_TOKEN = getattr(settings, 'QUANTCONNECT_ACCESS_TOKEN', None)
    
    if not USER_ID or not ACCESS_TOKEN:
        print("❌ ERROR: No se encontraron las credenciales de QuantConnect")
        print("Asegúrate de tener configurado QUANTCONNECT_USER_ID y QUANTCONNECT_ACCESS_TOKEN en tu .env")
        return
    
    print(f"✅ Credenciales encontradas: User ID = {USER_ID[:8]}...")
    
    # Crear instancia de la API
    qc_api = QuantConnectDirectAPI(USER_ID, ACCESS_TOKEN)
    
    # Ejecutar flujo completo
    try:
        # Paso 0: Probar autenticación
        if not qc_api.test_authentication():
            print("❌ No se pudo autenticar. Verifica tus credenciales.")
            return
        
        # Paso 1: Crear proyecto
        project_id = qc_api.create_project()
        if not project_id:
            print("❌ No se pudo crear el proyecto. Abortando.")
            return
        
        # Paso 2: Crear archivo
        if not qc_api.create_file(project_id):
            print("❌ No se pudo crear el archivo. Abortando.")
            return
        
        # Paso 3: Compilar proyecto
        compile_id = qc_api.compile_project(project_id)
        if not compile_id:
            print("❌ No se pudo compilar el proyecto. Abortando.")
            return
        
        # Esperar y verificar compilación hasta que esté lista
        print("⏳ Esperando que la compilación esté lista...")
        print("⏳ Esperando 15 segundos iniciales...")
        time.sleep(15)  # Espera inicial más larga
        
        max_compile_attempts = 30  # Máximo 5 minutos
        compile_attempt = 0
        
        while compile_attempt < max_compile_attempts:
            print(f"⏳ Intento {compile_attempt + 1}/{max_compile_attempts} - Verificando compilación...")
            
            # Paso 4: Leer compilación
            compile_success = qc_api.read_compilation(project_id, compile_id)
            if compile_success:
                print("✅ Compilación completada exitosamente!")
                break
            else:
                print("⏳ Compilación aún en progreso, esperando 10 segundos...")
                time.sleep(10)
                compile_attempt += 1
        
        if compile_attempt >= max_compile_attempts:
            print("⏰ Timeout: La compilación tardó demasiado")
            return
        
        # Paso 5: Ejecutar backtest
        backtest_id = qc_api.run_backtest(project_id, compile_id)
        if not backtest_id:
            print("❌ No se pudo iniciar el backtest. Abortando.")
            return
        
        # Paso 6: Monitorear estado del backtest
        print("\n⏳ Monitoreando estado del backtest...")
        max_attempts = 60  # Máximo 10 minutos
        attempt = 0
        
        while attempt < max_attempts:
            status, progress = qc_api.check_backtest_status(project_id, backtest_id)
            
            if status in ["Completed", "Completed."]:
                print("✅ Backtest completado!")
                break
            elif status in ["Failed", "Error", "BuildError"]:
                print("❌ Backtest falló!")
                return
            elif status in ["In Queue...", "Running", "In Progress"]:
                print(f"⏳ Estado: {status}, Progreso: {progress}% - Esperando...")
                time.sleep(10)  # Esperar 10 segundos
                attempt += 1
            else:
                print(f"⏳ Estado desconocido: {status}, Progreso: {progress}% - Esperando...")
                time.sleep(10)  # Esperar 10 segundos
                attempt += 1
        
        if attempt >= max_attempts:
            print("⏰ Timeout: El backtest tardó demasiado")
            return
        
        # Paso 7: Obtener resultados
        results = qc_api.get_backtest_results(project_id, backtest_id)
        if results:
            print("\n🎉 ¡BACKTEST COMPLETADO EXITOSAMENTE!")
            print("=" * 60)
            print("Resultados principales:")
            if 'statistics' in results:
                stats = results['statistics']
                print(f"Total Return: {stats.get('Total Return', 'N/A')}")
                print(f"Sharpe Ratio: {stats.get('Sharpe Ratio', 'N/A')}")
                print(f"Max Drawdown: {stats.get('Max Drawdown', 'N/A')}")
                print(f"Win Rate: {stats.get('Win Rate', 'N/A')}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()
