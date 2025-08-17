from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from services import CartService, OrderService, ProductService

# Tạo blueprint cho cart
cart_bp = Blueprint('cart', __name__)


def require_login():
    """Helper function kiểm tra đăng nhập"""
    if 'user_id' not in session:
        return False
    return True


@cart_bp.route('/cart')
def view_cart():
    """Xem giỏ hàng"""
    if not require_login():
        flash('Vui lòng đăng nhập để xem giỏ hàng!', 'warning')
        return redirect(url_for('auth.login', next=request.url))

    try:
        cart_items = CartService.get_cart_items(session['user_id'])
        total = sum(item['price'] * item['quantity'] for item in cart_items)

        return render_template('cart.html',
                               cart_items=cart_items,
                               total=total,
                               cart_count=len(cart_items))
    except Exception as e:
        flash(f'Lỗi khi tải giỏ hàng: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@cart_bp.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    """Thêm sản phẩm vào giỏ hàng (AJAX)"""
    if not require_login():
        return jsonify({
            'success': False,
            'message': 'Vui lòng đăng nhập!',
            'redirect': url_for('auth.login')
        }), 401

    try:
        # Lấy dữ liệu từ request
        if request.is_json:
            data = request.get_json()
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
        else:
            product_id = request.form.get('product_id')
            quantity = int(request.form.get('quantity', 1))

        # Validate input
        if not product_id:
            return jsonify({
                'success': False,
                'message': 'Thiếu thông tin sản phẩm!'
            }), 400

        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Dữ liệu không hợp lệ!'
            }), 400

        if quantity <= 0:
            return jsonify({
                'success': False,
                'message': 'Số lượng phải lớn hơn 0!'
            }), 400

        # Thêm vào giỏ hàng
        success, message = CartService.add_to_cart(session['user_id'], product_id, quantity)

        if success:
            # Lấy số lượng item trong giỏ hàng để cập nhật UI
            cart_items = CartService.get_cart_items(session['user_id'])
            cart_count = len(cart_items)

            return jsonify({
                'success': True,
                'message': message,
                'cart_count': cart_count
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@cart_bp.route('/update-cart', methods=['POST'])
def update_cart():
    """Cập nhật số lượng sản phẩm trong giỏ hàng"""
    if not require_login():
        return jsonify({
            'success': False,
            'message': 'Vui lòng đăng nhập!'
        }), 401

    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        if not product_id:
            return jsonify({
                'success': False,
                'message': 'Thiếu thông tin sản phẩm!'
            }), 400

        # Validate quantity
        try:
            quantity = int(quantity)
            if quantity < 0:
                return jsonify({
                    'success': False,
                    'message': 'Số lượng không hợp lệ!'
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Số lượng phải là số!'
            }), 400

        # Nếu quantity = 0 thì xóa khỏi giỏ hàng
        if quantity == 0:
            success, message = CartService.remove_from_cart(session['user_id'], product_id)
            item_subtotal = 0
        else:
            success, message = CartService.update_cart_item(session['user_id'], product_id, quantity)
            # THÊM: Tính subtotal cho item này
            product = ProductService.get_product_by_id(product_id)
            item_subtotal = float(product['price']) * quantity if product else 0

        if success:
            # Tính lại total
            cart_items = CartService.get_cart_items(session['user_id'])
            total = sum(item['price'] * item['quantity'] for item in cart_items)

            return jsonify({
                'success': True,
                'message': message,
                'total': total,
                'cart_count': len(cart_items),
                'item_subtotal': item_subtotal  # THÊM DÒNG NÀY
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500

@cart_bp.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    """Xóa sản phẩm khỏi giỏ hàng"""
    if not require_login():
        return jsonify({
            'success': False,
            'message': 'Vui lòng đăng nhập!'
        }), 401

    try:
        data = request.get_json()
        product_id = data.get('product_id')

        if not product_id:
            return jsonify({
                'success': False,
                'message': 'Thiếu thông tin sản phẩm!'
            }), 400

        success, message = CartService.remove_from_cart(session['user_id'], product_id)

        if success:
            # Tính lại total
            cart_items = CartService.get_cart_items(session['user_id'])
            total = sum(item['price'] * item['quantity'] for item in cart_items)

            return jsonify({
                'success': True,
                'message': message,
                'total': total,
                'cart_count': len(cart_items)
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@cart_bp.route('/clear-cart', methods=['POST'])
def clear_cart():
    """Xóa toàn bộ giỏ hàng"""
    if not require_login():
        return jsonify({
            'success': False,
            'message': 'Vui lòng đăng nhập!'
        }), 401

    try:
        success, message = CartService.clear_cart(session['user_id'])

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'total': 0,
                'cart_count': 0
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500


@cart_bp.route('/checkout')
def checkout():
    """Trang thanh toán"""
    if not require_login():
        flash('Vui lòng đăng nhập để thanh toán!', 'warning')
        return redirect(url_for('auth.login', next=request.url))

    try:
        cart_items = CartService.get_cart_items(session['user_id'])

        if not cart_items:
            flash('Giỏ hàng trống! Vui lòng thêm sản phẩm trước khi thanh toán.', 'warning')
            return redirect(url_for('product.list_products'))

        total = sum(item['price'] * item['quantity'] for item in cart_items)

        # TODO: Lấy danh sách địa chỉ của user từ database
        # addresses = AddressService.get_user_addresses(session['user_id'])

        return render_template('checkout.html',
                               cart_items=cart_items,
                               total=total,
                               # addresses=addresses
                               )
    except Exception as e:
        flash(f'Lỗi khi tải trang thanh toán: {str(e)}', 'error')
        return redirect(url_for('cart.view_cart'))


@cart_bp.route('/place-order', methods=['POST'])
def place_order():
    """Đặt hàng"""
    if not require_login():
        return jsonify({
            'success': False,
            'message': 'Vui lòng đăng nhập!'
        }), 401

    try:
        # Lấy thông tin từ form
        ma_dia_chi = request.form.get('address_id') or 1  # Default địa chỉ
        ghi_chu = request.form.get('note', '')

        # Tạo đơn hàng
        success, result = OrderService.create_order(session['user_id'], ma_dia_chi)

        if success:
            flash(f'Đặt hàng thành công! Mã đơn hàng: {result}', 'success')
            return redirect(url_for('cart.order_success', order_id=result))
        else:
            flash(result, 'error')
            return redirect(url_for('cart.checkout'))

    except Exception as e:
        flash(f'Lỗi khi đặt hàng: {str(e)}', 'error')
        return redirect(url_for('cart.checkout'))


@cart_bp.route('/order-success/<int:order_id>')
def order_success(order_id):
    """Trang đặt hàng thành công"""
    if not require_login():
        flash('Vui lòng đăng nhập!', 'warning')
        return redirect(url_for('auth.login'))

    return render_template('order_success.html', order_id=order_id)


@cart_bp.route('/api/cart-count')
def api_cart_count():
    """API lấy số lượng item trong giỏ hàng"""
    if not require_login():
        return jsonify({'count': 0})

    try:
        cart_items = CartService.get_cart_items(session['user_id'])
        return jsonify({
            'count': len(cart_items),
            'total_quantity': sum(item['quantity'] for item in cart_items)
        })
    except Exception as e:
        return jsonify({'count': 0})