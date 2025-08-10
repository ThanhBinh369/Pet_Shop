from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from services import ProductService, AuthService, OrderService
from models import db, SanPham, Loai, TaiKhoan, DonHang

# Tạo blueprint cho admin
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def require_admin():
    """Helper function kiểm tra quyền admin"""
    if 'user_id' not in session:
        return False
    # TODO: Kiểm tra quyền admin từ database
    # Hiện tại cho phép tất cả user đã đăng nhập
    return True


@admin_bp.route('/')
def dashboard():
    """Trang dashboard admin"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('auth.login'))

    try:
        # Thống kê tổng quan
        total_products = SanPham.query.filter_by(TrangThai=1).count()
        total_users = TaiKhoan.query.count()
        total_orders = DonHang.query.count()

        # Đơn hàng gần đây
        recent_orders = DonHang.query.order_by(DonHang.NgayDat.desc()).limit(5).all()

        stats = {
            'total_products': total_products,
            'total_users': total_users,
            'total_orders': total_orders
        }

        return render_template('admin/dashboard.html',
                               stats=stats,
                               recent_orders=recent_orders)
    except Exception as e:
        flash(f'Lỗi khi tải dashboard: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@admin_bp.route('/products')
def manage_products():
    """Quản lý sản phẩm"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('auth.login'))

    try:
        products = ProductService.get_all_products()
        categories = Loai.query.all()

        return render_template('admin/products.html',
                               products=products,
                               categories=categories)
    except Exception as e:
        flash(f'Lỗi khi tải danh sách sản phẩm: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/products/add', methods=['GET', 'POST'])
def add_product():
    """Thêm sản phẩm mới"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            ten_san_pham = request.form.get('tenSanPham', '').strip()
            chi_phi = request.form.get('chiPhi', '0')
            gia_nhap = request.form.get('giaNhap', '0')
            gia_ban = request.form.get('giaBan', '0')
            so_luong = request.form.get('soLuong', '0')
            thuong_hieu = request.form.get('thuongHieu', '').strip()
            mo_ta = request.form.get('moTa', '').strip()
            ma_loai = request.form.get('maLoai')

            # Validate
            if not all([ten_san_pham, gia_ban, so_luong, ma_loai]):
                flash('Vui lòng điền đầy đủ thông tin bắt buộc!', 'error')
                return render_template('admin/add_product.html')

            # Tạo sản phẩm mới
            san_pham = SanPham(
                TenSanPham=ten_san_pham,
                ChiPhi=float(chi_phi) if chi_phi else None,
                GiaNhap=float(gia_nhap) if gia_nhap else None,
                GiaBan=float(gia_ban),
                SoLuong=int(so_luong),
                ThungHieu=thuong_hieu,
                MoTa=mo_ta,
                MaLoai=int(ma_loai)
            )

            db.session.add(san_pham)
            db.session.commit()

            flash('Thêm sản phẩm thành công!', 'success')
            return redirect(url_for('admin.manage_products'))

        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi thêm sản phẩm: {str(e)}', 'error')

    try:
        categories = Loai.query.all()
        return render_template('admin/add_product.html', categories=categories)
    except Exception as e:
        flash(f'Lỗi: {str(e)}', 'error')
        return redirect(url_for('admin.manage_products'))


@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    """Sửa sản phẩm"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('auth.login'))

    try:
        product = SanPham.query.get_or_404(product_id)

        if request.method == 'POST':
            # Cập nhật thông tin
            product.TenSanPham = request.form.get('tenSanPham', '').strip()
            product.ChiPhi = float(request.form.get('chiPhi', '0')) if request.form.get('chiPhi') else None
            product.GiaNhap = float(request.form.get('giaNhap', '0')) if request.form.get('giaNhap') else None
            product.GiaBan = float(request.form.get('giaBan', '0'))
            product.SoLuong = int(request.form.get('soLuong', '0'))
            product.ThungHieu = request.form.get('thuongHieu', '').strip()
            product.MoTa = request.form.get('moTa', '').strip()
            product.MaLoai = int(request.form.get('maLoai'))

            db.session.commit()
            flash('Cập nhật sản phẩm thành công!', 'success')
            return redirect(url_for('admin.manage_products'))

        categories = Loai.query.all()
        return render_template('admin/edit_product.html', product=product, categories=categories)

    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi: {str(e)}', 'error')
        return redirect(url_for('admin.manage_products'))


@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    """Xóa sản phẩm (soft delete)"""
    if not require_admin():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        product = SanPham.query.get_or_404(product_id)
        product.TrangThai = 0  # Soft delete
        db.session.commit()

        return jsonify({'success': True, 'message': 'Xóa sản phẩm thành công!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500


@admin_bp.route('/orders')
def manage_orders():
    """Quản lý đơn hàng"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('auth.login'))

    try:
        # Lấy parameters
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = 20

        # Query đơn hàng
        query = DonHang.query

        if status:
            query = query.filter(DonHang.Status == status)

        orders = query.order_by(DonHang.NgayDat.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return render_template('admin/orders.html',
                               orders=orders,
                               current_status=status)

    except Exception as e:
        flash(f'Lỗi khi tải danh sách đơn hàng: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/orders/<int:order_id>')
def order_detail(order_id):
    """Chi tiết đơn hàng"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('auth.login'))

    try:
        order = DonHang.query.get_or_404(order_id)
        return render_template('admin/order_detail.html', order=order)

    except Exception as e:
        flash(f'Lỗi: {str(e)}', 'error')
        return redirect(url_for('admin.manage_orders'))


@admin_bp.route('/orders/update-status', methods=['POST'])
def update_order_status():
    """Cập nhật trạng thái đơn hàng"""
    if not require_admin():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        data = request.get_json()
        order_id = data.get('order_id')
        new_status = data.get('status')

        if not order_id or not new_status:
            return jsonify({'success': False, 'message': 'Thiếu thông tin!'}), 400

        order = DonHang.query.get_or_404(order_id)
        order.Status = new_status
        db.session.commit()

        return jsonify({'success': True, 'message': 'Cập nhật trạng thái thành công!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500


@admin_bp.route('/users')
def manage_users():
    """Quản lý người dùng"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('auth.login'))

    try:
        page = int(request.args.get('page', 1))
        per_page = 20

        users = TaiKhoan.query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return render_template('admin/users.html', users=users)

    except Exception as e:
        flash(f'Lỗi khi tải danh sách người dùng: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/categories')
def manage_categories():
    """Quản lý danh mục"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('auth.login'))

    try:
        categories = Loai.query.all()
        return render_template('admin/categories.html', categories=categories)

    except Exception as e:
        flash(f'Lỗi khi tải danh mục: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/categories/add', methods=['POST'])
def add_category():
    """Thêm danh mục mới"""
    if not require_admin():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        data = request.get_json()
        ten_loai = data.get('tenLoai', '').strip()
        mo_ta = data.get('moTa', '').strip()

        if not ten_loai:
            return jsonify({'success': False, 'message': 'Tên loại không được trống!'}), 400

        # Kiểm tra trùng tên
        existing = Loai.query.filter_by(TenLoai=ten_loai).first()
        if existing:
            return jsonify({'success': False, 'message': 'Tên loại đã tồn tại!'}), 400

        loai = Loai(TenLoai=ten_loai, MoTa=mo_ta)
        db.session.add(loai)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Thêm danh mục thành công!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500