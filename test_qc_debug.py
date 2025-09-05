#!/usr/bin/env python3
"""
Script completo para diagnosticar el problema "Status: Unknown" con QuantConnect
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_quantconnect_flow():
    """Prueba completa del flujo de QuantConnect con fix robusto"""
    
    print("🔍 DIAGNÓSTICO COMPLETO DE QUANTCONNECT (CON FIX ROBUSTO)")
    print("=" * 60)
    
    # 1. Estrategia de prueba simple
    strategy_data = {
        "strategy": {
            "id": 1,
            "name": "Test Strategy Debug",
            "lean_code": """from AlgorithmImports import *

class TestStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetEndDate(2023, 1, 3)  # Solo 2 días para velocidad
        self.SetCash(100000)
        self.AddEquity("SPY", Resolution.Daily)
    
    def OnData(self, data):
        if not self.Portfolio.Invested:
            self.SetHoldings("SPY", 1.0)"""
        },
        "backtest_params": {
            "start_date": "2023-01-01",
            "end_date": "2023-01-03",
            "initial_capital": 100000
        }
    }
    
    print("\n1️⃣ EJECUTANDO BACKTEST EN QUANTCONNECT")
    print("-" * 40)
    
    try:
        # POST /api/strategies/quantconnect-backtest/
        response = requests.post(
            f"{BASE_URL}/api/strategies/quantconnect-backtest/",
            json=strategy_data,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Extraer IDs para logging
            qc_data = result.get('quantconnect', {})
            project_id = qc_data.get('project_id')
            compile_id = qc_data.get('compile_id')
            backtest_id = qc_data.get('backtest_id')
            
            print(f"\n📊 IDs GENERADOS:")
            print(f"Project ID: {project_id}")
            print(f"Compile ID: {compile_id}")
            print(f"Backtest ID: {backtest_id}")
            
            # Log en formato JSON como pidió GPT
            log_data = {
                "strategyId": 1,
                "projectId": project_id,
                "compileId": compile_id,
                "backtestId": backtest_id,
                "qc_request_id": f"req_{int(time.time())}",
                "ts": datetime.now().isoformat() + "Z"
            }
            print(f"\n📝 LOG JSON (como pidió GPT):")
            print(json.dumps(log_data, indent=2))
            
            # 2. Probar polling del status
            if backtest_id:
                print(f"\n2️⃣ PROBANDO POLLING DEL STATUS")
                print("-" * 40)
                
                for i in range(5):  # 5 intentos de polling
                    print(f"\nPoll #{i+1}:")
                    
                    # GET /api/strategies/1/qc-status/
                    try:
                        status_response = requests.get(
                            f"{BASE_URL}/api/strategies/1/qc-status/",
                            timeout=10
                        )
                        
                        print(f"Status Code: {status_response.status_code}")
                        print(f"Headers: {dict(status_response.headers)}")
                        print(f"Content-Length: {status_response.headers.get('Content-Length', 'N/A')}")
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            print(f"Response: {json.dumps(status_data, indent=2)}")
                            
                            # Log de polling como pidió GPT
                            poll_log = {
                                "strategyId": 1,
                                "backtestId": backtest_id,
                                "qc_status": status_data.get('status', 'Unknown'),
                                "qc_progress": status_data.get('progress', 0),
                                "ts": datetime.now().isoformat() + "Z"
                            }
                            print(f"📝 POLL LOG JSON:")
                            print(json.dumps(poll_log, indent=2))
                            
                        else:
                            print(f"Error: {status_response.text}")
                            
                    except Exception as e:
                        print(f"Error en polling: {e}")
                    
                    time.sleep(2)  # Esperar 2 segundos entre polls
                    
            else:
                print("❌ No se obtuvo backtest_id - aquí está el bug!")
                
        else:
            print(f"Error en backtest: {response.text}")
            
    except Exception as e:
        print(f"Error general: {e}")

def test_direct_qc_api():
    """Prueba directa a la API de QuantConnect (si tenemos credenciales)"""
    print(f"\n3️⃣ PRUEBA DIRECTA A QUANTCONNECT API")
    print("-" * 40)
    print("⚠️  Nota: Necesitaríamos credenciales reales de QuantConnect")
    print("Para probar: curl -i 'https://www.quantconnect.com/api/v2/backtests/{projectId}/{backtestId}'")
    print("Con header: Authorization: Bearer {token}")

if __name__ == "__main__":
    test_quantconnect_flow()
    test_direct_qc_api()
