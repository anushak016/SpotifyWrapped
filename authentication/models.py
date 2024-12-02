from django.db import models
from django.contrib.auth.models import User
import json

class SavedWrap(models.Model):
    profile = models.ForeignKey('Profile', related_name='saved_wraps', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    wrap_type = models.CharField(max_length=50)  # e.g., "original", "long_term", "christmas"
    wrap_data = models.JSONField()  # Stores the entire wrap data as JSON

    class Meta:
        ordering = ['-created_at']

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    security_question = models.CharField(max_length=255)
    security_answer = models.CharField(max_length=255)
    spotify_token = models.CharField(max_length=255, null=True, blank=True)
    spotify_refresh_token = models.CharField(max_length=255, null=True, blank=True)
    spotify_token_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def save_wrap(self, wrap_type, slides):
        """Helper method to save a wrap"""
        return SavedWrap.objects.create(
            profile=self,
            wrap_type=wrap_type,
            wrap_data=slides
        )

    def get_saved_wraps(self):
        """Helper method to get all saved wraps"""
        return self.saved_wraps.all()