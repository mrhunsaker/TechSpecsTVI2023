## Keystroke Latency — Descriptive Statistics
| ScreenReader   |    mean |   median |      std |   min |   max |
|:---------------|--------:|---------:|---------:|------:|------:|
| JAWS           | 233.657 |      144 | 241.221  |    15 |   992 |
| NVDA           | 124.354 |      116 |  88.0154 |    10 |   399 |
| SUPERNOVA      | 201.152 |      108 | 224.755  |     4 |   945 |
## Keystroke Latency — Two-Way ANOVA
Analyzes the interaction between Screen Reader and RAM.

|                        |       sum_sq |       df |       F |   PR(>F) |
|:-----------------------|-------------:|---------:|--------:|---------:|
| C(ScreenReader)        |  3118773.973 |    2.000 | 140.152 |    0.000 |
| C(RAM)                 | 35914546.707 |    4.000 | 806.969 |    0.000 |
| C(ScreenReader):C(RAM) |  5255586.525 |    8.000 |  59.044 |    0.000 |
| Residual               | 16355763.152 | 1470.000 | nan     |  nan     |

## Keystroke Latency — Pairwise T-Tests
|    | Comparison         |   Mean Difference (ms) |   t-statistic |   p-value | Diff > 25ms   | Statistically Significant   |
|---:|:-------------------|-----------------------:|--------------:|----------:|:--------------|:----------------------------|
|  0 | JAWS vs. NVDA      |                 109.3  |          9.47 |     0     | Yes           | Yes                         |
|  1 | JAWS vs. SUPERNOVA |                  32.51 |          2.19 |     0.029 | Yes           | Yes                         |
|  2 | NVDA vs. SUPERNOVA |                 -76.8  |         -7.08 |     0     | Yes           | Yes                         |
## Navigation Latency — Descriptive Statistics
| ScreenReader   |    mean |   median |      std |   min |   max |
|:---------------|--------:|---------:|---------:|------:|------:|
| JAWS           | 232.095 |      153 | 245.074  |    10 |   996 |
| NVDA           | 126.974 |      124 |  90.9072 |    10 |   399 |
| SUPERNOVA      | 198.561 |      112 | 230.571  |     0 |   946 |
## Navigation Latency — Two-Way ANOVA
Analyzes the interaction between Screen Reader and RAM.

|                        |       sum_sq |       df |       F |   PR(>F) |
|:-----------------------|-------------:|---------:|--------:|---------:|
| C(ScreenReader)        |  2854450.697 |    2.000 | 135.553 |    0.000 |
| C(RAM)                 | 38949932.259 |    4.000 | 924.834 |    0.000 |
| C(ScreenReader):C(RAM) |  5587845.422 |    8.000 |  66.339 |    0.000 |
| Residual               | 15477485.197 | 1470.000 | nan     |  nan     |

## Navigation Latency — Pairwise T-Tests
|    | Comparison         |   Mean Difference (ms) |   t-statistic |   p-value | Diff > 50ms   | Statistically Significant   |
|---:|:-------------------|-----------------------:|--------------:|----------:|:--------------|:----------------------------|
|  0 | JAWS vs. NVDA      |                 105.12 |          8.95 |     0     | Yes           | Yes                         |
|  1 | JAWS vs. SUPERNOVA |                  33.53 |          2.22 |     0.027 | No            | Yes                         |
|  2 | NVDA vs. SUPERNOVA |                 -71.59 |         -6.43 |     0     | Yes           | Yes                         |
## Load Time — Descriptive Statistics
| ScreenReader   |     mean |   median |     std |   min |    max |
|:---------------|---------:|---------:|--------:|------:|-------:|
| JAWS           | 53284.8  |    44000 | 49296.7 |  1000 | 183000 |
| NVDA           |  9058.59 |     9000 |  5146.3 |  1000 |  21000 |
| SUPERNOVA      | 48236.4  |    32000 | 48057.7 | -2000 | 183000 |
## Load Time — Two-Way ANOVA
Analyzes the interaction between Screen Reader and RAM.

|                        |            sum_sq |       df |        F |   PR(>F) |
|:-----------------------|------------------:|---------:|---------:|---------:|
| C(ScreenReader)        |  580197383164.989 |    2.000 | 1517.511 |    0.000 |
| C(RAM)                 | 1494231276767.673 |    4.000 | 1954.086 |    0.000 |
| C(ScreenReader):C(RAM) |  579251983838.387 |    8.000 |  378.759 |    0.000 |
| Residual               |  281016222222.222 | 1470.000 |  nan     |  nan     |

## Load Time — Pairwise T-Tests
|    | Comparison         |   Mean Difference (ms) |   t-statistic |   p-value | Diff > 5000ms   | Statistically Significant   |
|---:|:-------------------|-----------------------:|--------------:|----------:|:----------------|:----------------------------|
|  0 | JAWS vs. NVDA      |               44226.3  |         19.85 |     0     | Yes             | Yes                         |
|  1 | JAWS vs. SUPERNOVA |                5048.48 |          1.63 |     0.103 | Yes             | No                          |
|  2 | NVDA vs. SUPERNOVA |              -39177.8  |        -18.03 |     0     | Yes             | Yes                         |
