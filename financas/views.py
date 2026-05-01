from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, viewsets
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Transacao, Categoria, Perfil, DespesaFixa
from .serializers import PerfilSerializer, DespesaFixaSerializer


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        
        # 1. Puxo minha renda fixa do perfil
        perfil, _ = Perfil.objects.get_or_create(usuario=usuario)
        renda_fixa = float(perfil.renda_mensal) if perfil.renda_mensal else 0.0

        # 2. Somo todas as minhas despesas fixas cadastradas
        total_despesas_fixas = DespesaFixa.objects.filter(usuario=usuario).aggregate(Sum('valor'))['valor__sum'] or 0
        total_despesas_fixas = float(total_despesas_fixas)

        # 3. Calculo minhas receitas avulsas (transações manuais)
        receitas_avulsas = Transacao.objects.filter(usuario=usuario).filter(
            Q(tipo__icontains='receita') | Q(tipo__icontains='entrada')
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        receitas_avulsas = float(receitas_avulsas)
        
        # 4. Calculo minhas despesas avulsas (transações manuais)
        despesas_avulsas = Transacao.objects.filter(usuario=usuario).filter(
            Q(tipo__icontains='despesa') | Q(tipo__icontains='saida') | Q(tipo__icontains='saída')
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        despesas_avulsas = float(despesas_avulsas)
        
        # 5. Junto os dois cadernos para os totais finais
        total_receitas_geral = renda_fixa + receitas_avulsas
        total_despesas_geral = total_despesas_fixas + despesas_avulsas
        saldo_real = total_receitas_geral - total_despesas_geral

        # Agrupo meus gastos por categoria para o gráfico de pizza (apenas avulsos)
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

        # Monto a linha do tempo do meu saldo
        transacoes_cronologicas = Transacao.objects.filter(usuario=usuario).order_by('data', 'id')
        
        # Meu saldo no gráfico começa com a minha renda fixa menos as despesas fixas
        saldo_corrente = renda_fixa - total_despesas_fixas 
        
        grafico_dados = []
        for t in transacoes_cronologicas:
            is_receita = any(x in t.tipo.lower() for x in ['receita', 'entrada'])
            saldo_corrente += float(t.valor) if is_receita else -float(t.valor)
            dia = t.data.strftime('%d/%m') if t.data else '?'
            if grafico_dados and grafico_dados[-1]['dia'] == dia:
                grafico_dados[-1]['saldo'] = saldo_corrente
            else:
                grafico_dados.append({'dia': dia, 'saldo': saldo_corrente})

        # Pego minhas últimas 5 transações
        ultimas = Transacao.objects.filter(usuario=usuario).order_by('-data', '-id')[:5]
        lista_ultimas = [{'descricao': u.descricao, 'valor': float(u.valor), 'is_receita': any(x in u.tipo.lower() for x in ['receita', 'entrada']), 'data': u.data.strftime('%d/%m')} for u in ultimas]

        categorias = Categoria.objects.all().values('id', 'nome')

        return Response({
            'saldo_atual': saldo_real,
            'total_receitas': total_receitas_geral,
            'total_despesas': total_despesas_geral,
            'grafico_pizza': pizza_dados,
            'grafico_linha': grafico_dados,
            'ultimas_transacoes': lista_ultimas,
            'categorias': list(categorias)
        })

    def post(self, request):
        usuario = request.user
        dados = request.data
        
        # Busco a categoria que selecionei
        categoria = Categoria.objects.get(id=dados['categoria_id'])
        
        # Salvo minha nova transação manual
        Transacao.objects.create(
            usuario=usuario,
            descricao=dados['descricao'],
            valor=dados['valor'],
            tipo=dados['tipo'],
            categoria=categoria,
            data=timezone.now() 
        )
        return Response({'status': 'sucesso'})
    

# Defino a rota para ler e atualizar minha renda
@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def perfil_usuario(request):
    # Busco ou crio meu perfil zerado se for meu primeiro acesso
    perfil, created = Perfil.objects.get_or_create(usuario=request.user)

    if request.method == 'GET':
        serializer = PerfilSerializer(perfil)
        return Response(serializer.data)
    
    elif request.method == 'PUT': 
        serializer = PerfilSerializer(perfil, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

# Defino o CRUD das minhas contas
class DespesaFixaViewSet(viewsets.ModelViewSet):
    serializer_class = DespesaFixaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtro para ver apenas as minhas contas
        return DespesaFixa.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        # marco a nova despesa com o meu usuário logado
        serializer.save(usuario=self.request.user)