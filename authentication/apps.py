from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'

class GameConfig(AppConfig):
        default_auto_field = 'django.db.models.BigAutoField'
        name = 'game'
