# app/core/shared/models.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, Text, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import uuid
from .database import Base

# Enum ها برای PostgreSQL
class DomainStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired" 
    PENDING = "pending"
    SUSPENDED = "suspended"
    PENDING_TRANSFER = "pending_transfer"

class DNSRecordType(enum.Enum):
    A = "A"
    AAAA = "AAAA" 
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"
    NS = "NS"

class HostingStatus(enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CANCELLED = "cancelled"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed" 
    FAILED = "failed"
    REFUNDED = "refunded"

class ServiceType(enum.Enum):
    DOMAIN = "domain"
    HOSTING = "hosting"
    SSL = "ssl"

# ایجاد ENUM ها در PostgreSQL
domain_status_enum = ENUM(
    DomainStatus, 
    name="domainstatus",
    create_type=True
)

dns_record_type_enum = ENUM(
    DNSRecordType,
    name="dnsrecordtype", 
    create_type=True
)

hosting_status_enum = ENUM(
    HostingStatus,
    name="hostingstatus",
    create_type=True
)

payment_status_enum = ENUM(
    PaymentStatus,
    name="paymentstatus", 
    create_type=True
)

service_type_enum = ENUM(
    ServiceType,
    name="servicetype",
    create_type=True
)

# 🆕 کلاس‌های Pydantic برای استفاده در DomainManager
class ContactInfo:
    """کلاس برای نگهداری اطلاعات مخاطب"""
    def __init__(self, first_name: str = "", last_name: str = "", email: str = "", 
                 phone: str = "", address: str = "", city: str = "", 
                 country: str = "", zip_code: str = "", organization: str = ""):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.address = address
        self.city = city
        self.country = country
        self.zip_code = zip_code
        self.organization = organization
    
    def to_dict(self) -> dict:
        """تبدیل ContactInfo به دیکشنری"""
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'zip_code': self.zip_code,
            'organization': self.organization or ""
        }

class PriceInfo:
    """کلاس برای نگهداری اطلاعات قیمت"""
    def __init__(self, registration: float = 0.0, renewal: float = 0.0, 
                 transfer: float = 0.0, currency: str = "USD"):
        self.registration = registration
        self.renewal = renewal
        self.transfer = transfer
        self.currency = currency

# 🆕 مدل‌های جدید برای TLD و Price
class TLD(Base):
    __tablename__ = "tlds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    extension = Column(String(10), unique=True, nullable=False)  # مانند: .com, .ir
    name = Column(String(100), nullable=False)  # نام کامل: Commercial, Iran
    enabled = Column(Boolean, default=True)
    min_registration_years = Column(Integer, default=1)
    max_registration_years = Column(Integer, default=10)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

class Price(Base):
    __tablename__ = "prices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tld_extension = Column(String(10), nullable=False)
    operation_type = Column(String(20), nullable=False)  # registration, renewal, transfer
    duration_years = Column(Integer, default=1)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    effective_from = Column(DateTime(timezone=True), default=func.now())
    effective_to = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now())

# مدل‌های دیتابیس اصلی
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    company = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    status = Column(String(20), default="active")
    
    # روابط
    domains = relationship("Domain", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    hosting_accounts = relationship("HostingAccount", back_populates="customer", cascade="all, delete-orphan")

class Domain(Base):
    __tablename__ = "domains"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    status = Column(domain_status_enum, default=DomainStatus.PENDING)
    expiry_date = Column(DateTime(timezone=True), nullable=False)
    registration_date = Column(DateTime(timezone=True), default=func.now())
    locked = Column(Boolean, default=False)
    privacy_protection = Column(Boolean, default=False)
    auto_renew = Column(Boolean, default=True)
    auth_code = Column(String(100))
    registrar = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # کلید خارجی
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    
    # روابط
    customer = relationship("Customer", back_populates="domains")
    dns_records = relationship("DNSRecord", back_populates="domain", cascade="all, delete-orphan")
    nameservers = relationship("Nameserver", back_populates="domain", cascade="all, delete-orphan")
    contacts = relationship("DomainContact", back_populates="domain", cascade="all, delete-orphan")

class Nameserver(Base):
    __tablename__ = "nameservers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    hostname = Column(String(255), nullable=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # کلید خارجی
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"))
    
    # روابط
    domain = relationship("Domain", back_populates="nameservers")

class DNSRecord(Base):
    __tablename__ = "dns_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    type = Column(dns_record_type_enum, nullable=False)
    name = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    ttl = Column(Integer, default=3600)
    priority = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # کلید خارجی
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"))
    
    # روابط
    domain = relationship("Domain", back_populates="dns_records")

class DomainContact(Base):
    __tablename__ = "domain_contacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    contact_type = Column(String(20), nullable=False)  # registrant, admin, tech, billing
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    country = Column(String(2), nullable=False)
    zip_code = Column(String(20), nullable=False)
    organization = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # کلید خارجی
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"))
    
    # روابط
    domain = relationship("Domain", back_populates="contacts")

class HostingPackage(Base):
    __tablename__ = "hosting_packages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    disk_space = Column(Integer, nullable=False)  # MB
    bandwidth = Column(Integer, nullable=False)   # GB
    price = Column(Float, nullable=False)
    features = Column(JSON)
    plan_type = Column(String(20), nullable=False)
    max_domains = Column(Integer, default=1)
    max_databases = Column(Integer, default=1)
    max_email_accounts = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

class HostingAccount(Base):
    __tablename__ = "hosting_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    domain = Column(String(255), nullable=False)
    username = Column(String(50), nullable=False)
    status = Column(hosting_status_enum, default=HostingStatus.PENDING)
    ip_address = Column(String(45))
    disk_usage = Column(Integer, default=0)
    bandwidth_usage = Column(Integer, default=0)
    suspended_reason = Column(Text)
    created_date = Column(DateTime(timezone=True), default=func.now())
    expires_date = Column(DateTime(timezone=True))
    last_backup = Column(DateTime(timezone=True))
    
    # کلیدهای خارجی
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    package_id = Column(UUID(as_uuid=True), ForeignKey("hosting_packages.id", ondelete="SET NULL"))
    
    # روابط
    customer = relationship("Customer", back_populates="hosting_accounts")
    package = relationship("HostingPackage")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    service_type = Column(service_type_enum, nullable=False)
    items = Column(JSON, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(payment_status_enum, default=PaymentStatus.PENDING)
    years = Column(Integer, default=1)
    invoice_id = Column(String(100))
    domain_name = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=func.now())
    paid_at = Column(DateTime(timezone=True))
    
    # کلید خارجی
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    
    # روابط
    customer = relationship("Customer", back_populates="orders")