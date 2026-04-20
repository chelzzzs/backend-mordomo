# financas/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.utils import timezone  # <-- Adicionamos o relógio do Django
from .models import Transacao, Categoria

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        
        # 1. Totais para os Cards
        receitas = Transacao.objects.filter(usuario=usuario).filter(
            Q(tipo__icontains='receita') | Q(tipo__icontains='entrada')
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        despesas = Transacao.objects.filter(usuario=usuario).filter(
            Q(tipo__icontains='despesa') | Q(tipo__icontains='saida') | Q(tipo__icontains='saída')
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        # 2. Dados para o Gráfico de Pizza (Gastos por Categoria)
        gastos_por_categoria = Transacao.objects.filter(
            usuario=usuario
        ).filter(
            Q(tipo__icontains='despesa') | Q(tipo__icontains='saida') | Q(tipo__icontains='saída')
        ).values('categoria__nome').annotate(total=Sum('valor'))

        pizza_dados = []
        for item in gastos_por_categoria:
            pizza_dados.append({
                'name': item['categoria__nome'] or 'Outros',
                'value': float(item['total'])
            })

        # 3. Histórico do Gráfico de Linha e Últimas Transações
        transacoes_cronologicas = Transacao.objects.filter(usuario=usuario).order_by('data', 'id')
        saldo_corrente = 0
        grafico_dados = []
        for t in transacoes_cronologicas:
            is_receita = any(x in t.tipo.lower() for x in ['receita', 'entrada'])
            saldo_corrente += float(t.valor) if is_receita else -float(t.valor)
            dia = t.data.strftime('%d/%m') if t.data else '?'
            if grafico_dados and grafico_dados[-1]['dia'] == dia:
                grafico_dados[-1]['saldo'] = saldo_corrente
            else:
                grafico_dados.append({'dia': dia, 'saldo': saldo_corrente})

        ultimas = Transacao.objects.filter(usuario=usuario).order_by('-data', '-id')[:5]
        lista_ultimas = [{'descricao': u.descricao, 'valor': float(u.valor), 'is_receita': any(x in u.tipo.lower() for x in ['receita', 'entrada']), 'data': u.data.strftime('%d/%m')} for u in ultimas]

        # 4. Lista de Categorias GLOBAIS para o Formulário Manual
        categorias = Categoria.objects.all().values('id', 'nome')

        return Response({
            'saldo_atual': receitas - despesas,
            'total_receitas': receitas,
            'total_despesas': despesas,
            'grafico_pizza': pizza_dados,
            'grafico_linha': grafico_dados,
            'ultimas_transacoes': lista_ultimas,
            'categorias': list(categorias)
        })

    def post(self, request):
        # Rota para salvar a entrada manual
        usuario = request.user
        dados = request.data
        
        # Pega a categoria correta, seja sua ou global
        categoria = Categoria.objects.get(id=dados['categoria_id'])
        
        # Cria a transação avisando o banco que a data é "agora"
        Transacao.objects.create(
            usuario=usuario,
            descricao=dados['descricao'],
            valor=dados['valor'],
            tipo=dados['tipo'],
            categoria=categoria,
            data=timezone.now() # <-- CORREÇÃO: Enviando a data atual!
        )
        return Response({'status': 'sucesso'})