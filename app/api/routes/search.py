# app/api/routes/search.py
from flask import Blueprint, request, jsonify

search_bp = Blueprint('search', __name__)

# 🔎 جستجوی دامنه
@search_bp.route('/domains', methods=['POST'])
def search_domains():
    """
    مثال استفاده:
    POST /api/v1/search/domains
    {
        "keyword": "shop",
        "tlds": [".com", ".net", ".ir"],
        "count": 10
    }
    """
    try:
        data = request.get_json()
        
        from app.core.domain.manager import DomainManager
        domain_manager = DomainManager()
        
        suggestions = domain_manager.suggest_domain_names(
            keyword=data.get('keyword', ''),
            tlds=data.get('tlds', ['.com', '.net', '.org']),
            count=data.get('count', 10)
        )
        
        return jsonify({
            "success": True,
            "suggestions": suggestions,
            "count": len(suggestions)
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400