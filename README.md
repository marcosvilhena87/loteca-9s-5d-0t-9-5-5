# Loteca 9S-5D-0T — Estratégia 9-5-5

Projeto para geração de **um único palpite final por concurso da Loteca**, usando o histórico de `data/concursos_anteriores.csv` e as informações do próximo concurso para maximizar prioritariamente:

```text
P(acertos >= 13)
```

O projeto deve respeitar integralmente as Hard Constraints e usar as Soft Constraints apenas como preferências subordinadas ao objetivo principal.

---

## Estratégia

1. Gerar um único palpite final por concurso, otimizado para maximizar a probabilidade de atingir pelo menos 13 acertos.
2. Representar as probabilidades dos três resultados possíveis como:
   - `p(1)`: vitória do mandante;
   - `p(X)`: empate;
   - `p(2)`: vitória do visitante.
3. Derivar `p(top1)`, `p(top2)` e `p(top3)` ordenando `p(1)`, `p(X)` e `p(2)` da maior para a menor.
4. Em caso de empate, usar obrigatoriamente:

```text
1 > 2 > X
```

5. Representar o resultado real por One-Hot Encoding:

```text
top1_hit
top2_hit
top3_hit
```

Em cada partida, exatamente uma dessas variáveis deve ser igual a `1`.

6. Exibir telemetria suficiente para auditar probabilidades, ranking, secos, duplos, restrições, cutoff, robustez, consenso entre seletores e critérios da aposta final.

---

## Hard Constraints

A aposta final só é válida se satisfizer simultaneamente:

```text
9 secos
5 duplos
0 triplos

9 Top1
5 Top2
5 Top3
```

Como existem 9 secos e 5 duplos:

```text
9 x 1 + 5 x 2 = 19 marcações
```

Logo:

```text
9 Top1 + 5 Top2 + 5 Top3 = 19 marcações
```

A contagem refere-se às marcações efetivamente presentes no volante, e não ao número de partidas.

### Flamengo

Quando o **FLAMENGO/RJ** participar do concurso, o resultado correspondente à sua vitória deve obrigatoriamente estar entre as marcações.

A validação deve ser feita sobre o resultado concreto `1`, `X` ou `2`, independentemente de ele ocupar Top1, Top2 ou Top3.

---

## Soft Constraints

1. Favorecer ordenações que antecipem e concentrem resultados Top1, especialmente nas 9 primeiras posições, privilegiando runs longas e baixa fragmentação.
2. Favorecer soluções que excluam a vitória do **PALMEIRAS/SP**, priorizando empate ou derrota quando isso não comprometer significativamente a qualidade global da aposta.
3. Soft Constraints nunca podem relaxar Hard Constraints.
4. O custo de aplicar uma Soft Constraint deve ser mensurável e exibido quando relevante.

---

## Hipótese estrutural 9-5-5

Uma baseline estrutural importante é:

```text
9 maiores p(top1)  -> seco Top1
5 menores p(top1)  -> duplo Top2+Top3
```

Essa configuração satisfaz automaticamente:

```text
9 secos
5 duplos
9 Top1
5 Top2
5 Top3
```

Para um jogo marcado como `Top2+Top3`:

```text
P(cobertura) = p(top2) + p(top3) = 1 - p(top1)
```

Essa baseline **não é regra obrigatória**. Ela é a referência que qualquer abordagem mais sofisticada deve superar fora da amostra.

### Relação entre os tipos de duplo

Definindo:

```text
D12 = duplos Top1+Top2
D13 = duplos Top1+Top3
D23 = duplos Top2+Top3
```

com:

```text
D12 + D13 + D23 = 5
```

as quantidades de secos necessárias são:

```text
SecoTop1 = 4 + D23
SecoTop2 = D13
SecoTop3 = D12
```

Portanto:

- cada `Top1+Top2` exige um Top3 seco em outra partida;
- cada `Top1+Top3` exige um Top2 seco em outra partida;
- `Top2+Top3` permite manter um Top1 seco adicional.

---

## Histórico vs. próximo concurso

