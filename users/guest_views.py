from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import uuid

class GuestSignupView(APIView):
    permission_classes = []

    def post(self, request):
        name = request.data.get("name")
        if not name:
            return Response({"error": "Name is required"}, status=400)
        # Generate a unique guest username
        guest_username = f"guest_{uuid.uuid4().hex[:8]}"
        user = User.objects.create_user(username=guest_username, first_name=name)
        user.set_unusable_password()
        user.save()
        return Response({"success": True, "user_id": user.id, "username": guest_username})
