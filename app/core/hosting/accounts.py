# app/core/hosting/accounts.py
import logging
from typing import List, Dict, Optional, Any
import uuid
from ..shared.models import HostingAccount, Customer
from ..shared.exceptions import HostingError, ValidationError

logger = logging.getLogger(__name__)

class HostingAccountManager:
    """مدیریت حساب‌های هاستینگ"""
    
    def __init__(self, repository_factory):
        self.repo_factory = repository_factory
        logger.info("Hosting Account Manager initialized")
    
    def get_account_by_domain(self, domain: str) -> Optional[HostingAccount]:
        """دریافت حساب بر اساس دامنه"""
        try:
            return self.repo_factory.hosting_accounts.get_by_domain(domain)
        except Exception as e:
            logger.error(f"Error getting account for domain {domain}: {str(e)}")
            raise HostingError(f"Failed to get hosting account: {str(e)}")
    
    def get_customer_accounts(self, customer_id: uuid.UUID) -> List[HostingAccount]:
        """دریافت تمام حساب‌های یک مشتری"""
        try:
            return self.repo_factory.hosting_accounts.get_customer_accounts(customer_id)
        except Exception as e:
            logger.error(f"Error getting accounts for customer {customer_id}: {str(e)}")
            raise HostingError(f"Failed to get customer accounts: {str(e)}")
    
    def update_account_usage(self, account_id: uuid.UUID, 
                           disk_usage: int, bandwidth_usage: int) -> bool:
        """بروزرسانی میزان استفاده از منابع"""
        try:
            return self.repo_factory.hosting_accounts.update_usage(
                account_id, disk_usage, bandwidth_usage
            )
        except Exception as e:
            logger.error(f"Error updating usage for account {account_id}: {str(e)}")
            raise HostingError(f"Failed to update account usage: {str(e)}")