A decisão deve combinar duas fontes complementares.

### Histórico

Em `data/concursos_anteriores.csv`, estudar:

```text
top1_hit
top2_hit
top3_hit
```

incluindo:

- frequência global e recente;
- distribuição por concurso;
- runs e fragmentação de Top1;
- transições Top1/Top2/Top3;
- comportamento por posição;
- comportamento por tipo de ranking;
- calibração histórica dos ranks;
- padrões dos concursos que produziram 13+;
- padrões de falha do Top1.

### Próximo concurso

Para cada partida de `data/proximo_concurso.csv`, produzir:

```text
p(1), p(X), p(2)
p(top1), p(top2), p(top3)
```

As probabilidades podem ser usadas em diferentes níveis de intensidade. O projeto deve testar se a magnitude exata das probabilidades realmente melhora `>=13` em relação a estratégias que utilizam apenas ranking, faixas, estrutura e histórico.

---

# Estratégias com menor dependência das probabilidades

Uma linha prioritária de pesquisa é tornar a decisão dos 5 duplos **menos dependente de pequenas diferenças numéricas** entre probabilidades estimadas.

Exemplo do problema:

```text
p(top1) jogo A = 0.4473
p(top1) jogo B = 0.4571
```

Uma diferença inferior a 1 ponto percentual não deve, por si só, dominar a decisão se outros sinais estruturais e históricos indicarem comportamento diferente.

O objetivo não é eliminar as probabilidades, mas reduzir a dependência de sua magnitude exata quando a evidência é fraca.

## Modos experimentais de seleção

O projeto deve suportar pelo menos três modos comparáveis em walk-forward.

### `PROBABILITY_ONLY`

Usa as probabilidades contínuas completas como principal sinal de decisão.

Baseline natural:

```text
score_duplo = 1 - p(top1)
```

### `RANK_ONLY`

As probabilidades são usadas somente para definir:

```text
Top1
Top2
Top3
```

Depois disso, as magnitudes são descartadas.

A decisão pode usar:

- posição da partida;
- tipo de ranking `1/X/2`;
- frequência histórica de `top1_hit`;
- runs e fragmentação;
- padrões históricos de Top1/Top2/Top3;
- regime estrutural do concurso.

### `HYBRID_ORDINAL`

Modo preferencial de pesquisa.

Usa as probabilidades para formar rankings e classes, mas evita depender diretamente de diferenças pequenas entre valores contínuos.

Pode usar:

```text
rank_pTop1
rank_gap12
rank_gap13
rank_entropy
rank_historical_fail
```

O objetivo é combinar posição relativa, incerteza e histórico.

---

## Ranking estrutural das probabilidades

Além de `p(top1)`, utilizar:

```text
gap12 = p(top1) - p(top2)
gap23 = p(top2) - p(top3)
gap13 = p(top1) - p(top3)
entropy = entropia de p(1), p(X), p(2)
```

Essas variáveis descrevem a **geometria da incerteza**.

Dois jogos com `p(top1)` semelhante podem ter riscos diferentes se um possuir Top1 muito próximo do Top2 e outro apresentar separação maior.

---

## Dependência por faixas, não por valores exatos

Também deve ser testada discretização das probabilidades em classes, por exemplo:

```text
p(top1) < 0.40       -> muito equilibrado
0.40 <= p < 0.47     -> equilibrado
0.47 <= p < 0.55     -> favorito moderado
0.55 <= p < 0.65     -> favorito forte
p(top1) >= 0.65      -> favorito extremo
```

Os limites acima são apenas hipóteses iniciais e devem ser ajustados exclusivamente com dados de treinamento.

A finalidade é fazer com que jogos muito próximos numericamente sejam tratados como pertencentes ao mesmo regime e sejam diferenciados por histórico e estrutura.

---

## Tipos de ranking 1/X/2

Existem seis ordenações possíveis:

```text
1 > X > 2
1 > 2 > X
X > 1 > 2
X > 2 > 1
2 > 1 > X
2 > X > 1
```

Para cada tipo, medir historicamente:

