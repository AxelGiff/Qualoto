from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout,get_user_model
from . models import *
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.contrib import messages
import json  
from django.views.decorators.http import require_POST
from .forms import RegisterForm 
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

def get_players(request):
    # Récupérer tous les utilisateurs
    players = Users.objects.all().values('user_id', 'username')
    
    # Renvoie une réponse JSON contenant les joueurs
    return JsonResponse(list(players), safe=False)



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
        wins = Winners.objects.filter(user=request.user)
        draw_id_win=wins.values_list('draw_id', flat=True)
        draw_win=Draws.objects.filter(draw_id__in=draw_id_win)

    else:
        # Si l'utilisateur n'est pas connecté, afficher tous les tirages
        draws = Draws.objects.all().order_by('draw_date')[:50]
    
    numbers = list(range(1, 50))  # Génère des numéros entre 1 et 49
    bonus = list(range(1, 11))  # Génère des numéros bonus entre 1 et 10
    # Compter le nombre de joueurs pour chaque tirage
    for draw in draws:
        draw.player_count = Tickets.objects.filter(draw=draw).count()

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
        #'user_wins': draw_win,
        'csrf_token': request.COOKIES['csrftoken'] 
    })


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

User = get_user_model()



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
