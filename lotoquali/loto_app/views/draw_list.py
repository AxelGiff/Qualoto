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

def draw_list(request):
    if request.user.username:
        # Récupérer uniquement les tirages auxquels l'utilisateur connecté a participé
        tickets = Tickets.objects.filter(user=request.user)  # Filtrer les tickets de l'utilisateur
        draw_ids = tickets.values_list('draw_id', flat=True)  # Obtenir les ID des tirages
        draws = Draws.objects.filter(draw_id__in=draw_ids).order_by('draw_date')  # Récupérer les tirages correspondants
        wins = Winners.objects.filter(user=request.user)
        draw_id_win=wins.values_list('draw_id', flat=True)
        draw_win=Draws.objects.filter(draw_id__in=draw_id_win)

    else:
        # Si l'utilisateur n'est pas connecté, afficher tous les tirages
        draws = Draws.objects.all().order_by('draw_date')
    
    numbers = list(range(1, 50))  # Génère des numéros entre 1 et 49
    bonus = list(range(1, 11))  # Génère des numéros bonus entre 1 et 10
    # Compter le nombre de joueurs pour chaque tirage
    for draw in draws:
        draw.player_count = Tickets.objects.filter(draw=draw).count()

    # Si la méthode GET, on affiche la page
    return render(request, 'draw_list.html', {
        'draws': draws,
        'numbers': numbers,
        'bonus': bonus,
        #'user_wins': draw_win,
        'csrf_token': request.COOKIES['csrftoken'] 
    })