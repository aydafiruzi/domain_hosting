# test_hosting_packages.py
import pytest
import uuid
from unittest.mock import Mock
from app.core.hosting.packages import HostingPackageManager
from app.core.shared.exceptions import HostingError


class TestHostingPackageManager:
    """Test cases for HostingPackageManager"""
    
    @pytest.fixture
    def mock_repo_factory(self):
        return Mock()
    
    @pytest.fixture
    def package_manager(self, mock_repo_factory):
        return HostingPackageManager(mock_repo_factory)
    
    def test_get_all_packages_success(self, package_manager, mock_repo_factory):
        """Test successful retrieval of all packages"""
        # Arrange
        expected_packages = [Mock(), Mock(), Mock()]
        mock_repo_factory.hosting_packages.get_active_packages.return_value = expected_packages
        
        # Act
        result = package_manager.get_all_packages()
        
        # Assert
        assert result == expected_packages
        mock_repo_factory.hosting_packages.get_active_packages.assert_called_once()
    
    def test_get_all_packages_error(self, package_manager, mock_repo_factory):
        """Test error handling in package retrieval"""
        # Arrange
        mock_repo_factory.hosting_packages.get_active_packages.side_effect = Exception("DB error")
        
        # Act & Assert
        with pytest.raises(HostingError) as exc_info:
            package_manager.get_all_packages()
        
        assert "Failed to get hosting packages" in str(exc_info.value)
    
    def test_get_package_by_id_success(self, package_manager, mock_repo_factory):
        """Test successful package retrieval by ID"""
        # Arrange
        package_id = uuid.uuid4()
        expected_package = Mock()
        mock_repo_factory.hosting_packages.get.return_value = expected_package
        
        # Act
        result = package_manager.get_package_by_id(package_id)
        
        # Assert
        assert result == expected_package
        mock_repo_factory.hosting_packages.get.assert_called_once_with(package_id)
    
    def test_get_package_by_id_not_found(self, package_manager, mock_repo_factory):
        """Test package retrieval when ID not found"""
        # Arrange
        package_id = uuid.uuid4()
        mock_repo_factory.hosting_packages.get.return_value = None
        
        # Act
        result = package_manager.get_package_by_id(package_id)
        
        # Assert
        assert result is None
    
    def test_get_package_by_id_error(self, package_manager, mock_repo_factory):
        """Test error handling in package retrieval by ID"""
        # Arrange
        package_id = uuid.uuid4()
        mock_repo_factory.hosting_packages.get.side_effect = Exception("DB error")
        
        # Act & Assert
        with pytest.raises(HostingError) as exc_info:
            package_manager.get_package_by_id(package_id)
        
        assert "Failed to get hosting package" in str(exc_info.value)
    
    def test_get_packages_by_type_success(self, package_manager, mock_repo_factory):
        """Test successful package retrieval by type"""
        # Arrange
        plan_type = "shared"
        expected_packages = [Mock(), Mock()]
        mock_repo_factory.hosting_packages.get_by_plan_type.return_value = expected_packages
        
        # Act
        result = package_manager.get_packages_by_type(plan_type)
        
        # Assert
        assert result == expected_packages
        mock_repo_factory.hosting_packages.get_by_plan_type.assert_called_once_with(plan_type)
    
    def test_get_packages_by_type_error(self, package_manager, mock_repo_factory):
        """Test error handling in package retrieval by type"""
        # Arrange
        plan_type = "shared"
        mock_repo_factory.hosting_packages.get_by_plan_type.side_effect = Exception("DB error")
        
        # Act & Assert
        with pytest.raises(HostingError) as exc_info:
            package_manager.get_packages_by_type(plan_type)
        
        assert "Failed to get packages by type" in str(exc_info.value)