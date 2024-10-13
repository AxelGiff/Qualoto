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

from django.shortcuts import render, redirect
from django.contrib import messages
""" # Create your views here.
def UsersList(request):
    utilisateurs = Users.objects.all()
    data = [{'id_user': utilisateur.id_user, 'nom': utilisateur.nom,'prenom': utilisateur.prenom,'role': utilisateur.role,'email':utilisateur.email} for utilisateur in utilisateurs]
    serializer=UtilisateursSerializer(utilisateurs,many=True)
    return JsonResponse(serializer.data, safe=False)
"""
def draw_view(request):
    draws = Draws.objects.all().order_by('draw_date')[:3]  # Exemple pour afficher 3 tirages

    return render(request, 'draw.html', {'draws': draws})

def get_players(request):
    players = Users.objects.all()
    players_data = [{"id": player.user_id, "username": player.username} for player in players]
    return JsonResponse(players_data, safe=False)

def participate_draw(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        players = data.get('players', [])
        number_of_random = data.get('number_of_random')
        participation = data.get('participation')  
        main_numbers = random.sample(range(1, 50), 5)  # 5 numéros entre 1 et 49
        bonus_numbers = random.sample(range(1, 10), 2)  # 2 numéros bonus entre 1 et 9
        
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
                random_bonus_numbers = random.sample(range(1, 10), 2)  # 2 numéros bonus entre 1 et 9
                
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
            if len(numbers) > 5:
                return JsonResponse({'error': 'Trop de numéros principaux. Un maximum de 5 numéros est autorisé.'}, status=400)
            if len(bonus) > 2:
                return JsonResponse({'error': 'Trop de numéros bonus. Un maximum de 2 numéros est autorisé.'}, status=400)
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
    bonus = list(range(1, 10))
    
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

def draw_list(request):
    if request.user.username:
        # Récupérer uniquement les tirages auxquels l'utilisateur connecté a participé
        tickets = Tickets.objects.filter(user=request.user)  # Filtrer les tickets de l'utilisateur
        draw_ids = tickets.values_list('draw_id', flat=True)  # Obtenir les ID des tirages
        draws = Draws.objects.filter(draw_id__in=draw_ids).order_by('draw_date')  # Récupérer les tirages correspondants
    else:
        # Si l'utilisateur n'est pas connecté, afficher tous les tirages
        draws = Draws.objects.all().order_by('draw_date')[:50]
    
    numbers = list(range(1, 50))  # Génère des numéros entre 1 et 49
    bonus = list(range(1, 11))  # Génère des numéros bonus entre 1 et 10
    
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_numbers = [num for num in data.get('selected_numbers') if num < 50]
        
        if len(selected_numbers) < 7:  # S'assurer qu'il y a au moins 5 numéros principaux et 2 bonus
            return JsonResponse({'message': 'Des informations manquent.'}, status=400)
        
        selected_bonus = selected_numbers[5:7]  # Les 2 derniers sont les bonus
        selected_numbers = selected_numbers[:5]  # Les 5 premiers sont les principaux
        draw_id = 1  # Remplacer par l'ID de tirage approprié
        
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
            user=request.user  # Utiliser l'utilisateur connecté
        )
        return JsonResponse({'message': 'Ticket soumis avec succès !'})
    
    # Si la méthode GET, on affiche la page
    return render(request, 'draw_list.html', {
        'draws': draws,
        'numbers': numbers,
        'bonus': bonus,
        'csrf_token': request.COOKIES['csrftoken'] 
    })


def home_view(request):
    username = request.session.get('username')
    user_id = request.session.get('user_id')

    context = {'username': username, 'user_id': user_id} if username and user_id else {}
    return render(request, 'home.html', context)

User = get_user_model()



from django.http import JsonResponse
from django.contrib.auth import login
from .forms import RegisterForm  # Assurez-vous que votre chemin est correct

def register_view(request):
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


