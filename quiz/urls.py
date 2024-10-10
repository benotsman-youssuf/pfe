from django.urls import path , include
from .views import create_quizes

urlpatterns = [
    path('create/', create_quizes, name='create_quizes'),
]
