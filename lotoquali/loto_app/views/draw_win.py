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

def checkingPrize(nbPlayers):
    """
    Calcul les gains pour chaque joueur en fonction du nombre de joueurs.
    
    Si moins de 10 joueurs, on ajuste les gains pour que le total soit de 3 000 000 €.
    
    :param nbPlayers: Le nombre de joueurs.
    :return: Une liste de gains, par joueur, en €.
    """
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

    # S'assurer que le total est de 3 millions
    total_prize = sum(adjusted_prizes)
    
    if total_prize != 3_000_000:
        difference = 3_000_000 - total_prize
        # Ajuster la première prime pour compenser la différence
        adjusted_prizes[0] += difference
    
    return adjusted_prizes

def evaluate_closest_sum(winning_numbers, player_numbers):
    """
    Calcule la différence entre la somme des numéros gagnants et la somme des numéros du joueur.
    
    :param winning_numbers: Les numéros gagnants
    :param player_numbers: Les numéros choisis par le joueur
    :return: La différence entre la somme des numéros gagnants et la somme des numéros du joueur
    """
    winning_sum = sum(map(int, winning_numbers))
    player_sum = sum(map(int, player_numbers))
    return abs(winning_sum - player_sum)


# Vérifie combien de numéros correspondent entre les numéros du joueur et les numéros gagnants
def evaluate_correct_numbers(player_numbers, winning_numbers):
    """
    Vérifie combien de numéros correspondent entre les numéros du joueur et les numéros gagnants
    
    :param player_numbers: Les numéros choisis par le joueur
    :param winning_numbers: Les numéros gagnants
    :return: Le nombre de numéros en commun entre le joueur et les numéros gagnants
    """
    return len(set(player_numbers) & set(winning_numbers))

# Calcule la différence de somme entre les numéros du joueur et les numéros gagnants
def calculate_sum_difference(winning_numbers, player_numbers):
    """
    Calcule la différence entre la somme des numéros gagnants et la somme des numéros du joueur.

    :param winning_numbers: Les numéros gagnants
    :param player_numbers: Les numéros choisis par le joueur
    :return: La différence entre la somme des numéros gagnants et la somme des numéros du joueur
    """
    return evaluate_closest_sum(winning_numbers, player_numbers)

# Crée et sauvegarde les résultats d'un joueur dans la base de données
def create_result(ticket, matched_main_numbers, matched_bonus_numbers,prize):
    """
    Crée et sauvegarde les résultats d'un joueur dans la base de données
    
    :param ticket: L'instance du ticket associé au joueur
    :param matched_main_numbers: Les numéros principaux correspondants entre le joueur et les numéros gagnants
    :param matched_bonus_numbers: Les numéros bonus correspondants entre le joueur et les numéros gagnants
    :param prize: Le gain du joueur
    :return: None
    """
    Results.objects.create(
        ticket_id=ticket.ticket_id,
        matched_main_numbers=matched_main_numbers,  # Stocké en tant que chaîne de caractères
        matched_bonus_numbers=matched_bonus_numbers,  # Stocké en tant que chaîne de caractères
        prize=prize
    )

# Crée et sauvegarde un gagnant dans la base de données
def create_winner(player, draw_instance):
    """
    Crée et sauvegarde un gagnant dans la base de données
    
    :param player: Dictionnaire contenant les informations du joueur
    :param draw_instance: Instance de l'objet Draw correspondant au tirage
    :return: None
    """
    Winners.objects.create(
        user_id=player['user_id'],  # ID de l'utilisateur
        draw_id=draw_instance.draw_id,  # ID du tirage
        prize=player['prize'],         # Gain du joueur
        ranking=player['rank']         # Rang du joueur
    )

# Génère les données pour chaque joueur
def generate_player_data(ticket, winning_numbers_list, winning_bonus_list):
    """
    Génère les données pour chaque joueur
    
    :param ticket: L'instance du ticket associée au joueur
    :param winning_numbers_list: La liste des numéros principaux gagnants
    :param winning_bonus_list: La liste des numéros bonus gagnants
    :return: Un dictionnaire contenant les informations du joueur
    """
    player_main_numbers = list(map(int, ticket.main_numbers.split(',')))
    player_bonus_numbers = list(map(int, ticket.bonus_numbers.split(',')))

    correct_main_numbers = evaluate_correct_numbers(player_main_numbers, winning_numbers_list)
    correct_bonus_numbers = evaluate_correct_numbers(player_bonus_numbers, winning_bonus_list)
    sum_difference = calculate_sum_difference(winning_numbers_list, player_main_numbers)

    matched_main_numbers_str = ','.join(map(str, set(player_main_numbers) & set(winning_numbers_list)))
    matched_bonus_numbers_str = ','.join(map(str, set(player_bonus_numbers) & set(winning_bonus_list)))

    has_won = correct_main_numbers > 0 or correct_bonus_numbers > 0

    return {
        'user_id': ticket.user.user_id,
        'username': ticket.user.username,
        'main_numbers': player_main_numbers,
        'bonus_numbers': player_bonus_numbers,
        'correct_main_numbers': correct_main_numbers,
        'correct_bonus_numbers': correct_bonus_numbers,
        'sum_difference': sum_difference,
        'has_won': has_won,
        'matched_main_numbers_str': matched_main_numbers_str,
        'matched_bonus_numbers_str': matched_bonus_numbers_str,
    }
def draw_win(request, draw):
    """
    This function processes the draw results and calculates the winnings for the players.

    Parameters:
    - request: The HTTP request object
    - draw: The draw identifier

    Returns:
    - Rendered webpage displaying the draw results
    """
    draw_instance = get_object_or_404(Draws, draw_id=draw)

    # Convertir les chaînes de nombres gagnants en listes
    winning_numbers_list = list(map(int, draw_instance.winning_main_numbers.split(',')))
    winning_bonus_list = list(map(int, draw_instance.winning_bonus_numbers.split(',')))

    # Récupérer tous les tickets associés à ce tirage
    tickets = Tickets.objects.filter(draw=draw_instance).select_related('user')
    
    players = []
    for ticket in tickets:
        player_data = generate_player_data(ticket, winning_numbers_list, winning_bonus_list)
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
            create_winner(player, draw_instance)
        else:
            player['rank'] = '-'

        create_result(tickets[idx], player['matched_main_numbers_str'], player['matched_bonus_numbers_str'],player['prize'])
    # Mettre à jour l'état du tirage comme terminé
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



def get_players(request):
    # Récupérer tous les utilisateurs
    players = Users.objects.all().values('user_id', 'username')
    
    # Renvoie une réponse JSON contenant les joueurs
    return JsonResponse(list(players), safe=False)
