from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout,get_user_model
from ..models import *
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.contrib import messages
import json  
from django.views.decorators.http import require_POST
from ..forms import RegisterForm 
from django.contrib.auth.decorators import login_required
import random
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser  

def register_view(request):
    """
    Vue pour la création d'un utilisateur.
    
    Si la méthode est GET, la vue affiche le formulaire de création d'un utilisateur.
    Si la méthode est POST, la vue essaie de créer l'utilisateur en utilisant le formulaire.
    Si le formulaire est valide, l'utilisateur est créé et connecté, puis redirigé vers la page d'accueil.
    Si le formulaire contient des erreurs, la vue renvoie les erreurs sous forme de JSON avec un statut 400.
    Si le nom d'utilisateur existe déjà, la vue renvoie une erreur avec un statut 400.
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        # Vérifier si le nom d'utilisateur existe déjà avant de valider le formulaire
        username = request.POST.get('username')
        if Users.objects.filter(username=username).exists():
            # Renvoyer une réponse JSON avec une erreur et le code 400
            messages.error(request, 'Cet utilisateur existe déjà.')
            return JsonResponse({'error': 'Cet utilisateur existe déjà'}, status=400)
        
        if form.is_valid():
            # Si le nom d'utilisateur est disponible, créer l'utilisateur
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            # Renvoyer les erreurs du formulaire sous forme de JSON avec un statut 400
            return JsonResponse({'error': form.errors}, status=400)
    else:
        form = RegisterForm()
    
    return render(request, 'register.html', {'form': form})


def login_view(request):
    """
    This view handles user login functionality.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Redirects to 'home' if login is successful, otherwise renders 'login.html' with an error message.

    Raises:
        N/A
    """

    if request.method == 'POST':
        username = request.POST['username']
        user = authenticate(request, username=username)
        if user is not None:
            login(request, user)
            request.session['username'] = user.username
            request.session['user_id'] = user.id
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Identifiants invalides'},status=200)
    return render(request, 'login.html')

def logout_view(request):
    
    logout(request)
    return redirect('home')