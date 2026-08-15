# Loteca 9S-5D-0T — Estratégia 9-5-5

Projeto para geração de **um único palpite final por concurso da Loteca**, usando o histórico de `data/concursos_anteriores.csv` e as probabilidades do próximo concurso para maximizar prioritariamente:

```text
P(acertos >= 13)
```

O projeto deve respeitar integralmente as Hard Constraints e usar as Soft Constraints apenas como preferências subordinadas ao objetivo probabilístico principal.

---

## Estratégia

1. Gerar um único palpite final por concurso, otimizado para maximizar a probabilidade de atingir pelo menos 13 acertos.
2. Representar as probabilidades dos três resultados possíveis de cada partida como:
   - `p(1)`: vitória do mandante;
   - `p(X)`: empate;
   - `p(2)`: vitória do visitante.
3. Derivar `p(top1)`, `p(top2)` e `p(top3)` ordenando `p(1)`, `p(X)` e `p(2)` da maior para a menor.
4. Em caso de probabilidades iguais, usar obrigatoriamente o desempate:

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

6. Exibir no terminal telemetria suficiente para auditar probabilidades, ranking, secos, duplos, restrições, cutoff dos duplos, robustez e critérios que levaram à aposta final.

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

Essa validação deve ser feita sobre o resultado real `1`, `X` ou `2`, independentemente de ele ocupar Top1, Top2 ou Top3.

---

## Soft Constraints

1. Favorecer ordenações que antecipem e concentrem resultados Top1, especialmente nas 9 primeiras posições, privilegiando runs longas e baixa fragmentação.
2. Favorecer soluções que excluam a vitória do **PALMEIRAS/SP**, priorizando empate ou derrota quando isso não comprometer significativamente a qualidade global da aposta.
3. Soft Constraints nunca podem relaxar Hard Constraints.
4. O custo probabilístico de aplicar uma Soft Constraint deve ser mensurável e exibido quando relevante.

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

Essa baseline **não é uma regra obrigatória**. Ela é a referência que qualquer abordagem mais sofisticada deve superar fora da amostra.

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

Essa compensação estrutural deve ser considerada pelo otimizador global.

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
- runs de Top1;
- fragmentação;
- transições entre Top1/Top2/Top3;
- comportamento por faixa de `p(top1)`, `p(top2)` e `p(top3)`;
- perfis probabilísticos semelhantes;
- calibração histórica dos ranks.

### Próximo concurso

Para cada partida de `data/proximo_concurso.csv`, produzir:

```text
p(1), p(X), p(2)
p(top1), p(top2), p(top3)
```

O histórico deve ajudar a contextualizar o risco; as probabilidades atuais determinam o custo probabilístico concreto de cada marcação.

---

## Fronteira dos duplos

O terminal deve ordenar os 14 jogos pelo risco de falha do Top1 e destacar a fronteira entre o 5º e o 6º candidato.

Exemplo:

```text
Rank | Jogo | pTop1 | 1-pTop1 | Decisão
1    | ...  | ...   | ...     | DUPLO
...
5    | ...  | ...   | ...     | DUPLO  <- cutoff
6    | ...  | ...   | ...     | SECO   <- cutoff
```

Também calcular:

```text
P13+ original
P13+ após trocar o 5º pelo 6º
Delta absoluto
Delta relativo
```

### Diagnóstico da fronteira

Não usar um único rótulo como `FRÁGIL / QUASE EMPATE` baseado apenas em `p(top1)`.

Separar dois conceitos:

```text
Margem probabilística:
abs(pTop1_6 - pTop1_5)

Impacto no objetivo:
Delta relativo de P13+
```

Exemplo de telemetria:

```text
Margem pTop1: 0.0098
Delta P13+: -3.2915% relativo

Fronteira probabilística: ESTREITA
Robustez no objetivo: MATERIAL
```

Uma fronteira pode ser estreita nas probabilidades individuais e, ainda assim, ter impacto material em `P(acertos >= 13)`.

---

## Backtest da baseline

Implementar explicitamente:

```text
9 maiores p(top1) -> Top1 seco
5 menores p(top1) -> Top2+Top3
```

Comparar em walk-forward contra o otimizador completo.

Métricas mínimas:

```text
14 acertos
>=13 acertos
>=12 acertos
média de acertos
mediana de acertos
distribuição de 0 a 14
```

A métrica principal de seleção de estratégia é o desempenho real de `>=13` fora da amostra.

