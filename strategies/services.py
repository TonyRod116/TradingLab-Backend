import hashlib
import time
import requests
from django.conf import settings

class QuantConnectService:
    def __init__(self, user_id, api_token):
        self.user_id = user_id
        self.api_token = api_token
        self.base_url = "https://www.quantconnect.com/api/v2"
    
    def get_headers(self):
        """Generate authentication headers for QuantConnect API"""
        timestamp = str(int(time.time()))
        hash_string = f"{self.user_id}{self.api_token}{timestamp}"
        hash_signature = hashlib.sha256(hash_string.encode()).hexdigest()
        
        return {
            'Timestamp': timestamp,
            'Authorization': hash_signature,
            'Content-Type': 'application/json'
        }
    
    def test_authentication(self):
        """Test if the API credentials are valid"""
        try:
            response = requests.get(
                f"{self.base_url}/users/{self.user_id}/account",
                headers=self.get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_algorithms(self):
        """Fetch all algorithms for the user"""
        try:
            response = requests.get(
                f"{self.base_url}/users/{self.user_id}/algorithms",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API returned status {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Failed to fetch algorithms: {str(e)}")
    
    def get_algorithm_by_id(self, algorithm_id):
        """Fetch specific algorithm details"""
        try:
            response = requests.get(
                f"{self.base_url}/algorithms/{algorithm_id}",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API returned status {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Failed to fetch algorithm {algorithm_id}: {str(e)}")
