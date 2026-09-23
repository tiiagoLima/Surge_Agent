# Surge — Personal Automation Hub

> Plataforma pessoal de automações em Python.
> MVP: `investment_scanner` — monitora B3/global, detecta quedas >= 5% e notifica por e-mail/Telegram.
> Arquitetura: Hexagonal (Ports & Adapters) + DDD tático.

## Quickstart (venv)

```powershell
# 1. Criar venv com Python 3.13
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar
pip install -e ".[dev]"

# 3. Configurar
Copy-Item .env.example .env
# edite .env: SURGE_WATCHLIST=PETR4.SA,VALE3.SA,AAPL

# 4. Rodar scan único
python -m surge.main --once

# 5. Rodar com scheduler (todo dia útil 18h)
python -m surge.main
# ou via entrypoint:
surge --once
surge
```

## Docker

```powershell
Copy-Item .env.example .env
docker compose -f docker/docker-compose.yml up --build
# Scan único:
docker compose -f docker/docker-compose.yml run --rm surge surge --once
```

## Configuração

| Var | Default | Descrição |
|-----|---------|-----------|
| `SURGE_WATCHLIST` | `""` | CSV de tickers (`PETR4.SA,VALE3.SA,AAPL`) |
| `SURGE_DROP_THRESHOLD` | `5.0` | Queda % vs fechamento anterior |
| `SURGE_DB_PATH` | `./surge.db` | SQLite |
| `SURGE_TELEGRAM_ENABLED` | `false` | Ativa Telegram |
| `SURGE_EMAIL_ENABLED` | `false` | Ativa e-mail SMTP |

## Arquitetura

```
src/surge/
  domain/        → models.py, ports.py (sem deps externas)
  application/   → investment_scanner/use_case.py (só ports)
  adapters/      → yfinance, brapi, email, telegram, sqlite, scheduler
  config.py      → pydantic-settings
  main.py        → composition root
agents/skills/   → instruções para IAs gerarem nova automação
```

Nova automação? Leia `agents/skills/new-automation.md`.

## Testes

```powershell
pytest tests/unit -v
pytest tests/integration -v  # requer rede
ruff check .
black --check .
```

## CI

`ci.yml` roda lint + testes unitários + `docker build` em PR para `main`.

## Roadmap

- [ ] Contas a pagar
- [ ] Faculdade (alertas de tarefas/provas)
- [ ] Agentes de IA (Surge personificado)
