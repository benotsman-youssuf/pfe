import google.generativeai as genai
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Card
from .serializers import CardSerializer
import os
from dotenv import load_dotenv
from typing import Dict, List
import re

# Load environment variables
load_dotenv()

# Configure the Google Generative AI model with API key
genai.configure(api_key=os.getenv('GEMINI_API'))

def detect_language(text: str) -> str:
    """
    Detect the primary language of the input text.
    Currently supports Arabic, English, and Chinese detection.
    """
    # Arabic character range
    if any("\u0600" <= char <= "\u06FF" for char in text):
        return "arabic"
    # Chinese character range
    elif any("\u4e00" <= char <= "\u9fff" for char in text):
        return "chinese"
    # Default to English for other scripts
    return "english"

def get_prompt_template(language: str, customizations: Dict = None) -> str:
    """
    Get the appropriate prompt template based on language and custom parameters.
    """
    base_prompts = {
        "english": """
        You are an expert educator tasked with creating comprehensive flashcards from the provided text.
        
        Text: {input_text}
        
        Guidelines for flashcard creation:
        1. Analyze the text thoroughly to identify:
           - Key concepts and definitions
           - Important facts and figures
           - Cause-and-effect relationships
           - Sequential processes
           - Notable examples and applications
        
        2. Create flashcards following these rules:
           - Minimum cards: {min_cards}
           - Maximum cards: {max_cards}
           - Question format: {question_format}
           - Answer length: {answer_length}
           - Include {special_focus} concepts
        
        3. Structural requirements:
           - Format each card as "Question\\nAnswer"
           - Separate cards with double newlines
           - Questions should be clear and specific
           - Answers should be concise but complete
        
        4. Special instructions:
           - {special_instructions}
           - Ensure progressive difficulty when relevant
           - Include application-based questions
           - Create reverse cards for key concepts
        
        Example format:
        What is the primary function of mitochondria?
        Generates cellular energy through ATP production.

        Define osmosis in simple terms.
        Movement of water molecules across a semi-permeable membrane.
        """,
        
        "arabic": """
        أنت خبير تعليمي مكلف بإنشاء بطاقات تعليمية شاملة من النص المقدم.

        النص: {input_text}

        إرشادات إنشاء البطاقات التعليمية:
        1. تحليل النص بدقة لتحديد:
           - المفاهيم والتعريفات الرئيسية
           - الحقائق والأرقام المهمة
           - علاقات السبب والنتيجة
           - العمليات المتسلسلة
           - الأمثلة والتطبيقات البارزة

        2. إنشاء البطاقات وفقاً للقواعد التالية:
           - الحد الأدنى للبطاقات: {min_cards}
           - الحد الأقصى للبطاقات: {max_cards}
           - صيغة السؤال: {question_format}
           - طول الإجابة: {answer_length}
           - تضمين مفاهيم {special_focus}

        3. المتطلبات الهيكلية:
           - تنسيق كل بطاقة كـ "سؤال\\nجواب"
           - فصل البطاقات بسطرين جديدين
           - يجب أن تكون الأسئلة واضحة ومحددة
           - يجب أن تكون الإجابات موجزة ولكن كاملة

        4. تعليمات خاصة:
           - {special_instructions}
           - ضمان التدرج في الصعوبة عند الاقتضاء
           - تضمين أسئلة تطبيقية
           - إنشاء بطاقات عكسية للمفاهيم الرئيسية
        """,
        
        "chinese": """
        您是一位专业教育专家，负责从提供的文本中创建全面的学习卡片。

        文本：{input_text}

        学习卡片创建指南：
        1. 仔细分析文本以确定：
           - 关键概念和定义
           - 重要事实和数据
           - 因果关系
           - 顺序过程
           - 显著的例子和应用

        2. 按照以下规则创建卡片：
           - 最少卡片数：{min_cards}
           - 最多卡片数：{max_cards}
           - 问题格式：{question_format}
           - 答案长度：{answer_length}
           - 包含{special_focus}概念

        3. 结构要求：
           - 将每张卡片格式化为"问题\\n答案"
           - 用双换行符分隔卡片
           - 问题应清晰具体
           - 答案应简明但完整

        4. 特别说明：
           - {special_instructions}
           - 在相关时确保难度递进
           - 包含应用型问题
           - 为关键概念创建反向卡片
        """
    }
    
    # Get base prompt for the language
    prompt = base_prompts.get(language, base_prompts["english"])
    
    # Apply customizations if provided
    default_customizations = {
        "min_cards": 3,
        "max_cards": 20,
        "question_format": "concise 5-7 words",
        "answer_length": "one sentence, 10-15 words",
        "special_focus": "theoretical and practical",
        "special_instructions": "prioritize clear, actionable learning outcomes"
    }
    
    # Merge default customizations with provided ones
    final_customizations = {**default_customizations, **(customizations or {})}
    
    return prompt.format(**final_customizations, input_text="{input_text}")

def parse_flashcards(content: str) -> List[Dict[str, str]]:
    """
    Parse the AI response into structured flashcard data.
    Handles various formats and cleans the output.
    """
    # Split content into individual cards
    cards_raw = re.split(r'\n\s*\n', content.strip())
    
    parsed_cards = []
    for card_raw in cards_raw:
        # Skip empty cards
        if not card_raw.strip():
            continue
            
        # Try different splitting patterns
        splits = card_raw.split('\n')
        splits = [s.strip() for s in splits if s.strip()]
        
        if len(splits) >= 2:
            # Extract question and answer
            question = splits[0]
            answer = splits[1]
            
            # Clean up common formatting issues
            question = re.sub(r'^Q:\s*|^\d+\.\s*|^Question:\s*', '', question)
            answer = re.sub(r'^A:\s*|^Answer:\s*', '', answer)
            
            parsed_cards.append({
                'question': question.strip(),
                'answer': answer.strip()
            })
    
    return parsed_cards

@api_view(['POST'])
def create_cards(request):
    """
    Create flashcards from input text with advanced customization options.
    """
    input_text = request.data.get('input_text')
    if not input_text:
        return Response({'error': 'Input text is required'}, status=400)

    try:
        # Get customization parameters from request
        customizations = {
            'min_cards': request.data.get('min_cards', 3),
            'max_cards': request.data.get('max_cards', 20),
            'question_format': request.data.get('question_format'),
            'answer_length': request.data.get('answer_length'),
            'special_focus': request.data.get('special_focus'),
            'special_instructions': request.data.get('special_instructions')
        }
        
        # Remove None values
        customizations = {k: v for k, v in customizations.items() if v is not None}

        # Detect language and get appropriate prompt
        language = detect_language(input_text)
        prompt_template = get_prompt_template(language, customizations)
        
        # Generate content using the AI model
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt_template.format(input_text=input_text))
        
        # Parse the generated content
        parsed_cards = parse_flashcards(response.text)
        
        # Save cards to database
        saved_cards = []
        for card_data in parsed_cards:
            card = Card.objects.create(
                question=card_data['question'],
                answer=card_data['answer']
            )
            saved_cards.append(card)

        # Serialize and return the response
        serializer = CardSerializer(saved_cards, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': str(e),
            'error_type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)