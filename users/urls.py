from django.urls import path
from .views import SignUpView, SignInView
from rest_framework_simplejwt.views import TokenObtainPairView


#already prefixed with '/users/'
urlpatterns = [
    path('signup/', SignUpView.as_view()),
    path('sign-in/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
]