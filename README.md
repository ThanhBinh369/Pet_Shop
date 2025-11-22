# 🐾 Hệ Thống Web Bán Hàng Cho Thú Cưng

> Đồ án ngành Khoa Học Máy Tính - Trường Đại Học Mở TP.HCM

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Mục Lục

- [Giới Thiệu](#-giới-thiệu)
- [Tính Năng](#-tính-năng)
- [Công Nghệ Sử Dụng](#-công-nghệ-sử-dụng)
- [Kiến Trúc Hệ Thống](#-kiến-trúc-hệ-thống)
- [Cài Đặt](#-cài-đặt)
- [Sử Dụng](#-sử-dụng)
- [Screenshots](#-screenshots)
- [Tác Giả](#-tác-giả)

## 🎯 Giới Thiệu

Hệ thống web bán hàng cho thú cưng là một nền tảng thương mại điện tử toàn diện, giúp quản lý và vận hành cửa hàng thú cưng một cách hiệu quả. Dự án được phát triển nhằm đáp ứng xu hướng mua sắm trực tuyến ngày càng tăng, mang đến trải nghiệm mua sắm thuận tiện cho khách hàng và công cụ quản lý mạnh mẽ cho chủ cửa hàng.

### Ý Nghĩa Đề Tài

- 🛒 Đơn giản hóa quy trình mua sắm trực tuyến
- 📊 Quản lý sản phẩm, đơn hàng hiệu quả
- 📈 Thống kê doanh thu theo thời gian thực
- 🎯 Nâng cao trải nghiệm người dùng

## ✨ Tính Năng

### Dành Cho Khách Hàng

- ✅ **Đăng ký & Đăng nhập** - Quản lý tài khoản cá nhân
- 🔍 **Tìm kiếm & Lọc sản phẩm** - Tìm kiếm theo tên, danh mục, giá cả
- 🛒 **Giỏ hàng thông minh** - Thêm, sửa, xóa sản phẩm dễ dàng
- 📦 **Đặt hàng & Thanh toán** - Quy trình đặt hàng đơn giản
- 👤 **Quản lý thông tin** - Cập nhật thông tin cá nhân, địa chỉ giao hàng
- 📋 **Theo dõi đơn hàng** - Xem lịch sử và trạng thái đơn hàng
- 🔒 **Bảo mật tài khoản** - Đổi mật khẩu, bảo vệ thông tin

### Dành Cho Quản Trị Viên

- 📦 **Quản lý sản phẩm** - CRUD đầy đủ cho sản phẩm
- 📊 **Dashboard thống kê** - Tổng quan nhanh về hệ thống
- 🚚 **Quản lý đơn hàng** - Cập nhật trạng thái, xử lý đơn hàng
- 👥 **Quản lý khách hàng** - Xem thông tin, hỗ trợ khách hàng
- 📈 **Báo cáo doanh thu** - Biểu đồ theo tuần, tháng, quý
- 🔍 **Tìm kiếm & Lọc** - Công cụ tìm kiếm mạnh mẽ

## 🛠️ Công Nghệ Sử Dụng

### Backend
- **Flask** - Framework Python cho web development
- **Python 3.8+** - Ngôn ngữ lập trình chính
- **Flask-SQLAlchemy** - ORM cho database
- **MySQL** - Hệ quản trị cơ sở dữ liệu

### Frontend
- **HTML5** - Cấu trúc trang web
- **CSS3** - Styling và responsive design
- **JavaScript** - Xử lý tương tác người dùng
- **Bootstrap** - Framework CSS

### Cloud & Storage
- **Cloudinary** - Lưu trữ và xử lý hình ảnh
- **CDN** - Tăng tốc độ tải trang

### Tools & Libraries
- **Git** - Version control
- **Draw.io** - Thiết kế sơ đồ hệ thống

## 🏗️ Kiến Trúc Hệ Thống

Dự án sử dụng mô hình **MVC (Model-View-Controller)** để tổ chức code:

```
Pet_Shop/
├── models/              # Database models
├── views/               # Templates & UI
├── controllers/         # Business logic
├── static/             
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── images/         # Static images
├── templates/          # HTML templates
├── config.py           # Configuration
├── requirements.txt    # Dependencies
└── app.py             # Main application
```

### ERD (Entity Relationship Diagram)

Hệ thống bao gồm các thực thể chính:
- **TaiKhoan** - Thông tin người dùng
- **SanPham** - Thông tin sản phẩm
- **GioHang** - Giỏ hàng
- **DonHang** - Đơn hàng
- **DiaChi** - Địa chỉ giao hàng

## 🚀 Cài Đặt

### Yêu Cầu Hệ Thống

- Python 3.8 trở lên
- MySQL 8.0+
- pip (Python package manager)

### Các Bước Cài Đặt

1. **Clone repository**
```bash
git clone https://github.com/ThanhBinh369/Pet_Shop.git
cd Pet_Shop
```

2. **Tạo môi trường ảo**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

4. **Cấu hình database**
```sql
-- Tạo database trong MySQL
CREATE DATABASE pet_shop;
```

5. **Cấu hình file config**
```python
# Tạo file config.py (không commit lên Git)
SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/pet_shop'
SECRET_KEY = 'your-secret-key-here'
CLOUDINARY_CLOUD_NAME = 'your-cloud-name'
CLOUDINARY_API_KEY = 'your-api-key'
CLOUDINARY_API_SECRET = 'your-api-secret'
```

6. **Chạy migration**
```bash
flask db init
flask db migrate
flask db upgrade
```

7. **Khởi động server**
```bash
python app.py
```

Truy cập: `http://localhost:5000`

## 💻 Sử Dụng

### Tài Khoản Mặc Định

**Admin:**
- Username: `admin`
- Password: `admin123`

**Khách hàng mẫu:**
- Username: `customer`
- Password: `customer123`

### Quy Trình Mua Hàng

1. Đăng ký/Đăng nhập tài khoản
2. Duyệt và tìm kiếm sản phẩm
3. Thêm sản phẩm vào giỏ hàng
4. Xác nhận giỏ hàng và thông tin giao hàng
5. Đặt hàng và theo dõi trạng thái

### Quy Trình Quản Lý (Admin)

1. Đăng nhập với tài khoản admin
2. Quản lý sản phẩm: Thêm/Sửa/Xóa
3. Xử lý đơn hàng: Cập nhật trạng thái
4. Xem báo cáo thống kê doanh thu
5. Quản lý thông tin khách hàng

## 📸 Screenshots

### Giao Diện Khách Hàng
- Trang chủ với danh sách sản phẩm nổi bật
- Chi tiết sản phẩm với mô tả đầy đủ
- Giỏ hàng và quy trình thanh toán
- Trang quản lý thông tin cá nhân

### Giao Diện Admin
- Dashboard với thống kê tổng quan
- Quản lý sản phẩm với bộ lọc mạnh mẽ
- Xử lý đơn hàng theo thời gian thực
- Biểu đồ doanh thu chi tiết

## 🎓 Tác Giả

**Nguyễn Thanh Bình**
- MSSV: 2251012016
- Trường: Đại Học Mở TP.HCM
- Khoa: Công Nghệ Thông Tin
- Email: [thanhbinh@ou.edu.vn]

**Giảng viên hướng dẫn:**
- ThS. Hồ Quang Khải

## 📝 License

Dự án này được phát triển cho mục đích học tập tại Trường Đại Học Mở TP.HCM.

## 🙏 Lời Cảm Ơn

Em xin chân thành cảm ơn:
- Quý thầy cô Khoa Công Nghệ Thông Tin
- ThS. Hồ Quang Khải - Giảng viên hướng dẫn
- Bạn bè và gia đình đã hỗ trợ trong quá trình thực hiện đề tài

## 🔮 Hướng Phát Triển

- [ ] Tích hợp thanh toán online (VNPay, Momo, ZaloPay)
- [ ] Tự động hóa cập nhật trạng thái đơn hàng
- [ ] Tích hợp AI hỗ trợ tư vấn khách hàng
- [ ] Thêm tính năng đánh giá và nhận xét sản phẩm
- [ ] Phát triển mobile app (iOS/Android)
- [ ] Hệ thống thông báo real-time
- [ ] Tích hợp chat với khách hàng

## 📞 Liên Hệ & Hỗ Trợ

Nếu bạn có bất kỳ câu hỏi hoặc góp ý nào, vui lòng liên hệ qua:
- Email: [17bighero10@gmail.com]


---

⭐ Nếu bạn thấy dự án này hữu ích, hãy cho một star nhé! ⭐
