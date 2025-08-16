## Keystroke Latency — Descriptive Statistics
| ScreenReader   |   count |    mean |   median |   mode |      std |     var |   min |   q25 |   q75 |   iqr |   max |     skew |     kurt |
|:---------------|--------:|--------:|---------:|-------:|---------:|--------:|------:|------:|------:|------:|------:|---------:|---------:|
| JAWS           |     495 | 233.657 |      144 |     16 | 241.221  | 58187.5 |    15 |    50 | 325   | 275   |   992 | 1.46756  | 1.37695  |
| SUPERNOVA      |     495 | 201.152 |      108 |     31 | 224.755  | 50515   |     4 |    39 | 278.5 | 239.5 |   945 | 1.56737  | 1.68617  |
| NARRATOR       |     495 | 226.196 |      137 |     35 | 241.321  | 58236   |     2 |    41 | 315   | 274   |   979 | 1.46577  | 1.37667  |
| NVDA           |     495 | 124.354 |      116 |     18 |  88.0154 |  7746.7 |    10 |    50 | 170.5 | 120.5 |   399 | 0.962122 | 0.845598 |
## Keystroke Latency — Two-Way ANOVA
Analyzes the interaction between Screen Reader and RAM.

|                        |       df |       sum_sq |      mean_sq |        F |   PR(>F) |
|:-----------------------|---------:|-------------:|-------------:|---------:|---------:|
| C(ScreenReader)        |    3.000 |  3707107.552 |  1235702.517 |  100.499 |    0.000 |
| C(RAM)                 |    4.000 | 55973452.230 | 13993363.058 | 1138.071 |    0.000 |
| C(ScreenReader):C(RAM) |   12.000 |  6221462.549 |   518455.212 |   42.166 |    0.000 |
| Residual               | 1960.000 | 24099553.596 |    12295.691 |  nan     |  nan     |

## Keystroke Latency — Pairwise T-Tests
|    | Comparison             |   Mean Difference (ms) |   t-statistic |   p-value | Diff > 25ms   | Statistically Significant   |
|---:|:-----------------------|-----------------------:|--------------:|----------:|:--------------|:----------------------------|
|  0 | JAWS vs. NVDA          |                 109.3  |          9.47 |     0     | Yes           | Yes                         |
|  1 | JAWS vs. SUPERNOVA     |                  32.51 |          2.19 |     0.029 | Yes           | Yes                         |
|  2 | JAWS vs. NARRATOR      |                   7.46 |          0.49 |     0.627 | No            | No                          |
|  3 | NVDA vs. SUPERNOVA     |                 -76.8  |         -7.08 |     0     | Yes           | Yes                         |
|  4 | NVDA vs. NARRATOR      |                -101.84 |         -8.82 |     0     | Yes           | Yes                         |
|  5 | SUPERNOVA vs. NARRATOR |                 -25.04 |         -1.69 |     0.091 | Yes           | No                          |
## Navigation Latency — Descriptive Statistics
| ScreenReader   |   count |    mean |   median |   mode |      std |      var |   min |   q25 |   q75 |   iqr |   max |     skew |     kurt |
|:---------------|--------:|--------:|---------:|-------:|---------:|---------:|------:|------:|------:|------:|------:|---------:|---------:|
| JAWS           |     495 | 232.095 |      153 |     24 | 245.074  | 60061.1  |    10 |    41 | 342.5 | 301.5 |   996 | 1.44111  | 1.35606  |
| SUPERNOVA      |     495 | 198.561 |      112 |      8 | 230.571  | 53163.2  |     0 |    30 | 281   | 251   |   946 | 1.57734  | 1.75985  |
| NARRATOR       |     495 | 224.628 |      144 |     12 | 244.917  | 59984.5  |     0 |    35 | 334.5 | 299.5 |   987 | 1.43779  | 1.34303  |
| NVDA           |     495 | 126.974 |      124 |     30 |  90.9072 |  8264.11 |    10 |    44 | 171   | 127   |   399 | 0.900802 | 0.576387 |
## Navigation Latency — Two-Way ANOVA
Analyzes the interaction between Screen Reader and RAM.

