import threading
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from products.models import Category, Product, Variant
from orders.models import Order, OrderItem

User = get_user_model()


class OrderConcurrencyTestCase(TransactionTestCase):

    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(
            username="concurrent",
            email="concurrent@test.com",
            password="12345678"
        )

        self.category = Category.objects.create(
            name="Concurrency Category",
            slug="concurrency-category"
        )

        self.product = Product.objects.create(
            name="Concurrency Product",
            slug="concurrency-product",
            description="desc",
            price=1000,
            category=self.category,
            is_active=True
        )

        self.variant = Variant.objects.create(
            product=self.product,
            stock=1000
        )

    def create_order(self):
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=self.user,
                    name="Concurrent User",
                    phone="123456789",
                    email="concurrent@test.com",
                    address="Test Address",
                    total_price=1000
                )

                OrderItem.objects.create(
                    order=order,
                    product=self.product,
                    variant=self.variant,
                    product_name=self.product.name,
                    variant_description="",
                    quantity=1,
                    price=1000
                )
        except Exception as e:
            print(e)
            raise

    def test_1000_concurrent_orders(self):
        threads = []

        for _ in range(1000):
            t = threading.Thread(target=self.create_order)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(Order.objects.count(), 1000)