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
            أنت خبير في إنشاء البطاقات التعليمية (الفلاش كارد) مكلف بإنتاج 10 بطاقات تعليمية عالية الجودة وموجزة على الأقل من النص التالي. هدفك هو التقاط أهم المعلومات في شكل سهل الاستيعاب.
            النص: {input_text}
            التعليمات:

            1-قم بتحليل النص بدقة وحدد 10   مفاهيم أو حقائق أو مواضيع رئيسية على الأقل.
            2-لكل عنصر تم تحديده، قم بإنشاء سؤال موجز للغاية وإجابة مختصرة ومركزة.
            3-تأكد من أن الأسئلة لا تتجاوز 5-7 كلمات كحد أقصى وأن الإجابات تقتصر على جملة قصيرة واحدة (10-15 كلمة كحد أقصى).
            4-قدم كل بطاقة تعليمية كزوج سؤال وإجابة، مفصولين بسطر واحد فقط.
            5-استخدم سطرين فارغين بين البطاقات التعليمية للفصل الواضح.
            6-أعط الأولوية للوضوح والإيجاز في كل من الأسئلة والأجابات.
            6-إذا لم ينتج النص بشكل طبيعي 10 مفاهيم متميزة، قم بإنشاء بطاقات تعليمية إضافية عن طريق تفكيك الأفكار المعقدة أو استكشاف المواضيع الفرعية ذات الصلة.

            شكل المثال:
            ما هي عاصمة السعودية
            الرياض

            من كتب رواية "ألف ليلة وليلة"
            مؤلف مجهول، تعود لعصر الدولة العباسية

            متى انتهت الحرب العالمية الثانية
            انتهت عام 1945 باستسلام دول المحور

            ما هي سرعة الضوء
            حوالي 299,792,458 متر في الثانية في الفراغ

            والآن، قم بإنشاء 10 بطاقات تعليمية على الأقل من النص المعطى، ملتزمًا بدقة بهذه الإرشادات. ركز على إنشاء بطاقات تعليمية موجزة ومفيدة ومتنوعة تلخص النقاط الرئيسية بشكل فعال.
            """
        else:
            prompt = f"""
            You are an expert flashcard creator tasked with generating high-quality, concise flashcards from the following text. Your goal is to capture the most important information in an easily digestible format.
            
            Text: {input_text}
            
            Instructions:
            1. Thoroughly analyze the text and identify all key concepts, facts, or topics.
            2. Create a minimum of 3 flashcards and a maximum number that covers all main ideas in the text.
            3. For each identified element, create an ultra-concise question and a brief, focused answer.
            4. Ensure questions are 5-7 words maximum and answers are limited to one short sentence (10-15 words max).
            5. Present each flashcard as a question-answer pair, separated by a single line break.
            6. Use a double line break between flashcards for clear separation.
            7. Prioritize clarity and brevity in both questions and answers.
            8. If the text contains fewer than 3 distinct main ideas, create additional flashcards by breaking down complex concepts or exploring related subtopics.
            9. If the text contains many important ideas, create as many flashcards as necessary to cover all main points, even if it exceeds 10 cards.

            Example format:
            What is photosynthesis?
            Process where plants convert sunlight into energy.

            Who wrote "To Kill a Mockingbird"?
            Harper Lee authored this classic American novel.

            When did World War II end?
            WWII concluded in 1945 with Axis powers' surrender.

            Now, generate flashcards from the given text, adhering strictly to these guidelines. Focus on creating concise, informative, and diverse flashcards that effectively summarize all key points in the text.
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