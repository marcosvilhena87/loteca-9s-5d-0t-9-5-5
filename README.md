# Loteca 9S-5D-0T — Estratégia 9-5-5

Projeto para geração de **um único palpite final por concurso da Loteca**, usando o histórico de `data/concursos_anteriores.csv` e as informações do próximo concurso para maximizar prioritariamente:

```text
P(acertos >= 13)
```

O projeto deve respeitar integralmente as Hard Constraints. Probabilidades, calibrações, histórico, meta-modelos, consenso, heurísticas e Soft Constraints só podem atuar dentro do espaço de soluções válidas.

---

## Estratégia

1. Gerar um único palpite final por concurso.
2. Produzir `p(1)`, `p(X)` e `p(2)` para cada partida.
3. Ordenar os resultados em `top1`, `top2` e `top3`.
4. Em empate de probabilidades, usar obrigatoriamente:

```text
1 > 2 > X
```

5. Representar o resultado real por:

```text
top1_hit
top2_hit
top3_hit
```

Em cada partida, exatamente uma dessas variáveis deve ser igual a `1`.

6. Exibir telemetria suficiente para auditar:
   - probabilidades base e calibradas;
   - ranking Top1/Top2/Top3;
   - `risk_rank`;
   - gaps e entropia;
   - secos e duplos;
   - fronteira 5º/6º;
   - evidência histórica;
   - robustez;
   - Hard/Soft Constraints;
   - decomposição de `P(>=13)`.

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

A contagem refere-se às marcações efetivamente presentes no volante, e não ao número de partidas.

## Flamengo

Quando o **FLAMENGO/RJ** participar do concurso, o resultado correspondente à sua vitória deve obrigatoriamente estar entre as marcações.

A validação deve ser feita sobre o resultado concreto `1`, `X` ou `2`, independentemente de ocupar Top1, Top2 ou Top3.

---

# Soft Constraints

1. Favorecer ordenações que antecipem e concentrem Top1, especialmente nas 9 primeiras posições, privilegiando runs longas e baixa fragmentação.
2. Favorecer soluções que excluam a vitória do **PALMEIRAS/SP**, priorizando empate ou derrota quando isso não comprometer significativamente a qualidade global.
3. Soft Constraints nunca podem relaxar Hard Constraints.
4. O custo de uma Soft Constraint deve ser mensurável e exibido quando relevante.

---

# Hipótese estrutural 9-5-5

Uma baseline estrutural importante é:

```text
9 maiores p(top1)  -> seco Top1
5 menores p(top1)  -> duplo Top2+Top3
```

Ela satisfaz automaticamente:

```text
9 secos
5 duplos
9 Top1
5 Top2
5 Top3
```

Para um jogo `Top2+Top3`:

```text
P(cobertura) = p(top2) + p(top3) = 1 - p(top1)
```

Essa baseline **não é regra obrigatória**. É a referência que qualquer abordagem mais sofisticada precisa superar fora da amostra.

## Relação entre tipos de duplo

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

- `Top1+Top2` exige um Top3 seco em outra partida;
- `Top1+Top3` exige um Top2 seco em outra partida;
- `Top2+Top3` permite manter um Top1 seco adicional.

---

# Histórico como segunda fonte de decisão

O histórico de `data/concursos_anteriores.csv` não deve servir apenas para treinar probabilidades. Ele deve ser uma fonte explícita de evidência para decisões estruturais.

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

incluindo:

- frequência global e recente;
- distribuição por concurso;
- runs e fragmentação de Top1;
- transições Top1/Top2/Top3;
- comportamento por posição;
- comportamento por tipo de ranking;
- comportamento por `risk_rank`;
- padrões dos concursos que produziram 13+;
- padrões dos concursos `RECOVERABLE`;
- comportamento específico da zona de cutoff;
- estabilidade temporal.

---

# Calibração probabilística

## Temperatura

A calibração por temperatura deve ser promovida apenas quando melhorar o log-loss em validação cronologicamente posterior.

Telemetria mínima:

```text
Temperatura candidata
Temperatura implantada
Log-loss bruto
Log-loss calibrado
Status: promovida / rejeitada
```

## Calibração global por rank Top1/Top2/Top3

Pode ser testada, mas só deve alterar a implantação se melhorar a validação fora da amostra.

Se rejeitada:

```text
lifts Top1/Top2/Top3 = [1.0, 1.0, 1.0]
```

O fato de uma calibração global por Top1/Top2/Top3 ser rejeitada **não implica** que sinais históricos relativos ao concurso sejam inúteis.

---

# `risk_rank`: prioridade atual de pesquisa

## Definição

Para cada concurso, ordenar as 14 partidas do maior risco de falha do Top1 para o menor e atribuir:

```text
risk_rank = 1..14
```

Na convenção principal:

```text
risk_rank=1  -> maior risco relativo de falha do Top1
risk_rank=14 -> menor risco relativo de falha do Top1
```

O `risk_rank` é importante porque transforma a magnitude probabilística em **posição relativa dentro do próprio concurso**.

---

## Calibração histórica por `risk_rank` — implantação atual

O treinamento pode estimar, para cada `risk_rank`, um fator suavizado entre a frequência observada e a probabilidade prevista de acerto do Top1.

Regras obrigatórias:

1. usar somente concursos cronologicamente anteriores;
2. preservar a proporção relativa de Top2 e Top3 quando o ajuste atuar sobre Top1;
3. avaliar em bloco posterior fora da amostra;
4. promover somente se reduzir o log-loss;
5. se o teste falhar, usar fatores neutros `1.0`;
6. não relaxar nenhuma Hard Constraint.

Telemetria mínima:

```text
Calibração por risk_rank: promovida / rejeitada
Log-loss risk_rank: base=... calibrado=...
```

---

# Auditoria completa do `risk_rank`

A partir da promoção do `risk_rank`, a prioridade é provar que o componente funciona de forma robusta, e não apenas em um único concurso.

## 1. Probabilidade base vs ajustada por jogo

Exibir:

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

Exemplo:

```text
J1 | rank=1 | 0.3592 -> 0.3503 | -0.0089 | 2 -> 1 | SIM
```

Também registrar alterações em Top2/Top3 quando ocorrerem.

---

## 2. Tabela histórica `risk_rank` 1..14

Gerar relatório:

```text
risk_rank
n_jogos
pTop1_medio_previsto
Top1_hit_observado
Top1_fail_observado
lift_hit
lift_fail
```

Objetivo principal:

> verificar se a posição relativa de risco contém informação histórica consistente além da probabilidade crua.

---

## 3. Intervalos de confiança e tamanho de amostra

Para cada `risk_rank`, reportar:

```text
n
hit_rate
fail_rate
IC95%
```

A confiança do ajuste deve diminuir quando a amostra for insuficiente ou o intervalo de confiança for largo.

---

## 4. Shrinkage do ajuste histórico

Evitar aplicar integralmente lifts ruidosos.

Exemplo:

```text
lift_shrunk = 1 + alpha * (lift - 1)
```

com:

```text
0 <= alpha <= 1
```

`alpha` pode depender de:

```text
tamanho da amostra
largura do IC
HistoricalStability
recência
consistência entre janelas
```

O shrinkage só deve ser promovido por validação walk-forward.

---

## 5. Estabilidade do `risk_rank` por janelas

Comparar, por rank:

```text
últimos 50 concursos
últimos 100 concursos
últimos 200 concursos
histórico completo
```

Exemplo estável:

```text
risk_rank=5 Top1_fail:
50  -> 0.54
100 -> 0.55
200 -> 0.53
all -> 0.54
```

Exemplo instável:

```text
50  -> 0.42
100 -> 0.61
200 -> 0.49
all -> 0.55
```

Criar:

```text
RiskRankStability
```

O peso do ajuste deve cair quando a estabilidade for baixa.

---

## 6. Monotonicidade do risco

Como `risk_rank` é ordinal, testar se o risco histórico observado respeita aproximadamente:

```text
rank 1 >= rank 2 >= ... >= rank 14
```

em termos de `Top1_fail`.

Se houver inversões causadas por ruído amostral, testar calibração monotônica/isotônica como Challenger.

Nenhuma imposição monotônica deve ser promovida sem ganho fora da amostra.

---

## 7. Interação `risk_rank` + tipo de ranking

Testar cruzamentos como:

```text
risk_rank=3 + 1>X>2
risk_rank=3 + 1>2>X
risk_rank=3 + 2>X>1
```

Usar obrigatoriamente:

```text
minimum_sample
shrinkage
walk-forward
```

