# app/core/shared/repositories.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any, TypeVar, Type, Generic
from datetime import datetime, timedelta
import uuid
from .database import Base
from .models import (
    Customer, Domain, DNSRecord, Nameserver, DomainContact,
    HostingPackage, HostingAccount, Order, TLD, Price  # ✅ اضافه شد
)

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """ریپازیتوری پایه برای تمام مدل‌ها"""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: uuid.UUID) -> Optional[ModelType]:
        """دریافت یک رکورد بر اساس ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """دریافت تمام رکوردها با صفحه‌بندی"""
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """ایجاد رکورد جدید"""
        if 'id' not in obj_in:
            obj_in['id'] = uuid.uuid4()
        
        obj = self.model(**obj_in)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def update(self, id: uuid.UUID, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """بروزرسانی رکورد"""
        obj = self.get(id)
        if obj:
            for field, value in obj_in.items():
                if hasattr(obj, field):
                    setattr(obj, field, value)
            self.db.commit()
            self.db.refresh(obj)
        return obj
    
    def delete(self, id: uuid.UUID) -> bool:
        """حذف رکورد"""
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
    
    def count(self) -> int:
        """شمردن تعداد کل رکوردها"""
        return self.db.query(func.count(self.model.id)).scalar()

# 🆕 ریپازیتوری‌های جدید برای TLD و Price
class TLDRepository(BaseRepository[TLD]):
    """ریپازیتوری مدیریت TLDها"""
    
    def get_by_extension(self, extension: str) -> Optional[TLD]:
        """دریافت TLD بر اساس پسوند"""
        return self.db.query(TLD).filter(TLD.extension == extension).first()
    
    def get_enabled_tlds(self) -> List[TLD]:
        """دریافت TLDهای فعال"""
        return self.db.query(TLD).filter(TLD.enabled == True).all()
    
    def get_tld_extensions(self) -> List[str]:
        """دریافت لیست پسوندهای TLD"""
        return [tld.extension for tld in self.get_enabled_tlds()]

class PriceRepository(BaseRepository[Price]):
    """ریپازیتوری مدیریت قیمت‌ها"""
    
    def get_current_price(self, tld_extension: str, operation_type: str, years: int = 1) -> Optional[Price]:
        """دریافت قیمت فعلی برای TLD و عملیات مشخص"""
        now = datetime.now()
        return self.db.query(Price).filter(
            and_(
                Price.tld_extension == tld_extension,
                Price.operation_type == operation_type,
                Price.duration_years == years,
                Price.effective_from <= now,
                or_(
                    Price.effective_to.is_(None),
                    Price.effective_to >= now
                )
            )
        ).order_by(desc(Price.effective_from)).first()
    
    def get_prices_for_tld(self, tld_extension: str) -> List[Price]:
        """دریافت تمام قیمت‌های یک TLD"""
        now = datetime.now()
        return self.db.query(Price).filter(
            and_(
                Price.tld_extension == tld_extension,
                Price.effective_from <= now,
                or_(
                    Price.effective_to.is_(None),
                    Price.effective_to >= now
                )
            )
        ).all()

class CustomerRepository(BaseRepository[Customer]):
    """ریپازیتوری مدیریت مشتریان"""
    
    def get_by_email(self, email: str) -> Optional[Customer]:
        """دریافت مشتری بر اساس ایمیل"""
        return self.db.query(Customer).filter(Customer.email == email).first()
    
    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Customer]:
        """جستجوی مشتریان"""
        search_filter = or_(
            Customer.email.ilike(f"%{query}%"),
            Customer.first_name.ilike(f"%{query}%"),
            Customer.last_name.ilike(f"%{query}%"),
            Customer.company.ilike(f"%{query}%")
        )
        return self.db.query(Customer).filter(search_filter).offset(skip).limit(limit).all()
    
    def get_customer_stats(self, customer_id: uuid.UUID) -> Dict[str, Any]:
        """دریافت آمار مشتری"""
        domains_count = self.db.query(func.count(Domain.id)).filter(
            Domain.customer_id == customer_id
        ).scalar()
        
        hosting_count = self.db.query(func.count(HostingAccount.id)).filter(
            HostingAccount.customer_id == customer_id
        ).scalar()
        
        orders_count = self.db.query(func.count(Order.id)).filter(
            Order.customer_id == customer_id
        ).scalar()
        
        return {
            'domains_count': domains_count or 0,
            'hosting_count': hosting_count or 0,
            'orders_count': orders_count or 0
        }

class DomainRepository(BaseRepository[Domain]):
    """ریپازیتوری مدیریت دامنه‌ها"""
    
    def get_by_name(self, name: str) -> Optional[Domain]:
        """دریافت دامنه بر اساس نام"""
        return self.db.query(Domain).filter(Domain.name == name).first()
    
    def get_customer_domains(self, customer_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Domain]:
        """دریافت دامنه‌های یک مشتری"""
        return self.db.query(Domain).filter(
            Domain.customer_id == customer_id
        ).offset(skip).limit(limit).all()
    
    def get_expiring_domains(self, days: int = 30) -> List[Domain]:
        """دریافت دامنه‌های در حال انقضا"""
        threshold = datetime.now() + timedelta(days=days)
        return self.db.query(Domain).filter(
            and_(
                Domain.expiry_date <= threshold,
                Domain.expiry_date > datetime.now()
            )
        ).all()
    
    def get_expired_domains(self) -> List[Domain]:
        """دریافت دامنه‌های منقضی شده"""
        return self.db.query(Domain).filter(
            Domain.expiry_date <= datetime.now()
        ).all()
    
    def search(self, query: str, customer_id: Optional[uuid.UUID] = None, 
               skip: int = 0, limit: int = 100) -> List[Domain]:
        """جستجوی دامنه‌ها"""
        search_filter = Domain.name.ilike(f"%{query}%")
        
        if customer_id:
            search_filter = and_(search_filter, Domain.customer_id == customer_id)
        
        return self.db.query(Domain).filter(search_filter).offset(skip).limit(limit).all()
    
    def get_domain_with_details(self, domain_id: uuid.UUID) -> Optional[Domain]:
        """دریافت دامنه با تمام جزئیات"""
        return self.db.query(Domain).options(
            joinedload(Domain.customer),
            joinedload(Domain.dns_records),
            joinedload(Domain.nameservers),
            joinedload(Domain.contacts)
        ).filter(Domain.id == domain_id).first()
    
    def update_status(self, domain_id: uuid.UUID, status: str) -> bool:
        """بروزرسانی وضعیت دامنه"""
        domain = self.get(domain_id)
        if domain:
            domain.status = status
            self.db.commit()
            return True
        return False
    
    def get_domains_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Domain]:
        """دریافت دامنه‌ها بر اساس وضعیت"""
        return self.db.query(Domain).filter(
            Domain.status == status
        ).offset(skip).limit(limit).all()

class DNSRecordRepository(BaseRepository[DNSRecord]):
    """ریپازیتوری مدیریت رکوردهای DNS"""
    
    def get_domain_records(self, domain_id: uuid.UUID) -> List[DNSRecord]:
        """دریافت تمام رکوردهای یک دامنه"""
        return self.db.query(DNSRecord).filter(
            DNSRecord.domain_id == domain_id
        ).order_by(DNSRecord.type, DNSRecord.name).all()
    
    def get_records_by_type(self, domain_id: uuid.UUID, record_type: str) -> List[DNSRecord]:
        """دریافت رکوردها بر اساس نوع"""
        return self.db.query(DNSRecord).filter(
            and_(
                DNSRecord.domain_id == domain_id,
                DNSRecord.type == record_type
            )
        ).all()
    
    def delete_domain_records(self, domain_id: uuid.UUID) -> bool:
        """حذف تمام رکوردهای یک دامنه"""
        try:
            self.db.query(DNSRecord).filter(
                DNSRecord.domain_id == domain_id
            ).delete()
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
    
    def update_domain_records(self, domain_id: uuid.UUID, records: List[Dict[str, Any]]) -> bool:
        """بروزرسانی گروهی رکوردهای دامنه"""
        try:
            # حذف رکوردهای موجود
            self.delete_domain_records(domain_id)
            
            # افزودن رکوردهای جدید
            for record_data in records:
                record_data['domain_id'] = domain_id
                record_data['id'] = uuid.uuid4()
                self.create(record_data)
            
            return True
        except Exception as e:
            self.db.rollback()
            return False

class NameserverRepository(BaseRepository[Nameserver]):
    """ریپازیتوری مدیریت نامسرورها"""
    
    def get_domain_nameservers(self, domain_id: uuid.UUID) -> List[Nameserver]:
        """دریافت نامسرورهای یک دامنه"""
        return self.db.query(Nameserver).filter(
            Nameserver.domain_id == domain_id
        ).order_by(Nameserver.order).all()
    
    def update_domain_nameservers(self, domain_id: uuid.UUID, nameservers: List[str]) -> bool:
        """بروزرسانی نامسرورهای دامنه"""
        try:
            # حذف نامسرورهای موجود
            self.db.query(Nameserver).filter(
                Nameserver.domain_id == domain_id
            ).delete()
            
            # افزودن نامسرورهای جدید
            for i, hostname in enumerate(nameservers):
                nameserver_data = {
                    'id': uuid.uuid4(),
                    'domain_id': domain_id,
                    'hostname': hostname,
                    'order': i
                }
                self.create(nameserver_data)
            
            return True
        except Exception:
            self.db.rollback()
            return False

class DomainContactRepository(BaseRepository[DomainContact]):
    """ریپازیتوری مدیریت مخاطبین دامنه"""
    
    def get_domain_contacts(self, domain_id: uuid.UUID) -> List[DomainContact]:
        """دریافت مخاطبین یک دامنه"""
        return self.db.query(DomainContact).filter(
            DomainContact.domain_id == domain_id
        ).all()
    
    def get_contact_by_type(self, domain_id: uuid.UUID, contact_type: str) -> Optional[DomainContact]:
        """دریافت مخاطب بر اساس نوع"""
        return self.db.query(DomainContact).filter(
            and_(
                DomainContact.domain_id == domain_id,
                DomainContact.contact_type == contact_type
            )
        ).first()
    
    def update_domain_contacts(self, domain_id: uuid.UUID, contacts: List[Dict[str, Any]]) -> bool:
        """بروزرسانی مخاطبین دامنه"""
        try:
            # حذف مخاطبین موجود
            self.db.query(DomainContact).filter(
                DomainContact.domain_id == domain_id
            ).delete()
            
            # افزودن مخاطبین جدید
            for contact_data in contacts:
                contact_data['domain_id'] = domain_id
                contact_data['id'] = uuid.uuid4()
                self.create(contact_data)
            
            return True
        except Exception:
            self.db.rollback()
            return False

class HostingPackageRepository(BaseRepository[HostingPackage]):
    """ریپازیتوری مدیریت پکیج‌های هاستینگ"""
    
    def get_active_packages(self) -> List[HostingPackage]:
        """دریافت پکیج‌های فعال"""
        return self.db.query(HostingPackage).filter(
            HostingPackage.active == True
        ).order_by(HostingPackage.price).all()
    
    def get_by_plan_type(self, plan_type: str) -> List[HostingPackage]:
        """دریافت پکیج‌ها بر اساس نوع پلن"""
        return self.db.query(HostingPackage).filter(
            and_(
                HostingPackage.plan_type == plan_type,
                HostingPackage.active == True
            )
        ).all()

class HostingAccountRepository(BaseRepository[HostingAccount]):
    """ریپازیتوری مدیریت حساب‌های هاستینگ"""
    
    def get_by_domain(self, domain: str) -> Optional[HostingAccount]:
        """دریافت حساب هاستینگ بر اساس دامنه"""
        return self.db.query(HostingAccount).filter(
            HostingAccount.domain == domain
        ).first()
    
    def get_customer_accounts(self, customer_id: uuid.UUID) -> List[HostingAccount]:
        """دریافت حساب‌های هاستینگ یک مشتری"""
        return self.db.query(HostingAccount).filter(
            HostingAccount.customer_id == customer_id
        ).all()
    
    def get_suspended_accounts(self) -> List[HostingAccount]:
        """دریافت حساب‌های تعلیق شده"""
        return self.db.query(HostingAccount).filter(
            HostingAccount.status == 'suspended'
        ).all()
    
    def update_usage(self, account_id: uuid.UUID, disk_usage: int, bandwidth_usage: int) -> bool:
        """بروزرسانی میزان استفاده از منابع"""
        account = self.get(account_id)
        if account:
            account.disk_usage = disk_usage
            account.bandwidth_usage = bandwidth_usage
            self.db.commit()
            return True
        return False

class OrderRepository(BaseRepository[Order]):
    """ریپازیتوری مدیریت سفارشات"""
    
    def get_customer_orders(self, customer_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Order]:
        """دریافت سفارشات یک مشتری"""
        return self.db.query(Order).filter(
            Order.customer_id == customer_id
        ).order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
    
    def get_orders_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Order]:
        """دریافت سفارشات بر اساس وضعیت"""
        return self.db.query(Order).filter(
            Order.status == status
        ).order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
    
    def get_recent_orders(self, days: int = 7) -> List[Order]:
        """دریافت سفارشات اخیر"""
        since_date = datetime.now() - timedelta(days=days)
        return self.db.query(Order).filter(
            Order.created_at >= since_date
        ).order_by(desc(Order.created_at)).all()
    
    def update_payment_status(self, order_id: uuid.UUID, status: str, invoice_id: str = None) -> bool:
        """بروزرسانی وضعیت پرداخت"""
        order = self.get(order_id)
        if order:
            order.status = status
            if status == 'completed':
                order.paid_at = datetime.now()
            if invoice_id:
                order.invoice_id = invoice_id
            self.db.commit()
            return True
        return False

class StatsRepository:
    """ریپازیتوری برای آمار و گزارشات"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_system_stats(self) -> Dict[str, Any]:
        """دریافت آمار کلی سیستم"""
        total_customers = self.db.query(func.count(Customer.id)).scalar()
        total_domains = self.db.query(func.count(Domain.id)).scalar()
        total_hosting_accounts = self.db.query(func.count(HostingAccount.id)).scalar()
        total_orders = self.db.query(func.count(Order.id)).scalar()
        
        revenue = self.db.query(func.sum(Order.total_amount)).filter(
            Order.status == 'completed'
        ).scalar() or 0
        
        return {
            'total_customers': total_customers,
            'total_domains': total_domains,
            'total_hosting_accounts': total_hosting_accounts,
            'total_orders': total_orders,
            'total_revenue': float(revenue)
        }
    
    def get_domain_stats(self) -> Dict[str, Any]:
        """آمار دامنه‌ها"""
        domains_by_status = self.db.query(
            Domain.status, func.count(Domain.id)
        ).group_by(Domain.status).all()
        
        expiring_soon = self.db.query(func.count(Domain.id)).filter(
            and_(
                Domain.expiry_date <= datetime.now() + timedelta(days=30),
                Domain.expiry_date > datetime.now()
            )
        ).scalar()
        
        return {
            'by_status': dict(domains_by_status),
            'expiring_soon': expiring_soon
        }

