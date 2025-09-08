// Admin Products Management JavaScript - Tích hợp API

// DOM Elements
const addProductBtn = document.getElementById('addProductBtn');
const productModal = new bootstrap.Modal(document.getElementById('productModal'));
const productForm = document.getElementById('productForm');
const productsTableBody = document.getElementById('productsTableBody');
const searchInput = document.getElementById('searchInput');
const categoryFilter = document.getElementById('categoryFilter');
const statusFilter = document.getElementById('statusFilter');
const resetFiltersBtn = document.getElementById('resetFilters');
const selectAllCheckbox = document.getElementById('selectAll');
const bulkActions = document.getElementById('bulkActions');

// Global variables
let productsData = [];
let filteredProducts = [];
let currentEditId = null;

// API Configuration
const API_BASE = '';

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    loadProductsFromAPI();
    initializeEventListeners();
});

// API Functions
async function loadProductsFromAPI() {
    try {
        showLoadingSpinner();

        // Gọi API để lấy dữ liệu sản phẩm từ backend
        const response = await fetch('/api/products');
        const data = await response.json();

        if (data.success) {
            productsData = data.products.map(product => ({
                id: product.id,
                name: product.name,
                category: product.type,
                categoryId: getCategoryIdByName(product.type),
                brand: product.brand || '',
                price: product.price,
                quantity: product.quantity,
                status: getStatusFromQuantity(product.quantity),
                description: product.description || ''
            }));

            filteredProducts = [...productsData];
            renderProductsTable();
            updateStatistics();
        } else {
            throw new Error(data.message || 'Lỗi khi tải dữ liệu');
        }

    } catch (error) {
        console.error('Error loading products:', error);
        Swal.fire({
            title: 'Lỗi!',
            text: `Không thể tải dữ liệu sản phẩm: ${error.message}`,
            icon: 'error',
            confirmButtonColor: '#f28c38'
        });
    } finally {
        hideLoadingSpinner();
    }
}

async function saveProduct(productData) {
    try {
        const url = currentEditId ?
            `/admin/products/edit/${currentEditId}` :
            `/admin/products/add`;
        const method = currentEditId ? 'POST' : 'POST';

        const formData = new FormData();
        formData.append('tenSanPham', productData.name);
        formData.append('maLoai', productData.categoryId);
        formData.append('thuongHieu', productData.brand);
        formData.append('giaBan', productData.price);
        formData.append('soLuong', productData.quantity);
        formData.append('moTa', productData.description);
        formData.append('chiPhi', productData.cost || '0');
        formData.append('giaNhap', productData.importPrice || '0');

        const hinhAnhUrl = document.getElementById('hinhAnhUrl').value;
        if (hinhAnhUrl) {
            formData.append('hinhAnhUrl', hinhAnhUrl);
        }
        const hinhAnhFile = document.getElementById('hinhAnh').files[0];
        if (hinhAnhFile) {
            formData.append('hinhAnh', hinhAnhFile);
        }

        const response = await fetch(url, {
            method: method,
            body: formData
        });

        if (response.ok) {
            // Reload data after successful save
            await loadProductsFromAPI();
            return {success: true};
        } else {
            const errorText = await response.text();
            throw new Error(errorText || 'Lỗi khi lưu sản phẩm');
        }

    } catch (error) {
        console.error('Error saving product:', error);
        return {success: false, message: error.message};
    }
}

