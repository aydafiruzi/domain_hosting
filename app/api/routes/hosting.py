# app/api/routes/hosting.py
from flask import Blueprint, request, jsonify
import uuid

hosting_bp = Blueprint('hosting', __name__)

# 🆕 ایجاد حساب هاستینگ
@hosting_bp.route('/accounts', methods=['POST'])
def create_hosting_account():
    """
    مثال استفاده:
    POST /api/v1/hosting/accounts
    {
        "domain": "example.com",
        "package_id": "12345678-1234-1234-1234-123456789012",
        "customer_id": "12345678-1234-1234-1234-123456789012", 
        "username": "testuser",
        "password": "securepassword123"
    }
    """
    try:
        data = request.get_json()
        
        from app.core.hosting.manager import HostingManager
        hosting_manager = HostingManager()
        
        account = hosting_manager.create_hosting_account(
            domain=data['domain'],
            package_id=uuid.UUID(data['package_id']),
            customer_id=uuid.UUID(data['customer_id']),
            username=data['username'],
            password=data['password']
        )
        
        return jsonify({
            "success": True,
            "account": {
                "id": str(account.id),
                "domain": account.domain,
                "username": account.username,
                "status": account.status,
                "ip_address": account.ip_address
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

# 📊 دریافت اطلاعات استفاده
@hosting_bp.route('/accounts/<account_id>/usage', methods=['GET'])
def get_account_usage(account_id):
    """
    مثال استفاده:
    GET /api/v1/hosting/accounts/12345678-1234-1234-1234-123456789012/usage
    """
    try:
        from app.core.hosting.manager import HostingManager
        hosting_manager = HostingManager()
        
        usage = hosting_manager.get_account_usage(uuid.UUID(account_id))
        
        return jsonify({
            "success": True,
            "usage": usage
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

# ⏸️ تعلیق حساب
@hosting_bp.route('/accounts/<account_id>/suspend', methods=['POST'])
def suspend_account(account_id):
    """
    مثال استفاده:
    POST /api/v1/hosting/accounts/12345678-1234-1234-1234-123456789012/suspend
    {
        "reason": "Non-payment"
    }
    """
    try:
        data = request.get_json()
        reason = data.get('reason', 'Administrative')
        
        from app.core.hosting.manager import HostingManager
        hosting_manager = HostingManager()
        
        success = hosting_manager.suspend_account(uuid.UUID(account_id), reason)
        
        return jsonify({
            "success": success,
            "message": f"Account {account_id} suspended"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400