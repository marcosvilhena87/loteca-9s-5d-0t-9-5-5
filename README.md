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

6. Exibir telemetria suficiente para auditar probabilidades, ranking, secos, duplos, restrições, cutoff, robustez, consenso entre seletores, evidência histórica e critérios da aposta final.

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

# Histórico vs. próximo concurso

O projeto deve tratar o histórico como **segunda fonte explícita de decisão**, e não apenas como material usado para treinar probabilidades.

## Histórico

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
- comportamento por `risk_rank` dentro do concurso;
- padrões dos concursos que produziram 13+;
- padrões dos concursos `RECOVERABLE`;
- padrões de falha do Top1;
- comportamento específico da zona de cutoff;
- estabilidade das evidências em diferentes janelas temporais.

## Próximo concurso

Para cada partida de `data/proximo_concurso.csv`, produzir:

```text
p(1), p(X), p(2)
p(top1), p(top2), p(top3)
```

As probabilidades podem ser usadas em diferentes níveis de intensidade. O projeto deve testar se a magnitude exata das probabilidades realmente melhora `>=13` em relação a estratégias que utilizam ranking, faixas, estrutura, histórico e consenso.

---

# Valorizar concursos anteriores

A estratégia deve testar formalmente se os concursos anteriores conseguem melhorar a escolha dos 5 duplos, principalmente quando as probabilidades atuais são pouco conclusivas.

Princípio preferencial:

```text
presente define o contexto
histórico resolve a dúvida
```

O histórico não deve substituir cegamente as probabilidades. Ele deve ganhar influência especialmente na **zona cinzenta**, no cutoff e nos casos em que diferentes sinais atuais discordam.

## HistoricalScore por jogo

Criar um score histórico independente das probabilidades atuais.

Exemplo conceitual:

```text
HistoricalScore =
    w1 * historical_risk_rank
  + w2 * historical_ranking_type
  + w3 * historical_position
  + w4 * historical_knn_game
  + w5 * historical_regime
  + w6 * historical_recency
```

Preferir componentes transformados em ranks, percentis ou scores normalizados.

Nenhum peso deve ser escolhido olhando o concurso alvo. Pesos só podem ser definidos por validação walk-forward.

---

## Histórico específico do cutoff 5º/6º

Para cada concurso histórico, armazenar:

```text
candidate_rank5
candidate_rank6
pTop1_rank5
pTop1_rank6
margin_56
top1_hit_rank5
top1_hit_rank6
cutoff_winner
```

Calcular estatísticas condicionais como:

```text
P(rank6 melhor que rank5 | margin_56 < 0.01)
P(rank6 melhor que rank5 | 0.01 <= margin_56 < 0.02)
P(rank6 melhor que rank5 | margin_56 >= 0.02)
```

O objetivo é aprender quando a ordem probabilística entre 5º e 6º é pouco confiável.

---

## Histórico do `risk_rank` 1..14

Ordenar os jogos de cada concurso histórico pelo risco de falha do Top1 e guardar a posição relativa:

```text
risk_rank = 1..14
```

Medir:

```text
P(top1_fail | risk_rank=1)
P(top1_fail | risk_rank=2)
...
P(top1_fail | risk_rank=14)
```

Esse sinal é especialmente importante por depender mais da **posição relativa** que da magnitude exata de `p(top1)`.

---

## Histórico por tipo de ranking

Existem seis ordenações possíveis:

```text
1 > X > 2
1 > 2 > X
X > 1 > 2
X > 2 > 1
2 > 1 > X
2 > X > 1
```

Para cada tipo, medir:

```text
Top1 hit rate
Top2 hit rate
Top3 hit rate
Top1 fail rate
```

Também testar cruzamentos com:

```text
risk_rank
classe de equilíbrio
posição
gap12 por faixa
entropia por faixa
```

---

## Histórico específico do empate

Separar o comportamento de:

```text
X como Top1
X como Top2
X como Top3
```