para evitar explosão de dimensionalidade e overfitting.

---

## 8. Interação `risk_rank` + gap12

Testar faixas/quantis de `gap12` dentro de cada `risk_rank`:

```text
rank 5 + gap12 baixo
rank 5 + gap12 médio
rank 5 + gap12 alto
```

Preferir buckets/percentis a limites escolhidos manualmente.

---

## 9. `risk_rank` + entropia ordinal

Criar:

```text
entropy_rank
rank_gap12
rank_gap13
```

E comparar com o uso das magnitudes contínuas.

A hipótese é que sinais ordinais podem preservar desempenho com menor dependência das probabilidades cruas.

---

# Métricas próprias do `risk_rank`

## RiskRankPrecision@5

```text
RiskRankPrecision@5 = Top1_fail entre os risk_ranks 1..5 / 5
```

Essa é uma métrica central porque a estrutura atual tende a usar exatamente 5 duplos `Top2+Top3`.

## RiskRankRecall@5

```text
RiskRankRecall@5 = Top1_fail capturados pelos ranks 1..5 / Top1_fail totais
```

## RiskRankNDCG@5

Testar NDCG@5 para avaliar a qualidade da ordenação, dando mais valor à posição correta das falhas no topo do ranking de risco.

## Ranking Change Success Rate

Quando a calibração histórica alterar o Top1 concreto:

```text
Top1_base -> Top1_ajustado
```

medir:

```text
n_ranking_changes
changes_correct
changes_wrong
ranking_change_success_rate
```

Pergunta:

> quando o histórico muda o Top1, essa intervenção melhora a taxa real de acerto?

---

# Backtest isolado do componente `risk_rank`

Comparar em walk-forward estrito:

```text
A = probabilidades brutas
B = + temperatura
C = + temperatura + risk_rank
```

Sem adicionar outras mudanças simultaneamente.

Relatório mínimo:

```text
Modelo
LogLoss
14
>=13
>=12
mean_hits
RecoveryRate
Precision@5
Recall@5
RiskRankPrecision@5
RiskRankRecall@5
```

O objetivo é medir a contribuição incremental específica do `risk_rank`.

---

# Promotion Gate do `risk_rank`

O componente só deve continuar implantado quando cumprir critérios fora da amostra.

Critérios desejáveis:

```text
1. log-loss não piora
2. hit_rate_13plus melhora ou permanece estatisticamente equivalente
3. hit_rate_12plus não piora materialmente
4. ganho não depende de um único período
5. RiskRankPrecision@5 apresenta sinal útil
6. mudanças de ranking não produzem deterioração sistemática
```

