// Thêm vào cuối file app.js

// Profile page navigation
$('.list-group-item').click(function (e) {
    e.preventDefault();

    // Remove active class from all items
    $('.list-group-item').removeClass('active');
    // Add active class to clicked item
    $(this).addClass('active');

    // Get target section
    let target = $(this).attr('href');

    // Hide all sections
    $('[id^="personal-info"], [id^="orders"], [id^="address"], [id^="security"]').hide();

    // Show target section
    if (target) {
        $(target).fadeIn(300);
    }
});

// Edit profile button
$(document).on('click', '.btn:contains("Chỉnh sửa")', function () {
    // Lấy thông tin hiện tại từ trang
    const currentData = {
        ho: $('.profile-ho').text().trim() || '',
        ten: $('.profile-ten').text().trim() || '',
        phone: $('.profile-phone').text().trim() || '',
        birth_date: $('.profile-birth-date').attr('data-value') || '',
        gender: $('.profile-gender').attr('data-value') || '',
        address: $('.profile-address').text().trim() || ''
    };

    Swal.fire({
        title: 'Chỉnh sửa thông tin cá nhân',
        html: `
            <div class="text-start">
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Họ *</label>
                            <input type="text" class="form-control" id="editHo" value="${currentData.ho}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Tên *</label>
                            <input type="text" class="form-control" id="editTen" value="${currentData.ten}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Số điện thoại</label>
                            <input type="tel" class="form-control" id="editPhone" value="${currentData.phone}">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Ngày sinh</label>
                            <input type="date" class="form-control" id="editBirthDate" value="${currentData.birth_date}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Giới tính</label>
                            <select class="form-control" id="editGender">
                                <option value="">Chọn giới tính</option>
                                <option value="1" ${currentData.gender === '1' ? 'selected' : ''}>Nam</option>
                                <option value="0" ${currentData.gender === '0' ? 'selected' : ''}>Nữ</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Địa chỉ</label>
                            <textarea class="form-control" id="editAddress" rows="3">${currentData.address}</textarea>
                        </div>
                    </div>
                </div>
            </div>
        `,
        width: '600px',
        showCancelButton: true,
        confirmButtonText: 'Cập nhật',
        cancelButtonText: 'Hủy',
        confirmButtonColor: '#f28c38',
        cancelButtonColor: '#6c757d',
        showLoaderOnConfirm: true,
        preConfirm: () => {
            const ho = $('#editHo').val().trim();
            const ten = $('#editTen').val().trim();
            const phone = $('#editPhone').val().trim();
            const birth_date = $('#editBirthDate').val();
            const gender = $('#editGender').val();
            const address = $('#editAddress').val().trim();

            if (!ho || !ten) {
                Swal.showValidationMessage('Họ và tên không được để trống');
                return false;
            }

            if (phone && (!/^\d+$/.test(phone) || phone.length < 10)) {
                Swal.showValidationMessage('Số điện thoại không hợp lệ');
                return false;
            }

            return fetch('/update-profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ho: ho,
                    ten: ten,
                    phone: phone,
                    birth_date: birth_date,
                    gender: gender,
                    address: address
                })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    throw new Error(data.message);
                }
                return data;
            })
            .catch(error => {
                Swal.showValidationMessage(error.message);
                return false;
            });
        },
        allowOutsideClick: () => !Swal.isLoading()
    }).then((result) => {
        if (result.isConfirmed && result.value) {
            Swal.fire({
                title: 'Thành công!',
                text: 'Thông tin đã được cập nhật.',
                icon: 'success',
                confirmButtonColor: '#f28c38'
            }).then(() => {
                location.reload(); // Reload trang để hiển thị thông tin mới
            });
        }
    });
});

