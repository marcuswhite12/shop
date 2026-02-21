from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

from orders.models import Order, OrderItem
from products.models import Product, Variant, Category

User = get_user_model()


class OrderProductionTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="password123"
        )

        self.other_user = User.objects.create_user(
            username="user2",
            password="password123"
        )

        self.category = Category.objects.create(
            name="Category",
            slug="category"
        )

        self.product = Product.objects.create(
            name="Product",
            slug="product",
            description="Desc",
            price=1000,
            is_active=True,
            category=self.category
        )

        self.variant = Variant.objects.create(
            product=self.product,
            stock=10
        )

        self.order = Order.objects.create(
            user=self.user,
            name="Name",
            phone="123",
            email="test@mail.com",
            address="Address",
            total_price=2000
        )

        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            variant=self.variant,
            quantity=2,
            price=1000
        )

    # ===============================
    # STATE MACHINE
    # ===============================

    def test_valid_status_flow(self):
        self.order.mark_paid()
        self.assertEqual(self.order.status, Order.STATUS_PAID)

        self.order.mark_shipped()
        self.assertEqual(self.order.status, Order.STATUS_SHIPPED)

    def test_invalid_transition(self):
        self.order.mark_paid()
        self.order.mark_shipped()

        with self.assertRaises(Exception):
            self.order.mark_paid()

    def test_shipped_cannot_be_cancelled(self):
        self.order.mark_paid()
        self.order.mark_shipped()

        with self.assertRaises(Exception):
            self.order.cancel()

    def test_paid_can_be_cancelled(self):
        self.order.mark_paid()
        self.order.cancel()
        self.assertEqual(self.order.status, Order.STATUS_CANCELLED)

    # ===============================
    # DIRECT STATUS PROTECTION
    # ===============================

    def test_direct_status_change_blocked(self):
        self.order.status = Order.STATUS_PAID
        with self.assertRaises(Exception):
            self.order.save()

    # ===============================
    # TOTAL PRICE PROTECTION
    # ===============================

    def test_total_price_change_blocked(self):
        self.order.total_price = 999999
        with self.assertRaises(Exception):
            self.order.save()

    # ===============================
    # CANCEL LOGIC
    # ===============================

    def test_cancel_returns_stock(self):
        original_stock = self.variant.stock

        self.order.cancel()
        self.variant.refresh_from_db()

        self.assertEqual(
            self.variant.stock,
            original_stock + self.item.quantity
        )

    def test_double_cancel_blocked(self):
        self.order.cancel()

        with self.assertRaises(Exception):
            self.order.cancel()

    def test_cancel_returns_stock_only_once(self):
        original_stock = self.variant.stock

        self.order.cancel()

        with self.assertRaises(Exception):
            self.order.cancel()

        self.variant.refresh_from_db()

        self.assertEqual(
            self.variant.stock,
            original_stock + self.item.quantity
        )

    # ===============================
    # ORDER ITEM PROTECTION
    # ===============================

    def test_orderitem_edit_blocked(self):
        self.item.quantity = 10
        with self.assertRaises(Exception):
            self.item.save()

    def test_orderitem_delete_blocked(self):
        with self.assertRaises(Exception):
            self.item.delete()

    # ===============================
    # DELETE PROTECTION
    # ===============================

    def test_order_delete_blocked(self):
        with self.assertRaises(Exception):
            self.order.delete()

    # ===============================
    # SNAPSHOT LOGIC
    # ===============================

    def test_snapshot_price_persists(self):
        self.product.price = 9999
        self.product.save()

        self.item.refresh_from_db()

        self.assertEqual(self.item.price, 1000)

    # ===============================
    # EXPIRATION
    # ===============================

    def test_is_expired_true(self):
        self.order.created_at = timezone.now() - timedelta(hours=2)
        self.order.save(update_fields=["created_at"])

        self.assertTrue(self.order.is_expired())

    def test_is_expired_false_if_paid(self):
        self.order.mark_paid()
        self.order.created_at = timezone.now() - timedelta(hours=2)
        self.order.save(update_fields=["created_at"])

        self.assertFalse(self.order.is_expired())

    # ===============================
    # USER ISOLATION (SECURITY)
    # ===============================

    def test_user_cannot_access_foreign_order(self):
        self.client.login(username="user2", password="password123")

        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_user_can_access_own_order(self):
        self.client.login(username="user1", password="password123")

        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )

        self.assertEqual(response.status_code, 200)