---

## Oracle histórico 9-5-5

Implementar um `oracle_9_5_5` exclusivamente para diagnóstico retrospectivo.

O oracle pode usar o resultado real do concurso histórico para encontrar a melhor aposta possível que respeite integralmente:

```text
9 secos
5 duplos
0 triplos
9 Top1
5 Top2
5 Top3
Flamengo obrigatório, quando aplicável
```

O oracle **nunca pode ser usado na geração do próximo concurso**. Sua função é medir o teto estrutural da estratégia e identificar o espaço real de melhoria do seletor.

### Classificação dos concursos

Cada concurso histórico deve ser classificado como:

```text
SUCCESS
RECOVERABLE
UNRECOVERABLE
```

Definições:

- `SUCCESS`: a estratégia real obteve pelo menos 13 acertos.
- `RECOVERABLE`: a estratégia real ficou abaixo de 13, mas existia alguma aposta válida 9-5-5 capaz de atingir 13+.
- `UNRECOVERABLE`: nenhuma aposta válida sob as Hard Constraints conseguiria atingir 13+ naquele concurso.

### Recovery Rate

Uma métrica útil é:

```text
RecoveryRate = SUCCESS / (SUCCESS + RECOVERABLE)
```

Ela mede a capacidade do seletor de capturar oportunidades que eram estruturalmente possíveis sob 9-5-5.

---

## Análise 12 -> 13

Para cada concurso em que a estratégia fizer exatamente 12 acertos, identificar a menor alteração necessária para atingir 13.

Exemplo:

```text
Modelo:
duplos = J1 J4 J6 J13 J14

Oracle:
duplos = J1 J3 J4 J13 J14

Mudança mínima:
J6 -> seco
J3 -> duplo
```

Acumular:

```text
% recuperável com 1 troca
% recuperável com 2 trocas
% recuperável com 3+ trocas
```

Essa análise deve mostrar se o principal problema está concentrado na zona de cutoff ou se o seletor erra de forma mais ampla.

---

## Regret do seletor

Criar métricas de arrependimento retrospectivo:

```text
RegretHits = acertos_oracle - acertos_modelo
```

E, quando comparável ex ante entre candidatos:

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

## Métricas específicas do seletor de duplos

Como a configuração estrutural tende a usar `Top2+Top3`, o seletor deve ser avaliado também como um ranking de falhas do Top1.

### Precision@5

```text
Precision@5 = falhas de Top1 entre os 5 duplos / 5
```

### Recall@5

```text
Recall@5 = falhas de Top1 capturadas pelos duplos / falhas de Top1 totais
```

### CoverageFail

```text
CoverageFail = Top1 failures nos jogos duplos / Top1 failures totais
```

### Double Waste Rate

Um duplo `Top2+Top3` é desperdiçado quando o Top1 vence.

```text
DoubleWasteRate = duplos em que Top1_hit=1 / 5
```

O seletor deve buscar simultaneamente:

```text
maximizar CoverageFail
minimizar DoubleWasteRate
```

---

## Decomposição dos erros

Separar os erros em duas classes:

```text
Erro de seco:
Top1 seco, resultado real = Top2 ou Top3

Erro de duplo:
Top2+Top3, resultado real = Top1
```

Reportar por concurso e no agregado:

```text
erros_secos_top1
erros_duplos_por_top1_hit
```

Isso ajuda a identificar se o seletor está protegendo jogos demais ou de menos.

---

## Cutoff histórico

Armazenar, para cada concurso walk-forward:

```text
pTop1_5
pTop1_6
margin_56
delta_P13_swap_56
top1_hit_5
top1_hit_6
```

Objetivo:

> aprender quando o 6º candidato deveria substituir o 5º, principalmente em fronteiras estreitas.

---

## Meta-modelo da zona cinzenta

Em vez de treinar apenas um modelo global, priorizar um meta-modelo para candidatos próximos ao cutoff, por exemplo ranks 4 a 8 de risco.

Alvo:

```text
top1_fail = 1 - top1_hit
```

Features candidatas:

```text
p_top1
p_top2
p_top3
gap12
gap23
gap13
entropy
rank_no_concurso
distance_to_cutoff
ranking concreto 1/X/2
features de regime do concurso
```

A finalidade é distinguir jogos com `p(top1)` semelhantes, mas risco histórico diferente de falha do Top1.

---

## Learning to Rank

