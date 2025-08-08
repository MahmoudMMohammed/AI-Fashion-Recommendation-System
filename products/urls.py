# Import both routers
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

# 1. Start with the main router for top-level resources
router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'sizes', views.ProductSizeViewSet, basename='productsize')

# 2. Create a nested router for product images
#    - The first argument is the parent router (`router`)
#    - The second argument is the parent's URL prefix (`r'products'`)
#    - The third argument is the lookup field name (`lookup='product'`)
#      that will be used in the URL (e.g., /products/{product_pk}/)
products_router = routers.NestedDefaultRouter(router, r'products', lookup='product')

# 3. Register the ProductImageViewSet with the nested router
#    - This creates URLs like /products/{product_pk}/images/
products_router.register(r'images', views.ProductImageViewSet, basename='product-images')

# 4. Combine the URL patterns from both routers
#    The order matters: parent router URLs should generally come first.
urlpatterns = router.urls + products_router.urls