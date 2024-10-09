from django.db import models

class Card(models.Model):
    question = models.CharField(max_length=200)
    answer = models.CharField(max_length=200)
    def __str__(self):
        return self.Question