// Order Management JavaScript
class OrderManager {
    constructor() {
        this.orders = [];
        this.filteredOrders = [];
        this.currentOrderId = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadOrderStats();
        this.loadOrders();
    }

    bindEvents() {
        // Filter events
        document.getElementById('status-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('date-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('search-filter').addEventListener('input', () => this.applyFilters());
        document.getElementById('clear-filters').addEventListener('click', () => this.clearFilters());

        // Action events
        document.getElementById('refresh-orders').addEventListener('click', () => this.refreshOrders());

        // Modal events
        const modal = document.getElementById('order-detail-modal');
        if (modal) {
            const closeBtn = modal.querySelector('.close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.closeOrderModal());
            }

            // Update status button
            const updateBtn = document.getElementById('update-status-btn');
            if (updateBtn) {
                updateBtn.addEventListener('click', () => this.updateOrderStatus());
            }

            // Close modal when clicking outside
            window.addEventListener('click', (event) => {
                if (event.target === modal) {
                    this.closeOrderModal();
                }
            });
        }
    }

    async loadOrderStats() {
        try {
            const response = await fetch('/api/admin/order-stats');
            const data = await response.json();

            if (data.success) {
                this.updateStatsDisplay(data.stats);
            }
        } catch (error) {
            console.error('Error loading order stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        const totalOrdersEl = document.getElementById('total-orders');
        const pendingOrdersEl = document.getElementById('pending-orders');
        const shippedOrdersEl = document.getElementById('shipped-orders');
        const deliveredOrdersEl = document.getElementById('delivered-orders');

        if (totalOrdersEl) totalOrdersEl.textContent = stats.total || 0;
        if (pendingOrdersEl) pendingOrdersEl.textContent = stats.pending || 0;
        if (shippedOrdersEl) shippedOrdersEl.textContent = stats.shipped || 0;
        if (deliveredOrdersEl) deliveredOrdersEl.textContent = stats.delivered || 0;
    }

    async loadOrders() {
        this.showLoading(true);

        try {
            const response = await fetch('/api/admin/orders');
            const data = await response.json();

            if (data.success) {
                this.orders = data.orders;
                this.filteredOrders = [...this.orders];
                this.renderOrders();
            } else {
                this.showToast('Lỗi khi tải đơn hàng: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Error loading orders:', error);
            this.showToast('Lỗi khi tải đơn hàng', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    renderOrders() {
        const tableBody = document.getElementById('orders-table-body');
        const noDataMessage = document.getElementById('no-data-message');
        const tableResponsive = document.querySelector('.table-responsive');

        if (this.filteredOrders.length === 0) {
            if (tableBody) tableBody.innerHTML = '';
            if (tableResponsive) tableResponsive.style.display = 'none';
            if (noDataMessage) noDataMessage.style.display = 'block';
            return;
        }

        if (noDataMessage) noDataMessage.style.display = 'none';
        if (tableResponsive) tableResponsive.style.display = 'block';

        if (tableBody) {
            tableBody.innerHTML = this.filteredOrders.map(order => `
                <tr>
                    <td>#${order.id}</td>
                    <td>${order.customer_name}</td>
                    <td>${this.formatDate(order.date)}</td>
                    <td>${this.formatCurrency(order.total)}</td>
                    <td><span class="status-badge status-${order.status}">${this.getStatusText(order.status)}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="orderManager.viewOrderDetail(${order.id})">
                            <i class="fas fa-eye"></i> Xem
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    }

    applyFilters() {
        const statusFilter = document.getElementById('status-filter').value;
        const dateFilter = document.getElementById('date-filter').value;
        const searchFilter = document.getElementById('search-filter').value.toLowerCase();

        this.filteredOrders = this.orders.filter(order => {
            const matchStatus = !statusFilter || order.status === statusFilter;
            const matchDate = !dateFilter || order.date.startsWith(dateFilter);
            const matchSearch = !searchFilter ||
                order.id.toString().includes(searchFilter) ||
                order.customer_name.toLowerCase().includes(searchFilter);

            return matchStatus && matchDate && matchSearch;
        });

        this.renderOrders();
    }

    clearFilters() {
        document.getElementById('status-filter').value = '';
        document.getElementById('date-filter').value = '';
        document.getElementById('search-filter').value = '';
        this.filteredOrders = [...this.orders];
        this.renderOrders();
    }

    async refreshOrders() {
        await this.loadOrders();
        await this.loadOrderStats();
        this.showToast('Đã làm mới dữ liệu', 'success');
    }

    async viewOrderDetail(orderId) {
        try {
            const response = await fetch(`/api/admin/orders/${orderId}`);
            const data = await response.json();

            if (data.success) {
                this.showOrderDetail(data.order);
            } else {
                this.showToast('Lỗi khi tải chi tiết đơn hàng: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Error loading order detail:', error);
            this.showToast('Lỗi khi tải chi tiết đơn hàng', 'error');
        }
    }

    showOrderDetail(order) {
        this.currentOrderId = order.id;

        // Update modal content
        const modalOrderId = document.getElementById('modal-order-id');
        const modalCustomerName = document.getElementById('modal-customer-name');
        const modalCustomerEmail = document.getElementById('modal-customer-email');
        const modalCustomerPhone = document.getElementById('modal-customer-phone');
        const modalReceiverName = document.getElementById('modal-receiver-name');
        const modalShippingAddress = document.getElementById('modal-shipping-address');
        const modalReceiverPhone = document.getElementById('modal-receiver-phone');
        const modalTotalAmount = document.getElementById('modal-total-amount');
        const modalStatusSelect = document.getElementById('modal-status-select');

        if (modalOrderId) modalOrderId.textContent = order.id;
        if (modalCustomerName) modalCustomerName.textContent = order.customer.name || 'N/A';
        if (modalCustomerEmail) modalCustomerEmail.textContent = order.customer.email || 'N/A';
        if (modalCustomerPhone) modalCustomerPhone.textContent = order.customer.phone || 'N/A';
        if (modalReceiverName) modalReceiverName.textContent = order.shipping.receiver_name || 'N/A';
        if (modalShippingAddress) modalShippingAddress.textContent = order.shipping.address || 'N/A';
        if (modalReceiverPhone) modalReceiverPhone.textContent = order.shipping.phone || 'N/A';
        if (modalTotalAmount) modalTotalAmount.textContent = this.formatCurrency(order.total);
        if (modalStatusSelect) modalStatusSelect.value = order.status;

        // Update order items
        const itemsTable = document.getElementById('modal-order-items');
        if (itemsTable) {
            itemsTable.innerHTML = order.items.map(item => `
                <tr>
                    <td>${item.product_name}</td>
                    <td>${item.quantity}</td>
                    <td>${this.formatCurrency(item.price)}</td>
                    <td>${this.formatCurrency(item.quantity * item.price)}</td>
                </tr>
            `).join('');
        }

        // Show modal
        const modal = document.getElementById('order-detail-modal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    closeOrderModal() {
        const modal = document.getElementById('order-detail-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.currentOrderId = null;
    }

    async updateOrderStatus() {
        if (!this.currentOrderId) return;

        const modalStatusSelect = document.getElementById('modal-status-select');
        if (!modalStatusSelect) return;

        const newStatus = modalStatusSelect.value;

        try {
            const response = await fetch(`/api/admin/orders/${this.currentOrderId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: newStatus })
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Cập nhật trạng thái thành công', 'success');
                this.closeOrderModal();
                await this.loadOrders();
                await this.loadOrderStats();
            } else {
                this.showToast('Lỗi khi cập nhật trạng thái: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Error updating order status:', error);
            this.showToast('Lỗi khi cập nhật trạng thái', 'error');
        }
    }

    showLoading(show) {
        const spinner = document.getElementById('loading-spinner');
        const tableResponsive = document.querySelector('.table-responsive');

        if (show) {
            if (spinner) spinner.style.display = 'block';
            if (tableResponsive) tableResponsive.style.display = 'none';
        } else {
            if (spinner) spinner.style.display = 'none';
            if (tableResponsive) tableResponsive.style.display = 'block';
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatCurrency(amount) {
        if (!amount) return '0 ₫';
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(amount);
    }

    getStatusText(status) {
        const statusTexts = {
            'pending': 'Chờ Xử Lý',
            'shipped': 'Đang Giao',
            'delivered': 'Đã Giao',
            'canceled': 'Đã Hủy'
        };
        return statusTexts[status] || status;
    }

    showToast(message, type = 'info') {
        // Sử dụng Bootstrap Toast thay vì custom toast
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;

        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${this.getBootstrapColorClass(type)} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="${this.getToastIcon(type)} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);

        const toastElement = document.getElementById(toastId);
        if (toastElement && typeof bootstrap !== 'undefined') {
            const toast = new bootstrap.Toast(toastElement);
            toast.show();

            // Remove toast after hidden
            toastElement.addEventListener('hidden.bs.toast', () => {
                toastElement.remove();
            });
        }
    }

    getBootstrapColorClass(type) {
        const colorMap = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return colorMap[type] || 'info';
    }

    getToastIcon(type) {
        const icons = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }
}

// Global functions
function closeOrderModal() {
    if (window.orderManager) {
        window.orderManager.closeOrderModal();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.orderManager = new OrderManager();
});