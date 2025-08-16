from flask import Blueprint, render_template, session
from services import ProductService

# Tạo blueprint cho các route chính
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Trang chủ"""
    products = ProductService.get_all_products()
    return render_template('layout/base.html', products=products)

@main_bp.route('/shop')
def shop():
    """Trang shop"""
    products = ProductService.get_all_products()
    return render_template('layout/products.html', products=products)

@main_bp.route('/about')
def about():
    """Trang giới thiệu"""
    return render_template('layout/about.html')

@main_bp.route('/contact')
def contact():
    """Trang liên hệ"""
    return render_template('layout/contact.html')

# Context processor để inject thông tin user vào tất cả templates
@main_bp.app_context_processor
def inject_user():
    """Inject thông tin user vào context"""
    return dict(
        current_user=session.get('full_name'),
        is_logged_in='user_id' in session,
        user_id=session.get('user_id')
    )