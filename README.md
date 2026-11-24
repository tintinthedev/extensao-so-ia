# Monitor do sistema

Dashboard local que exibe, a cada 2 segundos, o uso de CPU e RAM, as taxas de
leitura e escrita de disco e os processos em execução da máquina.

- **Front-end:** Streamlit, com um único `st.fragment(run_every=2.0)`.
- **Back-end:** pacote Python que coleta as métricas com `psutil`.
- **Histórico:** janela deslizante de 10 amostras (20 segundos) em memória.

## Requisitos

- Python 3.12+
- `python3-venv` (para criar o ambiente virtual)

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Se `ensurepip` não estiver disponível no sistema (Debian/Ubuntu sem
`python3-venv`), crie o ambiente sem pip e instale-o dentro dele:

```bash
python3 -m venv --without-pip .venv
curl -fsSL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python
.venv/bin/pip install -r requirements.txt
```

## Execução

```bash
.venv/bin/streamlit run app.py
```

A interface abre em `http://localhost:8501`.

## Skills do Streamlit

As skills oficiais para agentes de IA ficam em `.agents/skills/` (symlinks
para o pacote instalado no venv). Para reinstalá-las:

```bash
.venv/bin/streamlit skills --yes
```

Elas são específicas do ambiente e estão no `.gitignore`.

## Estrutura

```
app.py                  # entrada Streamlit; fragment de atualização
backend/collector.py    # coleta psutil + estado entre amostras
frontend/dashboard.py   # orquestra uma renderização completa
frontend/history.py     # janela deslizante em memória
frontend/charts.py      # quatro gráficos de histórico
frontend/processes.py   # top 5 + dialog com a lista completa
.streamlit/config.toml  # tema nativo (dense-dashboard)
```

As decisões arquiteturais estão em [AGENTS.md](AGENTS.md).
