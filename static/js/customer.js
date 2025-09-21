// Customer Management JavaScript
class CustomerManager {
    constructor() {
        this.customers = [];
        this.filteredCustomers = [];
        this.currentCustomerId = null;
        this.confirmationCallback = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadCustomerStats();
        this.loadCustomers();
    }

    bindEvents() {
        // Filter events
        document.getElementById('status-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('order-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('search-filter').addEventListener('input', () => this.applyFilters());
        document.getElementById('clear-filters').addEventListener('click', () => this.clearFilters());

        // Action events
        document.getElementById('refresh-customers').addEventListener('click', () => this.refreshCustomers());

        // Modal events
        const modal = document.getElementById('customer-detail-modal');
        if (modal) {
            const closeBtn = modal.querySelector('.close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.closeCustomerModal());
            }

            // Delete customer button
            const deleteBtn = document.getElementById('delete-customer-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', () => this.showDeleteConfirmation());
            }

            // Close modal when clicking outside
            window.addEventListener('click', (event) => {
                if (event.target === modal) {
                    this.closeCustomerModal();
                }
            });
        }

        // Confirmation modal events
        const confirmModal = document.getElementById('confirmation-modal');
        if (confirmModal) {
            const confirmBtn = document.getElementById('confirm-action-btn');
            if (confirmBtn) {
                confirmBtn.addEventListener('click', () => this.executeConfirmation());
            }

            window.addEventListener('click', (event) => {
                if (event.target === confirmModal) {
                    this.closeConfirmationModal();
                }
            });
        }
    }

