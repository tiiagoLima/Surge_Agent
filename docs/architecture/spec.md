# Spec — Personal Automation Hub (Surge)

> Documento de referência para desenvolvimento orientado a spec (spec-driven development).
> Este arquivo é a fonte de verdade para ferramentas de IA (OpenCode, Claude Code) gerarem a
> base do repositório. Alterações de arquitetura devem ser refletidas aqui antes de virar código.

## 1. Objetivo

O objetivo não é resolver um problema único, mas ter uma **base extensível** onde novas
automações pessoais possam ser adicionadas ao longo do tempo sem reescrever o núcleo.

Agente personificado: **Surge**.

**Módulo inicial (MVP):** `investment_scanner` — monitora ativos da B3 e do mercado global,
identifica quedas relevantes e notifica por e-mail e Telegram.

**Módulos previstos (não implementados agora, mas que a arquitetura deve suportar sem refatoração
estrutural):** contas a pagar, automações relacionadas à faculdade.

**Objetivos secundários:** peça de portfólio; exercício deliberado de POO, Clean Architecture e DDD tático.

## 2. Decisões de Arquitetura

### ADR-0001 — Hexagonal (Ports & Adapters)
Domínio não depende de detalhe técnico. Toda comunicação externa passa por portas.

### ADR-0002 — DDD tático dentro da camada de domínio
Entidades como `Quote`, `Opportunity` são objetos ricos, imutáveis.

### ADR-0003 — Python 3.13 com ambiente virtual isolado
`venv` + `pyproject.toml` (PEP 621). Python 3.13 escolhido por ecossistema maduro (vs 3.14 free-threading ainda em adoção).

### ADR-0004 — Docker para deploy
Imagem Docker é artefato de deploy. `docker-compose.yml` espelha produção. Agendamento dentro do container (APScheduler).

### ADR-0005 — CI cobre lint, testes e build de imagem

### ADR-0006 — Pasta `agents/skills` como instruções para ferramentas de IA

## 3. Estrutura de Pastas (atualizada: pacote `surge`)

```
surge-agent/
├── docs/
│   └── architecture/
│       └── spec.md
├── agents/
│   └── skills/
│       ├── README.md
│       ├── code-conventions.md
│       ├── new-automation.md
│       └── testing-guidelines.md
├── src/
│   └── surge/
│       ├── domain/
│       │   ├── models.py
│       │   └── ports.py
│       ├── application/
│       │   └── investment_scanner/
│       │       └── use_case.py
│       ├── adapters/
│       │   ├── inbound/
│       │   │   └── scheduler_trigger.py
│       │   └── outbound/
│       │       ├── yfinance_adapter.py
│       │       ├── brapi_adapter.py
│       │       ├── email_notifier.py
│       │       ├── telegram_notifier.py
│       │       └── sqlite_repository.py
│       ├── config.py
│       └── main.py
├── tests/
│   ├── unit/
│   └── integration/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .github/workflows/ci.yml
├── .env.example
├── pyproject.toml
└── README.md
```

Pacote importável: `surge` (não `automation_hub`).

## 4. Convenções de Código

- Type hints obrigatórios
- Docstrings Google style
- Imutabilidade (`@dataclass(frozen=True)`)
- `PascalCase` classes, `snake_case` funções, sufixo `Port` em portas
- `ruff` + `black`
- Sem lógica de negócio em adapters

## 5. Estratégia de Testes

- `tests/unit/`: domain + application com fakes
- `tests/integration/`: adapters reais

## 6. Investment Scanner — Parâmetros MVP

- Threshold: queda de 5% vs fechamento anterior (configurável via `SURGE_DROP_THRESHOLD`)
- Watchlist: vazia por padrão, configurável via `SURGE_WATCHLIST` (CSV) ou `watchlist.yaml` futuro
- Fonte primária: yfinance; fallback: brapi.dev

## 7. Docker

Multi-stage build, compose com .env, scheduler interno.

## 8. CI

Lint + testes unitários obrigatórios + build Docker.

## 9. Critérios de Aceite — Fase 1 (Bootstrap)

- [ ] Estrutura com `src/surge/`
- [ ] `domain/ports.py` e `domain/models.py`
- [ ] `investment_scanner/use_case.py` com DI
- [ ] Adapters outbound funcionais
- [ ] `main.py` composition root
- [ ] `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `ci.yml`
- [ ] `agents/skills/new-automation.md` antes dos adapters
- [ ] README com setup venv
