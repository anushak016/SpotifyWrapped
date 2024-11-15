from django.apps import AppConfig

class WrappedslidesConfig(AppConfig):
    """
        Configuration for the WrappedSlides Django application.

        This class configures the WrappedSlides app, which is responsible for managing the slides displayed on the user profile
        in the Spotify Wrapped functionality. It inherits from Django's AppConfig and sets the default auto field type as
        'BigAutoField', and specifies the name of the application as 'wrappedSlides'.

        Attributes:
            default_auto_field (str): The default type for auto-generated primary keys. Set to 'BigAutoField' for large integer fields.
            name (str): The name of the Django application, 'wrappedSlides'.

        """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wrappedSlides'
