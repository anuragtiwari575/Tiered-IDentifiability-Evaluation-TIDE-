# TIDE spatial-offset x session grid (OASIS-1, registered)

Total time: 1.35 h

## t88_gfc

- Rescan at 0 mm: pixel 0.979; pretrained 0.942-1.000
- SIG (rescan, 2-20 mm): pixel 0.969 [0.939,0.993]; pretrained 0.758-0.994; random 0.676, 0.605
- Encoder gain over pixel on SIG: significantly positive 1/30, significantly negative 16/30
- d50 rescan (mm): pixel inf; pretrained median inf
- d50 within (mm): pixel inf; pretrained median inf
- Mean session penalty (within minus rescan, same offset): pretrained median +0.046, pixel +0.022

- Top 5 SIG: mae_vitb16 0.994; dino_vits16 0.985; densenet121_in1k 0.980; efficientnet_b0_in1k 0.974; mobilenetv3_l_in1k 0.969
- Bottom 5 SIG: deit_small_in1k 0.863; maxvit_tiny_in1k 0.857; biomedclip_vitb16 0.807; inceptionv3_in1k 0.774; vgg16bn_in1k 0.758

## t88_masked

- Rescan at 0 mm: pixel 1.000; pretrained 0.889-1.000
- SIG (rescan, 2-20 mm): pixel 0.932 [0.911,0.952]; pretrained 0.493-0.891; random 0.317, 0.382
- Encoder gain over pixel on SIG: significantly positive 0/30, significantly negative 30/30
- d50 rescan (mm): pixel inf; pretrained median inf
- d50 within (mm): pixel inf; pretrained median inf
- Mean session penalty (within minus rescan, same offset): pretrained median +0.040, pixel +0.004

- Top 5 SIG: mae_vitb16 0.891; dino_vits16 0.834; densenet121_in1k 0.808; mobilenetv3_l_in1k 0.759; efficientnet_b0_in1k 0.734
- Bottom 5 SIG: maxvit_tiny_in1k 0.582; clip_vitb16_openai 0.574; biomedclip_vitb16 0.554; resnext50_in1k 0.551; vgg16bn_in1k 0.493

## Discriminability per cell (pretrained encoders)

