# tests/conftest.py
import pytest
import sys
import os
import uuid
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging to avoid cluttering test output"""
    with patch('app.core.hosting.manager.logger'), \
         patch('app.core.hosting.accounts.logger'), \
         patch('app.core.hosting.packages.logger'), \
         patch('app.core.hosting.cpanel.logger'):
        yield

@pytest.fixture
def sample_contact_info():
    """Sample contact information fixture"""
    # Mock the ContactInfo to avoid import issues
    contact_info = Mock()
    contact_info.first_name = "John"
    contact_info.last_name = "Doe"
    contact_info.email = "john.doe@example.com"
    contact_info.phone = "+1.5551234567"
    contact_info.address = "123 Main St"
    contact_info.city = "New York"
    contact_info.country = "US"
    contact_info.zip_code = "10001"
    
    return contact_info

@pytest.fixture
def sample_domain_object():
    """Sample Domain object for testing"""
    # Create a Mock for Domain to avoid SQLAlchemy issues
    domain = Mock()
    domain.name = "test-domain.com"
    domain.status = "ACTIVE"  # Use string instead of enum
    domain.expiry_date = datetime.now() + timedelta(days=365)
    domain.registration_date = datetime.now()
    domain.nameservers = ['ns1.test.com', 'ns2.test.com']
    domain.locked = False
    domain.privacy_protection = False
    domain.auto_renew = True
    
    return domain

# Hosting-related fixtures
@pytest.fixture
def sample_hosting_account():
    """Sample hosting account fixture"""
    account = Mock()
    account.id = uuid.uuid4()
    account.domain = "example.com"
    account.username = "testuser"
    account.status = Mock()  # Simple mock for status
    account.status.value = "active"  # Set value directly
    account.ip_address = "192.168.1.100"
    account.created_date = datetime.now()
    account.expires_date = datetime.now() + timedelta(days=365)
    account.disk_usage = 100
    account.bandwidth_usage = 500
    account.suspended_reason = None
    
    return account

@pytest.fixture
def sample_hosting_package():
    """Sample hosting package fixture"""
    package = Mock()
    package.id = uuid.uuid4()
    package.name = "starter"
    package.disk_space = 1024
    package.bandwidth = 10240
    package.active = True
    package.plan_type = "shared"
    
    return package

@pytest.fixture
def sample_customer():
    """Sample customer fixture"""
    customer = Mock()
    customer.id = uuid.uuid4()
    customer.first_name = "John"
    customer.last_name = "Doe"
    customer.email = "john.doe@example.com"
    
    return customer

@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return Mock()

@pytest.fixture
def mock_repository_factory():
    """Mock repository factory"""
    repo_factory = Mock()
    
    # Mock individual repositories
    repo_factory.hosting_accounts = Mock()
    repo_factory.hosting_packages = Mock()
    repo_factory.customers = Mock()
    
    return repo_factory

@pytest.fixture
def hosting_manager():
    """HostingManager instance without API client"""
    from app.core.hosting.manager import HostingManager
    return HostingManager()

@pytest.fixture
def hosting_manager_with_api():
    """HostingManager instance with API client"""
    from app.core.hosting.manager import HostingManager
    api_client = Mock()
    return HostingManager(api_client=api_client)

@pytest.fixture
def cpanel_manager():
    """CPanelManager instance for testing"""
    from app.core.hosting.cpanel import CPanelManager
    return CPanelManager(
        whm_host="whm.example.com",
        whm_username="root",
        whm_token="test_token"
    )

@pytest.fixture
def hosting_account_manager(mock_repository_factory):
    """HostingAccountManager instance for testing"""
    from app.core.hosting.accounts import HostingAccountManager
    return HostingAccountManager(mock_repository_factory)

@pytest.fixture
def hosting_package_manager(mock_repository_factory):
    """HostingPackageManager instance for testing"""
    from app.core.hosting.packages import HostingPackageManager
    return HostingPackageManager(mock_repository_factory)

@pytest.fixture
def mock_get_db(mock_db_session):
    """Mock get_db function"""
    with patch('app.core.hosting.manager.get_db') as mock_get_db:
        mock_get_db.return_value = iter([mock_db_session])
        yield mock_get_db

@pytest.fixture
def mock_get_repository_factory(mock_repository_factory):
    """Mock get_repository_factory function"""
    with patch('app.core.hosting.manager.get_repository_factory') as mock_get_repo:
        mock_get_repo.return_value = mock_repository_factory
        yield mock_get_repo

# Mock API responses
@pytest.fixture
def mock_cpanel_create_response():
    """Mock cPanel create account response"""
    return {
        "metadata": {"result": 1},
        "data": {"ip": "192.168.1.100"}
    }

@pytest.fixture
def mock_cpanel_usage_response():
    """Mock cPanel usage response"""
    return {
        "metadata": {"result": 1},
        "data": {
            "totalbytes": 1048576,  # 1MB
            "softlimit": 10485760   # 10MB
        }
    }

@pytest.fixture
def mock_cpanel_success_response():
    """Mock generic successful cPanel response"""
    return {
        "metadata": {"result": 1}
    }