Medir taxas reais de ocorrência e estabilidade temporal.

Esse diagnóstico é relevante porque muitos duplos da estrutura atual contêm empate (`1X` ou `X2`).

---

## KNN histórico por jogo

Para cada jogo atual, buscar jogos históricos semelhantes usando preferencialmente variáveis estruturais:

```text
tipo_de_ranking
risk_rank
pTop1_percentile
gap12_percentile
gap13_percentile
entropy_percentile
posição
```

Em vez de obrigatoriamente converter o resultado em uma nova probabilidade absoluta, o KNN pode gerar um voto auditável:

```text
20 vizinhos
12 Top1_fail
8 Top1_hit
HistoricalVoteKNN = 12/20
```

Registrar também o número efetivo de vizinhos e a distância média para evitar confiança excessiva em vizinhanças ruins.

---

## KNN histórico por concurso

Representar cada concurso por uma assinatura global, por exemplo:

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

Buscar concursos históricos semelhantes ao atual e analisar:

```text
quantidade de Top1_fail
posição das falhas
distribuição por risk_rank
estrutura das runs
falhas próximas ao cutoff
```

O KNN de concurso deve ser comparado com o KNN por jogo; ambos podem votar separadamente no `HistoricalVote`.

---

## Recência ponderada

O histórico deve ser analisado em múltiplas janelas, por exemplo:

```text
últimos 50 concursos
últimos 100 concursos
últimos 200 concursos
histórico completo
```

Opcionalmente testar pesos de recência, por exemplo:

```text
0-50      -> 1.00
51-150    -> 0.70
151-300   -> 0.40
mais antigo -> 0.20
```

Os pesos são hipóteses e só podem ser promovidos se melhorarem resultados fora da amostra.

---

## HistoricalStability

Criar uma medida de estabilidade do sinal histórico entre janelas temporais.

Exemplo conceitual:

```text
Top1_fail do perfil:
últimos 50   = 0.58
últimos 100  = 0.56
histórico    = 0.55
```

Sinal estável.

Exemplo instável:

```text
últimos 50   = 0.44
últimos 100  = 0.62
histórico    = 0.51
```

O peso histórico deve cair quando a dispersão entre janelas for elevada.

Definição possível:

```text
HistoricalStability = 1 - dispersão_normalizada_das_janelas
```

A fórmula final deve ser validada em walk-forward.

---

## Peso histórico adaptativo

O histórico não precisa ter peso fixo.

Regra experimental conceitual:

```text
fronteira probabilística larga  -> peso histórico baixo
fronteira intermediária         -> peso histórico moderado
fronteira estreita               -> peso histórico maior
```

Exemplo inicial:

```text
margin_56 > 0.03          -> hist_weight = 0.10
0.01 < margin_56 <= 0.03  -> hist_weight = 0.30
margin_56 <= 0.01         -> hist_weight = 0.50
```

Esses valores são apenas challengers experimentais.

O peso histórico efetivo também pode ser multiplicado por `HistoricalStability`, reduzindo automaticamente a influência de sinais históricos instáveis.

---

## HistoricalVote

Criar votos independentes a partir de diferentes fontes históricas:

```text
H1 = histórico do risk_rank
H2 = histórico do tipo de ranking
H3 = histórico da posição
H4 = KNN por jogo
H5 = KNN por concurso
H6 = recência / estabilidade
H7 = pattern matching
H8 = histórico de RECOVERABLE / 12->13
```

Exemplo:

```text
J6: 6 votos históricos
J3: 4 votos históricos
J8: 2 votos históricos
```

O voto histórico deve ficar separado do voto probabilístico na telemetria para permitir auditoria.

---

## Histórico como desempate

Filosofia preferencial para a primeira versão:

```text
probabilidade / estrutura -> define núcleo
histórico                 -> resolve zona cinzenta
```

Exemplo conceitual:

