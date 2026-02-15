from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField('Название категории', max_length=100)
    slug = models.SlugField(unique=True, help_text="Для URL, латиницей")
    image = models.ImageField(
        'Фото категории',
        upload_to='categories/',
        blank=True,
        null=True
    )


    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    name = models.CharField('Название товара', max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField('Описание')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=0, default=0)  # в сомах, целые
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    @property
    def in_stock(self):
        return self.variants.filter(stock__gt=0).exists()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('Фото', upload_to='products/')
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['order']


class Color(models.Model):
    name = models.CharField('Цвет', max_length=50)
    hex_code = models.CharField('HEX код', max_length=7, blank=True)  # например #FF0000

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField('Размер', max_length=20)  # S, M, L, XL и т.д.

    def __str__(self):
        return self.name


class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    stock = models.PositiveIntegerField('На складе', default=0)

    def __str__(self):
        return f"{self.product} - {self.size} {self.color}"