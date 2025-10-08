# app/core/domain/services.py
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from ..shared.models import ContactInfo, Domain, PriceInfo
from ..shared.exceptions import DomainError, ValidationError

logger = logging.getLogger(__name__)

class ContactType(Enum):
    REGISTRANT = "registrant"
    ADMIN = "admin"
    TECH = "tech"
    BILLING = "billing"

class PrivacyService:
    """سرویس مدیریت حریم خصوصی دامنه"""
    
    def __init__(self, api_client):
        self.api_client = api_client
        logger.info("Privacy Service initialized")

    def enable_privacy_protection(self, domain_name: str) -> bool:
        """فعال‌سازی حریم خصوصی برای دامنه"""
        try:
            logger.info(f"Enabling privacy protection for: {domain_name}")
            
            response = self.api_client.enable_whois_privacy(domain_name)
            
            logger.info(f"Privacy protection enabled for: {domain_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling privacy for {domain_name}: {str(e)}")
            raise DomainError(f"Failed to enable privacy protection: {str(e)}")

    def disable_privacy_protection(self, domain_name: str) -> bool:
        """غیرفعال‌سازی حریم خصوصی"""
        try:
            logger.info(f"Disabling privacy protection for: {domain_name}")
            
            response = self.api_client.disable_whois_privacy(domain_name)
            
            logger.info(f"Privacy protection disabled for: {domain_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error disabling privacy for {domain_name}: {str(e)}")
            raise DomainError(f"Failed to disable privacy protection: {str(e)}")

    def get_privacy_status(self, domain_name: str) -> Dict[str, Any]:
        """دریافت وضعیت حریم خصوصی دامنه"""
        try:
            response = self.api_client.get_whois_privacy_status(domain_name)
            
            return {
                'enabled': response.get('privacy_enabled', False),
                'expiry_date': response.get('privacy_expiry'),
                'service_type': response.get('privacy_service')
            }
            
        except Exception as e:
            logger.error(f"Error getting privacy status for {domain_name}: {str(e)}")
            raise DomainError(f"Failed to get privacy status: {str(e)}")

class ContactService:
    """سرویس مدیریت اطلاعات مخاطبین دامنه"""
    
    def __init__(self, api_client):
        self.api_client = api_client
        logger.info("Contact Service initialized")

    def get_contact_info(self, domain_name: str, contact_type: ContactType = ContactType.REGISTRANT) -> ContactInfo:
        """دریافت اطلاعات مخاطب دامنه"""
        try:
            logger.info(f"Getting {contact_type.value} contact info for: {domain_name}")
            
            response = self.api_client.get_contacts(domain_name, contact_type.value)
            
            contact_info = ContactInfo(
                first_name=response.get('first_name', ''),
                last_name=response.get('last_name', ''),
                email=response.get('email', ''),
                phone=response.get('phone', ''),
                address=response.get('address', ''),
                city=response.get('city', ''),
                country=response.get('country', ''),
                zip_code=response.get('zip_code', '')
            )
            
            return contact_info
            
        except Exception as e:
            logger.error(f"Error getting contact info for {domain_name}: {str(e)}")
            raise DomainError(f"Failed to get contact information: {str(e)}")

    def update_contact_info(self, domain_name: str, contact_type: ContactType, 
                          contact_data: ContactInfo) -> bool:
        """بروزرسانی اطلاعات مخاطب دامنه"""
        try:
            self._validate_contact_data(contact_data)
            
            logger.info(f"Updating {contact_type.value} contact for: {domain_name}")
            
            update_data = {
                'domain': domain_name,
                'contact_type': contact_type.value,
                'contact_info': contact_data.to_dict()
            }
            
            response = self.api_client.update_contacts(update_data)
            
            logger.info(f"Contact info updated for: {domain_name}")
            return True
            
        except ValidationError as e:
            # اگر ValidationError باشد، آن را مستقیماً پرتاب می‌کنیم
            raise e
        except Exception as e:
            logger.error(f"Error updating contact for {domain_name}: {str(e)}")
            raise DomainError(f"Failed to update contact information: {str(e)}")

    def validate_contact_info(self, contact_data: ContactInfo, tld: str) -> Dict[str, Any]:
        """
        اعتبارسنجی اطلاعات مخاطب برای TLD خاص
        
        Returns:
            Dict: نتایج اعتبارسنجی
        """
        validation_results = {
            'valid': True,
            'errors': []
        }
        
        # اعتبارسنجی عمومی
        if not contact_data.first_name or not contact_data.last_name:
            validation_results['valid'] = False
            validation_results['errors'].append("First and last name are required")
        
        if not self._validate_email(contact_data.email):
            validation_results['valid'] = False
            validation_results['errors'].append("Invalid email format")
            
        if not self._validate_phone(contact_data.phone, tld):
            validation_results['valid'] = False
            validation_results['errors'].append("Invalid phone number format")
        
        # اعتبارسنجی خاص TLD
        if tld == '.eu':
            eu_countries = ['EU', 'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 
                          'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 
                          'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 
                          'SK', 'SI', 'ES', 'SE']
            if contact_data.country not in eu_countries:
                validation_results['valid'] = False
                validation_results['errors'].append("EU domains require EU-based contact")
        
        elif tld == '.ca':
            if contact_data.country != 'CA':
                validation_results['valid'] = False
                validation_results['errors'].append(".ca domains require Canadian presence")
                
        return validation_results

    def _validate_contact_data(self, contact_data: ContactInfo) -> None:
        """اعتبارسنجی داخلی اطلاعات مخاطب"""
        if not contact_data.email:
            raise ValidationError("Email is required")
        if not contact_data.first_name or not contact_data.last_name:
            raise ValidationError("First and last name are required")

    def _validate_email(self, email: str) -> bool:
        """اعتبارسنجی ایمیل"""
        if not email:
            return False
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _validate_phone(self, phone: str, tld: str) -> bool:
        """اعتبارسنجی شماره تلفن"""
        if not phone:
            return False
        import re
        # الگوی پایه برای شماره تلفن بین‌المللی
        pattern = r'^\+\d{1,3}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,9}$'
        return bool(re.match(pattern, phone))

