# tests/test_domain_manager.py
import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.core.domain.manager import DomainManager
from app.core.shared.models import Domain, ContactInfo, PriceInfo, DomainStatus
from app.core.shared.exceptions import DomainError, ValidationError

class TestDomainManager:
    """Test suite for DomainManager class"""
    
    @pytest.fixture
    def mock_api_client(self):
        """Mock API client fixture"""
        client = Mock()
        client.check_availability = Mock()
        client.register_domain = Mock()
        client.renew_domain = Mock()
        client.transfer_domain = Mock()
        client.get_domain_status = Mock()
        client.lock_domain = Mock()
        client.unlock_domain = Mock()
        client.get_auth_code = Mock()
        client.get_domain_info = Mock()
        client.enable_whois_privacy = Mock()
        return client
    
    @pytest.fixture
    def mock_config(self):
        """Mock config fixture"""
        config = Mock()
        config.get_tld_price.return_value = 10.0  # Base price for all TLDs
        return config
    
    @pytest.fixture
    def domain_manager(self, mock_api_client, mock_config):
        """DomainManager instance fixture"""
        return DomainManager(mock_api_client, mock_config)
    
    @pytest.fixture
    def sample_contact_info(self):
        """Sample contact information fixture"""
        return ContactInfo(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1.5551234567",
            address="123 Main St",
            city="New York",
            country="US",
            zip_code="10001"
        )
    
    @pytest.fixture
    def sample_domain_data(self):
        """Sample domain data for API responses"""
        return {
            'status': 'active',
            'expiry_date': (datetime.now() + timedelta(days=365)).isoformat(),
            'registration_date': datetime.now().isoformat(),
            'nameservers': ['ns1.example.com', 'ns2.example.com'],
            'locked': False,
            'privacy': False,
            'auto_renew': True
        }

    # 🔍 Tests for Domain Availability Checking
    
    def test_check_domain_availability_success(self, domain_manager, mock_api_client):
        """Test successful domain availability check"""
        # Setup
        domain_name = "example.com"
        mock_api_client.check_availability.return_value = {'available': True}
        
        # Execute
        result = domain_manager.check_domain_availability(domain_name)
        
        # Assert
        assert result is True
        mock_api_client.check_availability.assert_called_once_with(domain_name)
    
    def test_check_domain_availability_not_available(self, domain_manager, mock_api_client):
        """Test domain availability check when domain is taken"""
        # Setup
        domain_name = "taken-domain.com"
        mock_api_client.check_availability.return_value = {'available': False}
        
        # Execute
        result = domain_manager.check_domain_availability(domain_name)
        
        # Assert
        assert result is False
    
    def test_check_domain_availability_invalid_domain(self, domain_manager):
        """Test domain availability check with invalid domain name"""
        # Setup
        invalid_domains = [
            "invalid_domain",           # بدون dot
            ".com",                     # فقط TLD
            "test..com",                # دو dot پشت سر هم
            "-test.com",                # شروع با خط تیره
            "test-.com",                # پایان با خط تیره
            "a" * 254 + ".com",         # خیلی طولانی
        ]
        
        for invalid_domain in invalid_domains:
            with pytest.raises(DomainError):
                domain_manager.check_domain_availability(invalid_domain)
    
    def test_check_domain_availability_api_error(self, domain_manager, mock_api_client):
        """Test domain availability check with API error"""
        # Setup
        domain_name = "example.com"
        mock_api_client.check_availability.side_effect = Exception("API Error")
        
        # Execute & Assert
        with pytest.raises(DomainError):
            domain_manager.check_domain_availability(domain_name)
    
    def test_check_bulk_domains_availability(self, domain_manager, mock_api_client):
        """Test bulk domain availability check"""
        # Setup
        domain_list = ["example.com", "test.org", "mydomain.net"]
        mock_api_client.check_availability.side_effect = [
            {'available': True},
            {'available': False},
            {'available': True}
        ]
        
        # Execute
        results = domain_manager.check_bulk_domains_availability(domain_list)
        
        # Assert
        assert results == {
            "example.com": True,
            "test.org": False,
            "mydomain.net": True
        }
        assert mock_api_client.check_availability.call_count == 3
    
    def test_check_bulk_domains_with_errors(self, domain_manager, mock_api_client):
        """Test bulk domain availability with some errors"""
        # Setup
        domain_list = ["good.com", "error.com", "another.com"]
        
        def side_effect(domain):
            if domain == "error.com":
                raise Exception("API Error")
            return {'available': True}
        
        mock_api_client.check_availability.side_effect = side_effect
        
        # Execute
        results = domain_manager.check_bulk_domains_availability(domain_list)
        
        # Assert
        assert results["good.com"] is True
        assert results["error.com"] is False  # Should be False on error
        assert results["another.com"] is True

    # 💡 Tests for Domain Suggestions
    
    def test_suggest_domain_names_basic(self, domain_manager):
        """Test basic domain name suggestions"""
        # Setup
        keyword = "test"
        
        # Execute
        suggestions = domain_manager.suggest_domain_names(keyword, count=5)
        
        # Assert
        assert len(suggestions) == 5
        assert "test.com" in suggestions
        assert "test.net" in suggestions
        assert "test.org" in suggestions
    
    def test_suggest_domain_names_custom_tlds(self, domain_manager):
        """Test domain suggestions with custom TLDs"""
        # Setup
        keyword = "myapp"
        custom_tlds = [".io", ".co", ".dev"]
        
        # Execute
        suggestions = domain_manager.suggest_domain_names(
            keyword, tlds=custom_tlds, count=3
        )
        
        # Assert
        assert len(suggestions) == 3
        assert "myapp.io" in suggestions
        assert "myapp.co" in suggestions
        assert "myapp.dev" in suggestions
    
    def test_suggest_domain_names_combined(self, domain_manager):
        """Test combined domain name suggestions"""
        # Setup
        keyword = "shop"
        
        # Execute
        suggestions = domain_manager.suggest_domain_names(keyword, count=10)
        
        # Assert
        assert len(suggestions) == 10
        # Check for combined suggestions
        combined_found = any("myshop" in s for s in suggestions)
        assert combined_found, "Should include combined suggestions"

    # 📝 Tests for Domain Registration
    
    def test_register_domain_success(self, domain_manager, mock_api_client, sample_contact_info):
        """Test successful domain registration"""
        # Setup
        domain_name = "newdomain.com"
        years = 2
        
        # Mock availability check
        mock_api_client.check_availability.return_value = {'available': True}
        
        # Mock registration response
        mock_api_client.register_domain.return_value = {'success': True}
        
        # Execute
        domain = domain_manager.register_domain(domain_name, years, sample_contact_info)
        
        # Assert
        assert domain.name == domain_name
        assert domain.status == DomainStatus.ACTIVE
        assert domain.auto_renew is True
        assert domain.privacy_protection is False
        
        # Verify API calls
        mock_api_client.check_availability.assert_called_once_with(domain_name)
        mock_api_client.register_domain.assert_called_once()
    
    def test_register_domain_not_available(self, domain_manager, mock_api_client, sample_contact_info):
        """Test domain registration when domain is not available"""
        # Setup
        domain_name = "taken.com"
        mock_api_client.check_availability.return_value = {'available': False}
        
        # Execute & Assert
        with pytest.raises(DomainError, match="is not available"):
            domain_manager.register_domain(domain_name, 1, sample_contact_info)
    
    def test_register_domain_invalid_years(self, domain_manager, mock_api_client, sample_contact_info):
        """Test domain registration with invalid years"""
        # Setup
        domain_name = "test.com"
        mock_api_client.check_availability.return_value = {'available': True}
        
        invalid_years = [0, -1]
        
        for years in invalid_years:
            with pytest.raises(DomainError):
                domain_manager.register_domain(domain_name, years, sample_contact_info)
    
    def test_register_domain_with_privacy(self, domain_manager, mock_api_client, sample_contact_info):
        """Test domain registration with privacy protection"""
        # Setup
        domain_name = "private.com"
        years = 1
        
        # Mock methods
        mock_api_client.check_availability.return_value = {'available': True}
        mock_api_client.register_domain.return_value = {'success': True}
        mock_api_client.enable_whois_privacy.return_value = {'success': True}
        
        # Execute
        domain = domain_manager.register_domain_with_privacy(
            domain_name, years, sample_contact_info
        )
        
        # Assert
        assert domain.privacy_protection is True
        mock_api_client.enable_whois_privacy.assert_called_once_with(domain_name)

    # 🔄 Tests for Domain Renewal
    
    def test_renew_domain_success(self, domain_manager, mock_api_client):
        """Test successful domain renewal"""
        # Setup
        domain_name = "example.com"
        years = 1
        mock_api_client.renew_domain.return_value = {'success': True}
        
        # Execute
        result = domain_manager.renew_domain(domain_name, years)
        
        # Assert
        assert result is True
        mock_api_client.renew_domain.assert_called_once_with({
            'domain': domain_name,
            'years': years
        })
    
    def test_renew_domain_invalid_years(self, domain_manager):
        """Test domain renewal with invalid years"""
        invalid_cases = [
            (0, "zero years"),
            (-1, "negative years"),
        ]
        
        for years, description in invalid_cases:
            with pytest.raises(DomainError):
                domain_manager.renew_domain("test.com", years)
    
    def test_get_renewal_price(self, domain_manager, mock_config):
        """Test getting renewal price"""
        # Setup
        domain_name = "example.com"
        years = 2
        
        # Execute
        price_info = domain_manager.get_renewal_price(domain_name, years)
        
        # Assert
        assert isinstance(price_info, PriceInfo)
        assert price_info.registration == 20.0  # 10 * 2 years
        assert price_info.renewal == 20.0
        assert price_info.transfer == 20.0
        assert price_info.currency == "USD"
        
        mock_config.get_tld_price.assert_called_with('com', 'renewal')

    # 🔀 Tests for Domain Transfer
    
    def test_transfer_domain_success(self, domain_manager, mock_api_client, sample_contact_info):
        """Test successful domain transfer"""
        # Setup
        domain_name = "transfer.com"
        auth_code = "ABC123"
        mock_api_client.transfer_domain.return_value = {'success': True}
        
        # Execute
        result = domain_manager.transfer_domain(domain_name, auth_code, sample_contact_info)
        
        # Assert
        assert result is True
        mock_api_client.transfer_domain.assert_called_once()
    
    def test_check_transfer_eligibility_eligible(self, domain_manager, mock_api_client):
        """Test transfer eligibility for eligible domain"""
        # Setup
        domain_name = "eligible.com"
        
        # Mock domain details
        future_date = datetime.now() + timedelta(days=90)
        
        with patch.object(domain_manager, 'get_domain_locking_status') as mock_lock:
            with patch.object(domain_manager, 'get_domain_details') as mock_details:
                mock_lock.return_value = False  # Not locked
                mock_details.return_value = Mock(expiry_date=future_date)
                
                # Execute
                result = domain_manager.check_transfer_eligibility(domain_name)
                
                # Assert
                assert result is True
    
    def test_check_transfer_eligibility_locked(self, domain_manager):
        """Test transfer eligibility for locked domain"""
        # Setup
        domain_name = "locked.com"
        
        with patch.object(domain_manager, 'get_domain_locking_status') as mock_lock:
            mock_lock.return_value = True  # Domain is locked
            
            # Execute
            result = domain_manager.check_transfer_eligibility(domain_name)
            
            # Assert
            assert result is False
    
    def test_check_transfer_eligibility_expiring_soon(self, domain_manager):
        """Test transfer eligibility for domain expiring soon"""
        # Setup
        domain_name = "expiring.com"
        
        with patch.object(domain_manager, 'get_domain_locking_status') as mock_lock:
            with patch.object(domain_manager, 'get_domain_details') as mock_details:
                mock_lock.return_value = False
                # Domain expires in 30 days
                expiring_date = datetime.now() + timedelta(days=30)
                mock_details.return_value = Mock(expiry_date=expiring_date)
                
                # Execute
                result = domain_manager.check_transfer_eligibility(domain_name)
                
                # Assert
                assert result is False

    # 🔒 Tests for Domain Locking
    
    def test_get_domain_locking_status(self, domain_manager, mock_api_client):
        """Test getting domain locking status"""
        # Setup
        domain_name = "test.com"
        mock_api_client.get_domain_status.return_value = {'locked': True}
        
        # Execute
        result = domain_manager.get_domain_locking_status(domain_name)
        
        # Assert
        assert result is True
        mock_api_client.get_domain_status.assert_called_once_with(domain_name)
    
    def test_lock_domain_success(self, domain_manager, mock_api_client):
        """Test successful domain locking"""
        # Setup
        domain_name = "lockme.com"
        mock_api_client.lock_domain.return_value = {'success': True}
        
        # Execute
        result = domain_manager.lock_domain(domain_name)
        
        # Assert
        assert result is True
        mock_api_client.lock_domain.assert_called_once_with(domain_name)
    
    def test_unlock_domain_success(self, domain_manager, mock_api_client):
        """Test successful domain unlocking"""
        # Setup
        domain_name = "unlockme.com"
        mock_api_client.unlock_domain.return_value = {'success': True}
        
        # Execute
        result = domain_manager.unlock_domain(domain_name)
        
        # Assert
        assert result is True
        mock_api_client.unlock_domain.assert_called_once_with(domain_name)
    
    def test_get_authorization_code(self, domain_manager, mock_api_client):
        """Test getting authorization code"""
        # Setup
        domain_name = "test.com"
        auth_code = "AUTH123456"
        mock_api_client.get_auth_code.return_value = {'auth_code': auth_code}
        
        # Execute
        result = domain_manager.get_authorization_code(domain_name)
        
        # Assert
        assert result == auth_code
        mock_api_client.get_auth_code.assert_called_once_with(domain_name)

    # 💰 Tests for Pricing
    
    def test_get_tld_pricing(self, domain_manager, mock_config):
        """Test getting TLD pricing"""
        # Setup
        tld_list = [".com", ".net", ".org"]
        mock_config.get_tld_price.return_value = 15.0
        
        # Execute
        pricing = domain_manager.get_tld_pricing(tld_list)
        
        # Assert
        assert len(pricing) == 3
        for tld in tld_list:
            assert tld in pricing
            assert isinstance(pricing[tld], PriceInfo)
            assert pricing[tld].registration == 15.0
        
        # Verify config calls
        assert mock_config.get_tld_price.call_count == 9  # 3 TLDs × 3 operations
    
    def test_get_domain_registration_price(self, domain_manager, mock_config):
        """Test getting domain registration price"""
        # Setup
        tld = ".com"
        years = 3
        mock_config.get_tld_price.return_value = 12.0
        
        # Execute
        price_info = domain_manager.get_domain_registration_price(tld, years)
        
        # Assert
        assert price_info.registration == 36.0  # 12 * 3 years
        mock_config.get_tld_price.assert_called_with('com', 'registration')

    # 🛡️ Tests for Validation Methods
    
    def test_validate_domain_name_valid(self, domain_manager):
        """Test domain name validation with valid names"""
        valid_domains = [
            "example.com",
            "test.co.uk",
            "my-domain.org",
            "sub.domain.net",
        ]
        
        for domain in valid_domains:
            assert domain_manager._validate_domain_name(domain) is True
    
    def test_validate_domain_name_invalid(self, domain_manager):
        """Test domain name validation with invalid names"""
        invalid_domains = [
            "invalid",          # No TLD
            ".com",             # Only TLD
            "test..com",        # Double dots
            "-test.com",        # Starts with hyphen
            "test-.com",        # Ends with hyphen
            "test_.com",        # Underscore not allowed
            "",                 # Empty string
            "a" * 64 + ".com",  # Label too long
        ]
        
        for domain in invalid_domains:
            assert domain_manager._validate_domain_name(domain) is False
    
    def test_validate_registration_input_valid(self, domain_manager, sample_contact_info):
        """Test registration input validation with valid data"""
        # This should not raise any exceptions
        domain_manager._validate_registration_input(
            "valid.com", 1, sample_contact_info
        )
    
    def test_validate_registration_input_invalid(self, domain_manager, sample_contact_info):
        """Test registration input validation with invalid data"""
        # Invalid domain
        with pytest.raises(ValidationError):
            domain_manager._validate_registration_input(
                "invalid", 1, sample_contact_info
            )
        
        # Invalid years
        with pytest.raises(ValidationError):
            domain_manager._validate_registration_input(
                "valid.com", 0, sample_contact_info
            )
        
        # Invalid contact info
        invalid_contact = ContactInfo(email="")  # Missing required email
        with pytest.raises(ValidationError):
            domain_manager._validate_registration_input(
                "valid.com", 1, invalid_contact
            )

    # 📊 Tests for Domain Details
    
    def test_get_domain_details_success(self, domain_manager, mock_api_client, sample_domain_data):
        """Test getting domain details successfully"""
        # Setup
        domain_name = "example.com"
        mock_api_client.get_domain_info.return_value = sample_domain_data
        
        # Execute
        domain = domain_manager.get_domain_details(domain_name)
        
        # Assert
        assert domain.name == domain_name
        assert domain.status == DomainStatus.ACTIVE
        assert len(domain.nameservers) == 2
        mock_api_client.get_domain_info.assert_called_once_with(domain_name)
    
    def test_get_domain_details_api_error(self, domain_manager, mock_api_client):
        """Test getting domain details with API error"""
        # Setup
        domain_name = "error.com"
        mock_api_client.get_domain_info.side_effect = Exception("API Error")
        
        # Execute & Assert
        with pytest.raises(DomainError):
            domain_manager.get_domain_details(domain_name)

    # 🔄 Tests for Error Handling and Edge Cases
    
    def test_api_client_not_implemented(self, domain_manager, mock_api_client):
        """Test behavior when API client methods are not implemented"""
        # Setup
        domain_name = "test.com"
        mock_api_client.check_availability.side_effect = NotImplementedError("Method not implemented")
        
        # Execute & Assert
        with pytest.raises(DomainError):
            domain_manager.check_domain_availability(domain_name)
    
    def test_network_timeout_handling(self, domain_manager, mock_api_client):
        """Test handling of network timeouts"""
        # Setup
        domain_name = "timeout.com"
        
        # Simulate different types of network errors
        network_errors = [
            TimeoutError("Request timed out"),
            ConnectionError("Connection failed"),
            Exception("Unknown network error")
        ]
        
        for error in network_errors:
            mock_api_client.check_availability.side_effect = error
            with pytest.raises(DomainError):
                domain_manager.check_domain_availability(domain_name)
    
    def test_concurrent_operations(self, domain_manager, mock_api_client):
        """Test that concurrent operations don't interfere"""
        # This would typically require async testing, but we can test basic isolation
        domain_name = "concurrent.com"
        
        # Setup different responses for different methods
        mock_api_client.check_availability.return_value = {'available': True}
        mock_api_client.get_domain_status.return_value = {'locked': False}
        
        # Execute multiple operations
        availability = domain_manager.check_domain_availability(domain_name)
        lock_status = domain_manager.get_domain_locking_status(domain_name)
        
        # Assert
        assert availability is True
        assert lock_status is False
        
        # Verify both methods were called correctly
        mock_api_client.check_availability.assert_called_with(domain_name)
        mock_api_client.get_domain_status.assert_called_with(domain_name)


