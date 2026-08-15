# Loteca 9S-5D-0T — Estratégia 9-5-5

Projeto para geração de um único palpite final da Loteca, baseado no histórico disponível em `data/concursos_anteriores.csv`, com foco em maximizar a probabilidade de atingir **pelo menos 13 acertos**, respeitando integralmente as restrições definidas abaixo.

## Objetivo

A estratégia utiliza os históricos dos concursos de `data/concursos_anteriores.csv` para modelar probabilidades, ordenar resultados por confiança e construir uma única aposta final por concurso.

### Estratégia

1. Gerar **um único palpite final por concurso**, otimizado para maximizar a probabilidade de atingir **pelo menos 13 acertos**, respeitando todas as **Hard Constraints**.

2. Representar as probabilidades dos três resultados possíveis de cada partida como:
   - `p(1)`: vitória do mandante;
   - `p(X)`: empate;
   - `p(2)`: vitória do visitante.

3. Derivar `p(top1)`, `p(top2)` e `p(top3)` ordenando `p(1)`, `p(X)` e `p(2)` da maior para a menor.

   Em caso de probabilidades iguais, utilizar a seguinte prioridade de desempate:

   ```text
   1 > 2 > X
   ```

4. Representar o resultado real de cada partida em relação ao ranking probabilístico por **One-Hot Encoding**, utilizando:
   - `top1_hit`;
   - `top2_hit`;
   - `top3_hit`.

   Para cada partida, exatamente uma dessas variáveis deve ser igual a `1`, e as demais devem ser iguais a `0`.

5. Exibir no terminal telemetria suficiente para permitir auditoria completa de:
   - probabilidades `p(1)`, `p(X)` e `p(2)`;
   - ranking `top1`, `top2` e `top3`;
   - escolha dos secos e duplos;
   - restrições aplicadas;
   - critérios utilizados para chegar à aposta final.

---

## Hard Constraints

As restrições abaixo são obrigatórias e não podem ser violadas pela geração do palpite final.

1. Gerar exatamente:
   - **9 secos**;
   - **5 duplos**;
   - **0 triplos**.

2. Gerar exatamente **19 marcações**, distribuídas obrigatoriamente em:
   - **9 resultados Top1**;
   - **5 resultados Top2**;
   - **5 resultados Top3**.

   Essa distribuição **9-5-5 não deve ser aplicada de forma cega ou puramente posicional**. A escolha de quais jogos receberão marcações Top1, Top2 e Top3 deve resultar da comparação entre:

   - o **histórico dos concursos anteriores** de `data/concursos_anteriores.csv`, incluindo a frequência, posição, sequência, concentração e demais padrões observados de `top1_hit`, `top2_hit` e `top3_hit`;
   - as **probabilidades do próximo concurso** de `data/proximo_concurso.csv`, especialmente `p(top1)`, `p(top2)` e `p(top3)` de cada uma das 14 partidas.

   O histórico deve orientar **como distribuir estruturalmente os ranks Top1/Top2/Top3**, enquanto as probabilidades do próximo concurso determinam **qual resultado concreto (`1`, `X` ou `2`) ocupa cada rank em cada partida**.

   A solução final deve, entre todas as combinações que respeitem exatamente `9 Top1 + 5 Top2 + 5 Top3`, escolher a distribuição que maximize o objetivo global:

   ```text
   P(acertos >= 13)
   ```

   Como existem 9 secos e 5 duplos:

   ```text
   9 × 1 + 5 × 2 = 19 marcações
   ```

   Portanto, a contagem `9 Top1 + 5 Top2 + 5 Top3 = 19` refere-se às **19 marcações efetivamente presentes no palpite final**, e não ao número de partidas.

3. Quando o **FLAMENGO/RJ** participar do concurso, incluir obrigatoriamente entre as marcações o resultado correspondente à sua **vitória**.

---

## Soft Constraints

As restrições abaixo devem orientar a otimização, mas podem ser flexibilizadas quando conflitarem com as Hard Constraints ou quando prejudicarem significativamente a qualidade global da aposta.

1. Favorecer ordenações que antecipem e concentrem resultados **Top1**, especialmente nas **9 primeiras posições**, privilegiando:
   - runs longas de Top1;
   - baixa fragmentação;
   - maior concentração dos resultados de maior probabilidade no início da ordenação.

2. Favorecer soluções que **excluam a vitória do PALMEIRAS/SP**, priorizando empate ou derrota quando isso não comprometer significativamente a qualidade global da aposta.

---

## Hipótese estrutural 9-5-5

