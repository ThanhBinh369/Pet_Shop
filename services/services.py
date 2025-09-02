from models.models import db, TaiKhoan, DangNhap, SanPham, Loai, GioHang, GioHang_SanPham, DonHang, ChiTiet_DonHang, \
    DiaChi
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import current_app
from sqlalchemy import and_
import json


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

    @staticmethod
    def change_password(ma_tai_khoan, current_password, new_password):
        """Đổi mật khẩu"""
        try:
            # Lấy thông tin đăng nhập
            dang_nhap = DangNhap.query.filter_by(MaTaiKhoan=ma_tai_khoan, TrangThai=1).first()

            if not dang_nhap:
                return False, "Không tìm thấy tài khoản"

            # Kiểm tra mật khẩu hiện tại
            if not check_password_hash(dang_nhap.MatKhau, current_password):
                return False, "Mật khẩu hiện tại không đúng"

            # Cập nhật mật khẩu mới
            dang_nhap.MatKhau = generate_password_hash(new_password)
            db.session.commit()

            return True, "Đổi mật khẩu thành công"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def update_profile(ma_tai_khoan, ho, ten, so_dien_thoai, ngay_sinh, gioi_tinh, dia_chi):
        """Cập nhật thông tin cá nhân"""
        try:
            tai_khoan = TaiKhoan.query.get(ma_tai_khoan)
            if not tai_khoan:
                return False, "Không tìm thấy tài khoản"

            # Cập nhật thông tin
            tai_khoan.Ho = ho
            tai_khoan.Ten = ten
            tai_khoan.SoDienThoai = so_dien_thoai
            tai_khoan.DiaChi = dia_chi
            tai_khoan.GioiTinh = gioi_tinh

            # Xử lý ngày sinh
            if ngay_sinh:
                try:
                    tai_khoan.NgaySinh = datetime.strptime(ngay_sinh, '%Y-%m-%d').date()
                except:
                    tai_khoan.NgaySinh = None

            db.session.commit()
            return True, "Cập nhật thông tin thành công"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def add_address(ma_tai_khoan, ten_nguoi_nhan, so_dien_thoai, dia_chi, quan_huyen, tinh_thanh, mac_dinh=False):
        """Thêm địa chỉ mới"""
        try:
            # Kiểm tra số lượng địa chỉ hiện có
            current_count = DiaChi.query.filter_by(MaTaiKhoan=ma_tai_khoan).count()
            if current_count >= 5:
                return False, "Bạn chỉ có thể thêm tối đa 5 địa chỉ giao hàng"
            # Nếu đặt làm địa chỉ mặc định, bỏ mặc định của các địa chỉ khác
            if mac_dinh:
                DiaChi.query.filter_by(MaTaiKhoan=ma_tai_khoan).update({'DiaChiMacDinh': 0})

            # Tạo địa chỉ mới
            dia_chi_moi = DiaChi(
                MaTaiKhoan=ma_tai_khoan,
                TenNguoiNhan=ten_nguoi_nhan,
                SoDienThoai=so_dien_thoai,
                DiaChi=dia_chi,
                QuanHuyen=quan_huyen,
                TinhThanh=tinh_thanh,
                DiaChiMacDinh=1 if mac_dinh else 0
            )

            db.session.add(dia_chi_moi)
            db.session.commit()

            return True, "Thêm địa chỉ thành công"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def update_address(ma_tai_khoan, address_id, ten_nguoi_nhan, so_dien_thoai, dia_chi, quan_huyen, tinh_thanh,
                       mac_dinh=False):
        """Cập nhật địa chỉ"""
        try:
            # Kiểm tra địa chỉ có thuộc về user không
            address = DiaChi.query.filter_by(MaDiaChi=address_id, MaTaiKhoan=ma_tai_khoan).first()
            if not address:
                return False, "Không tìm thấy địa chỉ hoặc không có quyền chỉnh sửa"

            # Nếu đặt làm địa chỉ mặc định, bỏ mặc định của các địa chỉ khác
            if mac_dinh:
                DiaChi.query.filter_by(MaTaiKhoan=ma_tai_khoan).update({'DiaChiMacDinh': 0})

            # Cập nhật thông tin địa chỉ
            address.TenNguoiNhan = ten_nguoi_nhan
            address.SoDienThoai = so_dien_thoai
            address.DiaChi = dia_chi
            address.QuanHuyen = quan_huyen
            address.TinhThanh = tinh_thanh
            address.DiaChiMacDinh = 1 if mac_dinh else 0

            db.session.commit()
            return True, "Cập nhật địa chỉ thành công"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def delete_address(ma_tai_khoan, address_id):
        """Xóa địa chỉ"""
        try:
            # Kiểm tra địa chỉ có thuộc về user không
            address = DiaChi.query.filter_by(MaDiaChi=address_id, MaTaiKhoan=ma_tai_khoan).first()
            if not address:
                return False, "Không tìm thấy địa chỉ hoặc không có quyền xóa"

            # Kiểm tra số lượng địa chỉ còn lại
            total_addresses = DiaChi.query.filter_by(MaTaiKhoan=ma_tai_khoan).count()
            if total_addresses <= 1:
                return False, "Không thể xóa địa chỉ cuối cùng"

            # Nếu xóa địa chỉ mặc định, đặt địa chỉ đầu tiên làm mặc định
            was_default = address.DiaChiMacDinh == 1

            db.session.delete(address)

            # Nếu địa chỉ vừa xóa là mặc định, đặt địa chỉ đầu tiên còn lại làm mặc định
            if was_default:
                first_remaining_address = DiaChi.query.filter_by(MaTaiKhoan=ma_tai_khoan).first()
                if first_remaining_address:
                    first_remaining_address.DiaChiMacDinh = 1

            db.session.commit()
            return True, "Xóa địa chỉ thành công"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def get_user_addresses(ma_tai_khoan):
        """Lấy danh sách địa chỉ của user"""
        try:
            addresses = DiaChi.query.filter_by(MaTaiKhoan=ma_tai_khoan).all()
            return [
                {
                    'id': addr.MaDiaChi,
                    'ten_nguoi_nhan': addr.TenNguoiNhan,
                    'so_dien_thoai': addr.SoDienThoai,
                    'dia_chi': addr.DiaChi,
                    'quan_huyen': addr.QuanHuyen,
                    'tinh_thanh': addr.TinhThanh,
                    'mac_dinh': bool(addr.DiaChiMacDinh),
                    'dia_chi_day_du': f"{addr.DiaChi}, {addr.QuanHuyen}, {addr.TinhThanh}"
                }
                for addr in addresses
            ]
        except Exception as e:
            print(f"Error getting addresses: {e}")
            return []