async function deleteProductAPI(productId) {
    try {
        const response = await fetch(`/admin/products/delete/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        return data;

    } catch (error) {
        console.error('Error deleting product:', error);
        return {success: false, message: error.message};
    }
}

// Event Listeners
function initializeEventListeners() {
    // Add product button
    addProductBtn.addEventListener('click', function () {
        openProductModal();
    });

    // Product form submit
    productForm.addEventListener('submit', function (e) {
        e.preventDefault();
        handleFormSubmit();
    });

    // Search functionality
    searchInput.addEventListener('input', debounce(filterProducts, 300));

    // Filter functionality
    categoryFilter.addEventListener('change', filterProducts);
    statusFilter.addEventListener('change', filterProducts);
    resetFiltersBtn.addEventListener('click', resetFilters);

    // Select all checkbox
    selectAllCheckbox.addEventListener('change', handleSelectAll);

    // Bulk action buttons
    document.getElementById('bulkDeleteBtn').addEventListener('click', handleBulkDelete);
    document.getElementById('bulkUpdateStockBtn').addEventListener('click', handleBulkUpdateStock);
    document.getElementById('bulkExportBtn').addEventListener('click', handleBulkExport);

    // Export/Import buttons
    document.getElementById('exportBtn').addEventListener('click', handleExport);
    document.getElementById('importBtn').addEventListener('click', handleImport);
}

// Modal Functions
function openProductModal(productId = null) {
    const modalTitle = document.getElementById('productModalTitle');

    if (productId) {
        // Edit mode
        currentEditId = productId;
        const product = productsData.find(p => p.id === productId);

        modalTitle.textContent = 'Chỉnh sửa sản phẩm';

        // Fill form with product data
        document.getElementById('productName').value = product.name;
        document.getElementById('productCategory').value = product.categoryId;
        document.getElementById('productBrand').value = product.brand || '';
        document.getElementById('productCost').value = product.cost || '';
        document.getElementById('productImportPrice').value = product.importPrice || '';
        document.getElementById('productSellPrice').value = product.price;
        document.getElementById('productQuantity').value = product.quantity;
        document.getElementById('productStatus').value = product.status === 'out-of-stock' && product.quantity === 0 ? '0' : '1';
        document.getElementById('productDescription').value = product.description || '';
    } else {
        // Add mode
        currentEditId = null;
        modalTitle.textContent = 'Thêm sản phẩm mới';
        productForm.reset();
    }

    productModal.show();
}

// Form Handling
async function handleFormSubmit() {
    const formData = {
        name: document.getElementById('productName').value.trim(),
        categoryId: parseInt(document.getElementById('productCategory').value),
        brand: document.getElementById('productBrand').value.trim(),
        cost: parseFloat(document.getElementById('productCost').value) || 0,
        importPrice: parseFloat(document.getElementById('productImportPrice').value) || 0,
        price: parseFloat(document.getElementById('productSellPrice').value),
        quantity: parseInt(document.getElementById('productQuantity').value),
        description: document.getElementById('productDescription').value.trim()
    };

    // Validation
    if (!formData.name || !formData.categoryId || formData.price <= 0 || formData.quantity < 0) {
        Swal.fire({
            title: 'Lỗi!',
            text: 'Vui lòng điền đầy đủ thông tin bắt buộc!',
            icon: 'error',
            confirmButtonColor: '#f28c38'
        });
        return;
    }

    // Show loading
    const submitBtn = document.querySelector('#productForm button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang lưu...';
    submitBtn.disabled = true;

    try {
        const result = await saveProduct(formData);

        if (result.success) {
            productModal.hide();

            Swal.fire({
                title: 'Thành công!',
                text: currentEditId ? 'Sản phẩm đã được cập nhật.' : 'Sản phẩm mới đã được thêm.',
                icon: 'success',
                confirmButtonColor: '#f28c38'
            });
        } else {
            throw new Error(result.message || 'Lỗi khi lưu sản phẩm');
        }
    } catch (error) {
        Swal.fire({
            title: 'Lỗi!',
            text: error.message,
            icon: 'error',
            confirmButtonColor: '#f28c38'
        });
    } finally {
        // Restore button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Render Functions
function renderProductsTable() {
    productsTableBody.innerHTML = '';

    if (filteredProducts.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="9" class="text-center py-4">
                <i class="fas fa-box-open fa-3x text-muted mb-3"></i>
                <p class="text-muted">Không có sản phẩm nào được tìm thấy</p>
            </td>
        `;
        productsTableBody.appendChild(row);
        return;
    }

    filteredProducts.forEach(product => {
        const row = document.createElement('tr');

        // Determine status class and text
        let statusClass, statusText;
        switch (product.status) {
            case 'in-stock':
                statusClass = 'status-in-stock';
                statusText = 'Còn hàng';
                break;
            case 'low-stock':
                statusClass = 'status-low-stock';
                statusText = 'Sắp hết';
                break;
            case 'out-of-stock':
                statusClass = 'status-out-of-stock';
                statusText = 'Hết hàng';
                break;
            default:
                statusClass = 'status-in-stock';
                statusText = 'Còn hàng';
        }

        // Determine badge color for category
        let badgeClass = getBadgeClassByCategory(product.category);

        // Determine quantity badge color
        let qtyBadgeClass = 'bg-success';
        if (product.quantity === 0) {
            qtyBadgeClass = 'bg-danger';
        } else if (product.quantity <= 10) {
            qtyBadgeClass = 'bg-warning';
        }

        row.innerHTML = `
            <td><input type="checkbox" class="form-check-input row-checkbox" data-id="${product.id}"></td>
            <td>#SP${product.id.toString().padStart(3, '0')}</td>
            <td>
                <div class="d-flex align-items-center">
                    <img src="https://via.placeholder.com/40x40?text=${encodeURIComponent(product.name.charAt(0))}" class="product-thumb me-2" alt="">
                    <span>${product.name}</span>
                </div>
            </td>
            <td><span class="badge ${badgeClass}">${product.category}</span></td>
            <td>${product.brand || '-'}</td>
            <td class="fw-bold text-primary">${formatCurrency(product.price)}</td>
            <td>
                <span class="badge ${qtyBadgeClass}">${product.quantity}</span>
            </td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-sm btn-outline-info view-btn" onclick="viewProduct(${product.id})" title="Xem chi tiết">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-primary edit-btn" onclick="editProduct(${product.id})" title="Chỉnh sửa">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-btn" onclick="deleteProduct(${product.id})" title="Xóa">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;

        productsTableBody.appendChild(row);
    });

    // Add event listeners for row checkboxes
    document.querySelectorAll('.row-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateBulkActions);
    });
}

// Filter Functions
function filterProducts() {
    const searchTerm = searchInput.value.toLowerCase();
    const categoryValue = categoryFilter.value;
    const statusValue = statusFilter.value;

    filteredProducts = productsData.filter(product => {
        const matchesSearch = !searchTerm ||
            product.name.toLowerCase().includes(searchTerm) ||
            (product.brand && product.brand.toLowerCase().includes(searchTerm)) ||
            (product.description && product.description.toLowerCase().includes(searchTerm));

        const matchesCategory = !categoryValue || product.categoryId.toString() === categoryValue;

        const matchesStatus = !statusValue || product.status === statusValue;

        return matchesSearch && matchesCategory && matchesStatus;
    });

    renderProductsTable();
}

function resetFilters() {
    searchInput.value = '';
    categoryFilter.value = '';
    statusFilter.value = '';
    filteredProducts = [...productsData];
    renderProductsTable();
}

// Product Actions
function viewProduct(productId) {
    const product = productsData.find(p => p.id === productId);
    if (!product) return;

    Swal.fire({
        title: product.name,
        html: `
            <div class="text-start">
                <div class="row">
                    <div class="col-6">
                        <img src="https://via.placeholder.com/200x200?text=${encodeURIComponent(product.name.charAt(0))}" 
                             class="img-fluid rounded mb-3" alt="">
                    </div>
                    <div class="col-6">
                        <p><strong>Loại:</strong> ${product.category}</p>
                        <p><strong>Thương hiệu:</strong> ${product.brand || 'Không có'}</p>
                        <p><strong>Giá bán:</strong> ${formatCurrency(product.price)}</p>
                        <p><strong>Số lượng:</strong> ${product.quantity}</p>
                        <p><strong>Trạng thái:</strong> 
                            <span class="badge ${product.status === 'in-stock' ? 'bg-success' :
            product.status === 'low-stock' ? 'bg-warning' : 'bg-danger'}">
                                ${product.status === 'in-stock' ? 'Còn hàng' :
            product.status === 'low-stock' ? 'Sắp hết' : 'Hết hàng'}
                            </span>
                        </p>
                    </div>
                </div>
                <div class="mt-3">
                    <strong>Mô tả:</strong>
                    <p>${product.description || 'Không có mô tả'}</p>
                </div>
            </div>
        `,
        width: '600px',
        confirmButtonColor: '#f28c38'
    });
}

function editProduct(productId) {
    openProductModal(productId);
}

async function deleteProduct(productId) {
    const product = productsData.find(p => p.id === productId);
    if (!product) return;

    const result = await Swal.fire({
        title: 'Xác nhận xóa',
        text: `Bạn có chắc chắn muốn xóa sản phẩm "${product.name}"?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Xóa',
        cancelButtonText: 'Hủy',
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d'
    });

    if (result.isConfirmed) {
        try {
            const deleteResult = await deleteProductAPI(productId);

            if (deleteResult.success) {
                await loadProductsFromAPI(); // Reload data

                Swal.fire({
                    title: 'Đã xóa!',
                    text: 'Sản phẩm đã được xóa thành công.',
                    icon: 'success',
                    confirmButtonColor: '#f28c38'
                });
            } else {
                throw new Error(deleteResult.message || 'Lỗi khi xóa sản phẩm');
            }
        } catch (error) {
            Swal.fire({
                title: 'Lỗi!',
                text: error.message,
                icon: 'error',
                confirmButtonColor: '#f28c38'
            });
        }
    }
}

