# Generated by Django 5.1.1 on 2024-11-30 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='email',
            field=models.EmailField(default='default@example.com', max_length=254, unique=True),
        ),
    ]
