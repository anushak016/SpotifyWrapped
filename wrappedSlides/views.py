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
    scope = "user-top-read user-library-read user-read-private user-read-recently-played"
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

@spotify_login_required
def original_wrapped(request):
    # Step 1: Get the authorization code from the URL
    code = request.GET.get("code")

    if not code:
        return render(request, "homepage.html", {"error": "Authorization failed or was canceled"})

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
        {"type": "profile", "title": "Welcome to Your Wrapped!", "content": profile_data,},
        {"type": "song_transitions", "title": "",},
        {"type": "top_tracks", "title": "Top Tracks", "content": top_tracks_data,},
        {"type": "song_playback:", "title": "Top Songs", "content": top_tracks_data, "token": access_token,},
        {"type": "top_artists", "title": "Top Artists", "content": top_artists_data,},
        {"type": "playlists", "title": "Favorite Playlists", "content": playlists_data,},
        {"type": "top_genres", "title": "Top Genres", "content": fun_genres_slide,},
        {"type": "end", "title": "The End", "content": profile_data,},
    ]

    return render(request, "slides.html", {"slides": slides})

# Reusable wrapped view for different time ranges
def wrapped(request, time_range):
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("spotify_login")
        # return render(request, "error.html", {"error": "Failed to obtain access token."})

    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch Spotify data
    profile_url = "https://api.spotify.com/v1/me"
    profile_data = fetch_spotify_data(profile_url, headers)

    top_tracks_url = f"https://api.spotify.com/v1/me/top/tracks?time_range={time_range}&limit=5"
    top_tracks_data = fetch_spotify_data(top_tracks_url, headers).get("items", [])

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
        {"type": "song_transitions", "title": "", },
        {"type": "top_tracks", "title": "Top Tracks", "content": top_tracks_data},
        {"type": "song_playback:", "title": "Top Songs", "content": top_tracks_data, "token": access_token, },
        {"type": "top_artists", "title": "Top Artists", "content": top_artists_data},
        {"type": "playlists", "title": "Playlists", "content": playlists_data,},
        {"type": "top_genres", "title": "Top Genres", "content": [{"genre": genre, "count": count} for genre, count in top_genres]},
        {"type": "end", "title": "The End", "content": profile_data,},
    ]

    return render(request, "slides.html", {"slides": slides})

def halloween(request, time_range):
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("spotify_login")
        # return render(request, "error.html", {"error": "Failed to obtain access token."})

    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch Spotify data
    profile_url = "https://api.spotify.com/v1/me"
    profile_data = fetch_spotify_data(profile_url, headers)

    top_tracks_url = f"https://api.spotify.com/v1/me/top/tracks?time_range={time_range}&limit=5"
    top_tracks_data = fetch_spotify_data(top_tracks_url, headers).get("items", [])

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
        {"type": "profile", "title": "Welcome to Your Spooky Wrapped!", "content": profile_data},
        {"type": "song_transitions", "title": "", },
        {"type": "top_tracks", "title": "Top Tracks", "content": top_tracks_data},
        {"type": "song_playback:", "title": "Top Songs", "content": top_tracks_data, "token": access_token, },
        {"type": "top_artists", "title": "Top Artists", "content": top_artists_data},
        {"type": "playlists", "title": "Playlists", "content": playlists_data,},
        {"type": "top_genres", "title": "Top Genres", "content": [{"genre": genre, "count": count} for genre, count in top_genres]},
        {"type": "end", "title": "The End", "content": profile_data,},
    ]

    return render(request, "slides.html", {"slides": slides})

def holiday(request, time_range):
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("spotify_login")
        # return render(request, "error.html", {"error": "Failed to obtain access token."})

    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch Spotify data
    profile_url = "https://api.spotify.com/v1/me"
    profile_data = fetch_spotify_data(profile_url, headers)

    top_tracks_url = f"https://api.spotify.com/v1/me/top/tracks?time_range={time_range}&limit=5"
    top_tracks_data = fetch_spotify_data(top_tracks_url, headers).get("items", [])

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
        {"type": "profile", "title": "Welcome to Your Holiday Wrapped!", "content": profile_data},
        {"type": "song_transitions", "title": "", },
        {"type": "top_tracks", "title": "Top Tracks", "content": top_tracks_data},
        {"type": "song_playback:", "title": "Top Songs", "content": top_tracks_data, "token": access_token, },
        {"type": "top_artists", "title": "Top Artists", "content": top_artists_data},
        {"type": "playlists", "title": "Playlists", "content": playlists_data,},
        {"type": "top_genres", "title": "Top Genres", "content": [{"genre": genre, "count": count} for genre, count in top_genres]},
        {"type": "end", "title": "The End", "content": profile_data,},
    ]

    return render(request, "slides.html", {"slides": slides})

# Views for specific time ranges
@spotify_login_required
def short(request):
    return wrapped(request, "short_term")

@spotify_login_required
def medium(request):
    return wrapped(request, "medium_term")

@spotify_login_required
def long(request):
    return wrapped(request, "long_term")

@spotify_login_required
def halloweenWrapped(request):
    return halloween(request, "short-term")

@spotify_login_required
def holidayWrapped(request):
    return holiday(request, "short-term")