from models.models import db, TaiKhoan, DangNhap, SanPham, Loai, GioHang, GioHang_SanPham, DonHang, ChiTiet_DonHang, \
    DiaChi
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import and_


class AuthService:
    @staticmethod
    def register_user(ho, ten, ngay_sinh, gioi_tinh, ma_can_cuoc, dia_chi, so_dien_thoai, ten_tai_khoan, mat_khau,
                      email=None):
        """Đăng ký tài khoản mới"""
        try:
            # Kiểm tra tên tài khoản đã tồn tại chưa
            existing_user = DangNhap.query.filter_by(TenTaiKhoan=ten_tai_khoan).first()
            if existing_user:
                return False, "Tên tài khoản đã tồn tại"

            # Tạo tài khoản mới
            tai_khoan = TaiKhoan(
                Ho=ho,
                Ten=ten,
                NgaySinh=datetime.strptime(ngay_sinh, '%Y-%m-%d').date() if ngay_sinh else None,
                GioiTinh=gioi_tinh,
                MaCanCuoc=ma_can_cuoc,
                DiaChi=dia_chi,
                SoDienThoai=so_dien_thoai
            )

            db.session.add(tai_khoan)
            db.session.flush()  # Để lấy MaTaiKhoan

            # Tạo thông tin đăng nhập
            dang_nhap = DangNhap(
                TenTaiKhoan=ten_tai_khoan,
                MatKhau=generate_password_hash(mat_khau),
                DiaChiEmail=email,
                MaTaiKhoan=tai_khoan.MaTaiKhoan
            )

            db.session.add(dang_nhap)
            db.session.commit()

            return True, tai_khoan.MaTaiKhoan

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def login_user(ten_tai_khoan, mat_khau):
        """Đăng nhập"""
        try:
            dang_nhap = DangNhap.query.filter_by(TenTaiKhoan=ten_tai_khoan, TrangThai=1).first()

            if dang_nhap and check_password_hash(dang_nhap.MatKhau, mat_khau):
                return True, dang_nhap.tai_khoan

            return False, "Tên tài khoản hoặc mật khẩu không đúng"

        except Exception as e:
            return False, f"Lỗi: {str(e)}"


class ProductService:
    @staticmethod
    def get_all_products():
        """Lấy tất cả sản phẩm"""
        try:
            products = db.session.query(SanPham, Loai).join(Loai).filter(SanPham.TrangThai == 1).all()
            return [
                {
                    'id': product.SanPham.MaSanPham,
                    'name': product.SanPham.TenSanPham,
                    'type': product.Loai.TenLoai.lower(),
                    'brand': product.SanPham.ThungHieu or '',
                    'price': float(product.SanPham.GiaBan) if product.SanPham.GiaBan else 0,
                    'description': product.SanPham.MoTa or '',
                    'quantity': product.SanPham.SoLuong
                }
                for product in products
            ]
        except Exception as e:
            print(f"Error getting products: {e}")
            return []

    @staticmethod
    def get_product_by_id(product_id):
        """Lấy sản phẩm theo ID"""
        try:
            product = db.session.query(SanPham, Loai).join(Loai).filter(
                and_(SanPham.MaSanPham == product_id, SanPham.TrangThai == 1)
            ).first()

            if product:
                return {
                    'id': product.SanPham.MaSanPham,
                    'name': product.SanPham.TenSanPham,
                    'type': product.Loai.TenLoai.lower(),
                    'brand': product.SanPham.ThungHieu or '',
                    'price': float(product.SanPham.GiaBan) if product.SanPham.GiaBan else 0,
                    'description': product.SanPham.MoTa or '',
                    'quantity': product.SanPham.SoLuong
                }
            return None
        except Exception as e:
            print(f"Error getting product: {e}")
            return None


