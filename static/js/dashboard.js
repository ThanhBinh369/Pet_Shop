// Dashboard functionality
class AdminDashboard {
    constructor() {
        this.init();
    }

    init() {
        this.loadStatistics();
        this.loadCharts();
        this.loadRecentOrders();
        this.loadLowStockProducts();
        this.setupEventListeners();
    }

    async loadStatistics() {
        try {
            const response = await fetch('/api/admin/quick-stats');
            const data = await response.json();

            if (data.success) {
                this.updateStatistics(data.data);
            } else {
                console.error('Error loading statistics:', data.message);
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    updateStatistics(stats) {
        // Cập nhật thống kê sản phẩm
        const totalProductsEl = document.getElementById('totalProducts');
        const inStockEl = document.getElementById('inStockProducts');
        const lowStockEl = document.getElementById('lowStockProducts');
        const outOfStockEl = document.getElementById('outOfStockProducts');

        if (totalProductsEl) totalProductsEl.textContent = stats.products.total;
        if (inStockEl) inStockEl.textContent = stats.products.in_stock;
        if (lowStockEl) lowStockEl.textContent = stats.products.low_stock;
        if (outOfStockEl) outOfStockEl.textContent = stats.products.out_of_stock;

        // Cập nhật thống kê đơn hàng
        const totalOrdersEl = document.getElementById('totalOrders');
        const pendingOrdersEl = document.getElementById('pendingOrders');

        if (totalOrdersEl) totalOrdersEl.textContent = stats.orders.total;
        if (pendingOrdersEl) pendingOrdersEl.textContent = stats.orders.pending;

        // Cập nhật thống kê người dùng
        const totalUsersEl = document.getElementById('totalUsers');
        if (totalUsersEl) totalUsersEl.textContent = stats.users.total;
    }

    async loadCharts() {
        try {
            // Mặc định load 7 ngày
            const response = await fetch('/api/admin/sales-chart?period=7');
            const data = await response.json();

            if (data.success) {
                this.renderSalesChart(data.chartData);
                this.setupChartPeriodButtons();
            } else {
                console.error('Error loading chart data:', data.message);
            }
        } catch (error) {
            console.error('Error loading chart data:', error);
        }
    }


    setupChartPeriodButtons() {
        const buttons = document.querySelectorAll('[data-period]');
        buttons.forEach(button => {
            button.addEventListener('click', async (e) => {
                // Remove active class from all buttons
                buttons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                e.target.classList.add('active');

                const period = e.target.getAttribute('data-period');
                try {
                    const response = await fetch(`/api/admin/sales-chart?period=${period}`);
                    const data = await response.json();

                    if (data.success) {
                        this.renderSalesChart(data.chartData);
                    }
                } catch (error) {
                    console.error('Error loading chart data:', error);
                }
            });
        });
    }

    renderSalesChart(chartData) {
        const ctx = document.getElementById('salesChart');
        if (!ctx) return;
        // Xóa chart cũ nếu có
        if (this.salesChart) {
            this.salesChart.destroy();
        }
        if (typeof Chart !== 'undefined') {
            this.salesChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.labels || [],
                    datasets: [{
                        label: 'Doanh thu (VND)',
                        data: chartData.values || [],
                        borderColor: '#f28c38',
                        backgroundColor: 'rgba(242, 140, 56, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#f28c38',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    return 'Doanh thu: ' + new Intl.NumberFormat('vi-VN').format(context.parsed.y) + ' VND';
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function (value) {
                                    if (value >= 1000000) {
                                        return (value / 1000000).toFixed(1) + ' triệu';
                                    } else if (value >= 1000) {
                                        return (value / 1000).toFixed(0) + ' nghìn';
                                    } else {
                                        return value.toLocaleString('vi-VN') + ' đ';
                                    }
                                }
                            }
                        }
                    },
                    elements: {
                        point: {
                            hoverRadius: 8
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
        }
    }

    async loadRecentOrders() {
        try {
            const response = await fetch('/api/admin/recent-orders');
            const data = await response.json();

            if (data.success) {
                this.renderRecentOrders(data.orders);
            }
        } catch (error) {
            console.error('Error loading recent orders:', error);
        }
    }

    renderRecentOrders(orders) {
        const tbody = document.getElementById('recentOrdersBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        orders.forEach(order => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>#${order.id}</td>
                <td>${order.customer_name}</td>
                <td>${this.formatCurrency(order.total)}</td>
                <td>${this.formatDate(order.date)}</td>
                <td><span class="badge status-${order.status}">${this.getStatusText(order.status)}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="adminDashboard.viewOrder(${order.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadLowStockProducts() {
        try {
            const response = await fetch('/api/admin/low-stock-products');
            const data = await response.json();

            if (data.success) {
                this.renderLowStockProducts(data.products);
            }
        } catch (error) {
            console.error('Error loading low stock products:', error);
        }
    }

    renderLowStockProducts(products) {
        const tbody = document.getElementById('lowStockProductsBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        products.forEach(product => {
            const row = document.createElement('tr');
            const stockClass = product.quantity === 0 ? 'danger' : product.quantity <= 5 ? 'warning' : 'success';

            row.innerHTML = `
                <td>${product.name}</td>
                <td>${product.category}</td>
                <td><span class="badge bg-${stockClass}">${product.quantity}</span></td>
                <td>${this.formatCurrency(product.price)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="adminDashboard.editProduct(${product.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshDashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshDashboard();
            });
        }

        // Auto refresh every 30 seconds
        setInterval(() => {
            this.loadStatistics();
            this.loadCharts(); // Thêm dòng này
        }, 60000);
    }

    refreshDashboard() {
        const refreshBtn = document.getElementById('refreshDashboard');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang tải...';
            refreshBtn.disabled = true;
        }

        Promise.all([
            this.loadStatistics(),
            this.loadRecentOrders(),
            this.loadLowStockProducts()
        ]).finally(() => {
            if (refreshBtn) {
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Làm mới';
                refreshBtn.disabled = false;
            }
        });
    }

    // Utility functions
    formatCurrency(amount) {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(amount);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    getStatusText(status) {
        const statusMap = {
            'pending': 'Chờ xử lý',
            'shipped': 'Đã gửi',
            'delivered': 'Đã giao',
            'cancelled': 'Đã hủy'
        };
        return statusMap[status] || status;
    }

    // Action functions
    viewOrder(orderId) {
        window.location.href = `/admin/orders/${orderId}`;
    }

    editProduct(productId) {
        window.location.href = `/admin/products/edit/${productId}`;
    }

    // Notification functions
    showNotification(message, type = 'info') {
        // Tạo toast notification
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        const toastContainer = document.getElementById('toastContainer') || document.body;
        toastContainer.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove toast after hide
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    window.adminDashboard = new AdminDashboard();
});

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdminDashboard;
}