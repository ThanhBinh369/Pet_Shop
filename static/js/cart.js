// Cart functionality
document.addEventListener('DOMContentLoaded', function() {
    initCartFunctionality();
});

function initCartFunctionality() {
    // Update quantity buttons
    document.querySelectorAll('.increase-qty, .decrease-qty').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-id');
            const input = document.querySelector(`.quantity-input[data-id="${productId}"]`);
            const isIncrease = this.classList.contains('increase-qty');

            let currentValue = parseInt(input.value);
            const newValue = isIncrease ? currentValue + 1 : Math.max(1, currentValue - 1);

            updateQuantity(productId, newValue, input);
        });
    });

    // Quantity input change
    document.querySelectorAll('.quantity-input').forEach(input => {
        input.addEventListener('change', function() {
            const productId = this.getAttribute('data-id');
            const newValue = Math.max(1, parseInt(this.value) || 1);

            updateQuantity(productId, newValue, this);
        });
    });

    // Remove item buttons
    document.querySelectorAll('.remove-item').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-id');
            removeItem(productId, this);
        });
    });

    // Clear all items button
    const clearAllBtn = document.querySelector('.clear-all-btn');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function() {
            if (confirm('Bạn có chắc muốn xóa tất cả sản phẩm khỏi giỏ hàng?')) {
                clearCart();
            }
        });
    }

    // Apply promo code button
    const applyPromoBtn = document.getElementById('apply-promo');
    if (applyPromoBtn) {
        applyPromoBtn.addEventListener('click', function() {
            const promoCode = document.getElementById('promo-code').value.trim();
            if (promoCode) {
                applyPromoCode(promoCode);
            } else {
                showToast('Vui lòng nhập mã giảm giá!', 'warning');
            }
        });
    }

    // Enter key for promo code
    const promoInput = document.getElementById('promo-code');
    if (promoInput) {
        promoInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('apply-promo').click();
            }
        });
    }
}


// Update quantity function
function updateQuantity(productId, quantity, inputElement) {
    const cartItem = inputElement.closest('.cart-item');
    const originalValue = inputElement.value;

    // Show loading state
    setLoadingState(cartItem, true);

    fetch('/update-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: parseInt(productId),
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            inputElement.value = quantity;

            // CHỈ cập nhật giá TỔNG (màu xanh) của sản phẩm này
            const totalPriceElement = cartItem.querySelector('.fw-bold.text-primary');
            if (totalPriceElement && data.item_subtotal !== undefined) {
                totalPriceElement.textContent = data.item_subtotal.toLocaleString() + 'đ';
            }

            updateCartDisplay(data);
            showToast('Đã cập nhật số lượng!', 'success');
        } else {
            inputElement.value = originalValue;
            showToast(data.message || 'Lỗi khi cập nhật số lượng', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        inputElement.value = originalValue;
        showToast('Lỗi mạng xảy ra', 'error');
    })
    .finally(() => {
        setLoadingState(cartItem, false);
    });
}
// Remove item function
function removeItem(productId, buttonElement) {
    if (!confirm('Bạn có chắc muốn xóa sản phẩm này khỏi giỏ hàng?')) {
        return;
    }

    const cartItem = buttonElement.closest('.cart-item');
    const originalHTML = buttonElement.innerHTML;

    // Show loading state
    buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    buttonElement.disabled = true;

    fetch('/remove-from-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_id: parseInt(productId) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Animate removal
            cartItem.classList.add('cart-item-removing');

            setTimeout(() => {
                cartItem.remove();
                updateCartDisplay(data);
                showToast('Đã xóa sản phẩm khỏi giỏ hàng!', 'success');

                // Check if cart is empty
                if (!document.querySelectorAll('.cart-item').length) {
                    setTimeout(() => location.reload(), 500);
                }
            }, 300);
        } else {
            showToast(data.message || 'Lỗi khi xóa sản phẩm', 'error');
            buttonElement.innerHTML = originalHTML;
            buttonElement.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Lỗi mạng xảy ra', 'error');
        buttonElement.innerHTML = originalHTML;
        buttonElement.disabled = false;
    });
}

// Clear all items function
function clearCart() {
    const clearBtn = document.querySelector('.clear-all-btn');
    const originalText = clearBtn.textContent;

    clearBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Đang xóa...';
    clearBtn.disabled = true;

    fetch('/clear-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Đã xóa tất cả sản phẩm!', 'success');
            setTimeout(() => location.reload(), 500);
        } else {
            showToast(data.message || 'Lỗi khi xóa giỏ hàng', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Lỗi mạng xảy ra', 'error');
    })
    .finally(() => {
        clearBtn.textContent = originalText;
        clearBtn.disabled = false;
    });
}

// Apply promo code function
function applyPromoCode(code) {
    const button = document.getElementById('apply-promo');
    const originalText = button.textContent;

    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    button.disabled = true;

    fetch('/apply-promo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ promo_code: code })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartDisplay(data);
            document.querySelector('.discount').textContent = `-${data.discount.toLocaleString()}₫`;
            showToast('Đã áp dụng mã giảm giá!', 'success');
            document.getElementById('promo-code').value = '';
        } else {
            showToast(data.message || 'Mã giảm giá không hợp lệ', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Lỗi mạng xảy ra', 'error');
    })
    .finally(() => {
        button.textContent = originalText;
        button.disabled = false;
    });
}

// Helper functions
function updateCartDisplay(data) {
    // Update cart totals
    if (data.subtotal !== undefined) {
        const subtotalElement = document.querySelector('.subtotal');
        if (subtotalElement) {
            subtotalElement.textContent = data.subtotal.toLocaleString() + '₫';
        }
    }

    if (data.total !== undefined) {
        const totalElement = document.querySelector('.total-amount');
        if (totalElement) {
            totalElement.textContent = data.total.toLocaleString() + '₫';
        }
    }

    // Update cart badge
    if (data.cart_count !== undefined) {
        updateCartBadge(data.cart_count);
    }

    // Update item count display
    if (data.item_count !== undefined) {
        const itemCountElement = document.querySelector('.cart-items-count');
        if (itemCountElement) {
            itemCountElement.textContent = `${data.item_count} sản phẩm trong giỏ`;
        }
    }
}

function updateSubtotalForItem(cartItem, subtotal) {
    const totalPriceElement = cartItem.querySelector('.fw-bold.text-primary');
    if (totalPriceElement && subtotal !== undefined) {
        totalPriceElement.textContent = subtotal.toLocaleString() + 'đ';
    }
}

function setLoadingState(element, isLoading) {
    if (isLoading) {
        element.classList.add('loading');
    } else {
        element.classList.remove('loading');
    }
}

function showToast(message, type = 'info') {
    // Remove existing toasts
    document.querySelectorAll('.custom-toast').forEach(toast => {
        toast.remove();
    });

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${getAlertClass(type)} alert-dismissible fade show custom-toast`;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.minWidth = '300px';
    toast.style.maxWidth = '400px';

    const icon = getToastIcon(type);
    toast.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    document.body.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

function getAlertClass(type) {
    switch (type) {
        case 'success': return 'success';
        case 'error': return 'danger';
        case 'warning': return 'warning';
        default: return 'info';
    }
}

function getToastIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-triangle';
        case 'warning': return 'exclamation-circle';
        default: return 'info-circle';
    }
}

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

// Smooth scroll to top when page loads
window.addEventListener('load', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});