# app/core/hosting/manager.py
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

from ..shared.database import get_db
from ..shared.repositories import get_repository_factory
from ..shared.models import HostingAccount, HostingPackage, Customer
from ..shared.exceptions import HostingError, ValidationError

logger = logging.getLogger(__name__)

class HostingManager:
    """
    مدیریت اصلی سرویس‌های هاستینگ
    """
    
    def __init__(self, api_client=None):
        self.api_client = api_client
        logger.info("Hosting Manager initialized")
    
    def create_hosting_account(self, domain: str, package_id: uuid.UUID, 
                             customer_id: uuid.UUID, username: str, 
                             password: str) -> HostingAccount:
        """
        ایجاد حساب هاستینگ جدید
        
        Args:
            domain (str): نام دامنه
            package_id (uuid.UUID): شناسه پکیج هاستینگ
            customer_id (uuid.UUID): شناسه مشتری
            username (str): نام کاربری
            password (str): رمز عبور
            
        Returns:
            HostingAccount: حساب هاستینگ ایجاد شده
        """
        try:
            db = next(get_db())
            repo_factory = get_repository_factory(db)
            
            # اعتبارسنجی ورودی‌ها
            self._validate_hosting_input(domain, username, password)
            
            # بررسی موجودی پکیج
            package = repo_factory.hosting_packages.get(package_id)
            if not package or not package.active:
                raise ValidationError("Hosting package not found or inactive")
            
            # بررسی موجودی مشتری
            customer = repo_factory.customers.get(customer_id)
            if not customer:
                raise ValidationError("Customer not found")
            
            # بررسی وجود حساب برای این دامنه
            existing_account = repo_factory.hosting_accounts.get_by_domain(domain)
            if existing_account:
                raise ValidationError(f"Hosting account already exists for domain: {domain}")
            
            logger.info(f"Creating hosting account for domain: {domain}, package: {package.name}")
            
            # ایجاد حساب در سیستم هاستینگ (cPanel/WHM)
            if self.api_client:
                hosting_response = self.api_client.create_account(
                    domain=domain,
                    username=username,
                    password=password,
                    plan=package.name,
                    email=customer.email
                )
                
                ip_address = hosting_response.get('ip_address', '0.0.0.0')
            else:
                # حالت شبیه‌سازی برای توسعه
                ip_address = "192.168.1.100"
                logger.warning("Using simulated hosting account creation")
            
            # ایجاد رکورد در دیتابیس
            account_data = {
                'domain': domain,
                'username': username,
                'package_id': package_id,
                'customer_id': customer_id,
                'ip_address': ip_address,
                'disk_usage': 0,
                'bandwidth_usage': 0,
                'expires_date': datetime.now() + timedelta(days=365)  # 1 سال
            }
            
            hosting_account = repo_factory.hosting_accounts.create(account_data)
            
            logger.info(f"Successfully created hosting account: {hosting_account.id}")
            return hosting_account
            
        except Exception as e:
            logger.error(f"Error creating hosting account for {domain}: {str(e)}")
            raise HostingError(f"Failed to create hosting account: {str(e)}")
    
    def suspend_account(self, account_id: uuid.UUID, reason: str = "Administrative") -> bool:
        """
        تعلیق حساب هاستینگ
        
        Args:
            account_id (uuid.UUID): شناسه حساب
            reason (str): دلیل تعلیق
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            db = next(get_db())
            repo_factory = get_repository_factory(db)
            
            account = repo_factory.hosting_accounts.get(account_id)
            if not account:
                raise ValidationError("Hosting account not found")
            
            logger.info(f"Suspending hosting account: {account_id}, reason: {reason}")
            
            # تعلیق حساب در سیستم هاستینگ
            if self.api_client:
                self.api_client.suspend_account(account.username, reason)
            
            # بروزرسانی وضعیت در دیتابیس
            update_data = {
                'status': 'suspended',
                'suspended_reason': reason
            }
            repo_factory.hosting_accounts.update(account_id, update_data)
            
            logger.info(f"Successfully suspended hosting account: {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error suspending hosting account {account_id}: {str(e)}")
            raise HostingError(f"Failed to suspend hosting account: {str(e)}")
    
    def unsuspend_account(self, account_id: uuid.UUID) -> bool:
        """
        رفع تعلیق حساب هاستینگ
        
        Args:
            account_id (uuid.UUID): شناسه حساب
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            db = next(get_db())
            repo_factory = get_repository_factory(db)
            
            account = repo_factory.hosting_accounts.get(account_id)
            if not account:
                raise ValidationError("Hosting account not found")
            
            logger.info(f"Unsuspending hosting account: {account_id}")
            
            # رفع تعلیق حساب در سیستم هاستینگ
            if self.api_client:
                self.api_client.unsuspend_account(account.username)
            
            # بروزرسانی وضعیت در دیتابیس
            update_data = {
                'status': 'active',
                'suspended_reason': None
            }
            repo_factory.hosting_accounts.update(account_id, update_data)
            
            logger.info(f"Successfully unsuspended hosting account: {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unsuspending hosting account {account_id}: {str(e)}")
            raise HostingError(f"Failed to unsuspend hosting account: {str(e)}")
    
    def change_hosting_plan(self, account_id: uuid.UUID, new_package_id: uuid.UUID) -> bool:
        """
        تغییر پلن هاستینگ
        
        Args:
            account_id (uuid.UUID): شناسه حساب
            new_package_id (uuid.UUID): شناسه پکیج جدید
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            db = next(get_db())
            repo_factory = get_repository_factory(db)
            
            account = repo_factory.hosting_accounts.get(account_id)
            if not account:
                raise ValidationError("Hosting account not found")
            
            new_package = repo_factory.hosting_packages.get(new_package_id)
            if not new_package or not new_package.active:
                raise ValidationError("New hosting package not found or inactive")
            
            logger.info(f"Changing hosting plan for {account_id} to {new_package.name}")
            
            # تغییر پلن در سیستم هاستینگ
            if self.api_client:
                self.api_client.change_plan(account.username, new_package.name)
            
            # بروزرسانی در دیتابیس
            update_data = {
                'package_id': new_package_id
            }
            repo_factory.hosting_accounts.update(account_id, update_data)
            
            logger.info(f"Successfully changed hosting plan for {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing hosting plan for {account_id}: {str(e)}")
            raise HostingError(f"Failed to change hosting plan: {str(e)}")
    
    def get_account_usage(self, account_id: uuid.UUID) -> Dict[str, Any]:
        """
        دریافت میزان استفاده از منابع حساب
        
        Args:
            account_id (uuid.UUID): شناسه حساب
            
        Returns:
            Dict: اطلاعات استفاده از منابع
        """
        try:
            db = next(get_db())
            repo_factory = get_repository_factory(db)
            
            account = repo_factory.hosting_accounts.get(account_id)
            if not account:
                raise ValidationError("Hosting account not found")
            
            # دریافت اطلاعات استفاده از سیستم هاستینگ
            if self.api_client:
                usage_data = self.api_client.get_account_usage(account.username)
                
                # بروزرسانی در دیتابیس
                update_data = {
                    'disk_usage': usage_data.get('disk_usage', 0),
                    'bandwidth_usage': usage_data.get('bandwidth_usage', 0)
                }
                repo_factory.hosting_accounts.update(account_id, update_data)
            else:
                # حالت شبیه‌سازی
                usage_data = {
                    'disk_usage': account.disk_usage,
                    'bandwidth_usage': account.bandwidth_usage,
                    'disk_limit': account.package.disk_space if account.package else 1024,
                    'bandwidth_limit': account.package.bandwidth if account.package else 10240
                }
            
            # محاسبه درصد استفاده
            disk_limit = usage_data.get('disk_limit', 1024)
            bandwidth_limit = usage_data.get('bandwidth_limit', 10240)
            
            usage_data['disk_usage_percent'] = round(
                (usage_data['disk_usage'] / disk_limit) * 100, 2
            ) if disk_limit > 0 else 0
            
            usage_data['bandwidth_usage_percent'] = round(
                (usage_data['bandwidth_usage'] / bandwidth_limit) * 100, 2
            ) if bandwidth_limit > 0 else 0
            
            return usage_data
            
        except Exception as e:
            logger.error(f"Error getting usage for account {account_id}: {str(e)}")
            raise HostingError(f"Failed to get account usage: {str(e)}")
    
    def renew_hosting_account(self, account_id: uuid.UUID, years: int = 1) -> bool:
        """
        تمدید حساب هاستینگ
        
        Args:
            account_id (uuid.UUID): شناسه حساب
            years (int): تعداد سال‌های تمدید
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            db = next(get_db())
            repo_factory = get_repository_factory(db)
            
            account = repo_factory.hosting_accounts.get(account_id)
            if not account:
                raise ValidationError("Hosting account not found")
            
            logger.info(f"Renewing hosting account {account_id} for {years} years")
            
            # محاسبه تاریخ انقضای جدید
            current_expiry = account.expires_date or datetime.now()
            new_expiry = current_expiry + timedelta(days=365 * years)
            
            # بروزرسانی تاریخ انقضا
            update_data = {
                'expires_date': new_expiry,
                'status': 'active'
            }
            repo_factory.hosting_accounts.update(account_id, update_data)
            
            logger.info(f"Successfully renewed hosting account {account_id} until {new_expiry}")
            return True
            
        except Exception as e:
            logger.error(f"Error renewing hosting account {account_id}: {str(e)}")
            raise HostingError(f"Failed to renew hosting account: {str(e)}")
    
    def delete_hosting_account(self, account_id: uuid.UUID) -> bool:
        """
        حذف حساب هاستینگ
        
        Args:
            account_id (uuid.UUID): شناسه حساب
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            db = next(get_db())
            repo_factory = get_repository_factory(db)
            
            account = repo_factory.hosting_accounts.get(account_id)
            if not account:
                raise ValidationError("Hosting account not found")
            
            logger.info(f"Deleting hosting account: {account_id}")
            
            # حذف حساب از سیستم هاستینگ
            if self.api_client:
                self.api_client.delete_account(account.username)
            
            # حذف از دیتابیس
            success = repo_factory.hosting_accounts.delete(account_id)
            
            if success:
                logger.info(f"Successfully deleted hosting account: {account_id}")
            else:
                logger.warning(f"Failed to delete hosting account: {account_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting hosting account {account_id}: {str(e)}")
            raise HostingError(f"Failed to delete hosting account: {str(e)}")
    
    def _validate_hosting_input(self, domain: str, username: str, password: str) -> None:
        """اعتبارسنجی ورودی‌های هاستینگ"""
        if not domain or '.' not in domain:
            raise ValidationError("Invalid domain name")
        
        if not username or len(username) < 3:
            raise ValidationError("Username must be at least 3 characters")
        
        if not password or len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        
        # بررسی کاراکترهای مجاز در نام کاربری
        import re
        if not re.match(r'^[a-z][a-z0-9_]{2,}$', username.lower()):
            raise ValidationError("Username can only contain lowercase letters, numbers, and underscores")
    
    def get_account_info(self, account_id: uuid.UUID) -> Dict[str, Any]:
        """
        دریافت اطلاعات کامل حساب هاستینگ
        
        Args:
            account_id (uuid.UUID): شناسه حساب
            
        Returns:
            Dict: اطلاعات کامل حساب
        """
        try:
            db = next(get_db())
            repo_factory = get_repository_factory(db)
            
            account = repo_factory.hosting_accounts.get(account_id)
            if not account:
                raise ValidationError("Hosting account not found")
            
            # دریافت اطلاعات استفاده
            usage_data = self.get_account_usage(account_id)
            
            # اطلاعات حساب
            account_info = {
                'id': str(account.id),
                'domain': account.domain,
                'username': account.username,
                'status': account.status.value,
                'ip_address': account.ip_address,
                'created_date': account.created_date.isoformat(),
                'expires_date': account.expires_date.isoformat() if account.expires_date else None,
                'package': {
                    'name': account.package.name,
                    'disk_space': account.package.disk_space,
                    'bandwidth': account.package.bandwidth,
                    'plan_type': account.package.plan_type
                } if account.package else None,
                'customer': {
                    'name': f"{account.customer.first_name} {account.customer.last_name}",
                    'email': account.customer.email
                } if account.customer else None,
                'usage': usage_data
            }
            
            return account_info
            
        except Exception as e:
            logger.error(f"Error getting account info for {account_id}: {str(e)}")
            raise HostingError(f"Failed to get account info: {str(e)}")