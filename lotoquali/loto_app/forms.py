from django import forms
from .models import Tickets
from .models import Draws
from .models import Users

class TicketsForm(forms.ModelForm):
    class Meta:
        model = Tickets
        fields = ['main_numbers', 'bonus_numbers','user','draw','ticket']



class DrawForm(forms.ModelForm):
    class Meta:
        model = Draws
        fields = ['draw_id','winning_main_numbers','winning_bonus_numbers']

class SimulateDrawForm:
    class Meta:
        model = Draws
        fields = ['draw_id','winning_main_numbers','winning_bonus_numbers']

class UsersDrawForm:
    class Meta:
        model = Users
        fields = ['user_id']
class RegisterForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['username']