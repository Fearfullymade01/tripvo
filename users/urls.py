from django.urls import path
from .signup_views import SignupView
from .guest_views import GuestSignupView
from .profile_views import ProfileView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('guest/', GuestSignupView.as_view(), name='guest-signup'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
