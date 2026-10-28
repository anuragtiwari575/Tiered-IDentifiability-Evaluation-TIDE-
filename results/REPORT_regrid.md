# TIDE re-analysis: identifiability vs distance to nearest probe-fit slice

Total time: 0.14 h

## Per distance bin (pretrained encoders; pixel = pixel floor; logreg, chance-adjusted)

| cond       | pool        | design   |   S | session             |   d_mm |   n_per_subject |   pixel |   mean |   min |   max |   n_above_pixel |   n_below_pixel |   frac_pairs_significant |
|:-----------|:------------|:---------|----:|:--------------------|-------:|----------------:|--------:|-------:|------:|------:|----------------:|----------------:|-------------------------:|
| raw        | all         | dense    | 404 | repeat              |   0    |              16 |   0.98  |  0.955 | 0.833 | 0.992 |               1 |              17 |                    0.818 |
| raw        | all         | dense    | 404 | repeat              |   1.25 |              13 |   0.981 |  0.901 | 0.687 | 0.986 |               0 |              27 |                    0.894 |
| raw        | all         | dense    | 404 | within              |   1.25 |              13 |   1     |  0.947 | 0.757 | 0.999 |               0 |              29 |                    0.894 |
| raw        | all         | sparse   | 404 | repeat              |   0    |               7 |   0.983 |  0.965 | 0.888 | 0.996 |               2 |              14 |                    0.77  |
| raw        | all         | sparse   | 404 | repeat              |   1.25 |               7 |   0.982 |  0.909 | 0.709 | 0.988 |               0 |              25 |                    0.903 |
| raw        | all         | sparse   | 404 | repeat              |   7.5  |              12 |   0.843 |  0.522 | 0.276 | 0.907 |               2 |              28 |                    0.894 |
| raw        | all         | sparse   | 404 | within              |   1.25 |               7 |   1     |  0.957 | 0.81  | 1     |               0 |              28 |                    0.883 |
| raw        | all         | sparse   | 404 | within              |   7.5  |              12 |   0.88  |  0.567 | 0.309 | 0.946 |               2 |              28 |                    0.903 |
| raw        | all         | sparse   | 404 | GEN repeat (d>=2mm) | nan    |             nan |   0.843 |  0.522 | 0.276 | 0.907 |             nan |             nan |                    0.894 |
| raw        | reliability | dense    |  20 | repeat              |   0    |              16 |   1     |  0.995 | 0.974 | 1     |               0 |               1 |                    0.037 |
| raw        | reliability | dense    |  20 | repeat              |   1.25 |              13 |   1     |  0.974 | 0.862 | 1     |               0 |              15 |                    0.398 |
| raw        | reliability | dense    |  20 | rescan              |   0    |              16 |   0.464 |  0.8   | 0.592 | 0.918 |              27 |               0 |                    0.52  |
| raw        | reliability | dense    |  20 | rescan              |   1.25 |              13 |   0.453 |  0.806 | 0.555 | 0.931 |              28 |               0 |                    0.605 |
| raw        | reliability | dense    |  20 | within              |   1.25 |              13 |   1     |  0.982 | 0.903 | 1     |               0 |              10 |                    0.393 |
| raw        | reliability | sparse   |  20 | repeat              |   0    |               7 |   1     |  0.994 | 0.97  | 1     |               0 |               1 |                    0.046 |
| raw        | reliability | sparse   |  20 | repeat              |   1.25 |               7 |   1     |  0.976 | 0.865 | 1     |               0 |               8 |                    0.271 |
| raw        | reliability | sparse   |  20 | repeat              |   7.5  |              12 |   0.917 |  0.722 | 0.535 | 0.982 |               1 |              26 |                    0.517 |
| raw        | reliability | sparse   |  20 | rescan              |   0    |               7 |   0.444 |  0.738 | 0.549 | 0.91  |              22 |               0 |                    0.418 |
| raw        | reliability | sparse   |  20 | rescan              |   1.25 |               7 |   0.451 |  0.764 | 0.526 | 0.925 |              22 |               0 |                    0.547 |
| raw        | reliability | sparse   |  20 | rescan              |   7.5  |              12 |   0.412 |  0.574 | 0.39  | 0.864 |               8 |               0 |                    0.492 |
| raw        | reliability | sparse   |  20 | within              |   1.25 |               7 |   1     |  0.981 | 0.925 | 1     |               0 |               6 |                    0.214 |
| raw        | reliability | sparse   |  20 | within              |   7.5  |              12 |   0.917 |  0.735 | 0.518 | 0.982 |               1 |              26 |                    0.462 |
| raw        | reliability | sparse   |  20 | GEN repeat (d>=2mm) | nan    |             nan |   0.917 |  0.722 | 0.535 | 0.982 |             nan |             nan |                    0.497 |
| raw        | reliability | sparse   |  20 | GEN rescan (d>=2mm) | nan    |             nan |   0.412 |  0.574 | 0.39  | 0.864 |             nan |             nan |                    0.494 |
| t88_gfc    | all         | dense    | 416 | within              |   1    |              20 |   1     |  0.982 | 0.849 | 1     |               0 |              25 |                    0.841 |
| t88_gfc    | all         | dense    | 416 | within              |   2    |              22 |   1     |  0.921 | 0.591 | 0.999 |               0 |              30 |                    0.91  |
| t88_gfc    | all         | dense    | 416 | within              |   3    |              23 |   1     |  0.884 | 0.491 | 0.998 |               0 |              30 |                    0.901 |
| t88_gfc    | all         | dense    | 416 | within              |   4    |               5 |   0.998 |  0.844 | 0.401 | 0.996 |               0 |              29 |                    0.878 |
| t88_gfc    | all         | sparse   | 416 | within              |   1    |               5 |   1     |  0.981 | 0.878 | 1     |               0 |              24 |                    0.747 |
| t88_gfc    | all         | sparse   | 416 | within              |   2    |              13 |   1     |  0.867 | 0.557 | 0.999 |               0 |              30 |                    0.897 |
| t88_gfc    | all         | sparse   | 416 | within              |   3    |               8 |   0.995 |  0.773 | 0.368 | 0.992 |               0 |              29 |                    0.922 |
| t88_gfc    | all         | sparse   | 416 | within              |   4    |               9 |   0.955 |  0.707 | 0.278 | 0.983 |               1 |              29 |                    0.901 |
| t88_gfc    | all         | sparse   | 416 | within              |   5    |              12 |   0.936 |  0.673 | 0.233 | 0.982 |               1 |              28 |                    0.89  |
| t88_gfc    | all         | sparse   | 416 | within              |   6    |               9 |   0.861 |  0.639 | 0.199 | 0.976 |               2 |              28 |                    0.901 |
| t88_gfc    | all         | sparse   | 416 | within              |   7    |              17 |   0.878 |  0.631 | 0.198 | 0.969 |               2 |              28 |                    0.897 |
| t88_gfc    | reliability | dense    |  20 | rescan              |   0    |              22 |   0.983 |  0.989 | 0.957 | 1     |               0 |               0 |                    0.195 |
| t88_gfc    | reliability | dense    |  20 | rescan              |   1    |              20 |   0.979 |  0.971 | 0.887 | 1     |               0 |               4 |                    0.517 |
| t88_gfc    | reliability | dense    |  20 | rescan              |   2    |              22 |   0.978 |  0.929 | 0.768 | 1     |               0 |              13 |                    0.6   |
| t88_gfc    | reliability | dense    |  20 | rescan              |   3    |              23 |   0.97  |  0.898 | 0.721 | 0.998 |               0 |              15 |                    0.648 |
| t88_gfc    | reliability | dense    |  20 | rescan              |   4    |               5 |   0.968 |  0.866 | 0.653 | 1     |               0 |              20 |                    0.453 |
| t88_gfc    | reliability | dense    |  20 | within              |   1    |              20 |   1     |  0.995 | 0.937 | 1     |               0 |               4 |                    0.207 |
| t88_gfc    | reliability | dense    |  20 | within              |   2    |              22 |   1     |  0.974 | 0.861 | 1     |               0 |              18 |                    0.536 |
| t88_gfc    | reliability | dense    |  20 | within              |   3    |              23 |   1     |  0.957 | 0.769 | 1     |               0 |              22 |                    0.503 |
| t88_gfc    | reliability | dense    |  20 | within              |   4    |               5 |   1     |  0.941 | 0.705 | 1     |               0 |              11 |                    0.382 |
| t88_gfc    | reliability | dense    |  20 | GEN rescan (d>=2mm) | nan    |             nan |   0.972 |  0.898 | 0.715 | 0.999 |             nan |             nan |                    0.646 |
| t88_gfc    | reliability | sparse   |  20 | rescan              |   0    |              13 |   0.984 |  0.991 | 0.927 | 1     |               0 |               1 |                    0.051 |
| t88_gfc    | reliability | sparse   |  20 | rescan              |   1    |               5 |   0.989 |  0.962 | 0.853 | 1     |               0 |               6 |                    0.345 |
| t88_gfc    | reliability | sparse   |  20 | rescan              |   2    |              13 |   0.988 |  0.873 | 0.668 | 1     |               0 |              24 |                    0.618 |
| t88_gfc    | reliability | sparse   |  20 | rescan              |   3    |               8 |   0.987 |  0.805 | 0.586 | 1     |               0 |              27 |                    0.595 |
| t88_gfc    | reliability | sparse   |  20 | rescan              |   4    |               9 |   0.947 |  0.75  | 0.503 | 0.977 |               0 |              26 |                    0.579 |
| t88_gfc    | reliability | sparse   |  20 | rescan              |   5    |              12 |   0.969 |  0.727 | 0.43  | 0.991 |               0 |              28 |                    0.545 |
| t88_gfc    | reliability | sparse   |  20 | rescan              |   6    |               9 |   0.889 |  0.707 | 0.363 | 0.982 |               1 |              25 |                    0.568 |
| t88_gfc    | reliability | sparse   |  20 | rescan              |   7    |              17 |   0.879 |  0.707 | 0.368 | 0.988 |               1 |              25 |                    0.536 |
| t88_gfc    | reliability | sparse   |  20 | within              |   1    |               5 |   1     |  0.993 | 0.926 | 1     |               0 |               2 |                    0.115 |
| t88_gfc    | reliability | sparse   |  20 | within              |   2    |              13 |   1     |  0.942 | 0.757 | 1     |               0 |              17 |                    0.529 |
| t88_gfc    | reliability | sparse   |  20 | within              |   3    |               8 |   1     |  0.884 | 0.572 | 1     |               0 |              25 |                    0.602 |
| t88_gfc    | reliability | sparse   |  20 | within              |   4    |               9 |   0.971 |  0.85  | 0.503 | 1     |               1 |              21 |                    0.611 |
| t88_gfc    | reliability | sparse   |  20 | within              |   5    |              12 |   0.974 |  0.829 | 0.456 | 1     |               0 |              23 |                    0.595 |
| t88_gfc    | reliability | sparse   |  20 | within              |   6    |               9 |   0.912 |  0.799 | 0.468 | 0.994 |               2 |              18 |                    0.584 |
| t88_gfc    | reliability | sparse   |  20 | within              |   7    |              17 |   0.913 |  0.788 | 0.399 | 0.991 |               2 |              20 |                    0.536 |
| t88_gfc    | reliability | sparse   |  20 | GEN rescan (d>=2mm) | nan    |             nan |   0.943 |  0.761 | 0.497 | 0.99  |             nan |             nan |                    0.648 |
| t88_masked | all         | dense    | 416 | within              |   1    |              20 |   1     |  0.83  | 0.546 | 0.988 |               0 |              30 |                    0.92  |
| t88_masked | all         | dense    | 416 | within              |   2    |              22 |   0.967 |  0.536 | 0.293 | 0.866 |               0 |              30 |                    0.929 |
| t88_masked | all         | dense    | 416 | within              |   3    |              23 |   0.9   |  0.409 | 0.186 | 0.781 |               0 |              30 |                    0.908 |
| t88_masked | all         | dense    | 416 | within              |   4    |               5 |   0.728 |  0.33  | 0.138 | 0.682 |               0 |              30 |                    0.867 |
| t88_masked | all         | sparse   | 416 | within              |   1    |               5 |   1     |  0.806 | 0.573 | 0.982 |               0 |              30 |                    0.92  |
| t88_masked | all         | sparse   | 416 | within              |   2    |              13 |   0.961 |  0.408 | 0.208 | 0.767 |               0 |              30 |                    0.92  |
| t88_masked | all         | sparse   | 416 | within              |   3    |               8 |   0.781 |  0.228 | 0.103 | 0.557 |               0 |              30 |                    0.878 |
| t88_masked | all         | sparse   | 416 | within              |   4    |               9 |   0.48  |  0.175 | 0.064 | 0.466 |               0 |              29 |                    0.86  |
| t88_masked | all         | sparse   | 416 | within              |   5    |              12 |   0.312 |  0.15  | 0.057 | 0.403 |               1 |              28 |                    0.818 |
| t88_masked | all         | sparse   | 416 | within              |   6    |               9 |   0.192 |  0.121 | 0.046 | 0.357 |               2 |              27 |                    0.816 |
| t88_masked | all         | sparse   | 416 | within              |   7    |              17 |   0.165 |  0.112 | 0.037 | 0.324 |               3 |              24 |                    0.789 |
| t88_masked | reliability | dense    |  20 | rescan              |   0    |              22 |   1     |  0.978 | 0.888 | 1     |               0 |               8 |                    0.345 |
| t88_masked | reliability | dense    |  20 | rescan              |   1    |              20 |   1     |  0.863 | 0.689 | 0.989 |               0 |              29 |                    0.674 |
| t88_masked | reliability | dense    |  20 | rescan              |   2    |              22 |   0.988 |  0.672 | 0.483 | 0.921 |               0 |              30 |                    0.609 |
| t88_masked | reliability | dense    |  20 | rescan              |   3    |              23 |   0.97  |  0.562 | 0.378 | 0.856 |               0 |              30 |                    0.584 |
| t88_masked | reliability | dense    |  20 | rescan              |   4    |               5 |   0.926 |  0.462 | 0.242 | 0.789 |               0 |              30 |                    0.391 |
| t88_masked | reliability | dense    |  20 | within              |   1    |              20 |   1     |  0.923 | 0.787 | 0.997 |               0 |              27 |                    0.63  |
| t88_masked | reliability | dense    |  20 | within              |   2    |              22 |   0.99  |  0.71  | 0.486 | 0.935 |               0 |              30 |                    0.646 |
| t88_masked | reliability | dense    |  20 | within              |   3    |              23 |   0.975 |  0.603 | 0.371 | 0.892 |               0 |              30 |                    0.646 |
| t88_masked | reliability | dense    |  20 | within              |   4    |               5 |   0.947 |  0.519 | 0.358 | 0.853 |               0 |              30 |                    0.416 |
| t88_masked | reliability | dense    |  20 | GEN rescan (d>=2mm) | nan    |             nan |   0.962 |  0.565 | 0.368 | 0.855 |             nan |             nan |                    0.598 |
| t88_masked | reliability | sparse   |  20 | rescan              |   0    |              13 |   1     |  0.991 | 0.927 | 1     |               0 |               3 |                    0.14  |
| t88_masked | reliability | sparse   |  20 | rescan              |   1    |               5 |   1     |  0.841 | 0.6   | 0.989 |               0 |              27 |                    0.547 |
| t88_masked | reliability | sparse   |  20 | rescan              |   2    |              13 |   0.988 |  0.568 | 0.413 | 0.903 |               0 |              30 |                    0.533 |
| t88_masked | reliability | sparse   |  20 | rescan              |   3    |               8 |   0.941 |  0.394 | 0.211 | 0.717 |               0 |              30 |                    0.476 |
| t88_masked | reliability | sparse   |  20 | rescan              |   4    |               9 |   0.778 |  0.333 | 0.17  | 0.661 |               0 |              30 |                    0.467 |
| t88_masked | reliability | sparse   |  20 | rescan              |   5    |              12 |   0.557 |  0.294 | 0.127 | 0.627 |               0 |              27 |                    0.352 |
| t88_masked | reliability | sparse   |  20 | rescan              |   6    |               9 |   0.415 |  0.266 | 0.094 | 0.637 |               1 |              19 |                    0.379 |
| t88_masked | reliability | sparse   |  20 | rescan              |   7    |              17 |   0.409 |  0.263 | 0.105 | 0.622 |               1 |              19 |                    0.379 |
| t88_masked | reliability | sparse   |  20 | within              |   1    |               5 |   1     |  0.897 | 0.716 | 0.989 |               0 |              25 |                    0.464 |
| t88_masked | reliability | sparse   |  20 | within              |   2    |              13 |   0.988 |  0.597 | 0.372 | 0.911 |               0 |              30 |                    0.549 |
| t88_masked | reliability | sparse   |  20 | within              |   3    |               8 |   0.941 |  0.429 | 0.23  | 0.783 |               0 |              30 |                    0.515 |
| t88_masked | reliability | sparse   |  20 | within              |   4    |               9 |   0.819 |  0.36  | 0.17  | 0.702 |               0 |              30 |                    0.494 |
| t88_masked | reliability | sparse   |  20 | within              |   5    |              12 |   0.588 |  0.312 | 0.123 | 0.684 |               0 |              27 |                    0.474 |
| t88_masked | reliability | sparse   |  20 | within              |   6    |               9 |   0.474 |  0.28  | 0.111 | 0.649 |               1 |              24 |                    0.434 |
| t88_masked | reliability | sparse   |  20 | within              |   7    |              17 |   0.44  |  0.287 | 0.127 | 0.65  |               1 |              19 |                    0.361 |
| t88_masked | reliability | sparse   |  20 | GEN rescan (d>=2mm) | nan    |             nan |   0.681 |  0.353 | 0.205 | 0.695 |             nan |             nan |                    0.57  |

