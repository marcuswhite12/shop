from django.test import TestCase
from django.urls import reverse
from products.models import Product, Variant, Category


class CartTestCase(TestCase):

    def setUp(self):
        print("\n--- SETUP CART ---")

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
            stock=5
        )

    # ==============================
    # ADD TESTS
    # ==============================

    def test_add_to_cart_success(self):
        print("Testing add to cart success")

        response = self.client.post(
            reverse("cart_add", args=[self.product.id]),
            {"variant_id": self.variant.id, "quantity": 2}
        )

        self.assertEqual(response.status_code, 302)

        cart = self.client.session.get("cart")
        self.assertIn(f"variant_{self.variant.id}", cart)
        self.assertEqual(cart[f"variant_{self.variant.id}"]["quantity"], 2)

    def test_add_more_than_stock_blocked(self):
        print("Testing add more than stock")

        self.client.post(
            reverse("cart_add", args=[self.product.id]),
            {"variant_id": self.variant.id, "quantity": 10}
        )

        cart = self.client.session.get("cart")
        self.assertEqual(cart, {})  # не добавилось

    def test_add_inactive_product_blocked(self):
        print("Testing inactive product")

        self.product.is_active = False
        self.product.save()

        response = self.client.post(
            reverse("cart_add", args=[self.product.id]),
            {"variant_id": self.variant.id, "quantity": 1}
        )

        self.assertEqual(response.status_code, 404)

    def test_add_wrong_variant_blocked(self):
        print("Testing wrong variant")

        other_product = Product.objects.create(
            name="Other",
            slug="other",
            description="d",
            price=500,
            category=self.category,
            is_active=True
        )

        wrong_variant = Variant.objects.create(
            product=other_product,
            stock=5
        )

        self.client.post(
            reverse("cart_add", args=[self.product.id]),
            {"variant_id": wrong_variant.id, "quantity": 1}
        )

        cart = self.client.session.get("cart")
        self.assertEqual(cart, {})

    # ==============================
    # CART CLEANING TESTS
    # ==============================

    def test_stock_zero_removes_item(self):
        print("Testing auto remove if stock 0")

        self.client.post(
            reverse("cart_add", args=[self.product.id]),
            {"variant_id": self.variant.id, "quantity": 2}
        )

        self.variant.stock = 0
        self.variant.save()

        self.client.get(reverse("cart_detail"))

        cart = self.client.session.get("cart")
        self.assertEqual(cart, {})

    def test_quantity_trimmed_to_stock(self):
        print("Testing quantity trimmed")

        self.client.post(
            reverse("cart_add", args=[self.product.id]),
            {"variant_id": self.variant.id, "quantity": 3}
        )

        self.variant.stock = 2
        self.variant.save()

        self.client.get(reverse("cart_detail"))

        cart = self.client.session.get("cart")
        key = f"variant_{self.variant.id}"
        self.assertEqual(cart[key]["quantity"], 2)

    # ==============================
    # UPDATE TESTS
    # ==============================

    def test_update_quantity_success(self):
        print("Testing update quantity")

        self.client.post(
            reverse("cart_add", args=[self.product.id]),
            {"variant_id": self.variant.id, "quantity": 1}
        )

        self.client.post(
            reverse("cart_update"),
            {"key": f"variant_{self.variant.id}", "quantity": 3}
        )

        cart = self.client.session.get("cart")
        self.assertEqual(cart[f"variant_{self.variant.id}"]["quantity"], 3)

    def test_update_quantity_over_stock_trimmed(self):
        print("Testing update over stock")

        self.client.post(
            reverse("cart_add", args=[self.product.id]),
            {"variant_id": self.variant.id, "quantity": 1}
        )

        self.client.post(
            reverse("cart_update"),
            {"key": f"variant_{self.variant.id}", "quantity": 10}
        )

        cart = self.client.session.get("cart")
        self.assertEqual(cart[f"variant_{self.variant.id}"]["quantity"], 5)

    # ==============================
    # REMOVE & CLEAR
    # ==============================

    def test_remove_item(self):
        print("Testing remove item")

        self.client.post(
            reverse("cart_add", args=[self.product.id]),
            {"variant_id": self.variant.id, "quantity": 1}
        )

        self.client.post(
            reverse("cart_remove"),
            {"key": f"variant_{self.variant.id}"}
        )

        cart = self.client.session.get("cart")
        self.assertEqual(cart, {})

    def test_clear_cart(self):
        print("Testing clear cart")

        self.client.post(
            reverse("cart_add", args=[self.product.id]),
            {"variant_id": self.variant.id, "quantity": 1}
        )

        self.client.post(reverse("cart_clear"))

        cart = self.client.session.get("cart")
        self.assertEqual(cart, {})
