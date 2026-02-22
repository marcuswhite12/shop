from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('account/', include('users.urls')),
    path("account/login/", auth_views.LoginView.as_view(
        template_name="users/login.html"
    ), name="login"),

    path("account/logout/", auth_views.LogoutView.as_view(
        next_page="home"
    ), name="logout"),

    path("password-reset/",
         auth_views.PasswordResetView.as_view(
             template_name="users/password_reset.html"
         ),
         name="password_reset"),
    path('orders/', include('orders.urls')),
    # path('payments/', include('payments.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