A melhora de log-loss isoladamente **não é suficiente** para justificar permanência se a aposta 9-5-5 piorar.

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
Top1_hit_rank5
Top1_hit_rank6
```

Classificar:

```text
ambos falharam
só rank5 falhou
só rank6 falhou
nenhum falhou
```

Calcular também:

```text
P(rank6 deveria substituir rank5 | margin_56 < 0.01)
P(rank6 deveria substituir rank5 | 0.01 <= margin_56 < 0.02)
P(rank6 deveria substituir rank5 | margin_56 >= 0.02)
```

---

# Pairwise da zona cinzenta

Em vez de prever todos os 14 jogos, testar um modelo especializado nos candidatos próximos ao cutoff.

Zona inicial sugerida:

```text
risk_rank 4..8
```

Problema pairwise:

```text
candidato A vs candidato B
qual merece maior prioridade para receber Top2+Top3?
```

Features preferenciais:

```text
delta_rank_pTop1
delta_gap_rank
delta_entropy_rank
tipo_ranking_A/B
historical_fail_A/B
RiskRankStability_A/B
HistoricalScore_A/B
HistoricalVote_A/B
regime do concurso
```

O modelo pairwise só deve atuar na zona cinzenta.

---

# HistoricalConfidence

Criar uma medida explícita de confiança histórica:

```text
HistoricalConfidence = f(
    tamanho_da_amostra,
    largura_IC,
    estabilidade_temporal,
    qualidade_KNN,
    consistência_entre_fontes
)
```

Telemetria:

```text
risk_rank=5
lift=...
HistoricalConfidence=HIGH/MEDIUM/LOW
```

O valor final deve ser contínuo internamente; rótulos são apenas para auditoria.

---

# Ajuste histórico adaptativo

A intensidade do histórico pode depender simultaneamente de:

```text
HistoricalConfidence
cutoff_uncertainty
```

Exemplo conceitual:

```text
adjustment_strength = HistoricalConfidence * CutoffUncertainty
```

Interpretação:

```text
fronteira ampla + histórico fraco     -> quase nenhuma interferência
fronteira estreita + histórico fraco  -> interferência moderada/baixa
fronteira ampla + histórico forte     -> interferência limitada
fronteira estreita + histórico forte  -> maior poder de desempate
```

---

# Múltiplos rankings de risco

Testar versões paralelas:

```text
risk_rank_prob      = rank por p(top1)
risk_rank_gap       = rank por gap12
risk_rank_entropy   = rank por entropia
risk_rank_history   = rank por HistoricalScore
risk_rank_consensus = rank por consenso
```

Comparar em walk-forward qual ranking melhor antecipa `Top1_fail`.

Nenhum deles deve substituir o Champion sem superar as métricas principais.

---

# Estratégias menos dependentes das probabilidades cruas

O objetivo não é eliminar probabilidades, mas reduzir dependência de pequenas diferenças numéricas quando a evidência atual é fraca.

## `PROBABILITY_ONLY`

```text
score_duplo = 1 - p(top1)
```

## `RANK_ONLY`

Usa as probabilidades somente para formar Top1/Top2/Top3 e posições ordinais.

## `HISTORICAL_ONLY`

Challenger diagnóstico que usa somente evidências históricas permitidas temporalmente.

Não é estratégia principal por padrão; serve para medir quanto do sinal está no histórico.

## `HYBRID_ORDINAL`

Usa:

```text
risk_rank
rank_gap12
rank_gap13
rank_entropy
HistoricalScore
HistoricalVote
HistoricalConfidence
```

sem depender diretamente das diferenças contínuas quando isso não agrega ganho fora da amostra.

---

# HistoricalScore e HistoricalVote

## HistoricalScore

Exemplo:

```text
HistoricalScore =
    w1 * historical_risk_rank
  + w2 * historical_ranking_type
  + w3 * historical_position
  + w4 * historical_knn_game
  + w5 * historical_regime
  + w6 * historical_recency