# فکتوری برای ایجاد ریپازیتوری‌ها
class RepositoryFactory:
    """فکتوری برای ایجاد instance از ریپازیتوری‌ها"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @property
    def customers(self) -> CustomerRepository:
        return CustomerRepository(Customer, self.db)
    
    @property
    def domains(self) -> DomainRepository:
        return DomainRepository(Domain, self.db)
    
    @property
    def dns_records(self) -> DNSRecordRepository:
        return DNSRecordRepository(DNSRecord, self.db)
    
    @property
    def nameservers(self) -> NameserverRepository:
        return NameserverRepository(Nameserver, self.db)
    
    @property
    def domain_contacts(self) -> DomainContactRepository:
        return DomainContactRepository(DomainContact, self.db)
    
    @property
    def hosting_packages(self) -> HostingPackageRepository:
        return HostingPackageRepository(HostingPackage, self.db)
    
    @property
    def hosting_accounts(self) -> HostingAccountRepository:
        return HostingAccountRepository(HostingAccount, self.db)
    
    @property
    def orders(self) -> OrderRepository:
        return OrderRepository(Order, self.db)
    
    @property
    def tlds(self) -> TLDRepository:  # ✅ اضافه شد
        return TLDRepository(TLD, self.db)
    
    @property
    def prices(self) -> PriceRepository:  # ✅ اضافه شد
        return PriceRepository(Price, self.db)
    
    @property
    def stats(self) -> StatsRepository:
        return StatsRepository(self.db)

# utility function برای استفاده آسان
def get_repository_factory(db: Session) -> RepositoryFactory:
    """دریافت فکتوری ریپازیتوری"""
    return RepositoryFactory(db)