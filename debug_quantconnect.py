#!/usr/bin/env python3
"""
Script de diagnóstico para QuantConnect API
"""

import requests
import json
import time
import hashlib
import base64
import os
import sys
import django

# Configurar Django
sys.path.append('/home/tonirod/code/ga/projects/TradingLab-Backend-Clean')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.conf import settings

class QuantConnectDebug:
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
    
    def test_compile_read_direct(self, compile_id):
        """Probar endpoint de compilación directamente"""
        print(f"🔍 Probando endpoint de compilación directamente...")
        print(f"Compile ID: {compile_id}")
        
        # Probar diferentes endpoints
        endpoints = [
            f"/compile/read",
            f"/compile/read/{compile_id}",
            f"/projects/compile/read",
            f"/projects/compile/read/{compile_id}"
        ]
        
        for endpoint in endpoints:
            print(f"\n📡 Probando: {endpoint}")
            try:
                if endpoint.endswith(compile_id):
                    # GET request
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=self._get_headers()
                    )
                else:
                    # POST request
                    data = {"compileId": compile_id}
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        headers=self._get_headers(),
                        json=data
                    )
                
                print(f"Status Code: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
                print(f"Response Text: '{response.text}'")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"JSON Response: {json.dumps(result, indent=2)}")
                    except:
                        print("No es JSON válido")
                        
            except Exception as e:
                print(f"Error: {e}")
    
    def test_compile_status(self, compile_id):
        """Probar endpoint de estado de compilación"""
        print(f"\n🔍 Probando endpoint de estado de compilación...")
        
        try:
            # Probar endpoint de estado
            response = requests.get(
                f"{self.base_url}/compile/status/{compile_id}",
                headers=self._get_headers()
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
        except Exception as e:
            print(f"Error: {e}")

def main():
    print("🔍 DIAGNÓSTICO DE QUANTCONNECT API")
    print("=" * 50)
    
    USER_ID = getattr(settings, 'QUANTCONNECT_USER_ID', None)
    ACCESS_TOKEN = getattr(settings, 'QUANTCONNECT_ACCESS_TOKEN', None)
    
    if not USER_ID or not ACCESS_TOKEN:
        print("❌ No se encontraron las credenciales")
        return
    
    debug = QuantConnectDebug(USER_ID, ACCESS_TOKEN)
    
    # Usar el último compile_id que vimos
    compile_id = "655094c927494786cffadf7d7e9a2fac-bcd7bf2705175b2db4879e898d8d83a5"
    
    debug.test_compile_read_direct(compile_id)
    debug.test_compile_status(compile_id)

if __name__ == "__main__":
    main()
