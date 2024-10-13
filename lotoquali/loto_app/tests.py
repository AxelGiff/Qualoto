from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from . models import *
import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from .views import evaluate_closest_sum, checkingPrize # Assurez-vous que le chemin est correct


class DrawViewsTest(TestCase):
    
    def setUp(self):
        # Créer des utilisateurs pour les tests
        self.user1 = Users.objects.create(username='player1')
        self.user2 = Users.objects.create(username='player2')
        ##self.user3 = Users.objects.create(username='player3')

        # Client pour envoyer des requêtes
        self.client = Client()
        
    def test_get_players(self):
        # Tester que la vue renvoie bien les joueurs sous forme de JSON
        response = self.client.get(reverse('get_players'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)  # Devrait retourner les 2 joueurs créés dans setUp
    

    def test_start_draw(self):
        # Créer un tirage pour le test
        draw = Draws.objects.create(draw_date=timezone.now(), winning_main_numbers="1,2,3,4,5", winning_bonus_numbers="1,2", isFinished=False)
        
        # Créer un ticket lié à ce tirage
        Tickets.objects.create(ticket_id=1,user=self.user1, draw=draw, main_numbers="1,2,3,4,5", bonus_numbers="1,2")
        
        # Tester que les données du tirage et des joueurs sont bien récupérées
        response = self.client.get(reverse('start_draw', kwargs={'draw': draw.draw_id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('winning_numbers', response.context)
        self.assertIn('players', response.context)
    
    def test_draw_win(self):
        # Créer un tirage avec des numéros gagnants
        draw = Draws.objects.create(draw_date=timezone.now(), winning_main_numbers="1,2,3,4,5", winning_bonus_numbers="1,2", isFinished=False)
        
        # Créer des tickets pour deux joueurs
        Tickets.objects.create(ticket_id=1,user=self.user1, draw=draw, main_numbers="1,2,3,4,5", bonus_numbers="1,2")
        Tickets.objects.create(ticket_id=2,user=self.user2, draw=draw, main_numbers="10,11,12,13,14", bonus_numbers="3,4")
        
        # Tester que la vue classe les joueurs et attribue des gains
        response = self.client.get(reverse('draw_win', kwargs={'draw': draw.draw_id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('players', response.context)
        self.assertEqual(len(response.context['players']), 2)
        self.assertEqual(response.context['players'][0]['username'], 'player1')  # Player1 devrait être le gagnant
    
    def test_prizes_distribution(self):
        # Tester la distribution des prix pour 2 joueurs
        draw = Draws.objects.create(draw_date=timezone.now(), winning_main_numbers="1,2,3,4,5", winning_bonus_numbers="1,2", isFinished=False)
        
        # Créer des tickets
        Tickets.objects.create(ticket_id=1,user=self.user1, draw=draw, main_numbers="1,2,3,4,5", bonus_numbers="1,2")
        Tickets.objects.create(ticket_id=2,user=self.user2, draw=draw, main_numbers="10,11,12,13,14", bonus_numbers="3,4")
        
        # Vérifier que la distribution des prix fonctionne bien
        response = self.client.get(reverse('draw_win', kwargs={'draw': draw.draw_id}))
        players = response.context['players']
        self.assertEqual(players[0]['prize'], 2000000)  # Vérifier le montant pour le 1er joueur
        self.assertEqual(players[1]['prize'], 1000000)   # Vérifier le montant pour le 2ème joueur


class AuthentificationUser(TestCase):
    def test_user_already_exists_on_login(self):
        # Créer un utilisateur déjà existant
        Users.objects.create(username='player1')
        
        # Essayer de créer un utilisateur avec le même pseudo
        data = {'username': 'player1'}
        response = self.client.post(reverse('register'), data=data)
        
        # Vérifier que la réponse renvoie une erreur 400
        self.assertEqual(response.status_code, 400)

        # Vérifier que le message d'erreur pour duplication de pseudo est présent dans la réponse JSON
        self.assertIn('Cet utilisateur existe déjà', response.json().get('error'))

class ParticipateDrawTests(TestCase):
    
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = Users.objects.create(username='player1')
                # Créer un ticket pour cet utilisateur
        # Créer un tirage pour ce test
        self.draw = Draws.objects.create(
            draw_date=timezone.now(),
            winning_main_numbers="1,2,3,4,5",
            winning_bonus_numbers="1,2",
            isFinished=False
        )

    
    def test_participate_draw_success(self):
        # Tester que la participation à un tirage fonctionne bien
        data = {
            'players': [{'name': 'player1', 'numbers': [1, 2, 3, 4, 5], 'bonus': [1, 2]}],
            'number_of_random': 1
        }
  # Créer un ticket associé à l'utilisateur et au tirage
        Tickets.objects.create(
            ticket_id=1, 
            user=self.user,
            draw=self.draw,  # Associer le ticket à ce tirage
            main_numbers=",".join(map(str, data['players'][0]['numbers'])),
            bonus_numbers=",".join(map(str, data['players'][0]['bonus']))
        )
        response = self.client.post(reverse('start_draw', kwargs={'draw': self.draw.draw_id}), data)
        # Vérifier le statut de la réponse
        self.assertEqual(response.status_code, 200)
        self.assertIn('Participation soumise avec succès !', response.json().get('message'))
        print("Le test de participation au tirage a réussi !")

    

    def test_participate_draw_error_too_many_numbers(self):
        # Tester qu'une erreur est renvoyée si un joueur soumet trop de numéros principaux
        data = {
            'players': [{'name': 'player1', 'numbers': [1, 2, 3, 4, 5,6], 'bonus': [1, 2]}],
        }
        response = self.client.post(reverse('participate_draw'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

class LoginUserTests(TestCase):
    
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = Users.objects.create(username='player1')

    def test_login_success(self):
        # Tester que la connexion réussit
        data = {'username': 'player1'}
        response = self.client.post(reverse('login'), data=data)
        
        # Vérifier que la réponse est une redirection
        self.assertEqual(response.status_code, 302)  # Redirection vers la page d'accueil
        self.assertRedirects(response, reverse('home'))  # Vérifier la redirection vers la bonne page

    def test_login_invalid_username(self):
        # Tester que la connexion échoue avec un pseudo invalide
        data = {'username': 'non_existent_user'}
        response = self.client.post(reverse('login'), data=data)
        
        # Vérifier que la réponse reste sur la page de connexion
        self.assertEqual(response.status_code, 200)  # Vérifier que le statut est 400
        self.assertContains(response, 'Identifiants invalides')  # Vérifier que le message d'erreur est présent

def test_utilisateur_renseigne_un_espace_a_la_connexion(self):
    # Essayer de se connecter avec un pseudo contenant des espaces
    data = {'username': ' player1 '}
    response = self.client.post(reverse('login'), data=data)
    
    # Vérifier que l'utilisateur ne peut pas se connecter
    self.assertContains(response, 'Identifiants invalides')




class EvaluateClosestSumTests(TestCase):
    
    def test_evaluate_closest_sum(self):
        # Cas de test 1 : Les mêmes numéros
        winning_numbers = [1, 2, 3, 4, 5]
        player_numbers = [1, 2, 3, 4, 5]
        result = evaluate_closest_sum(winning_numbers, player_numbers)
        self.assertEqual(result, 0)  # Les sommes doivent être égales

        # Cas de test 2 : Un numéro différent
        winning_numbers = [1, 2, 3, 4, 5]
        player_numbers = [1, 2, 3, 4, 6]
        result = evaluate_closest_sum(winning_numbers, player_numbers)
        self.assertEqual(result, 1)  # Différence de 1

        # Cas de test 3 : Deux numéros différents
        winning_numbers = [1, 2, 3, 4, 5]
        player_numbers = [1, 2, 3, 6, 7]
        result = evaluate_closest_sum(winning_numbers, player_numbers)
        self.assertEqual(result, 4)  # Différence de 4 (15 - 11)

        # Cas de test 4 : Aucun numéro correspondant
        winning_numbers = [10, 20, 30, 40, 50]
        player_numbers = [1, 2, 3, 4, 5]
        result = evaluate_closest_sum(winning_numbers, player_numbers)
        self.assertEqual(result, 135)  # Différence de 145 (150 - 5)

        # Cas de test 5 : Somme de 0 pour des numéros vides
        winning_numbers = []
        player_numbers = []
        result = evaluate_closest_sum(winning_numbers, player_numbers)
        self.assertEqual(result, 0)  # Les sommes doivent être égales

        # Cas de test 6 : Un joueur avec des numéros vides
        winning_numbers = [10, 20, 30]
        player_numbers = []
        result = evaluate_closest_sum(winning_numbers, player_numbers)
        self.assertEqual(result, 60)  # Différence de 60 (60 - 0)

class CheckingPrizeTests(TestCase):
    def test_prizes_with_ten_or_more_players(self):
        nbPlayers = 10
        expected_prizes = [
            1200000.0,  # 40% du prize pool
            600000.0,   # 20%
            360000.0,   # 12%
            210000.0,   # 7%
            180000.0,   # 6%
            150000.0,   # 5%
            120000.0,   # 4%
            90000.0,    # 3%
            60000.0,    # 2%
            30000.0     # 1%
        ]
        prizes = checkingPrize(nbPlayers)
        
        # Vérification avec une tolérance
        for expected, actual in zip(expected_prizes, prizes):
            self.assertAlmostEqual(expected, actual, places=2)

    def test_prizes_with_less_than_ten_players(self):
        for nbPlayers in range(1, 10):
            expected_total_percentage = sum([
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
            ][:nbPlayers])

            adjusted_prizes = [(prize / expected_total_percentage) * 3000000 for prize in [
                0.40,  # 40% pour le 1er
                0.20,  # 20% pour le 2ème
                0.12,  # 12% pour le 3ème
                0.07,  # 7% pour le 4ème
                0.06,  # 6% pour le 5ème
                0.05,  # 5% pour le 6ème
                0.04,  # 4% pour le 7ème
                0.03,  # 3% pour le 8ème
                0.02,  # 2% pour le 9ème
            ][:nbPlayers]]

            prizes = checkingPrize(nbPlayers)
            for expected, actual in zip(adjusted_prizes, prizes):
                self.assertAlmostEqual(expected, actual, places=2)
