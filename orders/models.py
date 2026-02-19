from django.db import models, transaction
from django.db.models import F
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta



User = get_user_model()


class Order(models.Model):
    PAYMENT_TIMEOUT_MINUTES = 15

    STATUS_NEW = 'new'
    STATUS_PAID = 'paid'
    STATUS_SHIPPED = 'shipped'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Новый'),
        (STATUS_PAID, 'Оплачен'),
        (STATUS_SHIPPED, 'Отправлен'),
        (STATUS_CANCELLED, 'Отменён'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    ALLOWED_TRANSITIONS = {
        STATUS_NEW: [STATUS_PAID, STATUS_CANCELLED],
        STATUS_PAID: [STATUS_SHIPPED, STATUS_CANCELLED],
        STATUS_SHIPPED: [],
        STATUS_CANCELLED: [],
    }

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)

    total_price = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.TextField()
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'Заказ #{self.id} ({self.name})'

    # ==============================
    # BUSINESS LOGIC
    # ==============================

    from django.db import transaction
    from django.db.models import F

    def mark_paid(self):
        self._change_status(self.STATUS_PAID)

    def mark_shipped(self):
        self._change_status(self.STATUS_SHIPPED)

    def cancel(self):
        if self.status == self.STATUS_SHIPPED:
            raise Exception("Нельзя отменить уже отправленный заказ")

        if self.status == self.STATUS_CANCELLED:
            raise Exception("Заказ уже отменён")

        with transaction.atomic():
            # возврат stock
            for item in self.items.select_related("variant"):
                if item.variant:
                    item.variant.stock = F("stock") + item.quantity
                    item.variant.save(update_fields=["stock"])

            self._change_status(self.STATUS_CANCELLED)

    def _restore_stock(self):
        for item in self.items.select_related("variant"):
            if item.variant:
                "orders.Variant".objects.filter(pk=item.variant.pk).update(
                    stock=F("stock") + item.quantity
                )

    def _change_status(self, new_status):
        if new_status not in self.ALLOWED_TRANSITIONS[self.status]:
            raise Exception(
                f"Недопустимый переход: {self.status} → {new_status}"
            )

        self.status = new_status
        self._allow_status_change = True
        self.save(update_fields=["status"])
        self._allow_status_change = False

    def save(self, *args, **kwargs):
        if self.pk:
            old = Order.objects.get(pk=self.pk)

            # Если статус меняется напрямую
            if old.status != self.status:
                # Разрешаем изменение только если стоит служебный флаг
                if not getattr(self, "_allow_status_change", False):
                    raise Exception(
                        "Нельзя менять статус напрямую. Используйте методы модели."
                    )

        super().save(*args, **kwargs)

    def is_expired(self):
        if self.status != self.STATUS_NEW:
            return False

        expiration_time = self.created_at + timedelta(minutes=self.PAYMENT_TIMEOUT_MINUTES)
        return timezone.now() > expiration_time

    def auto_cancel_if_expired(self):
        if self.is_expired():
            self.cancel()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')

    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey('products.Variant', on_delete=models.SET_NULL, null=True, blank=True)

    product_name = models.CharField(max_length=255)
    variant_description = models.CharField(max_length=255, blank=True)

    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=0)  # snapshot цены

    class Meta:
        indexes = [
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'

    @property
    def subtotal(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        if self.pk:
            raise Exception("OrderItem нельзя редактировать после создания.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise Exception("OrderItem нельзя удалять.")

