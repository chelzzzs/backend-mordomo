# assistente_ai/views.py
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from google import genai
from .services import processar_mensagem_usuario

class ChatMordomoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mensagem = request.data.get('mensagem')
        
        # 1. Recupera a chave do ambiente (sem o fallback de texto)
        chave_api = os.environ.get("GEMINI_API_KEY")
        
        if not chave_api:
            # Se a chave não existir, o Mordomo avisa o erro técnico
            return Response({
                "resposta_mordomo": "Perdão, Senhor. Minhas configurações de acesso estão incompletas.",
                "intencao": "erro_tecnico"
            }, status=500)

        # 2. Inicializa o cliente da IA
        cliente_ia = genai.Client(api_key=chave_api)
        
        # 3. Chama o serviço passando o cliente e o usuário autenticado
        resultado = processar_mensagem_usuario(cliente_ia, mensagem, request.user)
        
        return Response(resultado)