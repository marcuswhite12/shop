from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from products.models import Product, Variant, Category
from orders.models import Order, OrderItem

User = get_user_model()


class OrderModelTests(TestCase):

    def setUp(self):
        print("\n--- SETUP ---")

        self.user = User.objects.create_user(
            username="testuser",
            password="123456789"
        )

        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )

        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            description="desc",
            price=1000,
            category=self.category,
            is_active=True
        )

        self.variant = Variant.objects.create(
            product=self.product,
            stock=10
        )

    def create_order_with_item(self, quantity=2):
        order = Order.objects.create(
            user=self.user,
            name="Test",
            phone="123",
            email="test@test.com",
            address="Addr",
            total_price=2000
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            variant=self.variant,
            product_name=self.product.name,
            variant_description="",
            quantity=quantity,
            price=self.product.price
        )

        return order

    def test_status_transition_valid(self):
        print("Testing valid status transitions")

        order = self.create_order_with_item()

        order.mark_paid()
        self.assertEqual(order.status, Order.STATUS_PAID)

        order.mark_shipped()
        self.assertEqual(order.status, Order.STATUS_SHIPPED)

    def test_invalid_status_transition(self):
        print("Testing invalid transition")

        order = self.create_order_with_item()

        with self.assertRaises(Exception):
            order.mark_shipped()  # нельзя NEW → SHIPPED

    def test_direct_status_change_blocked(self):
        print("Testing direct status change block")

        order = self.create_order_with_item()

        order.status = Order.STATUS_PAID

        with self.assertRaises(Exception):
            order.save()

    def test_cancel_returns_stock(self):
        print("Testing cancel returns stock")

        order = self.create_order_with_item(quantity=3)

        # уменьшаем stock вручную, как будто списали
        self.variant.stock -= 3
        self.variant.save()

        order.cancel()
        self.variant.refresh_from_db()

        self.assertEqual(order.status, Order.STATUS_CANCELLED)
        self.assertEqual(self.variant.stock, 10)

    def test_cannot_delete_order_item(self):
        print("Testing OrderItem delete blocked")

        order = self.create_order_with_item()
        item = order.items.first()

        with self.assertRaises(Exception):
            item.delete()

    def test_variant_delete_blocked_if_in_order(self):
        print("Testing Variant delete blocked")

        order = self.create_order_with_item()

        with self.assertRaises(Exception):
            self.variant.delete()

    def test_order_expiration(self):
        print("Testing expiration logic")

        order = self.create_order_with_item()

        order.created_at = timezone.now() - timedelta(minutes=20)
        order.save()

        self.assertTrue(order.is_expired())

    def test_auto_cancel_if_expired(self):
        print("Testing auto cancel")

        order = self.create_order_with_item()

        order.created_at = timezone.now() - timedelta(minutes=20)
        order.save()

        order.auto_cancel_if_expired()

        self.assertEqual(order.status, Order.STATUS_CANCELLED)
