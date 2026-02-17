from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet
from .notification_settings_views import NotificationSettingView

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('notification-settings/', NotificationSettingView.as_view(), name='notification-settings'),
]
