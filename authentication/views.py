from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from .models import Profile
from django.db import IntegrityError
from django.urls import reverse
from django.utils.translation import gettext as _


def home_view(request):
    """
            Handles the home page view and manages user session after registration.

            This view function checks if the user has just registered by looking for the 'just_registered' flag in the session.
            If the flag is present, the user is logged out and redirected to the login page. Once logged out, the flag is removed
            from the session to prevent repeated logouts. If the user is not flagged as just registered, the home page is rendered.

            Parameters:
                request (HttpRequest): The HTTP request object that triggers this view.

            Returns:
                HttpResponseRedirect or HttpResponse:
                    - Redirects to the login page if the user was just registered and logged out.
                    - Renders the "home.html" template if no action is needed.
    """
    context = {
        'language_name': _('English')
    }
    # Check if the user has just registered
    if request.session.get('just_registered'):
        # Log out the user
        logout(request)
        # Remove the flag after logging out
        request.session.pop('just_registered', None)
        return redirect('login')  # Redirect them to the login page or other safe page
    return render(request, 'home.html')


def login_view(request):
    """
            Handles the login page view and manages user authentication.

            This view function checks if the user has just registered and logs them out if necessary, then redirects them to the
            login page. It processes the login form submission by verifying the user's credentials. If the credentials are correct,
            the user is logged in and redirected to the geolocator page. If authentication fails, an error message is displayed on
            the login page.

            Parameters:
                request (HttpRequest): The HTTP request object that triggers this view.

            Returns:
                HttpResponseRedirect or HttpResponse:
                    - Redirects to the 'geolocator' page if the login is successful.
                    - Renders the login page with an error message if the login fails.
                    - Renders the login page when the request method is GET.
    """
    context = {
        'language_name': _('English')
    }
    # Check if the user has just registered
    if request.session.get('just_registered'):
        logout(request)
        # Remove the flag after logging out
        request.session.pop('just_registered', None)
        return redirect('login')  # Redirect them to the login page or other safe page

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse('geolocator'))
        else:
            error_message = "Incorrect username or password."
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')

def logout_view(request):
    context = {
        'language_name': _('English')
    }
    """
            Handles the logout functionality for the user.

            This view function logs out the currently authenticated user and then redirects them to the login page.
            It ensures that the user is logged out by calling Django's `logout` function, which clears the user's session.

            Parameters:
                request (HttpRequest): The HTTP request object that triggers this view.

            Returns:
                HttpResponseRedirect:
                    Redirects the user to the login page after successfully logging them out.
    """
    logout(request)
    return redirect('/auth/login/')


def register_view(request):
    context = {
        'language_name': _('English')
    }
    """
           Handles user registration by validating the input data and creating a new user account.

           This view processes the registration form where the user provides a username, password,
           security question, and answer. It checks for errors such as an already existing username,
           mismatched passwords, or missing security question details. If the data is valid, it creates
           the user and their profile, including the security question and answer, then redirects the user
           to the login page.

           Parameters:
               request (HttpRequest): The HTTP request object that triggers this view.

           Returns:
               HttpResponse:
                   - Renders the registration page with an error message if validation fails.
                   - Redirects the user to the login page if registration is successful.
    """
    # Check if the user has just registered
    if request.session.get('just_registered'):
        # Log out the user
        logout(request)
        # Remove the flag after logging out
        request.session.pop('just_registered', None)
        return redirect('login')  # Redirect them to the login page or other safe page

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        security_question = request.POST['security_question']
        security_answer = request.POST['security_answer']
        error_message = None

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            error_message = 'Username already exists. Please choose another one.'

        # Check if the passwords match
        elif password != confirm_password:
            error_message = 'Passwords do not match.'

        elif not security_question or not security_answer:
            error_message = 'Please provide a security question and answer.'

        if error_message:
            return render(request, 'register.html', {'error_message': error_message})

        try:
            # Create the user
            user = User.objects.create_user(username=username, password=password)
            user.save()

            # Create or get the user's profile with security question and answer
            profile, created = Profile.objects.get_or_create(user=user)
            profile.security_question = security_question
            profile.security_answer = security_answer
            profile.save(update_fields=['security_question', 'security_answer'])  # Save the profile
            request.session['just_registered'] = True
            return redirect('login_user', username=username)

        except IntegrityError as e:
            error_message = 'An error occurred during registration. Please try again.'
            return render(request, 'register.html', {'error_message': error_message})
        except Exception as e:
            print(f"Error creating user: {e}")
            error_message = 'An error occurred during registration. Please try again.'
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')