class ProductService:
    @staticmethod
    def get_cloudinary_url(image_filename):
        """Tạo URL Cloudinary từ tên file"""
        if not image_filename:
            return None

        cloud_name = current_app.config.get('CLOUDINARY_CLOUD_NAME')
        if not cloud_name:
            return None

        # Nếu đã là URL đầy đủ thì return luôn
        if image_filename.startswith('http'):
            return image_filename

        # Tạo URL Cloudinary theo format: folder/filename
        return f"https://res.cloudinary.com/{cloud_name}/image/upload/v1/{image_filename}"

    @staticmethod
    def get_all_products():
        """Lấy tất cả sản phẩm"""
        try:
            # Thử cách khác
            products = db.session.query(SanPham).join(Loai, SanPham.MaLoai == Loai.MaLoai).filter(
                SanPham.TrangThai == 1).all()

            result = []
            for product in products:
                # Xử lý hình ảnh chính
                main_image = ProductService.get_cloudinary_url(
                    getattr(product, 'HinhAnh', None)
                )

                # Xử lý hình ảnh phụ
                additional_images = []
                if hasattr(product, 'HinhAnhPhu') and product.HinhAnhPhu:
                    try:
                        import json
                        image_list = json.loads(product.HinhAnhPhu)
                        additional_images = [ProductService.get_cloudinary_url(img) for img in image_list if img]
                        additional_images = [img for img in additional_images if img]
                    except:
                        additional_images = []

                # Tạo danh sách tất cả hình ảnh
                all_images = []
                if main_image:
                    all_images.append(main_image)
                all_images.extend(additional_images)

                result.append({
                    'id': product.MaSanPham,
                    'name': product.TenSanPham,
                    'type': product.loai.TenLoai if product.loai else 'unknown',
                    'brand': product.ThungHieu or '',
                    'price': float(product.GiaBan) if product.GiaBan else 0,
                    'description': product.MoTa or '',
                    'quantity': product.SoLuong,
                    'image': main_image,
                    'images': all_images
                })

            print(f"ProductService trả về {len(result)} sản phẩm")
            return result
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
                # Xử lý hình ảnh chính
                main_image = ProductService.get_cloudinary_url(
                    getattr(product.SanPham, 'HinhAnh', None)
                )

                # Xử lý hình ảnh phụ
                additional_images = []
                if hasattr(product.SanPham, 'HinhAnhPhu') and product.SanPham.HinhAnhPhu:
                    try:
                        import json
                        image_list = json.loads(product.SanPham.HinhAnhPhu)
                        additional_images = [ProductService.get_cloudinary_url(img) for img in image_list if img]
                        additional_images = [img for img in additional_images if img]
                    except:
                        additional_images = []

                # Tạo danh sách tất cả hình ảnh
                all_images = []
                if main_image:
                    all_images.append(main_image)
                all_images.extend(additional_images)

                return {
                    'id': product.SanPham.MaSanPham,
                    'name': product.SanPham.TenSanPham,
                    'type': product.Loai.TenLoai,
                    'brand': product.SanPham.ThungHieu or '',
                    'price': float(product.SanPham.GiaBan) if product.SanPham.GiaBan else 0,
                    'description': product.SanPham.MoTa or '',
                    'quantity': product.SanPham.SoLuong,
                    'image': main_image,
                    'images': all_images
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
                    'name': item.SanPham.TenSanPham,
                    'brand': item.SanPham.ThungHieu or '',
                    'category': item.SanPham.loai.TenLoai if item.SanPham.loai else '',
                    'price': float(item.SanPham.GiaBan) if item.SanPham.GiaBan else 0,
                    'quantity': item.GioHang_SanPham.SoLuong,
                    'image': '/static/images/products/default.jpg'  # Thêm ảnh mặc định
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

    @staticmethod
    def remove_from_cart(ma_tai_khoan, ma_san_pham):
        """Xóa sản phẩm khỏi giỏ hàng"""
        try:
            cart = GioHang.query.filter_by(MaTaiKhoan=ma_tai_khoan).first()
            if not cart:
                return False, "Không tìm thấy giỏ hàng"

            cart_item = GioHang_SanPham.query.filter_by(
                MaGioHang=cart.MaGioHang,
                MaSanPham=ma_san_pham
            ).first()

            if not cart_item:
                return False, "Sản phẩm không có trong giỏ hàng"

            db.session.delete(cart_item)

            # Cập nhật tổng số lượng
            CartService.update_cart_total(cart.MaGioHang)

            db.session.commit()
            return True, "Đã xóa sản phẩm khỏi giỏ hàng"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def update_cart_item(ma_tai_khoan, ma_san_pham, so_luong):
        """Cập nhật số lượng sản phẩm trong giỏ hàng"""
        try:
            cart = GioHang.query.filter_by(MaTaiKhoan=ma_tai_khoan).first()
            if not cart:
                return False, "Không tìm thấy giỏ hàng"

            cart_item = GioHang_SanPham.query.filter_by(
                MaGioHang=cart.MaGioHang,
                MaSanPham=ma_san_pham
            ).first()

            if not cart_item:
                return False, "Sản phẩm không có trong giỏ hàng"

            cart_item.SoLuong = so_luong

            # Cập nhật tổng số lượng
            CartService.update_cart_total(cart.MaGioHang)

            db.session.commit()
            return True, "Đã cập nhật số lượng"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def clear_cart(ma_tai_khoan):
        """Xóa toàn bộ giỏ hàng"""
        try:
            cart = GioHang.query.filter_by(MaTaiKhoan=ma_tai_khoan).first()
            if not cart:
                return False, "Không tìm thấy giỏ hàng"

            GioHang_SanPham.query.filter_by(MaGioHang=cart.MaGioHang).delete()
            cart.TongSoLuong = 0

            db.session.commit()
            return True, "Đã xóa toàn bộ giỏ hàng"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi: {str(e)}"


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