```text
Núcleo de duplos: J1 J13 J14 J4
Zona cinzenta:    J6 J3 J8
```

O histórico decide a vaga restante sem precisar reavaliar decisões muito robustas em todo o volante.

---

## Pattern matching de falhas

Representar cada concurso histórico como sequência:

```text
F A A F A F ...
```

onde:

```text
F = top1_fail
A = top1_hit
```

Estudar:

```text
quantidade de falhas
posição da primeira falha
posição da última falha
runs de acertos
runs de falhas
distância entre falhas
concentração das falhas
```

Também agrupar concursos em templates como:

```text
falhas concentradas no início
falhas concentradas no meio
falhas tardias
falhas dispersas
muitas falhas
poucas falhas
```

O próximo concurso pode ser comparado com esses templates usando somente informações disponíveis antes do resultado.

---

## Prior histórico para quantidade de falhas

Estimar historicamente:

```text
P(n_top1_fail = k)
```

A estratégia pode ser dividida em duas etapas:

```text
1. estimar quantas falhas de Top1 são plausíveis
2. estimar onde as falhas são mais prováveis
```

Esse prior é diagnóstico e não deve forçar uma quantidade fixa de falhas.

---

## Valorizar concursos `RECOVERABLE`

O `oracle_9_5_5` deve permitir separar:

```text
SUCCESS
RECOVERABLE
UNRECOVERABLE
```

O desenvolvimento do seletor deve dar atenção especial aos concursos `RECOVERABLE`, pois são os casos em que 13+ era estruturalmente possível, mas a estratégia falhou na escolha das marcações.

Criar relatórios específicos para esse subconjunto:

```text
risk_rank dos duplos corretos
cutoff correto vs escolhido
tipo de ranking dos erros
diferença de HistoricalScore
diferença de consenso
quantidade mínima de trocas
```

---

## Dataset específico 12 -> 13

Criar um dataset dedicado aos concursos em que:

```text
acertos_modelo = 12
acertos_oracle >= 13
```

Para cada caso, registrar:

```text
duplo que deveria sair
seco que deveria entrar
risk_rank de ambos
margin do cutoff
tipo de ranking
gap12 / entropia por faixa
HistoricalScore
HistoricalVote
KNN vote
regime do concurso
```

Esse dataset pode alimentar um modelo pairwise especializado na recuperação de 12 para 13.

---

## Modelo pairwise histórico da zona cinzenta

Para dois candidatos próximos, treinar a pergunta:

```text
qual dos dois merece maior prioridade para Top2+Top3?
```

Exemplo:

```text
J6 vs J3
```

O modelo pode usar diferenças ordinais entre:

```text
risk_rank
gap_rank
entropy_rank
HistoricalScore
HistoricalVote
KNN vote
regime
```

Preferir esse modelo apenas na zona cinzenta.

---

# Estratégias com menor dependência das probabilidades

Uma linha prioritária de pesquisa é tornar a decisão dos 5 duplos **menos dependente de pequenas diferenças numéricas** entre probabilidades estimadas.

O objetivo não é eliminar as probabilidades, mas reduzir a dependência de sua magnitude exata quando a evidência é fraca.

## Modos experimentais de seleção

### `PROBABILITY_ONLY`

Usa as probabilidades contínuas completas como principal sinal.

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

Pode usar:

- posição;
- tipo de ranking;
- frequência histórica de `top1_hit`;
- runs;
- regime estrutural;
- `HistoricalVote`.

### `HYBRID_ORDINAL`

Modo preferencial de pesquisa.

Usa probabilidades para formar rankings e classes, mas evita depender diretamente de diferenças pequenas entre valores contínuos.

Pode usar:

```text
rank_pTop1
rank_gap12
rank_gap13
rank_entropy
rank_historical_fail
HistoricalScore
HistoricalStability
HistoricalVote
```

---

## Ranking estrutural das probabilidades

Além de `p(top1)`, utilizar:

