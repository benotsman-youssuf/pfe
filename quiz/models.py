from django.db import models

class Quiz(models.Model):
    question = models.CharField(max_length=200)
    answer1 = models.CharField(max_length=500)
    answer2 = models.CharField(max_length=500)
    answer3 = models.CharField(max_length=500)
    answer4 = models.CharField(max_length=500)
    
    def __str__(self):
        return self.question