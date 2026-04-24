from rest_framework import serializers
from .models import Transacao, Categoria, Perfil, DespesaFixa


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome']

class TransacaoSerializer(serializers.ModelSerializer):
    
    categoria = serializers.StringRelatedField() 

    class Meta:
        model = Transacao
        fields = ['id', 'descricao', 'valor', 'data', 'tipo', 'categoria', 'criado_em']



class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['renda_mensal']

class DespesaFixaSerializer(serializers.ModelSerializer):
   
    percentual_pago = serializers.ReadOnlyField() 

    class Meta:
        model = DespesaFixa
        fields = ['id', 'descricao', 'valor', 'parcelas_totais', 'parcelas_pagas', 'percentual_pago']