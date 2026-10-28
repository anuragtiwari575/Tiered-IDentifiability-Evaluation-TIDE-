# TIDE run report (OASIS-1)

Total time: 0.82 h

## raw / reliability (S=20)

- Pretrained encoders: 30. DI range 0.584-0.916; pixel floor 0.463 [0.268, 0.674]; random encoders 0.237, 0.268.
- SIA-mode on the same subjects: range 0.747-0.984 (2/30 encoders >= 0.95).
- Encoder gain over pixel significant (paired CI > 0): 27/30.
- Max permuted-label control (chance-adjusted): 0.042.
- Top 5 DI: dino_vits16 0.916 [0.842,0.968]; mae_vitb16 0.911 [0.832,0.979]; mobilenetv3_l_in1k 0.911 [0.847,0.963]; densenet121_in1k 0.889 [0.795,0.968]; efficientnet_b0_in1k 0.884 [0.795,0.953]
- Bottom 5 DI: deit_small_in1k 0.695 [0.589,0.795]; resnext50_in1k 0.679 [0.558,0.779]; biomedclip_vitb16 0.626 [0.521,0.726]; clip_vitb16_openai 0.600 [0.474,0.721]; inceptionv3_in1k 0.584 [0.437,0.711]

## t88_gfc / reliability (S=20)

- Pretrained encoders: 30. DI range 0.937-1.000; pixel floor 0.979 [0.947, 1.000]; random encoders 0.895, 0.911.
- SIA-mode on the same subjects: range 0.542-0.984 (1/30 encoders >= 0.95).
- Encoder gain over pixel significant (paired CI > 0): 0/30.
- Max permuted-label control (chance-adjusted): 0.016.
- Top 5 DI: resnet18_in1k 1.000 [1.000,1.000]; vit_base_in21k 1.000 [1.000,1.000]; dino_vits16 1.000 [1.000,1.000]; densenet121_in1k 1.000 [1.000,1.000]; resnet50_in1k 1.000 [1.000,1.000]
- Bottom 5 DI: coatnet0_in1k 0.974 [0.947,0.995]; biomedclip_vitb16 0.974 [0.953,0.989]; clip_vitb16_openai 0.968 [0.942,0.989]; vgg16bn_in1k 0.947 [0.916,0.974]; maxvit_tiny_in1k 0.937 [0.895,0.974]

## t88_masked / reliability (S=20)

- Pretrained encoders: 30. DI range 0.921-1.000; pixel floor 1.000 [1.000, 1.000]; random encoders 0.911, 0.911.
- SIA-mode on the same subjects: range 0.163-0.732 (0/30 encoders >= 0.95).
- Encoder gain over pixel significant (paired CI > 0): 0/30.
- Max permuted-label control (chance-adjusted): 0.011.
- Top 5 DI: mobilenetv3_l_in1k 1.000 [1.000,1.000]; mae_vitb16 1.000 [1.000,1.000]; vit_base_in21k 1.000 [1.000,1.000]; mixer_b16_in21k 1.000 [1.000,1.000]; beit_base_in22k 1.000 [1.000,1.000]
- Bottom 5 DI: convnext_base_in1k 0.947 [0.905,0.984]; coatnet0_in1k 0.942 [0.900,0.979]; biomedclip_vitb16 0.937 [0.900,0.968]; clip_vitb16_openai 0.926 [0.889,0.963]; vgg16bn_in1k 0.921 [0.889,0.953]

## Discriminability: SIA-mode vs TIDE (pretrained encoders)

