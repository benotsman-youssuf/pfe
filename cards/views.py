import google.generativeai as genai
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Card
from .serializers import CardSerializer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the Google Generative AI model with API key
genai.configure(api_key=os.getenv('GEMINI_API'))

@api_view(['POST'])
def create_cards(request):
    input_text = request.data.get('input_text')
    if not input_text:
        return Response({'error': 'Input text is required'}, status=400)

    try:
        # Check if the input is in Arabic (basic heuristic using character detection)
        is_arabic = any("\u0600" <= char <= "\u06FF" for char in input_text)

        # Use appropriate prompt based on detected language
        if is_arabic:
            prompt = f"""
            استناداً إلى النص التالي، قم بإنشاء بطاقة تعليمية بسيطة تحتوي على سؤال وإجابة:

            النص: {input_text}

            التعليمات:
            1. قم بإنشاء سؤال مباشر لاختبار مفهوم أساسي مذكور في النص.
            2. قدم إجابة مختصرة تشرح المفهوم بشكل بسيط.
            3. تأكد أن يكون السؤال قصيراً وأن تكون الإجابة لا تتجاوز جملة أو جملتين.

            التنسيق:
            السؤال: [ضع سؤالك هنا]
            الإجابة: [ضع إجابتك هنا]
            """
        else:
            prompt = f"""
            Based on the following text, generate a simple flashcard with a brief question and answer:

            Text: {input_text}

            Instructions:
            1. Create a straightforward question testing a key concept from the text.
            2. Provide a concise answer that explains the concept in a simple way.
            3. Ensure the question is short and the answer is no longer than one or two sentences.

            Format:
            Question: [Your generated question here]
            Answer: [Your generated answer here]
            """

        # Generate the content using the AI model
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        # Extract the question and answer from the response
        content = response.text.split('\n')
        question = content[0].replace('Question:', '').strip()
        answer = ' '.join(content[1:]).replace('Answer:', '').strip()

        # Create a new Card instance and save it to the database
        card = Card(question=question, answer=answer)
        card.save()

        # Serialize the card and include the required response format
        serializer = CardSerializer(card)
        response_data = {
            'id': serializer.data['id'],
            'question': serializer.data['question'],
            'answer': serializer.data['answer']
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=500)
