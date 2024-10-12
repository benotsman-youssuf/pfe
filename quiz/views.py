import google.generativeai as genai
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Quiz
from .serializers import QuizSerializer
import os
from dotenv import load_dotenv


load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API'))

@api_view(['POST'])
def create_quizes(request):
    input_text = request.data.get('input_text')
    if not input_text:
        return Response({'error':'Input text is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        prompt = f"""Given the input text below, create a challenging quiz question with multiple-choice answers following these guidelines:

        1. Analyze the input text thoroughly to identify key concepts, important facts, or central themes.
        2. Formulate a thought-provoking question that tests deep understanding of the material.
        3. Create one correct answer and three plausible but incorrect answers.
        4. Present the output as follows in this structure in this example:

        what is the capital of france?
        paris
        london
        berlin
        rome

        Ensure that:
        - The question is clear, concise, and directly related to the most significant aspects of the input text.
        - The question requires critical thinking or application of knowledge, not just recall.
        - All answers are of similar length, style, and complexity to avoid unintentional hints.
        - Incorrect answers are highly plausible, related to the topic, and could trick someone who doesn't fully understand the material.
        - Each answer is on a separate line without labels or bullet points.
        - The correct answer is always the first option listed.

        Avoid:
        - Obvious trick questions or puns
        - True/False questions
        - "All of the above" or "None of the above" options
        - Answers that are partially correct

        Input text:
        {input_text}

        Generate a challenging quiz based on the above instructions, focusing on the most important or interesting information from the input text.
        """
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        content = response.text.strip().split('\n')
        
        # More robust parsing
        question = content[0].strip()
        answers = [line.strip() for line in content[1:] if line.strip()]

        # Create the quiz object
        quiz = Quiz(
            question=question,
            answer1=answers[0],
            answer2=answers[1],
            answer3=answers[2],
            answer4=answers[3]
        )
        quiz.save()

        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def get_quizes(request):
    quizes = Quiz.objects.all()
    serializer = QuizSerializer(quizes, many=True)
    return Response(serializer.data)



