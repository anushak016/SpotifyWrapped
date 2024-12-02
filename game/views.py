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

# Spotify Login View
def spotify_login(request):
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
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }

    response = requests.post(token_url, data=payload)
    response_data = response.json()

    # Debugging: Log the token response
    print(f"Spotify Token Response: {response_data}")

    # Save tokens in the session
    access_token = response_data.get("access_token")
    refresh_token = response_data.get("refresh_token")

    if access_token:
        request.session["spotify_access_token"] = access_token
    if refresh_token:
        request.session["spotify_refresh_token"] = refresh_token

    return redirect("timeline_game")

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
    if not access_token:
        return redirect("spotify_login")

    print(f"Access Token: {access_token}")  # Debugging

    tracks = fetch_top_tracks(access_token)
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

            # Calculate score
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

    # Sort tracks by popularity
    correct_order = sorted(tracks, key=lambda x: x["popularity"], reverse=True)
    request.session["correct_order_popularity"] = [track["id"] for track in correct_order]
    request.session["popularity_attempts"] = 0  # Track failed attempts

    return render(request, "game/popularity_challenge.html", {"tracks": tracks})

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