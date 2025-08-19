from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from services import AuthService
from models import TaiKhoan, DangNhap

# Tạo blueprint cho authentication
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Đăng nhập hoặc chuyển đến profile nếu đã đăng nhập"""
    # Nếu đã đăng nhập, chuyển đến trang profile
    if 'user_id' in session:
        return redirect(url_for('auth.profile'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Validate input
        if not username or not password:
            flash('Vui lòng nhập đầy đủ tên tài khoản và mật khẩu!', 'error')
            return render_template('login.html')

        # Thực hiện đăng nhập
        success, result = AuthService.login_user(username, password)

        if success:
            session['user_id'] = result.MaTaiKhoan
            session['username'] = username
            session['full_name'] = f"{result.Ho} {result.Ten}"
            flash('Đăng nhập thành công!', 'success')

            # Redirect về trang trước đó nếu có
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash(result, 'error')

    return render_template('login.html')


@auth_bp.route('/profile')
def profile():
    """Trang thông tin cá nhân"""
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem thông tin cá nhân!', 'warning')
        return redirect(url_for('auth.login'))

    try:
        # Lấy thông tin chi tiết user từ database
        tai_khoan = TaiKhoan.query.get(session['user_id'])
        dang_nhap = DangNhap.query.filter_by(MaTaiKhoan=session['user_id']).first()

        if not tai_khoan:
            flash('Không tìm thấy thông tin tài khoản!', 'error')
            return redirect(url_for('index'))

        user_info = {
            'full_name': f"{tai_khoan.Ho} {tai_khoan.Ten}" if tai_khoan.Ho and tai_khoan.Ten else session.get(
                'full_name'),
            'ho': tai_khoan.Ho,
            'ten': tai_khoan.Ten,
            'username': session.get('username'),
            'email': dang_nhap.DiaChiEmail if dang_nhap else None,
            'phone': tai_khoan.SoDienThoai,
            'birth_date': tai_khoan.NgaySinh.strftime('%Y-%m-%d') if tai_khoan.NgaySinh else None,
            'birth_date_display': tai_khoan.NgaySinh.strftime('%d/%m/%Y') if tai_khoan.NgaySinh else None,
            'gender': 'Nam' if str(tai_khoan.GioiTinh) == '1' else 'Nữ' if str(
                tai_khoan.GioiTinh) == '0' else 'Chưa cập nhật',
            'gender_value': tai_khoan.GioiTinh,
            'address': tai_khoan.DiaChi,
            'citizen_id': tai_khoan.MaCanCuoc
        }

        # Lấy danh sách địa chỉ
        addresses = AuthService.get_user_addresses(session['user_id'])

        return render_template('profile.html', user=user_info, addresses=addresses)

    except Exception as e:
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('index'))

@auth_bp.route('/logout')
def logout():
    """Đăng xuất"""
    username = session.get('username', 'Người dùng')
    session.clear()
    flash(f'Tạm biệt {username}! Đã đăng xuất thành công.', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Đăng ký tài khoản"""
    # Nếu đã đăng nhập, chuyển về trang chủ
    if 'user_id' in session:
        return redirect(url_for('index'))  # Sửa thành 'index' thay vì 'main.index'

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        ho = request.form.get('ho', '').strip()
        ten = request.form.get('ten', '').strip()
        ngay_sinh = request.form.get('ngaySinh', '').strip()
        gioi_tinh = request.form.get('gioiTinh', '').strip()
        ma_can_cuoc = request.form.get('maCanCuoc', '').strip()
        dia_chi = request.form.get('diaChi', '').strip()
        so_dien_thoai = request.form.get('soDienThoai', '').strip()
        ten_tai_khoan = request.form.get('tenTaiKhoan', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirmPassword', '').strip()
        email = request.form.get('email', '').strip()

        # Validate dữ liệu
        if not all([ho, ten, ngay_sinh, gioi_tinh, ma_can_cuoc, dia_chi, so_dien_thoai, ten_tai_khoan, password]):
            flash('Vui lòng điền đầy đủ thông tin bắt buộc!', 'error')
            return render_template('register.html')

        # Kiểm tra mật khẩu xác nhận
        if confirm_password and password != confirm_password:
            flash('Mật khẩu xác nhận không khớp!', 'error')
            return render_template('register.html')

        # Validate độ dài mật khẩu
        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự!', 'error')
            return render_template('register.html')

        # Validate số điện thoại
        if not so_dien_thoai.isdigit() or len(so_dien_thoai) < 10:
            flash('Số điện thoại không hợp lệ!', 'error')
            return render_template('register.html')

        # Thực hiện đăng ký
        success, result = AuthService.register_user(
            ho, ten, ngay_sinh, gioi_tinh, ma_can_cuoc,
            dia_chi, so_dien_thoai, ten_tai_khoan, password, email
        )

        if success:
            flash(f'Đăng ký thành công! Mã tài khoản: {result}. Hãy đăng nhập để tiếp tục.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result, 'error')

    return render_template('register.html')


@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    """Xác thực mã reset password"""
    code = request.form.get('verificationCode', '').strip()

    if not code:
        return "Vui lòng nhập mã xác nhận."

    # TODO: Implement logic xác thực mã thực tế
    # Hiện tại dùng mã cố định để test
    if code == "123456":
        return "Mã xác nhận đúng! Vui lòng đặt lại mật khẩu."
    else:
        return "Mã xác nhận không đúng. Vui lòng thử lại."


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Quên mật khẩu"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash('Vui lòng nhập email!', 'error')
            return render_template('forgot_password.html')

        # TODO: Implement logic gửi email reset password
        flash('Nếu email tồn tại, chúng tôi đã gửi mã xác nhận đến email của bạn.', 'info')
        return render_template('verify_code.html')

    return render_template('forgot_password.html')


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Đổi mật khẩu"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'}), 401

    try:
        data = request.get_json()
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()

        # Validate input
        if not current_password or not new_password:
            return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin!'}), 400

        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Mật khẩu mới phải có ít nhất 6 ký tự!'}), 400

        # Thực hiện đổi mật khẩu
        success, message = AuthService.change_password(session['user_id'], current_password, new_password)

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500


@auth_bp.route('/update-profile', methods=['POST'])
def update_profile():
    """Cập nhật thông tin cá nhân"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'}), 401

    try:
        data = request.get_json()

        # Lấy thông tin từ request
        ho = data.get('ho', '').strip()
        ten = data.get('ten', '').strip()
        phone = data.get('phone', '').strip()
        birth_date = data.get('birth_date', '').strip()
        gender = data.get('gender', '').strip()
        address = data.get('address', '').strip()

        # Validate
        if not ho or not ten:
            return jsonify({'success': False, 'message': 'Họ và tên không được để trống!'}), 400

        if phone and (not phone.isdigit() or len(phone) < 10):
            return jsonify({'success': False, 'message': 'Số điện thoại không hợp lệ!'}), 400

        # Cập nhật thông tin
        success, message = AuthService.update_profile(
            session['user_id'], ho, ten, phone, birth_date, gender, address
        )

        if success:
            # Cập nhật session
            session['full_name'] = f"{ho} {ten}"
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500


@auth_bp.route('/add-address', methods=['POST'])
def add_address():
    """Thêm địa chỉ mới"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'}), 401

    try:
        data = request.get_json()

        ten_nguoi_nhan = data.get('ten_nguoi_nhan', '').strip()
        so_dien_thoai = data.get('so_dien_thoai', '').strip()
        dia_chi = data.get('dia_chi', '').strip()
        quan_huyen = data.get('quan_huyen', '').strip()
        tinh_thanh = data.get('tinh_thanh', '').strip()
        mac_dinh = data.get('mac_dinh', False)

        # Validate
        if not all([ten_nguoi_nhan, so_dien_thoai, dia_chi, quan_huyen, tinh_thanh]):
            return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin!'}), 400

        if not so_dien_thoai.isdigit() or len(so_dien_thoai) < 10:
            return jsonify({'success': False, 'message': 'Số điện thoại không hợp lệ!'}), 400

        # Thêm địa chỉ
        success, message = AuthService.add_address(
            session['user_id'], ten_nguoi_nhan, so_dien_thoai,
            dia_chi, quan_huyen, tinh_thanh, mac_dinh
        )

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500

@auth_bp.route('/update-address', methods=['POST'])
def update_address():
    """Cập nhật địa chỉ"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'}), 401

    try:
        data = request.get_json()
        address_id = data.get('address_id')
        ten_nguoi_nhan = data.get('ten_nguoi_nhan', '').strip()
        so_dien_thoai = data.get('so_dien_thoai', '').strip()
        dia_chi = data.get('dia_chi', '').strip()
        quan_huyen = data.get('quan_huyen', '').strip()
        tinh_thanh = data.get('tinh_thanh', '').strip()
        mac_dinh = data.get('mac_dinh', False)

        # Validate
        if not all([address_id, ten_nguoi_nhan, so_dien_thoai, dia_chi, quan_huyen, tinh_thanh]):
            return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin!'}), 400

        if not so_dien_thoai.isdigit() or len(so_dien_thoai) < 10:
            return jsonify({'success': False, 'message': 'Số điện thoại không hợp lệ!'}), 400

        # Cập nhật địa chỉ
        success, message = AuthService.update_address(
            session['user_id'], address_id, ten_nguoi_nhan, so_dien_thoai,
            dia_chi, quan_huyen, tinh_thanh, mac_dinh
        )

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500


@auth_bp.route('/delete-address', methods=['POST'])
def delete_address():
    """Xóa địa chỉ"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'}), 401

    try:
        data = request.get_json()
        address_id = data.get('address_id')

        if not address_id:
            return jsonify({'success': False, 'message': 'Thiếu thông tin địa chỉ!'}), 400

        # Xóa địa chỉ
        success, message = AuthService.delete_address(session['user_id'], address_id)

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500
