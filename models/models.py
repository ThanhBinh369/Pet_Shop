from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Loai(db.Model):
    __tablename__ = 'Loai'

    MaLoai = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TenLoai = db.Column(db.String(100), nullable=False)
    MoTa = db.Column(db.Text)

    # Relationship
    san_phams = db.relationship('SanPham', backref='loai', lazy=True)


class SanPham(db.Model):
    __tablename__ = 'SanPham'

    MaSanPham = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TenSanPham = db.Column(db.String(255), nullable=False)
    ChiPhi = db.Column(db.Numeric(12, 2))
    GiaNhap = db.Column(db.Numeric(12, 2))
    GiaBan = db.Column(db.Numeric(12, 2))
    SoLuong = db.Column(db.Integer, nullable=False)
    NgayTao = db.Column(db.DateTime, default=datetime.utcnow)
    NgayCapNhat = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ThungHieu = db.Column(db.String(100))
    MoTa = db.Column(db.Text)
    TrangThai = db.Column(db.Integer, default=1)
    MaLoai = db.Column(db.Integer, db.ForeignKey('Loai.MaLoai'), nullable=False)


class TaiKhoan(db.Model):
    __tablename__ = 'TaiKhoan'

    MaTaiKhoan = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Ho = db.Column(db.String(100))
    Ten = db.Column(db.String(100))
    NgaySinh = db.Column(db.Date)
    GioiTinh = db.Column(db.String(1))
    MaCanCuoc = db.Column(db.String(20))
    DiaChi = db.Column(db.Text)
    SoDienThoai = db.Column(db.String(20))

    # Relationships
    dang_nhap = db.relationship('DangNhap', backref='tai_khoan', uselist=False)
    dia_chis = db.relationship('DiaChi', backref='tai_khoan', lazy=True)
    gio_hangs = db.relationship('GioHang', backref='tai_khoan', lazy=True)
    don_hangs = db.relationship('DonHang', backref='tai_khoan', lazy=True)


class DangNhap(db.Model):
    __tablename__ = 'DangNhap'

    TenTaiKhoan = db.Column(db.String(100), primary_key=True)
    MatKhau = db.Column(db.String(255), nullable=False)
    DiaChiEmail = db.Column(db.String(255))
    TrangThai = db.Column(db.Integer, default=1)
    MaTaiKhoan = db.Column(db.Integer, db.ForeignKey('TaiKhoan.MaTaiKhoan'), nullable=False)


class Quyen(db.Model):
    __tablename__ = 'Quyen'

    MaQuyen = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MieuTa = db.Column(db.String(255))
    TrangThai = db.Column(db.Integer, default=1)


class QuyenTaiKhoan(db.Model):
    __tablename__ = 'QuyenTaiKhoan'

    MaTaiKhoan = db.Column(db.Integer, db.ForeignKey('TaiKhoan.MaTaiKhoan'), primary_key=True)
    MaQuyen = db.Column(db.Integer, db.ForeignKey('Quyen.MaQuyen'), primary_key=True)
    NgayCapNhat = db.Column(db.DateTime, default=datetime.utcnow)


class DiaChi(db.Model):
    __tablename__ = 'DiaChi'

    MaDiaChi = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaTaiKhoan = db.Column(db.Integer, db.ForeignKey('TaiKhoan.MaTaiKhoan'), nullable=False)
    TenNguoiNhan = db.Column(db.String(200))
    SoDienThoai = db.Column(db.String(20))
    DiaChi = db.Column(db.Text)
    QuanHuyen = db.Column(db.String(100))
    TinhThanh = db.Column(db.String(100))
    DiaChiMacDinh = db.Column(db.Integer, default=0)


class GioHang(db.Model):
    __tablename__ = 'GioHang'

    MaGioHang = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaTaiKhoan = db.Column(db.Integer, db.ForeignKey('TaiKhoan.MaTaiKhoan'), nullable=False)
    TongSoLuong = db.Column(db.Integer, default=0)
    NgayTao = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    san_phams = db.relationship('GioHang_SanPham', backref='gio_hang', lazy=True, cascade='all, delete-orphan')


class GioHang_SanPham(db.Model):
    __tablename__ = 'GioHang_SanPham'

    MaGioHang = db.Column(db.Integer, db.ForeignKey('GioHang.MaGioHang'), primary_key=True)
    MaSanPham = db.Column(db.Integer, db.ForeignKey('SanPham.MaSanPham'), primary_key=True)
    SoLuong = db.Column(db.Integer, default=1)
    NgayCapNhat = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    san_pham = db.relationship('SanPham', backref='gio_hang_items', lazy=True)


class DonHang(db.Model):
    __tablename__ = 'DonHang'

    MaDonHang = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaTaiKhoan = db.Column(db.Integer, db.ForeignKey('TaiKhoan.MaTaiKhoan'), nullable=False)
    MaDiaChi = db.Column(db.Integer, db.ForeignKey('DiaChi.MaDiaChi'), nullable=False)
    NgayDat = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.Enum('pending', 'shipped', 'delivered', 'canceled'), default='pending')
    TongTien = db.Column(db.Numeric(12, 2), nullable=False)

    # Relationships
    dia_chi = db.relationship('DiaChi', backref='don_hangs', lazy=True)
    chi_tiets = db.relationship('ChiTiet_DonHang', backref='don_hang', lazy=True, cascade='all, delete-orphan')


class ChiTiet_DonHang(db.Model):
    __tablename__ = 'ChiTiet_DonHang'

    MaChiTietDH = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MaDonHang = db.Column(db.Integer, db.ForeignKey('DonHang.MaDonHang'), nullable=False)
    MaSanPham = db.Column(db.Integer, db.ForeignKey('SanPham.MaSanPham'), nullable=False)
    SoLuong = db.Column(db.Integer, nullable=False)
    DonGia = db.Column(db.Numeric(12, 2), nullable=False)

    # Relationship
    san_pham = db.relationship('SanPham', backref='chi_tiet_don_hangs', lazy=True)