```text
gap12 = p(top1) - p(top2)
gap23 = p(top2) - p(top3)
gap13 = p(top1) - p(top3)
entropy = entropia de p(1), p(X), p(2)
```

Dois jogos com `p(top1)` semelhante podem ter riscos diferentes se um possuir Top1 muito próximo do Top2 e outro apresentar separação maior.

---

## Dependência por faixas e percentis

Testar discretização das probabilidades em classes e quantis históricos.

Exemplo inicial:

```text
p(top1) < 0.40       -> muito equilibrado
0.40 <= p < 0.47     -> equilibrado
0.47 <= p < 0.55     -> favorito moderado
0.55 <= p < 0.65     -> favorito forte
p(top1) >= 0.65      -> favorito extremo
```

Também criar:

```text
percentil_pTop1
percentil_gap12
percentil_entropy
```

Os limites devem ser definidos exclusivamente com dados disponíveis no treino.

---

## Consenso entre seletores

Implementar seletores independentes:

```text
A = 5 menores p(top1)
B = 5 menores gap12
C = 5 maiores entropias
D = HistoricalVote
E = RANK_ONLY
F = HYBRID_ORDINAL
G = meta-modelo da zona cinzenta
```

Cada jogo recebe votos conforme a quantidade de métodos que o selecionam.

Manter separados:

```text
CurrentEvidenceVotes
HistoricalVotes
TotalConsensusVotes
```

---

## Núcleo robusto e zona cinzenta

Classificar os jogos em:

```text
núcleo_duplo
zona_cinzenta
núcleo_seco
```

O modelo histórico deve concentrar maior capacidade decisória na zona cinzenta.

---

## Historical Pattern Matching

Guardar para cada concurso histórico:

```text
estrutura de ranking das 14 partidas
sequência real T1/T2/T3
assinatura global do concurso
```

Comparar o próximo concurso com concursos históricos semelhantes e estimar onde o Top1 historicamente falhou.

Testar:

- versão sem magnitudes probabilísticas;
- versão híbrida usando apenas faixas/percentis.

---

## Score ordinal

Exemplo conceitual:

```text
ScoreOrdinal =
    w1 * rank_pTop1
  + w2 * rank_gap12
  + w3 * rank_entropy
  + w4 * rank_historical_fail
  + w5 * rank_HistoricalVote
```

Os pesos devem ser escolhidos apenas em validação walk-forward.

---

## Agreement@5

```text
Agreement@5(A, B) = jogos em comum entre os dois Top-5 / 5
```

Usar para comparar:

```text
PROBABILITY_ONLY vs RANK_ONLY
PROBABILITY_ONLY vs HYBRID_ORDINAL
PROBABILITY_ONLY vs HISTORICAL_ONLY
HISTORICAL_ONLY vs HYBRID_ORDINAL
```

---

## Rank Preservation Stress Test

1. manter o ranking Top1/Top2/Top3;
2. comprimir/expandir diferenças probabilísticas;
3. renormalizar;
4. rerodar o seletor;
5. medir `Agreement@5` e `Stability@5`.

Se o ranking permanece, mas a seleção muda excessivamente, existe dependência alta da magnitude probabilística.

---

## Temperature Stress Test

Como diagnóstico, testar temperaturas como:

```text
T = 0.70
T = 0.90
T = 1.00
T = 1.20
T = 1.50
```

Medir:

```text
Agreement@5
Stability@5
mudança no núcleo
mudança na zona cinzenta
```

O teste não deve alterar automaticamente a temperatura implantada.

---

# Fronteira dos duplos

Ordenar os 14 jogos pelo risco de falha do Top1 e destacar o 5º e 6º candidatos.

Calcular:

```text
P13+ original
P13+ após trocar o 5º pelo 6º
Delta absoluto
Delta relativo
Margem pTop1
HistoricalScore dos dois
HistoricalVote dos dois
HistoricalStability dos dois
```

