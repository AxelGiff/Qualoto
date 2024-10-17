
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from loto_app.models import *
import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from loto_app.views import evaluate_closest_sum, checkingPrize # Assurez-vous que le chemin est correct




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
        data = {'username': ' '}
        response = self.client.post(reverse('login'), data=data)
    
    # Vérifier que l'utilisateur ne peut pas se connecter
        self.assertContains(response, 'Identifiants invalides')

