# test_hosting_accounts.py
import pytest
import uuid
from unittest.mock import Mock
from app.core.shared.exceptions import HostingError


class TestHostingAccountManager:
    """Test cases for HostingAccountManager"""
    
    def test_get_account_by_domain_success(self, hosting_account_manager, mock_repository_factory):
        """Test successful account retrieval by domain"""
        # Arrange
        domain = "example.com"
        expected_account = Mock()
        mock_repository_factory.hosting_accounts.get_by_domain.return_value = expected_account
        
        # Act
        result = hosting_account_manager.get_account_by_domain(domain)
        
        # Assert
        assert result == expected_account
        mock_repository_factory.hosting_accounts.get_by_domain.assert_called_once_with(domain)
    
    def test_get_account_by_domain_not_found(self, hosting_account_manager, mock_repository_factory):
        """Test account retrieval when domain not found"""
        # Arrange
        domain = "nonexistent.com"
        mock_repository_factory.hosting_accounts.get_by_domain.return_value = None
        
        # Act
        result = hosting_account_manager.get_account_by_domain(domain)
        
        # Assert
        assert result is None
    
    def test_get_account_by_domain_error(self, hosting_account_manager, mock_repository_factory):
        """Test error handling in account retrieval"""
        # Arrange
        domain = "example.com"
        mock_repository_factory.hosting_accounts.get_by_domain.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(HostingError) as exc_info:
            hosting_account_manager.get_account_by_domain(domain)
        
        assert "Failed to get hosting account" in str(exc_info.value)
    
    def test_get_customer_accounts_success(self, hosting_account_manager, mock_repository_factory):
        """Test successful retrieval of customer accounts"""
        # Arrange
        customer_id = uuid.uuid4()
        expected_accounts = [Mock(), Mock()]
        mock_repository_factory.hosting_accounts.get_customer_accounts.return_value = expected_accounts
        
        # Act
        result = hosting_account_manager.get_customer_accounts(customer_id)
        
        # Assert
        assert result == expected_accounts
        mock_repository_factory.hosting_accounts.get_customer_accounts.assert_called_once_with(customer_id)
    
    def test_get_customer_accounts_error(self, hosting_account_manager, mock_repository_factory):
        """Test error handling in customer accounts retrieval"""
        # Arrange
        customer_id = uuid.uuid4()
        mock_repository_factory.hosting_accounts.get_customer_accounts.side_effect = Exception("DB error")
        
        # Act & Assert
        with pytest.raises(HostingError) as exc_info:
            hosting_account_manager.get_customer_accounts(customer_id)
        
        assert "Failed to get customer accounts" in str(exc_info.value)
    
    def test_update_account_usage_success(self, hosting_account_manager, mock_repository_factory):
        """Test successful account usage update"""
        # Arrange
        account_id = uuid.uuid4()
        disk_usage = 1024
        bandwidth_usage = 5120
        mock_repository_factory.hosting_accounts.update_usage.return_value = True
        
        # Act
        result = hosting_account_manager.update_account_usage(account_id, disk_usage, bandwidth_usage)
        
        # Assert
        assert result is True
        mock_repository_factory.hosting_accounts.update_usage.assert_called_once_with(
            account_id, disk_usage, bandwidth_usage
        )
    
    def test_update_account_usage_error(self, hosting_account_manager, mock_repository_factory):
        """Test error handling in account usage update"""
        # Arrange
        account_id = uuid.uuid4()
        disk_usage = 1024
        bandwidth_usage = 5120
        mock_repository_factory.hosting_accounts.update_usage.side_effect = Exception("Update failed")
        
        # Act & Assert
        with pytest.raises(HostingError) as exc_info:
            hosting_account_manager.update_account_usage(account_id, disk_usage, bandwidth_usage)
        
        assert "Failed to update account usage" in str(exc_info.value)