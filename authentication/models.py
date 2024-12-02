from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    security_question = models.CharField(max_length=255)
    security_answer = models.CharField(max_length=255)

    def __str__(self):
        return self.user.username

class TopSong(models.Model):
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        title = models.CharField(max_length=255)
        artist = models.CharField(max_length=255)
        spotify_order = models.IntegerField(default=0)  # Add a default value
        snippet_url = models.URLField(null=True, blank=True)

        def __str__(self):
            return f"{self.title} by {self.artist}"