Também deve ser testada uma abordagem de ranking dos 14 jogos pelo risco de falha do Top1.

Métricas recomendadas:

```text
Precision@5
Recall@5
NDCG@5
```

A pergunta central é:

> Dos cinco jogos classificados como maior risco de falha do Top1, em quantos o Top1 realmente falhou?

---

## Features de incerteza

Além de `p_top1`, `p_top2` e `p_top3`, testar:

```text
gap12 = p_top1 - p_top2
gap23 = p_top2 - p_top3
gap13 = p_top1 - p_top3
entropy = entropia de p(1), p(X), p(2)
```

Também podem ser avaliados:

- resultado concreto que ocupa Top1/Top2/Top3 (`1`, `X`, `2`);
- posição da partida no concurso;
- média e mediana de `p(top1)`;
- quantidade de favoritos fortes;
- quantidade de jogos equilibrados;
- dispersão das probabilidades;
- perfil probabilístico do concurso inteiro.

---

## Calibração por rank

Além da calibração global, auditar:

```text
p(top1) previsto vs frequência real de top1_hit
p(top2) previsto vs frequência real de top2_hit
p(top3) previsto vs frequência real de top3_hit
```

A análise deve ser feita por faixas e em walk-forward.

Definição possível:

```text
HistoricalLiftTopK = frequencia_real_topK_hit / probabilidade_media_prevista_topK
```

O lift deve ser diagnóstico ou feature, nunca correção automática sem validação fora da amostra.

---

## Historical Lift de falha do Top1

```text
LiftFail = P_hist(Top1 falha | faixa/perfil) / (1 - p(top1))
```

Valores acima de 1 sugerem que o modelo historicamente subestima a falha do Top1 naquele perfil; valores abaixo de 1 sugerem o contrário.

---

## Regime do concurso

Representar cada concurso por um vetor como:

```text
mean_top1
median_top1
min_top1
max_top1
mean_entropy
mean_gap12
n_top1_above_60
n_top1_below_45
n_jogos_equilibrados
```

Essas informações podem ser usadas para localizar concursos históricos semelhantes, inclusive por KNN.

---

## Matriz de trocas

Para o próximo concurso, calcular o impacto de trocar cada duplo por cada seco compatível com as Hard Constraints.

Exemplo:

```text
Sai | Entra | Delta P13+
J6   | J3    | ...
J6   | J8    | ...
J4   | J3    | ...
```

Isso permite visualizar a geometria completa da solução, não apenas o cutoff 5º/6º.

---

## Robustez e Stability@5

Perturbar as probabilidades em magnitudes como:

```text
+/- 0,5%
+/- 1%
+/- 2%
```

renormalizar e rodar novamente o otimizador.

Reportar a frequência com que cada jogo permanece entre os 5 duplos.

Exemplo:

```text
J1 100%
J13 98%
J14 91%
J4 81%
J6 56%
J3 entra em 42%
```

Criar também:

```text
Stability@5 = média da persistência dos 5 duplos escolhidos
```

---

## Monte Carlo sobre incerteza das probabilidades

Como evolução da análise de sensibilidade, simular múltiplos vetores probabilísticos plausíveis e medir:

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

com eventual penalização para soluções excessivamente instáveis.

---

## Ensemble de rankings

Testar combinação de rankings independentes:

```text
rank_probabilidade
rank_meta_modelo
rank_entropy
rank_historical_lift
```

Exemplo conceitual:

```text
Score = w1*R_prob + w2*R_meta + w3*R_hist
```

Os pesos devem ser escolhidos exclusivamente em validação walk-forward.

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

Não aceitar melhora apenas no agregado.

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

Como 13+ é um evento raro, estimar a incerteza da taxa observada por bootstrap no nível de concurso.

Reportar, por exemplo:

```text
hit_rate_13plus = ...
IC 95% = [... ; ...]
```

Isso ajuda a distinguir ganho real de variação aleatória.

---

## Ablation study

Comparar componentes progressivamente:

```text
A - probabilidades brutas
B - + calibração
C - + gap/entropia
D - + meta-modelo top1_fail
E - + Historical Lift
F - + regime de concurso
G - + ensemble
H - + Soft Constraint Palmeiras
I - modelo completo
```

Relatório esperado:

```text
Modelo | 14 | >=13 | >=12 | Média | Precision@5 | Recall@5 | P13+ estimado
```

Uma feature ou heurística só deve permanecer se demonstrar contribuição fora da amostra.

