from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from loto_app.models import *
import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from loto_app.views import evaluate_closest_sum, checkingPrize # Assurez-vous que le chemin est correct





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
            'players': [{'name': 'player1', 'numbers': [1, 3, 4, 5,6], 'bonus': [1, 2]}],
        }
        response = self.client.post(reverse('participate_draw'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
