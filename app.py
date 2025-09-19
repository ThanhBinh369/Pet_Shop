from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import cloudinary
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, TaiKhoan, DangNhap, DonHang, ChiTiet_DonHang, DiaChi, SanPham, GioHang, GioHang_SanPham
from sqlalchemy import desc
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
        selected_products = request.form.getlist('selected_products[]')
        selected_quantities = request.form.getlist('selected_quantities[]')

        if not address_id:
            flash('Vui lòng chọn địa chỉ giao hàng!', 'error')
            return redirect(url_for('checkout'))

        if not selected_products:
            flash('Vui lòng chọn ít nhất một sản phẩm!', 'error')
            return redirect(url_for('checkout'))

        # Lấy giỏ hàng hiện tại để kiểm tra
        all_cart_items = CartService.get_cart_items(session['user_id'])
        if not all_cart_items:
            flash('Giỏ hàng trống!', 'warning')
            return redirect(url_for('cart'))

        # Tạo danh sách sản phẩm được chọn với thông tin chi tiết
        selected_items = []
        total_amount = 0

        for i, product_id in enumerate(selected_products):
            quantity = int(selected_quantities[i])

            # Tìm sản phẩm trong giỏ hàng
            cart_item = next((item for item in all_cart_items if item['id'] == int(product_id)), None)

            if cart_item:
                selected_items.append({
                    'id': int(product_id),
                    'quantity': quantity,
                    'price': cart_item['price']
                })
                total_amount += cart_item['price'] * quantity

        if not selected_items:
            flash('Không tìm thấy sản phẩm được chọn!', 'error')
            return redirect(url_for('checkout'))

        # Tạo đơn hàng mới
        from models import DonHang, ChiTiet_DonHang, GioHang, GioHang_SanPham

        new_order = DonHang(
            MaTaiKhoan=session['user_id'],
            MaDiaChi=int(address_id),
            TongTien=total_amount,
            Status='pending'
        )

        db.session.add(new_order)
        db.session.flush()  # Để lấy MaDonHang

        # Thêm chi tiết đơn hàng cho các sản phẩm được chọn
        for item in selected_items:
            order_detail = ChiTiet_DonHang(
                MaDonHang=new_order.MaDonHang,
                MaSanPham=item['id'],
                SoLuong=item['quantity'],
                DonGia=item['price']
            )
            db.session.add(order_detail)

        # Chỉ xóa những sản phẩm được chọn khỏi giỏ hàng
        user_cart = GioHang.query.filter_by(MaTaiKhoan=session['user_id']).first()
        if user_cart:
            for item in selected_items:
                # Xóa sản phẩm được chọn khỏi giỏ hàng
                cart_product = GioHang_SanPham.query.filter_by(
                    MaGioHang=user_cart.MaGioHang,
                    MaSanPham=item['id']
                ).first()

                if cart_product:
                    if cart_product.SoLuong <= item['quantity']:
                        # Nếu số lượng đặt hàng >= số lượng trong giỏ, xóa hoàn toàn
                        db.session.delete(cart_product)
                    else:
                        # Nếu chỉ đặt một phần, giảm số lượng trong giỏ
                        cart_product.SoLuong -= item['quantity']

            # Cập nhật tổng số lượng trong giỏ hàng
            remaining_items = GioHang_SanPham.query.filter_by(MaGioHang=user_cart.MaGioHang).all()
            user_cart.TongSoLuong = sum(item.SoLuong for item in remaining_items)

        db.session.commit()

        flash(f'Đặt hàng thành công! Mã đơn hàng: {new_order.MaDonHang}', 'success')
        return redirect(url_for('order_success', order_id=new_order.MaDonHang))

    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi đặt hàng: {str(e)}', 'error')
        return redirect(url_for('checkout'))



@app.route('/order-success/<int:order_id>')
def order_success(order_id):
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập!', 'warning')
        return redirect(url_for('auth.login'))

    # Kiểm tra đơn hàng có tồn tại và thuộc về user không
    from models import DonHang
    order = DonHang.query.filter_by(
        MaDonHang=order_id,
        MaTaiKhoan=session['user_id']
    ).first()

    if not order:
        flash('Đơn hàng không tồn tại!', 'error')
        return redirect(url_for('index'))

    flash(f'Đặt hàng thành công! Mã đơn hàng: #{order_id}. Chúng tôi sẽ liên hệ với bạn sớm nhất.', 'success')
    return redirect(url_for('index'))  # hoặc redirect(url_for('my_orders'))


# Route quản lý đơn hàng
@app.route('/my-orders')
def my_orders():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập!', 'warning')
        return redirect(url_for('auth.login'))

    # Chuyển hướng về profile với tab orders
    return redirect(url_for('auth.profile') + '#orders')


# Route hủy đơn hàng
@app.route('/cancel-order', methods=['POST'])
def cancel_order():
    """Hủy đơn hàng"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'}), 401

    try:
        data = request.get_json()
        order_id = data.get('order_id')

        if not order_id:
            return jsonify({'success': False, 'message': 'Thiếu thông tin đơn hàng!'}), 400

        # Tìm đơn hàng
        order = DonHang.query.filter_by(
            MaDonHang=order_id,
            MaTaiKhoan=session['user_id']
        ).first()

        if not order:
            return jsonify({'success': False, 'message': 'Không tìm thấy đơn hàng!'}), 404

        # Kiểm tra trạng thái đơn hàng
        if order.Status != 'pending':
            return jsonify({
                'success': False,
                'message': 'Chỉ có thể hủy đơn hàng đang chờ xử lý!'
            }), 400

        # Cập nhật trạng thái đơn hàng thành 'canceled'
        order.Status = 'canceled'

        # Hoàn lại số lượng sản phẩm trong kho
        for chi_tiet in order.chi_tiets:
            san_pham = SanPham.query.get(chi_tiet.MaSanPham)
            if san_pham:
                san_pham.SoLuong += chi_tiet.SoLuong

        # Lưu thay đổi
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Hủy đơn hàng thành công!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        }), 500


# Lấy chi tiết đơn hàng
@app.route('/api/order-detail/<int:order_id>')
def api_order_detail(order_id):
    """API lấy chi tiết đơn hàng cho profile"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'}), 401

    try:
        # Tìm đơn hàng của user hiện tại
        order = DonHang.query.filter_by(
            MaDonHang=order_id,
            MaTaiKhoan=session['user_id']
        ).first()

        if not order:
            return jsonify({'success': False, 'message': 'Không tìm thấy đơn hàng!'}), 404

        return jsonify({
            'success': True,
            'order': {
                'id': order.MaDonHang,
                'date': order.NgayDat.strftime('%d/%m/%Y %H:%M'),
                'status': order.Status,
                'total': float(order.TongTien),
                'address': {
                    'recipient': order.dia_chi.TenNguoiNhan,
                    'phone': order.dia_chi.SoDienThoai,
                    'address': f"{order.dia_chi.DiaChi}, {order.dia_chi.QuanHuyen}, {order.dia_chi.TinhThanh}"
                },
                'items': [{
                    'name': item.san_pham.TenSanPham,
                    'quantity': item.SoLuong,
                    'price': float(item.DonGia),
                    'total': float(item.SoLuong * item.DonGia),
                    'image': item.san_pham.HinhAnh
                } for item in order.chi_tiets]
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        }), 500


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