---

## Champion / Challenger

Manter formalmente:

```text
Champion = estratégia atualmente aprovada
Challenger = nova implementação em avaliação
```

O Challenger só deve ser promovido se superar o Champion em walk-forward segundo a hierarquia de métricas.

Exemplo:

```text
Seletor challenger: PROMOVIDO
>=13: +8,3% relativo
>=12: +2,1% relativo
Precision@5: melhora
```

ou:

```text
Seletor challenger: NÃO PROMOVIDO
Motivo: melhora log-loss, mas piora >=13
```

---

## Hierarquia de métricas para promoção

Prioridade recomendada:

```text
1. hit_rate_13plus
2. hit_rate_12plus
3. RecoveryRate
4. Precision@5 / Recall@5 / CoverageFail
5. mean_hits
6. calibração / log-loss
```

O produto final é a aposta completa, não o estimador probabilístico isolado.

---

## Guardrail contra overfitting

> Nenhuma complexidade adicional deve entrar na estratégia principal sem demonstrar ganho fora da amostra sobre uma baseline mais simples.

Critérios desejáveis:

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

Sempre que possível, exibir separadamente:

```text
P(14)
P(13)
P(>=13)
P(12)
P(>=12)
```

Sob a hipótese de independência entre jogos, a distribuição de acertos pode ser calculada exatamente por programação dinâmica / Poisson-binomial a partir das probabilidades de cobertura de cada partida.

O projeto não deve maximizar apenas soma de probabilidades individuais ou acurácia média por jogo.

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
tipo: seco ou duplo
palpite
cobertura
score de falha Top1, quando disponível
motivo da escolha
```

### Fronteira dos duplos

```text
rank dos candidatos
5 escolhidos
6º candidato
margem pTop1
P13+ original
P13+ após troca 5º/6º
delta absoluto
delta relativo
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
Total de marcações: 19/19
Flamengo/RJ: regra satisfeita, quando aplicável
P(14)
P(13)
P(>=13)
P(12)
P(>=12)
```

A validação deve ser recalculada de forma independente após a otimização e lançar erro se qualquer Hard Constraint for violada.

---

## Soft Constraint Palmeiras — custo explícito

Quando houver conflito entre a melhor solução probabilística e a preferência por excluir a vitória do Palmeiras, exibir:

```text
Melhor solução absoluta: P13+ = ...
Melhor solução sem vitória do Palmeiras: P13+ = ...
Custo da preferência: ...
```

A preferência só deve prevalecer quando o custo probabilístico for aceitável dentro da estratégia.

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

- `main.py`: orquestração do pipeline e telemetria.
- `data/concursos_anteriores.csv`: histórico de treinamento, calibração e backtest.
- `data/proximo_concurso.csv`: concurso alvo.
- `scripts/preprocess_data.py`: leitura, validação e engenharia de features.
- `scripts/train_model.py`: treinamento, calibração, meta-modelos e avaliação walk-forward.
- `scripts/predict_results.py`: probabilidades, ranking, otimização 9-5-5 e palpite final.
- `output/predictions.csv`: saída auditável das previsões e marcações.

---

## Formato dos CSVs

Os arquivos usam:

```text
delimitador: ;
separador decimal das odds: ,
```

Exemplo com pandas:

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

Testes automatizados:

```bash
python -m unittest discover -v
```

---

## Ordem recomendada de implementação

```text
1. oracle_9_5_5
2. SUCCESS / RECOVERABLE / UNRECOVERABLE
3. análise 12 -> 13
4. Precision@5 / Recall@5 / CoverageFail / DoubleWasteRate
5. histórico do cutoff 5º/6º
6. meta-modelo da zona cinzenta
7. matriz de trocas
8. Stability@5
9. bootstrap de >=13
10. Champion / Challenger
11. learning to rank
12. Historical Lift / regime de concurso
13. Monte Carlo robusto
14. ablation study contínuo
```

As primeiras prioridades atacam diretamente a principal dúvida experimental do projeto:

> **o esquema 9-5-5 está estruturalmente limitando o desempenho, ou o sistema ainda está escolhendo os cinco duplos errados?**

---

## Regra fundamental

> **As Hard Constraints têm precedência absoluta sobre qualquer Soft Constraint, heurística ou preferência.**

> **A métrica decisiva do projeto é a qualidade da aposta completa para atingir pelo menos 13 acertos, validada fora da amostra.**
