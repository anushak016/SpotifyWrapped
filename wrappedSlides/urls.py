# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.spotify_login, name="spotify_login"),
    path("redirect/", views.wrapped, name="spotify_callback"),
    path("homepage/", views.home, name="homepage"),
    path("long_term/", views.long_term, name="long_term"),
    path("medium_term/", views.medium_term, name="medium_term"),
    path("short_term/", views.short_term, name="short_term"),
    path("christmas/", views.christmas, name="christmas"),
    path("halloween/", views.halloween, name="halloween"),
]
