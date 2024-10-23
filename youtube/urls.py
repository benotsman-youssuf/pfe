from django.urls import path
from . import views
urlpatterns = [
    path('get_captions/', views.get_captions, name='get_captions'),
]