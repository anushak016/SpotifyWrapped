# wrappedSlides/utils.py
import requests
from django.utils import timezone
import datetime

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