def login_user(request, username):
    """
            Logs the user in and redirects them to the geolocator page.

            This view is triggered after the user has successfully registered. It logs in the user
            using Django's `login` method and redirects them to the 'geolocator' page.

            Parameters:
                request (HttpRequest): The HTTP request object that triggers this view.
                username (str): The username of the user being logged in.

            Returns:
                HttpResponseRedirect: Redirects the user to the 'geolocator' page after successful login.
    """
    user = User.objects.get(username=username)
    login(request, user)  # Log the user in
    return redirect(reverse('geolocator'))


def request_username_view(request):
    context = {
        'language_name': _('English')
    }
    """
            Handles the form where the user enters their username to initiate a password reset.

            This view checks if the username provided by the user exists in the system. If the username
            exists, it stores the username in the session and redirects the user to the reset password page.
            If the username does not exist, it returns an error message.

            Parameters:
                request (HttpRequest): The HTTP request object that triggers this view.

            Returns:
                HttpResponse:
                    - Renders the username request page with an error message if the username is not found.
                    - Redirects to the reset password page if the username exists.
    """
    # Check if the user has just registered
    if request.session.get('just_registered'):
        # Log out the user
        logout(request)
        # Remove the flag after logging out
        request.session.pop('just_registered', None)
        return redirect('login')  # Redirect them to the login page or other safe page

    error_message = None
    if request.method == 'POST':
        username = request.POST['username']
        # Check if the user exists

        if User.objects.filter(username=username).exists():
            request.session['reset_username'] = username  # Store the username in session
            return redirect('reset_password')  # Redirect to the security question form
        else:
            error_message = 'Username does not exist.'
        return render(request, 'request_username.html', {'error_message': error_message})
    return render(request, 'request_username.html')


def reset_password_view(request):
    context = {
        'language_name': _('English')
    }
    """
           Handles the password reset process by verifying the user's security question answer.

           This view checks the user's answer to their security question. If the answer is correct,
           it allows the user to set a new password. If the new passwords match, the user's password
           is updated and they are notified of the successful reset. If any validation fails, an error
           message is returned.

           Parameters:
               request (HttpRequest): The HTTP request object that triggers this view.

           Returns:
               HttpResponse:
                   - Renders the password reset page with a success message if the reset is successful.
                   - Renders the page with error messages if the answer or password confirmation fails.
    """
    # Check if the user has just registered
    if request.session.get('just_registered'):
        # Log out the user
        logout(request)
        # Remove the flag after logging out
        request.session.pop('just_registered', None)
        return redirect('login')  # Redirect them to the login page or other safe page

    error_message = None
    success_message = None
    username = request.session.get('reset_username', None)

    if not username:
        return redirect('request_username')

    user = User.objects.get(username=username)

    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return HttpResponse('No profile found for this user. Please try again.')

    if request.method == 'POST':
        answer = request.POST['security_answer']
        if answer == profile.security_answer:
            # Correct answer, allow password reset
            new_password = request.POST['new_password']
            confirm_password = request.POST['confirm_password']

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                success_message = 'Password reset successful! Redirecting to login page...'
                return render(request, 'reset_password_question.html', {
                    'security_question': profile.security_question,
                    'success_message': success_message
                })
            else:
                error_message = 'Passwords do not match.'
        else:
            error_message = 'Security answer is incorrect.'
        return render(request, 'reset_password_question.html', {
            'security_question': profile.security_question,
            'error_message': error_message
        })

    return render(request, 'reset_password_question.html', {'security_question': profile.security_question})