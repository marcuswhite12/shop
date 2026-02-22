from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from .models import Category, Product, ProductImage, Variant


# ==============================
# CATEGORY LIST
# ==============================

class CategoryListView(ListView):
    model = Category
    template_name = "products/category_list.html"
    context_object_name = "categories"
    queryset = (
        Category.objects
        .only("id", "name", "slug", "image")
        .order_by("name")
    )


# ==============================
# PRODUCT LIST (Category page)
# ==============================

class ProductListView(ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(
            Category.objects.only("id", "name", "slug"),
            slug=self.kwargs["slug"]
        )

        return (
            Product.objects
            .filter(category=self.category, is_active=True)
            .only("id", "name", "slug", "price", "created_at", "category")
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=ProductImage.objects.only("id", "product", "image", "order")
                )
            )
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


# ==============================
# PRODUCT DETAIL
# ==============================

class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_active=True)
            .only(
                "id", "name", "slug",
                "description", "price",
                "category", "created_at"
            )
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=ProductImage.objects.only("id", "product", "image", "order")
                ),
                Prefetch(
                    "variants",
                    queryset=Variant.objects.select_related("color", "size")
                    .only("id", "product", "stock", "color", "size")
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # без дополнительного SQL
        variants = list(self.object.variants.all())

        context["first_available_variant"] = next(
            (v for v in variants if v.stock > 0),
            None
        )

        return context