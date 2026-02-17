from rest_framework import permissions, status, views
from rest_framework.response import Response
from .notification_settings_models import NotificationSetting
from .notification_settings_serializers import NotificationSettingSerializer

class NotificationSettingView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        obj, _ = NotificationSetting.objects.get_or_create(user=request.user)
        serializer = NotificationSettingSerializer(obj)
        return Response(serializer.data)

    def post(self, request):
        obj, _ = NotificationSetting.objects.get_or_create(user=request.user)
        serializer = NotificationSettingSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
