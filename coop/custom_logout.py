from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    """
    Logs out the user and flushes the session completely.
    """
    logout(request)
    request.session.flush()
    return redirect('login')
