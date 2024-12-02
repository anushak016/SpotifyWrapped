from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.conf import settings  # Add this import
from .models import Profile
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json


def home_view(request):
    # Check if the user has just registered
    if request.session.get('just_registered'):
        # Log out the user
        logout(request)
        # Remove the flag after logging out
        request.session.pop('just_registered', None)
        return redirect('login')  # Redirect them to the login page or other safe page
    return render(request, 'home.html')

def home(request):
    # Get theme from session or default
    theme = request.session.get('theme', 'default')
    return render(request, "home.html", {'theme': theme})

def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST['username']
        password = request.POST['password']
        
        # Check if the input is an email
        if '@' in username_or_email:
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                username = None
        else:
            username = username_or_email
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to Spotify auth after successful login
            scope = 'user-top-read'
            auth_url = (
                "https://accounts.spotify.com/authorize"
                "?response_type=code"
                f"&client_id={settings.SPOTIFY_CLIENT_ID}"
                f"&redirect_uri={settings.SPOTIFY_REDIRECT_URI}"
                f"&scope={scope}"
            )
            return redirect(auth_url)
        else:
            error_message = "Incorrect username or password."
            return render(request, 'login.html', {'error_message': error_message})    
    return render(request, 'login.html')

def logout_view(request):
    # Clear Spotify token when logging out
    if 'spotify_token' in request.session:
        del request.session['spotify_token']
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        security_question = request.POST['security_question']
        security_answer = request.POST['security_answer']
        error_message = None

        # Validation checks...
        if error_message:
            return render(request, 'register.html', {'error_message': error_message})

        try:
            from django.db import transaction
            with transaction.atomic():
                user = User.objects.create_user(username=username, password=password)
                profile = Profile.objects.create(
                    user=user,
                    email=email,
                    security_question=security_question,
                    security_answer=security_answer
                )
                login(request, user)
                
                # Redirect to Spotify auth after registration
                scope = 'user-top-read'
                auth_url = (
                    "https://accounts.spotify.com/authorize"
                    "?response_type=code"
                    f"&client_id={settings.SPOTIFY_CLIENT_ID}"
                    f"&redirect_uri={settings.SPOTIFY_REDIRECT_URI}"
                    f"&scope={scope}"
                )
                return redirect(auth_url)
        except Exception as e:
            if User.objects.filter(username=username).exists():
                User.objects.get(username=username).delete()
            error_message = f'An error occurred during registration: {str(e)}'
            return render(request, 'register.html', {'error_message': error_message})

    return render(request, 'register.html')

def login_user(request, username):
    user = User.objects.get(username=username)
    login(request, user)  # Log the user in
    return redirect('home')  # Change this to redirect to home page

def request_username_view(request):
    # Check if the user has just registered
    if request.session.get('just_registered'):
        # Log out the user
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
    # Check if the user has just registered
    if request.session.get('just_registered'):
        # Log out the user
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

@login_required(login_url='/auth/login/')
def saved_wraps(request):
    # Get the user's saved wraps from the database
    saved_wraps = request.user.profile.saved_wraps.all().order_by('-created_at')
    return render(request, 'saved_wraps.html', {'saved_wraps': saved_wraps})

@require_http_methods(["POST"])
@login_required(login_url='/auth/login/')
def delete_account(request):
    data = json.loads(request.body)
    password = data.get('password')
    
    # Verify password
    user = authenticate(username=request.user.username, password=password)
    if user is not None:
        # Delete the user's account
        user.delete()
        logout(request)
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})