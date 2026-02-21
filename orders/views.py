from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404

from cart.views import get_cart, save_cart
from products.models import Variant, Product
from .models import Order, OrderItem
from .forms import OrderCreateForm
from django.contrib.auth.decorators import login_required

# авто отмена просроченных товаров
# for order in Order.objects.filter(status=Order.STATUS_NEW):
#     order.auto_cancel_if_expired()


@login_required
def order_create(request):
    cart = get_cart(request)

    if not cart:
        messages.error(request, 'Корзина пуста')
        print("REDIRECT REASON: ...")

        return redirect('cart_detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST, user=request.user)

        if form.is_valid():
            with transaction.atomic():

                # Собираем variant_ids
                variant_ids = [
                    item['variant_id']
                    for item in cart.values()
                    if item.get('variant_id')
                ]

                # LOCK variants
                locked_variants = {
                    v.id: v
                    for v in Variant.objects.select_related('product')
                    .filter(id__in=variant_ids)
                    .select_for_update()
                }

                total = 0
                order_items_data = []

                print("CART CONTENT:", cart)

                for key, item in cart.items():

                    quantity = int(item['quantity'])

                    if quantity <= 0 or quantity > 100:
                        messages.error(request, 'Некорректное количество')
                        print("REDIRECT REASON: ...")
                        return redirect('cart_detail')

                    if item.get('variant_id'):
                        variant = locked_variants.get(item['variant_id'])

                        if not variant:
                            messages.error(request, 'Товар больше недоступен')
                            print("REDIRECT REASON: ...")
                            return redirect('cart_detail')

                        if variant.stock < quantity:
                            messages.error(
                                request,
                                f'Недостаточно "{variant.product.name}" на складе'
                            )
                            print("REDIRECT REASON: ...")
                            return redirect('cart_detail')

                        price = variant.product.price

                        # списание stock
                        Variant.objects.filter(id=variant.id).update(
                            stock=F('stock') - quantity
                        )

                        product = variant.product

                    else:
                        product = get_object_or_404(
                            Product,
                            id=item['product_id'],
                            is_active=True
                        )
                        price = product.price
                        variant = None

                    total += price * quantity

                    variant_description = ""

                    if variant:
                        parts = []
                        if variant.size:
                            parts.append(str(variant.size))
                        if variant.color:
                            parts.append(str(variant.color))
                        variant_description = " / ".join(parts)

                    order_items_data.append({
                        'product': product,
                        'variant': variant,
                        'product_name': product.name,
                        'variant_description': variant_description,
                        'quantity': quantity,
                        'price': price,
                    })

                print("ITEM:", item)
                print("QUANTITY:", quantity)
                print("VARIANT ID:", item.get('variant_id'))

                # создаём заказ
                order = form.save(commit=False)
                order.user = request.user
                order.total_price = total
                order.save()

                # создаём items
                OrderItem.objects.bulk_create([
                    OrderItem(order=order, **data)
                    for data in order_items_data
                ])

                # очищаем корзину
                save_cart(request, {})

                print("REDIRECT REASON: ...")

                return redirect('order_success', order_id=order.id)

    else:
        form = OrderCreateForm(user=request.user)

    return render(request, 'orders/order_create.html', {'form': form})


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})


@login_required
def order_list(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    return render(request, "orders/order_list.html", {
        "orders": orders
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__variant", "items__product"),
        id=order_id,
        user=request.user
    )

    return render(request, "orders/order_detail.html", {
        "order": order
    })