```

Preferir ranks, percentis ou scores normalizados.

Pesos somente por walk-forward.

## HistoricalVote

Fontes possíveis:

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

Manter voto histórico separado do voto probabilístico na telemetria.

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

Exibir:

```text
n_vizinhos
Top1_fail
Top1_hit
HistoricalVoteKNN
distância média
```

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

Analisar:

```text
quantidade de Top1_fail
distribuição por risk_rank
runs
falhas próximas ao cutoff
```

---

# Núcleo e zona cinzenta

Classificar os 14 jogos em:

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

O histórico não deve reabrir automaticamente decisões já muito robustas.

---

# Oracle histórico 9-5-5

Implementar `oracle_9_5_5` exclusivamente para diagnóstico retrospectivo.

O oracle pode usar o resultado real para encontrar a melhor aposta possível respeitando:

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

Classificação:

```text
SUCCESS
RECOVERABLE
UNRECOVERABLE
```

- `SUCCESS`: estratégia real atingiu 13+.
- `RECOVERABLE`: ficou abaixo de 13, mas existia aposta válida 9-5-5 capaz de atingir 13+.
- `UNRECOVERABLE`: nenhuma aposta válida sob as Hard Constraints conseguiria 13+.

```text
RecoveryRate = SUCCESS / (SUCCESS + RECOVERABLE)
```

---

# Análise 12 -> 13

Para concursos com exatamente 12 acertos, identificar a menor alteração necessária para chegar a 13.

Reportar:

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

Registrar:

```text
duplo que deveria sair
seco que deveria entrar
risk_rank
margin_56
tipo de ranking
gap/entropia ordinal
HistoricalScore
HistoricalVote
regime do concurso
```

---

# Métricas específicas dos duplos

```text
Precision@5 = falhas de Top1 entre os 5 duplos / 5
Recall@5 = falhas de Top1 capturadas pelos duplos / falhas de Top1 totais
CoverageFail = Recall@5
DoubleWasteRate = duplos em que Top1_hit=1 / 5
```

Objetivo auxiliar:

```text
maximizar CoverageFail
minimizar DoubleWasteRate
```

Essas métricas são diagnósticas; o objetivo principal continua sendo `>=13`.

---

# Fronteira 5º vs 6º

Exibir:

```text
Rank | Jogo | pTop1 | 1-pTop1 | risk_rank | Decisão
```

E calcular:

```text
P13+ original
P13+ após troca
Delta absoluto
Delta relativo
Margem pTop1
HistoricalScore 5º/6º
HistoricalVote 5º/6º
HistoricalConfidence 5º/6º
```

Separar:

```text
Fronteira probabilística
Evidência histórica
Robustez no objetivo
```

Uma margem pequena em `p(top1)` não implica impacto pequeno em `P13+`.

---

# Função objetivo

Objetivo principal:

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

Sob a hipótese de independência entre jogos, a distribuição pode ser calculada exatamente por programação dinâmica / Poisson-binomial.

A otimização não deve maximizar apenas soma de probabilidades individuais ou acurácia média.

---

# Matriz de trocas

Calcular o impacto de trocar cada duplo por cada seco compatível:

```text
Sai | Entra | Delta P13+ | Delta HistoricalScore | Delta Consensus
```

Isso permite visualizar a geometria completa da solução.

---

# Robustez

## Stability@5

Perturbar probabilidades, renormalizar e rerodar o seletor.

```text
Stability@5 = média da persistência dos 5 duplos escolhidos
```

## Rank Preservation Stress Test

1. preservar Top1/Top2/Top3;
2. comprimir/expandir magnitudes;
3. renormalizar;
4. rerodar;
5. medir `Agreement@5` e `Stability@5`.

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
calcula risk_rank e estatísticas históricas somente com dados permitidos
calcula HistoricalScore usando apenas concursos <= N-1
busca KNN apenas em concursos <= N-1
prevê concurso N
monta aposta N
avalia contra resultado real N
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

Como 13+ é raro, estimar incerteza por bootstrap no nível de concurso:

```text
hit_rate_13plus = ...
IC 95% = [... ; ...]
```

---

# Ablation study

Comparar progressivamente:

```text
A - probabilidades brutas
B - + temperatura
C - + risk_rank
D - + shrinkage risk_rank
E - + estabilidade risk_rank
F - + risk_rank x ranking_type
G - + risk_rank x gap/entropy ordinal
H - + HistoricalVote
I - + KNN jogo
J - + KNN concurso
K - + pairwise zona 4-8
L - + RECOVERABLE / 12->13
M - + consenso
N - + Soft Constraint Palmeiras
O - modelo completo
```

Relatório mínimo:

```text
Modelo | LogLoss | 14 | >=13 | >=12 | Média | RecoveryRate | Precision@5 | Recall@5 | RiskRankPrecision@5 | Stability@5
```

---

# Champion / Challenger

Manter formalmente:

```text
Champion = estratégia atualmente aprovada
Challenger = nova implementação em avaliação
```

Challengers possíveis:

```text
RISK_RANK_SHRINKAGE
RISK_RANK_ISOTONIC
RISK_RANK_INTERACTIONS
PAIRWISE_GRAY_ZONE
HISTORICAL_ONLY
HYBRID_ORDINAL
HYBRID_HISTORY_ADAPTIVE
KNN_HISTORY
CONSENSUS_HISTORY
```

O Challenger só deve ser promovido se superar o Champion em walk-forward segundo a hierarquia de métricas.

---

# Hierarquia de métricas

```text
1. hit_rate_13plus
2. hit_rate_12plus
3. RecoveryRate
4. Precision@5 / Recall@5 / CoverageFail
5. RiskRankPrecision@5 / RiskRankRecall@5
6. mean_hits
7. robustez / Stability@5
8. Agreement@5 / dependência probabilística
9. calibração / log-loss
```

O produto final é a aposta completa, não o estimador probabilístico isolado.

---

# Guardrail contra overfitting

> Nenhuma complexidade adicional deve entrar na estratégia principal sem demonstrar ganho fora da amostra sobre uma baseline mais simples.

Critérios:

- walk-forward estrito;
- amostra suficiente;
- melhoria em `>=13`;
- ausência de deterioração material em `>=12`;
- estabilidade por período;
- resultado não dependente de poucos concursos extremos;
- IC compatível com ganho plausível;
- shrinkage quando necessário;
- nenhuma informação futura em features/calibrações.

---

# Telemetria esperada

## Calibração

```text
Temperatura candidata
Temperatura implantada
LogLoss base/calibrado
Calibração Top1/2/3: promovida/rejeitada
Calibração risk_rank: promovida/rejeitada
LogLoss risk_rank base/calibrado
```

## Por partida

```text
Jogo
Mandante x Visitante
p_base(1/X/2)
p_ajustado(1/X/2)
top1/top2/top3 antes
top1/top2/top3 depois
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

