# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.spotify_login, name="spotify_login"),
    path("redirect/", views.spotify_callback, name="spotify_callback"),
    path("original", views.original_wrapped, name="original_wrapped"),
    path("longterm", views.long, name="long_term"),
    path("shortterm", views.short, name="short_term"),
    path("mediumterm", views.medium, name="medium_term"),
    path("christmas", views.holidayWrapped, name="christmas"),
    path("halloween", views.halloweenWrapped, name="halloween"),
    path("homepage/", views.home, name="homepage"),
    path("long_term/", views.long_term, name="long_term"),
    path("medium_term/", views.medium_term, name="medium_term"),
    path("short_term/", views.short_term, name="short_term"),
    path("christmas/", views.christmas, name="christmas"),
    path("halloween/", views.halloween, name="halloween"),
]
