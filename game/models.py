from django.db import models
from django.contrib.auth.models import User

class TopSong(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    spotify_order = models.IntegerField(default=0)  # Add a default value
    snippet_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} by {self.artist}"
