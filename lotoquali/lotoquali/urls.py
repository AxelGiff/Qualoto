"""
URL configuration for lotoquali project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from loto_app.views import create_draw
from loto_app.views import home_view,register_view,login_view,logout_view, participate_draw, simulate_draw,start_draw,draw_win,get_players


urlpatterns = [
    path('register/',register_view,name='register'),
    path('login',login_view,name='login'),
    path('admin/', admin.site.urls),
    path('logout',logout_view,name='logout'),
    path('participate_draw/', participate_draw, name='participate_draw'),
    #path('simulate_draw/', simulate_draw, name='simulate_draw'),
    path('draw_win/<int:draw>/', draw_win, name='draw_win'),
    path('start_draw/<int:draw>/', start_draw, name='start_draw'),
    path('get_players/', get_players, name='get_players'),
    path('draw', create_draw, name='create_draw'),
    ##path('draw', draw_view, name='draw_view'),
    path('', home_view, name='home'),

]