| cond       | pool        |   S | protocol                            |   mean |    sd |   range |   n_ge_0p95 |   frac_pairs_significant |
|:-----------|:------------|----:|:------------------------------------|-------:|------:|--------:|------------:|-------------------------:|
| raw        | reliability |  20 | SIA-mode (50/50 within acquisition) |  0.86  | 0.047 |   0.237 |           2 |                    0.276 |
| raw        | reliability |  20 | TIDE same_scan_far (within)         |  0.966 | 0.019 |   0.074 |          25 |                    0.299 |
| raw        | reliability |  20 | TIDE DI logreg (rescan_90d)         |  0.798 | 0.093 |   0.332 |           0 |                    0.533 |
| raw        | reliability |  20 | TIDE DI 1-NN (rescan_90d)           |  0.659 | 0.116 |   0.474 |           0 |                    0.616 |
| t88_gfc    | reliability |  20 | SIA-mode (50/50 within acquisition) |  0.854 | 0.095 |   0.442 |           1 |                    0.52  |
| t88_gfc    | reliability |  20 | TIDE same_scan_far (within)         |  0.928 | 0.048 |   0.205 |          10 |                    0.446 |
| t88_gfc    | reliability |  20 | TIDE DI logreg (rescan_90d)         |  0.988 | 0.015 |   0.063 |          28 |                    0.191 |
| t88_gfc    | reliability |  20 | TIDE DI 1-NN (rescan_90d)           |  0.996 | 0.008 |   0.032 |          30 |                    0.101 |
| t88_masked | reliability |  20 | SIA-mode (50/50 within acquisition) |  0.393 | 0.122 |   0.568 |           0 |                    0.545 |
| t88_masked | reliability |  20 | TIDE same_scan_far (within)         |  0.562 | 0.126 |   0.542 |           0 |                    0.595 |
| t88_masked | reliability |  20 | TIDE DI logreg (rescan_90d)         |  0.979 | 0.024 |   0.079 |          25 |                    0.377 |
| t88_masked | reliability |  20 | TIDE DI 1-NN (rescan_90d)           |  0.996 | 0.007 |   0.026 |          30 |                    0.053 |

## Within-session saturation ('all' pool)

| cond       |   S | protocol                            |   min |   max |   n_ge_0p95 |   frac_pairs_significant |
|:-----------|----:|:------------------------------------|------:|------:|------------:|-------------------------:|
| raw        | 404 | SIA-mode (50/50 within acquisition) | 0.61  | 0.933 |           0 |                    0.839 |
| raw        | 404 | TIDE same_scan_adjacent             | 0.764 | 1     |          18 |                    0.883 |
| raw        | 404 | TIDE same_scan_far                  | 0.854 | 0.982 |           8 |                    0.83  |
| raw        | 404 | TIDE repeat_scan                    | 0.826 | 0.992 |          20 |                    0.823 |
| t88_gfc    | 416 | SIA-mode (50/50 within acquisition) | 0.32  | 0.935 |           0 |                    0.894 |
| t88_gfc    | 416 | TIDE same_scan_adjacent             | 0.866 | 1     |          26 |                    0.823 |
| t88_gfc    | 416 | TIDE same_scan_far                  | 0.536 | 0.982 |           2 |                    0.908 |
| t88_masked | 416 | SIA-mode (50/50 within acquisition) | 0.084 | 0.509 |           0 |                    0.876 |
| t88_masked | 416 | TIDE same_scan_adjacent             | 0.508 | 0.983 |           2 |                    0.936 |
| t88_masked | 416 | TIDE same_scan_far                  | 0.168 | 0.728 |           0 |                    0.901 |

## Factor groups (DI)

| cond       | pool        | factor      | comparison        |   n_models |   mean |    lo |    hi |
|:-----------|:------------|:------------|:------------------|-----------:|-------:|------:|------:|
| raw        | reliability | pretraining | self-supervised   |          4 |  0.854 | 0.775 | 0.912 |
| raw        | reliability | pretraining | supervised IN-1k  |         17 |  0.796 | 0.719 | 0.861 |
| raw        | reliability | pretraining | supervised IN-21k |          6 |  0.834 | 0.773 | 0.883 |
| raw        | reliability | pretraining | vision-language   |          2 |  0.613 | 0.505 | 0.708 |
| raw        | reliability | pretraining | weakly supervised |          1 |  0.753 | 0.626 | 0.863 |
| raw        | reliability | family      | CNN               |         14 |  0.795 | 0.714 | 0.863 |
| raw        | reliability | family      | Hybrid            |          2 |  0.797 | 0.716 | 0.868 |
| raw        | reliability | family      | MLP/MetaFormer    |          2 |  0.868 | 0.808 | 0.918 |
| raw        | reliability | family      | Transformer       |         12 |  0.789 | 0.712 | 0.846 |
| t88_gfc    | reliability | pretraining | self-supervised   |          4 |  0.996 | 0.989 | 1     |
| t88_gfc    | reliability | pretraining | supervised IN-1k  |         17 |  0.987 | 0.981 | 0.991 |
| t88_gfc    | reliability | pretraining | supervised IN-21k |          6 |  0.993 | 0.987 | 0.997 |
| t88_gfc    | reliability | pretraining | vision-language   |          2 |  0.971 | 0.955 | 0.984 |
| t88_gfc    | reliability | pretraining | weakly supervised |          1 |  0.995 | 0.984 | 1     |
| t88_gfc    | reliability | family      | CNN               |         14 |  0.992 | 0.989 | 0.994 |
| t88_gfc    | reliability | family      | Hybrid            |          2 |  0.955 | 0.926 | 0.979 |
| t88_gfc    | reliability | family      | MLP/MetaFormer    |          2 |  0.997 | 0.992 | 1     |
| t88_gfc    | reliability | family      | Transformer       |         12 |  0.989 | 0.983 | 0.993 |
| t88_masked | reliability | pretraining | self-supervised   |          4 |  0.993 | 0.987 | 0.999 |
| t88_masked | reliability | pretraining | supervised IN-1k  |         17 |  0.976 | 0.967 | 0.985 |
| t88_masked | reliability | pretraining | supervised IN-21k |          6 |  0.991 | 0.985 | 0.996 |
| t88_masked | reliability | pretraining | vision-language   |          2 |  0.932 | 0.911 | 0.95  |
| t88_masked | reliability | pretraining | weakly supervised |          1 |  1     | 1     | 1     |
| t88_masked | reliability | family      | CNN               |         14 |  0.98  | 0.972 | 0.988 |
| t88_masked | reliability | family      | Hybrid            |          2 |  0.947 | 0.926 | 0.971 |
| t88_masked | reliability | family      | MLP/MetaFormer    |          2 |  0.997 | 0.992 | 1     |
| t88_masked | reliability | family      | Transformer       |         12 |  0.98  | 0.975 | 0.986 |

