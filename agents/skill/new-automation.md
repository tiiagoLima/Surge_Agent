# Como Criar uma Nova Automação — Surge

> Siga este passo a passo para adicionar um caso de uso sem quebrar Hexagonal/DDD. Leia `docs/spec.md` antes.

## 1. Modelar o domínio

Crie/edite `src/domain/models.py`:
- Entidades como `@dataclass(frozen=True)`
- Value objects imutáveis
- Métodos ricos (ex: `is_significant_drop()` em `Quote`) — não apenas dados

Se o novo módulo tem conceito conflitante (ex: "Ticker" diferente), avalie bounded context, mas por ora mantenha no mesmo `domain/`.

## 2. Definir portas

Edite `src/domain/ports.py`:
```python
class MyPort(ABC):
    @abstractmethod
    def do_something(self, ...) -> ...: ...
```
Portas são interfaces abstratas. Nunca importe adapter aqui.

## 3. Criar o UseCase

Crie `src/application/<meu_modulo>/use_case.py`:
```python
from src.domain.ports import MyPort

class MyUseCase:
    def __init__(self, port: MyPort) -> None:
        self._port = port

    def execute(self) -> ...:
        # só lógica de negócio, sem I/O concreto
        ...
```
- Injeção via `__init__` — nunca instanciar adapter dentro do UseCase
- Type hints obrigatórios, docstring Google style

## 4. Implementar adapters

Crie em `src/adapters/outbound/` (ou `inbound/` para gatilhos):
```python
from src.domain.ports import MyPort

class MyAdapter(MyPort):
    def do_something(self, ...) -> ...:
        # traduz formato externo <-> modelo de domínio
        ...
```
- Um adapter só traduz. Se começar a decidir regra de negócio, mova para `application/`

## 5. Registrar no composition root

Edite `src/main.py`:
- Instancie adapters concretos
- Injete nos UseCases
- Adicione trigger (scheduler, webhook, email) em `adapters/inbound/`

## 6. Testes

- `tests/unit/test_<meu_modulo>.py` — UseCase com fakes das portas
- `tests/integration/test_<meu_adapter>.py` — adapter real (se precisar de I/O)

## 7. Config

Se precisar de env vars, adicione em `src/config.py` (`Settings`) e documente em `.env.example`.

## Checklist

- [ ] Models imutáveis?
- [ ] Porta com sufixo `Port`?
- [ ] UseCase sem importar adapter?
- [ ] Adapter sem regra de negócio?
- [ ] Injetado em `main.py`?
- [ ] Testes unit com fakes?
- [ ] `.env.example` atualizado?
