from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services import AuthService

# Tạo blueprint cho authentication
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Đăng nhập"""
    # Nếu đã đăng nhập, chuyển về trang chủ
    if 'user_id' in session:
        return redirect(url_for('main.index'))

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
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash(result, 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Đăng xuất"""
    username = session.get('username', 'Người dùng')
    session.clear()
    flash(f'Tạm biệt {username}! Đã đăng xuất thành công.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Đăng ký tài khoản"""
    # Nếu đã đăng nhập, chuyển về trang chủ
    if 'user_id' in session:
        return redirect(url_for('main.index'))

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


@auth_bp.route('/profile')
def profile():
    """Trang thông tin cá nhân"""
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem thông tin cá nhân!', 'warning')
        return redirect(url_for('auth.login'))

    # TODO: Lấy thông tin chi tiết user từ database
    user_info = {
        'full_name': session.get('full_name'),
        'username': session.get('username')
    }

    return render_template('profile.html', user=user_info)