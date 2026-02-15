from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from products.models import Product, Variant


# -----------------------
# Helpers
# -----------------------

def get_cart(request):
    return request.session.get('cart', {})


def save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


# -----------------------
# Add to cart
# -----------------------

@require_POST
def cart_add(request, product_id):
    cart = get_cart(request)

    product = get_object_or_404(Product, id=product_id, is_active=True)
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        messages.error(request, "Некорректное количество")
        return redirect('product_detail', slug=product.slug)

    if variant_id:
        variant = get_object_or_404(
            Variant,
            id=variant_id,
            product_id=product_id
        )

        if variant.stock < quantity:
            messages.error(
                request,
                f'Недостаточно на складе: только {variant.stock} шт.'
            )
            return redirect('product_detail', slug=product.slug)

        key = f'variant_{variant.id}'
        display_name = f"{product.name} ({variant.size or ''} {variant.color or ''})".strip()

    else:
        if product.variants.exists():
            messages.error(request, "Выберите вариант товара")
            return redirect('product_detail', slug=product.slug)

        key = f'product_{product.id}'
        display_name = product.name

    # Добавление / увеличение
    if key in cart:
        new_quantity = cart[key]['quantity'] + quantity

        if variant_id:
            if variant.stock < new_quantity:
                messages.error(
                    request,
                    f'Недостаточно на складе: только {variant.stock} шт.'
                )
                return redirect('product_detail', slug=product.slug)

        cart[key]['quantity'] = new_quantity
    else:
        cart[key] = {
            'quantity': quantity,
            'product_id': product.id,
            'variant_id': variant_id,
            'display_name': display_name,
        }

    save_cart(request, cart)
    messages.success(request, "Товар добавлен в корзину")
    return redirect('product_detail', slug=product.slug)



# -----------------------
# Cart detail
# -----------------------

def cart_detail(request):
    cart = get_cart(request)
    items = []
    total = 0

    for key, item in cart.items():

        product = get_object_or_404(Product, id=item['product_id'])
        variant = None

        if item.get('variant_id'):
            variant = get_object_or_404(Variant, id=item['variant_id'])
            stock = variant.stock
        else:
            stock = 9999  # если простой товар без ограничений

        main_image = product.images.first()
        price = product.price
        subtotal = price * item['quantity']
        total += subtotal

        items.append({
            'key': key,
            'display_name': item['display_name'],
            'quantity': item['quantity'],
            'price': price,
            'subtotal': subtotal,
            'main_image': main_image.image.url if main_image else None,
            'stock': stock,  # ← важно
        })

    return render(request, 'cart/cart_detail.html', {
        'cart_items': items,
        'total': total,
        'currency_symbol': 'сом',
    })


# -----------------------
# Update quantity
# -----------------------
@require_POST
def cart_update(request):
    cart = get_cart(request)
    key = request.POST.get('key')

    if not key or key not in cart:
        messages.error(request, "Товар не найден в корзине")
        return redirect('cart_detail')

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        messages.error(request, "Некорректное количество")
        return redirect('cart_detail')

    if quantity < 1:
        cart.pop(key, None)
        save_cart(request, cart)
        return redirect('cart_detail')

    item = cart[key]

    # Проверка stock
    if item.get('variant_id'):
        variant = get_object_or_404(Variant, id=item['variant_id'])

        if quantity > variant.stock:
            messages.error(
                request,
                f'Можно добавить максимум {variant.stock} шт.'
            )
            return redirect('cart_detail')

    cart[key]['quantity'] = quantity
    save_cart(request, cart)

    messages.success(request, "Количество обновлено")
    return redirect('cart_detail')



# -----------------------
# Remove item
# -----------------------

@require_POST
def cart_remove(request):
    cart = get_cart(request)
    key = request.POST.get('key')

    if key and key in cart:
        cart.pop(key, None)
        save_cart(request, cart)
        messages.success(request, "Товар удалён из корзины")

    return redirect('cart_detail')

@require_POST
def cart_clear(request):
    request.session['cart'] = {}
    request.session.modified = True
    messages.success(request, "Корзина очищена")
    return redirect('cart_detail')
