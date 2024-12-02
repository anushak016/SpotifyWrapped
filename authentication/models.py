from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Profile(models.Model):
    """
           A model that stores additional information for a user, including their security question and answer.

           This model is associated with a specific `User` through a one-to-one relationship and stores
           a security question and its corresponding answer. It is used to manage user profiles that can
           include personalized security information.

           Attributes:
               user (OneToOneField): A one-to-one relationship with the `User` model. This field links
                                      each profile to a specific user.
               security_question (CharField): A field that stores the security question associated with the user.
               security_answer (CharField): A field that stores the answer to the security question.

           Methods:
               __str__(self): Returns the string representation of the profile, which is the username of the associated user.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    security_question = models.CharField(max_length=255)
    security_answer = models.CharField(max_length=255)

    def __str__(self):
        """
            Returns the string representation of the profile, which is the username of the associated user.

            Returns:
                str: The username of the associated user.
        """
        return self.user.username

class TopSong(models.Model):
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        title = models.CharField(max_length=255)
        artist = models.CharField(max_length=255)
        spotify_order = models.IntegerField(default=0)  # Add a default value
        snippet_url = models.URLField(null=True, blank=True)

        def __str__(self):
            return f"{self.title} by {self.artist}"
