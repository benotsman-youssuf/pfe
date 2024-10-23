import re
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Youtube
from .serializers import YoutubeSerializer
from youtube_transcript_api import YouTubeTranscriptApi


@api_view(['POST'])
def get_captions(request):
    url = request.data.get('url')
    if not url:
        return Response({'error': 'URL is required'}, status=400)
    
    # Regex pattern to match different YouTube URL formats
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    
    if not video_id_match:
        return Response({'error': 'Invalid YouTube URL'}, status=400)

    video_id = video_id_match.group(1)

    try:
        # Fetch the transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        # Extract the text from the transcript
        text = ' '.join([item['text'] for item in transcript])

        # Create a new Youtube instance and save it to the database
        youtube = Youtube(url=url, text=text)
        youtube.save()

        # Serialize the Youtube instance
        serializer = YoutubeSerializer(youtube)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=500)
