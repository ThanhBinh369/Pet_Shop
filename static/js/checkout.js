// Checkout Page JavaScript

$(document).ready(function() {
    // Debug - kiểm tra địa chỉ có load không
    console.log('Number of addresses found:', $('.address-card').length);

    // Xử lý chọn địa chỉ
    $('.address-card').on('click', function() {
        $('.address-card').removeClass('selected');
        $(this).addClass('selected');
        $(this).find('input[type="radio"]').prop('checked', true);
    });

    // Xử lý chọn/bỏ chọn sản phẩm
    $('.product-checkbox').on('change', function() {
        updateOrderSummary();
        updateSelectAllCheckbox();
    });

    // Xử lý chọn tất cả (nếu có)
    $('#selectAll').on('change', function() {
        const isChecked = $(this).is(':checked');
        $('.product-checkbox').prop('checked', isChecked);
        updateOrderSummary();
    });

    // Xử lý thay đổi số lượng bằng nút +/-
    $('.quantity-btn').on('click', function() {
        const action = $(this).data('action');
        const productId = $(this).data('product-id');
        const input = $(`.quantity-input[data-product-id="${productId}"]`);
        const maxQuantity = parseInt(input.data('max-quantity'));
        let currentValue = parseInt(input.val());

        if (action === 'increase' && currentValue < maxQuantity) {
            input.val(currentValue + 1);
        } else if (action === 'decrease' && currentValue > 1) {
            input.val(currentValue - 1);
        }

        // Cập nhật data-quantity cho checkbox
        $(`.product-checkbox[data-product-id="${productId}"]`).data('quantity', input.val());

        updateProductTotal(productId);
        updateOrderSummary();
    });

    // Xử lý thay đổi số lượng trực tiếp
    $('.quantity-input').on('change', function() {
        const productId = $(this).data('product-id');
        const maxQuantity = parseInt($(this).data('max-quantity'));
        let value = parseInt($(this).val());

        if (value < 1) value = 1;
        if (value > maxQuantity) value = maxQuantity;

        $(this).val(value);

        // Cập nhật data-quantity cho checkbox
        $(`.product-checkbox[data-product-id="${productId}"]`).data('quantity', value);

        updateProductTotal(productId);
        updateOrderSummary();
    });

    // Cập nhật tóm tắt đơn hàng
    function updateOrderSummary() {
        let total = 0;
        let selectedCount = 0;

        $('.product-checkbox:checked').each(function() {
            const productId = $(this).data('product-id') || $(this).data('product-id');
            const price = parseFloat($(this).data('price'));
            let quantity;

            // Lấy số lượng từ input nếu có, nếu không thì lấy từ data-quantity
            const quantityInput = $(`.quantity-input[data-product-id="${productId}"]`);
            if (quantityInput.length > 0) {
                quantity = parseInt(quantityInput.val());
            } else {
                quantity = parseInt($(this).data('quantity'));
            }

            total += price * quantity;
            selectedCount++;
        });

        // Cập nhật UI
        $('#selected-count').text(selectedCount);
        $('#selected-items-count').text(selectedCount); // Thêm cho trường hợp có element này
        $('#subtotal').text(formatCurrency(total));
        $('#total-amount').text(formatCurrency(total));

        // Disable nút đặt hàng nếu không có sản phẩm nào được chọn
        $('.confirm-btn').prop('disabled', selectedCount === 0);
    }

    // Cập nhật tổng tiền của từng sản phẩm
    function updateProductTotal(productId) {
        const checkbox = $(`.product-checkbox[data-product-id="${productId}"]`);
        const price = parseFloat(checkbox.data('price'));
        const quantityInput = $(`.quantity-input[data-product-id="${productId}"]`);
        const quantity = parseInt(quantityInput.val());
        const subtotal = price * quantity;

        $(`.product-summary[data-product-id="${productId}"] .item-subtotal`)
            .text(formatCurrency(subtotal));
    }

    // Format tiền tệ
    function formatCurrency(amount) {
        return new Intl.NumberFormat('vi-VN').format(amount) + '₫';
    }

    // Cập nhật trạng thái checkbox "Chọn tất cả"
    function updateSelectAllCheckbox() {
        const totalCheckboxes = $('.product-checkbox').length;
        const checkedCheckboxes = $('.product-checkbox:checked').length;

        if ($('#selectAll').length > 0) {
            $('#selectAll').prop('checked', totalCheckboxes === checkedCheckboxes);
            $('#selectAll').prop('indeterminate', checkedCheckboxes > 0 && checkedCheckboxes < totalCheckboxes);
        }
    }

    // Khởi tạo
    updateOrderSummary();

    // Xử lý form submit
    $('#checkout-form').on('submit', function(e) {
        e.preventDefault();

        const selectedProducts = [];
        const selectedQuantities = [];

        $('.product-checkbox:checked').each(function() {
            const productId = $(this).data('product-id');
            let quantity;

            // Lấy số lượng từ input nếu có
            const quantityInput = $(`.quantity-input[data-product-id="${productId}"]`);
            if (quantityInput.length > 0) {
                quantity = quantityInput.val();
            } else {
                quantity = $(this).data('quantity');
            }

            selectedProducts.push(productId);
            selectedQuantities.push(quantity);
        });

        if (selectedProducts.length === 0) {
            alert('Vui lòng chọn ít nhất một sản phẩm để đặt hàng!');
            return;
        }

        const selectedAddress = $('input[name="address_id"]:checked').length;
        if (selectedAddress === 0) {
            alert('Vui lòng chọn địa chỉ giao hàng!');
            return;
        }

        // Thêm hidden inputs cho các sản phẩm được chọn
        const form = $(this);
        form.find('input[name="selected_products[]"]').remove();
        form.find('input[name="selected_quantities[]"]').remove();

        selectedProducts.forEach(function(productId, index) {
            form.append(`<input type="hidden" name="selected_products[]" value="${productId}">`);
            form.append(`<input type="hidden" name="selected_quantities[]" value="${selectedQuantities[index]}">`);
        });

        if (confirm('Bạn có chắc chắn muốn đặt hàng ' + selectedProducts.length + ' sản phẩm đã chọn?')) {
            $('.confirm-btn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Đang xử lý...');
            this.submit();
        }
    });
});