| variant    | pool        |   S | session            |   offset_mm |   mean |    sd |   n_ge_0p95 |   frac_pairs_significant |
|:-----------|:------------|----:|:-------------------|------------:|-------:|------:|------------:|-------------------------:|
| t88_masked | reliability |  20 | within             |           1 |  0.913 | 0.058 |           7 |                    0.522 |
| t88_masked | reliability |  20 | within             |           2 |  0.725 | 0.109 |           0 |                    0.595 |
| t88_masked | reliability |  20 | within             |           3 |  0.616 | 0.123 |           0 |                    0.607 |
| t88_masked | reliability |  20 | within             |           4 |  0.601 | 0.12  |           0 |                    0.593 |
| t88_masked | reliability |  20 | within             |           6 |  0.757 | 0.072 |           0 |                    0.448 |
| t88_masked | reliability |  20 | within             |           8 |  0.907 | 0.044 |           4 |                    0.476 |
| t88_masked | reliability |  20 | within             |          10 |  0.607 | 0.116 |           0 |                    0.568 |
| t88_masked | reliability |  20 | within             |          15 |  0.879 | 0.031 |           0 |                    0.384 |
| t88_masked | reliability |  20 | within             |          20 |  0.568 | 0.11  |           0 |                    0.559 |
| t88_masked | reliability |  20 | rescan             |           0 |  0.979 | 0.028 |          27 |                    0.34  |
| t88_masked | reliability |  20 | rescan             |           1 |  0.851 | 0.084 |           3 |                    0.609 |
| t88_masked | reliability |  20 | rescan             |           2 |  0.682 | 0.106 |           0 |                    0.559 |
| t88_masked | reliability |  20 | rescan             |           3 |  0.577 | 0.11  |           0 |                    0.57  |
| t88_masked | reliability |  20 | rescan             |           4 |  0.553 | 0.117 |           0 |                    0.54  |
| t88_masked | reliability |  20 | rescan             |           6 |  0.714 | 0.084 |           0 |                    0.499 |
| t88_masked | reliability |  20 | rescan             |           8 |  0.86  | 0.061 |           2 |                    0.517 |
| t88_masked | reliability |  20 | rescan             |          10 |  0.568 | 0.101 |           0 |                    0.464 |
| t88_masked | reliability |  20 | rescan             |          15 |  0.857 | 0.04  |           0 |                    0.345 |
| t88_masked | reliability |  20 | rescan             |          20 |  0.527 | 0.1   |           0 |                    0.48  |
| t88_masked | all         | 416 | within             |           1 |  0.814 | 0.105 |           2 |                    0.922 |
| t88_masked | all         | 416 | within             |           2 |  0.557 | 0.139 |           0 |                    0.91  |
| t88_masked | all         | 416 | within             |           3 |  0.42  | 0.132 |           0 |                    0.899 |
| t88_masked | all         | 416 | within             |           4 |  0.405 | 0.132 |           0 |                    0.908 |
| t88_masked | all         | 416 | within             |           6 |  0.624 | 0.1   |           0 |                    0.91  |
| t88_masked | all         | 416 | within             |           8 |  0.837 | 0.059 |           0 |                    0.897 |
| t88_masked | all         | 416 | within             |          10 |  0.428 | 0.127 |           0 |                    0.894 |
| t88_masked | all         | 416 | within             |          15 |  0.839 | 0.018 |           0 |                    0.749 |
| t88_masked | all         | 416 | within             |          20 |  0.38  | 0.11  |           0 |                    0.894 |
| t88_masked | reliability |  20 | SIG (rescan, d>=2) |         nan |  0.667 | 0.086 |           0 |                    0.669 |
| t88_gfc    | reliability |  20 | within             |           1 |  0.995 | 0.013 |          29 |                    0.163 |
| t88_gfc    | reliability |  20 | within             |           2 |  0.977 | 0.036 |          26 |                    0.363 |
| t88_gfc    | reliability |  20 | within             |           3 |  0.96  | 0.056 |          25 |                    0.389 |
| t88_gfc    | reliability |  20 | within             |           4 |  0.955 | 0.055 |          23 |                    0.432 |
| t88_gfc    | reliability |  20 | within             |           6 |  0.968 | 0.039 |          26 |                    0.389 |
| t88_gfc    | reliability |  20 | within             |           8 |  0.982 | 0.017 |          28 |                    0.163 |
| t88_gfc    | reliability |  20 | within             |          10 |  0.951 | 0.06  |          24 |                    0.359 |
| t88_gfc    | reliability |  20 | within             |          15 |  0.961 | 0.024 |          24 |                    0.267 |
| t88_gfc    | reliability |  20 | within             |          20 |  0.901 | 0.061 |           4 |                    0.444 |
| t88_gfc    | reliability |  20 | rescan             |           0 |  0.987 | 0.016 |          27 |                    0.216 |
| t88_gfc    | reliability |  20 | rescan             |           1 |  0.97  | 0.032 |          25 |                    0.428 |
| t88_gfc    | reliability |  20 | rescan             |           2 |  0.926 | 0.062 |          11 |                    0.561 |
| t88_gfc    | reliability |  20 | rescan             |           3 |  0.9   | 0.075 |           6 |                    0.6   |
| t88_gfc    | reliability |  20 | rescan             |           4 |  0.89  | 0.072 |           6 |                    0.57  |
| t88_gfc    | reliability |  20 | rescan             |           6 |  0.933 | 0.055 |          15 |                    0.467 |
| t88_gfc    | reliability |  20 | rescan             |           8 |  0.963 | 0.028 |          23 |                    0.324 |
| t88_gfc    | reliability |  20 | rescan             |          10 |  0.895 | 0.074 |           6 |                    0.536 |
| t88_gfc    | reliability |  20 | rescan             |          15 |  0.94  | 0.03  |          10 |                    0.338 |
| t88_gfc    | reliability |  20 | rescan             |          20 |  0.849 | 0.081 |           2 |                    0.54  |
| t88_gfc    | all         | 416 | within             |           1 |  0.98  | 0.036 |          27 |                    0.814 |
| t88_gfc    | all         | 416 | within             |           2 |  0.924 | 0.091 |          15 |                    0.91  |
| t88_gfc    | all         | 416 | within             |           3 |  0.89  | 0.109 |           9 |                    0.89  |
| t88_gfc    | all         | 416 | within             |           4 |  0.877 | 0.115 |           8 |                    0.887 |
| t88_gfc    | all         | 416 | within             |           6 |  0.92  | 0.073 |          11 |                    0.887 |
| t88_gfc    | all         | 416 | within             |           8 |  0.962 | 0.031 |          26 |                    0.777 |
| t88_gfc    | all         | 416 | within             |          10 |  0.876 | 0.107 |           5 |                    0.89  |
| t88_gfc    | all         | 416 | within             |          15 |  0.924 | 0.028 |           4 |                    0.798 |
| t88_gfc    | all         | 416 | within             |          20 |  0.801 | 0.106 |           1 |                    0.857 |
| t88_gfc    | reliability |  20 | SIG (rescan, d>=2) |         nan |  0.912 | 0.057 |           6 |                    0.667 |

## Factor groups on SIG

