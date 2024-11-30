# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.spotify_login, name="spotify_login"),
    path("redirect/", views.wrapped, name="spotify_callback"),
    path("homepage/", views.home, name="homepage"),
path("game/timeline-game/", views.timeline_game, name="timeline_game"),
    path("game/submit-timeline/", views.submit_timeline, name="submit_timeline"),
]
