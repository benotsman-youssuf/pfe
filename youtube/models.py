from django.db import models

class Youtube(models.Model):
    url = models.CharField(max_length=200, default='default-url')  # Add default value
    text = models.TextField()
    