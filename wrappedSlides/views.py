from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone  # Add this import
import requests
from django.conf import settings
from collections import Counter
import datetime  # Add this import

# Create your views here.

def home(request):
    # Allow access to home page without authentication
    return render(request, "home.html")

@login_required(login_url='/auth/login/')
def spotify_login(request):
    scope = 'user-top-read'
    auth_url = (
        "https://accounts.spotify.com/authorize"
        "?response_type=code"
        f"&client_id={settings.SPOTIFY_CLIENT_ID}"
        f"&redirect_uri={settings.SPOTIFY_REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(auth_url)

@login_required(login_url='/auth/login/')
def wrapped(request):
    code = request.GET.get("code")
    if not code:
        return redirect('spotify_login')

    try:
        # Exchange code for tokens
        token_url = "https://accounts.spotify.com/api/token"
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(token_url, data=payload, headers=headers)
        if response.status_code != 200:
            return render(request, "error.html", {"error": "Failed to obtain access token."})

        token_data = response.json()
        
        # Store tokens in user's profile
        profile = request.user.profile
        profile.spotify_token = token_data['access_token']
        profile.spotify_refresh_token = token_data['refresh_token']
        profile.spotify_token_expires = timezone.now() + datetime.timedelta(seconds=token_data['expires_in'])
        profile.save()

        # After successful Spotify auth, redirect to home
        return redirect('home')
    except Exception as e:
        return render(request, "error.html", {"error": f"Error during Spotify authentication: {str(e)}"})

def refresh_spotify_token(profile):
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": profile.spotify_refresh_token,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        profile.spotify_token = token_data['access_token']
        profile.spotify_token_expires = timezone.now() + datetime.timedelta(seconds=token_data['expires_in'])
        profile.save()
        return True
    return False

def long_term(request):
    # Logic for long-term Wrapped
    return render(request, "long_term.html")

def medium_term(request):
    # Logic for medium-term Wrapped
    return render(request, "medium_term.html")

def short_term(request):
    # Logic for short-term Wrapped
    return render(request, "short_term.html")

def christmas(request):
    # Logic for Christmas Wrapped
    return render(request, "christmas.html")

def halloween(request):
    # Logic for Halloween Wrapped
    return render(request, "halloween.html")