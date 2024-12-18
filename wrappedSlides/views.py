from django.http import HttpResponse
from authentication.models import SavedWrap
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from functools import wraps  # Add this import
import requests
from django.conf import settings
from collections import Counter
import datetime  # Add this import
import requests
import json
import os
import random
from collections import Counter
from django.conf import settings
from functools import wraps
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.http import JsonResponse


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

@login_required(login_url='/auth/login/')
def spotify_callback(request):
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
        
        # Store tokens in both profile and session
        profile = request.user.profile
        profile.spotify_token = token_data['access_token']
        profile.spotify_refresh_token = token_data['refresh_token']
        profile.spotify_token_expires = timezone.now() + datetime.timedelta(seconds=token_data['expires_in'])
        profile.save()

        # Store access token in session
        request.session['access_token'] = token_data['access_token']

        # Redirect to saved path or home
        redirect_path = request.session.pop('redirect_after_login', 'home')
        return redirect(redirect_path)

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

def fetch_spotify_data(url, headers):
    """Helper function to fetch data from Spotify API"""
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {}

@login_required(login_url='/auth/login/')
def wrapped(request, time_range, theme):
    # Get the current theme from session
    current_theme = request.session.get('theme', 'light')
    
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("spotify_login")

    headers = {"Authorization": f"Bearer {access_token}"}

    # Use the fetch_spotify_data helper function
    profile_url = "https://api.spotify.com/v1/me"
    profile_data = fetch_spotify_data(profile_url, headers)

    if time_range == "default":
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
        top_tracks_url = f"https://api.spotify.com/v1/me/top/tracks?time_range={time_range}&limit=5"
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
        {"type": "song_playback:", "title": "Listen Back To Your Favorites", "content": top_tracks_data, "token": access_token, },
        {"type": "top_artists", "title": "Top Artists", "content": top_artists_data},
        {"type": "playlists", "title": "Playlists", "content": playlists_data,},
        {"type": "top_genres", "title": "Top Genres", "content": [{"genre": genre, "count": count} for genre, count in top_genres]},
        {"type": "end", "title": "The Journey Comes to An End", "content": profile_data,},
    ]

    # Save the wrap to the user's profile
    request.user.profile.save_wrap(
        wrap_type=f"{time_range}_{theme}",
        slides=slides
    )

    if theme == "christmas":
        return render(request, "christmas.html", {"slides": slides})
    elif theme == "halloween":
        return render(request, "halloween.html", {"slides": slides})
    else:
        return render(request, "slides.html", {
            "slides": slides,
            "current_theme": current_theme
        })

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

@login_required(login_url='/auth/login/')
def original_wrapped(request):
    if not request.user.profile.spotify_token:
        return redirect('spotify_login')
    return wrapped(request, "default", "none")

@login_required(login_url='/auth/login/')
def long_term(request):
    if not request.user.profile.spotify_token:
        return redirect('spotify_login')
    return wrapped(request, "long_term", "none")

@login_required(login_url='/auth/login/')
def medium_term(request):
    if not request.user.profile.spotify_token:
        return redirect('spotify_login')
    return wrapped(request, "medium_term", "none")

@login_required(login_url='/auth/login/')
def short_term(request):
    if not request.user.profile.spotify_token:
        return redirect('spotify_login')
    return wrapped(request, "short_term", "none")

@login_required(login_url='/auth/login/')
def christmas(request):
    if not request.user.profile.spotify_token:
        return redirect('spotify_login')
    return wrapped(request, "default", "christmas")

@login_required(login_url='/auth/login/')
def halloween(request):
    if not request.user.profile.spotify_token:
        return redirect('spotify_login')
    return wrapped(request, "default", "halloween")

@login_required(login_url='/auth/login/')
def view_wrap(request, wrap_id):
    try:
        # Get the saved wrap
        wrap = SavedWrap.objects.get(id=wrap_id, profile=request.user.profile)
        
        # Get the slides data
        slides = wrap.wrap_data
        
        # Determine which template to use based on wrap type
        if "christmas" in wrap.wrap_type:
            return render(request, "christmas.html", {"slides": slides})
        elif "halloween" in wrap.wrap_type:
            return render(request, "halloween.html", {"slides": slides})
        else:
            return render(request, "slides.html", {"slides": slides})
    except SavedWrap.DoesNotExist:
        return redirect('home')

