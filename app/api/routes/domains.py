# app/api/routes/domains.py
from flask import Blueprint, request, jsonify
from app.core.domain.manager import DomainManager
from app.core.shared.models import ContactInfo

domains_bp = Blueprint('domains', __name__)

# 🔍 بررسی موجودی دامنه
@domains_bp.route('/check-availability', methods=['POST'])
def check_domain_availability():
    """
    مثال استفاده:
    POST /api/v1/domains/check-availability
    {
        "domain_name": "example.com"
    }
    """
    try:
        data = request.get_json()
        domain_name = data.get('domain_name')
        
        # استفاده از DomainManager که از قبل دارید
        domain_manager = DomainManager()  # باید inject کنید
        available = domain_manager.check_domain_availability(domain_name)
        
        return jsonify({
            "domain": domain_name,
            "available": available,
            "success": True
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

# 📝 ثبت دامنه جدید
@domains_bp.route('/register', methods=['POST'])
def register_domain():
    """
    مثال استفاده:
    POST /api/v1/domains/register
    {
        "domain_name": "example.com",
        "years": 1,
        "contact_info": {
            "first_name": "John",
            "last_name": "Doe", 
            "email": "john@example.com",
            "phone": "+1.5551234567"
        }
    }
    """
    try:
        data = request.get_json()
        
        # ایجاد ContactInfo از داده‌های دریافتی
        contact_info = ContactInfo(
            first_name=data['contact_info']['first_name'],
            last_name=data['contact_info']['last_name'],
            email=data['contact_info']['email'],
            phone=data['contact_info'].get('phone', '')
        )
        
        domain_manager = DomainManager()
        domain = domain_manager.register_domain(
            domain_name=data['domain_name'],
            years=data['years'],
            contact_info=contact_info
        )
        
        return jsonify({
            "success": True,
            "domain": {
                "id": str(domain.id),
                "name": domain.name,
                "status": domain.status,
                "expiry_date": domain.expiry_date.isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

# 🔄 تمدید دامنه
@domains_bp.route('/<domain_name>/renew', methods=['POST'])
def renew_domain(domain_name):
    """
    مثال استفاده:
    POST /api/v1/domains/example.com/renew
    {
        "years": 1
    }
    """
    try:
        data = request.get_json()
        years = data.get('years', 1)
        
        domain_manager = DomainManager()
        success = domain_manager.renew_domain(domain_name, years)
        
        return jsonify({
            "success": success,
            "message": f"Domain {domain_name} renewed for {years} years"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

# 📋 دریافت اطلاعات دامنه
@domains_bp.route('/<domain_name>', methods=['GET'])
def get_domain_info(domain_name):
    """
    مثال استفاده:
    GET /api/v1/domains/example.com
    """
    try:
        domain_manager = DomainManager()
        domain = domain_manager.get_domain_details(domain_name)
        
        return jsonify({
            "success": True,
            "domain": {
                "name": domain.name,
                "status": domain.status,
                "expiry_date": domain.expiry_date.isoformat(),
                "locked": domain.locked,
                "privacy_protection": domain.privacy_protection
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404