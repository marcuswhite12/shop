from django.test import TestCase
from django.urls import reverse
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from .models import (
    Category,
    Product,
    ProductImage,
    Variant,
    Color,
    Size
)


class ProductModelTestCase(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Clothes",
            slug="clothes"
        )

        self.product = Product.objects.create(
            name="Jacket",
            slug="jacket",
            description="Warm jacket",
            price=5000,
            category=self.category,
            is_active=True
        )

        self.color = Color.objects.create(name="Red")
        self.size = Size.objects.create(name="M")

    # ===============================
    # MODEL LOGIC
    # ===============================

    def test_product_str(self):
        self.assertEqual(str(self.product), "Jacket")

    def test_category_str(self):
        self.assertEqual(str(self.category), "Clothes")

    def test_variant_unique_constraint(self):
        Variant.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            stock=5
        )

        with self.assertRaises(IntegrityError):
            Variant.objects.create(
                product=self.product,
                color=self.color,
                size=self.size,
                stock=3
            )

    def test_variant_delete_blocked_if_used_in_order(self):
        variant = Variant.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            stock=5
        )

        # имитируем OrderItem через импорт
        from orders.models import Order, OrderItem
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username="u", password="p")

        order = Order.objects.create(
            user=user,
            name="Test",
            phone="123",
            email="test@test.com",
            address="Address",
            total_price=1000
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            variant=variant,
            quantity=1,
            price=1000
        )

        with self.assertRaises(ValidationError):
            variant.delete()

    def test_in_stock_property(self):
        self.assertFalse(self.product.in_stock)

        Variant.objects.create(
            product=self.product,
            stock=5
        )

        self.assertTrue(self.product.in_stock)


# =====================================================
# VIEW TESTS
# =====================================================

class ProductViewTestCase(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Shoes",
            slug="shoes"
        )

        self.product = Product.objects.create(
            name="Sneakers",
            slug="sneakers",
            description="Nice shoes",
            price=3000,
            category=self.category,
            is_active=True
        )

        self.inactive_product = Product.objects.create(
            name="Hidden",
            slug="hidden",
            description="Hidden",
            price=1000,
            category=self.category,
            is_active=False
        )

        ProductImage.objects.create(
            product=self.product,
            image="products/test.jpg",
            order=0
        )

        Variant.objects.create(
            product=self.product,
            stock=10
        )

    # ===============================
    # CATEGORY LIST
    # ===============================

    def test_category_list_view(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shoes")

    # ===============================
    # PRODUCT LIST
    # ===============================

    def test_product_list_view(self):
        response = self.client.get(
            reverse("category_detail", args=[self.category.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sneakers")
        self.assertNotContains(response, "Hidden")

    def test_product_list_invalid_category(self):
        response = self.client.get(
            reverse("category_detail", args=["wrong"])
        )
        self.assertEqual(response.status_code, 404)

    # ===============================
    # PRODUCT DETAIL
    # ===============================

    def test_product_detail_view(self):
        response = self.client.get(
            reverse("product_detail", args=[self.product.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sneakers")
        self.assertContains(response, "3000")

    def test_product_detail_inactive_blocked(self):
        response = self.client.get(
            reverse("product_detail", args=[self.inactive_product.slug])
        )

        self.assertEqual(response.status_code, 404)

    def test_product_detail_invalid_slug(self):
        response = self.client.get(
            reverse("product_detail", args=["wrong"])
        )
        self.assertEqual(response.status_code, 404)

    # ===============================
    # PAGINATION
    # ===============================

    def test_product_list_pagination(self):
        for i in range(20):
            Product.objects.create(
                name=f"P{i}",
                slug=f"p{i}",
                description="d",
                price=100,
                category=self.category,
                is_active=True
            )

        response = self.client.get(
            reverse("category_detail", args=[self.category.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)