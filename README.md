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

2. Gerar exatamente:
   - **9 top1**;
   - **5 top2**;
   - **5 top3**.

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

## Princípio de otimização

O objetivo do projeto **não é simplesmente maximizar a acurácia média das previsões individuais**.

A função de decisão deve privilegiar a construção da aposta completa de 14 jogos que maximize a probabilidade de atingir o objetivo final:

```text
P(acertos >= 13)
```

A escolha de secos, duplos, distribuição de Top1/Top2/Top3 e aplicação das Soft Constraints deve ser avaliada à luz desse objetivo global, sempre subordinada às Hard Constraints.

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
tipo da marcação: seco ou duplo
palpite escolhido
motivo da escolha
restrições relevantes
```

Ao final, deve ser exibido um resumo validando as Hard Constraints, incluindo:

```text
Secos: 9/9
Duplos: 5/5
Triplos: 0/0
Top1: 9/9
Top2: 5/5
Top3: 5/5
Flamengo/RJ: regra satisfeita, quando aplicável
```

Também devem ser exibidos os indicadores utilizados pela otimização para comparar soluções candidatas e justificar a escolha do palpite final.

---

## Saída

O resultado final deve ser gravado em:

```text
output/predictions.csv
```

O arquivo deve preservar informações suficientes para reconstruir a decisão, incluindo probabilidades, rankings, marcações escolhidas e o palpite final do concurso.

---

## Regra fundamental

> **As Hard Constraints têm precedência absoluta sobre qualquer Soft Constraint ou preferência heurística.**

A aposta final só é válida se satisfizer simultaneamente todas as Hard Constraints do projeto.