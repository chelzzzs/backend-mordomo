from rest_framework import serializers
from .models import Transacao, Categoria

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome']

class TransacaoSerializer(serializers.ModelSerializer):
    # O StringRelatedField faz o Django retornar o NOME da categoria em vez de apenas o ID numérico
    categoria = serializers.StringRelatedField() 

    class Meta:
        model = Transacao
        fields = ['id', 'descricao', 'valor', 'data', 'tipo', 'categoria', 'criado_em']