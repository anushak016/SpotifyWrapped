from django.urls import path
from . import views

urlpatterns = [
    path("spotify/login/", views.spotify_login, name="spotify_login"),  # Spotify login
    path("spotify/redirect/", views.spotify_callback, name="spotify_callback"),  # Spotify redirect
    path("timeline-game/", views.timeline_game, name="timeline_game"),  # Timeline game
    path("submit-timeline/", views.submit_timeline, name="submit_timeline"),  # Submit timeline
    path("popularity-challenge/", views.popularity_challenge, name="popularity_challenge"),  # Popularity challenge
    path("submit-popularity-challenge/", views.submit_popularity_challenge, name="submit_popularity_challenge"),  # Submit popularity
]

