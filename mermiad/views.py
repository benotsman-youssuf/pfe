import google.generativeai as genai
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Diagram
from .serializers import DiagramSerializer
import os
from dotenv import load_dotenv
import re
from typing import Dict, Tuple

# Load environment variables
load_dotenv()

# Configure the Google Generative AI model with API key
genai.configure(api_key=os.getenv('GEMINI_API'))

def detect_language(text: str) -> str:
    """Detect the primary language of the input text."""
    return "arabic" if any("\u0600" <= char <= "\u06FF" for char in text) else "english"

def validate_mermaid_syntax(diagram: str) -> Tuple[bool, str]:
    """
    Validate Mermaid diagram syntax and clean up common issues.
    Returns (is_valid, cleaned_diagram).
    """
    # Remove any markdown code block markers
    diagram = re.sub(r'```mermaid\s*|```\s*$', '', diagram.strip())
    
    # Basic syntax validation
    required_elements = [
        ('graph', r'(graph|flowchart)\s+(TB|TD|BT|RL|LR)'),
        ('nodes', r'\w+\s*(\[|\(|\{).*?(\]|\)|\})'),
        ('connections', r'\w+\s*(-+>|\.+>|=+>)\s*\w+'),
    ]
    
    for element, pattern in required_elements:
        if not re.search(pattern, diagram):
            return False, f"Missing or invalid {element} definition"
    
    # Clean up formatting
    diagram = re.sub(r'\s+', ' ', diagram)  # Normalize whitespace
    diagram = re.sub(r'(\[|\(|\{)\s+', r'\1', diagram)  # Remove space after brackets
    diagram = re.sub(r'\s+(\]|\)|\})', r'\1', diagram)  # Remove space before brackets
    
    return True, diagram

def get_prompt_template(language: str) -> str:
    """Get the appropriate prompt template based on language."""
    templates = {
        "arabic": """
        أنت خبير في إنشاء مخططات Mermaid. مهمتك هي تحليل النص التالي وإنشاء مخطط Mermaid يلخص المفاهيم الرئيسية والعلاقات بينها.

        النص: {input_text}

        التعليمات:
        1. تحليل النص:
           - حدد المفاهيم الرئيسية والفرعية
           - حدد العلاقات والتسلسلات المنطقية
           - اكتشف التصنيفات والمجموعات الطبيعية

        2. بنية المخطط:
           - استخدم graph TD للتخطيط الهرمي من أعلى إلى أسفل
           - حافظ على عرض المخطط 3-4 عقد لكل مستوى
           - استخدم تسميات عربية واضحة وموجزة

        3. تنسيق العقد:
           - المفاهيم الرئيسية: استخدم الأقواس المربعة []
           - المفاهيم الفرعية: أضف وصفاً موجزاً
           - استخدم معرفات فريدة لكل عقدة

        4. العلاقات:
           - --> للعلاقات المباشرة
           - --- للروابط غير المباشرة
           - -.- للعلاقات الاختيارية
           - === للروابط المؤكدة

        5. مصادر الروابط:
           - المواقع التعليمية الرسمية
           - منصات التعلم العربية
           - المصادر الأكاديمية العربية
           - الوثائق التقنية المترجمة

        يجب أن يبدأ المخطط بـ:
        graph TD
        
        مثال على الصيغة المطلوبة:
        graph TD
            A[المفهوم الرئيسي] --> B[المفهوم الفرعي 1]
            A --> C[المفهوم الفرعي 2]
            B --> D[التفصيل 1]
            C --> E[التفصيل 2]
        """,
        
        "english": """
        You are an expert Mermaid diagram creator. Your task is to analyze the text and create a valid, well-structured Mermaid diagram.

        Text to analyze: {input_text}

        CRITICAL REQUIREMENTS:
        1. ALWAYS start with 'graph TD' on its own line
        2. Use ONLY valid Mermaid syntax
        3. Ensure all node IDs are alphanumeric (no spaces or special characters)
        4. Test all connections for valid syntax
        5. Keep node texts concise and clear
        6. Limit diagram width to 3-4 nodes per level

        FORMATTING RULES:
        1. Node Structure:
           - Main concepts: nodeId[Main Concept]
           - Sub-concepts: subNodeId[Sub Concept]
           - Use underscores for multi-word IDs: main_concept
        
        2. Connections:
           - Basic: A --> B
           - Dotted: A -.-> B
           - Thick: A ==> B
           - With text: A -->|describes| B
        
        3. Subgraphs (if needed):
           subgraph title
           node1 --> node2
           end

        4. Link URLs:
           click nodeId "URL" "Hover text"
           
        Educational Sources Priority:
        1. me-iu-dm (preferred)
        2. Official documentation
        3. Educational platforms
        4. Industry resources
        5. Research papers

        Example of required format:
        graph TD
            A[Main Concept] --> B[First Point]
            A --> C[Second Point]
            B --> D[Detail 1]
            C --> E[Detail 2]
            
            click A "https://me-iu-dm/topic" "Learn more"
            click B "https://docs.example.com" "Official docs"
        """
    }
    
    return templates.get(language, templates["english"])

@api_view(['POST'])
def create_diagram(request):
    """Create a Mermaid diagram from input text."""
    input_text = request.data.get('input_text')
    if not input_text:
        return Response({'error': 'Input text is required'}, status=400)

    try:
        # Detect language and get appropriate prompt
        language = detect_language(input_text)
        prompt_template = get_prompt_template(language)
        
        # Generate diagram using AI model
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt_template.format(input_text=input_text))
        
        # Extract and validate Mermaid code
        mermaid_code = response.text.strip()
        is_valid, cleaned_code = validate_mermaid_syntax(mermaid_code)
        
        if not is_valid:
            # If invalid, try to regenerate with more explicit instructions
            retry_prompt = f"""
            The previous attempt produced invalid Mermaid syntax. Please create a new diagram following these strict rules:
            1. Start with 'graph TD' on its own line
            2. Use only basic node definitions: ID[Text]
            3. Use only simple connections: -->
            4. Ensure all node IDs are alphanumeric
            5. Keep it simple and valid
            
            Original text: {input_text}
            """
            
            retry_response = model.generate_content(retry_prompt)
            is_valid, cleaned_code = validate_mermaid_syntax(retry_response.text.strip())
            
            if not is_valid:
                return Response({
                    'error': 'Unable to generate valid Mermaid diagram',
                    'details': cleaned_code
                }, status=400)

        # Save the validated diagram
        diagram = Diagram.objects.create(
            title=cleaned_code,
            source_text=input_text,
            language=language
        )

        serializer = DiagramSerializer(diagram)
        return Response({
            'diagram': serializer.data,
            'mermaid_code': cleaned_code
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': 'Failed to generate diagram',
            'details': str(e),
            'error_type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)