from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from .models import Profile
from django.db import IntegrityError
from django.urls import reverse


def home_view(request):
    # Check if the user has just registered
    if request.session.get('just_registered'):
        # Log out the user
        logout(request)
        # Remove the flag after logging out
        request.session.pop('just_registered', None)
        return redirect('login')  # Redirect them to the login page or other safe page
    return render(request, 'home.html')

def login_view(request):
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
    logout(request)
    return redirect('/auth/login/')

def register_view(request):
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
    user = User.objects.get(username=username)
    login(request, user)  # Log the user in
    return redirect(reverse('geolocator'))

def request_username_view(request):
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