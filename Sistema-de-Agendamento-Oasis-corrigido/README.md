# Sistema de Agendamento - Chácara Oasis

Backend em FastAPI para reservas da Chácara Oasis.

## Fluxo principal

1. O cliente envia uma solicitação pelo site.
2. A API valida as datas.
3. A reserva é salva no banco.
4. Depois do `commit`, uma tarefa em background envia o resumo para o Gmail do ADM.
5. A API retorna os dados da reserva.

## Instalação

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Instale:

```bash
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e preencha as variáveis.

Inicie:

```bash
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Gmail

Use uma App Password do Google. Nunca coloque a senha real da conta ou a App Password no GitHub.
