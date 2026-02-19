from django.contrib import admin
from django.contrib import messages
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False

    readonly_fields = [
        'product',
        'variant',
        'quantity',
        'price',
    ]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'created_at',
        'name',
        'phone',
        'total_price',
        'status'
    ]

    list_filter = ['status', 'created_at']
    search_fields = ['id', 'name', 'phone', 'email']
    inlines = [OrderItemInline]

    # ВСЕ поля readonly
    readonly_fields = [
        'created_at',
        'user',
        'name',
        'phone',
        'email',
        'address',
        'comment',
        'total_price',
        'status',
    ]

    fields = [
        'created_at',
        'status',
        'user',
        'name',
        'phone',
        'email',
        'address',
        'comment',
        'total_price',
    ]

    actions = [
        'mark_as_shipped',
        'cancel_orders'
    ]

    # ❗ Запрещаем удаление оплаченных и отправленных
    def has_delete_permission(self, request, obj=None):
        if obj and obj.status in ['paid', 'shipped']:
            return False
        return True

    # ===== ACTIONS =====

    def mark_as_paid(self, request, queryset):
        for order in queryset:
            try:
                order.mark_paid()
            except Exception as e:
                self.message_user(
                    request,
                    f"Ошибка в заказе #{order.id}: {e}",
                    level=messages.ERROR
                )
        self.message_user(request, "Выбранные заказы отмечены как оплаченные.")

    mark_as_paid.short_description = "Отметить как оплаченный"

    def mark_as_shipped(self, request, queryset):
        for order in queryset:
            try:
                order.mark_shipped()
            except Exception as e:
                self.message_user(
                    request,
                    f"Ошибка в заказе #{order.id}: {e}",
                    level=messages.ERROR
                )
        self.message_user(request, "Выбранные заказы отмечены как отправленные.")

    mark_as_shipped.short_description = "Отметить как отправленный"

    def cancel_orders(self, request, queryset):
        for order in queryset:
            try:
                order.cancel()
            except Exception as e:
                self.message_user(
                    request,
                    f"Ошибка в заказе #{order.id}: {e}",
                    level=messages.ERROR
                )
        self.message_user(request, "Выбранные заказы отменены.")

    cancel_orders.short_description = "Отменить заказ (с возвратом stock)"
