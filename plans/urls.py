from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, NotificationViewSet, ItineraryItemViewSet, ItemCommentViewSet, PollNotifyView
from .expense_views import ExpenseViewSet
from .push_notify_view import push_notify
from .ai_suggest_view import AiSuggestView

router = DefaultRouter()
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'itinerary', ItineraryItemViewSet, basename='itinerary')
router.register(r'comments', ItemCommentViewSet, basename='comment')
router.register(r'expenses', ExpenseViewSet, basename='expense')

urlpatterns = [
    path('', include(router.urls)),
    path('poll_notify/', PollNotifyView.as_view(), name='poll-notify'),
    path('push_notify/', push_notify, name='push-notify'),
    path('ai/suggest/', AiSuggestView.as_view(), name='ai-suggest'),
]