@login_required(login_url='/auth/login/')
def delete_wrap(request, wrap_id):
    if request.method == 'POST':
        try:
            wrap = SavedWrap.objects.get(id=wrap_id, profile=request.user.profile)
            wrap.delete()
            return HttpResponse(status=200)
        except SavedWrap.DoesNotExist:
            return HttpResponse(status=404)
    return HttpResponse(status=405)


def contact(request):
    """
        View for displaying the contact page.

        This view renders the `contact.html` template, providing the user with a page
        to contact the service or support team.

        Args:
            request (HttpRequest): The HTTP request object containing session data and request details.

        Returns:
            HttpResponse: A rendered response using the `contact.html` template.
    """
    context = {
        'language_name': _('English')
    }
    return render(request, "contact.html")

# Timeline Game View
@spotify_login_required
def timeline_game(request):
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("spotify_login")

    current_theme = request.session.get('theme', 'light')
    tracks = fetch_top_tracks(access_token)
    if not tracks:
        return render(request, "error.html", {"message": "Unable to load your top tracks. Please try again later."})

    randomized_tracks = random.sample(tracks, len(tracks))
    request.session["correct_order"] = [track["id"] for track in tracks]

    return render(request, "timeline_game.html", {
        "tracks": randomized_tracks,
        "current_theme": current_theme
    })

# Submit Timeline View
@spotify_login_required
def submit_timeline(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            submitted_order = data.get("track_order", [])
            correct_order = request.session.get("correct_order", [])

            # Calculate score
            score = sum(1 for i, track_id in enumerate(submitted_order) if track_id == correct_order[i])
            total = len(correct_order)

            return JsonResponse({"score": score, "total": total, "correct_order": correct_order})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "This endpoint only accepts POST requests."}, status=405)

def fetch_top_tracks(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://api.spotify.com/v1/me/top/tracks?limit=10"

    response = requests.get(url, headers=headers)

    # Debugging: Log the full API response
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")

    if response.status_code != 200:
        print(f"Error fetching tracks: {response.status_code} - {response.text}")
        return []

    try:
        data = response.json()
        if "items" not in data or not data["items"]:
            print("No tracks found in the API response.")
            return []

        tracks = [
            {
                "id": item["id"],
                "title": item["name"],
                "artist": item["artists"][0]["name"],
                "popularity": item.get("popularity", 0),  # Include popularity for the challenge
            }
            for item in data["items"]
        ]
        print("Fetched Tracks:", tracks)  # Debugging: Print fetched tracks
        return tracks
    except Exception as e:
        print(f"Error decoding JSON response: {e}")
        return []

# Popularity Challenge View
@spotify_login_required
def popularity_challenge(request):
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("spotify_login")

    tracks = fetch_top_tracks(access_token)
    if not tracks:
        return render(request, "error.html", {"message": "Unable to load tracks for the challenge."})

    # Sort tracks by popularity
    correct_order = sorted(tracks, key=lambda x: x["popularity"], reverse=True)
    request.session["correct_order_popularity"] = [track["id"] for track in correct_order]
    request.session["popularity_attempts"] = 0  # Track failed attempts

    return render(request, "popularity_challenge.html", {"tracks": tracks})

# Submit Popularity Challenge View
def submit_popularity_challenge(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_order = data.get("track_order", [])
        correct_order = request.session.get("correct_order_popularity", [])

        if not correct_order:
            return JsonResponse({"error": "Correct order not available."})

        # Track attempts
        attempts = request.session.get("popularity_attempts", 0)

        # Calculate score
        score = sum(1 for i, track_id in enumerate(user_order) if track_id == correct_order[i])
        is_correct = score == len(correct_order)

        # Increment attempt count
        if not is_correct:
            attempts += 1
            request.session["popularity_attempts"] = attempts

        # Check for 5 failed attempts
        if attempts >= 5 and not is_correct:
            request.session["popularity_attempts"] = 0  # Reset attempts
            return JsonResponse({
                "message": "it's called a challenge for a reason...better luck next time",
                "show_correct": True,
                "correct_order": correct_order,
            })

        return JsonResponse({"score": score, "total": len(correct_order), "is_correct": is_correct})
    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)