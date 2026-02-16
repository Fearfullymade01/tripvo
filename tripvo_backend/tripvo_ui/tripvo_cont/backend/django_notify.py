import requests
import os

def notify_django_poll_event(event_type, poll):
    """
    Notify Django backend of poll events (new poll, poll closed).
    event_type: 'new' or 'closed'
    poll: dict with poll data
    """
    # This assumes Django is running locally and has an endpoint to receive poll notifications
    # You must implement this endpoint in Django for full integration
    django_url = os.environ.get("DJANGO_POLL_NOTIFY_URL", "http://localhost:8000/api/poll_notify/")
    payload = {
        "event": event_type,
        "poll": poll
    }
    try:
        requests.post(django_url, json=payload, timeout=2)
    except Exception as e:
        print(f"Failed to notify Django: {e}")
