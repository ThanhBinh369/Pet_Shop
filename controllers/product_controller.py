from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from services import ProductService

# Tạo blueprint cho products
product_bp = Blueprint('product', __name__)


@product_bp.route('/products')
def list_products():
    """Danh sách tất cả sản phẩm"""

    # DEBUG: Kiểm tra dữ liệu
    from models.models import SanPham, Loai
    print("=== DEBUG INFO ===")
    san_phams = SanPham.query.all()
    print(f"Tổng số sản phẩm trong DB: {len(san_phams)}")
    for sp in san_phams[:3]:  # In 3 sản phẩm đầu
        print(f"ID: {sp.MaSanPham}, Tên: {sp.TenSanPham}, Trạng thái: {sp.TrangThai}")

    loais = Loai.query.all()
    print(f"Tổng số loại: {len(loais)}")
    for loai in loais:
        print(f"Loại ID: {loai.MaLoai}, Tên: {loai.TenLoai}")
    print("=== END DEBUG ===")

    # Lấy parameters từ query string
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'name')  # name, price_low, price_high

    products = ProductService.get_all_products()

    # Filter theo category
    if category:
        products = [p for p in products if p['type'].lower() == category.lower()]

    # Filter theo search
    if search:
        search_lower = search.lower()
        products = [p for p in products if
                    search_lower in p['name'].lower() or
                    search_lower in p['brand'].lower() or
                    search_lower in p['description'].lower()]

    # Sorting
    if sort_by == 'price_low':
        products.sort(key=lambda x: x['price'])
    elif sort_by == 'price_high':
        products.sort(key=lambda x: x['price'], reverse=True)
    else:  # sort by name
        products.sort(key=lambda x: x['name'])

    # SỬA: Đổi từ 'products/list.html' thành 'products.html'
    return render_template('products.html',
                           products=products,
                           current_category=category,
                           current_search=search,
                           current_sort=sort_by)


@product_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Chi tiết sản phẩm"""
    product = ProductService.get_product_by_id(product_id)

    if not product:
        flash('Sản phẩm không tồn tại!', 'error')
        return redirect(url_for('product.list_products'))

    # Lấy sản phẩm liên quan (cùng loại)
    all_products = ProductService.get_all_products()
    related_products = [p for p in all_products
                        if p['type'] == product['type'] and p['id'] != product_id][:4]

    # SỬA: Đổi từ 'products/detail.html' thành 'detail_product.html'
    return render_template('detail_product.html',
                           product=product,
                           related_products=related_products)


@product_bp.route('/api/products')
def api_products():
    """API lấy danh sách sản phẩm (JSON)"""
    try:
        category = request.args.get('category', '')
        search = request.args.get('search', '')

        products = ProductService.get_all_products()

        # Filter theo category
        if category:
            products = [p for p in products if p['type'].lower() == category.lower()]

        # Filter theo search - Improved fuzzy search
        if search:
            search_lower = search.lower().strip()
            search_words = search_lower.split()  # Tách thành từng từ

            filtered_products = []
            for product in products:
                # Tạo chuỗi tìm kiếm từ tất cả thông tin sản phẩm
                searchable_text = f"{product['name']} {product.get('brand', '')} {product.get('description', '')} {product['type']}".lower()

                # Tính điểm matching
                score = 0

                # Kiểm tra từng từ khóa
                for word in search_words:
                    if word in searchable_text:
                        # Bonus điểm nếu từ khóa xuất hiện trong tên
                        if word in product['name'].lower():
                            score += 3
                        # Bonus điểm nếu từ khóa xuất hiện trong brand
                        elif word in product.get('brand', '').lower():
                            score += 2
                        # Điểm thường nếu xuất hiện trong mô tả hoặc type
                        else:
                            score += 1

                # Kiểm tra tìm kiếm mờ (fuzzy search) cho từ khóa dài
                if len(search_lower) > 3:
                    if any(word in search_lower for word in searchable_text.split() if len(word) > 2):
                        score += 1

                # Nếu có điểm > 0 thì thêm vào kết quả
                if score > 0:
                    product['search_score'] = score
                    filtered_products.append(product)

            # Sắp xếp theo điểm cao nhất
            products = sorted(filtered_products, key=lambda x: x.get('search_score', 0), reverse=True)

            # Xóa search_score khỏi kết quả trả về
            for product in products:
                product.pop('search_score', None)

        return jsonify({
            'success': True,
            'products': products,
            'total': len(products)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@product_bp.route('/api/product/<int:product_id>')
def api_product_detail(product_id):
    """API lấy chi tiết sản phẩm (JSON)"""
    try:
        product = ProductService.get_product_by_id(product_id)

        if not product:
            return jsonify({
                'success': False,
                'message': 'Sản phẩm không tồn tại'
            }), 404

        return jsonify({
            'success': True,
            'product': product
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@product_bp.route('/categories')
def categories():
    """Danh sách các danh mục sản phẩm"""
    products = ProductService.get_all_products()

    # Lấy danh sách các loại sản phẩm
    categories = {}
    for product in products:
        category = product['type']
        if category not in categories:
            categories[category] = {
                'name': category.title(),
                'count': 0,
                'products': []
            }
        categories[category]['count'] += 1
        categories[category]['products'].append(product)

    return render_template('products/categories.html', categories=categories)