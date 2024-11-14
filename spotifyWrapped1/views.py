from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import requests
import base64
import random


# View to test Spotify credentials
def test_spotify_credentials(request):
    return HttpResponse(f"Client ID: {settings.SPOTIFY_CLIENT_ID}, Redirect URI: {settings.SPOTIFY_REDIRECT_URI}")


# View to initiate Spotify login
def spotify_login(request):
    auth_url = (
        "https://accounts.spotify.com/authorize?"
        f"client_id={settings.SPOTIFY_CLIENT_ID}&"
        "response_type=code&"
        f"redirect_uri={settings.SPOTIFY_REDIRECT_URI}&"
        "scope=user-top-read"
    )
    return redirect(auth_url)


# View to handle the callback from Spotify and retrieve the access token
def spotify_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponse("Error: No code returned from Spotify.")

    auth_str = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    auth_bytes = auth_str.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
    }

    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    response_data = response.json()
    access_token = response_data.get("access_token")

    if not access_token:
        return HttpResponse("Error: Unable to retrieve access token.")

    # Store the access token in session
    request.session["access_token"] = access_token

    return redirect("spotify_game")  # Redirect to the game view


# Helper function to get user's top tracks
def get_top_tracks(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": 10, "time_range": "long_term"}  # Retrieves top tracks over the past year
    response = requests.get("https://api.spotify.com/v1/me/top/tracks", headers=headers, params=params)

    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        return []


# View for the game where users guess their listening habits
def spotify_game(request):
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("spotify_login")

    # Fetch top tracks
    top_tracks = get_top_tracks(access_token)

    # Structure game data (track name, artist, etc.)
    game_data = [
        {
            "track_name": track["name"],
            "album_name": track["album"]["name"],
            "artist_name": track["artists"][0]["name"],
            "track_id": track["id"],
        }
        for track in top_tracks
    ]

    # Pass game data to the template
    context = {"game_data": game_data}
    return render(request, "spotify_game.html", context)


# View to handle user's guess submission
def submit_guess(request):
    if request.method == "POST":
        track_id = request.POST.get("track_id")
        guessed_month = request.POST.get("month")

        # Simulate a "correct" month for each track
        correct_month = random.choice([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])

        # Check if the guess is correct
        if guessed_month == correct_month:
            result = "Correct!"
        else:
            result = f"Incorrect. The correct month was {correct_month}."

        # Display result to user
        return render(request, "result.html", {"result": result, "track_id": track_id})
    else:
        return HttpResponseRedirect("spotify_game")