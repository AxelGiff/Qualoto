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


def home_view(request):
    """
    Vue pour la page d'accueil.

    Si l'utilisateur est connecté, la vue affiche son nom d'utilisateur et son ID.
    Sinon, la vue n'affiche rien.
    """
    username = request.session.get('username')
    user_id = request.session.get('user_id')

    context = {'username': username, 'user_id': user_id} if username and user_id else {}
    return render(request, 'home.html', context)    