```text
Top1 hit rate
Top2 hit rate
Top3 hit rate
Top1 fail rate
```

Isso permite aprender padrões que dependem da **ordenação dos resultados**, sem depender necessariamente das magnitudes exatas das probabilidades.

---

## Modelo de posição

Como baseline adicional, medir:

```text
P(top1_hit | posição do jogo)
```

para posições 1 a 14.

Essa feature não deve ser assumida como causal, mas pode servir como sinal estrutural ou baseline para verificar se existem efeitos históricos persistentes por posição.

---

## Padrões de sequência e runs

Representar concursos históricos como sequências de ranks reais:

```text
T1 T1 T2 T1 T3 T1 T1 T2 T1 T1 T3 T2 T1 T1
```

Estudar:

```text
quantidade de Top1
quantidade de falhas de Top1
max_run_top1
numero_de_runs_top1
fragmentação
posição da primeira falha
posição da última falha
distância entre falhas
```

O objetivo é verificar se existem estruturas associadas a maior recuperação de 13+ sob as Hard Constraints.

---

## Número esperado de falhas do Top1

Testar uma modelagem em duas etapas:

```text
1. estimar quantas falhas de Top1 esperar no concurso
2. estimar onde essas falhas tendem a ocorrer
```

Isso pode ser mais robusto do que tomar 14 decisões independentes baseadas apenas nas probabilidades individuais.

---

## Consenso entre seletores

Implementar seletores independentes, por exemplo:

```text
A = 5 menores p(top1)
B = 5 menores gap12
C = 5 maiores entropias
D = 5 maiores taxas históricas de Top1_fail
E = seletor ordinal / rank-only
F = meta-modelo
```

Cada jogo recebe votos conforme a quantidade de métodos que o selecionam para duplo.

Exemplo:

```text
Jogo | Prob | Gap12 | Entropia | Histórico | RankOnly | Votos
1    |   X  |   X   |    X     |     X     |    X     | 5
13   |   X  |   X   |    X     |     -     |    X     | 4
...
```

Os pesos de cada seletor, caso utilizados, devem ser definidos exclusivamente em validação walk-forward.

---

## Núcleo robusto e zona cinzenta

A partir do consenso, classificar os jogos em três grupos.

### Núcleo de duplos

Jogos em que múltiplos métodos concordam que o Top1 é vulnerável.

### Zona cinzenta

Jogos próximos ao cutoff ou com forte discordância entre métodos.

Exemplo conceitual:

```text
Núcleo de duplos: J1 J13 J14 J4
Zona cinzenta:    J6 J3 J8
Núcleo de secos:  demais jogos
```

O modelo histórico deve concentrar maior capacidade decisória na zona cinzenta, em vez de tentar substituir sinais muito fortes em todos os 14 jogos.

---

## Historical Pattern Matching

Para cada concurso histórico, guardar a estrutura de ranking das 14 partidas, por exemplo:

```text
1>X>2
2>X>1
1>2>X
...
```

junto com a sequência real:

```text
T1 T2 T1 T3 ...
```

Para o próximo concurso, comparar sua estrutura de rankings com concursos históricos semelhantes e estimar onde o Top1 historicamente falhou.

Esse método deve ser testado tanto:

- sem magnitudes probabilísticas;
- quanto em versão híbrida usando apenas faixas de confiança.

---

## Score ordinal

Testar um score baseado em posições relativas, em vez de magnitudes diretas.

Exemplo conceitual:

```text
ScoreOrdinal =
    w1 * rank_pTop1
  + w2 * rank_gap12
  + w3 * rank_entropy
  + w4 * rank_historical_fail
```

A direção dos ranks deve ser normalizada para que score maior sempre represente maior prioridade para receber duplo.

Os pesos devem ser escolhidos apenas em validação walk-forward.

---

## Agreement@5

Medir a concordância entre seletores.

Exemplo:

```text
Agreement@5(PROBABILITY_ONLY, RANK_ONLY)
= número de jogos em comum entre os dois Top-5 / 5
```

Interpretar:

