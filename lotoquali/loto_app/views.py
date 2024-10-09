from django.shortcuts import render
from . models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import get_user_model

import json  
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from .forms import TicketsForm,RegisterForm
from django.shortcuts import render, get_object_or_404
import random
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser  

""" # Create your views here.
def UsersList(request):
    utilisateurs = Users.objects.all()
    data = [{'id_user': utilisateur.id_user, 'nom': utilisateur.nom,'prenom': utilisateur.prenom,'role': utilisateur.role,'email':utilisateur.email} for utilisateur in utilisateurs]
    serializer=UtilisateursSerializer(utilisateurs,many=True)
    return JsonResponse(serializer.data, safe=False)

def Dashboard(request):
    utilisateur_connecte = request.user

    # Assurez-vous que l'utilisateur connecté est une instance de votre modèle `Utilisateurs`
    try:
        utilisateur = Utilisateurs.objects.get(prenom=utilisateur_connecte.prenom)
        prenom_utilisateur_connecte = utilisateur.prenom
    except Utilisateurs.DoesNotExist:
        prenom_utilisateur_connecte = ''

    dashboard_data = {
        'prenom': prenom_utilisateur_connecte,
        # Ajoutez d'autres données du tableau de bord ici si nécessaire
    }
    return JsonResponse(dashboard_data)



@login_required
def ma_vue_protegee(request):
    # Cette vue nécessite une authentification
    return HttpResponse("Bienvenue sur la page protégée !")




@csrf_exempt
def connexion_utilisateur(request):
    data = json.loads(request.body)
    usermane = data.get('username')

    # Authenticate user with email and password
    try:
        utilisateur = Utilisateurs.objects.get(usermane=username)
        login(request, utilisateur)
        return JsonResponse({'username': utilisateur.username})

    except Utilisateurs.DoesNotExist:
        return JsonResponse({'erreur': 'Utilisateur non trouvé'}, status=400)


 """
def draw_view(request):
    draws = Draws.objects.all().order_by('draw_date')[:3]  # Exemple pour afficher 3 tirages

    return render(request, 'draw.html', {'draws': draws})


def participate_draw(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        players = data.get('players', [])
        number_of_random = data.get('number_of_random')
        print(number_of_random)
        main_numbers = random.sample(range(1, 50), 5)  # 5 numéros entre 1 et 49
        bonus_numbers = random.sample(range(1, 11), 2)  # 2 numéros bonus entre 1 et 10

        # Créer un nouveau tirage
        new_draw = Draws.objects.create(
            draw_date=timezone.now(),
            winning_main_numbers=",".join(map(str, main_numbers)),
            winning_bonus_numbers=",".join(map(str, bonus_numbers)),
            isFinished=False
        )

        if number_of_random:
            for _ in range(int(number_of_random)):
                random_username = f"Joueur{random.randint(1000, 9999)}"
                random_user, created = Users.objects.get_or_create(username=random_username)
                
                random_main_numbers = random.sample(range(1, 50), 5)  # 5 numéros entre 1 et 49
                random_bonus_numbers = random.sample(range(1, 11), 2)  # 2 numéros bonus entre 1 et 10
                
                # Créer un ticket pour ce joueur aléatoire
                Tickets.objects.create(
                    draw=new_draw,
                    main_numbers=",".join(map(str, random_main_numbers)),
                    bonus_numbers=",".join(map(str, random_bonus_numbers)),
                    user=random_user
                )

        # Traiter les joueurs soumis par l'utilisateur
        for player in players:
            name = player.get('name')
            numbers = player.get('numbers')
            bonus = player.get('bonus')

            if not name or not numbers or not bonus:
                return JsonResponse({'error': f'Informations manquantes pour le joueur: {name}'}, status=400)

            user, created = Users.objects.get_or_create(username=name)

            # Créer un ticket pour le joueur lié au nouveau tirage
            Tickets.objects.create(
                draw=new_draw,
                main_numbers=",".join(map(str, numbers)),
                bonus_numbers=",".join(map(str, bonus)),
                user=user
            )
        draw_id = new_draw.draw_id
        redirect_url = reverse('start_draw', kwargs={'draw': draw_id})
        
        return JsonResponse({'message': 'Participation soumise avec succès !', 'draw_id': draw_id, 'redirect_url': redirect_url})
    
    # Si méthode GET, afficher la page
    draws = Draws.objects.all().order_by('draw_date')[:3]
    numbers = list(range(1, 50))
    bonus = list(range(1, 11))
    
    return render(request, 'participate_draw.html', {
        'draws': draws,
        'numbers': numbers,
        'bonus': bonus,
        'csrf_token': request.COOKIES['csrftoken']
    })
    
def simulate_draw(request):
    if request.method == 'POST':
        winning_main_numbers = request.POST.get('winning_main_numbers')
        winning_bonus_numbers = request.POST.get('winning_bonus_numbers')
        
        # Traitement des numéros gagnants et bonus (vérification, stockage, etc.)
        winning_numbers_list = [int(n) for n in winning_main_numbers.split(',')]
        bonus_numbers_list = [int(n) for n in winning_bonus_numbers.split(',')]
        
        draw = Draws.objects.create(
            winning_main_numbers=winning_numbers_list,
            winning_bonus_numbers=bonus_numbers_list
        )
        draw.save()
        
        return redirect('home')
    
    return render(request, 'simulate_draw.html')

def create_draw(request):
    draws = Draws.objects.all().order_by('draw_date')[:10] 
    numbers = list(range(1, 50))  # Génère des numéros entre 1 et 49
    bonus = list(range(1, 11))  # Génère des numéros bonus entre 1 et 10
    
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_numbers = [num for num in data.get('selected_numbers') if num < 50]
        selected_bonus = selected_numbers[5:]
        draw_id = 1
        print(selected_numbers[5:])
        
        if not selected_numbers or not selected_bonus or not draw_id:
            return JsonResponse({'message': 'Des informations manquent.'}, status=400)
        
        # Convertir les listes de numéros en chaînes séparées par des virgules
        selected_numbers_str = ",".join(map(str, selected_numbers))
        selected_bonus_str = ",".join(map(str, selected_bonus))
        
        # Récupérer le tirage correspondant
        draw = get_object_or_404(Draws, draw_id=draw_id)
        
        # Créer et enregistrer le ticket
        ticket = Tickets.objects.create(
            draw=draw,
            main_numbers=selected_numbers_str,  
            bonus_numbers=selected_bonus_str,  
            user="Users object (57)"  
        )
        return JsonResponse({'message': 'Ticket soumis avec succès !'})
    
    # Si la méthode GET, on affiche la page
    return render(request, 'create_draw.html', {
        'draws': draws,
        'numbers': numbers,
        'bonus': bonus,
        'csrf_token': request.COOKIES['csrftoken'] 
    })

from django.shortcuts import render, redirect
from django.contrib import messages

def home_view(request):
    username = request.session.get('username')
    user_id = request.session.get('user_id')

    context = {'username': username, 'user_id': user_id} if username and user_id else {}
    return render(request, 'home.html', context)

User = get_user_model()


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  
        else:
            print(form.errors)
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        user = authenticate(request, username=username)
        if user is not None:
            login(request, user)
            request.session['username'] = user.username
            request.session['user_id'] = user.id
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Identifiants invalides'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')