Sob as Hard Constraints atuais, uma configuração merece ser tratada como **baseline estrutural explícito**, e não como regra obrigatória:

```text
9 jogos: seco Top1
5 jogos: duplo Top2 + Top3
```

Essa configuração satisfaz simultaneamente:

```text
9 secos
5 duplos
0 triplos

9 Top1
5 Top2
5 Top3
```

Ela surge naturalmente porque `Top1` é, por definição, a maior probabilidade individual de cada partida, enquanto um duplo `Top2+Top3` cobre exatamente o evento complementar ao Top1:

```text
P(Top2 ou Top3) = 1 - p(top1)
```

Consequentemente, uma baseline simples para auditoria é:

```text
9 maiores p(top1)  -> seco Top1
5 menores p(top1)  -> duplo Top2+Top3
```

Essa baseline **não substitui o otimizador**. Ela deve ser usada como referência para medir se modelos históricos, meta-modelos e heurísticas adicionais realmente geram ganho em `P(acertos >= 13)` ou apenas reproduzem uma solução estrutural já implícita nas restrições.

### Relação geral entre os tipos de duplo

Definindo:

```text
D12 = quantidade de duplos Top1+Top2
D13 = quantidade de duplos Top1+Top3
D23 = quantidade de duplos Top2+Top3
```

com:

```text
D12 + D13 + D23 = 5
```

as contagens de secos necessárias para fechar exatamente `9 Top1 + 5 Top2 + 5 Top3` obedecem a:

```text
SecoTop1 = 4 + D23
SecoTop2 = D13
SecoTop3 = D12
```

Logo, qualquer uso de `Top1+Top2` força a existência de um **Top3 seco** em outra partida, e qualquer uso de `Top1+Top3` força a existência de um **Top2 seco**. Essa compensação estrutural deve ser considerada explicitamente na otimização global.

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

### Arquivos principais

- `main.py`: ponto de entrada do projeto e orquestração do pipeline.
- `data/concursos_anteriores.csv`: histórico utilizado para treinamento, validação e análise dos concursos anteriores.
- `data/proximo_concurso.csv`: partidas e informações do concurso para o qual será gerado o palpite.
- `scripts/preprocess_data.py`: preparação, validação e transformação dos dados.
- `scripts/train_model.py`: treinamento e calibração dos modelos probabilísticos.
- `scripts/predict_results.py`: geração das probabilidades, rankings e aposta final sob as restrições do projeto.
- `output/predictions.csv`: saída consolidada das previsões e do palpite final.

---

## Formato dos arquivos CSV

Os arquivos:

- `data/concursos_anteriores.csv`;
- `data/proximo_concurso.csv`;

utilizam as seguintes convenções:

```text
Delimitador de colunas: ;
Separador decimal das odds: ,
```

Exemplo conceitual:

```text
Concurso;Jogo;Mandante;Visitante;Odd_1;Odd_X;Odd_2
1266;1;TIME A;TIME B;1,85;3,20;4,10
```

Ao carregar os arquivos com pandas, deve-se respeitar explicitamente essas configurações, por exemplo:

```python
pd.read_csv(caminho, sep=";", decimal=",")
```

---

## Convenção dos palpites

### Secos

Um resultado simples é representado diretamente por:

```text
1
X
2
```

### Duplos

Duplos devem ser representados exclusivamente nos seguintes formatos:

```text
1X
12
X2
```

### Triplos

Caso sejam utilizados em algum cenário futuro, triplos devem ser representados como:

```text
1X2
```

Na configuração atual deste projeto, entretanto, a Hard Constraint exige **0 triplos**.

---

## Ranking probabilístico

Para cada partida, o modelo deve produzir:

```text
p(1), p(X), p(2)
```

Essas três probabilidades são ordenadas para formar:

```text
top1 = resultado com maior probabilidade
top2 = resultado com segunda maior probabilidade
top3 = resultado com menor probabilidade
```

Com suas respectivas probabilidades:

```text
p(top1) >= p(top2) >= p(top3)
```

Em caso de empate de probabilidades, aplicar obrigatoriamente:

```text
1 > 2 > X
```

### Exemplo

Se:

```text
p(1) = 0,48
p(X) = 0,27
p(2) = 0,25
```

então:

```text
top1 = 1   | p(top1) = 0,48
top2 = X   | p(top2) = 0,27
top3 = 2   | p(top3) = 0,25
```

Se o resultado real for `X`:

```text
top1_hit = 0
top2_hit = 1
top3_hit = 0
```

---

## Histórico vs. próximo concurso

A seleção das 19 marcações deve combinar duas fontes de informação complementares.

### 1. Histórico dos concursos anteriores

