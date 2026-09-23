# Code Conventions — Surge

## Nomenclatura
- Classes: `PascalCase`
- Funções/variáveis: `snake_case`
- Ports: sufixo `Port` (`NotificationPort`, `QuotePort`, `StoragePort`)
- Adapters: sufixo do que implementam (`TelegramNotifier`, `SqliteRepository`, `YFinanceAdapter`)

## Type hints
Obrigatórios em toda função/método público. Use `from __future__ import annotations`.

## Docstrings
Google style para classes e funções não triviais.

## Imutabilidade
Entidades de domínio com `@dataclass(frozen=True)` por padrão.

## Hexagonal
- `domain/` não importa nada de `adapters/` ou `application/`
- `application/` depende apenas de `domain/ports.py` e `domain/models.py`
- Adapters só traduzem formato externo <-> modelo de domínio. Sem regra de negócio em adapter.

## Lint/Format
- `ruff check` (inclui isort)
- `black --check`
- Config em `pyproject.toml`. Rodar antes de commit.

## Imports
`ruff` organiza. Primeiro party: `src`.

## Erros
Adapters não devem vazar exceções de libs externas para o domínio. Traduzir para `None` ou logar e continuar.