def start_draw(request, draw):
    # Utilisation de get_object_or_404 pour une meilleure gestion des erreurs
    draw_instance = get_object_or_404(Draws, draw_id=draw)
    
    # Convertit les chaînes de nombres gagnants en listes
    winning_numbers_list = draw_instance.winning_main_numbers.split(',')
    winning_bonus_list = draw_instance.winning_bonus_numbers.split(',')
    
    tickets = Tickets.objects.filter(draw=draw_instance).select_related('user')
    
    # Prépare les données des joueurs
    players = []
    for ticket in tickets:
        player_data = {
            'username': ticket.user.username,
            'main_numbers': ticket.main_numbers.split(','),
            'bonus_numbers': ticket.bonus_numbers.split(',')
        }
        players.append(player_data)
    
    context = {
        'draw': draw_instance,
        'winning_numbers': winning_numbers_list,
        'bonus_numbers': winning_bonus_list,
        'players': players,
        'total_players': len(players)
    }
    redirect_url = reverse('draw_win', kwargs={'draw': draw_instance.draw_id})

    if request.method == 'POST':
        return JsonResponse({'message': 'Participation soumise avec succès !', 'draw_id': draw_instance.draw_id, 'redirect_url': redirect_url})
    return render(request, 'start_draw.html', context)


def draw_win(request, draw):
    # Utilisation de get_object_or_404 pour une meilleure gestion des erreurs
    draw_instance = get_object_or_404(Draws, draw_id=draw)
    
    # Convertir les chaînes de nombres gagnants en listes
    winning_numbers_list = draw_instance.winning_main_numbers.split(',')
    winning_bonus_list = draw_instance.winning_bonus_numbers.split(',')
    
    # Convertir les listes de nombres gagnants en ensembles pour une comparaison facile
    winning_numbers_set = set(winning_numbers_list)
    winning_bonus_set = set(winning_bonus_list)
    
    # Récupérer tous les tickets associés à ce tirage
    tickets = Tickets.objects.filter(draw=draw_instance).select_related('user')
    
    # Préparer les données des joueurs
    players = []
    for ticket in tickets:
        player_main_numbers = ticket.main_numbers.split(',')
        player_bonus_numbers = ticket.bonus_numbers.split(',')
        
        # Vérifier si le joueur a tous les numéros gagnants (même sans ordre)
        player_main_set = set(player_main_numbers)
        player_bonus_set = set(player_bonus_numbers)
        
        correct_main_numbers = len(player_main_set & winning_numbers_set)
        correct_bonus_numbers = len(player_bonus_set & winning_bonus_set)
        
        has_won = correct_main_numbers == len(winning_numbers_set) and correct_bonus_numbers == len(winning_bonus_set)
        
        player_data = {
            'username': ticket.user.username,
            'main_numbers': player_main_numbers,
            'bonus_numbers': player_bonus_numbers,
            'correct_main_numbers': correct_main_numbers,
            'correct_bonus_numbers': correct_bonus_numbers,
            'has_won': has_won  
        }
        
        players.append(player_data)

        draw_instance.isFinished = True
        draw_instance.save()  
    
    context = {
        'draw': draw_instance,
        'winning_numbers': winning_numbers_list,
        'bonus_numbers': winning_bonus_list,
        'players': players,
        'total_players': len(players)
    }
    
    return render(request, 'draw_win.html', context)
