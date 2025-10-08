# test_hosting_manager.py
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.core.hosting.manager import HostingManager
from app.core.shared.exceptions import HostingError, ValidationError


class TestHostingManager:
    """Test cases for HostingManager"""
    
    def test_validate_hosting_input_valid(self, hosting_manager):
        """Test valid hosting input validation"""
        # This should not raise any exception
        hosting_manager._validate_hosting_input(
            domain="example.com",
            username="testuser",
            password="securepassword123"
        )
    
    def test_validate_hosting_input_invalid_domain(self, hosting_manager):
        """Test invalid domain validation"""
        with pytest.raises(ValidationError) as exc_info:
            hosting_manager._validate_hosting_input(
                domain="invalid",
                username="testuser",
                password="securepassword123"
            )
        assert "Invalid domain name" in str(exc_info.value)
    
    def test_validate_hosting_input_short_username(self, hosting_manager):
        """Test short username validation"""
        with pytest.raises(ValidationError) as exc_info:
            hosting_manager._validate_hosting_input(
                domain="example.com",
                username="ab",
                password="securepassword123"
            )
        assert "Username must be at least 3 characters" in str(exc_info.value)
    
    def test_validate_hosting_input_short_password(self, hosting_manager):
        """Test short password validation"""
        with pytest.raises(ValidationError) as exc_info:
            hosting_manager._validate_hosting_input(
                domain="example.com",
                username="testuser",
                password="short"
            )
        assert "Password must be at least 8 characters" in str(exc_info.value)
    
    def test_validate_hosting_input_invalid_username_chars(self, hosting_manager):
        """Test invalid username characters validation"""
        with pytest.raises(ValidationError) as exc_info:
            hosting_manager._validate_hosting_input(
                domain="example.com",
                username="test-user",
                password="securepassword123"
            )
        assert "Username can only contain lowercase letters, numbers, and underscores" in str(exc_info.value)
    
    def test_create_hosting_account_success(self, hosting_manager_with_api, mock_get_db, mock_get_repository_factory, 
                                         sample_customer, sample_hosting_package):
        """Test successful hosting account creation"""
        # Arrange
        mock_repository_factory = mock_get_repository_factory.return_value
        
        # Mock repositories
        mock_repository_factory.hosting_packages.get.return_value = sample_hosting_package
        mock_repository_factory.customers.get.return_value = sample_customer
        mock_repository_factory.hosting_accounts.get_by_domain.return_value = None
        
        # Mock API response
        hosting_manager_with_api.api_client.create_account.return_value = {
            'ip_address': '192.168.1.100'
        }
        
        # Mock account creation
        mock_account = Mock()
        mock_repository_factory.hosting_accounts.create.return_value = mock_account
        
        # Act
        result = hosting_manager_with_api.create_hosting_account(
            domain="example.com",
            package_id=sample_hosting_package.id,
            customer_id=sample_customer.id,
            username="testuser",
            password="securepassword123"
        )
        
        # Assert
        assert result == mock_account
        mock_repository_factory.hosting_packages.get.assert_called_once_with(sample_hosting_package.id)
        mock_repository_factory.customers.get.assert_called_once_with(sample_customer.id)
        mock_repository_factory.hosting_accounts.get_by_domain.assert_called_once_with("example.com")
        hosting_manager_with_api.api_client.create_account.assert_called_once()
        mock_repository_factory.hosting_accounts.create.assert_called_once()
    
    def test_create_hosting_account_existing_domain(self, hosting_manager, mock_get_db, mock_get_repository_factory,
                                                  sample_customer, sample_hosting_package):
        """Test hosting account creation with existing domain"""
        # Arrange
        mock_repository_factory = mock_get_repository_factory.return_value
        
        mock_repository_factory.hosting_packages.get.return_value = sample_hosting_package
        mock_repository_factory.customers.get.return_value = sample_customer
        
        # Mock existing account
        mock_existing_account = Mock()
        mock_repository_factory.hosting_accounts.get_by_domain.return_value = mock_existing_account
        
        # Act & Assert
        with pytest.raises(HostingError) as exc_info:  # Changed from ValidationError to HostingError
            hosting_manager.create_hosting_account(
                domain="example.com",
                package_id=sample_hosting_package.id,
                customer_id=sample_customer.id,
                username="testuser",
                password="securepassword123"
            )
        
        assert "Failed to create hosting account" in str(exc_info.value)
    
    def test_suspend_account_success(self, hosting_manager_with_api, mock_get_db, mock_get_repository_factory,
                                   sample_hosting_account):
        """Test successful account suspension"""
        # Arrange
        mock_repository_factory = mock_get_repository_factory.return_value
        mock_repository_factory.hosting_accounts.get.return_value = sample_hosting_account
        mock_repository_factory.hosting_accounts.update.return_value = True
        
        # Act
        result = hosting_manager_with_api.suspend_account(
            account_id=sample_hosting_account.id,
            reason="Non-payment"
        )
        
        # Assert
        assert result is True
        hosting_manager_with_api.api_client.suspend_account.assert_called_once_with(
            sample_hosting_account.username, "Non-payment"
        )
        mock_repository_factory.hosting_accounts.update.assert_called_once()
    
    def test_unsuspend_account_success(self, hosting_manager_with_api, mock_get_db, mock_get_repository_factory,
                                     sample_hosting_account):
        """Test successful account unsuspension"""
        # Arrange
        mock_repository_factory = mock_get_repository_factory.return_value
        mock_repository_factory.hosting_accounts.get.return_value = sample_hosting_account
        mock_repository_factory.hosting_accounts.update.return_value = True
        
        # Act
        result = hosting_manager_with_api.unsuspend_account(sample_hosting_account.id)
        
        # Assert
        assert result is True
        hosting_manager_with_api.api_client.unsuspend_account.assert_called_once_with(
            sample_hosting_account.username
        )
        mock_repository_factory.hosting_accounts.update.assert_called_once()
    
    def test_change_hosting_plan_success(self, hosting_manager_with_api, mock_get_db, mock_get_repository_factory,
                                       sample_hosting_account, sample_hosting_package):
        """Test successful hosting plan change"""
        # Arrange
        mock_repository_factory = mock_get_repository_factory.return_value
        mock_repository_factory.hosting_accounts.get.return_value = sample_hosting_account
        
        new_package = Mock()
        new_package.id = uuid.uuid4()
        new_package.name = "business"
        new_package.active = True
        mock_repository_factory.hosting_packages.get.return_value = new_package
        
        mock_repository_factory.hosting_accounts.update.return_value = True
        
        # Act
        result = hosting_manager_with_api.change_hosting_plan(
            account_id=sample_hosting_account.id,
            new_package_id=new_package.id
        )
        
        # Assert
        assert result is True
        hosting_manager_with_api.api_client.change_plan.assert_called_once_with(
            sample_hosting_account.username, new_package.name
        )
        mock_repository_factory.hosting_accounts.update.assert_called_once_with(
            sample_hosting_account.id, {'package_id': new_package.id}
        )
    
    def test_get_account_usage_with_api(self, hosting_manager_with_api, mock_get_db, mock_get_repository_factory,
                                      sample_hosting_account):
        """Test account usage retrieval with API client"""
        # Arrange
        mock_repository_factory = mock_get_repository_factory.return_value
        
        sample_hosting_account.package = Mock(disk_space=2048, bandwidth=20480)
        mock_repository_factory.hosting_accounts.get.return_value = sample_hosting_account
        
        # Mock API usage data
        usage_data = {
            'disk_usage': 1024,
            'bandwidth_usage': 5120,
            'disk_limit': 2048,
            'bandwidth_limit': 20480
        }
        hosting_manager_with_api.api_client.get_account_usage.return_value = usage_data
        
        mock_repository_factory.hosting_accounts.update.return_value = True
        
        # Act
        result = hosting_manager_with_api.get_account_usage(sample_hosting_account.id)
        
        # Assert
        assert result['disk_usage'] == 1024
        assert result['bandwidth_usage'] == 5120
        assert result['disk_usage_percent'] == 50.0
        assert result['bandwidth_usage_percent'] == 25.0
        hosting_manager_with_api.api_client.get_account_usage.assert_called_once_with(
            sample_hosting_account.username
        )
    
    def test_renew_hosting_account_success(self, hosting_manager, mock_get_db, mock_get_repository_factory,
                                        sample_hosting_account):
        """Test successful hosting account renewal"""
        # Arrange
        mock_repository_factory = mock_get_repository_factory.return_value
        
        # Create a new mock account to avoid conflicts with expires_date
        mock_account = Mock()
        mock_account.id = sample_hosting_account.id
        mock_account.expires_date = datetime.now()
        
        mock_repository_factory.hosting_accounts.get.return_value = mock_account
        mock_repository_factory.hosting_accounts.update.return_value = True
        
        # Act
        result = hosting_manager.renew_hosting_account(
            account_id=mock_account.id,
            years=2
        )
        
        # Assert
        assert result is True
        mock_repository_factory.hosting_accounts.update.assert_called_once()
        call_args = mock_repository_factory.hosting_accounts.update.call_args[0]
        assert call_args[0] == mock_account.id
        assert call_args[1]['status'] == 'active'
    
    def test_delete_hosting_account_success(self, hosting_manager_with_api, mock_get_db, mock_get_repository_factory,
                                          sample_hosting_account):
        """Test successful hosting account deletion"""
        # Arrange
        mock_repository_factory = mock_get_repository_factory.return_value
        mock_repository_factory.hosting_accounts.get.return_value = sample_hosting_account
        mock_repository_factory.hosting_accounts.delete.return_value = True
        
        # Act
        result = hosting_manager_with_api.delete_hosting_account(sample_hosting_account.id)
        
        # Assert
        assert result is True
        hosting_manager_with_api.api_client.delete_account.assert_called_once_with(
            sample_hosting_account.username
        )
        mock_repository_factory.hosting_accounts.delete.assert_called_once_with(sample_hosting_account.id)
    
    def test_get_account_info_success(self, hosting_manager, mock_get_db, mock_get_repository_factory,
                                   sample_hosting_account, sample_customer, sample_hosting_package):
        """Test successful account info retrieval"""
        # Arrange
        mock_repository_factory = mock_get_repository_factory.return_value
        
        # Create proper mocks with correct attributes
        mock_account = Mock()
        mock_account.id = sample_hosting_account.id
        mock_account.domain = sample_hosting_account.domain
        mock_account.username = sample_hosting_account.username
        mock_account.status = Mock(value='active')  # Mock the status enum
        mock_account.ip_address = sample_hosting_account.ip_address
        mock_account.created_date = datetime.now()
        mock_account.expires_date = datetime.now() + timedelta(days=365)
        
        # Mock package with proper attributes
        mock_package = Mock()
        mock_package.name = sample_hosting_package.name
        mock_package.disk_space = sample_hosting_package.disk_space
        mock_package.bandwidth = sample_hosting_package.bandwidth
        mock_package.plan_type = sample_hosting_package.plan_type
        
        # Mock customer with proper attributes
        mock_customer = Mock()
        mock_customer.first_name = sample_customer.first_name
        mock_customer.last_name = sample_customer.last_name
        mock_customer.email = sample_customer.email
        
        mock_account.package = mock_package
        mock_account.customer = mock_customer
        
        mock_repository_factory.hosting_accounts.get.return_value = mock_account
        
        # Mock usage data
        usage_data = {
            'disk_usage': 100,
            'bandwidth_usage': 500,
            'disk_limit': 1024,
            'bandwidth_limit': 10240,
            'disk_usage_percent': 9.77,
            'bandwidth_usage_percent': 4.88
        }
        hosting_manager.get_account_usage = Mock(return_value=usage_data)
        
        # Act
        result = hosting_manager.get_account_info(mock_account.id)
        
        # Assert
        assert result['id'] == str(mock_account.id)
        assert result['domain'] == mock_account.domain
        assert result['username'] == mock_account.username
        assert result['status'] == 'active'
        assert result['package']['name'] == mock_package.name
        assert result['customer']['name'] == f"{mock_customer.first_name} {mock_customer.last_name}"
        assert result['usage'] == usage_data