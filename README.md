# Mordomo Financeiro — Backend

API REST do **Mordomo Financeiro**, um app de finanças pessoais com assistente de IA. Backend em Django + DRF; chat conversacional via Gemini que interpreta mensagens do usuário e registra transações automaticamente no banco.

Frontend irmão (React + Vite) vive em `../frontend-mordomo/`.

## Stack

- Python 3 + Django 6.0.4
- Django REST Framework 3.17 + SimpleJWT 5.5 (autenticação por JWT)
- django-cors-headers 4.9
- google-genai 1.73 (Gemini 2.5 Flash)
- python-dotenv 1.2
- SQLite (default em dev)

## Setup local

```powershell
# 1. Clonar e entrar
git clone <repo>
cd backend-mordomo

# 2. Criar venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis (ver seção abaixo)
# Criar arquivo .env na raiz

# 5. Aplicar migrations
python manage.py migrate

# 6. Criar superuser (opcional, para acessar /admin)
python manage.py createsuperuser

# 7. Subir o servidor
python manage.py runserver
```

API fica em `http://127.0.0.1:8000`.

## Variáveis de ambiente (`.env`)

Arquivo `.env` na raiz do projeto (já ignorado pelo `.gitignore`):

```env
SECRET_KEY=<gere uma chave com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`>
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
GEMINI_API_KEY=<sua chave do Google AI Studio>
```

Em produção: `DEBUG=False` e `ALLOWED_HOSTS` com o domínio real.

## Endpoints

Todos sob `/api/`. Auth via header `Authorization: Bearer <access_token>` (exceto login/refresh).

| Método | Rota | Função |
|---|---|---|
| `POST` | `/api/token/` | Login — retorna `{access, refresh}` |
| `POST` | `/api/token/refresh/` | Renova `access` a partir de `refresh` |
| `GET` `PUT` | `/api/perfil/` | Lê/atualiza renda mensal do usuário |
| `GET` `POST` | `/api/dashboard/` | GET: saldo, gráficos, últimas 5 transações. POST: cria transação manual |
| `GET` `POST` `PUT` `DELETE` | `/api/despesas-fixas/` | CRUD de despesas fixas (com parcelas) |
| `POST` | `/api/chat/` | Conversa com o Mordomo (Gemini) |

JWT default: `access` vive 7 dias, `refresh` 14 dias (configurável em `core/settings.py`).

## Estrutura

```
backend-mordomo/
├── core/             # Projeto Django — settings, urls centralizadas, wsgi
├── financas/         # Domínio financeiro
│   ├── models.py     # Categoria, Transacao, Perfil, DespesaFixa
│   ├── views.py      # DashboardView, perfil_usuario, DespesaFixaViewSet
│   ├── serializers.py
│   └── migrations/
├── assistente_ai/    # Chat com Gemini
│   ├── services.py   # Monta prompt com "relatório do cofre" e cria transações automáticas
│   └── views.py      # ChatMordomoView
├── manage.py
├── db.sqlite3        # Não versionado
└── .env              # Não versionado
```

## Como o Mordomo funciona

O usuário manda uma mensagem em linguagem natural (ex.: *"gastei 50 reais no almoço"*). O service `assistente_ai.services.processar_mensagem_usuario`:

1. Monta um "RELATÓRIO INTERNO DO COFRE" com renda + despesas fixas do usuário
2. Injeta esse contexto + a mensagem num prompt para o Gemini
3. Espera de volta um JSON com `resposta_mordomo`, `intencao`, e opcionalmente `dados_transacao`
4. Se vier `dados_transacao`, cria a `Categoria` (se não existir) e a `Transacao` automaticamente

## Frontend

O cliente React/Vite está em `../frontend-mordomo/` e consome esta API em `http://127.0.0.1:8000`. CORS atualmente libera apenas `localhost:5173` e `127.0.0.1:5173` (Vite default).
