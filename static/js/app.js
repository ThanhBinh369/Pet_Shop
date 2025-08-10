$(document).ready(function() {
    // Filter products
    function filterProducts() {
        let petType = $('#pet-type-filter').val();
        let brand = $('#brand-filter').val();
        let price = $('#price-filter').val();

        $('.product-item').each(function() {
            let $item = $(this);
            let show = true;

            if (petType && $item.data('type') !== petType) {
                show = false;
            }
            if (brand && $item.data('brand') !== brand) {
                show = false;
            }
            if (price) {
                let [min, max] = price.split('-').map(Number);
                let itemPrice = $item.data('price');
                if (itemPrice < min || (max && itemPrice > max)) {
                    show = false;
                }
            }

            $item.toggle(show);
        });
    }

    $('#pet-type-filter, #brand-filter, #price-filter').change(filterProducts);

    // Add to cart
    $('.add-to-cart').click(function() {
        let productId = $(this).data('id');
        Swal.fire({
            title: 'Success!',
            text: 'Product added to cart!',
            icon: 'success',
            timer: 1500
        });
    });

    // Contact form submission
    $('#contact-form').submit(function(e) {
        e.preventDefault();
        Swal.fire({
            title: 'Success!',
            text: 'Your message has been sent!',
            icon: 'success',
            timer: 1500
        });
        $(this)[0].reset();
    });
});