// Bulk Actions
function handleSelectAll() {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    updateBulkActions();
}

function updateBulkActions() {
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
    const allCheckboxes = document.querySelectorAll('.row-checkbox');

    // Update select all checkbox
    if (checkedBoxes.length === 0) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = false;
    } else if (checkedBoxes.length === allCheckboxes.length) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = true;
    } else {
        selectAllCheckbox.indeterminate = true;
    }

    // Show/hide bulk actions
    if (checkedBoxes.length > 0) {
        bulkActions.style.display = 'block';
    } else {
        bulkActions.style.display = 'none';
    }
}

function handleBulkDelete() {
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
    if (checkedBoxes.length === 0) return;

    Swal.fire({
        title: 'Chức năng chưa hoàn thiện',
        text: 'Tính năng xóa hàng loạt sẽ được cập nhật trong phiên bản tiếp theo.',
        icon: 'info',
        confirmButtonColor: '#f28c38'
    });
}

function handleBulkUpdateStock() {
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
    if (checkedBoxes.length === 0) return;

    Swal.fire({
        title: 'Chức năng chưa hoàn thiện',
        text: 'Tính năng cập nhật số lượng hàng loạt sẽ được cập nhật trong phiên bản tiếp theo.',
        icon: 'info',
        confirmButtonColor: '#f28c38'
    });
}