Separar sempre:

```text
Fronteira probabilística
Evidência histórica
Robustez no objetivo
```

Uma margem pequena em `p(top1)` não implica necessariamente impacto pequeno em `P13+`.

---

# Backtest e diagnóstico estrutural

## Baseline

```text
9 maiores p(top1) -> Top1 seco
5 menores p(top1) -> Top2+Top3
```

Comparar em walk-forward contra:

```text
PROBABILITY_ONLY
RANK_ONLY
HISTORICAL_ONLY
HYBRID_ORDINAL
CONSENSUS
otimizador completo
```

Métricas mínimas:

```text
14 acertos
>=13 acertos
>=12 acertos
média
mediana
Precision@5
Recall@5
CoverageFail
DoubleWasteRate
Agreement@5
Stability@5
RecoveryRate
```

---

## Oracle histórico 9-5-5

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

```text
Precision@5 = falhas de Top1 entre os 5 duplos / 5
Recall@5 = falhas de Top1 capturadas pelos duplos / falhas de Top1 totais
CoverageFail = Recall@5
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

Priorizar candidatos próximos ao cutoff, por exemplo ranks 4 a 8.

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
risk_rank
distance_to_cutoff
HistoricalScore
HistoricalVote
HistoricalStability
KNN_game_vote
KNN_contest_vote
regime
```

---

## Learning to Rank

Testar ranking dos 14 jogos pelo risco de falha do Top1.

Métricas:

```text
Precision@5
Recall@5
NDCG@5
```

Comparar features contínuas, ordinais e históricas.

---

## Matriz de trocas

Calcular o impacto de trocar cada duplo por cada seco compatível com as Hard Constraints.

```text
Sai | Entra | Delta P13+ | Delta HistoricalScore | Delta Consensus
```

Isso permite visualizar a geometria completa da solução.

---

## Robustez e Stability@5

Perturbar probabilidades, renormalizar e rerodar o seletor.

```text
Stability@5 = média da persistência dos 5 duplos escolhidos
```

Robustez deve ser analisada junto com `>=13`.

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

# Walk-forward e prevenção de leakage

Fluxo obrigatório:

```text
treina até concurso N-1
calibra usando apenas dados disponíveis até N-1
calcula HistoricalScore usando apenas concursos <= N-1
busca KNN usando apenas concursos <= N-1
prevê concurso N
monta a aposta de N
avalia contra o resultado real de N
avança para N+1
```

Probabilidades, estatísticas históricas, KNN, recência, templates, pesos e meta-features devem respeitar integralmente esse corte temporal.

---

## Validação por período

Reportar resultados por janelas:

```text
últimos 50 concursos
51-100 anteriores
101-200 anteriores
histórico completo
```

Uma estratégia só deve ser considerada robusta se o ganho não depender de um único período.

---

## Bootstrap da taxa de 13+

Como 13+ é raro, estimar a incerteza por bootstrap no nível de concurso.

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
D - HISTORICAL_ONLY
E - HYBRID_ORDINAL
F - + HistoricalVote
G - + KNN por jogo
H - + KNN por concurso
I - + HistoricalStability / recência
J - + meta-modelo zona cinzenta
K - + Historical Pattern Matching
L - + regime de concurso
M - + Soft Constraint Palmeiras
N - modelo completo
```

Relatório mínimo:

```text
Modelo | 14 | >=13 | >=12 | Média | RecoveryRate | Precision@5 | Recall@5 | Agreement@5 | Stability@5
```

---

# Champion / Challenger

Manter:

```text
Champion = estratégia atualmente aprovada
Challenger = nova implementação em avaliação
```

Exemplos de Challengers:

```text
HISTORICAL_ONLY
HYBRID_ORDINAL
HYBRID_HISTORY_ADAPTIVE
PAIRWISE_GRAY_ZONE
KNN_HISTORY
CONSENSUS_HISTORY
```

O Challenger só deve ser promovido se superar o Champion em walk-forward.

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
- intervalo de confiança compatível com ganho plausível;
- nenhum uso indireto do resultado futuro em estatísticas históricas.

---

# Função objetivo

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

O histórico pode alterar a **ordenação/prioridade das soluções**, mas nenhuma abordagem histórica deve ser promovida apenas por parecer intuitiva.

---

# Telemetria esperada

## Por partida

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
risk_rank
rank_pTop1
rank_gap12
rank_entropy
HistoricalScore
HistoricalVote
HistoricalStability
KNN_game_vote
KNN_contest_vote
CurrentEvidenceVotes
TotalConsensusVotes
grupo: núcleo_duplo / zona_cinzenta / núcleo_seco
tipo: seco ou duplo
palpite
cobertura
motivo da escolha
```

