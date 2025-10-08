# app/core/hosting/cpanel.py
import logging
import requests
from typing import Dict, List, Optional, Any
from ..shared.exceptions import HostingError, ValidationError

logger = logging.getLogger(__name__)

class CPanelManager:
    """
    مدیریت cPanel/WHM API
    """
    
    def __init__(self, whm_host: str, whm_username: str, whm_token: str):
        self.whm_host = whm_host.rstrip('/')
        self.whm_username = whm_username
        self.whm_token = whm_token
        self.base_url = f"https://{self.whm_host}:2087/json-api"
        logger.info("cPanel Manager initialized")
    
    def _make_request(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """ایجاد درخواست به WHM API"""
        try:
            headers = {
                'Authorization': f'whm {self.whm_username}:{self.whm_token}'
            }
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.post(
                url,
                data=data,
                headers=headers,
                verify=True,  # در production باید True باشد
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"WHM API request failed: {str(e)}")
            raise HostingError(f"WHM API request failed: {str(e)}")
    
    def create_cpanel_account(self, domain: str, username: str, password: str, 
                            plan: str, email: str) -> Dict[str, Any]:
        """
        ایجاد حساب cPanel جدید
        
        Args:
            domain (str): نام دامنه
            username (str): نام کاربری
            password (str): رمز عبور
            plan (str): نام پلن
            email (str): ایمیل مشتری
            
        Returns:
            Dict: نتیجه ایجاد حساب
        """
        try:
            data = {
                'api.version': 1,
                'domain': domain,
                'user': username,
                'password': password,
                'plan': plan,
                'contactemail': email
            }
            
            response = self._make_request('createacct', data)
            
            if response.get('metadata', {}).get('result') == 1:
                logger.info(f"Successfully created cPanel account: {username}")
                return {
                    'success': True,
                    'username': username,
                    'domain': domain,
                    'ip_address': response['data']['ip']
                }
            else:
                error_msg = response.get('metadata', {}).get('reason', 'Unknown error')
                raise HostingError(f"Failed to create cPanel account: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error creating cPanel account {username}: {str(e)}")
            raise
    
    def suspend_account(self, username: str, reason: str = "Administrative") -> bool:
        """
        تعلیق حساب cPanel
        
        Args:
            username (str): نام کاربری
            reason (str): دلیل تعلیق
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            data = {
                'api.version': 1,
                'user': username,
                'reason': reason
            }
            
            response = self._make_request('suspendacct', data)
            
            if response.get('metadata', {}).get('result') == 1:
                logger.info(f"Successfully suspended cPanel account: {username}")
                return True
            else:
                error_msg = response.get('metadata', {}).get('reason', 'Unknown error')
                raise HostingError(f"Failed to suspend cPanel account: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error suspending cPanel account {username}: {str(e)}")
            raise
    
    def unsuspend_account(self, username: str) -> bool:
        """
        رفع تعلیق حساب cPanel
        
        Args:
            username (str): نام کاربری
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            data = {
                'api.version': 1,
                'user': username
            }
            
            response = self._make_request('unsuspendacct', data)
            
            if response.get('metadata', {}).get('result') == 1:
                logger.info(f"Successfully unsuspended cPanel account: {username}")
                return True
            else:
                error_msg = response.get('metadata', {}).get('reason', 'Unknown error')
                raise HostingError(f"Failed to unsuspend cPanel account: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error unsuspending cPanel account {username}: {str(e)}")
            raise
    
    def change_plan(self, username: str, new_plan: str) -> bool:
        """
        تغییر پلن حساب cPanel
        
        Args:
            username (str): نام کاربری
            new_plan (str): پلن جدید
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            data = {
                'api.version': 1,
                'user': username,
                'pkg': new_plan
            }
            
            response = self._make_request('changepackage', data)
            
            if response.get('metadata', {}).get('result') == 1:
                logger.info(f"Successfully changed plan for {username} to {new_plan}")
                return True
            else:
                error_msg = response.get('metadata', {}).get('reason', 'Unknown error')
                raise HostingError(f"Failed to change plan: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error changing plan for {username}: {str(e)}")
            raise
    
    def get_account_usage(self, username: str) -> Dict[str, Any]:
        """
        دریافت میزان استفاده از منابع حساب
        
        Args:
            username (str): نام کاربری
            
        Returns:
            Dict: اطلاعات استفاده از منابع
        """
        try:
            data = {
                'api.version': 1,
                'user': username
            }
            
            response = self._make_request('get_disk_usage', data)
            
            if response.get('metadata', {}).get('result') == 1:
                usage_data = response['data']
                
                return {
                    'disk_usage': int(usage_data.get('totalbytes', 0)),
                    'disk_limit': int(usage_data.get('softlimit', 0)),
                    'bandwidth_usage': 0,  # نیاز به API جداگانه دارد
                    'bandwidth_limit': 0
                }
            else:
                error_msg = response.get('metadata', {}).get('reason', 'Unknown error')
                raise HostingError(f"Failed to get account usage: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error getting usage for {username}: {str(e)}")
            raise
    
    def create_email_account(self, domain: str, email: str, password: str, 
                           quota: int = 250) -> bool:
        """
        ایجاد حساب ایمیل
        
        Args:
            domain (str): نام دامنه
            email (str): آدرس ایمیل
            password (str): رمز عبور
            quota (int): سقف حجم ایمیل (MB)
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            data = {
                'api.version': 1,
                'domain': domain,
                'email': email,
                'password': password,
                'quota': quota
            }
            
            response = self._make_request('create_email_account', data)
            
            if response.get('metadata', {}).get('result') == 1:
                logger.info(f"Successfully created email account: {email}")
                return True
            else:
                error_msg = response.get('metadata', {}).get('reason', 'Unknown error')
                raise HostingError(f"Failed to create email account: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error creating email account {email}: {str(e)}")
            raise
    
    def create_database(self, username: str, db_name: str, db_user: str, 
                       db_password: str) -> bool:
        """
        ایجاد دیتابیس MySQL
        
        Args:
            username (str): نام کاربری cPanel
            db_name (str): نام دیتابیس
            db_user (str): کاربر دیتابیس
            db_password (str): رمز دیتابیس
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            # ایجاد دیتابیس
            data = {
                'api.version': 1,
                'name': db_name
            }
            response = self._make_request('create_database', data)
            
            if response.get('metadata', {}).get('result') == 1:
                # ایجاد کاربر دیتابیس
                user_data = {
                    'api.version': 1,
                    'name': db_user,
                    'password': db_password
                }
                user_response = self._make_request('create_database_user', user_data)
                
                if user_response.get('metadata', {}).get('result') == 1:
                    # اتصال کاربر به دیتابیس
                    privilege_data = {
                        'api.version': 1,
                        'user': db_user,
                        'database': db_name,
                        'privileges': 'ALL PRIVILEGES'
                    }
                    privilege_response = self._make_request('set_database_privileges', privilege_data)
                    
                    if privilege_response.get('metadata', {}).get('result') == 1:
                        logger.info(f"Successfully created database: {db_name}")
                        return True
            
            error_msg = response.get('metadata', {}).get('reason', 'Unknown error')
            raise HostingError(f"Failed to create database: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error creating database {db_name}: {str(e)}")
            raise
    
    def change_cpanel_password(self, username: str, new_password: str) -> bool:
        """
        تغییر رمز cPanel
        
        Args:
            username (str): نام کاربری
            new_password (str): رمز جدید
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            data = {
                'api.version': 1,
                'user': username,
                'password': new_password
            }
            
            response = self._make_request('passwd', data)
            
            if response.get('metadata', {}).get('result') == 1:
                logger.info(f"Successfully changed password for: {username}")
                return True
            else:
                error_msg = response.get('metadata', {}).get('reason', 'Unknown error')
                raise HostingError(f"Failed to change password: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error changing password for {username}: {str(e)}")
            raise
    
    def delete_account(self, username: str) -> bool:
        """
        حذف حساب cPanel
        
        Args:
            username (str): نام کاربری
            
        Returns:
            bool: True اگر عملیات موفق باشد
        """
        try:
            data = {
                'api.version': 1,
                'user': username
            }
            
            response = self._make_request('removeacct', data)
            
            if response.get('metadata', {}).get('result') == 1:
                logger.info(f"Successfully deleted cPanel account: {username}")
                return True
            else:
                error_msg = response.get('metadata', {}).get('reason', 'Unknown error')
                raise HostingError(f"Failed to delete cPanel account: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error deleting cPanel account {username}: {str(e)}")
            raise