function handleBulkExport() {
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
    if (checkedBoxes.length === 0) return;

    Swal.fire({
        title: 'Xuất dữ liệu',
        text: `Đã xuất ${checkedBoxes.length} sản phẩm ra file Excel.`,
        icon: 'success',
        confirmButtonColor: '#f28c38'
    });
}

// Export/Import Functions
function handleExport() {
    Swal.fire({
        title: 'Xuất dữ liệu',
        text: 'Đã xuất toàn bộ sản phẩm ra file Excel.',
        icon: 'success',
        confirmButtonColor: '#f28c38'
    });
}

function handleImport() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.xlsx,.xls,.csv';

    fileInput.onchange = function (e) {
        const file = e.target.files[0];
        if (file) {
            Swal.fire({
                title: 'Nhập dữ liệu',
                text: `Đã nhập dữ liệu từ file: ${file.name}`,
                icon: 'success',
                confirmButtonColor: '#f28c38'
            });
        }
    };

    fileInput.click();
}

// Statistics Update
function updateStatistics() {
    const total = productsData.length;
    const inStock = productsData.filter(p => p.status === 'in-stock').length;
    const lowStock = productsData.filter(p => p.status === 'low-stock').length;
    const outOfStock = productsData.filter(p => p.status === 'out-of-stock').length;

    document.getElementById('totalProducts').textContent = total;
    document.getElementById('inStockProducts').textContent = inStock;
    document.getElementById('lowStockProducts').textContent = lowStock;
    document.getElementById('outOfStockProducts').textContent = outOfStock;
}

// Utility Functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function getCategoryIdByName(categoryName) {
    const categoryMap = {
        'Thức ăn cho chó': 1,
        'Thức ăn cho mèo': 2,
        'Phụ kiện cho chó': 3,
        'Phụ kiện cho mèo': 4,
        'Thuốc & Vitamin': 5
    };
    return categoryMap[categoryName] || 1;
}

function getBadgeClassByCategory(category) {
    const badgeMap = {
        'Thức ăn cho chó': 'bg-primary',
        'Thức ăn cho mèo': 'bg-info',
        'Phụ kiện cho chó': 'bg-secondary',
        'Phụ kiện cho mèo': 'bg-dark',
        'Thuốc & Vitamin': 'bg-warning'
    };
    return badgeMap[category] || 'bg-primary';
}

function getStatusFromQuantity(quantity) {
    if (quantity === 0) {
        return 'out-of-stock';
    } else if (quantity <= 10) {
        return 'low-stock';
    } else {
        return 'in-stock';
    }
}

function showLoadingSpinner() {
    // Có thể thêm spinner loading
    console.log('Loading...');
}

function hideLoadingSpinner() {
    // Ẩn spinner loading
    console.log('Loading completed');
}