```text
100% -> seleção praticamente estrutural
80%  -> forte concordância
60%  -> zona relevante de divergência
40% ou menos -> forte dependência do método
```

Os limites são apenas descritivos; não devem ser usados como Hard Constraints.

---

## Rank Preservation Stress Test

Testar a dependência da aposta às magnitudes preservando a ordem Top1/Top2/Top3.

Procedimento:

1. manter o ranking dos três resultados de cada partida;
2. comprimir ou expandir artificialmente as diferenças probabilísticas;
3. renormalizar;
4. rerodar o seletor;
5. medir quantos dos 5 duplos permanecem.

Exemplo:

```text
original:   0.4473 / 0.3098 / 0.2429
comprimido: 0.4000 / 0.3300 / 0.2700
```

Se o ranking permanece igual, mas a seleção dos duplos muda excessivamente, isso indica dependência elevada da magnitude probabilística.

---

## Temperature Stress Test

Como diagnóstico, recalcular probabilidades sob diferentes temperaturas, por exemplo:

```text
T = 0.70
T = 0.90
T = 1.00
T = 1.20
T = 1.50
```

Medir:

```text
Agreement@5 entre temperaturas
Stability@5
mudança no núcleo de duplos
mudança na zona cinzenta
```

O teste é diagnóstico e não deve alterar automaticamente a temperatura implantada.

---

## Métrica de dependência probabilística

Criar uma telemetria agregada para medir quanto o seletor depende das magnitudes contínuas.

Sinais possíveis:

```text
Agreement@5(PROBABILITY_ONLY, RANK_ONLY)
Agreement@5(PROBABILITY_ONLY, HYBRID_ORDINAL)
Stability@5 no Rank Preservation Stress Test
Stability@5 no Temperature Stress Test
```

Uma estratégia menos dependente das probabilidades deve preservar desempenho em `>=13` enquanto apresenta maior estabilidade quando as magnitudes são perturbadas sem alteração relevante do ranking.

---

## Fronteira dos duplos

O terminal deve ordenar os 14 jogos pelo risco de falha do Top1 e destacar a fronteira entre o 5º e o 6º candidato.

Calcular:

```text
P13+ original
P13+ após trocar o 5º pelo 6º
Delta absoluto
Delta relativo
Margem pTop1
```

Separar sempre:

```text
Fronteira probabilística
Robustez no objetivo
```

Uma margem pequena em `p(top1)` não implica necessariamente impacto pequeno em `P13+`.

---

## Backtest da baseline

Implementar explicitamente:

```text
9 maiores p(top1) -> Top1 seco
5 menores p(top1) -> Top2+Top3
```

Comparar em walk-forward contra:

```text
PROBABILITY_ONLY
RANK_ONLY
HYBRID_ORDINAL
CONSENSUS
otimizador completo
```

Métricas mínimas:

```text
14 acertos
>=13 acertos
>=12 acertos
média de acertos
mediana
distribuição de 0 a 14
Precision@5
Recall@5
CoverageFail
DoubleWasteRate
Agreement@5
Stability@5
```

---

## Oracle histórico 9-5-5

Implementar um `oracle_9_5_5` exclusivamente para diagnóstico retrospectivo.

O oracle pode usar o resultado real para encontrar a melhor aposta possível respeitando integralmente:

```text
9 secos
5 duplos
0 triplos
9 Top1
5 Top2
5 Top3
Flamengo obrigatório, quando aplicável
```

O oracle **nunca pode ser usado para prever o próximo concurso**.

### Classificação

```text
SUCCESS
RECOVERABLE
UNRECOVERABLE
```

- `SUCCESS`: estratégia real atingiu 13+.
- `RECOVERABLE`: ficou abaixo de 13, mas existia aposta válida 9-5-5 capaz de atingir 13+.
- `UNRECOVERABLE`: nenhuma aposta válida sob as Hard Constraints conseguiria 13+.

### RecoveryRate

```text
RecoveryRate = SUCCESS / (SUCCESS + RECOVERABLE)
```

---

## Análise 12 -> 13

