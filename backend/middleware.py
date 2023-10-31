# middleware.py
from django.conf import settings

from datetime import datetime

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        now = datetime.now()

        if 'last_activity' in request.session:
            last_activity_str = request.session['last_activity']
            
            # Convert the stored string back to a datetime object
            last_activity = datetime.strptime(last_activity_str, '%Y-%m-%d %H:%M:%S')

            if (now - last_activity).seconds > settings.SESSION_COOKIE_AGE:
                # Session has timed out; log the user out
                del request.session['user_id']  # Clear user data from the session

        # Update the last activity timestamp for the user as a string
        request.session['last_activity'] = now.strftime('%Y-%m-%d %H:%M:%S')

        response = self.get_response(request)
        return response
