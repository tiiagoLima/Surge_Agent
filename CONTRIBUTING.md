# Contributing — Surge

## Workflow
1. Leia `docs/architecture/spec.md` e `agents/skills/*`.
2. Crie branch a partir de `main`.
3. Siga Hexagonal: domain não depende de adapters.
4. Type hints + docstrings Google style.
5. `ruff check` e `black` antes de commit.
6. Testes em `tests/unit` com fakes.

## Commits
Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`.

## PR
Descreva o que mudou e por que. CI deve passar (lint + testes + docker build).
