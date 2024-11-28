from django.urls import path
from . import views

urlpatterns = [
    path("spotify/login/", views.spotify_login, name="spotify_login"),  # Login route
    path("spotify/redirect/", views.spotify_callback, name="spotify_callback"),  # Redirect route
    path("timeline-game/", views.timeline_game, name="timeline_game"),  # Game route
    path("submit-timeline/", views.submit_timeline, name="submit_timeline"),  # Submit timeline route
]