Para concursos com exatamente 12 acertos, identificar a menor alteração necessária para chegar a 13.

Acumular:

```text
% recuperável com 1 troca
% recuperável com 2 trocas
% recuperável com 3+ trocas
```

Verificar especialmente se as recuperações ocorrem dentro da zona cinzenta.

---

## Regret do seletor

```text
RegretHits = acertos_oracle - acertos_modelo
```

Quando comparável ex ante:

```text
RegretP13 = P13+_melhor_candidato - P13+_escolhido
```

Reportar:

```text
mean_regret
median_regret
p90_regret
zero_regret_rate
```

---

## Métricas específicas dos duplos

### Precision@5

```text
Precision@5 = falhas de Top1 entre os 5 duplos / 5
```

### Recall@5 / CoverageFail

```text
Recall@5 = falhas de Top1 capturadas pelos duplos / falhas de Top1 totais
```

### DoubleWasteRate

```text
DoubleWasteRate = duplos em que Top1_hit=1 / 5
```

O seletor deve buscar:

```text
maximizar CoverageFail
minimizar DoubleWasteRate
```

---

## Decomposição dos erros

```text
Erro de seco:
Top1 seco, resultado real = Top2 ou Top3

Erro de duplo:
Top2+Top3, resultado real = Top1
```

Reportar:

```text
erros_secos_top1
erros_duplos_por_top1_hit
```

---

## Meta-modelo da zona cinzenta

Priorizar um meta-modelo para candidatos próximos ao cutoff, por exemplo ranks 4 a 8 de risco.

Alvo:

```text
top1_fail = 1 - top1_hit
```

Features candidatas:

```text
classe_p_top1
rank_p_top1
rank_gap12
rank_gap13
rank_entropy
tipo_ranking_1X2
posição
rank_no_concurso
distance_to_cutoff
historical_fail_rate
features de regime
```

A versão menos dependente de probabilidades deve preferir features ordinais/categóricas quando seu desempenho fora da amostra for equivalente ou superior ao uso das magnitudes contínuas.

---

## Learning to Rank

Testar ranking dos 14 jogos pelo risco de falha do Top1.

Métricas:

```text
Precision@5
Recall@5
NDCG@5
```

O modelo pode ser treinado com features contínuas, ordinais ou exclusivamente estruturais, permitindo comparação direta da dependência probabilística.

---

## Calibração por rank

Auditar:

```text
p(top1) previsto vs frequência real de top1_hit
p(top2) previsto vs frequência real de top2_hit
p(top3) previsto vs frequência real de top3_hit
```

Definição possível:

```text
HistoricalLiftTopK = frequencia_real_topK_hit / probabilidade_media_prevista_topK
```

O lift deve ser diagnóstico ou feature, nunca correção automática sem validação fora da amostra.

---

## Regime do concurso

Representar o concurso por características como:

```text
quantidade de Top1=1
quantidade de Top1=X
quantidade de Top1=2
quantidade de cada um dos 6 tipos de ranking
mean_top1
median_top1
mean_entropy
mean_gap12
n_favoritos_fortes
n_jogos_equilibrados
```

As versões `RANK_ONLY` e `HYBRID_ORDINAL` devem priorizar as variáveis estruturais e categóricas desse vetor.

---

## Matriz de trocas

Calcular o impacto de trocar cada duplo por cada seco compatível com as Hard Constraints.

```text
Sai | Entra | Delta P13+
```

Isso permite visualizar a geometria completa da solução e identificar a verdadeira zona cinzenta.

---

## Robustez e Stability@5

Perturbar probabilidades, renormalizar e rerodar o seletor.

Reportar a frequência com que cada jogo permanece nos 5 duplos.

```text
Stability@5 = média da persistência dos 5 duplos escolhidos
```

A robustez deve ser analisada em conjunto com o desempenho de `>=13`: estabilidade sem desempenho não é objetivo suficiente.

---

## Monte Carlo sobre incerteza

Simular múltiplos vetores probabilísticos plausíveis e medir:

```text
frequência de cada jogo entrar nos 5 duplos
P13+ médio
percentil 5%
percentil 50%
percentil 95%
```

Um objetivo robusto futuro pode considerar:

```text
max E[P13+]
```

---

## Walk-forward e prevenção de leakage

Fluxo obrigatório:

```text
treina até concurso N-1
calibra usando apenas dados disponíveis até N-1
prevê concurso N
monta a aposta de N
avalia contra o resultado real de N
avança para N+1
```

Probabilidades in-sample não devem ser usadas como meta-features para `top1_hit`, `top2_hit`, `top3_hit` ou `top1_fail`.

---

## Validação por período

Reportar resultados por janelas, por exemplo:

```text
últimos 50 concursos
51-100 anteriores
101-200 anteriores
histórico completo
```

Uma estratégia só deve ser considerada robusta se o ganho não depender de um único período.

---

## Bootstrap da taxa de 13+

Como 13+ é raro, estimar a incerteza da taxa observada por bootstrap no nível de concurso.

```text
hit_rate_13plus = ...
IC 95% = [... ; ...]
```

---

## Ablation study

Comparar progressivamente:

```text
A - baseline 5 menores p(top1)
B - PROBABILITY_ONLY
C - RANK_ONLY
D - HYBRID_ORDINAL
E - CONSENSUS
F - + meta-modelo zona cinzenta
G - + Historical Pattern Matching
H - + regime de concurso
I - + Soft Constraint Palmeiras
J - modelo completo
```

Relatório:

```text
Modelo | 14 | >=13 | >=12 | Média | Precision@5 | Recall@5 | Agreement@5 | Stability@5
```

Uma feature ou heurística só deve permanecer se demonstrar contribuição fora da amostra.

---

## Champion / Challenger

Manter:

```text
Champion = estratégia atualmente aprovada
Challenger = nova implementação em avaliação
```

O Challenger só deve ser promovido se superar o Champion em walk-forward.

Para estratégias menos dependentes de probabilidades, a promoção deve considerar simultaneamente:

1. desempenho de `>=13`;
2. desempenho de `>=12`;
3. estabilidade por período;
4. robustez a perturbações;
5. dependência probabilística menor, **desde que não haja perda material no objetivo principal**.

---

## Hierarquia de métricas

```text
1. hit_rate_13plus
2. hit_rate_12plus
3. RecoveryRate
4. Precision@5 / Recall@5 / CoverageFail
5. mean_hits
6. robustez / Stability@5
7. Agreement@5 / dependência probabilística
8. calibração / log-loss
```

O produto final é a aposta completa, não o estimador probabilístico isolado.

---

## Guardrail contra overfitting

> Nenhuma complexidade adicional deve entrar na estratégia principal sem demonstrar ganho fora da amostra sobre uma baseline mais simples.

Critérios:

- walk-forward;
- amostra suficiente;
- melhoria em `>=13`;
- ausência de deterioração material em `>=12`;
- estabilidade em diferentes períodos;
- resultado não dependente de poucos concursos extremos;
- intervalo de confiança compatível com ganho plausível.

---

## Função objetivo

O objetivo principal permanece:

```text
max P(acertos >= 13)
```

Exibir sempre que possível:

```text
P(14)
P(13)
P(>=13)
P(12)
P(>=12)
```

Sob a hipótese de independência entre jogos, a distribuição de acertos pode ser calculada exatamente por programação dinâmica / Poisson-binomial.

A estratégia menos dependente das probabilidades **não altera a Hard Constraint nem o objetivo final**. Ela altera apenas a forma de escolher entre soluções viáveis.

---

## Telemetria esperada

### Por partida

```text
Jogo
Mandante x Visitante
p(1)
p(X)
p(2)
top1 / p(top1)
top2 / p(top2)
top3 / p(top3)
gap12
gap13
entropy
classe de confiança
rank_pTop1
rank_gap12
rank_entropy
votos dos seletores
grupo: núcleo_duplo / zona_cinzenta / núcleo_seco
tipo: seco ou duplo
palpite
cobertura
motivo da escolha
```

