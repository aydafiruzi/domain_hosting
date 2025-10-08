# app/core/shared/exceptions.py

class DomainError(Exception):
    """خطاهای مربوط به مدیریت دامنه"""
    pass

class ValidationError(Exception):
    """خطاهای اعتبارسنجی"""
    pass

class HostingError(Exception):
    """خطاهای مربوط به هاستینگ"""
    pass

class DNSError(Exception):
    """خطاهای مربوط به DNS"""
    pass

class DatabaseError(Exception):
    """خطاهای مربوط به دیتابیس"""
    pass

class APIError(Exception):
    """خطاهای مربوط به API خارجی"""
    pass