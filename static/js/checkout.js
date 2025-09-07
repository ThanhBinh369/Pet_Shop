// Checkout Page JavaScript

$(document).ready(function() {
    // Xử lý chọn địa chỉ
    $('.address-card').on('click', function() {
        $('.address-card').removeClass('selected');
        $(this).addClass('selected');
        $(this).find('input[type="radio"]').prop('checked', true);
    });

    // Xử lý checkbox sản phẩm
    $('.product-checkbox').on('change', function() {
        const isChecked = $(this).is(':checked');

        // Enable/disable hidden inputs
        if (isChecked) {
            $(this).closest('.product-summary').find('input[type="hidden"]').prop('disabled', false);
        } else {
            $(this).closest('.product-summary').find('input[type="hidden"]').prop('disabled', true);
        }

        updateOrderSummary();
    });

    // Cập nhật tóm tắt đơn hàng
    function updateOrderSummary() {
        let total = 0;
        let selectedCount = 0;

        $('.product-checkbox:checked').each(function() {
            const price = parseFloat($(this).data('price'));
            const quantity = parseInt($(this).data('quantity'));
            total += price * quantity;
            selectedCount++;
        });

        // Cập nhật UI
        $('#selected-count').text(selectedCount);
        $('#subtotal').text(formatCurrency(total));
        $('#total-amount').text(formatCurrency(total));

        // Disable nút đặt hàng nếu không có sản phẩm nào được chọn
        if (selectedCount === 0) {
            $('.confirm-btn').prop('disabled', true);
        } else {
            $('.confirm-btn').prop('disabled', false);
        }
    }

    // Format tiền tệ
    function formatCurrency(amount) {
        return new Intl.NumberFormat('vi-VN').format(amount) + '₫';
    }

    // Khởi tạo
    updateOrderSummary();

    // Xử lý form submit
    $('#checkout-form').on('submit', function(e) {
        e.preventDefault();

        const selectedCount = $('.product-checkbox:checked').length;
        if (selectedCount === 0) {
            alert('Vui lòng chọn ít nhất một sản phẩm để đặt hàng!');
            return;
        }

        const selectedAddress = $('input[name="address_id"]:checked').length;
        if (selectedAddress === 0) {
            alert('Vui lòng chọn địa chỉ giao hàng!');
            return;
        }

        if (confirm('Bạn có chắc chắn muốn đặt hàng ' + selectedCount + ' sản phẩm đã chọn?')) {
            $('.confirm-btn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Đang xử lý...');
            this.submit();
        }
    });
});