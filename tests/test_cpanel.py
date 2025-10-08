# test_cpanel.py
import pytest
import requests
from unittest.mock import Mock, patch
from app.core.shared.exceptions import HostingError


class TestCPanelManager:
    """Test cases for CPanelManager"""
    
    def test_init(self):
        """Test CPanelManager initialization"""
        # Act
        from app.core.hosting.cpanel import CPanelManager
        manager = CPanelManager(
            whm_host="whm.example.com",
            whm_username="root", 
            whm_token="test_token"
        )
        
        # Assert
        assert manager.whm_host == "whm.example.com"
        assert manager.whm_username == "root"
        assert manager.whm_token == "test_token"
        assert manager.base_url == "https://whm.example.com:2087/json-api"
    
    @patch('app.core.hosting.cpanel.requests.post')
    def test_make_request_success(self, mock_post, cpanel_manager, mock_cpanel_success_response):
        """Test successful API request"""
        # Arrange
        mock_post.return_value = Mock(status_code=200, json=lambda: mock_cpanel_success_response)
        
        # Act
        result = cpanel_manager._make_request("test_endpoint", {"param": "value"})
        
        # Assert
        assert result == mock_cpanel_success_response
        mock_post.assert_called_once()
    
    @patch('app.core.hosting.cpanel.requests.post')
    def test_make_request_failure(self, mock_post, cpanel_manager):
        """Test API request failure"""
        # Arrange
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        # Act & Assert
        with pytest.raises(HostingError) as exc_info:
            cpanel_manager._make_request("test_endpoint")
        
        assert "WHM API request failed" in str(exc_info.value)
    
    def test_create_cpanel_account_success(self, cpanel_manager, mock_cpanel_create_response):
        """Test successful cPanel account creation"""
        # Arrange
        cpanel_manager._make_request = Mock(return_value=mock_cpanel_create_response)
        
        # Act
        result = cpanel_manager.create_cpanel_account(
            domain="example.com",
            username="testuser", 
            password="securepassword",
            plan="starter",
            email="test@example.com"
        )
        
        # Assert
        assert result['success'] is True
        assert result['username'] == "testuser"
        assert result['domain'] == "example.com"
        assert result['ip_address'] == "192.168.1.100"
        cpanel_manager._make_request.assert_called_once_with('createacct', {
            'api.version': 1,
            'domain': 'example.com',
            'user': 'testuser',
            'password': 'securepassword', 
            'plan': 'starter',
            'contactemail': 'test@example.com'
        })
    
    def test_create_cpanel_account_failure(self, cpanel_manager):
        """Test cPanel account creation failure"""
        # Arrange
        mock_response = {
            "metadata": {"result": 0, "reason": "Account already exists"}
        }
        cpanel_manager._make_request = Mock(return_value=mock_response)
        
        # Act & Assert
        with pytest.raises(HostingError) as exc_info:
            cpanel_manager.create_cpanel_account(
                domain="example.com",
                username="testuser",
                password="securepassword", 
                plan="starter",
                email="test@example.com"
            )
        
        assert "Failed to create cPanel account" in str(exc_info.value)
    
    def test_suspend_account_success(self, cpanel_manager, mock_cpanel_success_response):
        """Test successful account suspension"""
        # Arrange
        cpanel_manager._make_request = Mock(return_value=mock_cpanel_success_response)
        
        # Act
        result = cpanel_manager.suspend_account("testuser", "Non-payment")
        
        # Assert
        assert result is True
        cpanel_manager._make_request.assert_called_once_with('suspendacct', {
            'api.version': 1,
            'user': 'testuser',
            'reason': 'Non-payment'
        })
    
    def test_unsuspend_account_success(self, cpanel_manager, mock_cpanel_success_response):
        """Test successful account unsuspension"""
        # Arrange
        cpanel_manager._make_request = Mock(return_value=mock_cpanel_success_response)
        
        # Act
        result = cpanel_manager.unsuspend_account("testuser")
        
        # Assert
        assert result is True
        cpanel_manager._make_request.assert_called_once_with('unsuspendacct', {
            'api.version': 1, 
            'user': 'testuser'
        })
    
    def test_change_plan_success(self, cpanel_manager, mock_cpanel_success_response):
        """Test successful plan change"""
        # Arrange
        cpanel_manager._make_request = Mock(return_value=mock_cpanel_success_response)
        
        # Act
        result = cpanel_manager.change_plan("testuser", "business")
        
        # Assert
        assert result is True
        cpanel_manager._make_request.assert_called_once_with('changepackage', {
            'api.version': 1,
            'user': 'testuser',
            'pkg': 'business'
        })
    
    def test_get_account_usage_success(self, cpanel_manager, mock_cpanel_usage_response):
        """Test successful account usage retrieval"""
        # Arrange
        cpanel_manager._make_request = Mock(return_value=mock_cpanel_usage_response)
        
        # Act
        result = cpanel_manager.get_account_usage("testuser")
        
        # Assert
        assert result['disk_usage'] == 1048576
        assert result['disk_limit'] == 10485760
        cpanel_manager._make_request.assert_called_once_with('get_disk_usage', {
            'api.version': 1,
            'user': 'testuser'
        })
    
    def test_create_email_account_success(self, cpanel_manager, mock_cpanel_success_response):
        """Test successful email account creation"""
        # Arrange
        cpanel_manager._make_request = Mock(return_value=mock_cpanel_success_response)
        
        # Act
        result = cpanel_manager.create_email_account(
            domain="example.com",
            email="user@example.com",
            password="emailpass", 
            quota=500
        )
        
        # Assert
        assert result is True
        cpanel_manager._make_request.assert_called_once_with('create_email_account', {
            'api.version': 1,
            'domain': 'example.com',
            'email': 'user@example.com',
            'password': 'emailpass',
            'quota': 500
        })
    
    def test_delete_account_success(self, cpanel_manager, mock_cpanel_success_response):
        """Test successful account deletion"""
        # Arrange
        cpanel_manager._make_request = Mock(return_value=mock_cpanel_success_response)
        
        # Act
        result = cpanel_manager.delete_account("testuser")
        
        # Assert
        assert result is True
        cpanel_manager._make_request.assert_called_once_with('removeacct', {
            'api.version': 1,
            'user': 'testuser'
        })