from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from loto_app.models import *
import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from loto_app.views import evaluate_closest_sum, checkingPrize # Assurez-vous que le chemin est correct





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

class CheckingPrizeTests(TestCase):
    def test_prix_quand_dix_ou_plus_de_dix_joueurs(self):
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

    def test_prix_quand_moins_de_10_joueurs(self):
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