Em `data/concursos_anteriores.csv`, após calcular o ranking probabilístico de cada partida e confrontá-lo com o resultado real, o sistema deve estudar a distribuição de:

```text
top1_hit
top2_hit
top3_hit
```

A análise histórica pode considerar, entre outros sinais:

- frequência global e recente de cada rank;
- distribuição por posição do jogo no concurso;
- quantidade de Top1 por concurso;
- runs consecutivas de Top1;
- fragmentação das ocorrências de Top1;
- transições entre Top1, Top2 e Top3;
- padrões condicionais em função das próprias probabilidades;
- comportamento histórico de partidas com perfis probabilísticos semelhantes aos do próximo concurso.

### 2. Probabilidades do próximo concurso

Para cada uma das 14 partidas de `data/proximo_concurso.csv`, devem ser obtidos:

```text
p(top1)
p(top2)
p(top3)
```

Essas probabilidades fornecem o custo e o benefício probabilístico de incluir cada rank na aposta.

### 3. Otimização conjunta

O otimizador deve confrontar os padrões aprendidos no histórico com as probabilidades atuais e decidir em quais partidas utilizar cada uma das 19 marcações, sujeito simultaneamente a:

```text
9 secos
5 duplos
0 triplos

9 Top1
5 Top2
5 Top3
```

Uma distribuição historicamente frequente não deve ser escolhida apenas por sua frequência se ela for incompatível com as probabilidades do concurso atual. Da mesma forma, a maior probabilidade individual de uma partida não deve, isoladamente, ignorar padrões históricos relevantes.

O critério decisivo continua sendo a qualidade da **aposta completa**, medida prioritariamente por:

```text
P(acertos >= 13)
```

---

## Features recomendadas para aprimoramento

Além de `p(top1)`, `p(top2)` e `p(top3)`, devem ser avaliadas features que representem a incerteza e a proximidade entre os três resultados:

```text
gap12 = p(top1) - p(top2)
gap23 = p(top2) - p(top3)
gap13 = p(top1) - p(top3)
entropy = entropia de p(1), p(X), p(2)
```

Essas features podem ajudar a identificar partidas em que abandonar o Top1 é mais justificável do que sugere apenas `1 - p(top1)`.

Também podem ser avaliados:

- ranking concreto dos resultados (`1`, `X`, `2`) em cada partida;
- posição do jogo no concurso;
- perfil probabilístico do concurso inteiro;
- quantidade de favoritos fortes;
- quantidade de jogos equilibrados;
- médias e dispersões de `p(top1)`, `p(top2)` e `p(top3)`.

---

## Calibração histórica por rank

Além da calibração global de `p(1)`, `p(X)` e `p(2)`, o sistema deve auditar especificamente:

```text
p(top1) previsto vs frequência real de top1_hit
p(top2) previsto vs frequência real de top2_hit
p(top3) previsto vs frequência real de top3_hit
```

A análise deve ser feita preferencialmente em faixas de probabilidade e de forma walk-forward.

Exemplo conceitual:

```text
Faixa p(top1) | p(top1) médio | frequência top1_hit | lift
0,40-0,45     | 0,426         | 0,389               | 0,913
```

Pode-se definir:

```text
HistoricalLiftTopK = frequência_real_topK_hit / probabilidade_média_prevista_topK
```

Esse lift deve ser tratado como sinal de calibração ou feature de meta-modelo, não como substituição automática da probabilidade prevista.

---

## Meta-modelo de falha do Top1

Uma linha prioritária de aprimoramento é modelar diretamente:

```text
P(top1_hit = 0)
```

ou, equivalentemente:

```text
P(Top2 ou Top3)
```

O objetivo desse meta-modelo é distinguir jogos com valores semelhantes de `p(top1)` nos quais o histórico indica riscos diferentes de falha do favorito probabilístico.

Features candidatas:

```text
p(top1)
p(top2)
p(top3)
gap12
gap23
gap13
entropy
ranking 1/X/2
posição do jogo
features globais do concurso
```

A seleção dos cinco jogos candidatos a `Top2+Top3` pode então comparar:

```text
FailRaw = 1 - p(top1)
FailAdjusted = P_meta(top1_hit = 0)
```

O meta-modelo só deve ser incorporado à estratégia final se superar a baseline estrutural em validação walk-forward, especialmente em `P(acertos >= 13)`.

---

## Regime do concurso e concursos semelhantes

Pode ser criado um vetor de características para cada concurso, por exemplo:

```text
mean_top1
mean_top2
mean_top3
median_gap12
mean_entropy
min_top1
max_top1
quantidade de p(top1) > 0,60
quantidade de jogos equilibrados
```

