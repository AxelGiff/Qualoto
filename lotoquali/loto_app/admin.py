from django.contrib import admin
from .models import Draws, Users  # Import des modèles

# Enregistrement des modèles dans l'admin
admin.site.register(Draws)
admin.site.register(Users)
