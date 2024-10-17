from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from loto_app.models import *
import json
from django.utils import timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from loto_app.views import evaluate_closest_sum, checkingPrize,process_player_participation # Assurez-vous que le chemin est correct





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
       
    @patch('loto_app.views.process_player_participation')
    def test_too_many_bonus_numbers(self, mock_create_ticket):
        """
        Teste le cas où un utilisateur renseigne un nombre supérieur à 5 numéros principaux ou 2 bonus
        """
        data = {
            'players': [{'name': 'player1', 'numbers': [1, 2, 3, 4, 5], 'bonus': [1, 2, 3]}]
        }
        response = process_player_participation(data['players'], self.draw)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Trop de numéros bonus. Un maximum de 2 numéros est autorisé.', json.loads(response.content).get('error'))

    
    def test_participate_draw_success(self):
        """
        Teste le cas où un utilisateur participe avec des numéros principaux et bonus valides.
        - Crée un ticket pour cet utilisateur
        - Vérifie que le statut de la réponse est 200
        """
        data = {
            'players': [{'name': 'player1', 'numbers': [1, 2, 3, 4, 5], 'bonus': [1, 2]}],
            'number_of_random': 1
        }
  
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

