from django.urls import path
from .views import create_diagram 


urlpatterns = [
    path('create_diagram/', create_diagram, name='create_diagram'),
]