// Add new address button
$(document).on('click', '.btn:contains("Thêm địa chỉ mới")', function () {
    Swal.fire({
        title: 'Thêm địa chỉ mới',
        html: `
            <div class="text-start">
                <div class="mb-3">
                    <label class="form-label">Tên người nhận *</label>
                    <input type="text" class="form-control" id="addTenNguoiNhan" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Số điện thoại *</label>
                    <input type="tel" class="form-control" id="addSoDienThoai" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Địa chỉ chi tiết *</label>
                    <textarea class="form-control" id="addDiaChi" rows="2" required></textarea>
                </div>
                <div class="mb-3">
                    <label class="form-label">Quận/Huyện *</label>
                    <input type="text" class="form-control" id="addQuanHuyen" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Tỉnh/Thành phố *</label>
                    <input type="text" class="form-control" id="addTinhThanh" required>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="addMacDinh">
                    <label class="form-check-label" for="addMacDinh">
                        Đặt làm địa chỉ mặc định
                    </label>
                </div>
            </div>
        `,
        width: '500px',
        showCancelButton: true,
        confirmButtonText: 'Thêm địa chỉ',
        cancelButtonText: 'Hủy',
        confirmButtonColor: '#f28c38',
        cancelButtonColor: '#6c757d',
        showLoaderOnConfirm: true,
        preConfirm: () => {
            const ten_nguoi_nhan = $('#addTenNguoiNhan').val().trim();
            const so_dien_thoai = $('#addSoDienThoai').val().trim();
            const dia_chi = $('#addDiaChi').val().trim();
            const quan_huyen = $('#addQuanHuyen').val().trim();
            const tinh_thanh = $('#addTinhThanh').val().trim();
            const mac_dinh = $('#addMacDinh').is(':checked');

            if (!ten_nguoi_nhan || !so_dien_thoai || !dia_chi || !quan_huyen || !tinh_thanh) {
                Swal.showValidationMessage('Vui lòng điền đầy đủ thông tin bắt buộc');
                return false;
            }

            if (!/^\d+$/.test(so_dien_thoai) || so_dien_thoai.length < 10) {
                Swal.showValidationMessage('Số điện thoại không hợp lệ');
                return false;
            }

            return fetch('/add-address', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ten_nguoi_nhan: ten_nguoi_nhan,
                    so_dien_thoai: so_dien_thoai,
                    dia_chi: dia_chi,
                    quan_huyen: quan_huyen,
                    tinh_thanh: tinh_thanh,
                    mac_dinh: mac_dinh
                })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    throw new Error(data.message);
                }
                return data;
            })
            .catch(error => {
                Swal.showValidationMessage(error.message);
                return false;
            });
        },
        allowOutsideClick: () => !Swal.isLoading()
    }).then((result) => {
        if (result.isConfirmed && result.value) {
            Swal.fire({
                title: 'Thành công!',
                text: 'Địa chỉ đã được thêm.',
                icon: 'success',
                confirmButtonColor: '#f28c38'
            }).then(() => {
                location.reload(); // Reload trang để hiển thị địa chỉ mới
            });
        }
    });
});

