from django.urls import path
from .views import SignUpView, ProfileView, UserDetailView
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path('signup/', SignUpView.as_view()),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('profile/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
]