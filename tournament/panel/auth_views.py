"""Auth views — login / logout for the custom admin panel."""

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render


def panel_login(request):
    """Staff login page for the custom panel."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("panel:dashboard")

    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            next_url = request.GET.get("next", "panel:dashboard")
            return redirect(next_url)
        error = "Invalid credentials or insufficient permissions."

    return render(request, "panel/login.html", {"error": error})


def panel_logout(request):
    """Log out and redirect to panel login."""
    logout(request)
    return redirect("panel:login")
