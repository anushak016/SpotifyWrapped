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
    path("", views.home, name="homepage"),
]