    async loadCustomerStats() {
        try {
            const response = await fetch('/api/admin/customer-stats');
            const data = await response.json();

            if (data.success) {
                this.updateStatsDisplay(data.stats);
            }
        } catch (error) {
            console.error('Error loading customer stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        const totalCustomersEl = document.getElementById('total-customers');
        const activeCustomersEl = document.getElementById('active-customers');
        const newCustomersEl = document.getElementById('new-customers');
        const vipCustomersEl = document.getElementById('vip-customers');

        if (totalCustomersEl) totalCustomersEl.textContent = stats.total || 0;
        if (activeCustomersEl) activeCustomersEl.textContent = stats.active || 0;
        if (newCustomersEl) newCustomersEl.textContent = stats.new_this_month || 0;
        if (vipCustomersEl) vipCustomersEl.textContent = stats.vip || 0;
    }

    async loadCustomers() {
        this.showLoading(true);

        try {
            const response = await fetch('/api/admin/customers');
            const data = await response.json();

            if (data.success) {
                this.customers = data.customers;
                this.filteredCustomers = [...this.customers];
                this.renderCustomers();
            } else {
                this.showToast('Lỗi khi tải khách hàng: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Error loading customers:', error);
            this.showToast('Lỗi khi tải khách hàng', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    renderCustomers() {
        const tableBody = document.getElementById('customers-table-body');
        const noDataMessage = document.getElementById('no-data-message');
        const tableResponsive = document.querySelector('.table-responsive');

        if (this.filteredCustomers.length === 0) {
            if (tableBody) tableBody.innerHTML = '';
            if (tableResponsive) tableResponsive.style.display = 'none';
            if (noDataMessage) noDataMessage.style.display = 'block';
            return;
        }

        if (noDataMessage) noDataMessage.style.display = 'none';
        if (tableResponsive) tableResponsive.style.display = 'block';

        if (tableBody) {
            tableBody.innerHTML = this.filteredCustomers.map(customer => `
                <tr>
                    <td>#${customer.id}</td>
                    <td>${customer.full_name}</td>
                    <td>${customer.email || 'N/A'}</td>
                    <td>${customer.phone || 'N/A'}</td>
                    <td><span class="text-primary fw-bold">${customer.total_orders}</span></td>
                    <td><span class="money ${customer.total_spent > 0 ? '' : 'zero'}">${this.formatCurrency(customer.total_spent)}</span></td>
                    <td><span class="status-badge status-${customer.status}">${this.getStatusText(customer.status)}</span></td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-sm btn-outline-primary" onclick="customerManager.viewCustomerDetail(${customer.id})">
                                <i class="fas fa-eye"></i> Xem
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="customerManager.confirmDeleteCustomer(${customer.id}, '${customer.full_name}')">
                                <i class="fas fa-trash"></i> Xóa
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        }
    }

    applyFilters() {
        const statusFilter = document.getElementById('status-filter').value;
        const orderFilter = document.getElementById('order-filter').value;
        const searchFilter = document.getElementById('search-filter').value.toLowerCase();

        this.filteredCustomers = this.customers.filter(customer => {
            const matchStatus = !statusFilter || customer.status === statusFilter;

            let matchOrder = true;
            if (orderFilter === 'has_orders') {
                matchOrder = customer.total_orders > 0;
            } else if (orderFilter === 'no_orders') {
                matchOrder = customer.total_orders === 0;
            }

            const matchSearch = !searchFilter ||
                customer.id.toString().includes(searchFilter) ||
                customer.full_name.toLowerCase().includes(searchFilter) ||
                (customer.email && customer.email.toLowerCase().includes(searchFilter));

            return matchStatus && matchOrder && matchSearch;
        });

        this.renderCustomers();
    }

    clearFilters() {
        document.getElementById('status-filter').value = '';
        document.getElementById('order-filter').value = '';
        document.getElementById('search-filter').value = '';
        this.filteredCustomers = [...this.customers];
        this.renderCustomers();
    }

    async refreshCustomers() {
        await this.loadCustomers();
        await this.loadCustomerStats();
        this.showToast('Đã làm mới dữ liệu', 'success');
    }

    async viewCustomerDetail(customerId) {
        try {
            const response = await fetch(`/api/admin/customers/${customerId}`);
            const data = await response.json();

            if (data.success) {
                this.showCustomerDetail(data.customer);
            } else {
                this.showToast('Lỗi khi tải chi tiết khách hàng: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Error loading customer detail:', error);
            this.showToast('Lỗi khi tải chi tiết khách hàng', 'error');
        }
    }

    showCustomerDetail(customer) {
        this.currentCustomerId = customer.id;

        // Update modal content
        const modalCustomerId = document.getElementById('modal-customer-id');
        const modalCustomerName = document.getElementById('modal-customer-name');
        const modalCustomerEmail = document.getElementById('modal-customer-email');
        const modalCustomerPhone = document.getElementById('modal-customer-phone');
        const modalCustomerBirth = document.getElementById('modal-customer-birth');
        const modalCustomerGender = document.getElementById('modal-customer-gender');
        const modalCustomerAddress = document.getElementById('modal-customer-address');
        const modalTotalOrders = document.getElementById('modal-total-orders');
        const modalTotalSpent = document.getElementById('modal-total-spent');
        const modalLastOrder = document.getElementById('modal-last-order');
        const modalCustomerStatus = document.getElementById('modal-customer-status');

        if (modalCustomerId) modalCustomerId.textContent = customer.id;
        if (modalCustomerName) modalCustomerName.textContent = customer.full_name || 'N/A';
        if (modalCustomerEmail) modalCustomerEmail.textContent = customer.email || 'N/A';
        if (modalCustomerPhone) modalCustomerPhone.textContent = customer.phone || 'N/A';
        if (modalCustomerBirth) modalCustomerBirth.textContent = customer.birth_date || 'N/A';
        if (modalCustomerGender) {
            const genderText = this.getGenderText(customer.gender);
            modalCustomerGender.innerHTML = genderText;
        }
        if (modalCustomerAddress) modalCustomerAddress.textContent = customer.address || 'N/A';
        if (modalTotalOrders) modalTotalOrders.textContent = customer.total_orders || 0;
        if (modalTotalSpent) modalTotalSpent.textContent = this.formatCurrency(customer.total_spent || 0);
        if (modalLastOrder) modalLastOrder.textContent = customer.last_order_date || 'Chưa có đơn hàng';
        if (modalCustomerStatus) {
            modalCustomerStatus.innerHTML = `<span class="status-badge status-${customer.status}">${this.getStatusText(customer.status)}</span>`;
        }

        // Update customer orders
        const ordersTable = document.getElementById('modal-customer-orders');
        if (ordersTable) {
            if (customer.recent_orders && customer.recent_orders.length > 0) {
                ordersTable.innerHTML = customer.recent_orders.map(order => `
                    <tr>
                        <td>#${order.id}</td>
                        <td>${this.formatDate(order.date)}</td>
                        <td>${this.formatCurrency(order.total)}</td>
                        <td><span class="status-badge status-${order.status}">${this.getStatusText(order.status)}</span></td>
                    </tr>
                `).join('');
            } else {
                ordersTable.innerHTML = '<tr><td colspan="4" class="no-orders">Chưa có đơn hàng nào</td></tr>';
            }
        }

        // Show modal
        const modal = document.getElementById('customer-detail-modal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    closeCustomerModal() {
        const modal = document.getElementById('customer-detail-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.currentCustomerId = null;
    }

    confirmDeleteCustomer(customerId, customerName) {
        this.currentCustomerId = customerId;
        const message = `Bạn có chắc chắn muốn xóa khách hàng "${customerName}"?<br><small class="text-muted">Hành động này không thể hoàn tác.</small>`;
        this.showConfirmation(message, () => this.deleteCustomer(customerId));
    }

    showDeleteConfirmation() {
        if (!this.currentCustomerId) return;

        const customer = this.customers.find(c => c.id === this.currentCustomerId);
        if (!customer) return;

        this.confirmDeleteCustomer(this.currentCustomerId, customer.full_name);
    }

    showConfirmation(message, callback) {
        this.confirmationCallback = callback;

        const messageEl = document.getElementById('confirmation-message');
        if (messageEl) {
            messageEl.innerHTML = message;
        }

        const modal = document.getElementById('confirmation-modal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    closeConfirmationModal() {
        const modal = document.getElementById('confirmation-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.confirmationCallback = null;
    }

    executeConfirmation() {
        if (this.confirmationCallback) {
            this.confirmationCallback();
        }
        this.closeConfirmationModal();
    }

    async deleteCustomer(customerId) {
        try {
            const response = await fetch(`/api/admin/customers/${customerId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Xóa khách hàng thành công', 'success');
                this.closeCustomerModal();
                await this.loadCustomers();
                await this.loadCustomerStats();
            } else {
                this.showToast('Lỗi khi xóa khách hàng: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Error deleting customer:', error);
            this.showToast('Lỗi khi xóa khách hàng', 'error');
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
            day: '2-digit'
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
            'active': 'Hoạt Động',
            'inactive': 'Không Hoạt Động'
        };
        return statusTexts[status] || status;
    }

    getGenderText(gender) {
        const genderTexts = {
            'M': '<i class="fas fa-mars gender-icon gender-male"></i> Nam',
            'F': '<i class="fas fa-venus gender-icon gender-female"></i> Nữ'
        };
        return genderTexts[gender] || '<i class="fas fa-question gender-icon"></i> Không xác định';
    }

    showToast(message, type = 'info') {
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
function closeCustomerModal() {
    if (window.customerManager) {
        window.customerManager.closeCustomerModal();
    }
}

function closeConfirmationModal() {
    if (window.customerManager) {
        window.customerManager.closeConfirmationModal();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.customerManager = new CustomerManager();
});