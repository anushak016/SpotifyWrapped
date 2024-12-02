# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.spotify_login, name="spotify_login"),
    path("redirect/", views.spotify_callback, name="spotify_callback"),
    path("original/", views.default, name="original_wrapped"),
    path("longterm/", views.long, name="long_term"),
    path("shortterm/", views.short, name="short_term"),
    path("mediumterm/", views.medium, name="medium_term"),
    path("christmas/", views.holiday, name="christmas"),
    path("halloween/", views.halloween, name="halloween"),
    path("homepage/", views.home, name="homepage"),
    path("contact/", views.contact, name="contact"),
    path("timeline-game/", views.timeline_game, name="timeline_game"),  # Timeline game route
    path("submit-timeline/", views.submit_timeline, name="submit_timeline"),  # Submit timeline route
    path("popularity-challenge/", views.popularity_challenge, name="popularity_challenge"),
    path("submit-popularity-challenge/", views.submit_popularity_challenge, name="submit_popularity_challenge"),
]