## Generalisation score (mean over d >= 2 mm), per condition / design / session

- raw/all/sparse/repeat: pixel 0.843; pretrained 0.276-0.907; above pixel 2/30, below pixel 28/30; top3 mae_vitb16 0.907, densenet121_in1k 0.874, efficientnet_b0_in1k 0.675; bottom3 vgg16bn_in1k 0.351, biomedclip_vitb16 0.295, inceptionv3_in1k 0.276
- raw/reliability/sparse/repeat: pixel 0.917; pretrained 0.535-0.982; above pixel 1/30, below pixel 26/30; top3 mae_vitb16 0.982, densenet121_in1k 0.969, efficientnet_b0_in1k 0.882; bottom3 resnext50_in1k 0.553, vgg16bn_in1k 0.548, biomedclip_vitb16 0.535
- raw/reliability/sparse/rescan: pixel 0.412; pretrained 0.390-0.864; above pixel 9/30, below pixel 0/30; top3 mae_vitb16 0.864, densenet121_in1k 0.798, efficientnet_b0_in1k 0.741; bottom3 biomedclip_vitb16 0.408, resnet50_swsl 0.399, inceptionv3_in1k 0.390
- t88_gfc/reliability/dense/rescan: pixel 0.972; pretrained 0.715-0.999; above pixel 0/30, below pixel 19/30; top3 mae_vitb16 0.999, densenet121_in1k 0.991, dino_vits16 0.989; bottom3 biomedclip_vitb16 0.762, inceptionv3_in1k 0.739, vgg16bn_in1k 0.715
- t88_gfc/reliability/sparse/rescan: pixel 0.943; pretrained 0.497-0.990; above pixel 1/30, below pixel 26/30; top3 mae_vitb16 0.990, densenet121_in1k 0.932, mobilenetv3_l_in1k 0.904; bottom3 resnext50_in1k 0.613, vgg16bn_in1k 0.558, inceptionv3_in1k 0.497
- t88_masked/reliability/dense/rescan: pixel 0.962; pretrained 0.368-0.855; above pixel 0/30, below pixel 30/30; top3 mae_vitb16 0.855, dino_vits16 0.782, densenet121_in1k 0.757; bottom3 biomedclip_vitb16 0.433, resnext50_in1k 0.403, vgg16bn_in1k 0.368
- t88_masked/reliability/sparse/rescan: pixel 0.681; pretrained 0.205-0.695; above pixel 0/30, below pixel 29/30; top3 mae_vitb16 0.695, dino_vits16 0.572, densenet121_in1k 0.489; bottom3 inceptionv3_in1k 0.240, vgg16bn_in1k 0.208, resnext50_in1k 0.205

