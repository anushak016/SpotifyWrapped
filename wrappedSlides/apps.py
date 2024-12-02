from django.apps import AppConfig


class WrappedslidesConfig(AppConfig):
    """
        Configuration class for the 'wrappedSlides' application.

        This class is used by Django to configure application-specific
        settings for the 'wrappedSlides' app.

        Attributes:
            default_auto_field (str): Specifies the type of auto-generated primary key field.
                                      Default is 'django.db.models.BigAutoField'.
            name (str): The name of the application, as used in Django's settings and import paths.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wrappedSlides'