// Change password button
$(document).on('click', '.btn:contains("Đổi mật khẩu")', function () {
    Swal.fire({
        title: 'Đổi mật khẩu',
        html: `
            <div class="text-start">
                <div class="mb-3">
                    <label class="form-label">Mật khẩu hiện tại</label>
                    <input type="password" class="form-control" id="currentPassword" placeholder="Nhập mật khẩu hiện tại">
                </div>
                <div class="mb-3">
                    <label class="form-label">Mật khẩu mới</label>
                    <input type="password" class="form-control" id="newPassword" placeholder="Nhập mật khẩu mới">
                </div>
                <div class="mb-3">
                    <label class="form-label">Xác nhận mật khẩu mới</label>
                    <input type="password" class="form-control" id="confirmPassword" placeholder="Xác nhận mật khẩu mới">
                </div>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Đổi mật khẩu',
        cancelButtonText: 'Hủy',
        confirmButtonColor: '#f28c38',
        cancelButtonColor: '#6c757d',
        showLoaderOnConfirm: true,
        preConfirm: () => {
            const current = $('#currentPassword').val();
            const newPass = $('#newPassword').val();
            const confirm = $('#confirmPassword').val();

            if (!current || !newPass || !confirm) {
                Swal.showValidationMessage('Vui lòng điền đầy đủ thông tin');
                return false;
            }

            if (newPass !== confirm) {
                Swal.showValidationMessage('Mật khẩu xác nhận không khớp');
                return false;
            }

            if (newPass.length < 6) {
                Swal.showValidationMessage('Mật khẩu phải có ít nhất 6 ký tự');
                return false;
            }

            // Gửi request đổi mật khẩu
            return fetch('/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    current_password: current,
                    new_password: newPass
                })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    throw new Error(data.message);
                }
                return data;
            })
            .catch(error => {
                Swal.showValidationMessage(error.message);
                return false;
            });
        },
        allowOutsideClick: () => !Swal.isLoading()
    }).then((result) => {
        if (result.isConfirmed && result.value) {
            Swal.fire({
                title: 'Thành công!',
                text: 'Mật khẩu đã được thay đổi.',
                icon: 'success',
                confirmButtonColor: '#f28c38'
            });
        }
    });
});

// Add new address button
$(document).on('click', '.btn:contains("Thêm địa chỉ mới")', function () {
    Swal.fire({
        title: 'Thông báo!',
        text: 'Chức năng thêm địa chỉ đang được phát triển.',
        icon: 'info',
        confirmButtonColor: '#f28c38',
        timer: 2000
    });
});

document.addEventListener('DOMContentLoaded', function () {
    // Add to cart functionality
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function () {
            const productId = this.getAttribute('data-id');

            // Show loading state
            const originalHTML = this.innerHTML;
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';

            fetch('/add-to-cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: 1
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success state
                        this.innerHTML = '<i class="fas fa-check"></i> Added!';
                        this.classList.remove('btn-primary');
                        this.classList.add('btn-success');

                        // Show success message
                        showToast('Product added to cart successfully!', 'success');

                        // Update cart count if available
                        if (data.cart_count !== undefined) {
                            updateCartBadge(data.cart_count);
                        }

                        // Reset button after 2 seconds
                        setTimeout(() => {
                            this.innerHTML = originalHTML;
                            this.classList.remove('btn-success');
                            this.classList.add('btn-primary');
                            this.disabled = false;
                        }, 2000);
                    } else {
                        // Show error
                        showToast(data.message || 'Error adding product to cart', 'error');
                        this.disabled = false;
                        this.innerHTML = originalHTML;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Network error occurred', 'error');
                    this.disabled = false;
                    this.innerHTML = originalHTML;
                });
        });
    });

    // Auto-submit form when select changes
    const categorySelect = document.getElementById('category');
    const sortSelect = document.getElementById('sort');

    if (categorySelect) {
        categorySelect.addEventListener('change', function () {
            this.form.submit();
        });
    }

    if (sortSelect) {
        sortSelect.addEventListener('change', function () {
            this.form.submit();
        });
    }
});

// Product detail page functionality
document.addEventListener('DOMContentLoaded', function () {
    const quantityInput = document.getElementById('quantity');
    const decreaseBtn = document.getElementById('decrease-qty');
    const increaseBtn = document.getElementById('increase-qty');
    const addToCartBtn = document.getElementById('add-to-cart-btn');

    // Get max quantity from page (will be set by template)
    const maxQuantityElement = document.querySelector('[data-max-quantity]');
    const maxQuantity = maxQuantityElement ? parseInt(maxQuantityElement.getAttribute('data-max-quantity')) : 999;

    // Quantity controls
    if (decreaseBtn && increaseBtn && quantityInput) {
        decreaseBtn.addEventListener('click', function () {
            let currentValue = parseInt(quantityInput.value);
            if (currentValue > 1) {
                quantityInput.value = currentValue - 1;
            }
        });

        increaseBtn.addEventListener('click', function () {
            let currentValue = parseInt(quantityInput.value);
            if (currentValue < maxQuantity) {
                quantityInput.value = currentValue + 1;
            }
        });

        // Validate quantity input
        quantityInput.addEventListener('change', function () {
            let value = parseInt(this.value);
            if (isNaN(value) || value < 1) {
                this.value = 1;
            } else if (value > maxQuantity) {
                this.value = maxQuantity;
            }
        });
    }

    // Add to cart functionality for product detail page
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', function () {
            const productId = this.getAttribute('data-id');
            const quantity = quantityInput ? parseInt(quantityInput.value) : 1;

            // Show loading state
            const originalHTML = this.innerHTML;
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding to Cart...';

            fetch('/add-to-cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: quantity
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success state
                        this.innerHTML = '<i class="fas fa-check"></i> Added to Cart!';
                        this.classList.remove('btn-primary');
                        this.classList.add('btn-success');

                        // Show success message
                        showToast(`Added ${quantity} item(s) to cart!`, 'success');

                        // Update cart count
                        if (data.cart_count !== undefined) {
                            updateCartBadge(data.cart_count);
                        }

                        // Reset button after 3 seconds
                        setTimeout(() => {
                            this.innerHTML = originalHTML;
                            this.classList.remove('btn-success');
                            this.classList.add('btn-primary');
                            this.disabled = false;
                        }, 3000);
                    } else {
                        showToast(data.message || 'Error adding product to cart', 'error');
                        this.disabled = false;
                        this.innerHTML = originalHTML;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Network error occurred', 'error');
                    this.disabled = false;
                    this.innerHTML = originalHTML;
                });
        });
    }

    // Product thumbnail functionality
    document.querySelectorAll('.product-thumb').forEach(thumb => {
        thumb.addEventListener('click', function () {
            document.getElementById('main-product-image').src = this.src.replace('80x80', '500x500');
        });
    });
});

// Toast notification function
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show`;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.minWidth = '300px';

    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

// Update cart badge
function updateCartBadge(count) {
    const cartBadge = document.getElementById('cart-badge');
    if (cartBadge) {
        if (count > 0) {
            cartBadge.textContent = count;
            cartBadge.style.display = 'flex';
        } else {
            cartBadge.style.display = 'none';
        }
    }
}
