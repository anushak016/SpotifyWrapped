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
    """
           Initiates the Spotify OAuth authorization flow by redirecting the user to Spotify's login page.

           This view function constructs the URL required for Spotify's authorization process, which includes the client ID,
           redirect URI, and required scope. It then redirects the user to this URL to begin the OAuth authorization flow.

           Parameters:
               request (HttpRequest): The HTTP request object that triggers the login process.

           Returns:
               HttpResponseRedirect: A redirect response to Spotify's authorization page, where the user can grant access to their data.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """
        Wrapper function to check if the user is authenticated before accessing a view.

        This function is used to protect views by ensuring that the user is authenticated
        (i.e., has an access token stored in the session). If the user is not authenticated,
        it stores the requested path in the session and redirects the user to the Spotify login
        page. Once the user logs in, they will be redirected back to the saved destination.

        Args:
            request (HttpRequest): The HTTP request object containing session data and request details.
            *args: Additional positional arguments passed to the wrapped view function.
            **kwargs: Additional keyword arguments passed to the wrapped view function.

        Returns:
            HttpResponse: A redirect response to the Spotify login page if the user is not authenticated,
                           or the original view response if the user is authenticated.

        Example:
            @login_required_view
            def my_view(request):
                # View code here
        """
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
    """
        Get an access token from Spotify using the authorization code.

        This function sends a POST request to Spotify's token endpoint to exchange
        the provided authorization code for an access token. It includes necessary
        credentials (client ID, client secret, and redirect URI) and returns the
        access token if the request is successful (HTTP status code 200). If the
        request fails or the access token is not returned, it returns None.

        Args:
            auth_code (str): The authorization code received from Spotify after the user grants permission.

        Returns:
            str or None: The access token if the request is successful, otherwise None.

    """
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


# Utility function to fetch data from Spotify API
def fetch_spotify_data(url, headers):
    """
        Fetch data from the Spotify API.

        This function sends a GET request to the specified URL with the provided
        headers, typically for interacting with the Spotify API. If the request is
        successful (HTTP status code 200), it returns the response data as a JSON object.
        If the request fails or the status code is not 200, it returns an empty dictionary.

        Args:
            url (str): The URL to which the GET request is sent, typically an API endpoint.
            headers (dict): A dictionary of headers to include in the request, such as authorization tokens.

        Returns:
            dict: The JSON response data from the API if the request is successful, otherwise an empty dictionary.

    """
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {}

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

# Spotify login view
def spotify_login(request):
    """
           Initiates the Spotify OAuth authorization flow by redirecting the user to Spotify's login page.

           This view function constructs the URL required for Spotify's authorization process, which includes the client ID,
           redirect URI, and required scope. It then redirects the user to this URL to begin the OAuth authorization flow.

           Parameters:
               request (HttpRequest): The HTTP request object that triggers the login process.

           Returns:
               HttpResponseRedirect: A redirect response to Spotify's authorization page, where the user can grant access to their data.
           """
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
    """
        Handle the callback from Spotify after user authentication.

        This function is called when Spotify redirects back to the application after
        the user grants permission. It retrieves the authorization code from the
        request, exchanges it for an access token, and stores the token in the session.
        If authentication is successful, the user is redirected to the originally
        requested page (if available) or to the homepage. If the authentication fails,
        an error message is displayed.

        Args:
            request (HttpRequest): The HTTP request object containing the authorization code
                                   and session data.

        Returns:
            HttpResponse: A redirect to the original destination or homepage if successful,
                           or a rendered error page if authentication fails.

        Example:
            @spotify_callback
            def callback_view(request):
                # Callback handling logic
    """
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
    """
            Renders the home page of the application.

            This view function is responsible for rendering the "home.html" template. It does not process any input or perform
            any dynamic operations, but simply returns the static home page view.

            Parameters:
                request (HttpRequest): The HTTP request object that triggers the rendering of the home page.

            Returns:
                HttpResponse: A response that renders the "home.html" template to the client.
    """
    context = {
        'language_name': _('English')
    }
    return render(request, "homepage.html")

# Reusable wrapped view for different time ranges
def wrapped(request, time_range, theme):
    """
            Handles the Spotify OAuth authorization code flow and retrieves user data.

            This view function processes the authorization code received from Spotify, exchanges it for an access token,
            and then fetches the user's profile data, top tracks, top artists, and playlists from the Spotify API.
            It prepares the data to be displayed on the user's profile page.

            Steps:
                1. Get the authorization code from the GET request.
                2. Exchange the authorization code for an access token.
                3. Use the access token to fetch the user's profile data.
                4. Fetch the user's top tracks, top artists, and playlists.
                5. Prepare the data and render it on the profile page.

            Parameters:
                request (HttpRequest): The HTTP request object containing the authorization code and other metadata.

            Returns:
                HttpResponse: The rendered profile page with the user's Spotify data, or an error page if any step fails.
    """
    context = {
        'language_name': _('English')
    }
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
    """
        View for displaying default wrapped data for the user.

        This view is decorated with the `spotify_login_required` decorator to ensure
        that only authenticated users with a valid Spotify access token can access it.
        It calls the `wrapped` function to display the default wrapped data for the user.

        Args:
            request (HttpRequest): The HTTP request object containing session data and request details.

        Returns:
            HttpResponse: The response from the `wrapped` function displaying the default wrapped data.
    """
    context = {
        'language_name': _('English')
    }
    return wrapped(request, "default", "none")

@spotify_login_required
def short(request):
    """
        View for displaying short-term wrapped data for the user.

        This view is decorated with the `spotify_login_required` decorator to ensure
        that only authenticated users with a valid Spotify access token can access it.
        It calls the `wrapped` function to display short-term wrapped data for the user.

        Args:
            request (HttpRequest): The HTTP request object containing session data and request details.

        Returns:
            HttpResponse: The response from the `wrapped` function displaying the short-term wrapped data.
    """
    context = {
        'language_name': _('English')
    }
    return wrapped(request, "short_term", "none")

@spotify_login_required
def medium(request):
    """
        View for displaying medium-term wrapped data for the user.

        This view is decorated with the `spotify_login_required` decorator to ensure
        that only authenticated users with a valid Spotify access token can access it.
        It calls the `wrapped` function to display medium-term wrapped data for the user.

        Args:
            request (HttpRequest): The HTTP request object containing session data and request details.

        Returns:
            HttpResponse: The response from the `wrapped` function displaying the medium-term wrapped data.
    """
    context = {
        'language_name': _('English')
    }
    return wrapped(request, "medium_term", "none")

@spotify_login_required
def long(request):
    """
        View for displaying long-term wrapped data for the user.

        This view is decorated with the `spotify_login_required` decorator to ensure
        that only authenticated users with a valid Spotify access token can access it.
        It calls the `wrapped` function to display long-term wrapped data for the user.

        Args:
            request (HttpRequest): The HTTP request object containing session data and request details.

        Returns:
            HttpResponse: The response from the `wrapped` function displaying the long-term wrapped data.
    """
    context = {
        'language_name': _('English')
    }
    return wrapped(request, "long_term", "none")

@spotify_login_required
def halloween(request):
    """
       View for displaying Halloween-themed wrapped data for the user.

       This view is decorated with the `spotify_login_required` decorator to ensure
       that only authenticated users with a valid Spotify access token can access it.
       It calls the `wrapped` function to display Halloween-themed wrapped data for the user.

       Args:
           request (HttpRequest): The HTTP request object containing session data and request details.

       Returns:
           HttpResponse: The response from the `wrapped` function displaying the Halloween-themed wrapped data.
    """
    context = {
        'language_name': _('English')
    }
    return wrapped(request, "default", "halloween")

@spotify_login_required
def holiday(request):
    """
        View for displaying Christmas-themed wrapped data for the user.

        This view is decorated with the `spotify_login_required` decorator to ensure
        that only authenticated users with a valid Spotify access token can access it.
        It calls the `wrapped` function to display Christmas-themed wrapped data for the user.

        Args:
            request (HttpRequest): The HTTP request object containing session data and request details.

        Returns:
            HttpResponse: The response from the `wrapped` function displaying the Christmas-themed wrapped data.
    """
    context = {
        'language_name': _('English')
    }
    return wrapped(request, "default", "christmas")

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

    print(f"Access Token: {access_token}")  # Debugging

    tracks = fetch_top_tracks(access_token)
    if not tracks:
        return render(request, "error.html", {"message": "Unable to load your top tracks. Please try again later."})

    randomized_tracks = random.sample(tracks, len(tracks))
    request.session["correct_order"] = [track["id"] for track in tracks]

    return render(request, "timeline_game.html", {"tracks": randomized_tracks})

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