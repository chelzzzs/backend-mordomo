import json
import re
import os
from datetime import date
from google import genai
from google.genai import types

# Importei o Perfil e DespesaFixa do banco de dados
from financas.models import Categoria, Transacao, Perfil, DespesaFixa 

MODELO_IA = "gemini-2.5-flash"

INSTRUCAO_SISTEMA_MORDOMO = """Você é o 'Mordomo Financeiro', um assistente virtual polido, analítico e direto.
Seu tom deve ser cordial, chamando o usuário de 'Senhor' ou 'Senhora'.

Você receberá um "[RELATÓRIO INTERNO DO COFRE]" com a situação financeira atual do usuário junto com a mensagem dele. 
USE ESSES DADOS (Renda e Despesas Fixas) para dar conselhos cirúrgicos e matemáticos. Se o usuário perguntar se pode comprar algo, ou pedir dicas de economia, faça as contas reais considerando o Saldo Livre dele.

Sua tarefa é analisar a mensagem e retornar EXCLUSIVAMENTE um JSON com a seguinte estrutura:

{
  "intencao": "", // "analise_gasto", "dica_financeira", "duvida_geral", "fora_do_escopo"
  "resposta_mordomo": "", // Sua fala polida e conselhos baseados na matemática do relatório.
  "acao_frontend": "", // "atualizar_extrato", "mostrar_graficos", "nenhuma"
  
  // PREENCHA O BLOCO ABAIXO APENAS SE O USUÁRIO DECLARAR UM NOVO GASTO OU RECEITA CLARA:
  "dados_transacao": {
    "valor": 0.00, // Apenas o número, usando ponto para decimais (ex: 50.00)
    "descricao": "", // Resumo curto do que foi
    "categoria": "", // Sugira uma categoria
    "tipo": "" // Use EXATAMENTE "SA_SAIDA" para gastos ou "RE_ENTRADA" para ganhos
  } 
}
""".strip()

def extrair_json_resposta(texto_bruto: str) -> dict | None:
    match_json = re.search(r"\{.*\}", texto_bruto or "", re.DOTALL)
    if not match_json:
        return None
    try:
        return json.loads(match_json.group(0))
    except json.JSONDecodeError:
        return None

def falha_segura_mordomo() -> dict:
    return {
        "intencao": "fora_do_escopo",
        "acao_frontend": "nenhuma",
        "resposta_mordomo": "Peço perdão, mas meus sistemas de cálculo e registro estão temporariamente indisponíveis.",
        "transacao_salva": False
    }

def processar_mensagem_usuario(cliente_ia: genai.Client, mensagem_usuario: str, usuario_logado) -> dict:
    
    # 1. Busca os dados reais do usuário no banco
    perfil, _ = Perfil.objects.get_or_create(usuario=usuario_logado)
    renda_mensal = float(perfil.renda_mensal) if perfil.renda_mensal else 0.0

    despesas_fixas = DespesaFixa.objects.filter(usuario=usuario_logado)
    texto_despesas = ""
    total_despesas_fixas = 0.0

    for d in despesas_fixas:
        texto_despesas += f"- {d.descricao}: R$ {float(d.valor):.2f}\n"
        total_despesas_fixas += float(d.valor)

    saldo_livre = renda_mensal - total_despesas_fixas

    # 2. Monta o relatório oculto que vai junto com a pergunta do usuário
    mensagem_com_contexto = f"""
[RELATÓRIO INTERNO DO COFRE - USE PARA CONTEXTO NAS RESPOSTAS]
Renda Mensal do Usuário: R$ {renda_mensal:.2f}
Soma das Despesas Fixas: R$ {total_despesas_fixas:.2f}
Saldo Livre Estimado: R$ {saldo_livre:.2f}

Lista de Contas Cadastradas:
{texto_despesas if texto_despesas else "Nenhuma conta fixa cadastrada."}
---------------------------------------------------------
[MENSAGEM DO USUÁRIO]
{mensagem_usuario}
    """

    configuracao_gemini = types.GenerateContentConfig(
        system_instruction=[types.Part.from_text(text=INSTRUCAO_SISTEMA_MORDOMO)],
        temperature=0.2, 
    )

    try:
        # 3. Envia a mensagem modificada (Contexto + Pergunta) para a IA
        resposta_ia = cliente_ia.models.generate_content(
            model=MODELO_IA,
            contents=mensagem_com_contexto,
            config=configuracao_gemini,
        )

        dados_extraidos = extrair_json_resposta(resposta_ia.text)
        if not dados_extraidos:
            return falha_segura_mordomo()

        # Verifica se a IA identificou dados para salvar no banco
        transacao_info = dados_extraidos.get("dados_transacao")
        dados_extraidos["transacao_salva"] = False 

        if transacao_info and transacao_info.get("valor"):
            try:
                # Busca ou cria a Categoria
                categoria_obj, created = Categoria.objects.get_or_create(
                    usuario=usuario_logado,
                    nome=transacao_info["categoria"].capitalize()
                )

                # Salva a transação oficial
                Transacao.objects.create(
                    usuario=usuario_logado, 
                    descricao=transacao_info["descricao"],
                    valor=float(transacao_info["valor"]),
                    data=date.today(),
                    tipo=transacao_info["tipo"],
                    categoria=categoria_obj
                )
                
                dados_extraidos["transacao_salva"] = True 
                dados_extraidos["acao_frontend"] = "atualizar_extrato"
                
            except Exception as erro_banco:
                print(f"Erro ao salvar no banco: {erro_banco}")
                dados_extraidos["resposta_mordomo"] += " No entanto, enfrentei um erro técnico ao tentar registrar este valor."

        return dados_extraidos

    except Exception as erro_api:
        print(f"Erro de API: {erro_api}")
        return falha_segura_mordomo()