Esse vetor permite comparar o próximo concurso com concursos históricos semelhantes, por exemplo via KNN ou agrupamento de regimes.

O objetivo é estimar se o próximo concurso apresenta perfil historicamente associado a maior ou menor incidência de:

```text
top1_hit
top2_hit
top3_hit
```

Qualquer sinal de regime deve complementar, e não substituir, as probabilidades específicas de cada partida.

---

## Backtests obrigatórios para novas heurísticas

Toda nova heurística ou modelo deve ser comparado contra baselines simples e reproduzíveis.

### Baseline A — probabilidades puras

```text
9 maiores p(top1)  -> seco Top1
5 menores p(top1)  -> duplo Top2+Top3
```

### Baseline B — otimizador probabilístico atual

Solução que maximiza exatamente `P(acertos >= 13)` utilizando as probabilidades calibradas e todas as Hard Constraints.

### Candidatos de aprimoramento

Podem incluir:

```text
menor gap12
maior entropia
historical lift
meta-modelo de top1_fail
KNN/regime de concurso
combinações dos sinais anteriores
```

As comparações devem reportar pelo menos:

```text
14 acertos
13 acertos
P(acertos >= 13)
12 acertos
P(acertos >= 12)
média de acertos
mediana de acertos
Top1 capturados
Top2 capturados
Top3 capturados
```

O critério principal de promoção de uma estratégia continua sendo o desempenho **fora da amostra**, em walk-forward, para atingir pelo menos 13 acertos.

---

## Validação walk-forward

Backtests e calibrações devem preservar a ordem temporal dos concursos.

Para cada concurso `N`:

```text
treinar somente com concursos < N
calibrar somente com concursos < N
prever o concurso N
montar a aposta do concurso N
avaliar o resultado real do concurso N
```

Nenhuma informação do concurso avaliado pode participar do treinamento, calibração, seleção de hiperparâmetros ou construção de features que não estivessem disponíveis antes daquele concurso.

---

## Fronteira dos cinco duplos

A telemetria deve tornar explícita a fronteira entre o último jogo escolhido para receber duplo e o primeiro jogo excluído.

Exemplo:

```text
=== FRONTEIRA DOS DUPLOS ===
Rank | Jogo      | pTop1 | FailRaw | FailAdj | Score
1    | Jogo A    | .3592 | .6408   | .6621   | .6814
2    | Jogo B    | .4102 | .5898   | .6034   | .6170
3    | Jogo C    | .4231 | .5769   | .5901   | .6018
4    | Jogo D    | .4310 | .5690   | .5742   | .5845
5    | Jogo E    | .4473 | .5527   | .5680   | .5762
-----------------------------------------------------
6    | Jogo F    | .4571 | .5429   | .5661   | .5739
```

Deve ser mostrado, quando possível:

```text
margem entre 5º e 6º candidato
delta de P(acertos >= 13) ao trocar 5º por 6º
classificação da decisão: robusta ou frágil
```

Essa análise é especialmente importante quando os candidatos próximos ao cutoff apresentam probabilidades muito semelhantes.

---

## Sensibilidade e robustez

A solução final deve poder ser auditada quanto à sensibilidade a pequenas mudanças nas probabilidades.

Testes recomendados:

```text
p(top1) ± pequenas perturbações
p(top2) ± pequenas perturbações
p(top3) ± pequenas perturbações
```

O objetivo é verificar se os mesmos cinco jogos continuam selecionados como duplos.

Uma solução que muda com perturbações mínimas deve ser marcada como **instável** ou **frágil**, permitindo distinguir:

```text
decisão robusta
decisão marginal
decisão instável
```

A robustez pode ser usada como critério secundário, desde que não viole as Hard Constraints nem substitua `P(acertos >= 13)` como objetivo principal.

---

## Princípio de otimização

O objetivo do projeto **não é simplesmente maximizar a acurácia média das previsões individuais**.

A função de decisão deve privilegiar a construção da aposta completa de 14 jogos que maximize a probabilidade de atingir o objetivo final:

```text
P(acertos >= 13)
```

A escolha de secos, duplos, distribuição de Top1/Top2/Top3 e aplicação das Soft Constraints deve ser avaliada à luz desse objetivo global, sempre subordinada às Hard Constraints.

Sempre que possível, devem ser reportados separadamente:

```text
P(14 acertos)
P(13 acertos)
P(acertos >= 13)
P(12 acertos)
P(acertos >= 12)
```

---

## Telemetria esperada

