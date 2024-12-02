import json
import os
import random
import requests
from django.http import JsonResponse
from django.shortcuts import redirect, render

# Spotify API Credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")


# Fetch the user's top tracks
def fetch_top_tracks(access_token, refresh_token=None):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://api.spotify.com/v1/me/top/tracks?limit=10"

    response = requests.get(url, headers=headers)

    # Check for expired token (401 Unauthorized)
    if response.status_code == 401 and refresh_token:
        access_token = refresh_access_token(refresh_token)
        if access_token:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(url, headers=headers)
        else:
            return []  # Return empty if token refresh fails

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
                "popularity": item.get("popularity", 0),
            }
            for item in data["items"]
        ]
        return tracks
    except Exception as e:
        print(f"Error decoding JSON response: {e}")
        return []

def refresh_access_token(refresh_token):
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }

    response = requests.post(token_url, data=payload)

    if response.status_code != 200:
        print(f"Failed to refresh token: {response.status_code} - {response.text}")
        return None

    response_data = response.json()
    new_access_token = response_data.get("access_token")

    if new_access_token:
        print("Access token refreshed successfully.")
    else:
        print("Failed to retrieve new access token.")

    return new_access_token

def spotify_callback(request):
    code = request.GET.get("code")
    print(f"Received Code: {code}")  # Debugging

    if not code:
        return redirect("home")

    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }

    response = requests.post(token_url, data=payload)
    print(f"Token Exchange Response: {response.status_code}, {response.text}")  # Debugging

    if response.status_code != 200:
        return redirect("home")

    response_data = response.json()
    access_token = response_data.get("access_token")
    refresh_token = response_data.get("refresh_token")

    print(f"Access Token: {access_token}, Refresh Token: {refresh_token}")  # Debugging

    if access_token:
        request.session["spotify_access_token"] = access_token
    if refresh_token:
        request.session["spotify_refresh_token"] = refresh_token
        if not access_token and not refresh_token:
            logger.warning("No tokens found, redirecting to login.")
            return redirect("spotify_login")

    return redirect("timeline_game")


# Spotify Login View
def spotify_login(request):
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_REDIRECT_URI:
        raise ValueError("Spotify credentials are not set in the environment")

    scope = "user-top-read"
    spotify_auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={SPOTIFY_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={SPOTIFY_REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(spotify_auth_url)

# Spotify Callback View
def spotify_callback(request):
    code = request.GET.get("code")
    if not code:
        return redirect("home")

    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }

    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        print(f"Token exchange failed: {response.status_code} - {response.text}")
        return redirect("home")

    response_data = response.json()
    access_token = response_data.get("access_token")
    refresh_token = response_data.get("refresh_token")

    if access_token:
        request.session["spotify_access_token"] = access_token
    if refresh_token:
        request.session["spotify_refresh_token"] = refresh_token

    return redirect("timeline_game")


# Refresh Access Token
def refresh_access_token(refresh_token):
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(token_url, data=payload)
    response_data = response.json()
    return response_data.get("access_token")


# Timeline Game View
def timeline_game(request):
    access_token = request.session.get("spotify_access_token")
    refresh_token = request.session.get("spotify_refresh_token")

    # Refresh access token if it's missing or expired
    if not access_token and refresh_token:
        print("Refreshing access token...")
        access_token = refresh_access_token(refresh_token)
        if access_token:
            request.session["spotify_access_token"] = access_token
        else:
            return redirect("spotify_login")  # Redirect to login if token refresh fails

    if not access_token:
        return redirect("spotify_login")  # No valid tokens, force re-login

    tracks = fetch_top_tracks(access_token, refresh_token)
    if not tracks:
        return render(request, "error.html", {"message": "Unable to load your top tracks. Please try again later."})

    randomized_tracks = random.sample(tracks, len(tracks))
    request.session["correct_order"] = [track["id"] for track in tracks]

    return render(request, "game/timeline_game.html", {"tracks": randomized_tracks})

# Submit Timeline View
def submit_timeline(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            submitted_order = data.get("track_order", [])
            correct_order = request.session.get("correct_order", [])

            score = sum(1 for i, track_id in enumerate(submitted_order) if track_id == correct_order[i])
            total = len(correct_order)

            return JsonResponse({"score": score, "total": total, "correct_order": correct_order})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "This endpoint only accepts POST requests."}, status=405)


# Popularity Challenge View
def popularity_challenge(request):
    access_token = request.session.get("spotify_access_token")
    if not access_token:
        return redirect("spotify_login")

    tracks = fetch_top_tracks(access_token)
    if not tracks:
        return render(request, "error.html", {"message": "Unable to load tracks for the challenge."})

    correct_order = sorted(tracks, key=lambda x: x["popularity"], reverse=True)
    request.session["correct_order_popularity"] = [track["id"] for track in correct_order]
    request.session["popularity_attempts"] = 0

    return render(request, "game/popularity_challenge.html", {"tracks": tracks})


# Submit Popularity Challenge View
def submit_popularity_challenge(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_order = data.get("track_order", [])
        correct_order = request.session.get("correct_order_popularity", [])

        if not correct_order:
            return JsonResponse({"error": "Correct order not available."})

        attempts = request.session.get("popularity_attempts", 0)

        score = sum(1 for i, track_id in enumerate(user_order) if track_id == correct_order[i])
        is_correct = score == len(correct_order)

        if not is_correct:
            attempts += 1
            request.session["popularity_attempts"] = attempts

        if attempts >= 5 and not is_correct:
            request.session["popularity_attempts"] = 0
            return JsonResponse({
                "message": "It's called a challenge for a reason...better luck next time",
                "show_correct": True,
                "correct_order": correct_order,
            })

        return JsonResponse({"score": score, "total": len(correct_order), "is_correct": is_correct})

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)