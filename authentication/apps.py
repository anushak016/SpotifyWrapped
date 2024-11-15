from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """
       Configuration class for the 'authentication' application in a Django project.

       This class inherits from `AppConfig` and is used to define configuration settings
       for the 'authentication' app. It sets the default auto field type for model primary keys
       and the name of the app within the Django project.

       Attributes:
           default_auto_field (str): The default type for automatically generated primary keys in models.
           name (str): The name of the application as used in Django's settings and app registry.

       Methods:
           __init__(self, *args, **kwargs): Initializes the app configuration with default values for auto field and app name.
       """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
