# signals.py in authentication app
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """
            Creates a profile for a newly registered user.

            This function is triggered after a new `User` instance is saved. If the user is newly created,
            it automatically creates a `Profile` instance associated with the user.

        Parameters:
            sender (Model): The model class that triggered the signal (User).
            instance (User): The user instance that was just saved.
            created (bool): A boolean that indicates whether the instance was newly created.
            **kwargs: Additional keyword arguments passed by the signal.

        Returns:
            None
    """
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    """
            Saves the profile whenever the user instance is saved.

            This function is triggered every time a `User` instance is saved. It ensures that the associated
            `Profile` instance is also saved to persist any changes made to the profile.

        Parameters:
            sender (Model): The model class that triggered the signal (User).
            instance (User): The user instance that was just saved.
            **kwargs: Additional keyword arguments passed by the signal.

        Returns:
            None
    """
    instance.profile.save()