from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, SanPham, DonHang, TaiKhoan
import cloudinary.uploader
from services.services import AuthService, ProductService, OrderService
from datetime import datetime, timedelta
from sqlalchemy import func, extract

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

        # Tạo unique filename để tránh cache và conflict
        import uuid
        import time
        unique_filename = f"product_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # Upload lên Cloudinary với overwrite=True để tránh conflict
        result = cloudinary.uploader.upload(
            file,
            folder="pet_shop/products",
            public_id=unique_filename,
            resource_type="auto",
            transformation=[
                {'quality': 'auto:good'},
                {'format': 'auto'},
                {'width': 800, 'height': 600, 'crop': 'limit'}
            ],
            overwrite=True,  # Thay đổi từ False thành True
            invalidate=True  # Thêm dòng này để clear cache
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
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500


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
        products_query = db.session.query(SanPham, Loai).join(Loai, SanPham.MaLoai == Loai.MaLoai).filter(
            SanPham.TrangThai == 1).all()

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


@admin_app.route('/admin/dashboard')
def admin_dashboard():
    if not require_admin_auth():
        return redirect(url_for('admin_login'))

    # Có thể lấy stats cơ bản để hiển thị ban đầu
    try:
        stats = {
            'total_products': SanPham.query.filter_by(TrangThai=1).count(),
            'total_orders': DonHang.query.count(),
            'total_users': TaiKhoan.query.count()
        }
    except:
        stats = {'total_products': 0, 'total_orders': 0, 'total_users': 0}

    return render_template('dashboard.html', stats=stats)


@admin_app.route('/api/admin/sales-chart')
def admin_sales_chart():
    """API lấy dữ liệu biểu đồ doanh thu"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        from models import DonHang, ChiTiet_DonHang

        # Lấy tham số thời gian (mặc định 7 ngày)
        period = request.args.get('period', '7')

        # Tính toán khoảng thời gian
        if period == '7':
            # 7 ngày gần đây
            start_date = datetime.now() - timedelta(days=6)  # Bao gồm hôm nay
            labels = []
            for i in range(7):
                date = start_date + timedelta(days=i)
                labels.append(date.strftime('%d/%m'))
        elif period == '30':
            # 30 ngày gần đây, nhóm theo tuần (4 tuần)
            start_date = datetime.now() - timedelta(days=27)  # 4 tuần
            labels = ['Tuần 1', 'Tuần 2', 'Tuần 3', 'Tuần 4']
        else:  # 90 ngày
            # 3 tháng gần đây
            current_date = datetime.now()
            labels = []
            for i in range(3):
                month_date = current_date - timedelta(days=30 * (2 - i))  # Sửa thứ tự
                labels.append(f"Tháng {month_date.month}")

        # Truy vấn dữ liệu doanh thu
        if period == '7':
            # Doanh thu theo ngày trong 7 ngày
            sales_data = db.session.query(
                func.date(DonHang.NgayDat).label('date'),
                func.sum(DonHang.TongTien).label('total')
            ).filter(
                DonHang.NgayDat >= start_date,
                DonHang.Status.in_(['delivered', 'shipped'])  # Sử dụng shipped thay vì completed
            ).group_by(
                func.date(DonHang.NgayDat)
            ).all()


        elif period == '30':

            # Doanh thu theo tuần trong 30 ngày

            values = [0, 0, 0, 0]  # 4 tuần

            for week in range(4):
                week_start = start_date + timedelta(days=week * 7)

                week_end = week_start + timedelta(days=6)

                week_total = db.session.query(

                    func.sum(DonHang.TongTien)

                ).filter(

                    DonHang.NgayDat >= week_start,

                    DonHang.NgayDat <= week_end,

                    DonHang.Status.in_(['delivered', 'shipped'])

                ).scalar() or 0

                values[week] = float(week_total)


        else:  # 90 ngày

            # Doanh thu theo tháng trong 3 tháng

            values = []

            current_date = datetime.now()

            for i in range(3):

                # Tính 3 tháng: tháng hiện tại, tháng trước, 2 tháng trước

                months_back = 2 - i  # 2, 1, 0

                if months_back == 0:

                    # Tháng hiện tại

                    month_start = current_date.replace(day=1)

                    month_end = current_date

                else:

                    # Tháng trước hoặc 2 tháng trước

                    year = current_date.year

                    month = current_date.month - months_back

                    if month <= 0:
                        month += 12

                        year -= 1

                    month_start = datetime(year, month, 1)

                    # Tính ngày cuối tháng

                    if month == 12:

                        month_end = datetime(year + 1, 1, 1) - timedelta(days=1)

                    else:

                        month_end = datetime(year, month + 1, 1) - timedelta(days=1)

                month_total = db.session.query(

                    func.sum(DonHang.TongTien)

                ).filter(

                    DonHang.NgayDat >= month_start,

                    DonHang.NgayDat <= month_end,

                    DonHang.Status.in_(['delivered', 'shipped'])

                ).scalar() or 0

                values.append(float(month_total))

        # Xử lý dữ liệu cho period='7'

        if period == '7':

            # Xử lý dữ liệu cho 7 ngày

            sales_data = db.session.query(

                func.date(DonHang.NgayDat).label('date'),

                func.sum(DonHang.TongTien).label('total')

            ).filter(

                DonHang.NgayDat >= start_date,

                DonHang.Status.in_(['delivered', 'shipped'])

            ).group_by(

                func.date(DonHang.NgayDat)

            ).all()

            values = []

            sales_dict = {item[0].strftime('%Y-%m-%d'): float(item[1]) for item in sales_data}

            for i in range(7):
                date_key = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')

                values.append(sales_dict.get(date_key, 0))

        return jsonify({
            'success': True,
            'chartData': {
                'labels': labels,
                'values': values,
                'period': period
            }
        })

    except Exception as e:
        print(f"Error loading sales chart: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@admin_app.route('/api/admin/recent-orders')
def admin_recent_orders():
    """API lấy danh sách đơn hàng gần đây"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        from models import DonHang, TaiKhoan

        # Lấy 10 đơn hàng gần đây nhất
        recent_orders = db.session.query(DonHang, TaiKhoan).join(
            TaiKhoan, DonHang.MaTaiKhoan == TaiKhoan.MaTaiKhoan
        ).order_by(
            DonHang.NgayDat.desc()
        ).limit(10).all()

        result = []
        for order_data in recent_orders:
            order, user = order_data
            # Tạo tên đầy đủ từ Ho và Ten
            customer_name = f"{user.Ho or ''} {user.Ten or ''}".strip()
            if not customer_name:
                customer_name = f"Khách hàng #{user.MaTaiKhoan}"

            result.append({
                'id': order.MaDonHang,
                'customer_name': customer_name,
                'total': float(order.TongTien) if order.TongTien else 0,
                'date': order.NgayDat.strftime('%Y-%m-%d %H:%M:%S') if order.NgayDat else '',
                'status': order.Status or 'pending'
            })

        return jsonify({
            'success': True,
            'orders': result
        })

    except Exception as e:
        print(f"Error loading recent orders: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@admin_app.route('/api/admin/low-stock-products')
def admin_low_stock_products():
    """API lấy danh sách sản phẩm sắp hết hàng"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        from models import SanPham, Loai

        # Lấy các sản phẩm có số lượng <= 10
        low_stock_products = db.session.query(SanPham, Loai).join(
            Loai, SanPham.MaLoai == Loai.MaLoai
        ).filter(
            SanPham.TrangThai == 1,
            SanPham.SoLuong <= 10
        ).order_by(
            SanPham.SoLuong.asc()
        ).limit(15).all()

        result = []
        for product_data in low_stock_products:
            product, category = product_data
            result.append({
                'id': product.MaSanPham,
                'name': product.TenSanPham,
                'category': category.TenLoai,
                'quantity': product.SoLuong,
                'price': float(product.GiaBan) if product.GiaBan else 0
            })

        return jsonify({
            'success': True,
            'products': result
        })

    except Exception as e:
        print(f"Error loading low stock products: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@admin_app.route('/api/admin/quick-stats')
def admin_quick_stats():
    """API lấy thống kê nhanh cho dashboard"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        # Thống kê sản phẩm theo trạng thái kho
        in_stock = SanPham.query.filter(
            SanPham.TrangThai == 1,
            SanPham.SoLuong > 10
        ).count()

        low_stock = SanPham.query.filter(
            SanPham.TrangThai == 1,
            SanPham.SoLuong.between(1, 10)
        ).count()

        out_of_stock = SanPham.query.filter(
            SanPham.TrangThai == 1,
            SanPham.SoLuong == 0
        ).count()

        total_products = SanPham.query.filter_by(TrangThai=1).count()

        # Thống kê đơn hàng
        total_orders = DonHang.query.count()
        pending_orders = DonHang.query.filter_by(Status='pending').count()
        shipped_orders = DonHang.query.filter_by(Status='shipped').count()
        delivered_orders = DonHang.query.filter_by(Status='delivered').count()

        # Doanh thu hôm nay
        today = datetime.now().date()
        today_revenue = db.session.query(
            func.sum(DonHang.TongTien)
        ).filter(
            func.date(DonHang.NgayDat) == today,
            DonHang.Status.in_(['delivered', 'shipped'])
        ).scalar() or 0

        # Doanh thu tháng này
        current_month = datetime.now().replace(day=1)
        month_revenue = db.session.query(
            func.sum(DonHang.TongTien)
        ).filter(
            DonHang.NgayDat >= current_month,
            DonHang.Status.in_(['delivered', 'shipped'])
        ).scalar() or 0

        # Thống kê người dùng
        total_users = TaiKhoan.query.count()
        # Vì TaiKhoan không có NgayTao, chúng ta sẽ không thống kê user mới
        new_users_this_month = 0

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
                    'pending': pending_orders,
                    'shipped': shipped_orders,
                    'delivered': delivered_orders
                },
                'revenue': {
                    'today': float(today_revenue),
                    'month': float(month_revenue)
                },
                'users': {
                    'total': total_users,
                    'new_this_month': new_users_this_month
                }
            }
        })

    except Exception as e:
        print(f"Error loading quick stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@admin_app.route('/api/admin/dashboard-overview')
def admin_dashboard_overview():
    """API tổng hợp tất cả dữ liệu cho dashboard"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        # Gọi các API khác để lấy dữ liệu
        stats_response = admin_quick_stats()
        stats_data = stats_response.get_json() if stats_response.status_code == 200 else {'data': {}}

        chart_response = admin_sales_chart()
        chart_data = chart_response.get_json() if chart_response.status_code == 200 else {'chartData': {}}

        orders_response = admin_recent_orders()
        orders_data = orders_response.get_json() if orders_response.status_code == 200 else {'orders': []}

        products_response = admin_low_stock_products()
        products_data = products_response.get_json() if products_response.status_code == 200 else {'products': []}

        return jsonify({
            'success': True,
            'overview': {
                'statistics': stats_data.get('data', {}),
                'chart': chart_data.get('chartData', {}),
                'recent_orders': orders_data.get('orders', []),
                'low_stock_products': products_data.get('products', [])
            }
        })

    except Exception as e:
        print(f"Error loading dashboard overview: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


if __name__ == '__main__':
    admin_app.run(debug=True, host='0.0.0.0', port=443)