### Consenso dos seletores

```text
Jogo | Prob | Gap12 | Entropia | Histórico | RankOnly | Votos
```

Exibir:

```text
Núcleo robusto dos duplos
Zona cinzenta
Núcleo robusto dos secos
Agreement@5
```

### Fronteira

```text
5º candidato
6º candidato
margem pTop1
delta P13+
fronteira probabilística
robustez no objetivo
```

### Validação final

```text
Secos: 9/9
Duplos: 5/5
Triplos: 0/0
Top1: 9/9
Top2: 5/5
Top3: 5/5
Total: 19/19
Flamengo/RJ: regra satisfeita, quando aplicável
P(14)
P(13)
P(>=13)
P(12)
P(>=12)
```

---

## Soft Constraint Palmeiras — custo explícito

Quando houver conflito:

```text
Melhor solução absoluta: P13+ = ...
Melhor solução sem vitória do Palmeiras: P13+ = ...
Custo da preferência: ...
```

A preferência só deve prevalecer quando o custo for aceitável dentro da estratégia.

---

## Estrutura do repositório

```text
.
├── main.py
├── data/
│   ├── concursos_anteriores.csv
│   └── proximo_concurso.csv
├── scripts/
│   ├── preprocess_data.py
│   ├── train_model.py
│   └── predict_results.py
└── output/
    └── predictions.csv
```

### Responsabilidades

- `main.py`: orquestração e telemetria.
- `data/concursos_anteriores.csv`: histórico de treinamento, calibração e backtest.
- `data/proximo_concurso.csv`: concurso alvo.
- `scripts/preprocess_data.py`: leitura, validação e engenharia de features.
- `scripts/train_model.py`: treinamento, calibração, meta-modelos e avaliação walk-forward.
- `scripts/predict_results.py`: probabilidades, ranking, seletores, otimização 9-5-5 e palpite final.
- `output/predictions.csv`: saída auditável.

---

## Formato dos CSVs

```text
delimitador: ;
separador decimal das odds: ,
```

Exemplo:

```python
pd.read_csv(caminho, sep=";", decimal=",")
```

---

## Convenção dos palpites

Secos:

```text
1
X
2
```

Duplos:

```text
1X
12
X2
```

Triplos:

```text
1X2
```

Na configuração atual:

```text
0 triplos
```

---

## Execução

```bash
python main.py
```

Testes:

```bash
python -m unittest discover -v
```

---

## Ordem recomendada de implementação

```text
1. modos PROBABILITY_ONLY / RANK_ONLY / HYBRID_ORDINAL
2. consenso dos seletores + votação
3. núcleo de duplos / zona cinzenta / núcleo de secos
4. Agreement@5
5. Rank Preservation Stress Test
6. Temperature Stress Test
7. backtest comparativo dos modos
8. oracle_9_5_5
9. SUCCESS / RECOVERABLE / UNRECOVERABLE
10. análise 12 -> 13
11. Precision@5 / Recall@5 / CoverageFail / DoubleWasteRate
12. meta-modelo da zona cinzenta
13. Historical Pattern Matching
14. matriz de trocas
15. Stability@5
16. bootstrap de >=13
17. Champion / Challenger
18. learning to rank
19. Monte Carlo robusto
20. ablation study contínuo
```

A pergunta experimental central passa a ter duas partes:

> **O esquema 9-5-5 está estruturalmente limitando o desempenho, ou o sistema ainda está escolhendo os cinco duplos errados?**

> **Quanto da qualidade atual vem realmente da magnitude das probabilidades, e quanto pode ser preservado ou melhorado usando ranking, histórico, estrutura e consenso?**

---

## Regra fundamental

> **As Hard Constraints têm precedência absoluta sobre qualquer Soft Constraint, heurística ou preferência.**

> **A métrica decisiva do projeto é a qualidade da aposta completa para atingir pelo menos 13 acertos, validada fora da amostra.**

> **Reduzir dependência das probabilidades só é melhoria se preservar ou aumentar o desempenho real de 13+.**
