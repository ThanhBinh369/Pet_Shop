from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import cloudinary
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db
from services.services import AuthService, ProductService, OrderService

# Import admin controller
try:
    from controllers.admin_controller import admin_bp
    admin_imported = True
except ImportError:
    admin_imported = False
    print("Warning: Could not import admin_controller")

import os

# Khởi tạo Flask cho admin
admin_app = Flask(__name__,
                  template_folder='templates',
                  static_folder='static')

admin_app.config.from_object(Config)

# Khởi tạo database
db.init_app(admin_app)

cloudinary.config(
    cloud_name=admin_app.config['CLOUDINARY_CLOUD_NAME'],
    api_key=admin_app.config['CLOUDINARY_API_KEY'],
    api_secret=admin_app.config['CLOUDINARY_API_SECRET'],
    secure=True
)

# Bảo mật admin - chỉ định admin accounts
ADMIN_ACCOUNTS = {
    'admin': 'admin123',  # username: password
    'superadmin': 'super456'
}


def require_admin_auth():
    """Kiểm tra xác thực admin"""
    if 'admin_logged_in' not in session:
        return False

    if 'admin_username' not in session:
        return False

    return True


# Đăng ký admin blueprint nếu import thành công
if admin_imported:
    admin_app.register_blueprint(admin_bp)


# Route đăng nhập admin
@admin_app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Kiểm tra admin credentials
        if username in ADMIN_ACCOUNTS and ADMIN_ACCOUNTS[username] == password:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session.permanent = True

            flash('Đăng nhập admin thành công!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'error')

    return render_template('admin_login.html')


@admin_app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Đã đăng xuất khỏi admin!', 'success')
    return redirect(url_for('admin_login'))


# Route chính admin - redirect to dashboard
@admin_app.route('/')
@admin_app.route('/admin')
def admin_index():
    if not require_admin_auth():
        return redirect(url_for('admin_login'))
    return redirect(url_for('admin.dashboard'))

@admin_app.route('/api/admin/upload-image', methods=['POST'])
def admin_upload_image():
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in file.filename and
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'error': 'Invalid file type'}), 400

        # Upload lên Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder="pet_shop/products",
            resource_type="auto",
            transformation=[
                {'quality': 'auto:good'},
                {'format': 'auto'},
                {'width': 800, 'height': 600, 'crop': 'limit'}
            ]
        )

        return jsonify({
            'success': True,
            'data': {
                'url': result['secure_url'],
                'public_id': result['public_id']
            }
        })

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'error': 'Upload failed'}), 500

# Context processor cho admin
@admin_app.context_processor
def inject_admin_context():
    return dict(
        admin_username=session.get('admin_username'),
        is_admin_logged_in=require_admin_auth()
    )


# API để lấy dữ liệu sản phẩm cho admin (override từ admin_controller nếu cần)
@admin_app.route('/api/products')
def api_admin_products():
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        from models import SanPham, Loai

        # Lấy tất cả sản phẩm (kể cả ẩn) cho admin
        products_query = db.session.query(SanPham, Loai).join(Loai, SanPham.MaLoai == Loai.MaLoai).filter(SanPham.TrangThai == 1).all()

        result = []
        for product_data in products_query:
            product, loai = product_data

            # Xử lý hình ảnh
            main_image = None
            if hasattr(product, 'HinhAnh') and product.HinhAnh:
                if product.HinhAnh.startswith('http'):
                    main_image = product.HinhAnh
                else:
                    cloud_name = admin_app.config.get('CLOUDINARY_CLOUD_NAME')
                    if cloud_name:
                        main_image = f"https://res.cloudinary.com/{cloud_name}/image/upload/v1/pet_shop/products/{product.HinhAnh}"

            result.append({
                'id': product.MaSanPham,
                'name': product.TenSanPham,
                'type': loai.TenLoai,
                'brand': product.ThungHieu or '',
                'price': float(product.GiaBan) if product.GiaBan else 0,
                'quantity': product.SoLuong,
                'description': product.MoTa or '',
                'cost': float(product.ChiPhi) if product.ChiPhi else 0,
                'import_price': float(product.GiaNhap) if product.GiaNhap else 0,
                'status': 'active' if product.TrangThai == 1 else 'inactive',
                'created_date': product.NgayTao.strftime('%Y-%m-%d') if product.NgayTao else '',
                'updated_date': product.NgayCapNhat.strftime('%Y-%m-%d') if product.NgayCapNhat else '',
                'image': main_image  # THÊM MỚI
            })

        return jsonify({
            'success': True,
            'products': result,
            'total': len(result)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


# Override require_admin function từ admin_controller
def require_admin():
    """Helper function kiểm tra quyền admin cho admin_controller"""
    return require_admin_auth()


# Patch require_admin function trong admin_controller nếu đã import
if admin_imported:
    try:
        from controllers import admin_controller
        admin_controller.require_admin = require_admin
    except ImportError:
        print("Warning: Could not patch admin_controller")

# Tạo bảng nếu chưa tồn tại
with admin_app.app_context():
    try:
        db.create_all()
        print("Admin app - Database tables created successfully!")
    except Exception as e:
        print(f"Admin app - Error creating database tables: {e}")


# Route thống kê admin
@admin_app.route('/api/admin/statistics')
def admin_statistics():
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        from models.models import SanPham, DonHang, TaiKhoan

        # Thống kê sản phẩm theo trạng thái kho
        in_stock = SanPham.query.filter(SanPham.TrangThai == 1, SanPham.SoLuong > 10).count()
        low_stock = SanPham.query.filter(SanPham.TrangThai == 1, SanPham.SoLuong.between(1, 10)).count()
        out_of_stock = SanPham.query.filter(SanPham.TrangThai == 1, SanPham.SoLuong == 0).count()
        total_products = SanPham.query.filter_by(TrangThai=1).count()

        # Thống kê đơn hàng
        total_orders = DonHang.query.count()
        pending_orders = DonHang.query.filter_by(Status='pending').count()

        # Thống kê người dùng
        total_users = TaiKhoan.query.count()

        return jsonify({
            'success': True,
            'data': {
                'products': {
                    'total': total_products,
                    'in_stock': in_stock,
                    'low_stock': low_stock,
                    'out_of_stock': out_of_stock
                },
                'orders': {
                    'total': total_orders,
                    'pending': pending_orders
                },
                'users': {
                    'total': total_users
                }
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


# Error handlers cho admin
@admin_app.errorhandler(404)
def admin_not_found(error):
    return render_template('admin_error.html',
                           error_code=404,
                           error_message='Trang không tồn tại'), 404


@admin_app.errorhandler(403)
def admin_forbidden(error):
    return render_template('admin_error.html',
                           error_code=403,
                           error_message='Không có quyền truy cập'), 403


@admin_app.errorhandler(500)
def admin_internal_error(error):
    return render_template('admin_error.html',
                           error_code=500,
                           error_message='Lỗi server nội bộ'), 500


if __name__ == '__main__':
    admin_app.run(debug=True, host='0.0.0.0', port=443)