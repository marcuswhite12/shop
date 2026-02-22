from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from products.models import Product, Variant


# =========================
# Helpers
# =========================

def get_cart(request):
    cart = request.session.get('cart')
    if cart is None:
        request.session['cart'] = {}
        request.session.modified = True
        return {}
    return cart


def save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


# =========================
# Add to cart
# =========================

@require_POST
def cart_add(request, product_id):
    cart = get_cart(request)

    product = get_object_or_404(Product, id=product_id, is_active=True)

    variant_id = request.POST.get("variant_id")
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        messages.error(request, "Некорректное количество")
        return redirect("product_detail", slug=product.slug)

    if quantity < 1:
        messages.error(request, "Количество должно быть больше 0")
        return redirect("product_detail", slug=product.slug)

    variant = None

    if variant_id:
        try:
            variant_id = int(variant_id)
        except (TypeError, ValueError):
            messages.error(request, "Некорректный вариант товара")
            return redirect("product_detail", slug=product.slug)

        variant = Variant.objects.filter(
            id=variant_id,
            product_id=product.id
        ).first()

        if not variant:
            messages.error(request, "Вариант товара не найден")
            return redirect("product_detail", slug=product.slug)

        if variant.stock < quantity:
            messages.error(
                request,
                f"Недостаточно на складе: только {variant.stock} шт."
            )
            return redirect("product_detail", slug=product.slug)

        key = f"variant_{variant.id}"

    else:
        # если у товара есть варианты — без варианта нельзя
        if product.variants.count() > 0:
            messages.error(request, "Выберите вариант товара")
            return redirect("product_detail", slug=product.slug)

        key = f"product_{product.id}"

    # увеличение количества
    if key in cart:
        new_quantity = cart[key]["quantity"] + quantity

        if variant and variant.stock < new_quantity:
            messages.error(
                request,
                f"Недостаточно на складе: только {variant.stock} шт."
            )
            return redirect("product_detail", slug=product.slug)

        cart[key]["quantity"] = new_quantity
    else:
        cart[key] = {
            "product_id": product.id,
            "variant_id": variant.id if variant else None,
            "quantity": quantity,
        }

    save_cart(request, cart)
    messages.success(request, "Товар добавлен в корзину")

    return redirect("product_detail", slug=product.slug)


# =========================
# Cart detail (production-safe)
# =========================

def cart_detail(request):
    cart = get_cart(request)

    items = []
    total = 0
    cart_changed = False

    if not cart:
        return render(request, "cart/cart_detail.html", {
            "cart_items": [],
            "total": 0,
            "currency_symbol": "сом",
        })

    product_ids = {item["product_id"] for item in cart.values()}
    variant_ids = {
        item["variant_id"]
        for item in cart.values()
        if item.get("variant_id")
    }

    products = {
        p.id: p
        for p in Product.objects
        .filter(id__in=product_ids, is_active=True)
        .prefetch_related("images")
    }

    variants = {
        v.id: v
        for v in Variant.objects
        .filter(id__in=variant_ids)
        .select_related("product")
    }

    for key, item in list(cart.items()):
        product = products.get(item["product_id"])

        if not product:
            cart.pop(key)
            cart_changed = True
            continue

        variant = None
        stock = None

        variant_id = item.get("variant_id")

        if variant_id:
            variant = variants.get(variant_id)

            if not variant or variant.stock <= 0:
                cart.pop(key)
                cart_changed = True
                continue

            stock = variant.stock

        quantity = int(item.get("quantity", 1))

        if stock is not None and quantity > stock:
            quantity = stock
            cart[key]["quantity"] = stock
            cart_changed = True

        price = product.price
        subtotal = price * quantity
        total += subtotal

        main_image = product.images.first()

        if variant:
            display_name = f"{product.name} ({variant.size or ''} {variant.color or ''})".strip()
        else:
            display_name = product.name

        items.append({
            "key": key,
            "display_name": display_name,
            "quantity": quantity,
            "price": price,
            "subtotal": subtotal,
            "main_image": main_image.image.url if main_image else None,
            "stock": stock if stock is not None else 9999,
        })

    if cart_changed:
        save_cart(request, cart)

    return render(request, "cart/cart_detail.html", {
        "cart_items": items,
        "total": total,
        "currency_symbol": "сом",
    })


# =========================
# Update quantity
# =========================

@require_POST
def cart_update(request):
    cart = get_cart(request)
    key = request.POST.get("key")

    if not key or key not in cart:
        return redirect("cart_detail")

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        return redirect("cart_detail")

    if quantity < 1:
        cart.pop(key, None)
        save_cart(request, cart)
        return redirect("cart_detail")

    item = cart[key]

    product = Product.objects.filter(
        id=item.get("product_id"),
        is_active=True
    ).first()

    if not product:
        cart.pop(key)
        save_cart(request, cart)
        return redirect("cart_detail")

    variant_id = item.get("variant_id")

    if variant_id:
        variant = Variant.objects.filter(
            id=variant_id,
            product_id=product.id
        ).first()

        if not variant or variant.stock <= 0:
            cart.pop(key)
            save_cart(request, cart)
            return redirect("cart_detail")

        if quantity > variant.stock:
            quantity = variant.stock

    cart[key]["quantity"] = quantity
    save_cart(request, cart)

    return redirect("cart_detail")


# =========================
# Remove
# =========================

@require_POST
def cart_remove(request):
    cart = get_cart(request)
    key = request.POST.get("key")

    if key in cart:
        cart.pop(key)
        save_cart(request, cart)

    return redirect("cart_detail")


@require_POST
def cart_clear(request):
    save_cart(request, {})
    return redirect("cart_detail")