| variant    | factor      | comparison        |   n_models |   mean |    lo |    hi |
|:-----------|:------------|:------------------|-----------:|-------:|------:|------:|
| t88_masked | pretraining | self-supervised   |          4 |  0.786 | 0.757 | 0.816 |
| t88_masked | pretraining | supervised IN-1k  |         17 |  0.647 | 0.617 | 0.68  |
| t88_masked | pretraining | supervised IN-21k |          6 |  0.686 | 0.658 | 0.713 |
| t88_masked | pretraining | vision-language   |          2 |  0.564 | 0.53  | 0.6   |
| t88_masked | pretraining | weakly supervised |          1 |  0.632 | 0.586 | 0.676 |
| t88_masked | family      | CNN               |         14 |  0.657 | 0.626 | 0.69  |
| t88_masked | family      | Hybrid            |          2 |  0.593 | 0.556 | 0.631 |
| t88_masked | family      | MLP/MetaFormer    |          2 |  0.697 | 0.667 | 0.725 |
| t88_masked | family      | Transformer       |         12 |  0.686 | 0.66  | 0.713 |
| t88_gfc    | pretraining | self-supervised   |          4 |  0.946 | 0.928 | 0.962 |
| t88_gfc    | pretraining | supervised IN-1k  |         17 |  0.904 | 0.881 | 0.922 |
| t88_gfc    | pretraining | supervised IN-21k |          6 |  0.932 | 0.91  | 0.951 |
| t88_gfc    | pretraining | vision-language   |          2 |  0.843 | 0.8   | 0.88  |
| t88_gfc    | pretraining | weakly supervised |          1 |  0.933 | 0.909 | 0.955 |
| t88_gfc    | family      | CNN               |         14 |  0.909 | 0.886 | 0.927 |
| t88_gfc    | family      | Hybrid            |          2 |  0.877 | 0.836 | 0.913 |
| t88_gfc    | family      | MLP/MetaFormer    |          2 |  0.941 | 0.921 | 0.959 |
| t88_gfc    | family      | Transformer       |         12 |  0.916 | 0.895 | 0.935 |

Significant differences:

- t88_masked pretraining: self-supervised minus supervised IN-1k = +0.139 [+0.121,+0.157]
- t88_masked pretraining: self-supervised minus supervised IN-21k = +0.100 [+0.079,+0.119]
- t88_masked pretraining: self-supervised minus vision-language = +0.222 [+0.192,+0.249]
- t88_masked pretraining: self-supervised minus weakly supervised = +0.154 [+0.115,+0.199]
- t88_masked pretraining: supervised IN-1k minus supervised IN-21k = -0.039 [-0.057,-0.021]
- t88_masked pretraining: supervised IN-1k minus vision-language = +0.083 [+0.048,+0.112]
- t88_masked pretraining: supervised IN-21k minus vision-language = +0.121 [+0.093,+0.148]
- t88_masked pretraining: supervised IN-21k minus weakly supervised = +0.054 [+0.020,+0.093]
- t88_masked pretraining: vision-language minus weakly supervised = -0.067 [-0.108,-0.020]
- t88_masked family: CNN minus Hybrid = +0.064 [+0.039,+0.089]
- t88_masked family: CNN minus MLP/MetaFormer = -0.040 [-0.068,-0.014]
- t88_masked family: CNN minus Transformer = -0.029 [-0.046,-0.013]
- t88_masked family: Hybrid minus MLP/MetaFormer = -0.104 [-0.141,-0.063]
- t88_masked family: Hybrid minus Transformer = -0.093 [-0.117,-0.068]
- t88_gfc pretraining: self-supervised minus supervised IN-1k = +0.042 [+0.028,+0.057]
- t88_gfc pretraining: self-supervised minus supervised IN-21k = +0.014 [+0.000,+0.028]
- t88_gfc pretraining: self-supervised minus vision-language = +0.103 [+0.075,+0.136]
- t88_gfc pretraining: supervised IN-1k minus supervised IN-21k = -0.028 [-0.040,-0.016]
- t88_gfc pretraining: supervised IN-1k minus vision-language = +0.061 [+0.031,+0.095]
- t88_gfc pretraining: supervised IN-1k minus weakly supervised = -0.029 [-0.047,-0.010]
- t88_gfc pretraining: supervised IN-21k minus vision-language = +0.089 [+0.058,+0.124]
- t88_gfc pretraining: vision-language minus weakly supervised = -0.090 [-0.133,-0.052]
- t88_gfc family: CNN minus Hybrid = +0.033 [+0.004,+0.067]
- t88_gfc family: CNN minus MLP/MetaFormer = -0.032 [-0.046,-0.019]
- t88_gfc family: Hybrid minus MLP/MetaFormer = -0.065 [-0.100,-0.033]
- t88_gfc family: Hybrid minus Transformer = -0.039 [-0.072,-0.008]
- t88_gfc family: MLP/MetaFormer minus Transformer = +0.026 [+0.011,+0.042]

## Capacity (Spearman log-params vs SIG)

| variant    | subset         |   n_models |   spearman_logparams_vs_SIG |     lo |     hi |
|:-----------|:---------------|-----------:|----------------------------:|-------:|-------:|
| t88_masked | all pretrained |         30 |                      -0.311 | -0.396 | -0.202 |
| t88_masked | CNN            |         14 |                      -0.612 | -0.731 | -0.528 |
| t88_masked | Transformer    |         12 |                      -0.205 | -0.314 | -0.021 |
| t88_gfc    | all pretrained |         30 |                      -0.284 | -0.375 | -0.204 |
| t88_gfc    | CNN            |         14 |                      -0.59  | -0.702 | -0.442 |
| t88_gfc    | Transformer    |         12 |                      -0.042 | -0.183 |  0.12  |
