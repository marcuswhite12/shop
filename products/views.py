from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from .models import Category, Product


class CategoryListView(ListView):
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    queryset = Category.objects.all()  # все категории


class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])

        return (
            Product.objects
            .filter(category=self.category, is_active=True)
            .prefetch_related('images')   # важно
            .order_by('-created_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_active=True)
            .prefetch_related(
                'images',
                'variants__color',
                'variants__size'
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['first_available_variant'] = (
            self.object.variants.filter(stock__gt=0).first()
        )
        return context


