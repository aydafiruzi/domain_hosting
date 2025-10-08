# pages.py - نسخه ساده شده فقط برای جستجوی دامنه
from flask import Blueprint, render_template, jsonify, request
import random
import re

pages = Blueprint('pages', __name__)

@pages.route('/')
def home():
    """صفحه اصلی با فرم جستجوی دامنه"""
    return render_template('index.html')

@pages.route('/about')
def about():
    """صفحه درباره ما"""
    return """
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>درباره ما</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card shadow">
                        <div class="card-body p-5">
                            <h1 class="text-center mb-4">درباره سرویس ما</h1>
                            <p class="lead">سرویس تخصصی ثبت و مدیریت دامنه</p>
                            <a href="/" class="btn btn-primary mt-3">بازگشت به صفحه اصلی</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