def start_draw(request, draw):
    # Utilisation de get_object_or_404 pour la gestion des erreurs
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
    draw_instance = get_object_or_404(Draws, draw_id=draw)
    
    # Convertir les chaînes de nombres gagnants en listes
    winning_numbers_list = list(map(int, draw_instance.winning_main_numbers.split(',')))
    winning_bonus_list = list(map(int, draw_instance.winning_bonus_numbers.split(',')))
    
    # Récupérer tous les tickets associés à ce tirage
    tickets = Tickets.objects.filter(draw=draw_instance).select_related('user')
    
    players = []
    
    for ticket in tickets:
        player_main_numbers = list(map(int, ticket.main_numbers.split(',')))
        player_bonus_numbers = list(map(int, ticket.bonus_numbers.split(',')))
        
        # Correspondance des numéros gagnants
        correct_main_numbers = len(set(player_main_numbers) & set(winning_numbers_list))
        correct_bonus_numbers = len(set(player_bonus_numbers) & set(winning_bonus_list))
        
        # Calcul de la proximité par la somme
        sum_difference = evaluate_closest_sum(winning_numbers_list, player_main_numbers)
        
        # Stocker les numéros principaux et bonus correspondants sous forme de chaînes de caractères
        matched_main_numbers_str = ','.join(map(str, set(player_main_numbers) & set(winning_numbers_list)))
        matched_bonus_numbers_str = ','.join(map(str, set(player_bonus_numbers) & set(winning_bonus_list)))
        
        has_won = correct_main_numbers > 0 or correct_bonus_numbers > 0  
        
       

       
        
        player_data = {
            'user_id':ticket.user.user_id, ## On récupère l'id de l'utilisateur via l'instance du ticket
            'username': ticket.user.username,
            'main_numbers': player_main_numbers,
            'bonus_numbers': player_bonus_numbers,
            'correct_main_numbers': correct_main_numbers,
            'correct_bonus_numbers': correct_bonus_numbers,
            'sum_difference': sum_difference,
            'has_won': has_won,
        }
        
        players.append(player_data)
    
    # Trier les joueurs selon la correspondance et la proximité
    players_sorted = sorted(players, key=lambda p: (p['correct_main_numbers'], p['correct_bonus_numbers'], -p['sum_difference']), reverse=True)
    

    # Assigner les gains
    max_winners = 10
    prizes = checkingPrize(min(len(players_sorted), max_winners))

    for idx, player in enumerate(players_sorted):
        if idx < max_winners:
            player['rank'] = idx + 1
            player['prize'] = prizes[idx]  
        else:
            player['rank'] = '-'  
         # Créer un résultat pour chaque joueur et l'enregistrer dans la table Results
        Results.objects.create(
            ticket_id=ticket.ticket_id,
            matched_main_numbers=matched_main_numbers_str,  # Stocker en tant que chaîne de caractères
            matched_bonus_numbers=matched_bonus_numbers_str,  # Stocker en tant que chaîne de caractères
        )
         # Enregistrer les gagnants dans la table Winner si le joueur a remporté un gain
        if player['rank'] != '-':  # Si le joueur est dans les premiers (gagnants)
            Winners.objects.create(
                user_id=player['user_id'],  # ID de l'utilisateur
                draw_id=draw_instance.draw_id,  # ID du tirage
                prize=player['prize'],         # Gain du joueur
                ranking=player['rank']         # Rang du joueur
            )
    

    
    draw_instance.isFinished = True
    draw_instance.save()

    context = {
        'draw': draw_instance,
        'winning_numbers': winning_numbers_list,
        'bonus_numbers': winning_bonus_list,
        'players': players_sorted,
        'total_players': len(players_sorted),
    }
    
    return render(request, 'draw_win.html', context)



def checkingPrize(nbPlayers):
    prize_distribution = [
        0.40,  # 40% pour le 1er
        0.20,  # 20% pour le 2ème
        0.12,  # 12% pour le 3ème
        0.07,  # 7% pour le 4ème
        0.06,  # 6% pour le 5ème
        0.05,  # 5% pour le 6ème
        0.04,  # 4% pour le 7ème
        0.03,  # 3% pour le 8ème
        0.02,  # 2% pour le 9ème
        0.01   # 1% pour le 10ème
    ]
    
    # Ajustement des gains si moins de 10 joueurs
    if nbPlayers < 10:
        total_percentage = sum(prize_distribution[:nbPlayers])
        adjusted_prizes = [(prize / total_percentage) * 3_000_000 for prize in prize_distribution[:nbPlayers]]
    else:
        adjusted_prizes = [prize * 3_000_000 for prize in prize_distribution]
    
    return adjusted_prizes
def evaluate_closest_sum(winning_numbers, player_numbers):
    winning_sum = sum(map(int, winning_numbers))
    player_sum = sum(map(int, player_numbers))
    return abs(winning_sum - player_sum)

