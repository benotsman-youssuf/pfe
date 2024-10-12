from django.urls import path , include
from .views import create_quizes , get_quizes

urlpatterns = [
    path('create/', create_quizes, name='create_quizes'),
    path('show/' , get_quizes , name='get_quizes')
]
