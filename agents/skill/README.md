# Agents Skills — Surge

Esta pasta ensina ferramentas de IA (OpenCode, Claude Code) a trabalhar neste repositório seguindo o spec.

## Arquivos

- `code-conventions.md` — naming, type hints, docstrings, estilo
- `new-automation.md` — passo a passo para criar um novo caso de uso
- `testing-guidelines.md` — como gerar testes

## Uso

Antes de gerar código, o agente deve ler `docs/spec.md` e os três arquivos acima.
Qualquer nova automação deve seguir Hexagonal + DDD tático e depender apenas de ports.
