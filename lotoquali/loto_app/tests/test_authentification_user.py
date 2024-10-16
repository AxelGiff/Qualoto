from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from loto_app.models import *
import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from loto_app.views import evaluate_closest_sum, checkingPrize # Assurez-vous que le chemin est correct


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
