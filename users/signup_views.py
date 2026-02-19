from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .signup_serializers import SignupSerializer

class SignupView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"success": True, "user_id": user.id})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
