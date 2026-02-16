from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from webpush import send_user_notification
from django.contrib.auth import get_user_model

@csrf_exempt
def push_notify(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        payload = request.POST.get("payload")
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            send_user_notification(user=user, payload={"head": "Tripvo Chat", "body": payload}, ttl=1000)
            return JsonResponse({"status": "success"})
        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "User not found"}, status=404)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
