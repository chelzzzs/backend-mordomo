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
        
        # Recupera a chave do ambiente 
        chave_api = os.environ.get("GEMINI_API_KEY")
        
        if not chave_api:
           
            return Response({
                "resposta_mordomo": "Perdão, Senhor. Minhas configurações de acesso estão incompletas.",
                "intencao": "erro_tecnico"
            }, status=500)

        # Inicializa o cliente da IA
        cliente_ia = genai.Client(api_key=chave_api)
        
        #  Chama o serviço passando o cliente e o usuário autenticado
        resultado = processar_mensagem_usuario(cliente_ia, mensagem, request.user)
        
        return Response(resultado)