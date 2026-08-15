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

6. Exibir no terminal telemetria suficiente para auditar probabilidades, ranking, secos, duplos, restrições, cutoff dos duplos e critérios que levaram à aposta final.

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

Essa baseline **não é uma regra obrigatória**. Ela existe para responder experimentalmente se o otimizador e os modelos históricos realmente conseguem superá-la fora da amostra.

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

A decisão não deve usar somente frequência histórica nem somente as probabilidades atuais.

### Histórico

Em `data/concursos_anteriores.csv`, o sistema deve estudar:

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

Para cada partida de `data/proximo_concurso.csv`, o sistema deve produzir:

```text
p(1), p(X), p(2)
p(top1), p(top2), p(top3)
```

O histórico deve ajudar a corrigir ou contextualizar o risco, enquanto as probabilidades atuais determinam o custo probabilístico concreto de cada marcação.

---

## Prioridades de implementação

### 1. Fronteira do 5º vs. 6º candidato a duplo

O terminal deve ordenar os 14 jogos pelo risco de falha do Top1 e destacar a fronteira entre o último duplo escolhido e o primeiro seco excluído.

Exemplo:

```text
Rank | Jogo       | pTop1 | 1-pTop1 | Decisão
1    | ...         | ...   | ...     | DUPLO
...
5    | ...         | ...   | ...     | DUPLO
---------------------------------------------
6    | ...         | ...   | ...     | SECO
```

Também deve calcular:

```text
P13+ original
P13+ após trocar o 5º pelo 6º
Delta absoluto
Delta relativo
```

Se a diferença for muito pequena, a decisão deve ser sinalizada como **frágil** ou **quase empate**.

### 2. Backtest da baseline dos 5 menores p(top1)

Implementar e medir explicitamente:

```text
9 maiores p(top1) -> Top1 seco
5 menores p(top1) -> Top2+Top3
```

Comparar com o otimizador completo em walk-forward.

### 3. Backtest real de 13+

Não avaliar somente `P(acertos >= 13)` estimado pelo próprio modelo.

Medir historicamente, fora da amostra:

```text
14 acertos
>=13 acertos
>=12 acertos
média de acertos
mediana de acertos
distribuição de 0 a 14 acertos
```

A métrica principal de seleção de estratégia deve ser o desempenho real de `>=13` em walk-forward, observando também a estabilidade estatística.

---

## Features recomendadas

Além das probabilidades básicas:

```text
p_top1
p_top2
p_top3
```

usar ou testar:

```text
gap12 = p_top1 - p_top2
gap23 = p_top2 - p_top3
gap13 = p_top1 - p_top3
entropy = entropia de p(1), p(X), p(2)
```

Também podem ser avaliados:

- resultado concreto que ocupa Top1/Top2/Top3 (`1`, `X` ou `2`);
- posição da partida no concurso;
- média e mediana de `p(top1)` no concurso;
- quantidade de favoritos fortes;
- quantidade de jogos equilibrados;
- dispersão das probabilidades;
- perfil probabilístico do concurso inteiro.

---

## Calibração por rank

Além da calibração global das probabilidades, auditar:

```text
p(top1) previsto vs frequência real de top1_hit
p(top2) previsto vs frequência real de top2_hit
p(top3) previsto vs frequência real de top3_hit
```

A análise deve ser feita por faixas e de forma walk-forward.

Exemplo conceitual:

```text
Faixa p(top1) | Previsto médio | Top1 observado | Lift
0,40-0,45     | 0,426          | 0,389          | 0,913
```

Definição possível:

```text
HistoricalLiftTopK = frequencia_real_topK_hit / probabilidade_media_prevista_topK
```

Esse lift deve ser usado como diagnóstico ou feature, nunca como correção automática sem validação fora da amostra.

---

## Meta-modelo de falha do Top1

Uma linha prioritária de pesquisa é modelar diretamente:

```text
P(top1_hit = 0)
```

ou:

```text
P(Top2 ou Top3)
```

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
ranking concreto 1/X/2
features de regime do concurso
```

A finalidade é distinguir jogos com `p(top1)` semelhantes, mas risco histórico diferente de falha do Top1.

A escolha dos 5 duplos pode então comparar:

```text
1 - p(top1)
vs
p_top1_fail_adjusted
```

A versão ajustada só deve substituir a baseline se demonstrar ganho real em walk-forward.

---

## Historical Lift de falha do Top1

Pode-se definir:

```text
LiftFail = P_hist(Top1 falha | faixa/perfil) / (1 - p(top1))
```

Exemplo conceitual:

```text
p(top1) médio = 0,44
falha prevista = 0,56
falha observada = 0,61
LiftFail = 1,089
```

Valores acima de 1 sugerem que o modelo historicamente subestima a falha do Top1 naquele perfil; valores abaixo de 1 sugerem o contrário.

---

## Regime do concurso

Cada concurso pode ser representado por um vetor como:

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

Essas informações podem ser usadas para localizar concursos históricos semelhantes, inclusive por KNN ou métodos equivalentes.

A pergunta principal é:

> Em concursos probabilisticamente parecidos com o atual, quantos Top1 normalmente falharam e onde essas falhas se concentraram?

---

## Walk-forward e prevenção de leakage

Todas as previsões históricas usadas em backtests, meta-modelos ou calibração devem ser produzidas sem acesso ao futuro.

Fluxo obrigatório:

```text
treina até concurso N-1
calibra usando apenas dados disponíveis até N-1
prevê concurso N
monta a aposta de N
avalia contra o resultado real de N
avança para N+1
```

Probabilidades in-sample não devem ser usadas como meta-features para treinar `top1_hit`, `top2_hit`, `top3_hit` ou `top1_fail`.

---

## Robustez e análise de sensibilidade

As probabilidades são estimativas e não valores exatos. O sistema deve testar a estabilidade da solução diante de pequenas perturbações.

Sugestão:

```text
+/- 0,5%
+/- 1%
+/- 2%
```

Após perturbar e renormalizar `p(1)`, `p(X)` e `p(2)`, rodar novamente o otimizador e medir a frequência com que cada jogo permanece entre os 5 duplos.

Exemplo:

```text
Jogo A: duplo em 100% das simulações -> robusto
Jogo B: duplo em 57% das simulações  -> instável
Jogo C: duplo em 43% das simulações  -> fronteira
```

A telemetria deve destacar escolhas frágeis.

---

## Monte Carlo sobre incerteza das probabilidades

Como evolução da análise de sensibilidade, pode-se simular múltiplos vetores probabilísticos plausíveis ao redor das probabilidades estimadas e medir:

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

## Ablation study

Deve existir um modo de comparação experimental entre componentes, por exemplo:

```text
A - probabilidades brutas
B - + calibração
C - + gap/entropia
D - + meta-modelo top1_fail
E - + Historical Lift
F - + regime de concurso
G - + Soft Constraint Palmeiras
H - modelo completo
```

Relatório esperado:

```text
Modelo | 14 | >=13 | >=12 | Média | P13+ estimado
```

Uma feature, heurística ou modelo novo não deve ser mantido apenas porque parece intuitivo; deve demonstrar contribuição fora da amostra.

---

## Guardrail contra overfitting

Princípio de promoção de melhorias:

> Nenhuma complexidade adicional deve entrar na estratégia principal sem demonstrar ganho fora da amostra sobre uma baseline mais simples.

Critérios desejáveis:

- avaliação walk-forward;
- número suficiente de concursos;
- melhoria em `>=13`;
- ausência de deterioração material em `>=12`;
- estabilidade em diferentes períodos;
- resultado não dependente de poucos concursos extremos.

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

## Soft Constraint Palmeiras — custo explícito

Quando houver conflito entre a melhor solução probabilística e a preferência por excluir a vitória do Palmeiras, exibir:

```text
Melhor solução absoluta: P13+ = ...
Melhor solução sem vitória do Palmeiras: P13+ = ...
Custo da preferência: ...
```

A preferência só deve prevalecer quando o custo probabilístico for considerado aceitável dentro da estratégia.

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
Rank dos candidatos
5 escolhidos
6º candidato
margem do cutoff
P13+ original
P13+ após troca 5º/6º
delta
classificação: robusta / frágil
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

Os arquivos:

```text
data/concursos_anteriores.csv
data/proximo_concurso.csv
```

usam:

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
1. Fronteira 5º/6º + delta P13+
2. Baseline dos 5 menores p(top1)
3. Backtest walk-forward real de >=13
4. Calibração de top1_hit por faixa
5. gap12/gap13 + entropia
6. Meta-modelo P(top1_fail)
7. Sensitivity analysis / estabilidade dos 5 duplos
8. Historical Lift
9. Regime de concurso / concursos semelhantes
10. Monte Carlo robusto
11. Ablation study contínuo
```

As prioridades 1, 2 e 6 atacam diretamente o principal ponto de decisão da estratégia: **identificar corretamente os cinco jogos em que abandonar o Top1 oferece maior valor para atingir 13 ou 14 acertos**.

---

## Regra fundamental

> **As Hard Constraints têm precedência absoluta sobre qualquer Soft Constraint, heurística ou preferência.**

> **A métrica decisiva do projeto é a qualidade da aposta completa para atingir pelo menos 13 acertos, validada fora da amostra.**
