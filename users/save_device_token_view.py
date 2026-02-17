from rest_framework import permissions, status, views
from rest_framework.response import Response
from users.models import UserProfile

class SaveDeviceTokenView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "No token provided"}, status=status.HTTP_400_BAD_REQUEST)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.device_token = token
        profile.save()
        return Response({"success": True})
