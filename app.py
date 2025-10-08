# app.py - نسخه کاملاً جدید و ساده
from flask import Flask
from pages import pages

def create_app():
    app = Flask(__name__)
    app.register_blueprint(pages)
    return app

if __name__ == '__main__':
    app = create_app()
    print("=" * 50)
    print("🚀 سرور فلاسک با موفقیت راه‌اندازی شد!")
    print("🌐 آدرس: http://127.0.0.1:5000")
    print("📄 صفحه اصلی: http://127.0.0.1:5000/")
    print("ℹ️ درباره ما: http://127.0.0.1:5000/about")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)