A execução deve fornecer informações suficientes para reproduzir e auditar a decisão. Para cada partida, é desejável exibir pelo menos:

```text
Jogo
Mandante x Visitante
p(1)
p(X)
p(2)
top1 / p(top1)
top2 / p(top2)
top3 / p(top3)
gap12 / gap23 / gap13
entropia
tipo da marcação: seco ou duplo
palpite escolhido
motivo da escolha
restrições relevantes
```

A telemetria da otimização 9-5-5 também deve mostrar, quando aplicável:

```text
score histórico da distribuição candidata
score probabilístico do próximo concurso
quantidade de Top1/Top2/Top3 selecionados
posições das marcações Top1/Top2/Top3
ganho marginal de cada duplo
FailRaw
FailAdjusted
impacto estimado sobre P(acertos >= 13)
fronteira entre 5º e 6º candidato a duplo
sensibilidade da solução
```

Ao final, deve ser exibido um resumo validando as Hard Constraints, incluindo:

```text
Secos: 9/9
Duplos: 5/5
Triplos: 0/0
Top1: 9/9
Top2: 5/5
Top3: 5/5
Total de marcações: 19/19
Flamengo/RJ: regra satisfeita, quando aplicável
```

Também devem ser exibidos os indicadores utilizados pela otimização para comparar soluções candidatas e justificar a escolha do palpite final.

---

## Validação independente das Hard Constraints

Depois de o otimizador gerar a solução, as Hard Constraints devem ser recalculadas de forma independente a partir do palpite final.

A execução deve falhar explicitamente se qualquer condição não for satisfeita:

```text
secos == 9
duplos == 5
triplos == 0
top1 == 9
top2 == 5
top3 == 5
total de marcações == 19
vitória do Flamengo incluída, quando aplicável
```

Duplos válidos devem pertencer exclusivamente ao conjunto:

```text
1X
12
X2
```

---

## Tratamento das Soft Constraints

### Palmeiras/SP

A preferência por excluir a vitória do Palmeiras deve ser quantitativa e subordinada à qualidade global da aposta.

A solução sem vitória do Palmeiras deve ser favorecida quando a perda estimada em `P(acertos >= 13)` for pequena ou equivalente, mas a Soft Constraint não deve forçar uma solução substancialmente pior.

### Runs de Top1

A concentração de Top1 pode ser medida por indicadores como:

```text
maior_run_top1
numero_de_runs_top1
fragmentacao_top1
```

Esses indicadores devem atuar apenas como critérios secundários ou de desempate até que backtests walk-forward demonstrem ganho consistente no objetivo principal.

---

## Ordem recomendada de implementação

Priorizar os aprimoramentos na seguinte sequência:

```text
1. Backtest da baseline: 5 menores p(top1) recebem Top2+Top3
2. Comparação com o otimizador probabilístico atual
3. Auditoria/calibração de top1/top2/top3 por faixa de probabilidade
4. Features gap12/gap23/gap13 e entropia
5. Meta-modelo P(top1_hit = 0)
6. Comparação meta-modelo vs baselines em walk-forward
7. Telemetria da fronteira 5º vs 6º candidato
8. Sensitivity analysis e classificação de robustez
9. KNN/regime de concurso
10. Avaliação histórica das runs de Top1
11. Ajuste quantitativo da Soft Constraint do Palmeiras
```

Nenhuma complexidade adicional deve ser promovida para a estratégia principal sem demonstrar ganho fora da amostra sobre baselines mais simples.

---

## Saída

O resultado final deve ser gravado em:

```text
output/predictions.csv
```

O arquivo deve preservar informações suficientes para reconstruir a decisão, incluindo probabilidades, rankings, marcações escolhidas e o palpite final do concurso.

## Execução

O pipeline usa apenas a biblioteca padrão do Python 3.10+:

```bash
python main.py
```

A execução valida os CSVs, ajusta uma calibração por temperatura em uma divisão cronológica do histórico e resolve a aposta por programação dinâmica. Para cada estado viável, o otimizador mantém a fronteira de Pareto das probabilidades de zero e uma falha; assim, a função final calculada é exatamente `P(14 acertos) + P(13 acertos)`, sob a hipótese explícita de independência entre os jogos. As preferências suaves são usadas somente para desempatar soluções com probabilidade equivalente, nunca para relaxar uma restrição obrigatória.

Os testes automatizados podem ser executados com:

```bash
python -m unittest discover -v
```

---

## Regra fundamental

> **As Hard Constraints têm precedência absoluta sobre qualquer Soft Constraint ou preferência heurística.**

A aposta final só é válida se satisfizer simultaneamente todas as Hard Constraints do projeto.