## Significant factor differences on GEN

- raw/all/sparse/repeat pretraining: self-supervised minus supervised IN-1k = +0.089 [+0.079,+0.099]
- raw/all/sparse/repeat pretraining: self-supervised minus supervised IN-21k = +0.081 [+0.068,+0.092]
- raw/all/sparse/repeat pretraining: self-supervised minus vision-language = +0.254 [+0.237,+0.269]
- raw/all/sparse/repeat pretraining: self-supervised minus weakly supervised = +0.243 [+0.222,+0.266]
- raw/all/sparse/repeat pretraining: supervised IN-1k minus vision-language = +0.164 [+0.150,+0.179]
- raw/all/sparse/repeat pretraining: supervised IN-1k minus weakly supervised = +0.153 [+0.135,+0.174]
- raw/all/sparse/repeat pretraining: supervised IN-21k minus vision-language = +0.173 [+0.156,+0.189]
- raw/all/sparse/repeat pretraining: supervised IN-21k minus weakly supervised = +0.162 [+0.142,+0.185]
- raw/all/sparse/repeat family: CNN minus Hybrid = +0.044 [+0.029,+0.058]
- raw/all/sparse/repeat family: CNN minus MLP/MetaFormer = -0.082 [-0.097,-0.069]
- raw/all/sparse/repeat family: Hybrid minus MLP/MetaFormer = -0.126 [-0.144,-0.108]
- raw/all/sparse/repeat family: Hybrid minus Transformer = -0.041 [-0.056,-0.026]
- raw/all/sparse/repeat family: MLP/MetaFormer minus Transformer = +0.085 [+0.072,+0.100]
- raw/reliability/sparse/repeat pretraining: self-supervised minus supervised IN-1k = +0.047 [+0.004,+0.093]
- raw/reliability/sparse/repeat pretraining: self-supervised minus supervised IN-21k = +0.092 [+0.042,+0.139]
- raw/reliability/sparse/repeat pretraining: self-supervised minus vision-language = +0.186 [+0.132,+0.242]
- raw/reliability/sparse/repeat pretraining: self-supervised minus weakly supervised = +0.099 [+0.026,+0.179]
- raw/reliability/sparse/repeat pretraining: supervised IN-1k minus supervised IN-21k = +0.046 [+0.009,+0.082]
- raw/reliability/sparse/repeat pretraining: supervised IN-1k minus vision-language = +0.140 [+0.082,+0.196]
- raw/reliability/sparse/repeat pretraining: supervised IN-21k minus vision-language = +0.094 [+0.028,+0.162]
- raw/reliability/sparse/repeat pretraining: vision-language minus weakly supervised = -0.088 [-0.158,-0.018]
- raw/reliability/sparse/repeat family: CNN minus Hybrid = +0.086 [+0.006,+0.172]
- raw/reliability/sparse/repeat family: CNN minus Transformer = +0.043 [+0.001,+0.085]
- raw/reliability/sparse/repeat family: Hybrid minus MLP/MetaFormer = -0.136 [-0.235,-0.046]
- raw/reliability/sparse/repeat family: MLP/MetaFormer minus Transformer = +0.093 [+0.040,+0.145]
- raw/reliability/sparse/rescan pretraining: self-supervised minus supervised IN-1k = +0.095 [+0.039,+0.155]
- raw/reliability/sparse/rescan pretraining: self-supervised minus supervised IN-21k = +0.108 [+0.063,+0.161]
- raw/reliability/sparse/rescan pretraining: self-supervised minus vision-language = +0.261 [+0.184,+0.342]
- raw/reliability/sparse/rescan pretraining: self-supervised minus weakly supervised = +0.276 [+0.186,+0.379]
- raw/reliability/sparse/rescan pretraining: supervised IN-1k minus vision-language = +0.166 [+0.087,+0.250]
- raw/reliability/sparse/rescan pretraining: supervised IN-1k minus weakly supervised = +0.182 [+0.097,+0.278]
- raw/reliability/sparse/rescan pretraining: supervised IN-21k minus vision-language = +0.153 [+0.068,+0.241]
- raw/reliability/sparse/rescan pretraining: supervised IN-21k minus weakly supervised = +0.168 [+0.074,+0.272]
- raw/reliability/sparse/rescan family: Hybrid minus MLP/MetaFormer = -0.134 [-0.228,-0.048]
- t88_gfc/reliability/dense/rescan pretraining: self-supervised minus supervised IN-1k = +0.048 [+0.027,+0.071]
- t88_gfc/reliability/dense/rescan pretraining: self-supervised minus vision-language = +0.127 [+0.079,+0.180]
- t88_gfc/reliability/dense/rescan pretraining: supervised IN-1k minus supervised IN-21k = -0.031 [-0.047,-0.015]
- t88_gfc/reliability/dense/rescan pretraining: supervised IN-1k minus vision-language = +0.079 [+0.032,+0.130]
- t88_gfc/reliability/dense/rescan pretraining: supervised IN-1k minus weakly supervised = -0.036 [-0.062,-0.011]
- t88_gfc/reliability/dense/rescan pretraining: supervised IN-21k minus vision-language = +0.109 [+0.058,+0.163]
- t88_gfc/reliability/dense/rescan pretraining: vision-language minus weakly supervised = -0.115 [-0.175,-0.057]
- t88_gfc/reliability/dense/rescan family: CNN minus Hybrid = +0.034 [+0.000,+0.070]
- t88_gfc/reliability/dense/rescan family: CNN minus MLP/MetaFormer = -0.040 [-0.059,-0.023]
- t88_gfc/reliability/dense/rescan family: Hybrid minus MLP/MetaFormer = -0.074 [-0.106,-0.042]
- t88_gfc/reliability/dense/rescan family: Hybrid minus Transformer = -0.039 [-0.074,-0.008]
- t88_gfc/reliability/dense/rescan family: MLP/MetaFormer minus Transformer = +0.035 [+0.020,+0.050]
- t88_gfc/reliability/sparse/rescan pretraining: self-supervised minus supervised IN-1k = +0.077 [+0.053,+0.104]
- t88_gfc/reliability/sparse/rescan pretraining: self-supervised minus supervised IN-21k = +0.046 [+0.020,+0.073]
- t88_gfc/reliability/sparse/rescan pretraining: self-supervised minus vision-language = +0.182 [+0.134,+0.232]
- t88_gfc/reliability/sparse/rescan pretraining: self-supervised minus weakly supervised = +0.062 [+0.020,+0.116]
- t88_gfc/reliability/sparse/rescan pretraining: supervised IN-1k minus supervised IN-21k = -0.030 [-0.056,-0.007]
- t88_gfc/reliability/sparse/rescan pretraining: supervised IN-1k minus vision-language = +0.105 [+0.051,+0.160]
- t88_gfc/reliability/sparse/rescan pretraining: supervised IN-21k minus vision-language = +0.135 [+0.077,+0.196]
- t88_gfc/reliability/sparse/rescan pretraining: vision-language minus weakly supervised = -0.119 [-0.185,-0.048]
- t88_gfc/reliability/sparse/rescan family: CNN minus Hybrid = +0.061 [+0.016,+0.108]
- t88_gfc/reliability/sparse/rescan family: Hybrid minus MLP/MetaFormer = -0.088 [-0.145,-0.029]
- t88_gfc/reliability/sparse/rescan family: Hybrid minus Transformer = -0.067 [-0.111,-0.030]
- t88_masked/reliability/dense/rescan pretraining: self-supervised minus supervised IN-1k = +0.177 [+0.151,+0.202]
- t88_masked/reliability/dense/rescan pretraining: self-supervised minus supervised IN-21k = +0.142 [+0.110,+0.173]
- t88_masked/reliability/dense/rescan pretraining: self-supervised minus vision-language = +0.268 [+0.229,+0.303]
- t88_masked/reliability/dense/rescan pretraining: self-supervised minus weakly supervised = +0.212 [+0.164,+0.264]
- t88_masked/reliability/dense/rescan pretraining: supervised IN-1k minus supervised IN-21k = -0.035 [-0.061,-0.011]
- t88_masked/reliability/dense/rescan pretraining: supervised IN-1k minus vision-language = +0.091 [+0.047,+0.134]
- t88_masked/reliability/dense/rescan pretraining: supervised IN-21k minus vision-language = +0.127 [+0.082,+0.166]
- t88_masked/reliability/dense/rescan pretraining: supervised IN-21k minus weakly supervised = +0.070 [+0.017,+0.116]
- t88_masked/reliability/dense/rescan family: CNN minus Hybrid = +0.057 [+0.012,+0.108]
- t88_masked/reliability/dense/rescan family: CNN minus MLP/MetaFormer = -0.055 [-0.094,-0.017]
- t88_masked/reliability/dense/rescan family: CNN minus Transformer = -0.043 [-0.069,-0.017]
- t88_masked/reliability/dense/rescan family: Hybrid minus MLP/MetaFormer = -0.112 [-0.173,-0.050]
- t88_masked/reliability/dense/rescan family: Hybrid minus Transformer = -0.100 [-0.148,-0.053]
- t88_masked/reliability/sparse/rescan pretraining: self-supervised minus supervised IN-1k = +0.194 [+0.170,+0.221]
- t88_masked/reliability/sparse/rescan pretraining: self-supervised minus supervised IN-21k = +0.154 [+0.124,+0.184]
- t88_masked/reliability/sparse/rescan pretraining: self-supervised minus vision-language = +0.239 [+0.177,+0.296]
- t88_masked/reliability/sparse/rescan pretraining: self-supervised minus weakly supervised = +0.245 [+0.203,+0.288]
- t88_masked/reliability/sparse/rescan pretraining: supervised IN-1k minus supervised IN-21k = -0.040 [-0.068,-0.012]
- t88_masked/reliability/sparse/rescan pretraining: supervised IN-1k minus weakly supervised = +0.050 [+0.001,+0.098]
- t88_masked/reliability/sparse/rescan pretraining: supervised IN-21k minus vision-language = +0.085 [+0.022,+0.136]
- t88_masked/reliability/sparse/rescan pretraining: supervised IN-21k minus weakly supervised = +0.091 [+0.048,+0.134]
- t88_masked/reliability/sparse/rescan family: CNN minus Hybrid = +0.044 [+0.003,+0.087]
- t88_masked/reliability/sparse/rescan family: CNN minus MLP/MetaFormer = -0.058 [-0.093,-0.025]
- t88_masked/reliability/sparse/rescan family: CNN minus Transformer = -0.057 [-0.081,-0.035]
- t88_masked/reliability/sparse/rescan family: Hybrid minus MLP/MetaFormer = -0.102 [-0.144,-0.061]
- t88_masked/reliability/sparse/rescan family: Hybrid minus Transformer = -0.102 [-0.141,-0.061]

