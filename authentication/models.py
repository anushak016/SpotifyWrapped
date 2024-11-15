from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Profile(models.Model):
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
