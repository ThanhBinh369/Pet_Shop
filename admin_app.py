from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, SanPham, DonHang, TaiKhoan, ChiTiet_DonHang, DiaChi, DangNhap, GioHang, GioHang_SanPham
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

# Phần xử lý cho quản lý đơn hàng
@admin_app.route('/api/admin/order-stats')
def admin_order_stats():
    """API lấy thống kê đơn hàng"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        total_orders = DonHang.query.count()
        pending_orders = DonHang.query.filter_by(Status='pending').count()
        shipped_orders = DonHang.query.filter_by(Status='shipped').count()
        delivered_orders = DonHang.query.filter_by(Status='delivered').count()
        canceled_orders = DonHang.query.filter_by(Status='canceled').count()

        return jsonify({
            'success': True,
            'stats': {
                'total': total_orders,
                'pending': pending_orders,
                'shipped': shipped_orders,
                'delivered': delivered_orders,
                'canceled': canceled_orders
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@admin_app.route('/api/admin/orders')
def admin_orders():
    """API lấy danh sách đơn hàng"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        # Lấy tham số lọc từ query string
        status_filter = request.args.get('status')
        date_filter = request.args.get('date')
        search_filter = request.args.get('search')

        # Query cơ bản với JOIN
        orders_query = db.session.query(DonHang, TaiKhoan).join(
            TaiKhoan, DonHang.MaTaiKhoan == TaiKhoan.MaTaiKhoan
        )

        # Áp dụng các bộ lọc
        if status_filter:
            orders_query = orders_query.filter(DonHang.Status == status_filter)

        if date_filter:
            orders_query = orders_query.filter(
                func.date(DonHang.NgayDat) == date_filter
            )

        if search_filter:
            orders_query = orders_query.filter(
                db.or_(
                    DonHang.MaDonHang.like(f'%{search_filter}%'),
                    TaiKhoan.Ho.like(f'%{search_filter}%'),
                    TaiKhoan.Ten.like(f'%{search_filter}%')
                )
            )

        # Sắp xếp theo ngày đặt giảm dần
        orders_query = orders_query.order_by(DonHang.NgayDat.desc())

        # Lấy kết quả
        orders_data = orders_query.all()

        result = []
        for order_data in orders_data:
            order, user = order_data

            # Tạo tên đầy đủ từ Ho và Ten
            customer_name = f"{user.Ho or ''} {user.Ten or ''}".strip()
            if not customer_name:
                customer_name = f"Khách hàng #{user.MaTaiKhoan}"

            result.append({
                'id': order.MaDonHang,
                'customer_name': customer_name,
                'date': order.NgayDat.isoformat() if order.NgayDat else '',
                'total': float(order.TongTien) if order.TongTien else 0,
                'status': order.Status or 'pending'
            })

        return jsonify({
            'success': True,
            'orders': result,
            'total': len(result)
        })

    except Exception as e:
        print(f"Error loading orders: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@admin_app.route('/api/admin/orders/<int:order_id>')
def admin_order_detail(order_id):
    """API lấy chi tiết đơn hàng"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        # Lấy đơn hàng với thông tin khách hàng và địa chỉ
        order_query = db.session.query(DonHang, TaiKhoan, DiaChi, DangNhap).join(
            TaiKhoan, DonHang.MaTaiKhoan == TaiKhoan.MaTaiKhoan
        ).join(
            DiaChi, DonHang.MaDiaChi == DiaChi.MaDiaChi
        ).outerjoin(
            DangNhap, TaiKhoan.MaTaiKhoan == DangNhap.MaTaiKhoan
        ).filter(DonHang.MaDonHang == order_id).first()

        if not order_query:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy đơn hàng'
            }), 404

        order, user, shipping_address, login_info = order_query

        # Lấy chi tiết sản phẩm trong đơn hàng
        order_items = db.session.query(ChiTiet_DonHang, SanPham).join(
            SanPham, ChiTiet_DonHang.MaSanPham == SanPham.MaSanPham
        ).filter(ChiTiet_DonHang.MaDonHang == order_id).all()

        items = []
        for item_data in order_items:
            item, product = item_data
            items.append({
                'product_name': product.TenSanPham,
                'quantity': item.SoLuong,
                'price': float(item.DonGia) if item.DonGia else 0
            })

        # Tạo tên đầy đủ
        customer_name = f"{user.Ho or ''} {user.Ten or ''}".strip()
        if not customer_name:
            customer_name = f"Khách hàng #{user.MaTaiKhoan}"

        result = {
            'id': order.MaDonHang,
            'date': order.NgayDat.isoformat() if order.NgayDat else '',
            'status': order.Status or 'pending',
            'total': float(order.TongTien) if order.TongTien else 0,
            'customer': {
                'name': customer_name,
                'email': login_info.DiaChiEmail if login_info else 'N/A',
                'phone': user.SoDienThoai or 'N/A'
            },
            'shipping': {
                'receiver_name': shipping_address.TenNguoiNhan or customer_name,
                'phone': shipping_address.SoDienThoai or user.SoDienThoai or 'N/A',
                'address': f"{shipping_address.DiaChi or ''}, {shipping_address.QuanHuyen or ''}, {shipping_address.TinhThanh or ''}".strip(
                    ', ')
            },
            'items': items
        }

        return jsonify({
            'success': True,
            'order': result
        })

    except Exception as e:
        print(f"Error loading order detail: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@admin_app.route('/api/admin/orders/<int:order_id>/status', methods=['PUT'])
def admin_update_order_status(order_id):
    """API cập nhật trạng thái đơn hàng"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        data = request.get_json()
        new_status = data.get('status')

        # Kiểm tra trạng thái hợp lệ
        valid_statuses = ['pending', 'shipped', 'delivered', 'canceled']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': 'Trạng thái không hợp lệ'
            }), 400

        # Tìm đơn hàng
        order = DonHang.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy đơn hàng'
            }), 404

        # Cập nhật trạng thái
        order.Status = new_status
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Đã cập nhật trạng thái đơn hàng #{order_id} thành {new_status}'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error updating order status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


