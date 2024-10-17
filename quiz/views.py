import google.generativeai as genai
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Quiz
from .serializers import QuizSerializer
import os
from dotenv import load_dotenv
import re

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API'))

@api_view(['POST'])
def create_quizes(request):
    input_text = request.data.get('input_text')
    if not input_text:
        return Response({'error': 'Input text is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        prompt = f"""
        You are an AI quiz creator. Given the input text below, create multiple challenging multiple-choice quiz questions. Follow these guidelines:

        1. **Content Analysis:** Analyze the input text to identify key concepts, facts, definitions, or important ideas.
        2. **Question Generation:**
            - Generate 4 to 10 questions based on the input content.
            - Each question should test comprehension and understanding of the input text.
            - Ensure the questions are varied, including conceptual, factual, and applied knowledge.
        3. **Answer Structure:**
            - Provide one correct answer and three plausible incorrect answers for each question.
            - The incorrect answers should not be random, but reasonably related to the correct answer.
        4. **Formatting:**
            - Present each question followed by the four multiple-choice answers in this exact format:
            Question: [Question text here]
            a) [First answer]
            b) [Second answer]
            c) [Third answer]
            d) [Fourth answer]

        5. **Additional Clarifications:**
            - Use proper grammar and punctuation.
            - Ensure no ambiguity in questions and answers.
            - Start each new question with "Question:" on a new line
            - Use exactly a), b), c), d) for answer choices

        Input text:
        {input_text}
        """
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        content = response.text.strip()

        # Split content into individual questions using regex
        question_blocks = re.split(r'\n(?=Question:)', content)
        
        quizzes = []
        for block in question_blocks:
            if not block.strip():
                continue
                
            # Parse question and answers
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            
            # Extract question (remove "Question:" prefix if present)
            question = lines[0]
            if question.startswith('Question:'):
                question = question[9:].strip()
            
            # Extract answers
            answers = []
            for line in lines[1:]:
                # Match answer pattern (a), b), c), d))
                if re.match(r'^[a-d]\)', line):
                    answer = line[2:].strip()  # Remove the prefix (e.g., "a)")
                    answers.append(answer)
            
            # Only create quiz if we have a question and exactly 4 answers
            if len(answers) == 4:
                quiz = Quiz(
                    question=question,
                    answer1=answers[0],
                    answer2=answers[1],
                    answer3=answers[2],
                    answer4=answers[3]
                )
                quiz.save()
                quizzes.append(quiz)

        if not quizzes:
            return Response(
                {'error': 'No valid questions were generated'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {'error': f'An error occurred: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_quizes(request):
    quizes = Quiz.objects.all()
    serializer = QuizSerializer(quizes, many=True)
    return Response(serializer.data)