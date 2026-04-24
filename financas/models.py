from django.db import models
from django.conf import settings 
from django.contrib.auth.models import User

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
    
    TIPO_CHOICES = [
        ('RE_ENTRADA', 'Entrada / Receita'),
        ('SA_SAIDA', 'Saída / Despesa'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    
    
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
    
   
class Perfil(models.Model):
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    renda_mensal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

class DespesaFixa(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2) 

    parcelas_totais = models.IntegerField(null=True, blank=True, help_text="Deixe em branco se for uma conta contínua (ex: Internet)")
    parcelas_pagas = models.IntegerField(default=0, null=True, blank=True)

    @property
    def percentual_pago(self):
       
        if self.parcelas_totais and self.parcelas_totais > 0:
            return round((self.parcelas_pagas / self.parcelas_totais) * 100, 1)
        return 0

    def __str__(self):
        return self.descricao