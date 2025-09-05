"""
Integration tests for QuantConnect endpoints
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from strategies.models import Strategy


class TestQuantConnectStatusEndpoint(TestCase):
    """Test QuantConnect status endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.strategy = Strategy.objects.create(
            user=self.user,
            name='Test Strategy',
            description='Test strategy for QC testing',
            lean_code='print("test")'
        )
    
    def test_status_missing_ids(self):
        """Test status endpoint with missing QuantConnect IDs"""
        # Login user
        self.client.force_login(self.user)
        
        # Make request
        response = self.client.get(f'/api/strategies/{self.strategy.id}/qc-status/')
        
        # Should return 422 with missing IDs error
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data['status'], 'Unknown')
        self.assertEqual(data['errors'], ['MISSING_IDS'])
        self.assertIn('Missing QuantConnect IDs', data['message'])
    
    def test_status_with_qc_ids(self):
        """Test status endpoint with QuantConnect IDs"""
        # Set up QuantConnect IDs
        self.strategy.qc_project_id = 'test_project_123'
        self.strategy.qc_backtest_id = 'test_backtest_456'
        self.strategy.save()
        
        # Mock QuantConnect service response
        mock_qc_response = {
            'Status': 'Running',
            'Progress': 45.5,
            'Message': 'Backtest in progress'
        }
        
        with patch('strategies.services.quantconnect_service.QuantConnectService.get_backtest_status') as mock_get_status:
            mock_get_status.return_value = mock_qc_response
            
            # Login user
            self.client.force_login(self.user)
            
            # Make request
            response = self.client.get(f'/api/strategies/{self.strategy.id}/qc-status/')
            
            # Should return 200 with correct status
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['status'], 'Running')
            self.assertEqual(data['progress'], 45.5)
            self.assertEqual(data['message'], 'Backtest in progress')
            
            # Check cache headers
            self.assertEqual(response['Cache-Control'], 'no-store, no-cache, must-revalidate')
            self.assertEqual(response['Pragma'], 'no-cache')
    
    def test_status_qc_unreachable(self):
        """Test status endpoint when QuantConnect is unreachable"""
        # Set up QuantConnect IDs
        self.strategy.qc_project_id = 'test_project_123'
        self.strategy.qc_backtest_id = 'test_backtest_456'
        self.strategy.save()
        
        # Mock QuantConnect service to raise exception
        with patch('strategies.services.quantconnect_service.QuantConnectService.get_backtest_status') as mock_get_status:
            mock_get_status.side_effect = Exception('Connection timeout')
            
            # Login user
            self.client.force_login(self.user)
            
            # Make request
            response = self.client.get(f'/api/strategies/{self.strategy.id}/qc-status/')
            
            # Should return 424 Failed Dependency
            self.assertEqual(response.status_code, 424)
            data = response.json()
            self.assertEqual(data['status'], 'Unknown')
            self.assertEqual(data['errors'], ['QC_UNREACHABLE'])
            self.assertIn('QuantConnect unreachable', data['message'])
    
    def test_status_case_insensitive_mapping(self):
        """Test that status mapping handles case variations"""
        # Set up QuantConnect IDs
        self.strategy.qc_project_id = 'test_project_123'
        self.strategy.qc_backtest_id = 'test_backtest_456'
        self.strategy.save()
        
        # Mock QuantConnect service response with lowercase fields
        mock_qc_response = {
            'status': 'completed',  # lowercase
            'progress': 100.0,      # lowercase
            'message': 'Backtest finished'
        }
        
        with patch('strategies.services.quantconnect_service.QuantConnectService.get_backtest_status') as mock_get_status:
            mock_get_status.return_value = mock_qc_response
            
            # Login user
            self.client.force_login(self.user)
            
            # Make request
            response = self.client.get(f'/api/strategies/{self.strategy.id}/qc-status/')
            
            # Should return 200 with normalized status
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['status'], 'Completed')  # Should be normalized
            self.assertEqual(data['progress'], 100.0)
    
    def test_status_unauthorized(self):
        """Test status endpoint without authentication"""
        response = self.client.get(f'/api/strategies/{self.strategy.id}/qc-status/')
        self.assertEqual(response.status_code, 401)
    
    def test_status_strategy_not_found(self):
        """Test status endpoint with non-existent strategy"""
        self.client.force_login(self.user)
        response = self.client.get('/api/strategies/99999/qc-status/')
        self.assertEqual(response.status_code, 404)
