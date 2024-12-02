# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.spotify_login, name="spotify_login"),
    path("redirect/", views.spotify_callback, name="spotify_callback"),  # Changed from "callback/" to "redirect/"
    path("wrapped/", views.original_wrapped, name="wrapped"),  # Change this to use original_wrapped
    path("long/", views.long_term, name="long_term"),
    path("medium/", views.medium_term, name="medium_term"),
    path("short/", views.short_term, name="short_term"),
    path("christmas/", views.christmas, name="christmas"),
    path("halloween/", views.halloween, name="halloween"),
    path("wrap/<int:wrap_id>/", views.view_wrap, name="view_wrap"),
    path("wrap/<int:wrap_id>/delete/", views.delete_wrap, name="delete_wrap"),
    path("", views.home, name="homepage"),
    path("contact/", views.contact, name="contact"),
    path("timeline-game/", views.timeline_game, name="timeline_game"),
    path("submit-timeline/", views.submit_timeline, name="submit_timeline"),
    path("popularity-challenge/", views.popularity_challenge, name="popularity_challenge"),
    path("submit-popularity-challenge/", views.submit_popularity_challenge, name="submit_popularity_challenge"),
]
