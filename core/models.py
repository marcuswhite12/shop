from django.db import models
from django.core.exceptions import ValidationError

def get_singleton(instance):
    return SiteSettings.objects.first()

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=200, default='Мой магазин одежды')
    site_description = models.TextField(default='Лучший магазин одежды в Бишкеке')
    logo = models.ImageField(upload_to='logo/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#3B82F6')  # hex, например blue-500
    secondary_color = models.CharField(max_length=7, default='#1E40AF')
    email = models.EmailField(default='info@shop.kg')
    phone = models.CharField(max_length=50, default='+996 999 123 456')
    currency = models.CharField(max_length=10, default='KGS')
    currency_symbol = models.CharField(max_length=5, default='сом')

    class Meta:
        verbose_name = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайта'

    def __str__(self):
        return self.site_name

    def clean(self):
        if SiteSettings.objects.exclude(pk=self.pk).exists():
            raise ValidationError('Может быть только один объект SiteSettings!')

    @classmethod
    def get_singleton(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj