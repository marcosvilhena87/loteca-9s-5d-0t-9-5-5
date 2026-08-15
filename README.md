# Loteca 9S-5D-0T — Estratégia 9-5-5

Projeto para geração de **um único palpite final por concurso da Loteca**, usando `data/concursos_anteriores.csv` e as informações do próximo concurso para maximizar prioritariamente:

```text
P(acertos >= 13)
```

O projeto deve respeitar integralmente as Hard Constraints. Probabilidades, calibrações, histórico, meta-modelos, consenso, heurísticas e Soft Constraints só podem atuar dentro do espaço de soluções válidas.

---

# Estratégia

1. Gerar um único palpite final por concurso.
2. Produzir `p(1)`, `p(X)` e `p(2)` para cada partida.
3. Ordenar os três resultados em `top1`, `top2` e `top3`.
4. Em empate de probabilidades, usar obrigatoriamente:

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

6. Exibir telemetria suficiente para auditar probabilidades base/calibradas, rankings, `risk_rank`, gaps, entropia, secos, duplos, fronteira 5º/6º, evidência histórica, robustez, Hard/Soft Constraints e decomposição de `P(>=13)`.

---

# Hard Constraints

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

A contagem refere-se às marcações efetivamente presentes no volante.

## Flamengo

Quando o **FLAMENGO/RJ** participar do concurso, o resultado correspondente à sua vitória deve obrigatoriamente estar entre as marcações, independentemente de ocupar Top1, Top2 ou Top3.

---

# Soft Constraints

1. Favorecer ordenações que antecipem e concentrem Top1, especialmente nas 9 primeiras posições, privilegiando runs longas e baixa fragmentação.
2. Favorecer soluções que excluam a vitória do **PALMEIRAS/SP**, priorizando empate ou derrota quando isso não comprometer significativamente a qualidade global.
3. Soft Constraints nunca podem relaxar Hard Constraints.
4. O custo de uma Soft Constraint deve ser mensurável e exibido quando relevante.

---

# Hipótese estrutural 9-5-5

Baseline estrutural:

```text
9 maiores p(top1) -> seco Top1
5 menores p(top1) -> duplo Top2+Top3
```

Essa configuração satisfaz automaticamente 9 secos, 5 duplos, 9 Top1, 5 Top2 e 5 Top3.

Para um jogo `Top2+Top3`:

```text
P(cobertura) = 1 - p(top1)
```

Essa baseline não é regra obrigatória. É a referência que qualquer abordagem mais sofisticada precisa superar fora da amostra.

## Relação entre tipos de duplo

```text
D12 = duplos Top1+Top2
D13 = duplos Top1+Top3
D23 = duplos Top2+Top3

D12 + D13 + D23 = 5

SecoTop1 = 4 + D23
SecoTop2 = D13
SecoTop3 = D12
```

Portanto:

- `Top1+Top2` exige um Top3 seco em outra partida;
- `Top1+Top3` exige um Top2 seco em outra partida;
- `Top2+Top3` permite manter um Top1 seco adicional.

---

# Histórico como segunda fonte de decisão

O histórico não deve servir apenas para treinar probabilidades. Ele deve fornecer evidência explícita para decisões estruturais.

Princípio preferencial:

```text
presente define o contexto
histórico resolve a dúvida
```

Estudar historicamente:

```text
top1_hit
top2_hit
top3_hit
risk_rank
```

incluindo frequência global/recente, distribuição por concurso, runs, fragmentação, transições Top1/Top2/Top3, posição, tipo de ranking, `risk_rank`, concursos 13+, concursos `RECOVERABLE`, zona de cutoff e estabilidade temporal.

---

# Calibração probabilística

## Temperatura

Promover apenas quando melhorar log-loss em validação cronologicamente posterior.

```text
Temperatura candidata
Temperatura implantada
Log-loss bruto
Log-loss calibrado
Status: promovida / rejeitada
```

## Calibração global por rank Top1/Top2/Top3

Pode ser testada, mas só altera a implantação se melhorar a validação fora da amostra.

Se rejeitada:

```text
lifts Top1/Top2/Top3 = [1.0, 1.0, 1.0]
```

Uma calibração global rejeitada não implica que sinais históricos relativos ao concurso sejam inúteis.

---

# `risk_rank`: prioridade atual de pesquisa

Para cada concurso, ordenar as 14 partidas do maior risco relativo de falha do Top1 para o menor:

```text
risk_rank = 1..14

risk_rank=1  -> maior risco relativo
risk_rank=14 -> menor risco relativo
```

O `risk_rank` reduz dependência da magnitude crua ao transformar confiança em **posição relativa dentro do próprio concurso**.

## Calibração histórica por `risk_rank`

O treinamento pode estimar, para cada `risk_rank`, um fator suavizado entre frequência observada e probabilidade prevista de acerto do Top1.

Regras obrigatórias:

1. usar somente concursos cronologicamente anteriores;
2. preservar a proporção relativa de Top2/Top3 quando ajustar Top1;
3. avaliar em bloco posterior fora da amostra;
4. promover somente se houver ganho de validação;
5. usar fatores neutros `1.0` quando rejeitada;
6. nunca relaxar Hard Constraints.

Telemetria:

```text
Calibração por risk_rank: promovida / rejeitada
Log-loss risk_rank: base=... calibrado=...
```

---

# Auditoria histórica do `risk_rank`

## Base vs ajustado por jogo

```text
Jogo
risk_rank
pTop1_base
pTop1_ajustado
delta_pTop1
top1_base
top1_ajustado
ranking_mudou?
```

Registrar também alterações de Top2/Top3.

## Tabela histórica 1..14

```text
risk_rank
n
pTop1_medio_previsto
Top1_hit_observado
Top1_fail_observado
CalibrationError
lift_hit
lift_fail
IC95%
RiskRankStability
HistoricalConfidence
```

Definir:

```text
CalibrationError = Top1_hit_observado - pTop1_medio_previsto
```

Destacar os ranks com maior `overconfidence` e `underconfidence`.

## Intervalos de confiança

Para cada rank, reportar `n`, hit rate, fail rate e IC95%. A força do ajuste deve cair quando a evidência for mais incerta.

## Shrinkage

```text
lift_shrunk = 1 + alpha * (lift - 1)
0 <= alpha <= 1
```

`alpha` pode depender de amostra, largura do IC, estabilidade temporal e consistência entre janelas.

## Estabilidade temporal

Comparar:

```text
últimos 50
últimos 100
últimos 200
histórico completo
```

Criar `RiskRankStability` e reduzir o peso de sinais instáveis.

## Monotonicidade / isotonic calibration

Testar como Challenger uma curva monotônica em que:

```text
Top1_fail(rank1) >= Top1_fail(rank2) >= ... >= Top1_fail(rank14)
```

Usar isotonic regression somente se melhorar o desempenho walk-forward.

---

# Métricas próprias do `risk_rank`

## RiskRankPrecision@5

```text
RiskRankPrecision@5 = Top1_fail entre risk_ranks 1..5 / 5
```

## RiskRankRecall@5

```text
RiskRankRecall@5 = Top1_fail capturados por risk_ranks 1..5 / Top1_fail totais
```

## Curva cumulativa Recall@k

Calcular:

```text
Recall@1
Recall@2
...
Recall@14
```

Destacar especialmente `Recall@5`, `Recall@6` e `Recall@7` para medir quanto da dificuldade vem do seletor e quanto vem do limite estrutural de apenas 5 duplos.

## RiskRankNDCG@5

Usar NDCG@5 para medir a qualidade da ordenação das falhas no topo do ranking.

## RiskRankECE

Criar ECE específico por `risk_rank`:

```text
RiskRankECE = soma ponderada |observado - previsto|
```

Como cada posição tende a ter a mesma quantidade de observações, a interpretação é simples.

## Brier por `risk_rank`

Adicionar Brier Score para complementar o log-loss e evitar promoção baseada em uma única métrica probabilística.

---

# Backtest real BASE vs RISK_RANK — prioridade máxima

O ganho de `P(>=13)` calculado com probabilidades ajustadas é **estimado pelo próprio modelo**. Ele não prova sozinho ganho real.

Executar walk-forward estrito comparando:

```text
A = probabilidades brutas
B = + temperatura
C = + temperatura + risk_rank
```

Sem adicionar outras mudanças simultaneamente.

Relatório mínimo:

```text
Modelo
Concursos
LogLoss
Brier
RiskRankECE
14
>=13
>=12
mean_hits
median_hits
RecoveryRate
Precision@5
Recall@5
CoverageFail
DoubleWasteRate
RiskRankPrecision@5
RiskRankRecall@5
RiskRankNDCG@5
```

A contribuição incremental do `risk_rank` deve ser medida nos resultados reais, não apenas em `P13+` calculado.

---

# Net13Gain

Criar métrica explícita de migração para o objetivo principal.

```text
Net13Gain =
  concursos que passaram de <13 para >=13
- concursos que passaram de >=13 para <13
```

Reportar separadamente:

```text
11 -> 13
12 -> 13
12 -> 14
13 -> 12
13 -> 11
14 -> 13
14 -> <13
```

Exemplo:

```text
BASE -> RISK_RANK
<13 -> >=13 : 6
>=13 -> <13 : 2
Net13Gain = +4
```

Essa métrica tem prioridade maior que pequenas diferenças de log-loss.

---

# Matriz de transição de acertos

Comparar os acertos concurso a concurso antes/depois do `risk_rank`.

Exemplo estrutural:

```text
BASE\RISK | 10 | 11 | 12 | 13 | 14
10        | .. | .. | .. | .. | ..
11        | .. | .. | .. | .. | ..
12        | .. | .. | .. | .. | ..
13        | .. | .. | .. | .. | ..
14        | .. | .. | .. | .. | ..
```

A matriz deve mostrar se o componente está principalmente recuperando `12->13`, melhorando `11->12`, ou apenas deslocando resultados sem ganho na cauda.

---

# RankingChangeImpact

Quando o ajuste histórico alterar a identidade de Top1/Top2/Top3, registrar:

```text
n_ranking_changes
changes_correct
changes_wrong
net_hit_gain_from_changes
ranking_change_success_rate
```

Pergunta principal:

> quando o histórico muda o ranking concreto, a mudança produz mais acertos do que erros?

---

# RISK_RANK_FREE vs RISK_RANK_PRESERVE_ORDER

Testar duas versões explicitamente:

```text
RISK_RANK_FREE
- pode alterar a ordem 1/X/2

RISK_RANK_PRESERVE_ORDER
- ajusta a confiança
- preserva Top1/Top2/Top3 originais
```

Comparar em walk-forward:

```text
>=13
>=12
Net13Gain
mean_hits
RankingChangeImpact
LogLoss
Brier
```

Esse experimento é central para avaliar uma estratégia menos dependente das magnitudes sem permitir que pequenos ajustes históricos troquem a identidade dos ranks de forma desnecessária.

---

# Cutoff histórico 5º vs 6º

A fronteira entre `risk_rank=5` e `risk_rank=6` é uma prioridade especial.

Para cada concurso histórico, armazenar:

```text
candidate_rank5
candidate_rank6
pTop1_rank5
pTop1_rank6
margin_56
gap12_5
gap12_6
entropy_5
entropy_6
ranking_type_5
ranking_type_6
top1_hit_rank5
top1_hit_rank6
```

Classificar em quatro estados:

```text
A = rank5 fail / rank6 hit   -> rank5 correto
B = rank5 hit / rank6 fail   -> rank6 deveria entrar
C = ambos fail               -> ambos úteis
D = ambos hit                -> ambos desperdício
```

## CutoffDecisionAccuracy

Calcular somente nos casos informativos A/B:

```text
CutoffDecisionAccuracy = decisões corretas / casos em que apenas um dos dois falhou
```

Não diluir essa métrica com casos C/D, nos quais não existe vencedor inequívoco.

Também calcular:

```text
P(rank6 deveria substituir rank5 | margin_56 < 0.01)
P(rank6 deveria substituir rank5 | 0.01 <= margin_56 < 0.02)
P(rank6 deveria substituir rank5 | margin_56 >= 0.02)
```

---

# Oracle específico do ranking de risco

Criar diagnóstico retrospectivo para responder:

```text
quantos concursos RECOVERABLE exigiam sair do top-5 risk_rank?
quantas falhas estavam em risk_rank 6/7/8?
quantas eram recuperáveis com uma única troca?
```

O objetivo é separar:

```text
limitação do ranking de risco
vs
limitação estrutural dos 5 duplos
```

Esse oracle nunca pode ser usado na previsão do próximo concurso.

---

# Pairwise 5 vs 6

Treinar um Challenger especializado apenas na decisão crítica do cutoff.

Entrada:

```text
delta_pTop1
delta_gap12
delta_entropy
ranking_type_5
ranking_type_6
CalibrationError_5
CalibrationError_6
RiskRankStability_5
RiskRankStability_6
HistoricalConfidence_5
HistoricalConfidence_6
```

Saída:

```text
KEEP_5
SWAP_6
```

Métrica principal:

```text
CutoffDecisionAccuracy
```

Também medir impacto real em `>=13` e `Net13Gain`.

---

# Modelo da zona cinzenta 4..8

Somente depois de validar o pairwise 5/6, expandir para:

```text
risk_rank 4..8
```

Target:

```text
top1_fail
```

Features preferenciais:

```text
risk_rank
rank_gap12
rank_entropy
ranking_type
posição
CalibrationErrorByRiskRank
RiskRankStability
HistoricalConfidence
HistoricalScore
HistoricalVote
regime do concurso
```

Preferir features ordinais/categóricas quando apresentarem desempenho equivalente ou superior às magnitudes contínuas.

---

# HistoricalConfidence operacional

Transformar a confiança histórica em variável utilizável pelo seletor.

```text
HistoricalConfidence = f(
  tamanho_da_amostra,
  largura_IC,
  estabilidade_temporal,
  consistência_entre_fontes
)
```

A intensidade do ajuste pode ser:

```text
adjustment_strength = base_adjustment * HistoricalConfidence
```

Os pesos concretos precisam ser aprendidos exclusivamente em validação walk-forward.

---

# Confidence-aware cutoff

Na fronteira 5º/6º, a confiança histórica pode modular o desempate.

Exemplo conceitual:

```text
rank5 HIGH + rank6 MEDIUM -> maior resistência ao swap
rank5 LOW  + rank6 HIGH   -> maior abertura ao swap
```

Isso é Soft/Challenger, nunca Hard Constraint.

---

# Interações futuras do `risk_rank`

Somente depois de validar o componente isolado:

## `risk_rank` + tipo de ranking

```text
risk_rank=3 + 1>X>2
risk_rank=3 + 1>2>X
risk_rank=3 + 2>X>1
```

Exigir `minimum_sample`, shrinkage e walk-forward.

## `risk_rank` + gap12 ordinal

Usar `rank_gap12`, quantis ou buckets históricos.

## `risk_rank` + entropia ordinal

Usar `entropy_rank` em vez de depender diretamente da magnitude.

## Múltiplos rankings de risco

```text
risk_rank_prob
risk_rank_gap
risk_rank_entropy
risk_rank_history
risk_rank_consensus
```

Comparar qual ranking melhor antecipa `Top1_fail` fora da amostra.

---

# Estratégias menos dependentes das probabilidades cruas

## `PROBABILITY_ONLY`

```text
score_duplo = 1 - p(top1)
```

## `RANK_ONLY`

Usa probabilidades apenas para formar Top1/Top2/Top3 e posições ordinais.

## `RISK_RANK_ONLY`

Baseline simples:

```text
risk_rank 1..5  -> duplo Top2+Top3
risk_rank 6..14 -> seco Top1
```

Esse baseline deve ser medido explicitamente.

## `HISTORICAL_ONLY`

Challenger diagnóstico usando apenas evidências históricas permitidas temporalmente.

## `HYBRID_ORDINAL`

Pode usar:

```text
risk_rank
rank_gap12
rank_gap13
rank_entropy
HistoricalScore
HistoricalVote
HistoricalConfidence
```

O objetivo é preservar ou melhorar `>=13` reduzindo dependência da magnitude crua.

---

# HistoricalScore e HistoricalVote

## HistoricalScore

```text
HistoricalScore =
    w1 * historical_risk_rank
  + w2 * historical_ranking_type
  + w3 * historical_position
  + w4 * historical_knn_game
  + w5 * historical_regime
  + w6 * historical_recency
```

Preferir ranks, percentis e scores normalizados. Pesos somente por walk-forward.

## HistoricalVote

```text
H1 = risk_rank
H2 = tipo de ranking
H3 = posição
H4 = KNN por jogo
H5 = KNN por concurso
H6 = recência/estabilidade
H7 = pattern matching
H8 = RECOVERABLE / 12->13
```

Manter voto histórico separado do probabilístico na telemetria.

---

# KNN histórico

## Por jogo

Features preferenciais:

```text
tipo_de_ranking
risk_rank
pTop1_percentile
gap12_percentile
gap13_percentile
entropy_percentile
posição
```

Exibir `n_vizinhos`, Top1_fail, Top1_hit, voto KNN e distância média.

## Por concurso

Assinatura global:

```text
mean_pTop1
median_pTop1
mean_entropy
mean_gap12
n_top1_home
n_top1_draw
n_top1_away
n_jogos_equilibrados
n_favoritos_fortes
quantidade de cada tipo de ranking
```

Analisar quantidade de Top1_fail, distribuição por `risk_rank`, runs e falhas próximas ao cutoff.

---

# Núcleo e zona cinzenta

Classificar os jogos em:

```text
núcleo_duplo
zona_cinzenta
núcleo_seco
```

Filosofia inicial:

```text
probabilidade / estrutura -> define o núcleo
histórico                 -> resolve a zona cinzenta
```

---

# Oracle histórico 9-5-5

Implementar `oracle_9_5_5` exclusivamente para diagnóstico retrospectivo.

Classificação:

```text
SUCCESS
RECOVERABLE
UNRECOVERABLE
```

- `SUCCESS`: estratégia real atingiu 13+;
- `RECOVERABLE`: ficou abaixo de 13, mas existia aposta válida 9-5-5 capaz de atingir 13+;
- `UNRECOVERABLE`: nenhuma aposta válida conseguiria 13+.

```text
RecoveryRate = SUCCESS / (SUCCESS + RECOVERABLE)
```

O oracle nunca pode ser usado para prever o próximo concurso.

---

# Análise 12 -> 13

Para concursos com exatamente 12 acertos, identificar a menor alteração necessária para chegar a 13.

```text
% recuperável com 1 troca
% recuperável com 2 trocas
% recuperável com 3+ trocas
```

Criar dataset específico quando:

```text
acertos_modelo = 12
acertos_oracle >= 13
```

Registrar duplo que deveria sair, seco que deveria entrar, `risk_rank`, `margin_56`, ranking type, gap/entropia ordinal, HistoricalScore, HistoricalVote e regime.

---

# Métricas específicas dos duplos

```text
Precision@5 = falhas de Top1 entre os 5 duplos / 5
Recall@5 = falhas de Top1 capturadas pelos duplos / falhas Top1 totais
CoverageFail = Recall@5
DoubleWasteRate = duplos em que Top1_hit=1 / 5
```

Objetivo auxiliar:

```text
maximizar CoverageFail
minimizar DoubleWasteRate
```

O objetivo principal continua sendo `>=13`.

---

# Fronteira 5º vs 6º

Exibir:

```text
Rank | Jogo | pTop1 | 1-pTop1 | risk_rank | Decisão
```

Calcular:

```text
P13+ original
P13+ após troca
Delta absoluto
Delta relativo
Margem pTop1
HistoricalScore 5º/6º
HistoricalVote 5º/6º
HistoricalConfidence 5º/6º
CutoffDecision signal
```

Separar sempre:

```text
Fronteira probabilística
Evidência histórica
Robustez no objetivo
```

---

# Função objetivo

```text
max P(acertos >= 13)
```

Exibir:

```text
P(14)
P(13)
P(>=13)
P(12)
P(>=12)
```

Sob hipótese de independência entre jogos, a distribuição pode ser calculada exatamente por programação dinâmica / Poisson-binomial.

**Importante:** `P(>=13)` calculado com probabilidades ajustadas é uma estimativa interna. Promoção de estratégia depende do desempenho real walk-forward.

---

# Matriz de trocas

```text
Sai | Entra | Delta P13+ | Delta HistoricalScore | Delta Consensus
```

A matriz permite visualizar a geometria completa da solução e a zona cinzenta real.

---

# Robustez

## Stability@5

Perturbar probabilidades, renormalizar e rerodar o seletor.

```text
Stability@5 = persistência média dos 5 duplos
```

## Rank Preservation Stress Test

Preservar Top1/Top2/Top3, comprimir/expandir magnitudes, renormalizar, rerodar e medir `Agreement@5`/`Stability@5`.

## Temperature Stress Test

Testar diagnosticamente:

```text
T = 0.70
T = 0.90
T = 1.00
T = 1.20
T = 1.50
```

Sem alterar automaticamente a temperatura implantada.

---

# Walk-forward e prevenção de leakage

Fluxo obrigatório:

```text
treina até concurso N-1
calibra usando apenas dados <= N-1
calcula risk_rank/estatísticas usando apenas dados permitidos
calcula HistoricalScore somente com concursos <= N-1
busca KNN somente em concursos <= N-1
prevê concurso N
monta aposta N
avalia resultado real N
avança para N+1
```

Nenhuma estatística histórica pode incorporar direta ou indiretamente o resultado do concurso avaliado.

---

# Validação por período

Reportar:

```text
últimos 50 concursos
51-100 anteriores
101-200 anteriores
histórico completo
```

Uma estratégia só é robusta se o ganho não depender de um único período.

---

# Bootstrap de 13+

Como 13+ é raro, estimar incerteza no nível de concurso:

```text
hit_rate_13plus = ...
IC95% = [... ; ...]
```

Também aplicar bootstrap ao **delta de hit_rate_13plus entre Champion e Challenger** sempre que possível.

---

# Promotion Gate do `risk_rank`

O componente só deve continuar implantado quando cumprir critérios fora da amostra.

Prioridade:

```text
1. hit_rate_13plus melhora ou fica estatisticamente equivalente
2. Net13Gain >= 0 e preferencialmente > 0
3. hit_rate_12plus não piora materialmente
4. ganho aparece em diferentes períodos
5. RiskRankPrecision@5 / Recall@5 apresentam sinal útil
6. CutoffDecisionAccuracy apresenta sinal útil
7. RankingChangeImpact não é negativo de forma sistemática
8. Brier / ECE / LogLoss não pioram materialmente
```

Melhorar log-loss isoladamente **não é suficiente**.

---

# Ablation study

Comparar progressivamente:

```text
A - probabilidades brutas
B - + temperatura
C - + risk_rank
D - RISK_RANK_PRESERVE_ORDER
E - RISK_RANK_FREE
F - + shrinkage
G - + isotonic
H - + confidence-aware adjustment
I - + pairwise 5/6
J - + modelo zona 4..8
K - + ranking_type / gap / entropia ordinal
L - + HistoricalVote
M - + KNN histórico
N - + RECOVERABLE / 12->13
O - + consenso
P - + Soft Constraint Palmeiras
Q - modelo completo
```

Relatório mínimo:

```text
Modelo
LogLoss
Brier
RiskRankECE
14
>=13
>=12
Net13Gain
Média
RecoveryRate
Precision@5
Recall@5
RiskRankPrecision@5
RiskRankRecall@5
CutoffDecisionAccuracy
Stability@5
```

---

# Champion / Challenger

```text
Champion = estratégia atualmente aprovada
Challenger = nova implementação em avaliação
```

Challengers:

```text
RISK_RANK_ONLY
RISK_RANK_PRESERVE_ORDER
RISK_RANK_FREE
RISK_RANK_SHRINKAGE
RISK_RANK_ISOTONIC
RISK_RANK_CONFIDENCE_AWARE
PAIRWISE_5_6
PAIRWISE_GRAY_ZONE
HISTORICAL_ONLY
HYBRID_ORDINAL
HYBRID_HISTORY_ADAPTIVE
KNN_HISTORY
CONSENSUS_HISTORY
```

Promoção somente por walk-forward.

---

# Hierarquia de métricas

```text
1. hit_rate_13plus
2. Net13Gain
3. hit_rate_12plus
4. RecoveryRate
5. Precision@5 / Recall@5 / CoverageFail
6. RiskRankPrecision@5 / RiskRankRecall@5
7. CutoffDecisionAccuracy
8. mean_hits
9. robustez / Stability@5
10. Agreement@5 / dependência probabilística
11. Brier / RiskRankECE / LogLoss
```

O produto final é a aposta completa, não o estimador probabilístico isolado.

---

# Guardrail contra overfitting

Nenhuma complexidade adicional entra na estratégia principal sem ganho fora da amostra sobre uma baseline mais simples.

Critérios:

- walk-forward estrito;
- amostra suficiente;
- melhoria em `>=13`;
- `Net13Gain` não negativo;
- ausência de deterioração material em `>=12`;
- estabilidade por período;
- resultado não dependente de poucos concursos extremos;
- bootstrap/IC compatível com ganho plausível;
- shrinkage quando necessário;
- nenhuma informação futura nas features/calibrações.

---

# Telemetria esperada

## Calibração

```text
Temperatura candidata/implantada
LogLoss base/calibrado
Calibração Top1/2/3: promovida/rejeitada
Calibração risk_rank: promovida/rejeitada
LogLoss risk_rank
Brier risk_rank
RiskRankECE
```

## Auditoria histórica `risk_rank`

```text
Rank | n | pTop1 previsto | hit observado | fail observado | erro calibração | IC95% | estabilidade | confiança | lift
```

## Por partida

```text
Jogo
Mandante x Visitante
p_base(1/X/2)
p_ajustado(1/X/2)
top1/top2/top3 antes/depois
ranking_mudou?
risk_rank
gap12
gap13
entropy
rank_gap12
rank_entropy
HistoricalScore
HistoricalVote
HistoricalConfidence
grupo: núcleo_duplo / zona_cinzenta / núcleo_seco
tipo: seco ou duplo
palpite
cobertura
motivo da escolha
```

## Backtest `risk_rank`

```text
BASE vs TEMP vs TEMP+RISK_RANK
14
>=13
>=12
Net13Gain
12->13
13->12
Precision@5
Recall@5
RiskRankPrecision@5
RiskRankRecall@5
CutoffDecisionAccuracy
```

## Fronteira

```text
5º candidato
6º candidato
margin_56
P13+ original/após troca
delta absoluto/relativo
HistoricalScore
HistoricalVote
HistoricalConfidence
CutoffDecision signal
fronteira probabilística
evidência histórica
robustez no objetivo
```

## Validação final

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

A validação deve ser recalculada independentemente após a otimização e lançar erro se qualquer Hard Constraint for violada.

---

# Soft Constraint Palmeiras — custo explícito

```text
Melhor solução absoluta: P13+ = ...
Melhor solução sem vitória do Palmeiras: P13+ = ...
Custo da preferência: ...
```

A preferência só deve prevalecer quando o custo for aceitável.

---

# Estrutura do repositório

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

Responsabilidades:

- `main.py`: orquestração e telemetria;
- `data/concursos_anteriores.csv`: treinamento, calibração e backtest;
- `data/proximo_concurso.csv`: concurso alvo;
- `scripts/preprocess_data.py`: leitura, validação e features;
- `scripts/train_model.py`: treinamento, calibração, `risk_rank`, histórico e avaliação walk-forward;
- `scripts/predict_results.py`: probabilidades, rankings, seletores, evidência histórica, otimização 9-5-5 e palpite final;
- `output/predictions.csv`: saída auditável.

---

# Formato dos CSVs

```text
delimitador: ;
separador decimal das odds: ,
```

```python
pd.read_csv(caminho, sep=";", decimal=",")
```

---

# Convenção dos palpites

```text
Secos:    1 | X | 2
Duplos:   1X | 12 | X2
Triplos:  1X2
```

Configuração atual:

```text
0 triplos
```

---

# Execução

```bash
python main.py
```

Testes:

```bash
python -m unittest discover -v
```

---

# Ordem recomendada de implementação

```text
1. backtest real BASE vs TEMP vs TEMP+RISK_RANK
2. Net13Gain
3. matriz de transição de acertos
4. RiskRankPrecision@5 / RiskRankRecall@5
5. curva cumulativa Recall@k
6. Cutoff 5/6 nos quatro estados A/B/C/D
7. CutoffDecisionAccuracy
8. CalibrationErrorByRiskRank
9. RiskRankECE + Brier
10. RISK_RANK_PRESERVE_ORDER vs RISK_RANK_FREE
11. RankingChangeImpact
12. isotonic risk_rank como Challenger
13. shrinkage / HistoricalConfidence operacional
14. pairwise 5 vs 6
15. modelo da zona 4..8
16. risk_rank + ranking_type / gap / entropia ordinal
17. oracle específico do risk_rank
18. oracle_9_5_5 / RECOVERABLE / 12->13
19. HistoricalVote / KNN histórico
20. matriz de trocas
21. Stability@5 / stress tests
22. bootstrap do delta de >=13
23. Champion / Challenger
24. ablation study contínuo
```

A prioridade imediata é **provar se o `risk_rank` aumenta de fato a taxa real de 13+**, e não apenas o log-loss ou o `P13+` estimado pelo próprio modelo.

---

# Perguntas experimentais centrais

> **O `risk_rank` gera `Net13Gain` positivo em walk-forward?**

> **Os cinco primeiros `risk_rank` capturam uma parcela suficientemente alta das falhas Top1 para justificar a estrutura de cinco duplos?**

> **A decisão crítica entre o 5º e o 6º candidato pode ser melhorada historicamente sem overfitting?**

> **Permitir mudanças de Top1/Top2/Top3 ajuda mais do que prejudica, ou é melhor preservar a ordem e ajustar apenas confiança?**

> **A melhora do `risk_rank` persiste em diferentes períodos e no bootstrap do delta de 13+?**

> **Quanto da qualidade atual pode ser preservado usando sinais relativos/ordinais em vez das probabilidades cruas?**

---

# Regras fundamentais

> **As Hard Constraints têm precedência absoluta sobre qualquer Soft Constraint, heurística, calibração ou preferência.**

> **A métrica decisiva é a qualidade da aposta completa para atingir pelo menos 13 acertos, validada fora da amostra.**

> **`P13+` estimado pelo próprio modelo não substitui hit_rate_13plus real em walk-forward.**

> **Melhorar log-loss é útil, mas não substitui melhora real de 13+.**

> **Valorizar o histórico só é melhoria se aumentar ou preservar o desempenho real de 13+ em walk-forward.**

> **Reduzir dependência das probabilidades só é melhoria se preservar ou aumentar o desempenho real de 13+.**