Significant group differences:

- raw/reliability pretraining: self-supervised minus supervised IN-1k = +0.058 [+0.023, +0.099]
- raw/reliability pretraining: self-supervised minus vision-language = +0.241 [+0.179, +0.307]
- raw/reliability pretraining: self-supervised minus weakly supervised = +0.101 [+0.007, +0.215]
- raw/reliability pretraining: supervised IN-1k minus supervised IN-21k = -0.039 [-0.080, -0.003]
- raw/reliability pretraining: supervised IN-1k minus vision-language = +0.183 [+0.122, +0.247]
- raw/reliability pretraining: supervised IN-21k minus vision-language = +0.221 [+0.151, +0.293]
- raw/reliability pretraining: vision-language minus weakly supervised = -0.139 [-0.250, -0.032]
- raw/reliability family: CNN minus MLP/MetaFormer = -0.073 [-0.110, -0.043]
- raw/reliability family: Hybrid minus MLP/MetaFormer = -0.071 [-0.124, -0.016]
- raw/reliability family: MLP/MetaFormer minus Transformer = +0.080 [+0.049, +0.111]
- t88_gfc/reliability pretraining: self-supervised minus supervised IN-1k = +0.009 [+0.004, +0.015]
- t88_gfc/reliability pretraining: self-supervised minus vision-language = +0.025 [+0.009, +0.042]
- t88_gfc/reliability pretraining: supervised IN-1k minus supervised IN-21k = -0.006 [-0.012, -0.000]
- t88_gfc/reliability pretraining: supervised IN-1k minus vision-language = +0.016 [+0.001, +0.032]
- t88_gfc/reliability pretraining: supervised IN-21k minus vision-language = +0.022 [+0.008, +0.037]
- t88_gfc/reliability pretraining: vision-language minus weakly supervised = -0.024 [-0.037, -0.013]
- t88_gfc/reliability family: CNN minus Hybrid = +0.036 [+0.013, +0.065]
- t88_gfc/reliability family: Hybrid minus MLP/MetaFormer = -0.042 [-0.071, -0.016]
- t88_gfc/reliability family: Hybrid minus Transformer = -0.033 [-0.059, -0.012]
- t88_gfc/reliability family: MLP/MetaFormer minus Transformer = +0.009 [+0.000, +0.016]
- t88_masked/reliability pretraining: self-supervised minus supervised IN-1k = +0.018 [+0.007, +0.028]
- t88_masked/reliability pretraining: self-supervised minus vision-language = +0.062 [+0.041, +0.084]
- t88_masked/reliability pretraining: self-supervised minus weakly supervised = -0.007 [-0.013, -0.001]
- t88_masked/reliability pretraining: supervised IN-1k minus supervised IN-21k = -0.016 [-0.023, -0.009]
- t88_masked/reliability pretraining: supervised IN-1k minus vision-language = +0.044 [+0.023, +0.065]
- t88_masked/reliability pretraining: supervised IN-1k minus weakly supervised = -0.024 [-0.033, -0.015]
- t88_masked/reliability pretraining: supervised IN-21k minus vision-language = +0.060 [+0.042, +0.077]
- t88_masked/reliability pretraining: supervised IN-21k minus weakly supervised = -0.009 [-0.015, -0.004]
- t88_masked/reliability pretraining: vision-language minus weakly supervised = -0.068 [-0.089, -0.050]
- t88_masked/reliability family: CNN minus Hybrid = +0.032 [+0.014, +0.051]
- t88_masked/reliability family: CNN minus MLP/MetaFormer = -0.018 [-0.026, -0.010]
- t88_masked/reliability family: Hybrid minus MLP/MetaFormer = -0.050 [-0.071, -0.029]
- t88_masked/reliability family: Hybrid minus Transformer = -0.033 [-0.052, -0.012]
- t88_masked/reliability family: MLP/MetaFormer minus Transformer = +0.017 [+0.011, +0.023]

