import requests
from collections import Counter
from django.conf import settings
from functools import wraps
from django.shortcuts import redirect, render

def spotify_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if the user is authenticated (access_token in session)
        if not request.session.get("access_token"):
            # Save the intended destination in the session
            request.session['redirect_after_login'] = request.path
            # Redirect to the Spotify login URL
            return redirect('spotify_login')  # Replace with your login URL name
        return view_func(request, *args, **kwargs)
    return wrapper

# Utility function to exchange code for an access token
def get_access_token(auth_code):
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

# Utility function to fetch data from Spotify API
def fetch_spotify_data(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {}

# Spotify login view
def spotify_login(request):
    # Spotify authentication URL and scope
    scope = "streaming user-read-playback-state user-modify-playback-state user-read-currently-playing user-top-read user-library-read user-read-private user-read-recently-played"
    auth_url = (
        "https://accounts.spotify.com/authorize"
        "?response_type=code"
        f"&client_id={settings.SPOTIFY_CLIENT_ID}"
        f"&redirect_uri={settings.SPOTIFY_REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(auth_url)

def spotify_callback(request):
    # Exchange the auth code for an access token
    code = request.GET.get("code")
    if not code:
        return redirect("homepage")  # Or any error page

    access_token = get_access_token(code)
    if access_token:
        request.session["access_token"] = access_token

        # Redirect to the original destination (if any) or homepage
        redirect_url = request.session.pop('redirect_after_login', 'homepage')
        return redirect(redirect_url)

    return render(request, "error.html", {"error": "Failed to authenticate with Spotify."})

# Homepage view
def home(request):
    return render(request, "homepage.html")

# Reusable wrapped view for different time ranges
def wrapped(request, time_range, theme):
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("spotify_login")
        # return render(request, "error.html", {"error": "Failed to obtain access token."})

    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch Spotify data
    if time_range == "default":
        profile_url = "https://api.spotify.com/v1/me"
        profile_data = fetch_spotify_data(profile_url, headers)

        top_tracks_url = "https://api.spotify.com/v1/me/top/tracks?limit=5"
        top_tracks_response = requests.get(top_tracks_url, headers=headers)
        top_tracks_data = top_tracks_response.json().get("items", []) if top_tracks_response.status_code == 200 else []

        top_artists_url = "https://api.spotify.com/v1/me/top/artists?limit=5"
        top_artists_response = requests.get(top_artists_url, headers=headers)
        top_artists_data = top_artists_response.json().get("items",[]) if top_artists_response.status_code == 200 else []

        playlists_url = "https://api.spotify.com/v1/me/playlists?limit=5"
        playlists_response = requests.get(playlists_url, headers=headers)
        playlists_data = playlists_response.json().get("items", []) if playlists_response.status_code == 200 else []

        # Aggregate genres
        all_genres = []
        for artist in top_artists_data:
            all_genres.extend(artist.get("genres", []))

        genre_counts = Counter(all_genres)
        top_genres = genre_counts.most_common()
    else:
        profile_url = "https://api.spotify.com/v1/me"
        profile_data = fetch_spotify_data(profile_url, headers)

        top_tracks_url = f"https://api.spotify.com/v1/me/top/tracks?time_range={time_range}&limit=10"
        top_tracks_response = requests.get(top_tracks_url, headers=headers)
        top_tracks_data = top_tracks_response.json().get("items", []) if top_tracks_response.status_code == 200 else []

        top_artists_url = f"https://api.spotify.com/v1/me/top/artists?time_range={time_range}&limit=5"
        top_artists_data = fetch_spotify_data(top_artists_url, headers).get("items", [])

        playlists_url = "https://api.spotify.com/v1/me/playlists?limit=5"
        playlists_response = requests.get(playlists_url, headers=headers)
        playlists_data = playlists_response.json().get("items", []) if playlists_response.status_code == 200 else []

        # Aggregate genres
        all_genres = []
        for artist in top_artists_data:
            all_genres.extend(artist.get("genres", []))

        genre_counts = Counter(all_genres)
        top_genres = genre_counts.most_common()

    slides = [
        {"type": "profile", "title": "Welcome to Your Wrapped!", "content": profile_data},
        {"type": "song_transitions", "title": "Keep Clicking to Find Out Your Biggest Secrets :)", },
        {"type": "top_tracks", "title": "Top Tracks", "content": top_tracks_data},
        {"type": "song_playback", "title": "Listen Back To Your Favorites", "content": top_tracks_data, "token": access_token, },
        {"type": "top_artists", "title": "Top Artists", "content": top_artists_data},
        {"type": "playlists", "title": "Playlists", "content": playlists_data,},
        {"type": "top_genres", "title": "Top Genres", "content": [{"genre": genre, "count": count} for genre, count in top_genres]},
        {"type": "end", "title": "The Journey Comes to An End", "content": profile_data,},
    ]

    if theme == "christmas":
        return render(request, "christmas.html", {"slides": slides})
    elif theme == "halloween":
        return render(request, "halloween.html", {"slides": slides})
    else:
        return render(request, "slides.html", {"slides": slides})

# Views for specific time ranges
@spotify_login_required
def default(request):
    return wrapped(request, "default", "none")

@spotify_login_required
def short(request):
    return wrapped(request, "short_term", "none")

@spotify_login_required
def medium(request):
    return wrapped(request, "medium_term", "none")

@spotify_login_required
def long(request):
    return wrapped(request, "long_term", "none")

@spotify_login_required
def halloween(request):
    return wrapped(request, "default", "halloween")

@spotify_login_required
def holiday(request):
    return wrapped(request, "default", "christmas")

def contact(request):
    return render(request, "contact.html")