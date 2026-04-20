from django.db import models
from django.conf import settings # Importa as configurações do Usuário

class Categoria(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('usuario', 'nome')
        verbose_name_plural = "Categorias"

    def __str__(self):
        return f"{self.nome} ({self.usuario.username})"

class Transacao(models.Model):
    # A lista precisa existir DENTRO da classe, antes de ser usada nos campos
    TIPO_CHOICES = [
        ('RE_ENTRADA', 'Entrada / Receita'),
        ('SA_SAIDA', 'Saída / Despesa'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    
    # Aqui ele finalmente usa a lista criada ali em cima:
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='transacoes'
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor}"