class TestDomainManagerIntegration:
    """Integration-style tests for DomainManager"""
    
    @pytest.fixture
    def real_domain_manager(self):
        """Create a DomainManager with minimal real dependencies"""
        # This would use a test API client in a real scenario
        mock_api = Mock()
        mock_config = Mock()
        mock_config.get_tld_price.return_value = 10.0
        
        return DomainManager(mock_api, mock_config)
    
    def test_complete_domain_lifecycle(self, real_domain_manager, sample_contact_info):
        """Test a complete domain lifecycle: check -> register -> lock -> renew"""
        # This is a high-level integration test
        api_client = real_domain_manager.api_client
        config = real_domain_manager.config
        
        # Setup all mock responses
        api_client.check_availability.return_value = {'available': True}
        api_client.register_domain.return_value = {'success': True}
        api_client.lock_domain.return_value = {'success': True}
        api_client.renew_domain.return_value = {'success': True}
        api_client.enable_whois_privacy.return_value = {'success': True}
        
        domain_name = "lifecycle.com"
        
        # 1. Check availability
        available = real_domain_manager.check_domain_availability(domain_name)
        assert available is True
        
        # 2. Register domain
        domain = real_domain_manager.register_domain(domain_name, 1, sample_contact_info)
        assert domain.name == domain_name
        assert domain.status == DomainStatus.ACTIVE
        
        # 3. Lock domain
        lock_result = real_domain_manager.lock_domain(domain_name)
        assert lock_result is True
        
        # 4. Renew domain
        renew_result = real_domain_manager.renew_domain(domain_name, 1)
        assert renew_result is True
        
        # Verify all API calls were made
        assert api_client.check_availability.call_count == 2
        assert api_client.register_domain.call_count == 1
        assert api_client.lock_domain.call_count == 1
        assert api_client.renew_domain.call_count == 1


# Run tests with: pytest tests/test_domain_manager.py -v