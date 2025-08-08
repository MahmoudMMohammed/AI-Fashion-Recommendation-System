"""
URL configuration for fashionRecommendationSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Add djoser's core authentication URLs
    path('api/auth/', include('djoser.urls')),
    # Add djoser's JWT specific URLs (for token creation, refresh, verification)
    path('api/auth/', include('djoser.urls.jwt')),

    path('api/', include('users.urls')),
    path('api/', include('products.urls')),
    path('api/', include('orders.urls')),
    path('api/', include('wallet.urls')),
    path('api/', include('recommendations.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