# API thống kê khách hàng
@admin_app.route('/api/admin/customer-stats')
def admin_customer_stats():
    """API lấy thống kê khách hàng"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        # Tổng số khách hàng
        total_customers = TaiKhoan.query.count()

        # Khách hàng có đơn hàng (active)
        active_customers = db.session.query(TaiKhoan.MaTaiKhoan).join(
            DonHang, TaiKhoan.MaTaiKhoan == DonHang.MaTaiKhoan
        ).distinct().count()

        # Khách hàng mới trong tháng này (do không có NgayTao trong TaiKhoan, tạm tính = 0)
        new_customers_this_month = 0

        # Khách hàng VIP (có tổng chi tiêu > 10 triệu)
        vip_customers = db.session.query(TaiKhoan.MaTaiKhoan).join(
            DonHang, TaiKhoan.MaTaiKhoan == DonHang.MaTaiKhoan
        ).filter(
            DonHang.Status.in_(['delivered', 'shipped'])
        ).group_by(TaiKhoan.MaTaiKhoan).having(
            func.sum(DonHang.TongTien) > 10000000
        ).count()

        return jsonify({
            'success': True,
            'stats': {
                'total': total_customers,
                'active': active_customers,
                'new_this_month': new_customers_this_month,
                'vip': vip_customers
            }
        })

    except Exception as e:
        print(f"Error loading customer stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@admin_app.route('/api/admin/customers')
def admin_customers():
    """API lấy danh sách khách hàng"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        # Lấy tham số lọc từ query string
        status_filter = request.args.get('status')
        order_filter = request.args.get('order')
        search_filter = request.args.get('search')

        # Query cơ bản với LEFT JOIN để lấy thông tin email và thống kê đơn hàng
        from sqlalchemy import case

        customers_query = db.session.query(
            TaiKhoan,
            DangNhap.DiaChiEmail,
            func.count(DonHang.MaDonHang).label('total_orders'),
            func.sum(
                case(
                    (DonHang.Status.in_(['delivered', 'shipped']), DonHang.TongTien),
                    else_=0
                )
            ).label('total_spent')
        ).outerjoin(
            DangNhap, TaiKhoan.MaTaiKhoan == DangNhap.MaTaiKhoan
        ).outerjoin(
            DonHang, TaiKhoan.MaTaiKhoan == DonHang.MaTaiKhoan
        ).group_by(TaiKhoan.MaTaiKhoan, DangNhap.DiaChiEmail)

        # Áp dụng các bộ lọc
        if search_filter:
            customers_query = customers_query.filter(
                db.or_(
                    TaiKhoan.MaTaiKhoan.like(f'%{search_filter}%'),
                    TaiKhoan.Ho.like(f'%{search_filter}%'),
                    TaiKhoan.Ten.like(f'%{search_filter}%'),
                    DangNhap.DiaChiEmail.like(f'%{search_filter}%')
                )
            )

        # Sắp xếp theo mã tài khoản giảm dần
        customers_query = customers_query.order_by(TaiKhoan.MaTaiKhoan.desc())

        # Lấy kết quả
        customers_data = customers_query.all()

        result = []
        for customer_data in customers_data:
            customer, email, total_orders, total_spent = customer_data

            # Tạo tên đầy đủ
            full_name = f"{customer.Ho or ''} {customer.Ten or ''}".strip()
            if not full_name:
                full_name = f"Khách hàng #{customer.MaTaiKhoan}"

            # Xác định trạng thái
            status = 'active' if total_orders > 0 else 'inactive'

            # Áp dụng bộ lọc trạng thái
            if status_filter and status != status_filter:
                continue

            # Áp dụng bộ lọc đơn hàng
            if order_filter:
                if order_filter == 'has_orders' and total_orders == 0:
                    continue
                elif order_filter == 'no_orders' and total_orders > 0:
                    continue

            result.append({
                'id': customer.MaTaiKhoan,
                'full_name': full_name,
                'email': email,
                'phone': customer.SoDienThoai,
                'total_orders': total_orders or 0,
                'total_spent': float(total_spent) if total_spent else 0,
                'status': status
            })

        return jsonify({
            'success': True,
            'customers': result,
            'total': len(result)
        })

    except Exception as e:
        print(f"Error loading customers: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@admin_app.route('/api/admin/customers/<int:customer_id>')
def admin_customer_detail(customer_id):
    """API lấy chi tiết khách hàng"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        # Lấy thông tin khách hàng với email
        customer_query = db.session.query(TaiKhoan, DangNhap).outerjoin(
            DangNhap, TaiKhoan.MaTaiKhoan == DangNhap.MaTaiKhoan
        ).filter(TaiKhoan.MaTaiKhoan == customer_id).first()

        if not customer_query:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy khách hàng'
            }), 404

        customer, login_info = customer_query

        # Lấy thống kê đơn hàng
        from sqlalchemy import case

        orders_stats = db.session.query(
            func.count(DonHang.MaDonHang).label('total_orders'),
            func.sum(
                case(
                    (DonHang.Status.in_(['delivered', 'shipped']), DonHang.TongTien),
                    else_=0
                )
            ).label('total_spent'),
            func.max(DonHang.NgayDat).label('last_order_date')
        ).filter(DonHang.MaTaiKhoan == customer_id).first()

        # Lấy 5 đơn hàng gần nhất
        recent_orders = db.session.query(DonHang).filter(
            DonHang.MaTaiKhoan == customer_id
        ).order_by(DonHang.NgayDat.desc()).limit(5).all()

        # Tạo tên đầy đủ
        full_name = f"{customer.Ho or ''} {customer.Ten or ''}".strip()
        if not full_name:
            full_name = f"Khách hàng #{customer.MaTaiKhoan}"

        # Format ngày sinh
        birth_date = None
        if customer.NgaySinh:
            birth_date = customer.NgaySinh.strftime('%d/%m/%Y')

        # Xác định trạng thái
        total_orders = orders_stats[0] if orders_stats else 0
        status = 'active' if total_orders > 0 else 'inactive'

        # Format lịch sử đơn hàng
        orders_history = []
        for order in recent_orders:
            orders_history.append({
                'id': order.MaDonHang,
                'date': order.NgayDat.isoformat() if order.NgayDat else '',
                'total': float(order.TongTien) if order.TongTien else 0,
                'status': order.Status or 'pending'
            })

        result = {
            'id': customer.MaTaiKhoan,
            'full_name': full_name,
            'email': login_info.DiaChiEmail if login_info else None,
            'phone': customer.SoDienThoai,
            'birth_date': birth_date,
            'gender': customer.GioiTinh,
            'address': customer.DiaChi,
            'total_orders': total_orders or 0,
            'total_spent': float(orders_stats[1]) if orders_stats and orders_stats[1] else 0,
            'last_order_date': orders_stats[2].strftime('%d/%m/%Y') if orders_stats and orders_stats[2] else None,
            'status': status,
            'recent_orders': orders_history
        }

        return jsonify({
            'success': True,
            'customer': result
        })

    except Exception as e:
        print(f"Error loading customer detail: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@admin_app.route('/api/admin/customers/<int:customer_id>', methods=['DELETE'])
def admin_delete_customer(customer_id):
    """API xóa khách hàng"""
    if not require_admin_auth():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        # Tìm khách hàng
        customer = TaiKhoan.query.get(customer_id)
        if not customer:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy khách hàng'
            }), 404

        # Kiểm tra xem khách hàng có đơn hàng không
        order_count = DonHang.query.filter_by(MaTaiKhoan=customer_id).count()
        if order_count > 0:
            return jsonify({
                'success': False,
                'message': 'Không thể xóa khách hàng đã có đơn hàng. Vui lòng liên hệ quản trị viên để xử lý.'
            }), 400

        # Xóa các bản ghi liên quan trước
        # Xóa thông tin đăng nhập
        DangNhap.query.filter_by(MaTaiKhoan=customer_id).delete()

        # Xóa địa chỉ
        DiaChi.query.filter_by(MaTaiKhoan=customer_id).delete()

        # Xóa giỏ hàng và sản phẩm trong giỏ hàng
        gio_hangs = GioHang.query.filter_by(MaTaiKhoan=customer_id).all()
        for gio_hang in gio_hangs:
            GioHang_SanPham.query.filter_by(MaGioHang=gio_hang.MaGioHang).delete()
        GioHang.query.filter_by(MaTaiKhoan=customer_id).delete()

        # Cuối cùng xóa tài khoản
        db.session.delete(customer)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Đã xóa khách hàng #{customer_id} thành công'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting customer: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500



if __name__ == '__main__':
    admin_app.run(debug=True, host='0.0.0.0', port=443)
