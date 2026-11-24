# AGENTS.md

## Visão geral

Aplicação local de monitoramento do sistema em "tempo real" (janela de 2 s).
Um único processo Streamlit serve a interface e coleta as métricas da própria
máquina com `psutil`.

- **Back-end** (`backend/`): coleta CPU, RAM, taxas de leitura/escrita de disco
  e a lista de processos.
- **Front-end** (`frontend/` + `app.py`): exibe cards com os valores atuais,
  quatro gráficos de histórico e a tabela de processos.

## Estrutura

```
app.py                  # entrada Streamlit; declara o fragment de atualização
backend/collector.py    # coleta psutil + estado entre amostras
frontend/dashboard.py   # orquestra uma renderização completa
frontend/controls.py    # barra lateral: iniciar/pausar e limpar histórico
frontend/history.py     # janela dos gráficos + registro completo em memória
frontend/charts.py      # quatro gráficos de histórico
frontend/measurements.py # tabela do histórico completo + download em CSV
frontend/processes.py   # top 5 + dialog com a lista completa
.streamlit/config.toml  # tema nativo (dense-dashboard)
```

## Decisões arquiteturais

### 1. Back-end como pacote Python, não como serviço HTTP

O front-end importa `backend.collector` diretamente; não há API, porta extra ou
serialização JSON. Como o Streamlit executa no mesmo host que está sendo
monitorado, uma chamada de rede só adicionaria latência e um segundo processo
para gerenciar. A separação front/back é mantida por camadas de código, não por
transporte.

### 2. psutil como única fonte de dados

Todas as métricas vêm de `psutil`, sem subprocessos (`top`, `iostat`) nem
leitura manual de `/proc`. Isso mantém a coleta portátil e sem parsing de texto.

### 3. Coletor único, com lock e throttle

`get_collector()` devolve uma instância única por processo. A coleta é
serializada por `threading.Lock`, pois o estado anterior (contadores de disco)
é compartilhado. Amostras separadas por menos de 1 s retornam o último resultado
em cache, evitando intervalos degenerados quando várias sessões ou interações
disparam coletas fora do ciclo de 2 s.

### 4. Coleta não bloqueante baseada em deltas

- CPU do sistema: `psutil.cpu_percent(interval=None)` com _priming_ na criação
  do coletor; cada chamada calcula a média desde a anterior.
- Disco: `psutil.disk_io_counters()` é cumulativo; a taxa é
  `(bytes_atuais - bytes_anteriores) / tempo_decorrido`, medido com
  `time.monotonic()` para não sofrer com ajustes de relógio. A primeira amostra
  reporta 0 MB/s.
- Processos: `psutil.process_iter(...)` com `cpu_percent` não bloqueante. O
  cache interno do psutil entrega o delta desde a amostra anterior.

### 5. CPU por processo normalizada pela capacidade total

`Process.cpu_percent()` do psutil pode passar de 100% (uma thread por núcleo).
O valor exibido é dividido pelo número de CPUs lógicas e limitado a 100%, para
ficar na mesma escala do gráfico de CPU do sistema. O ranking usa CPU
decrescente, com RAM como critério de desempate.

### 6. Histórico em memória: janela dos gráficos + registro completo

O histórico vive em `st.session_state` como `deque(maxlen=10)` (20 segundos a
2 s por amostra) para os gráficos, e a mesma amostra também é anexada a uma
lista sem limite com tudo o que foi coletado na sessão. Cada nova amostra
empurra a mais antiga para fora da janela, mas permanece no registro completo,
que alimenta a tabela e o CSV. Se o `HISTORY_SIZE` mudar em tempo de execução,
`get_history()` recria o deque para não manter um `maxlen` antigo. "Limpar
histórico" esvazia os dois e zera a última amostra, mantendo o timestamp para
que o cache do coletor não reintroduza uma amostra repetida. Não há persistência
em disco: reiniciar a aplicação zera tudo. Amostras repetidas (mesmo timestamp
do cache) são descartadas.

### 7. Um único `st.fragment(run_every=2.0)` como laço de atualização

Todo o painel — cards, quatro gráficos, histórico e tabela de processos — é
renderizado dentro do mesmo fragment. Assim, todos os componentes leem a mesma
amostra e são atualizados junto, sem `st_autorefresh` nem recarregar a página
inteira. O título fica fora do fragment. O `run_every` é `None` quando o
monitoramento está pausado: o fragment para de disparar e nenhuma amostra é
coletada; a última amostra continua na tela.

