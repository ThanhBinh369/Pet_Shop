from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, TaiKhoan, DangNhap, SanPham, Loai
from services import AuthService, ProductService, CartService, OrderService
import os

# Khởi tạo Flask với thư mục templates và static tùy chỉnh
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Cấu hình ứng dụng
app.config.from_object(Config)

# Khởi tạo database
db.init_app(app)

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


# Route shop
@app.route('/shop')
def shop():
    products = ProductService.get_all_products()
    return render_template('layout/shop.html', products=products)


# Route about
@app.route('/about')
def about():
    return render_template('layout/about.html')


# Route contact
@app.route('/contact')
def contact():
    return render_template('layout/contact.html')


# Route đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        success, result = AuthService.login_user(username, password)

        if success:
            session['user_id'] = result.MaTaiKhoan
            session['username'] = username
            session['full_name'] = f"{result.Ho} {result.Ten}"
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('index'))
        else:
            flash(result, 'error')

    return render_template('login.html')


# Route đăng xuất
@app.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất!', 'info')
    return redirect(url_for('index'))


# Route đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        ho = request.form['ho']
        ten = request.form['ten']
        ngay_sinh = request.form['ngaySinh']
        gioi_tinh = request.form['gioiTinh']
        ma_can_cuoc = request.form['maCanCuoc']
        dia_chi = request.form['diaChi']
        so_dien_thoai = request.form['soDienThoai']
        ten_tai_khoan = request.form.get('tenTaiKhoan', '')  # Thêm field này vào form
        password = request.form['password']
        email = request.form.get('email', '')  # Thêm field này vào form

        # Kiểm tra dữ liệu
        if not all([ho, ten, ngay_sinh, gioi_tinh, ma_can_cuoc, dia_chi, so_dien_thoai, ten_tai_khoan, password]):
            flash('Vui lòng điền đầy đủ thông tin!', 'error')
            return render_template('register.html')

        # Đăng ký tài khoản
        success, result = AuthService.register_user(
            ho, ten, ngay_sinh, gioi_tinh, ma_can_cuoc,
            dia_chi, so_dien_thoai, ten_tai_khoan, password, email
        )

        if success:
            flash(f'Đăng ký thành công! Mã tài khoản của bạn là {result}.', 'success')
            return redirect(url_for('login'))
        else:
            flash(result, 'error')

    return render_template('register.html')


# Route xác thực mã
@app.route('/verify-code', methods=['POST'])
def verify_code():
    code = request.form['verificationCode']
    # Logic kiểm tra mã code (cần implement thêm)
    if code == "123456":  # Mã tạm thời
        return "Mã xác nhận đúng! Vui lòng đặt lại mật khẩu."
    else:
        return "Mã xác nhận không đúng. Vui lòng thử lại."


# Route giỏ hàng
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem giỏ hàng!', 'warning')
        return redirect(url_for('login'))

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
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500


# Route checkout
@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập!', 'warning')
        return redirect(url_for('login'))

    cart_items = CartService.get_cart_items(session['user_id'])
    if not cart_items:
        flash('Giỏ hàng trống!', 'warning')
        return redirect(url_for('cart'))

    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)


# Helper function để kiểm tra đăng nhập
@app.context_processor
def inject_user():
    return dict(
        current_user=session.get('full_name'),
        is_logged_in='user_id' in session
    )


if __name__ == '__main__':
    app.run(debug=True)