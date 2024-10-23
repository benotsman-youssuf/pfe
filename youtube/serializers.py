from rest_framework import serializers
from .models import Youtube

class YoutubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Youtube
        fields = ['id', 'text', 'url']
