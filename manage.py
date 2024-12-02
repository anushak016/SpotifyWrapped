#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """
    Run administrative tasks for the Django project.

    This function is used to set up the necessary environment for
    running Django's command-line utility and to execute administrative
    tasks (like running the development server or managing migrations).

    It sets the `DJANGO_SETTINGS_MODULE` environment variable to specify
    the settings module for the project. It also attempts to import and
    execute Django's `execute_from_command_line` function to handle the
    command-line arguments passed to the script.

    Raises:
        ImportError: If Django is not installed or cannot be found on the PYTHONPATH.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify_wrapped.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
