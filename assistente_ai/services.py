import json
import re
import os
from datetime import date
from google import genai
from google.genai import types

from financas.models import Categoria, Transacao 

MODELO_IA = "gemini-2.5-flash"

INSTRUCAO_SISTEMA_MORDOMO = """Você é o 'Mordomo Financeiro', um assistente virtual polido, analítico e direto.
Seu tom deve ser cordial, chamando o usuário de 'Senhor' ou 'Senhora'.

Sua nova habilidade: Identificar se a mensagem do usuário contém um novo GASTO (despesa) ou GANHO (receita) financeiro que deve ser registrado no sistema.

Sua tarefa é analisar a mensagem e retornar EXCLUSIVAMENTE um JSON com a seguinte estrutura:

{
  "intencao": "", // "analise_gasto", "dica_financeira", "duvida_geral", "fora_do_escopo"
  "resposta_mordomo": "", // Sua fala polida e conselhos financeiros.
  "acao_frontend": "", // "atualizar_extrato", "mostrar_graficos", "nenhuma"
  
  // PREENCHA O BLOCO ABAIXO APENAS SE O USUÁRIO DECLARAR UM GASTO OU RECEITA CLARA:
  "dados_transacao": {
    "valor": 0.00, // Apenas o número, usando ponto para decimais (ex: 50.00)
    "descricao": "", // Resumo curto do que foi (ex: "iFood", "Salário", "Monitor 144hz")
    "categoria": "", // Sugira uma categoria (ex: "Alimentação", "Tecnologia", "Salário")
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
    configuracao_gemini = types.GenerateContentConfig(
        system_instruction=[types.Part.from_text(text=INSTRUCAO_SISTEMA_MORDOMO)],
        temperature=0.2, # Temperatura mais baixa para garantir um JSON estrito
    )

    try:
        resposta_ia = cliente_ia.models.generate_content(
            model=MODELO_IA,
            contents=mensagem_usuario,
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
                # Busca a Categoria sugerida pela IA 
                categoria_obj, created = Categoria.objects.get_or_create(
                    usuario=usuario_logado, #Vinculando a Categoria ao dono
                    nome=transacao_info["categoria"].capitalize()
                )

                # Salva a transação oficial no banco de dados
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
                dados_extraidos["resposta_mordomo"] += " No entanto, enfrentei um erro técnico ao tentar registrar este valor no cofre."

        return dados_extraidos

    except Exception as erro_api:
        print(f"Erro de API: {erro_api}")
        return falha_segura_mordomo()