|                        |       df |       sum_sq |      mean_sq |        F |   PR(>F) |
|:-----------------------|---------:|-------------:|-------------:|---------:|---------:|
| C(ScreenReader)        |    3.000 |  3411959.058 |  1137319.686 |   98.601 |    0.000 |
| C(RAM)                 |    4.000 | 60457418.222 | 15114354.556 | 1310.359 |    0.000 |
| C(ScreenReader):C(RAM) |   12.000 |  6582563.164 |   548546.930 |   47.557 |    0.000 |
| Residual               | 1960.000 | 22607643.096 |    11534.512 |  nan     |  nan     |

## Navigation Latency — Pairwise T-Tests
|    | Comparison             |   Mean Difference (ms) |   t-statistic |   p-value | Diff > 50ms   | Statistically Significant   |
|---:|:-----------------------|-----------------------:|--------------:|----------:|:--------------|:----------------------------|
|  0 | JAWS vs. NVDA          |                 105.12 |          8.95 |     0     | Yes           | Yes                         |
|  1 | JAWS vs. SUPERNOVA     |                  33.53 |          2.22 |     0.027 | No            | Yes                         |
|  2 | JAWS vs. NARRATOR      |                   7.47 |          0.48 |     0.632 | No            | No                          |
|  3 | NVDA vs. SUPERNOVA     |                 -71.59 |         -6.43 |     0     | Yes           | Yes                         |
|  4 | NVDA vs. NARRATOR      |                 -97.65 |         -8.32 |     0     | Yes           | Yes                         |
|  5 | SUPERNOVA vs. NARRATOR |                 -26.07 |         -1.72 |     0.085 | No            | No                          |
## Load Time — Descriptive Statistics
| ScreenReader   |   count |     mean |   median |   mode |     std |         var |   min |   q25 |   q75 |   iqr |    max |     skew |       kurt |
|:---------------|--------:|---------:|---------:|-------:|--------:|------------:|------:|------:|------:|------:|-------:|---------:|-----------:|
| JAWS           |     495 | 53284.8  |    44000 |   5000 | 49296.7 | 2.43017e+09 |  1000 | 10000 | 82000 | 72000 | 183000 | 0.933324 | -0.120996  |
| SUPERNOVA      |     495 | 48236.4  |    32000 |  10000 | 48057.7 | 2.30954e+09 | -2000 | 10000 | 72000 | 62000 | 183000 | 1.05541  |  0.0180717 |
| NARRATOR       |     495 | 47228.3  |    36000 |   1000 | 48128.5 | 2.31635e+09 | -7000 |  6000 | 73000 | 67000 | 177000 | 0.983927 | -0.0378832 |
| NVDA           |     495 |  9058.59 |     9000 |  11000 |  5146.3 | 2.64844e+07 |  1000 |  4000 | 13000 |  9000 |  21000 | 0.310436 | -0.788695  |
## Load Time — Two-Way ANOVA
Analyzes the interaction between Screen Reader and RAM.

|                        |       df |            sum_sq |          mean_sq |        F |   PR(>F) |
|:-----------------------|---------:|------------------:|-----------------:|---------:|---------:|
| C(ScreenReader)        |    3.000 |  620107755050.507 | 206702585016.836 | 1011.253 |    0.000 |
| C(RAM)                 |    4.000 | 2446811095959.597 | 611702773989.899 | 2992.640 |    0.000 |
| C(ScreenReader):C(RAM) |   12.000 |  651336904040.406 |  54278075336.700 |  265.545 |    0.000 |
| Residual               | 1960.000 |  400628686868.687 |    204402391.260 |  nan     |  nan     |

## Load Time — Pairwise T-Tests
|    | Comparison             |   Mean Difference (ms) |   t-statistic |   p-value | Diff > 5000ms   | Statistically Significant   |
|---:|:-----------------------|-----------------------:|--------------:|----------:|:----------------|:----------------------------|
|  0 | JAWS vs. NVDA          |               44226.3  |         19.85 |     0     | Yes             | Yes                         |
|  1 | JAWS vs. SUPERNOVA     |                5048.48 |          1.63 |     0.103 | Yes             | No                          |
|  2 | JAWS vs. NARRATOR      |                6056.57 |          1.96 |     0.051 | Yes             | No                          |
|  3 | NVDA vs. SUPERNOVA     |              -39177.8  |        -18.03 |     0     | Yes             | Yes                         |
|  4 | NVDA vs. NARRATOR      |              -38169.7  |        -17.54 |     0     | Yes             | Yes                         |
|  5 | SUPERNOVA vs. NARRATOR |                1008.08 |          0.33 |     0.742 | No              | No                          |
