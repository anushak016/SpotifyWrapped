from django.contrib import admin
from .models import Profile

class ProfileAdmin(admin.ModelAdmin):
    """
            Custom admin interface for managing `Profile` instances in the Django admin site.

            This class customizes how the `Profile` model is displayed and interacted with in the Django admin interface.
            It allows for better visibility and management of `Profile` objects by specifying which fields should
            be shown in the list view.

            Attributes:
                list_display (tuple): A tuple of field names to be displayed in the list view of the `Profile` model
                                       within the Django admin interface. In this case, the `user` and `security_question`
                                       fields are displayed.

            Methods:
                list_display(self): Defines the fields to be shown in the list view of the admin interface for `Profile` model.
    """
    list_display = ('user', 'security_question')
# Register your models here.
admin.site.register(Profile)