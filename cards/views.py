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
            prompt = f'''
            النص: {input_text}

            التعليمات:
            1. حدد المفاهيم أو المواضيع الرئيسية في النص.
            2. لكل مفهوم، قم بإنشاء سؤال قصير جدًا وإجابة موجزة.
            3. تأكد من أن كل سؤال مختصر للغاية وأن الإجابة لا تتجاوز جملة واحدة.
            4. اكتب كل زوج من السؤال والإجابة في سطرين منفصلين، مع ترك سطر فارغ بين كل بطاقة تعليمية.
            5. قلل من الكلمات غير الضرورية في الأسئلة والإجابات.

            مثال على التنسيق المطلوب:
            ما عاصمة فرنسا؟
            باريس.

            ما هو أطول نهر في العالم؟
            نهر النيل، بطول 6,650 كم.

            الآن، قم بإنشاء البطاقات التعليمية وفقًا للتعليمات أعلاه، بشكل مثالي لإنشاء بطاقات تعليمية مع تقليل طول الأسئلة والإجابات.
            '''
        else:
            prompt = f"""
            You are an experienced flashcard creator. Based on the following text, generate multiple flashcards covering the main subjects in the text:

            Text: {input_text}

            Instructions:
            1. Identify the key concepts or topics in the text.
            2. For each concept, create a very short, summarized question and a concise answer.
            3. Ensure each question is extremely brief and the answer is no longer than one sentence.
            4. Write each question-answer pair on separate lines, with a blank line separating each flashcard.
            5. Minimize unnecessary words in both questions and answers.

            Example of the required format:
            Capital of France?
            Paris.

            Longest river?
            The Nile, 6,650 km long.

            Now, create the flashcards according to the instructions above, perfect for creating flash cards and minimizing the length of questions and answers.
            """

        # Generate the content using the AI model
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        # Extract the questions and answers from the response
        content = response.text.split('\n\n')
        
        cards = []
        for card_content in content:
            qa_pair = card_content.split('\n')
            if len(qa_pair) == 2:
                question, answer = qa_pair
                # Create a new Card instance and save it to the database
                card = Card(question=question, answer=answer)
                card.save()
                cards.append(card)

        # Serialize the cards and include the required response format
        serializer = CardSerializer(cards, many=True)
        response_data = [
            {
                'id': card['id'],
                'question': card['question'],
                'answer': card['answer']
            }
            for card in serializer.data
        ]

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=500)