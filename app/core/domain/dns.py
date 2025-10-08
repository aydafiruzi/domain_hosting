# app/core/domain/dns.py
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from ..shared.models import DNSRecord
from ..shared.exceptions import DNSError, ValidationError

logger = logging.getLogger(__name__)

class DNSRecordType(Enum):
    """انواع رکوردهای DNS"""
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"
    NS = "NS"
    SRV = "SRV"
    CAA = "CAA"
    PTR = "PTR"
    SOA = "SOA"

class DNSManager:
    """
    مدیریت کامل رکوردهای DNS برای دامنه‌ها
    """
    
    def __init__(self, api_client, db_session=None):
        self.api_client = api_client
        self.db_session = db_session  # ✅ اضافه شد برای transaction
        logger.info("DNS Manager initialized")

    # 🔍 بخش دریافت رکوردها
    def get_dns_records(self, domain_name: str) -> List[DNSRecord]:
        """
        دریافت تمام رکوردهای DNS دامنه
        """
        try:
            logger.info(f"Fetching DNS records for domain: {domain_name}")
            
            response = self.api_client.get_dns_records(domain_name)
            
            records = []
            for record_data in response.get('records', []):
                record = DNSRecord(
                    id=record_data.get('id'),
                    type=record_data.get('type'),
                    name=record_data.get('name'),
                    value=record_data.get('value'),
                    ttl=record_data.get('ttl', 3600),
                    priority=record_data.get('priority')
                )
                records.append(record)
            
            logger.info(f"Retrieved {len(records)} DNS records for {domain_name}")
            return records
            
        except Exception as e:
            logger.error(f"Error fetching DNS records for {domain_name}: {str(e)}")
            raise DNSError(f"Failed to get DNS records: {str(e)}")

    # ✏️ بخش مدیریت رکوردها - بهبود bulk operations
    def update_dns_records(self, domain_name: str, records: List[DNSRecord]) -> bool:
        """
        بروزرسانی گروهی رکوردهای DNS با transaction ایمن
        """
        try:
            logger.info(f"Bulk updating DNS records for {domain_name}")
            
            # اگر session دیتابیس موجود باشد، از transaction استفاده می‌کنیم
            if self.db_session:
                return self._update_records_with_transaction(domain_name, records)
            else:
                return self._update_records_without_transaction(domain_name, records)
            
        except Exception as e:
            logger.error(f"Error bulk updating DNS records for {domain_name}: {str(e)}")
            raise DNSError(f"Failed to update DNS records: {str(e)}")

    def _update_records_with_transaction(self, domain_name: str, records: List[DNSRecord]) -> bool:
        """بروزرسانی با transaction ایمن"""
        try:
            # شروع transaction
            with self.db_session.begin():
                # دریافت رکوردهای فعلی
                current_records = self.get_dns_records(domain_name)
                
                # حذف رکوردهای موجود
                for record in current_records:
                    self.delete_dns_record(domain_name, record.id)
                
                # افزودن رکوردهای جدید
                for record in records:
                    self.add_dns_record(
                        domain_name=domain_name,
                        record_type=DNSRecordType(record.type),
                        name=record.name,
                        value=record.value,
                        ttl=record.ttl,
                        priority=record.priority
                    )
            
            logger.info(f"Successfully updated {len(records)} DNS records for {domain_name}")
            return True
            
        except Exception as e:
            logger.error(f"Transaction failed for DNS update {domain_name}: {str(e)}")
            raise

    def _update_records_without_transaction(self, domain_name: str, records: List[DNSRecord]) -> bool:
        """بروزرسانی بدون transaction (برای backward compatibility)"""
        try:
            # ایجاد backup از رکوردهای فعلی
            backup_records = self.get_dns_records(domain_name)
            
            try:
                # حذف رکوردهای موجود
                current_records = self.get_dns_records(domain_name)
                for record in current_records:
                    self.delete_dns_record(domain_name, record.id)
                
                # افزودن رکوردهای جدید
                for record in records:
                    self.add_dns_record(
                        domain_name=domain_name,
                        record_type=DNSRecordType(record.type),
                        name=record.name,
                        value=record.value,
                        ttl=record.ttl,
                        priority=record.priority
                    )
                
                logger.info(f"Successfully updated {len(records)} DNS records for {domain_name}")
                return True
                
            except Exception as e:
                # در صورت خطا، بازگردانی از backup
                logger.error(f"Update failed, restoring backup for {domain_name}")
                self._restore_from_backup(domain_name, backup_records)
                raise
                
        except Exception as e:
            logger.error(f"Failed to update DNS records for {domain_name}: {str(e)}")
            return False

    def _restore_from_backup(self, domain_name: str, backup_records: List[DNSRecord]):
        """بازگردانی رکوردها از backup"""
        try:
            # حذف رکوردهای فعلی
            current_records = self.get_dns_records(domain_name)
            for record in current_records:
                self.delete_dns_record(domain_name, record.id)
            
            # بازگردانی رکوردهای backup
            for record in backup_records:
                self.add_dns_record(
                    domain_name=domain_name,
                    record_type=DNSRecordType(record.type),
                    name=record.name,
                    value=record.value,
                    ttl=record.ttl,
                    priority=record.priority
                )
            
            logger.info(f"Successfully restored {len(backup_records)} DNS records for {domain_name}")
            
        except Exception as restore_error:
            logger.error(f"Failed to restore DNS backup for {domain_name}: {str(restore_error)}")
            raise DNSError(f"Critical: DNS restoration failed for {domain_name}")

    # 🛡️ متدهای اعتبارسنجی - بهبود اعتبارسنجی IPv6
    def _validate_ipv6_address(self, ip_address: str) -> None:
        """اعتبارسنجی آدرس IPv6 با پشتیبانی کامل"""
        import re
        import ipaddress
        
        try:
            # استفاده از کتابخانه استاندارد برای اعتبارسنجی دقیق
            ipaddress.IPv6Address(ip_address)
        except ipaddress.AddressValueError:
            # همچنین الگوی regex برای فرمت‌های مختلف
            ipv6_patterns = [
                r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$',  # کامل
                r'^::([0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}$',  # compressed
                r'^([0-9a-fA-F]{1,4}:){1,7}:$',  # compressed
                r'^([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}$',  # mixed
            ]
            
            if not any(re.match(pattern, ip_address) for pattern in ipv6_patterns):
                raise ValidationError(f"Invalid IPv6 address: {ip_address}")

    def _validate_dns_record_input(self, record_type: DNSRecordType, name: str, 
                                 value: str, ttl: int, priority: Optional[int]) -> None:
        """اعتبارسنجی پیشرفته ورودی‌های رکورد DNS"""
        
        if not name or not value:
            raise ValidationError("Name and value are required for DNS record")
        
        if ttl < 60 or ttl > 86400:
            raise ValidationError("TTL must be between 60 and 86400 seconds")
        
        # اعتبارسنجی name
        if not self._validate_dns_name(name):
            raise ValidationError(f"Invalid DNS name: {name}")
        
        if record_type == DNSRecordType.MX and priority is None:
            raise ValidationError("Priority is required for MX records")
        
        if record_type == DNSRecordType.MX and priority is not None:
            if priority < 0 or priority > 65535:
                raise ValidationError("Priority must be between 0 and 65535")
        
        # اعتبارسنجی خاص بر اساس نوع رکورد
        validation_methods = {
            DNSRecordType.A: lambda v: self._validate_ipv4_address(v),
            DNSRecordType.AAAA: lambda v: self._validate_ipv6_address(v),
            DNSRecordType.CNAME: lambda v: self._validate_dns_name(v) or v.endswith('.'),
            DNSRecordType.MX: lambda v: self._validate_dns_name(v),
            DNSRecordType.NS: lambda v: self._validate_dns_name(v),
            DNSRecordType.TXT: lambda v: len(v) <= 255  # محدودیت طول TXT
        }
        
        if record_type in validation_methods:
            try:
                validation_methods[record_type](value)
            except ValidationError:
                raise
            except Exception as e:
                raise ValidationError(f"Invalid value for {record_type.value} record: {str(e)}")

    def _validate_dns_name(self, name: str) -> bool:
        """اعتبارسنجی نام DNS"""
        import re
        # الگوی برای نام‌های DNS (شامل wildcard و root)
        pattern = r'^(\*\.)?([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.?$'
        return bool(re.match(pattern, name))

    # سایر متدها بدون تغییر باقی می‌مانند...
    # [بقیه متدها مانند قبل]