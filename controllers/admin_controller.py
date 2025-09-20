from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from services.services import ProductService, AuthService, OrderService
from models import db, SanPham, Loai, TaiKhoan, DonHang

# Tạo blueprint cho admin
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def require_admin():
    """Helper function kiểm tra quyền admin"""
    # Sẽ được override bởi admin_app.py
    if 'admin_logged_in' not in session:
        return False
    if 'admin_username' not in session:
        return False
    return True


@admin_bp.route('/')
def dashboard():
    """Trang dashboard admin"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('admin_login'))

    try:
        # Thống kê tổng quan
        total_products = SanPham.query.filter_by(TrangThai=1).count()
        total_users = TaiKhoan.query.count()
        total_orders = DonHang.query.count()

        # Đơn hàng gần đây
        recent_orders = DonHang.query.order_by(DonHang.NgayDat.desc()).limit(5).all()

        # Sản phẩm sắp hết hàng
        low_stock_products = SanPham.query.filter(
            SanPham.TrangThai == 1,
            SanPham.SoLuong.between(1, 10)
        ).limit(10).all()

        stats = {
            'total_products': total_products,
            'total_users': total_users,
            'total_orders': total_orders
        }

        return render_template('dashboard.html',
                               stats=stats,
                               recent_orders=recent_orders,
                               low_stock_products=low_stock_products)
    except Exception as e:
        flash(f'Lỗi khi tải dashboard: {str(e)}', 'error')
        return redirect(url_for('admin_login'))


@admin_bp.route('/products')
def manage_products():
    """Quản lý sản phẩm"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('admin_login'))

    try:
        categories = Loai.query.all()
        return render_template('manage_product.html', categories=categories)
    except Exception as e:
        flash(f'Lỗi khi tải danh sách sản phẩm: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/products/add', methods=['GET', 'POST'])
def add_product():
    """Thêm sản phẩm mới"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('admin_login'))

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

            # XỬ LÝ HÌNH ẢNH
            # Ưu tiên lấy URL từ hidden input (khi upload qua API /api/admin/upload-image)
            hinh_anh_url = request.form.get('hinhAnhUrl')

            # Nếu không có URL thì fallback sang upload trực tiếp file từ form
            if not hinh_anh_url and 'hinhAnh' in request.files and request.files['hinhAnh'].filename != '':
                file = request.files['hinhAnh']
                try:
                    import cloudinary.uploader
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
                    hinh_anh_url = result['secure_url']
                except Exception as e:
                    flash(f'Lỗi upload ảnh: {str(e)}', 'error')
                    categories = Loai.query.all()
                    return render_template('manage_product.html', categories=categories, mode='add')

            # Validate
            if not all([ten_san_pham, gia_ban, so_luong, ma_loai]):
                flash('Vui lòng điền đầy đủ thông tin bắt buộc!', 'error')
                categories = Loai.query.all()
                return render_template('manage_product.html', categories=categories, mode='add')

            # Tạo sản phẩm mới
            san_pham = SanPham(
                TenSanPham=ten_san_pham,
                ChiPhi=float(chi_phi) if chi_phi else None,
                GiaNhap=float(gia_nhap) if gia_nhap else None,
                GiaBan=float(gia_ban),
                SoLuong=int(so_luong),
                ThungHieu=thuong_hieu,
                MoTa=mo_ta,
                MaLoai=int(ma_loai),
                HinhAnh=hinh_anh_url  # THÊM HÌNH ẢNH
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
        return render_template('manage_product.html', categories=categories, mode='add')
    except Exception as e:
        flash(f'Lỗi: {str(e)}', 'error')
        return redirect(url_for('admin.manage_products'))


# Mở file: admin_controller.py

@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    """Sửa sản phẩm"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('admin_login'))

    try:
        # Lấy sản phẩm từ DB, nếu không có sẽ báo lỗi 404
        product = SanPham.query.get_or_404(product_id)

        # Xử lý khi người dùng nhấn nút "Lưu" trên form
        if request.method == 'POST':
            # Cập nhật thông tin từ form
            product.TenSanPham = request.form.get('tenSanPham', '').strip()
            product.ChiPhi = float(request.form.get('chiPhi', '0')) if request.form.get('chiPhi') else None
            product.GiaNhap = float(request.form.get('giaNhap', '0')) if request.form.get('giaNhap') else None
            product.GiaBan = float(request.form.get('giaBan', '0'))
            product.SoLuong = int(request.form.get('soLuong', '0'))
            product.ThungHieu = request.form.get('thuongHieu', '').strip()
            product.MoTa = request.form.get('moTa', '').strip()
            product.MaLoai = int(request.form.get('maLoai'))

            # Ưu tiên lấy URL từ hidden input
            hinh_anh_url = request.form.get('hinhAnhUrl')

            # Nếu có URL hình ảnh mới thì cập nhật, không thì giữ nguyên ảnh cũ
            if hinh_anh_url:
                product.HinhAnh = hinh_anh_url
            # ===============================================

            db.session.commit()
            flash('Cập nhật sản phẩm thành công!', 'success')
            return redirect(url_for('admin.manage_products'))

        # Xử lý khi người dùng bấm nút "Sửa" để mở form
        # (Phần này có thể không chạy nếu bạn load data bằng JS, nhưng sửa lại cho đúng)
        categories = Loai.query.all()

        # === SỬA LỖI 2: RENDER ĐÚNG TEMPLATE 'manage_product.html' ===
        return render_template('manage_product.html', product=product, categories=categories, mode='edit')
        # =============================================================

    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi chỉnh sửa sản phẩm: {str(e)}', 'error')
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


@admin_bp.route('/products/<int:product_id>')
def get_product_detail(product_id):
    """API lấy chi tiết sản phẩm"""
    if not require_admin():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập!'}), 403

    try:
        product_data = db.session.query(SanPham, Loai).join(Loai).filter(
            SanPham.MaSanPham == product_id
        ).first()

        if not product_data:
            return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại'}), 404

        product, loai = product_data
        result = {
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
            'category_id': product.MaLoai,
            'created_date': product.NgayTao.strftime('%Y-%m-%d %H:%M:%S') if product.NgayTao else '',
            'updated_date': product.NgayCapNhat.strftime('%Y-%m-%d %H:%M:%S') if product.NgayCapNhat else ''
        }

        return jsonify({
            'success': True,
            'product': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@admin_bp.route('/manage_orders')
def manage_orders():
    """Route cho trang quản lý đơn hàng"""
    if not require_admin():
        return redirect(url_for('admin_login'))

    return render_template('manage_orders.html')


@admin_bp.route('/orders/<int:order_id>')
def order_detail(order_id):
    """Chi tiết đơn hàng"""
    if not require_admin():
        flash('Bạn không có quyền truy cập!', 'error')
        return redirect(url_for('admin_login'))

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
        return redirect(url_for('admin_login'))

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
        return redirect(url_for('admin_login'))

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
