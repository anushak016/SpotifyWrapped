import requests, json
from django.conf import settings
from django.shortcuts import redirect, render
from urllib.parse import urlencode

# Create your views here.

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
    scope = 'user-top-read'
    auth_url = (
        "https://accounts.spotify.com/authorize"
        "?response_type=code"
        f"&client_id={settings.SPOTIFY_CLIENT_ID}"
        f"&redirect_uri={settings.SPOTIFY_REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(auth_url)
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
    return render(request, "home.html")

def wrapped(request):
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
    code = request.GET.get("code")
    if not code:
        return render(request, "home.html", {"error": "Authorization failed or was canceled"})

    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Step 3: Exchange the code for an access token
    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code != 200:
        return render(request, "error.html", {"error": "Failed to obtain access token."})

    response_data = response.json()
    access_token = response_data.get("access_token")

    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}

    # Step 4: Fetch user profile data
    profile_url = "https://api.spotify.com/v1/me"
    profile_response = requests.get(profile_url, headers=headers)
    profile_data = profile_response.json() if profile_response.status_code == 200 else None

    # Step 5: Fetch user’s top songs (tracks)
    top_tracks_url = "https://api.spotify.com/v1/me/top/tracks?limit=5"
    top_tracks_response = requests.get(top_tracks_url, headers=headers)
    top_tracks_data = top_tracks_response.json().get("items", []) if top_tracks_response.status_code == 200 else []

    # Step 6: Fetch user’s playlists
    playlists_url = "https://api.spotify.com/v1/me/playlists?limit=5"
    playlists_response = requests.get(playlists_url, headers=headers)
    playlists_data = playlists_response.json().get("items", []) if playlists_response.status_code == 200 else []

    # Step 7: Fetch user’s top artists
    top_artists_url = "https://api.spotify.com/v1/me/top/artists?limit=5"
    top_artists_response = requests.get(top_artists_url, headers=headers)
    top_artists_data = top_artists_response.json().get("items", []) if top_artists_response.status_code == 200 else []

    # Debug: Log the top tracks and top artists data to verify structure
    print("Top Tracks Data:", json.dumps(top_tracks_data, indent=2))
    print("Top Artists Data:", json.dumps(top_artists_data, indent=2))

    # Compile slides
    slides = [
        {
            "type": "profile",
            "title": "Your Profile",
            "content": profile_data,
        },
        {
            "type": "top_tracks",
            "title": "Top Tracks",
            "content": top_tracks_data,  # Corrected this to use the list directly
        },
        {
            "type": "top_artists",
            "title": "Top Artists",
            "content": top_artists_data,  # Corrected this to use the list directly
        },
        {
            "type": "playlists",
            "title": "Playlists",
            "content": playlists_data,  # Corrected this to use the list directly
        },
    ]

    return render(request, "profile.html", {"slides": slides})

def contact(request):
    """
        Renders the contact page template.

        This view function handles the HTTP request to display the contact page.
        It renders the 'contact.html' template and returns the response to the client.

        Parameters:
            request (HttpRequest): The request object containing metadata about the request.

        Returns:
            HttpResponse: The rendered HTML page (contact.html) to be returned to the client.
        """
    return render(request, "contact.html")