class BulkOperationsService:
    """سرویس عملیات گروهی روی دامنه‌ها"""
    
    def __init__(self, domain_manager):
        self.domain_manager = domain_manager
        logger.info("Bulk Operations Service initialized")

    def bulk_domain_renewal(self, domain_list: List[str], years: int) -> Dict[str, Any]:
        """تمدید گروهی دامنه‌ها"""
        results = {
            'successful': [],
            'failed': [],
            'total_processed': 0
        }
        
        for domain in domain_list:
            try:
                success = self.domain_manager.renew_domain(domain, years)
                if success:
                    results['successful'].append(domain)
                else:
                    results['failed'].append(domain)
                    
                results['total_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error renewing {domain}: {str(e)}")
                results['failed'].append(domain)
                results['total_processed'] += 1
        
        logger.info(f"Bulk renewal completed: {len(results['successful'])} successful, {len(results['failed'])} failed")
        return results

    def bulk_contact_update(self, domain_list: List[str], contact_type: ContactType,
                          contact_data: ContactInfo) -> Dict[str, Any]:
        """بروزرسانی گروهی اطلاعات مخاطب"""
        results = {
            'successful': [],
            'failed': [],
            'total_processed': 0
        }
        
        contact_service = ContactService(self.domain_manager.api_client)
        
        for domain in domain_list:
            try:
                success = contact_service.update_contact_info(domain, contact_type, contact_data)
                if success:
                    results['successful'].append(domain)
                else:
                    results['failed'].append(domain)
                    
                results['total_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error updating contact for {domain}: {str(e)}")
                results['failed'].append(domain)
                results['total_processed'] += 1
        
        return results

    def bulk_domain_lock(self, domain_list: List[str], lock: bool = True) -> Dict[str, Any]:
        """قفل/باز کردن گروهی دامنه‌ها"""
        results = {
            'successful': [],
            'failed': [],
            'total_processed': 0
        }
        
        for domain in domain_list:
            try:
                if lock:
                    success = self.domain_manager.lock_domain(domain)
                else:
                    success = self.domain_manager.unlock_domain(domain)
                    
                if success:
                    results['successful'].append(domain)
                else:
                    results['failed'].append(domain)
                    
                results['total_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error {'locking' if lock else 'unlocking'} {domain}: {str(e)}")
                results['failed'].append(domain)
                results['total_processed'] += 1
        
        action = "locked" if lock else "unlocked"
        logger.info(f"Bulk {action} completed: {len(results['successful'])} successful")
        return results

class DomainMonitoringService:
    """سرویس مانیتورینگ و نظارت بر دامنه‌ها"""
    
    def __init__(self, domain_manager):
        self.domain_manager = domain_manager
        logger.info("Domain Monitoring Service initialized")

    def check_expiring_domains(self, days_threshold: int = 30) -> List[Dict[str, Any]]:
        """بررسی دامنه‌های در حال انقضا"""
        expiring_domains = []
        
        try:
            all_domains = self._get_all_customer_domains()
            
            for domain in all_domains:
                days_until_expiry = (domain.expiry_date - datetime.now()).days
                
                if 0 < days_until_expiry <= days_threshold:
                    expiring_domains.append({
                        'domain_name': domain.name,
                        'expiry_date': domain.expiry_date,
                        'days_until_expiry': days_until_expiry,
                        'auto_renew': domain.auto_renew
                    })
            
            logger.info(f"Found {len(expiring_domains)} domains expiring within {days_threshold} days")
            
        except Exception as e:
            logger.error(f"Error checking expiring domains: {str(e)}")
            
        return expiring_domains

    def monitor_domain_changes(self, domain_name: str, 
                             check_interval: timedelta = timedelta(hours=24)) -> Dict[str, Any]:
        """مانیتورینگ تغییرات دامنه"""
        changes = {
            'domain': domain_name,
            'checked_at': datetime.now(),
            'changes_detected': False,
            'details': {}
        }
        
        try:
            current_details = self.domain_manager.get_domain_details(domain_name)
            
            changes['details'] = {
                'status': current_details.status.value,
                'locked': current_details.locked,
                'privacy_protection': current_details.privacy_protection,
                'nameservers': current_details.nameservers
            }
            
            logger.info(f"Domain monitoring completed for: {domain_name}")
            
        except Exception as e:
            logger.error(f"Error monitoring domain {domain_name}: {str(e)}")
            changes['error'] = str(e)
            
        return changes

    def _get_all_customer_domains(self) -> List[Domain]:
        """دریافت تمام دامنه‌های کاربر"""
        # این یک پیاده‌سازی نمونه است
        return []

class DomainValidationService:
    """سرویس اعتبارسنجی دامنه"""
    
    def __init__(self):
        logger.info("Domain Validation Service initialized")

    def validate_domain_syntax(self, domain_name: str) -> Dict[str, Any]:
        """اعتبارسنجی سینتکس نام دامنه"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # بررسی طول
        if len(domain_name) < 4:  # حداقل 4 کاراکتر (a.co)
            result['valid'] = False
            result['errors'].append("Domain name too short (minimum 4 characters)")
        elif len(domain_name) > 253:
            result['valid'] = False
            result['errors'].append("Domain name too long (maximum 253 characters)")
        
        # بررسی کاراکترهای مجاز
        import re
        if not re.match(r'^[a-zA-Z0-9.-]+$', domain_name):
            result['valid'] = False
            result['errors'].append("Domain name contains invalid characters")
        
        # بررسی اینکه با خط تیره شروع یا پایان نیابد
        if domain_name.startswith('-') or domain_name.endswith('-'):
            result['valid'] = False
            result['errors'].append("Domain name cannot start or end with hyphen")
        
        # بررسی نقطه‌های متوالی
        if '..' in domain_name:
            result['valid'] = False
            result['errors'].append("Domain name cannot contain consecutive dots")
        
        # بررسی حداقل دو بخش (نام و TLD)
        parts = domain_name.split('.')
        if len(parts) < 2:
            result['valid'] = False
            result['errors'].append("Domain name must have at least one dot")
        
        # بررسی طول هر بخش
        for part in parts:
            if len(part) < 1:
                result['valid'] = False
                result['errors'].append("Domain name parts cannot be empty")
            elif len(part) > 63:
                result['valid'] = False
                result['errors'].append("Domain name part too long (maximum 63 characters)")
            
        return result

    def validate_tld(self, tld: str) -> bool:
        """اعتبارسنجی TLD"""
        valid_tlds = [
            'com', 'net', 'org', 'ir', 'io', 'co', 'info', 'biz', 
            'me', 'tv', 'us', 'uk', 'de', 'fr', 'it', 'es', 'nl'
        ]
        
        return tld.lower() in valid_tlds

class DomainServiceFactory:
    """فکتوری برای ایجاد نمونه‌های سرویس"""
    
    @staticmethod
    def create_privacy_service(api_client) -> PrivacyService:
        return PrivacyService(api_client)
    
    @staticmethod
    def create_contact_service(api_client) -> ContactService:
        return ContactService(api_client)
    
    @staticmethod
    def create_bulk_operations_service(domain_manager) -> BulkOperationsService:
        return BulkOperationsService(domain_manager)
    
    @staticmethod
    def create_monitoring_service(domain_manager) -> DomainMonitoringService:
        return DomainMonitoringService(domain_manager)
    
    @staticmethod
    def create_validation_service() -> DomainValidationService:
        return DomainValidationService()