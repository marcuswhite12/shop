from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Color, Size, Variant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_preview']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px; border-radius:8px;" />',
                obj.image.url
            )
        return "(Нет фото)"

    image_preview.short_description = 'Фото'



class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'order']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 100px;" />', obj.image.url)
        return "(Нет фото)"
    image_preview.short_description = 'Превью'


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    fields = ['color', 'size', 'stock']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, VariantInline]
    readonly_fields = ['created_at']


admin.site.register(Color)
admin.site.register(Size)
