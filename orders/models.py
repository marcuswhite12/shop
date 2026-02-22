from django.db import models, transaction
from django.db.models import F
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from products.models import *
from django.apps import apps
from django.contrib.auth import get_user_model

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
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f'Заказ #{self.id} ({self.name})'

    # ==============================
    # BUSINESS LOGIC
    # ==============================

    from django.db import transaction
    from django.db.models import F

    def mark_paid(self):
        with transaction.atomic():
            locked = (
                Order.objects
                .select_for_update()
                .get(pk=self.pk)
            )

            locked._change_status(self.STATUS_PAID)

            # синхронизация текущего объекта
            self.status = locked.status

    def mark_shipped(self):
        with transaction.atomic():
            locked = (
                Order.objects
                .select_for_update()
                .get(pk=self.pk)
            )

            locked._change_status(self.STATUS_SHIPPED)

            self.status = locked.status

    def cancel(self):
        with transaction.atomic():
            locked = (
                Order.objects
                .select_for_update()
                .get(pk=self.pk)
            )

            if locked.status == self.STATUS_SHIPPED:
                raise Exception("Нельзя отменить уже отправленный заказ")

            if locked.status == self.STATUS_CANCELLED:
                raise Exception("Заказ уже отменён")

            for item in locked.items.select_related("variant"):
                if item.variant:
                    type(item.variant).objects.filter(pk=item.variant.pk).update(
                        stock=F("stock") + item.quantity
                    )

            locked._change_status(self.STATUS_CANCELLED)

            # синхронизируем текущий объект
            self.status = locked.status

    def _restore_stock(self):
        Variant = apps.get_model('products', 'Variant')
        for item in self.items.select_related("variant"):
            if item.variant:
                Variant.objects.filter(pk=item.variant.pk).update(
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
            old = (
                Order.objects
                .filter(pk=self.pk)
                .values("status", "total_price")
                .first()
            )

            if old:
                old_status = old["status"]
                old_total = old["total_price"]

                # защита статуса
                if old_status != self.status:
                    if not getattr(self, "_allow_status_change", False):
                        raise Exception(
                            "Нельзя менять статус напрямую. Используйте методы модели."
                        )

                # защита total_price
                if old_total != self.total_price:
                    raise Exception("Нельзя менять total_price напрямую.")

        super().save(*args, **kwargs)

    def is_expired(self):
        if self.status != self.STATUS_NEW:
            return False

        expiration_time = self.created_at + timedelta(minutes=self.PAYMENT_TIMEOUT_MINUTES)
        return timezone.now() > expiration_time

    def auto_cancel_if_expired(self):
        if self.is_expired():
            self.cancel()

    def delete(self, *args, **kwargs):
        raise Exception("Удаление заказа запрещено.")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')

    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)

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

