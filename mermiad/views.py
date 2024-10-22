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
            You are an expert Mermaid diagram creator specializing in educational content visualization. Your task is to analyze the following text and create a comprehensive, hierarchical Mermaid diagram with clickable nodes linking to authoritative and educational resources.

            Text to analyze: {input_text}

            Instructions:
            1. ANALYSIS PHASE:
                - Identify main concepts, sub-concepts, and their relationships
                - Determine natural groupings and hierarchies
                - Identify key terms that require external references

            2. DIAGRAM STRUCTURE:
                - Use graph TD for top-down hierarchical layout
                    - Implement clear visual hierarchy with main concepts at top
                - Limit diagram width to 3-4 nodes per level for readability
                - Use consistent naming conventions for nodes (e.g., mainTopic_subTopic)

            3. NODE FORMATTING:
                - Main concepts: Use descriptive labels in square brackets
                - Sub-concepts: Include brief, clear descriptions
                - Add hover text using quotation marks for additional context
                - Ensure each node has a unique identifier

            4. LINKING STRATEGY:
                - Primary sources: Wikipedia for fundamental concepts
                - Secondary sources: Educational websites (e.g., Khan Academy, W3Schools)
                - Academic sources: Google Scholar or research papers when applicable
                - Documentation: Official docs for technical concepts
                - Use this syntax: click nodeId "URL" "Hover text"

            5. RELATIONSHIP REPRESENTATION:
                - --> for direct relationships
                - --- for loose associations
                - -.- for optional relationships
                - === for emphasized connections

            Example Structure:
            ```mermaid
            graph TD
                A["Main Concept"]
                B["Sub-Concept 1"]
                C["Sub-Concept 2"]

                A --> B
                A --> C
                B --> D["Detail 1"]
                B --> E["Detail 2"]
                C --> F["Detail 3"]

                %% Clickable nodes with hover text
                click A "https://en.wikipedia.org/wiki/Main_Concept" "Click to learn more about Main Concept"
                click B "https://edu-source.org/sub1" "Detailed explanation of Sub-Concept 1"
                click C "https://docs.example.com/sub2" "Official documentation for Sub-Concept 2"
            ```

            Source Priority List:
            1. Wikipedia (for general concepts)
            2. Official Documentation (for technical topics)
            3. Educational Platforms (khanacademy )
            4. Research Papers (for academic concepts)
            5. Industry Standard Resources (W3Schools, MDN, youtube , medium , etc.)

            Please generate a comprehensive Mermaid diagram following these guidelines, ensuring all nodes are clickable and link to relevant, authoritative sources.
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