# app/core/hosting/packages.py
import logging
from typing import List, Optional
import uuid
from ..shared.models import HostingPackage
from ..shared.exceptions import HostingError

logger = logging.getLogger(__name__)

class HostingPackageManager:
    """مدیریت پکیج‌های هاستینگ"""
    
    def __init__(self, repository_factory):
        self.repo_factory = repository_factory
        logger.info("Hosting Package Manager initialized")
    
    def get_all_packages(self) -> List[HostingPackage]:
        """دریافت تمام پکیج‌های فعال"""
        try:
            return self.repo_factory.hosting_packages.get_active_packages()
        except Exception as e:
            logger.error(f"Error getting hosting packages: {str(e)}")
            raise HostingError(f"Failed to get hosting packages: {str(e)}")
    
    def get_package_by_id(self, package_id: uuid.UUID) -> Optional[HostingPackage]:
        """دریافت پکیج بر اساس شناسه"""
        try:
            return self.repo_factory.hosting_packages.get(package_id)
        except Exception as e:
            logger.error(f"Error getting package {package_id}: {str(e)}")
            raise HostingError(f"Failed to get hosting package: {str(e)}")
    
    def get_packages_by_type(self, plan_type: str) -> List[HostingPackage]:
        """دریافت پکیج‌ها بر اساس نوع"""
        try:
            return self.repo_factory.hosting_packages.get_by_plan_type(plan_type)
        except Exception as e:
            logger.error(f"Error getting packages by type {plan_type}: {str(e)}")
            raise HostingError(f"Failed to get packages by type: {str(e)}")