## Tabela `risk_rank`

```text
risk_rank | n | pTop1 previsto | Top1 hit | Top1 fail | lift | IC95 | stability
```

## Fronteira

```text
5º candidato
6º candidato
margin_56
P13+ original
P13+ após troca
delta absoluto/relativo
HistoricalScore
HistoricalVote
HistoricalConfidence
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

Quando houver conflito:

```text
Melhor solução absoluta: P13+ = ...
Melhor solução sem vitória do Palmeiras: P13+ = ...
Custo da preferência: ...
```

A preferência só deve prevalecer quando o custo for aceitável dentro da estratégia.

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

### Responsabilidades

- `main.py`: orquestração e telemetria.
- `data/concursos_anteriores.csv`: histórico de treinamento, calibração e backtest.
- `data/proximo_concurso.csv`: concurso alvo.
- `scripts/preprocess_data.py`: leitura, validação e engenharia de features.
- `scripts/train_model.py`: treinamento, calibração, `risk_rank`, meta-modelos, histórico e avaliação walk-forward.
- `scripts/predict_results.py`: probabilidades, rankings, seletores, evidência histórica, otimização 9-5-5 e palpite final.
- `output/predictions.csv`: saída auditável.

---

# Formato dos CSVs

```text
delimitador: ;
separador decimal das odds: ,
```

Exemplo:

```python
pd.read_csv(caminho, sep=";", decimal=",")
```

---

# Convenção dos palpites

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
1. telemetria pTop1 base vs ajustado por risk_rank
2. tabela histórica risk_rank 1..14
3. n + IC95 por risk_rank
4. RiskRankStability por janelas
5. backtest isolado BASE vs TEMP vs TEMP+RISK_RANK
6. RiskRankPrecision@5 / RiskRankRecall@5
7. diagnóstico das mudanças de ranking causadas pelo histórico
8. cutoff histórico risk_rank 5 vs 6
9. shrinkage dos ajustes risk_rank
10. monotonic/isotonic calibration como Challenger
11. risk_rank + tipo de ranking
12. risk_rank + gap/entropia ordinal
13. HistoricalConfidence
14. pairwise da zona 4..8
15. múltiplos rankings de risco
16. HistoricalVote / KNN histórico
17. oracle_9_5_5
18. análise RECOVERABLE / 12->13
19. matriz de trocas
20. Stability@5 / stress tests
21. bootstrap de >=13
22. Champion / Challenger
23. ablation study contínuo
```

A prioridade imediata é **validar profundamente o `risk_rank` antes de adicionar complexidade adicional**.

---

# Perguntas experimentais centrais

> **A melhora do `risk_rank` persiste em walk-forward e em diferentes períodos, ou é apenas ruído de calibração?**

> **O `risk_rank` melhora de fato a escolha dos cinco duplos e a taxa real de 13+, além do pequeno ganho de log-loss?**

> **Quando o histórico altera o ranking concreto de uma partida, essa intervenção aumenta ou diminui a taxa real de acerto?**

> **O histórico consegue resolver melhor a fronteira 5º/6º e recuperar concursos de 12 para 13 sem overfitting?**

> **Quanto da qualidade atual pode ser preservado usando sinais relativos/ordinais em vez das probabilidades cruas?**

---

# Regras fundamentais

> **As Hard Constraints têm precedência absoluta sobre qualquer Soft Constraint, heurística, calibração ou preferência.**

> **A métrica decisiva é a qualidade da aposta completa para atingir pelo menos 13 acertos, validada fora da amostra.**

> **Melhorar log-loss é útil, mas não substitui melhora real de 13+.**

> **Valorizar o histórico só é melhoria se aumentar ou preservar o desempenho real de 13+ em walk-forward.**

> **Reduzir dependência das probabilidades só é melhoria se preservar ou aumentar o desempenho real de 13+.**