## Evidência histórica

```text
Fonte histórica | Voto | Amostra | Taxa Top1_fail | Estabilidade
risk_rank
ranking_type
position
KNN_game
KNN_contest
recency
pattern_match
recoverable_12to13
```

## Consenso dos seletores

```text
Jogo | Prob | Gap12 | Entropia | Histórico | RankOnly | Hybrid | Votos
```

Exibir:

```text
Núcleo robusto dos duplos
Zona cinzenta
Núcleo robusto dos secos
Agreement@5
```

## Fronteira

```text
5º candidato
6º candidato
margem pTop1
delta P13+
HistoricalScore 5º/6º
HistoricalVote 5º/6º
HistoricalStability 5º/6º
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
- `scripts/train_model.py`: treinamento, calibração, meta-modelos, histórico e avaliação walk-forward.
- `scripts/predict_results.py`: probabilidades, ranking, seletores, evidência histórica, otimização 9-5-5 e palpite final.
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

# Ordem recomendada de implementação

```text
1. histórico do cutoff 5º/6º
2. histórico do risk_rank 1..14
3. histórico dos 6 tipos de ranking
4. HistoricalVote
5. KNN histórico por jogo
6. KNN histórico por concurso
7. HistoricalStability por janelas
8. peso histórico adaptativo
9. análise específica de RECOVERABLE
10. dataset 12 -> 13
11. pairwise histórico da zona cinzenta
12. Historical Pattern Matching
13. modos PROBABILITY_ONLY / RANK_ONLY / HISTORICAL_ONLY / HYBRID_ORDINAL
14. consenso dos seletores
15. núcleo / zona cinzenta / núcleo seco
16. Agreement@5
17. Rank Preservation Stress Test
18. backtest comparativo dos modos
19. oracle_9_5_5
20. Precision@5 / Recall@5 / CoverageFail / DoubleWasteRate
21. meta-modelo da zona cinzenta
22. matriz de trocas
23. Stability@5
24. bootstrap de >=13
25. Champion / Challenger
26. learning to rank
27. Monte Carlo robusto
28. ablation study contínuo
```

As perguntas experimentais centrais são:

> **O esquema 9-5-5 está estruturalmente limitando o desempenho, ou o sistema ainda está escolhendo os cinco duplos errados?**

> **Quanto da qualidade atual vem da magnitude das probabilidades, e quanto pode ser preservado ou melhorado usando ranking, histórico, estrutura e consenso?**

> **Os concursos anteriores conseguem resolver melhor a zona cinzenta e recuperar casos de 12 para 13 sem provocar overfitting?**

---

# Regra fundamental

> **As Hard Constraints têm precedência absoluta sobre qualquer Soft Constraint, heurística ou preferência.**

> **A métrica decisiva do projeto é a qualidade da aposta completa para atingir pelo menos 13 acertos, validada fora da amostra.**

> **Valorizar o histórico só é melhoria se aumentar ou preservar o desempenho real de 13+ em walk-forward.**

> **Reduzir dependência das probabilidades só é melhoria se preservar ou aumentar o desempenho real de 13+.**