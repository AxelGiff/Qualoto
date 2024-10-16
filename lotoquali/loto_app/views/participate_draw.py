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


def draw_view(request):
    """
    Renders a view displaying the latest draw events.

    Fetches the latest three draw events from the database, ordered by draw date, 
    and renders them in the 'draw.html' template.

    Args:
        request: The HTTP request object.

    Returns:
    HttpResponse: The rendered HTML page with the draws data.
    """
    draws = Draws.objects.all().order_by('draw_date')[:3]  # Exemple pour afficher 3 tirages

    return render(request, 'draw.html', {'draws': draws})


def start_draw(request, draw):
    # Utilisation de get_object_or_404 pour la gestion des erreurs
    """
    Page de démarrage d'un tirage

    Affiche les numéros gagnants et la liste des joueurs qui ont participé
    à ce tirage.

    Si la méthode est POST, redirige vers la page des résultats du tirage
    """
    
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


# Génère les numéros de tirage aléatoires
def generate_random_numbers(main_range, bonus_range, main_count, bonus_count):
    """
    Génère les numéros de tirage aléatoires.

    :param int main_range: La plage de numéros pour les numéros principaux
    :param int bonus_range: La plage de numéros pour les numéros bonus
    :param int main_count: Le nombre de numéros principaux à générer
    :param int bonus_count: Le nombre de numéros bonus à générer
    :return: Un tuple contenant les numéros principaux et les numéros bonus
    """
    main_numbers = random.sample(range(1, main_range + 1), main_count)  # Numéros principaux
    bonus_numbers = random.sample(range(1, bonus_range + 1), bonus_count)  # Numéros bonus
    return main_numbers, bonus_numbers

# Crée un ticket pour un utilisateur
def create_ticket(draw, user, main_numbers, bonus_numbers):
    """
    Crée un ticket pour l'utilisateur lié au tirage passé en paramètre
    avec les numéros principaux et bonus passés en paramètre.
    :param draw: Le tirage lié au ticket
    :param user: L'utilisateur lié au ticket
    :param main_numbers: Les numéros principaux
    :param bonus_numbers: Les numéros bonus
    :return: Le ticket créé
    """
    Tickets.objects.create(
        draw=draw,
        main_numbers=",".join(map(str, main_numbers)),
        bonus_numbers=",".join(map(str, bonus_numbers)),
        user=user
    )

# Gère la création des utilisateurs aléatoires
def create_random_users(number_of_random, draw):
    """
    Crée des utilisateurs aléatoires avec des numéros aléatoires pour le tirage
    spécifié.

    :param number_of_random: Le nombre d'utilisateurs aléatoires à créer
    :param draw: Le tirage pour lequel créer des billets
    """
    for _ in range(int(number_of_random)):
        random_username = f"Joueur{random.randint(1000, 9999)}"
        random_user, created = Users.objects.get_or_create(username=random_username)
        main_numbers, bonus_numbers = generate_random_numbers(49, 9, 5, 2)
        create_ticket(draw, random_user, main_numbers, bonus_numbers)

def process_player_participation(players, draw):
    """
    Traite les participations des joueurs envoyées via l'interface.
    
    Args:
        players (list): Liste des joueurs avec leurs numéros principaux et bonus.
        draw (Draws): Instance de Draws correspondant au tirage.
    
    Returns:
        JsonResponse: Erreur en cas d'informations manquantes ou de mauvaise
            format, None sinon.
    """
    for player in players:
        name = player.get('name')
        numbers = player.get('numbers')
        bonus = player.get('bonus')

        if not name or not numbers or not bonus:
            return JsonResponse({'error': f'Informations manquantes pour le joueur: {name}'}, status=400)
        if len(numbers) > 5:
            return JsonResponse({'error': 'Trop de numéros principaux. Un maximum de 5 numéros est autorisé.'}, status=400)
        if len(bonus) > 2:
            return JsonResponse({'error': 'Trop de numéros bonus. Un maximum de 2 numéros est autorisé.'}, status=400)

        user, created = Users.objects.get_or_create(username=name)
        create_ticket(draw, user, numbers, bonus)

def participate_draw(request):
    """
    Vue pour gérer la participation des joueurs au tirage

    Si la requête est en POST, il s'agit d'une participation via l'interface
    - Génère les numéros de tirage pour un nouveau tirage
    - Crée un nouveau tirage
    - Crée des utilisateurs aléatoires si demandé
    - Gère la participation des joueurs envoyés via l'interface
    - Redirection vers la page de démarrage du tirage

    Si la requête est en GET, il s'agit d'une simple affichage de la page
    - Récupère les 3 derniers tirages
    - Envoie les numéros principaux et bonus à la page
    - Envoie le jeton CSRF
    - Envoie la liste des joueurs pour affichage
    """
    players = []  # Définir players_data par défaut comme une liste vide
    if request.method == 'POST':
        data = json.loads(request.body)
        players = data.get('players', [])
        number_of_random = data.get('number_of_random')

        # Génération des numéros de tirage pour un nouveau tirage
        main_numbers, bonus_numbers = generate_random_numbers(49, 9, 5, 2)

        # Créer un nouveau tirage
        new_draw = Draws.objects.create(
            draw_date=timezone.now(),
            winning_main_numbers=",".join(map(str, main_numbers)),
            winning_bonus_numbers=",".join(map(str, bonus_numbers)),
            isFinished=False
        )

        # Création des utilisateurs aléatoires si demandé
        if number_of_random:
            create_random_users(number_of_random, new_draw)

        # Gérer la participation des joueurs envoyés via l'interface
        participation_error = process_player_participation(players, new_draw)
        if participation_error:
            return participation_error

        players = Users.objects.all()  # Récupère tous les utilisateurs
        # Redirection vers la page de démarrage du tirage
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
        'csrf_token': request.COOKIES['csrftoken'],
        'players_data':players
    })