## Capacity (Spearman log-params vs DI)

| cond       | pool        | subset         |   n_models |   spearman_logparams_vs_DI |     lo |     hi |
|:-----------|:------------|:---------------|-----------:|---------------------------:|-------:|-------:|
| raw        | reliability | all pretrained |         30 |                     -0.203 | -0.265 | -0.065 |
| raw        | reliability | CNN            |         14 |                     -0.512 | -0.607 | -0.184 |
| raw        | reliability | Transformer    |         12 |                      0.018 | -0.18  |  0.131 |
| t88_gfc    | reliability | all pretrained |         30 |                     -0.495 | -0.558 | -0.339 |
| t88_gfc    | reliability | CNN            |         14 |                     -0.66  | -0.787 | -0.359 |
| t88_gfc    | reliability | Transformer    |         12 |                     -0.305 | -0.502 |  0.073 |
| t88_masked | reliability | all pretrained |         30 |                     -0.323 | -0.472 | -0.198 |
| t88_masked | reliability | CNN            |         14 |                     -0.552 | -0.696 | -0.315 |
| t88_masked | reliability | Transformer    |         12 |                     -0.277 | -0.392 | -0.059 |

## Probe geometry

| cond       | pool        |   spearman_logreg_vs_1nn |   median_LG |
|:-----------|:------------|-------------------------:|------------:|
| raw        | reliability |                    0.887 |       0.826 |
| t88_gfc    | reliability |                    0.53  |       1.005 |
| t88_masked | reliability |                    0.681 |       1.011 |

## Preprocessing ladder (rescan DI)

- pixel: raw 0.463, t88_gfc 0.979, t88_masked 1.000
- median pretrained: raw 0.826, t88_gfc 0.995, t88_masked 0.989
- delta_raw_to_t88_gfc: significant drop 0/30, significant rise 30/30
- delta_t88_gfc_to_t88_masked: significant drop 1/30, significant rise 0/30
- delta_raw_to_t88_masked: significant drop 0/30, significant rise 30/30

## Near-duplicate injection (cross-session eval contaminated)

- raw/reliability: median pretrained 0.826 -> 0.989; pixel 0.463 -> 1.000
- t88_gfc/reliability: median pretrained 0.995 -> 1.000; pixel 0.979 -> 1.000
- t88_masked/reliability: median pretrained 0.989 -> 0.913; pixel 1.000 -> 1.000

## Positive control (identity-supervised PCA+LDA head, disjoint training subjects)

| cond   | model              |   DI_base |   DI_LDA |   delta |     lo |    hi | significant   |   SIA_LDA |
|:-------|:-------------------|----------:|---------:|--------:|-------:|------:|:--------------|----------:|
| raw    | pixel              |     0.463 |    0.426 |  -0.037 | -0.116 | 0.016 | False         |     0.953 |
| raw    | resnet18_in1k      |     0.816 |    0.795 |  -0.021 | -0.079 | 0.032 | False         |     0.942 |
| raw    | resnet50_in1k      |     0.747 |    0.821 |   0.074 |  0.011 | 0.142 | True          |     0.958 |
| raw    | convnext_tiny_in1k |     0.853 |    0.868 |   0.016 | -0.058 | 0.079 | False         |     0.958 |
| raw    | vit_base_in21k     |     0.879 |    0.9   |   0.021 | -0.016 | 0.058 | False         |     0.9   |
| raw    | dino_vits16        |     0.916 |    0.921 |   0.005 | -0.032 | 0.042 | False         |     0.953 |
| raw    | clip_vitb16_openai |     0.6   |    0.737 |   0.137 |  0.058 | 0.211 | True          |     0.895 |
| raw    | biomedclip_vitb16  |     0.626 |    0.826 |   0.2   |  0.126 | 0.279 | True          |     0.926 |
