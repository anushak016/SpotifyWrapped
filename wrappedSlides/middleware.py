from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from .utils import refresh_spotify_token

class SpotifyAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Exclude these paths from requiring authentication
        excluded_paths = [
            '/',  # Home page
            '/auth/login/',
            '/auth/register/',
            '/auth/reset_password/',
            '/auth/logout/',
            '/static/',
            '/admin/',
            '/spotify/login/',  # Add Spotify login path
            '/spotify/redirect/'  # Add Spotify callback path
        ]
        
        if any(request.path.startswith(path) for path in excluded_paths):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect('login')
            
        # Check if user has Spotify token for all authenticated pages
        if request.user.is_authenticated and not request.user.profile.spotify_token:
            return redirect('spotify_login')
            
        # Check if token needs refresh
        if request.user.is_authenticated and request.user.profile.spotify_token_expires:
            if request.user.profile.spotify_token_expires <= timezone.now():
                if not refresh_spotify_token(request.user.profile):
                    return redirect('spotify_login')

        return self.get_response(request)