### 8. Gráficos com Altair e tooltips customizados

Quatro séries temporais em grade 2×2 (CPU, RAM, leitura e escrita) via
`st.altair_chart`. Altair já vem com o Streamlit e permite controlar o tooltip:
o horário aparece como `HH:MM:SS` em vez da data completa, e as taxas de disco
usam `.3~f` (até 3 casas, sem zeros à direita). CPU e RAM usam uma casa
decimal. A camada de pontos invisíveis (`mark_point`, `opacity=0`) mantém a
área de hover sobre a linha. As cores vêm da paleta do tema, não são fixadas
por gráfico.

O eixo X usa `axis.values` com o timestamp de cada amostra, em vez de uma grade
fixa (`tickCount`), para acompanhar a coleta de 2 s. `tickCount` com
`TimeIntervalStep` quebra no Vega do navegador (`Cannot read properties of
undefined (reading 'every')`). Com 10 amostras em ~375 px, os rótulos de
`HH:MM:SS` ficam na horizontal e o `labelOverlap="greedy"` ainda oculta metade
deles — na prática aparecem marcas a cada 4 s.

### 9. Lista de processos: top 5 + dialog fora do fragment

A tabela principal mostra os 5 maiores consumidores de CPU. O botão grava um
snapshot em `st.session_state`, pede um rerun completo do app e o dialog é
renderizado pelo script principal, depois do fragment. Ele fica fora do ciclo
de 2 s de propósito: se fosse recriado a cada atualização, o scroll da lista
completa voltaria ao topo. O dialog mostra a lista inteira (já ordenada) em um
`st.dataframe` de altura fixa, que rola internamente, e é fechado pelo
`on_dismiss`, que limpa o flag.

### 10. Tema nativo em `.streamlit/config.toml`

O visual usa o tema `dense-dashboard` (modo claro/escuro, tipografia, raios e
paleta de gráficos) copiado das skills oficiais. Não há CSS customizado:
aparência é responsabilidade do tema, não do código dos componentes.

### 11. Skills oficiais do Streamlit no venv

`.venv/bin/streamlit skills --yes` instala as skills em `.agents/skills/` e
`.claude/skills/` como symlinks para o pacote do venv. Elas acompanham a versão
instalada, não são versionadas (entram no `.gitignore`) e foram usadas como
referência de API e de boas práticas (por exemplo, `width="stretch"` em vez de
`use_container_width`, e `alt=` em gráficos e tabelas).

### 12. Ambiente virtual local e dependências fixadas

As dependências são instaladas em `.venv/` na raiz do projeto, nunca no Python
do sistema. `requirements.txt` é a fonte da verdade.

### 13. Controles de monitoramento na barra lateral

`frontend/controls.py` concentra o botão "Pausar"/"Iniciar monitoramento" e o
"Limpar histórico". O estado fica em `st.session_state["monitorando"]` (inicia
ligado, preservando o comportamento anterior) e os cliques usam `on_click`,
para que o callback rode antes do script e o rótulo do botão já apareça correto
no mesmo rerun. Os controles são renderizados antes da definição do fragment,
para que `run_every` seja avaliado com o estado atualizado.

### 14. Tabela do histórico completo e CSV

`frontend/measurements.py` mostra todas as amostras da sessão, da mais recente
para a mais antiga, em um `st.dataframe` de altura fixa (o scroll interno é
preservado entre reruns do fragment). O cabeçalho resume quantidade de amostras
e média/pico de CPU e RAM. O CSV baixa o registro completo em ordem cronológica,
com data e hora, e as mesmas colunas: CPU, RAM, RAM usada, leitura, escrita e
número de processos. As colunas usam `NumberColumn` para formatar casas
decimais; a largura "small" evita que a última coluna seja cortada.

## Fluxo de uma atualização

1. O fragment dispara a cada 2 s (ou fica parado, se pausado).
2. `render_dashboard()` pede uma amostra ao coletor (ou recebe a última, se
   tiver menos de 1 s) e a anexa à janela dos gráficos e ao registro completo.
   Quando pausado, reaproveita `last_metrics` sem coletar nada.
3. Cards, gráficos, histórico e tabela de processos são renderizados com essa
   mesma amostra.
4. O botão "Ver todos" guarda um snapshot, força um rerun completo e o script
   principal abre o dialog com esse snapshot.
