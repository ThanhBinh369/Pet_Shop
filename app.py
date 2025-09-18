from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import cloudinary
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db
from services import AuthService, ProductService, CartService, OrderService

# Import controllers
try:
    from controllers.auth_controller import auth_bp

    auth_imported = True
except ImportError:
    try:
        from auth_controller import auth_bp

        auth_imported = True
    except ImportError:
        auth_imported = False

try:
    from controllers.product_controller import product_bp

    product_imported = True
except ImportError:
    product_imported = False

try:
    from controllers.cart_controller import cart_bp

    cart_imported = True
except ImportError:
    cart_imported = False

try:
    from controllers.main_controller import main_bp

    main_imported = True
except ImportError:
    main_imported = False

import os

# Khởi tạo Flask với thư mục templates và static tùy chỉnh
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Cấu hình ứng dụng
app.config.from_object(Config)

# Khởi tạo database
db.init_app(app)

cloudinary.config(
    cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
    api_key=app.config['CLOUDINARY_API_KEY'],
    api_secret=app.config['CLOUDINARY_API_SECRET'],
    secure=True
)

# Đăng ký blueprints
if auth_imported:
    app.register_blueprint(auth_bp)

if product_imported:
    app.register_blueprint(product_bp)

if cart_imported:
    app.register_blueprint(cart_bp)

if main_imported:
    app.register_blueprint(main_bp)

# Tạo bảng nếu chưa tồn tại
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")


# Route trang chủ
@app.route('/')
def index():
    products = ProductService.get_all_products()
    return render_template('layout/base.html', products=products)


# Route shop - SỬA LẠI ĐỂ DÙNG ĐÚNG TEMPLATE
@app.route('/products')
def shop():
    # Lấy parameters từ query string
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'name')

    products = ProductService.get_all_products()

    # Filter theo category
    if category:
        products = [p for p in products if p['type'].lower() == category.lower()]

    # Filter theo search
    if search:
        search_lower = search.lower()
        products = [p for p in products if
                    search_lower in p['name'].lower() or
                    search_lower in p['brand'].lower() or
                    search_lower in p['description'].lower()]

    # Sorting
    if sort_by == 'price_low':
        products.sort(key=lambda x: x['price'])
    elif sort_by == 'price_high':
        products.sort(key=lambda x: x['price'], reverse=True)
    else:  # sort by name
        products.sort(key=lambda x: x['name'])

    return render_template('products.html',  # SỬA: Dùng products.html thay vì layout/products.html
                           products=products,
                           current_category=category,
                           current_search=search,
                           current_sort=sort_by)


# Route chi tiết sản phẩm
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Chi tiết sản phẩm"""
    product = ProductService.get_product_by_id(product_id)

    if not product:
        flash('Sản phẩm không tồn tại!', 'error')
        return redirect(url_for('shop'))

    # Lấy sản phẩm liên quan (cùng loại)
    all_products = ProductService.get_all_products()
    related_products = [p for p in all_products
                        if p['type'] == product['type'] and p['id'] != product_id][:4]

    return render_template('detail_product.html',
                           product=product,
                           related_products=related_products)


# Route about
@app.route('/about')
def about():
    return render_template('layout/about.html')


# Route contact
@app.route('/contact')
def contact():
    return render_template('layout/contact.html')


# Route giỏ hàng
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem giỏ hàng!', 'warning')
        return redirect(url_for('auth.login'))

    cart_items = CartService.get_cart_items(session['user_id'])
    total = sum(item['price'] * item['quantity'] for item in cart_items)

    return render_template('cart.html', cart_items=cart_items, total=total)


# Route thêm vào giỏ hàng
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'}), 401

    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        if not product_id:
            return jsonify({'success': False, 'message': 'Thiếu thông tin sản phẩm!'}), 400

        success, message = CartService.add_to_cart(session['user_id'], product_id, quantity)

        if success:
            # Lấy số lượng cart hiện tại để trả về
            cart_items = CartService.get_cart_items(session['user_id'])
            cart_count = sum(item['quantity'] for item in cart_items)

            return jsonify({
                'success': True,
                'message': message,
                'cart_count': cart_count
            })
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500


# Route checkout
@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập!', 'warning')
        return redirect(url_for('auth.login'))

    cart_items = CartService.get_cart_items(session['user_id'])
    if not cart_items:
        flash('Giỏ hàng trống!', 'warning')
        return redirect(url_for('cart'))

    # Lấy danh sách địa chỉ của user
    addresses = AuthService.get_user_addresses(session['user_id'])
    total = sum(item['price'] * item['quantity'] for item in cart_items)

    return render_template('checkout.html',
                           cart_items=cart_items,
                           total=total,
                           addresses=addresses)

# Route đặt hàng
@app.route('/place-order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập!', 'warning')
        return redirect(url_for('auth.login'))

    try:
        # Lấy thông tin từ form
        address_id = request.form.get('address_id')
        note = request.form.get('note', '')

        if not address_id:
            flash('Vui lòng chọn địa chỉ giao hàng!', 'error')
            return redirect(url_for('checkout'))

        # Tạo đơn hàng
        success, result = OrderService.create_order(session['user_id'], address_id)

        if success:
            flash(f'Đặt hàng thành công! Mã đơn hàng: {result}', 'success')
            return redirect(url_for('order_success', order_id=result))
        else:
            flash(result, 'error')
            return redirect(url_for('checkout'))

    except Exception as e:
        flash(f'Lỗi khi đặt hàng: {str(e)}', 'error')
        return redirect(url_for('checkout'))


# Route thành công
@app.route('/order-success/<int:order_id>')
def order_success(order_id):
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập!', 'warning')
        return redirect(url_for('auth.login'))

    return render_template('order_success.html', order_id=order_id)


# Route quản lý đơn hàng
@app.route('/my-orders')
def my_orders():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập!', 'warning')
        return redirect(url_for('auth.login'))

    # Lấy danh sách đơn hàng của user
    orders = OrderService.get_user_orders(session['user_id'])
    return render_template('my_orders.html', orders=orders)


# Route hủy đơn hàng
@app.route('/cancel-order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'}), 401

    try:
        success, message = OrderService.cancel_order(session['user_id'], order_id)

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

# Helper function để kiểm tra đăng nhập và thêm thông tin cart
@app.context_processor
def inject_user():
    cart_count = 0
    if 'user_id' in session:
        try:
            cart_items = CartService.get_cart_items(session['user_id'])
            cart_count = sum(item['quantity'] for item in cart_items)
        except:
            cart_count = 0

    return dict(
        current_user=session.get('full_name'),
        is_logged_in='user_id' in session,
        cart_count=cart_count
    )


if __name__ == '__main__':
    app.run(debug=True)
