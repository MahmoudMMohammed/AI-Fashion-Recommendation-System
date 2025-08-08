from django.urls import path
from .views import UserProfileViewSet, PasswordResetCodeView, PasswordResetConfirmWithCode

# Since it's a singleton resource for the user, we define a direct path.
# This gives us GET, PUT, PATCH at /api/profile/
profile_detail = UserProfileViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'})

urlpatterns = [
    path('profile/', profile_detail, name='user-profile-detail'),
    path("auth/reset_code/", PasswordResetCodeView.as_view(), name="reset_code"),
    path("auth/reset_code/confirm/", PasswordResetConfirmWithCode.as_view(), name="reset_code_confirm"),
]