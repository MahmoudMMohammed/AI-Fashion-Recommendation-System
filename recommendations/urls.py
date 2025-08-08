from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'style-images', views.StyleImageViewSet, basename='styleimage')
router.register(r'recommendation-logs', views.RecommendationLogViewSet, basename='recommendationlog')
router.register(r'feedbacks', views.FeedbackViewSet, basename='feedback')

urlpatterns = router.urls