## Capacity (Spearman log-params vs GEN)

| cond       | pool        | design   | session   | subset         |   n_models |   spearman |     lo |     hi |
|:-----------|:------------|:---------|:----------|:---------------|-----------:|-----------:|-------:|-------:|
| raw        | all         | sparse   | repeat    | all pretrained |         30 |     -0.291 | -0.335 | -0.266 |
| raw        | all         | sparse   | repeat    | CNN            |         14 |     -0.636 | -0.667 | -0.581 |
| raw        | all         | sparse   | repeat    | Transformer    |         12 |      0.035 | -0.014 |  0.099 |
| raw        | reliability | sparse   | repeat    | all pretrained |         30 |     -0.386 | -0.489 | -0.242 |
| raw        | reliability | sparse   | repeat    | CNN            |         14 |     -0.693 | -0.75  | -0.436 |
| raw        | reliability | sparse   | repeat    | Transformer    |         12 |     -0.081 | -0.308 |  0.187 |
| raw        | reliability | sparse   | rescan    | all pretrained |         30 |     -0.307 | -0.414 | -0.135 |
| raw        | reliability | sparse   | rescan    | CNN            |         14 |     -0.591 | -0.702 | -0.35  |
| raw        | reliability | sparse   | rescan    | Transformer    |         12 |     -0.053 | -0.307 |  0.201 |
| t88_gfc    | reliability | dense    | rescan    | all pretrained |         30 |     -0.295 | -0.379 | -0.185 |
| t88_gfc    | reliability | dense    | rescan    | CNN            |         14 |     -0.612 | -0.744 | -0.409 |
| t88_gfc    | reliability | dense    | rescan    | Transformer    |         12 |      0.021 | -0.176 |  0.176 |
| t88_gfc    | reliability | sparse   | rescan    | all pretrained |         30 |     -0.252 | -0.364 | -0.165 |
| t88_gfc    | reliability | sparse   | rescan    | CNN            |         14 |     -0.552 | -0.713 | -0.376 |
| t88_gfc    | reliability | sparse   | rescan    | Transformer    |         12 |      0.063 | -0.166 |  0.18  |
| t88_masked | reliability | dense    | rescan    | all pretrained |         30 |     -0.254 | -0.346 | -0.155 |
| t88_masked | reliability | dense    | rescan    | CNN            |         14 |     -0.535 | -0.748 | -0.451 |
| t88_masked | reliability | dense    | rescan    | Transformer    |         12 |     -0.205 | -0.303 |  0.039 |
| t88_masked | reliability | sparse   | rescan    | all pretrained |         30 |     -0.248 | -0.389 | -0.104 |
| t88_masked | reliability | sparse   | rescan    | CNN            |         14 |     -0.607 | -0.722 | -0.414 |
| t88_masked | reliability | sparse   | rescan    | Transformer    |         12 |     -0.127 | -0.381 |  0.131 |
