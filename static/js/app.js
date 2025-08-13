// Thêm vào cuối file app.js

// Profile page navigation
$('.list-group-item').click(function(e) {
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
    if(target) {
        $(target).fadeIn(300);
    }
});

// Edit profile button
$(document).on('click', '.btn:contains("Chỉnh sửa")', function() {
    Swal.fire({
        title: 'Thông báo!',
        text: 'Chức năng chỉnh sửa thông tin đang được phát triển.',
        icon: 'info',
        confirmButtonColor: '#f28c38',
        timer: 2000
    });
});

// Change password button
$(document).on('click', '.btn:contains("Đổi mật khẩu")', function() {
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

            return { current, newPass };
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // TODO: Implement actual password change logic
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
$(document).on('click', '.btn:contains("Thêm địa chỉ mới")', function() {
    Swal.fire({
        title: 'Thông báo!',
        text: 'Chức năng thêm địa chỉ đang được phát triển.',
        icon: 'info',
        confirmButtonColor: '#f28c38',
        timer: 2000
    });
});