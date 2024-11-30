import requests, json
from django.conf import settings
from django.shortcuts import redirect, render
from urllib.parse import urlencode
from collections import Counter

# Create your views here.

def spotify_login(request):
    scope = 'user-top-read user-library-read user-read-private user-read-recently-played'
    auth_url = (
        "https://accounts.spotify.com/authorize"
        "?response_type=code"
        f"&client_id={settings.SPOTIFY_CLIENT_ID}"
        f"&redirect_uri={settings.SPOTIFY_REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(auth_url)

def home(request):
    return render(request, "homepage.html")

def wrapped(request):
    # Step 1: Get the authorization code from the URL
    code = request.GET.get("code")

    if not code:
        return render(request, "home.html", {"error": "Authorization failed or was canceled"})

    # Store the code in the session (if you haven't already done so)
    request.session['auth_code'] = code

    # Step 2: Exchange the authorization code for an access token
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

    # Step 3: Extract the access token
    response_data = response.json()
    access_token = response_data.get("access_token")

    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}

    # Step 4: Fetch user profile data
    profile_url = "https://api.spotify.com/v1/me"
    profile_response = requests.get(profile_url, headers=headers)
    profile_data = profile_response.json() if profile_response.status_code == 200 else None

    # Step 5: Fetch other data (top tracks, artists, playlists, etc.)
    top_tracks_url = "https://api.spotify.com/v1/me/top/tracks?limit=5"
    top_tracks_response = requests.get(top_tracks_url, headers=headers)
    top_tracks_data = top_tracks_response.json().get("items", []) if top_tracks_response.status_code == 200 else []

    playlists_url = "https://api.spotify.com/v1/me/playlists?limit=5"
    playlists_response = requests.get(playlists_url, headers=headers)
    playlists_data = playlists_response.json().get("items", []) if playlists_response.status_code == 200 else []

    top_artists_url = "https://api.spotify.com/v1/me/top/artists?limit=5"
    top_artists_response = requests.get(top_artists_url, headers=headers)
    top_artists_data = top_artists_response.json().get("items", []) if top_artists_response.status_code == 200 else []

    all_genres = []
    for artist in top_artists_data:
        all_genres.extend(artist.get("genres", []))

    genre_counts = Counter(all_genres)

    # Get the top 5 genres
    top_genres = genre_counts.most_common(6)

    # Format data for the slide
    fun_genres_slide = {
        "type": "top_genres",
        "title": "Your Top Genres",
        "content": [{"genre": genre, "count": count} for genre, count in top_genres],
    }

    # Step 6: Reset the authorization code in the session after it's been used
    request.session.pop('auth_code', None)

    # Step 7: Return the data to the user in the response
    slides = [
        {
            "type": "profile",
            "title": "Your Profile",
            "content": profile_data,
        },
        {
            "type": "top_tracks",
            "title": "Top Tracks",
            "content": top_tracks_data,
        },
        {
            "type": "top_artists",
            "title": "Top Artists",
            "content": top_artists_data,
        },
        {
            "type": "playlists",
            "title": "Playlists",
            "content": playlists_data,
        },
        {
            "type": "overall_stats",
            "title": "Your Listening Overview",
            "content": fun_genres_slide,
        },
    ]

    return render(request, "profile.html", {"slides": slides})