class CartService:
    @staticmethod
    def get_or_create_cart(ma_tai_khoan):
        """Lấy hoặc tạo giỏ hàng cho tài khoản"""
        try:
            cart = GioHang.query.filter_by(MaTaiKhoan=ma_tai_khoan).first()
            if not cart:
                cart = GioHang(MaTaiKhoan=ma_tai_khoan)
                db.session.add(cart)
                db.session.commit()
            return cart
        except Exception as e:
            db.session.rollback()
            print(f"Error getting cart: {e}")
            return None

    @staticmethod
    def add_to_cart(ma_tai_khoan, ma_san_pham, so_luong=1):
        """Thêm sản phẩm vào giỏ hàng"""
        try:
            cart = CartService.get_or_create_cart(ma_tai_khoan)
            if not cart:
                return False, "Không thể tạo giỏ hàng"

            # Kiểm tra sản phẩm có tồn tại và còn hàng
            product = SanPham.query.filter_by(MaSanPham=ma_san_pham, TrangThai=1).first()
            if not product:
                return False, "Sản phẩm không tồn tại"

            if product.SoLuong < so_luong:
                return False, "Không đủ hàng trong kho"

            # Kiểm tra sản phẩm đã có trong giỏ hàng chưa
            cart_item = GioHang_SanPham.query.filter_by(
                MaGioHang=cart.MaGioHang,
                MaSanPham=ma_san_pham
            ).first()

            if cart_item:
                # Cập nhật số lượng
                new_quantity = cart_item.SoLuong + so_luong
                if product.SoLuong < new_quantity:
                    return False, "Không đủ hàng trong kho"
                cart_item.SoLuong = new_quantity
            else:
                # Thêm mới
                cart_item = GioHang_SanPham(
                    MaGioHang=cart.MaGioHang,
                    MaSanPham=ma_san_pham,
                    SoLuong=so_luong
                )
                db.session.add(cart_item)

            # Cập nhật tổng số lượng trong giỏ hàng
            CartService.update_cart_total(cart.MaGioHang)

            db.session.commit()
            return True, "Thêm vào giỏ hàng thành công"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def get_cart_items(ma_tai_khoan):
        """Lấy các item trong giỏ hàng"""
        try:
            cart = GioHang.query.filter_by(MaTaiKhoan=ma_tai_khoan).first()
            if not cart:
                return []

            cart_items = db.session.query(GioHang_SanPham, SanPham).join(SanPham).filter(
                GioHang_SanPham.MaGioHang == cart.MaGioHang
            ).all()

            return [
                {
                    'id': item.SanPham.MaSanPham,
                    'name': f"{item.SanPham.TenSanPham} - {item.SanPham.ThungHieu or ''}",
                    'price': float(item.SanPham.GiaBan) if item.SanPham.GiaBan else 0,
                    'quantity': item.GioHang_SanPham.SoLuong
                }
                for item in cart_items
            ]

        except Exception as e:
            print(f"Error getting cart items: {e}")
            return []

    @staticmethod
    def update_cart_total(ma_gio_hang):
        """Cập nhật tổng số lượng trong giỏ hàng"""
        try:
            total = db.session.query(db.func.sum(GioHang_SanPham.SoLuong)).filter_by(
                MaGioHang=ma_gio_hang
            ).scalar() or 0

            cart = GioHang.query.get(ma_gio_hang)
            if cart:
                cart.TongSoLuong = total

        except Exception as e:
            print(f"Error updating cart total: {e}")


class OrderService:
    @staticmethod
    def create_order(ma_tai_khoan, ma_dia_chi):
        """Tạo đơn hàng từ giỏ hàng"""
        try:
            # Lấy giỏ hàng
            cart = GioHang.query.filter_by(MaTaiKhoan=ma_tai_khoan).first()
            if not cart or cart.TongSoLuong == 0:
                return False, "Giỏ hàng trống"

            # Lấy các item trong giỏ hàng
            cart_items = db.session.query(GioHang_SanPham, SanPham).join(SanPham).filter(
                GioHang_SanPham.MaGioHang == cart.MaGioHang
            ).all()

            if not cart_items:
                return False, "Giỏ hàng trống"

            # Tính tổng tiền
            tong_tien = sum(
                item.GioHang_SanPham.SoLuong * float(item.SanPham.GiaBan or 0)
                for item in cart_items
            )

            # Tạo đơn hàng
            don_hang = DonHang(
                MaTaiKhoan=ma_tai_khoan,
                MaDiaChi=ma_dia_chi,
                TongTien=tong_tien
            )

            db.session.add(don_hang)
            db.session.flush()  # Để lấy MaDonHang

            # Tạo chi tiết đơn hàng
            for item in cart_items:
                chi_tiet = ChiTiet_DonHang(
                    MaDonHang=don_hang.MaDonHang,
                    MaSanPham=item.SanPham.MaSanPham,
                    SoLuong=item.GioHang_SanPham.SoLuong,
                    DonGia=item.SanPham.GiaBan
                )
                db.session.add(chi_tiet)

            # Xóa giỏ hàng
            GioHang_SanPham.query.filter_by(MaGioHang=cart.MaGioHang).delete()
            cart.TongSoLuong = 0

            db.session.commit()
            return True, don_hang.MaDonHang

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi: {str(e)}"