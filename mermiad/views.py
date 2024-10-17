import google.generativeai as genai
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Diagram
from .serializers import DiagramSerializer
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API'))

@api_view(['POST'])
def create_diagram(request):
    input_text = request.data.get('input_text')
    if not input_text:
        return Response({'error': 'Input text is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        is_arabic = any("\u0600" <= char <= "\u06FF" for char in input_text)

        if is_arabic:
            prompt = f"""
            أنت خبير في إنشاء مخططات Mermaid. مهمتك هي تحليل النص التالي وإنشاء مخطط Mermaid يلخص المفاهيم الرئيسية والعلاقات بينها.

            النص: {input_text}

            التعليمات:
            1. قم بتحليل النص وتحديد المفاهيم والعلاقات الرئيسية.
            2. أنشئ مخطط Mermaid يعبر عن هذه المفاهيم والعلاقات بشكل واضح وموجز.
            3. استخدم الأشكال والأسهم المناسبة لتمثيل العلاقات بين المفاهيم.
            4. تأكد من أن المخطط سهل القراءة ومنظم بشكل جيد.
            5. قدم المخطط باستخدام صيغة Mermaid الصحيحة.

            مثال على صيغة Mermaid:
            ```mermaid
            graph TD
                A[مفهوم 1] --> B[مفهوم 2]
                B --> C[مفهوم 3]
                C --> D[مفهوم 4]
            ```

            الآن، قم بإنشاء مخطط Mermaid يلخص النص المعطى، ملتزمًا بهذه الإرشادات.
            """
        else:
            prompt = f"""
            You are an expert Mermaid diagram creator. Your task is to analyze the following text and create a Mermaid diagram that summarizes the key concepts and relationships.

            Text: {input_text}

            Instructions:
            1. Analyze the text and identify the main concepts and relationships.
            2. Create a Mermaid diagram that clearly and concisely expresses these concepts and relationships.
            3. Use appropriate shapes and arrows to represent relationships between concepts.
            4. Ensure the diagram is easy to read and well-organized.
            5. Present the diagram using correct Mermaid syntax.

            Example Mermaid syntax:
            ```mermaid
            graph TD
                A[Concept 1] --> B[Concept 2]
                B --> C[Concept 3]
                C --> D[Concept 4]
            ```

            Now, generate a Mermaid diagram summarizing the given text, adhering strictly to these guidelines.
            """

        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt)

        # Extract the Mermaid code from the response
        mermaid_code = response.text.strip()
        if mermaid_code.startswith("```mermaid"):
            mermaid_code = mermaid_code.split("```")[1].strip()

        diagram = Diagram(title=mermaid_code)
        diagram.save()

        serializer = DiagramSerializer(diagram)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)