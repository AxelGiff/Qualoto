from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from loto_app.models import *
import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from loto_app.views import evaluate_closest_sum, checkingPrize # Assurez-vous que le chemin est correct





class DrawViewsTest(TestCase):
    
    def setUp(self):
        # Créer des utilisateurs pour les tests
        """
        Crée des utilisateurs pour les tests et instancie un client pour
        envoyer des requêtes.

        """

        self.user1 = Users.objects.create(username='player1')
        self.user2 = Users.objects.create(username='player2')
        ##self.user3 = Users.objects.create(username='player3')

        # Client pour envoyer des requêtes
        self.client = Client()
        
    def test_get_players(self):
        """
        Tester que la vue get_players renvoie bien la liste des joueurs
        enregistrés.
        Puis vérifie que le statut de la réponse est 200 et que la
        liste des joueurs contient les 2 joueurs créés dans setUp.
        """
        response = self.client.get(reverse('get_players'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)  # Devrait retourner les 2 joueurs créés dans setUp
    

    def test_start_draw(self):
        """
        Tester que la vue start_draw renvoie bien les données du tirage
        et des joueurs sous forme de context.

        Crée un tirage, un ticket lié à ce tirage, puis envoie une
        requête GET pour récupérer les données du tirage et des joueurs.
        Vérifie que les données attendues sont bien dans le context.
        """
        draw = Draws.objects.create(draw_date=timezone.now(), winning_main_numbers="1,2,3,4,5", winning_bonus_numbers="1,2", isFinished=False)
        
        
        
        # Créer un ticket lié à ce tirage
        Tickets.objects.create(ticket_id=1,user=self.user1, draw=draw, main_numbers="1,2,3,4,5", bonus_numbers="1,2")
        
        # Tester que les données du tirage et des joueurs sont bien récupérées
        response = self.client.get(reverse('start_draw', kwargs={'draw': draw.draw_id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('winning_numbers', response.context)
        self.assertIn('players', response.context)
    
    def test_draw_win(self):
        """
        Tester que la vue draw_win classe les joueurs et attribue des gains.

        - Crée un tirage et des tickets associés
        - Tester que la vue classe les joueurs et attribue des gains
        """
        draw = Draws.objects.create(draw_date=timezone.now(), winning_main_numbers="1,2,3,4,5", winning_bonus_numbers="1,2", isFinished=False)
        
        Tickets.objects.create(ticket_id=1,user=self.user1, draw=draw, main_numbers="1,2,3,4,5", bonus_numbers="1,2")
        Tickets.objects.create(ticket_id=2,user=self.user2, draw=draw, main_numbers="10,11,12,13,14", bonus_numbers="3,4")
        
        # Tester que la vue classe les joueurs et attribue des gains
        response = self.client.get(reverse('draw_win', kwargs={'draw': draw.draw_id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('players', response.context) # Verifie que le context contient les joueurs
        self.assertEqual(len(response.context['players']), 2) # vérifie que les 2 joueurs sont classeés
        self.assertEqual(response.context['players'][0]['username'], 'player1')  # Player1 devrait être le gagnant
    
    def test_prizes_distribution(self):
        """
        Tester la distribution des prix pour 2 joueurs
        Vérifie que la distribution des prix fonctionne bien
        """
        draw = Draws.objects.create(draw_date=timezone.now(), winning_main_numbers="1,2,3,4,5", winning_bonus_numbers="1,2", isFinished=False)
        
        # Créer des tickets
        Tickets.objects.create(ticket_id=1,user=self.user1, draw=draw, main_numbers="1,2,3,4,5", bonus_numbers="1,2")
        Tickets.objects.create(ticket_id=2,user=self.user2, draw=draw, main_numbers="10,11,12,13,14", bonus_numbers="3,4")
        
        # Vérifier que la distribution des prix fonctionne bien
        response = self.client.get(reverse('draw_win', kwargs={'draw': draw.draw_id}))
        players = response.context['players']
        self.assertEqual(players[0]['prize'], 2000000)  # Vérifier le montant pour le 1er joueur
        self.assertEqual(players[1]['prize'], 1000000)   # Vérifier le montant pour le 2ème joueur
