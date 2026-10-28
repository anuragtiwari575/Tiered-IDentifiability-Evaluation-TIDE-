# TIDE full run (OASIS-2 + OASIS-1 registration check)

Total time: 0.80 h

## Stage status

```
{
  "1_index": "ok (0.0 min)",
  "2_raw_oasis2": "ok (0.0 min)",
  "3_clinical": "ok (0.8 min)",
  "4_register": "ok (0.2 min)",
  "5_reg_encode": "ok (42.9 min)",
  "params": "ok (0.0 min)",
  "6_probe_o2_raw": "ok (0.0 min)",
  "6_probe_o2_reg": "ok (1.5 min)",
  "6_probe_o2_regmask": "ok (2.0 min)",
  "6_probe_o1val_reg": "ok (0.2 min)",
  "6_probe_o1val_regmask": "ok (0.2 min)",
  "6_probe_o1off_gfc": "ok (0.0 min)",
  "6_probe_o1off_masked": "ok (0.0 min)",
  "7_analysis": "ok (0.4 min)",
  "8_figures": "ok (0.1 min)"
}
```

Registration: 346/413 volumes passed; NCC median 0.566 (min 0.115).

## Registration validation (own registration vs official T88, OASIS-1 reliability, GEN)

| own           | official     | design   |   n_models |   spearman |   mean_abs_diff |   pixel_own |   pixel_official |   median_own |   median_official |
|:--------------|:-------------|:---------|-----------:|-----------:|----------------:|------------:|-----------------:|-------------:|------------------:|
| o1val_reg     | o1off_gfc    | dense    |         33 |      0.927 |           0.034 |       0.977 |            0.972 |        0.885 |             0.91  |
| o1val_reg     | o1off_gfc    | sparse   |         33 |      0.968 |           0.049 |       0.945 |            0.943 |        0.736 |             0.771 |
| o1val_regmask | o1off_masked | dense    |         33 |      0.91  |           0.03  |       0.973 |            0.962 |        0.56  |             0.553 |
| o1val_regmask | o1off_masked | sparse   |         33 |      0.912 |           0.033 |       0.749 |            0.681 |        0.343 |             0.331 |

## GEN (cross-session, d >= 2 mm) per condition / design

- o1off_gfc/dense (S=20): pixel 0.972 [0.937,0.998]; pretrained 0.715-0.999; above pixel 0/30, below 18/30; top3 mae_vitb16 0.999, densenet121_in1k 0.991, dino_vits16 0.989; bottom3 biomedclip_vitb16 0.762, inceptionv3_in1k 0.739, vgg16bn_in1k 0.715
- o1off_gfc/sparse (S=20): pixel 0.943 [0.921,0.964]; pretrained 0.497-0.990; above pixel 1/30, below 26/30; top3 mae_vitb16 0.990, densenet121_in1k 0.932, mobilenetv3_l_in1k 0.904; bottom3 resnext50_in1k 0.613, vgg16bn_in1k 0.558, inceptionv3_in1k 0.497
- o1off_masked/dense (S=20): pixel 0.962 [0.942,0.980]; pretrained 0.368-0.855; above pixel 0/30, below 30/30; top3 mae_vitb16 0.855, dino_vits16 0.782, densenet121_in1k 0.757; bottom3 biomedclip_vitb16 0.433, resnext50_in1k 0.403, vgg16bn_in1k 0.368
- o1off_masked/sparse (S=20): pixel 0.681 [0.631,0.727]; pretrained 0.205-0.695; above pixel 0/30, below 29/30; top3 mae_vitb16 0.695, dino_vits16 0.572, densenet121_in1k 0.489; bottom3 inceptionv3_in1k 0.240, vgg16bn_in1k 0.208, resnext50_in1k 0.205
- o1val_reg/dense (S=16): pixel 0.977 [0.939,1.000]; pretrained 0.656-0.992; above pixel 0/30, below 23/30; top3 mae_vitb16 0.992, densenet121_in1k 0.980, dino_vits16 0.971; bottom3 resnext50_in1k 0.715, vgg16bn_in1k 0.691, inceptionv3_in1k 0.656
- o1val_reg/sparse (S=16): pixel 0.945 [0.912,0.977]; pretrained 0.383-0.958; above pixel 0/30, below 27/30; top3 mae_vitb16 0.958, densenet121_in1k 0.913, vit_base_in21k 0.882; bottom3 biomedclip_vitb16 0.520, resnext50_in1k 0.511, inceptionv3_in1k 0.383
- o1val_regmask/dense (S=16): pixel 0.973 [0.955,0.988]; pretrained 0.328-0.824; above pixel 0/30, below 30/30; top3 mae_vitb16 0.824, dino_vits16 0.787, densenet121_in1k 0.758; bottom3 biomedclip_vitb16 0.439, vgg16bn_in1k 0.346, resnext50_in1k 0.328
- o1val_regmask/sparse (S=16): pixel 0.749 [0.689,0.803]; pretrained 0.194-0.591; above pixel 0/30, below 30/30; top3 mae_vitb16 0.591, dino_vits16 0.580, densenet121_in1k 0.528; bottom3 inceptionv3_in1k 0.253, vgg16bn_in1k 0.248, resnext50_in1k 0.194
- o2_raw/dense (S=150): pixel 0.120 [0.083,0.160]; pretrained 0.192-0.553; above pixel 30/30, below 0/30; top3 dino_vits16 0.553, mobilenetv3_l_in1k 0.453, vit_base_in21k 0.441; bottom3 clip_vitb16_openai 0.226, inceptionv3_in1k 0.210, biomedclip_vitb16 0.192
- o2_raw/sparse (S=150): pixel 0.110 [0.074,0.152]; pretrained 0.133-0.430; above pixel 28/30, below 0/30; top3 dino_vits16 0.430, mobilenetv3_l_in1k 0.354, mae_vitb16 0.339; bottom3 inceptionv3_in1k 0.152, biomedclip_vitb16 0.140, clip_vitb16_openai 0.133
- o2_reg/dense (S=118): pixel 0.803 [0.748,0.853]; pretrained 0.334-0.770; above pixel 0/30, below 29/30; top3 densenet121_in1k 0.770, mae_vitb16 0.726, dino_vits16 0.722; bottom3 inceptionv3_in1k 0.397, clip_vitb16_openai 0.375, vgg16bn_in1k 0.334
- o2_reg/sparse (S=118): pixel 0.732 [0.679,0.780]; pretrained 0.198-0.637; above pixel 0/30, below 30/30; top3 mae_vitb16 0.637, densenet121_in1k 0.608, dino_vits16 0.588; bottom3 resnext50_in1k 0.257, inceptionv3_in1k 0.229, vgg16bn_in1k 0.198
- o2_regmask/dense (S=118): pixel 0.824 [0.788,0.859]; pretrained 0.229-0.627; above pixel 0/30, below 30/30; top3 dino_vits16 0.627, mae_vitb16 0.589, densenet121_in1k 0.578; bottom3 inceptionv3_in1k 0.282, resnext50_in1k 0.268, vgg16bn_in1k 0.229
- o2_regmask/sparse (S=118): pixel 0.548 [0.513,0.579]; pretrained 0.115-0.401; above pixel 0/30, below 30/30; top3 dino_vits16 0.401, mae_vitb16 0.387, densenet121_in1k 0.368; bottom3 inceptionv3_in1k 0.145, resnext50_in1k 0.135, vgg16bn_in1k 0.115

## Time axis: change in identifiability per year between visits

Time axis: visit index

| cond       | design   | metric   | model              |   n_units |   slope_per_year |      lo |      hi |   spearman |   dist_slope_per_mm |   mm_equivalent_of_one_year |
|:-----------|:---------|:---------|:-------------------|----------:|-----------------:|--------:|--------:|-----------:|--------------------:|----------------------------:|
| o2_raw     | dense    | d0       | pixel              |       223 |          -0.0208 | -0.067  |  0.0311 |    -0.0827 |              0.0004 |                    nan      |
| o2_raw     | dense    | d0       | resnet50_in1k      |       223 |          -0.0665 | -0.1073 | -0.0217 |    -0.2009 |             -0.005  |                     13.2448 |
| o2_raw     | dense    | d0       | densenet121_in1k   |       223 |          -0.0886 | -0.1396 | -0.0309 |    -0.183  |             -0.0064 |                     13.9315 |
| o2_raw     | dense    | d0       | dino_vits16        |       223 |          -0.089  | -0.143  | -0.0201 |    -0.1686 |              0.0041 |                    nan      |
| o2_raw     | dense    | d0       | mae_vitb16         |       223 |          -0.0733 | -0.1289 | -0.0138 |    -0.1688 |              0.0032 |                    nan      |
| o2_raw     | dense    | d0       | clip_vitb16_openai |       223 |          -0.068  | -0.0997 | -0.0391 |    -0.2185 |             -0.0022 |                     30.5957 |
| o2_raw     | dense    | d0       | biomedclip_vitb16  |       223 |          -0.0135 | -0.0529 |  0.0315 |    -0.0474 |             -0.0034 |                      3.9968 |
| o2_raw     | dense    | d0       | pretrained_mean    |       223 |          -0.0624 | -0.0979 | -0.0213 |    -0.1811 |            nan      |                    nan      |
| o2_raw     | dense    | far      | pixel              |       223 |          -0.0014 | -0.0505 |  0.0548 |    -0.0733 |            nan      |                    nan      |
| o2_raw     | dense    | far      | resnet50_in1k      |       223 |          -0.0615 | -0.0935 | -0.0214 |    -0.1847 |            nan      |                    nan      |
| o2_raw     | dense    | far      | densenet121_in1k   |       223 |          -0.0749 | -0.1275 | -0.0051 |    -0.1607 |            nan      |                    nan      |
| o2_raw     | dense    | far      | dino_vits16        |       223 |          -0.0926 | -0.1424 | -0.0415 |    -0.1787 |            nan      |                    nan      |
| o2_raw     | dense    | far      | mae_vitb16         |       223 |          -0.0519 | -0.1107 |  0.0146 |    -0.1415 |            nan      |                    nan      |
| o2_raw     | dense    | far      | clip_vitb16_openai |       223 |          -0.0511 | -0.0818 | -0.0154 |    -0.1809 |            nan      |                    nan      |
| o2_raw     | dense    | far      | biomedclip_vitb16  |       223 |           0.0083 | -0.0435 |  0.0621 |    -0.0231 |            nan      |                    nan      |
| o2_raw     | dense    | far      | pretrained_mean    |       223 |          -0.0569 | -0.0924 | -0.0163 |    -0.1644 |            nan      |                    nan      |
| o2_raw     | sparse   | d0       | pixel              |       223 |          -0.0239 | -0.0674 |  0.0263 |    -0.0704 |             -0.0002 |                    149.369  |
| o2_raw     | sparse   | d0       | resnet50_in1k      |       223 |          -0.0857 | -0.1241 | -0.0469 |    -0.218  |             -0.0106 |                      8.0741 |
| o2_raw     | sparse   | d0       | densenet121_in1k   |       223 |          -0.0957 | -0.1583 | -0.0252 |    -0.1855 |             -0.0151 |                      6.3464 |
| o2_raw     | sparse   | d0       | dino_vits16        |       223 |          -0.0908 | -0.1468 | -0.0239 |    -0.1748 |             -0.0199 |                      4.5684 |
| o2_raw     | sparse   | d0       | mae_vitb16         |       223 |          -0.1014 | -0.1521 | -0.0494 |    -0.2017 |             -0.0051 |                     19.7033 |
| o2_raw     | sparse   | d0       | clip_vitb16_openai |       223 |          -0.0575 | -0.0851 | -0.0305 |    -0.1802 |             -0.0143 |                      4.022  |
| o2_raw     | sparse   | d0       | biomedclip_vitb16  |       223 |          -0.0312 | -0.0607 |  0.0003 |    -0.0771 |             -0.0076 |                      4.098  |
| o2_raw     | sparse   | d0       | pretrained_mean    |       223 |          -0.0564 | -0.088  | -0.0135 |    -0.1687 |            nan      |                    nan      |
| o2_raw     | sparse   | far      | pixel              |       223 |          -0.0024 | -0.0489 |  0.0584 |    -0.0695 |            nan      |                    nan      |
| o2_raw     | sparse   | far      | resnet50_in1k      |       223 |          -0.0522 | -0.0799 | -0.0171 |    -0.2228 |            nan      |                    nan      |
| o2_raw     | sparse   | far      | densenet121_in1k   |       223 |          -0.0646 | -0.116  |  0.0001 |    -0.1673 |            nan      |                    nan      |
| o2_raw     | sparse   | far      | dino_vits16        |       223 |          -0.0626 | -0.1062 | -0.0068 |    -0.149  |            nan      |                    nan      |
| o2_raw     | sparse   | far      | mae_vitb16         |       223 |          -0.07   | -0.1195 | -0.0139 |    -0.1649 |            nan      |                    nan      |
| o2_raw     | sparse   | far      | clip_vitb16_openai |       223 |          -0.0317 | -0.0501 | -0.0062 |    -0.1486 |            nan      |                    nan      |
| o2_raw     | sparse   | far      | biomedclip_vitb16  |       223 |          -0.014  | -0.0394 |  0.0199 |    -0.1069 |            nan      |                    nan      |
| o2_raw     | sparse   | far      | pretrained_mean    |       223 |          -0.0412 | -0.0704 | -0.0128 |    -0.1622 |            nan      |                    nan      |
| o2_reg     | dense    | d0       | pixel              |       170 |          -0.0257 | -0.1306 |  0.0508 |    -0.0276 |             -0.0061 |                      4.2233 |
| o2_reg     | dense    | d0       | resnet50_in1k      |       170 |          -0.0496 | -0.1039 |  0.0033 |    -0.164  |             -0.0672 |                      0.7377 |
| o2_reg     | dense    | d0       | densenet121_in1k   |       170 |          -0.015  | -0.0608 |  0.0222 |    -0.1141 |             -0.0479 |                      0.3131 |
| o2_reg     | dense    | d0       | dino_vits16        |       170 |          -0.0074 | -0.061  |  0.0414 |     0.0013 |             -0.0364 |                      0.2045 |
| o2_reg     | dense    | d0       | mae_vitb16         |       170 |          -0.0198 | -0.1075 |  0.0421 |    -0.0284 |             -0.0223 |                      0.8876 |
| o2_reg     | dense    | d0       | clip_vitb16_openai |       170 |          -0.0279 | -0.0955 |  0.0599 |    -0.0533 |             -0.0358 |                      0.7803 |
| o2_reg     | dense    | d0       | biomedclip_vitb16  |       170 |          -0.0334 | -0.0885 |  0.0239 |    -0.0879 |             -0.0704 |                      0.474  |
| o2_reg     | dense    | d0       | pretrained_mean    |       170 |          -0.0304 | -0.0874 |  0.0216 |    -0.0974 |            nan      |                    nan      |
| o2_reg     | dense    | far      | pixel              |       170 |          -0.0217 | -0.0965 |  0.0532 |    -0.0661 |            nan      |                    nan      |
| o2_reg     | dense    | far      | resnet50_in1k      |       170 |          -0.0007 | -0.0646 |  0.0607 |    -0.0243 |            nan      |                    nan      |
| o2_reg     | dense    | far      | densenet121_in1k   |       170 |          -0.0223 | -0.0779 |  0.0314 |    -0.0953 |            nan      |                    nan      |
| o2_reg     | dense    | far      | dino_vits16        |       170 |          -0.0384 | -0.0978 |  0.025  |    -0.0969 |            nan      |                    nan      |
| o2_reg     | dense    | far      | mae_vitb16         |       170 |          -0.0182 | -0.1032 |  0.0531 |    -0.0714 |            nan      |                    nan      |
| o2_reg     | dense    | far      | clip_vitb16_openai |       170 |          -0.0164 | -0.0769 |  0.0547 |    -0.0319 |            nan      |                    nan      |
| o2_reg     | dense    | far      | biomedclip_vitb16  |       170 |           0.0007 | -0.0555 |  0.0586 |    -0.0371 |            nan      |                    nan      |
| o2_reg     | dense    | far      | pretrained_mean    |       170 |          -0.023  | -0.0749 |  0.0328 |    -0.0994 |            nan      |                    nan      |
| o2_reg     | sparse   | d0       | pixel              |       170 |          -0.0257 | -0.1244 |  0.0448 |    -0.0603 |             -0.0133 |                      1.9322 |
| o2_reg     | sparse   | d0       | resnet50_in1k      |       170 |          -0.0505 | -0.1109 |  0.0008 |    -0.1754 |             -0.1322 |                      0.3821 |
| o2_reg     | sparse   | d0       | densenet121_in1k   |       170 |          -0.01   | -0.0583 |  0.0334 |    -0.063  |             -0.0875 |                      0.1145 |
| o2_reg     | sparse   | d0       | dino_vits16        |       170 |          -0.0279 | -0.0836 |  0.0336 |    -0.1278 |             -0.0775 |                      0.3597 |
| o2_reg     | sparse   | d0       | mae_vitb16         |       170 |          -0.04   | -0.1244 |  0.0277 |    -0.1419 |             -0.051  |                      0.7854 |
| o2_reg     | sparse   | d0       | clip_vitb16_openai |       170 |          -0.0107 | -0.0869 |  0.0699 |    -0.0246 |             -0.0719 |                      0.1481 |
| o2_reg     | sparse   | d0       | biomedclip_vitb16  |       170 |          -0.0644 | -0.1426 | -0.0012 |    -0.1815 |             -0.1368 |                      0.4708 |
| o2_reg     | sparse   | d0       | pretrained_mean    |       170 |          -0.0255 | -0.0732 |  0.019  |    -0.1163 |            nan      |                    nan      |
| o2_reg     | sparse   | far      | pixel              |       170 |          -0.0045 | -0.0883 |  0.0599 |    -0.0418 |            nan      |                    nan      |
| o2_reg     | sparse   | far      | resnet50_in1k      |       170 |          -0.0028 | -0.0543 |  0.0462 |    -0.0396 |            nan      |                    nan      |
| o2_reg     | sparse   | far      | densenet121_in1k   |       170 |          -0.0256 | -0.0933 |  0.0522 |    -0.0895 |            nan      |                    nan      |
| o2_reg     | sparse   | far      | dino_vits16        |       170 |          -0.0383 | -0.106  |  0.0317 |    -0.1115 |            nan      |                    nan      |
| o2_reg     | sparse   | far      | mae_vitb16         |       170 |           0.0176 | -0.0591 |  0.0989 |     0.019  |            nan      |                    nan      |
| o2_reg     | sparse   | far      | clip_vitb16_openai |       170 |          -0.009  | -0.0718 |  0.0621 |    -0.0506 |            nan      |                    nan      |
| o2_reg     | sparse   | far      | biomedclip_vitb16  |       170 |           0.0085 | -0.0516 |  0.0724 |    -0.0488 |            nan      |                    nan      |
| o2_reg     | sparse   | far      | pretrained_mean    |       170 |          -0.0121 | -0.0563 |  0.0411 |    -0.0708 |            nan      |                    nan      |
| o2_regmask | dense    | d0       | pixel              |       170 |          -0.0165 | -0.0507 |  0.0096 |    -0.1054 |             -0.0251 |                      0.659  |
| o2_regmask | dense    | d0       | resnet50_in1k      |       170 |          -0.0337 | -0.0988 |  0.0164 |    -0.0836 |             -0.1372 |                      0.2456 |
| o2_regmask | dense    | d0       | densenet121_in1k   |       170 |          -0.0241 | -0.0644 |  0.01   |    -0.1043 |             -0.1132 |                      0.2129 |
| o2_regmask | dense    | d0       | dino_vits16        |       170 |          -0.0241 | -0.0683 |  0.0193 |    -0.0798 |             -0.0883 |                      0.2732 |
| o2_regmask | dense    | d0       | mae_vitb16         |       170 |          -0.0528 | -0.1002 | -0.0025 |    -0.1915 |             -0.0811 |                      0.6508 |
| o2_regmask | dense    | d0       | clip_vitb16_openai |       170 |          -0.0065 | -0.0525 |  0.0413 |    -0.034  |             -0.1014 |                      0.064  |
| o2_regmask | dense    | d0       | biomedclip_vitb16  |       170 |          -0.0276 | -0.0866 |  0.0322 |    -0.0489 |             -0.1216 |                      0.2272 |
| o2_regmask | dense    | d0       | pretrained_mean    |       170 |          -0.0294 | -0.0764 |  0.0127 |    -0.1145 |            nan      |                    nan      |
| o2_regmask | dense    | far      | pixel              |       170 |          -0.011  | -0.0642 |  0.0399 |    -0.0805 |            nan      |                    nan      |
| o2_regmask | dense    | far      | resnet50_in1k      |       170 |          -0.0143 | -0.0603 |  0.0345 |    -0.1136 |            nan      |                    nan      |
| o2_regmask | dense    | far      | densenet121_in1k   |       170 |          -0.0072 | -0.058  |  0.0546 |    -0.0476 |            nan      |                    nan      |
| o2_regmask | dense    | far      | dino_vits16        |       170 |          -0.014  | -0.0772 |  0.0614 |    -0.0305 |            nan      |                    nan      |
| o2_regmask | dense    | far      | mae_vitb16         |       170 |          -0.0304 | -0.0766 |  0.0168 |    -0.0782 |            nan      |                    nan      |
| o2_regmask | dense    | far      | clip_vitb16_openai |       170 |          -0.0192 | -0.072  |  0.0376 |    -0.1191 |            nan      |                    nan      |
| o2_regmask | dense    | far      | biomedclip_vitb16  |       170 |           0.0079 | -0.0327 |  0.0615 |     0.0234 |            nan      |                    nan      |
| o2_regmask | dense    | far      | pretrained_mean    |       170 |          -0.0043 | -0.0454 |  0.0469 |    -0.0797 |            nan      |                    nan      |
| o2_regmask | sparse   | d0       | pixel              |       170 |          -0.0129 | -0.041  |  0.0063 |    -0.135  |             -0.0247 |                      0.5233 |
| o2_regmask | sparse   | d0       | resnet50_in1k      |       170 |          -0.031  | -0.0961 |  0.0213 |    -0.0844 |             -0.2088 |                      0.1483 |
| o2_regmask | sparse   | d0       | densenet121_in1k   |       170 |          -0.0336 | -0.0894 |  0.0081 |    -0.1358 |             -0.1841 |                      0.1826 |
| o2_regmask | sparse   | d0       | dino_vits16        |       170 |          -0.044  | -0.0983 |  0.0001 |    -0.1493 |             -0.156  |                      0.282  |
| o2_regmask | sparse   | d0       | mae_vitb16         |       170 |          -0.0326 | -0.0777 |  0.0069 |    -0.104  |             -0.1322 |                      0.2463 |
| o2_regmask | sparse   | d0       | clip_vitb16_openai |       170 |          -0.0276 | -0.0941 |  0.0297 |    -0.0865 |             -0.1483 |                      0.1865 |
| o2_regmask | sparse   | d0       | biomedclip_vitb16  |       170 |          -0.0673 | -0.1327 | -0.0035 |    -0.1694 |             -0.2043 |                      0.3295 |
| o2_regmask | sparse   | d0       | pretrained_mean    |       170 |          -0.0272 | -0.0722 |  0.0094 |    -0.0931 |            nan      |                    nan      |
| o2_regmask | sparse   | far      | pixel              |       170 |          -0.0088 | -0.0594 |  0.049  |    -0.0715 |            nan      |                    nan      |
| o2_regmask | sparse   | far      | resnet50_in1k      |       170 |          -0.0112 | -0.0457 |  0.0323 |    -0.0807 |            nan      |                    nan      |
| o2_regmask | sparse   | far      | densenet121_in1k   |       170 |          -0.019  | -0.0733 |  0.0457 |    -0.1227 |            nan      |                    nan      |
| o2_regmask | sparse   | far      | dino_vits16        |       170 |          -0.0389 | -0.0812 |  0.0056 |    -0.1147 |            nan      |                    nan      |
| o2_regmask | sparse   | far      | mae_vitb16         |       170 |          -0.0306 | -0.0708 |  0.0143 |    -0.0931 |            nan      |                    nan      |
| o2_regmask | sparse   | far      | clip_vitb16_openai |       170 |          -0.016  | -0.0459 |  0.0226 |    -0.0819 |            nan      |                    nan      |
| o2_regmask | sparse   | far      | biomedclip_vitb16  |       170 |           0.0054 | -0.0336 |  0.0469 |    -0.0514 |            nan      |                    nan      |
| o2_regmask | sparse   | far      | pretrained_mean    |       170 |          -0.0042 | -0.0392 |  0.0387 |    -0.1006 |            nan      |                    nan      |

- o2_raw/dense/d0: encoders with slope CI < 0: 21/30; median slope -0.0657/yr; median mm-equivalent of one year 11.492 mm
- o2_raw/dense/far: encoders with slope CI < 0: 18/30; median slope -0.0558/yr; median mm-equivalent of one year nan mm
- o2_raw/sparse/d0: encoders with slope CI < 0: 15/30; median slope -0.0549/yr; median mm-equivalent of one year 3.774 mm
- o2_raw/sparse/far: encoders with slope CI < 0: 15/30; median slope -0.0369/yr; median mm-equivalent of one year nan mm
- o2_reg/dense/d0: encoders with slope CI < 0: 1/30; median slope -0.0277/yr; median mm-equivalent of one year 0.495 mm
- o2_reg/dense/far: encoders with slope CI < 0: 0/30; median slope -0.0186/yr; median mm-equivalent of one year nan mm
- o2_reg/sparse/d0: encoders with slope CI < 0: 3/30; median slope -0.0279/yr; median mm-equivalent of one year 0.249 mm
- o2_reg/sparse/far: encoders with slope CI < 0: 0/30; median slope -0.0114/yr; median mm-equivalent of one year nan mm
- o2_regmask/dense/d0: encoders with slope CI < 0: 1/30; median slope -0.0276/yr; median mm-equivalent of one year 0.221 mm
- o2_regmask/dense/far: encoders with slope CI < 0: 0/30; median slope -0.0058/yr; median mm-equivalent of one year nan mm
- o2_regmask/sparse/d0: encoders with slope CI < 0: 2/30; median slope -0.0277/yr; median mm-equivalent of one year 0.148 mm
- o2_regmask/sparse/far: encoders with slope CI < 0: 1/30; median slope -0.0044/yr; median mm-equivalent of one year nan mm

## Per distance bin (pretrained encoders, logreg)

| cond          | design   | session            |   d_mm |   n_subj |   pixel |   mean |   min |   max |   n_above_pixel |   n_below_pixel |   frac_pairs_significant |
|:--------------|:---------|:-------------------|-------:|---------:|--------:|-------:|------:|------:|----------------:|----------------:|-------------------------:|
| o2_raw        | dense    | cross              |   0    |      150 |   0.125 |  0.365 | 0.197 | 0.558 |              30 |               0 |                    0.733 |
| o2_raw        | dense    | cross              |   1.25 |      150 |   0.122 |  0.356 | 0.193 | 0.558 |              30 |               0 |                    0.775 |
| o2_raw        | dense    | cross              |   2.5  |      150 |   0.126 |  0.353 | 0.188 | 0.568 |              30 |               0 |                    0.791 |
| o2_raw        | dense    | cross              |   3.75 |      150 |   0.114 |  0.346 | 0.195 | 0.537 |              30 |               0 |                    0.621 |
| o2_raw        | dense    | repeat             |   0    |      150 |   0.998 |  0.963 | 0.847 | 0.993 |               0 |              27 |                    0.618 |
| o2_raw        | dense    | repeat             |   1.25 |      150 |   0.998 |  0.933 | 0.784 | 0.985 |               0 |              30 |                    0.789 |
| o2_raw        | dense    | repeat             |   2.5  |      150 |   0.998 |  0.903 | 0.713 | 0.983 |               0 |              30 |                    0.816 |
| o2_raw        | dense    | repeat             |   3.75 |      150 |   0.998 |  0.874 | 0.644 | 0.98  |               0 |              29 |                    0.664 |
| o2_raw        | dense    | within             |   1.25 |      150 |   1     |  0.974 | 0.862 | 0.999 |               0 |              28 |                    0.736 |
| o2_raw        | dense    | within             |   2.5  |      150 |   1     |  0.949 | 0.783 | 1     |               0 |              29 |                    0.818 |
| o2_raw        | dense    | within             |   3.75 |      150 |   1     |  0.919 | 0.694 | 1     |               0 |              28 |                    0.701 |
| o2_raw        | dense    | GEN cross (d>=2mm) | nan    |      150 |   0.12  |  0.35  | 0.192 | 0.553 |             nan |             nan |                    0.754 |
| o2_raw        | sparse   | cross              |   0    |      150 |   0.115 |  0.34  | 0.166 | 0.543 |              30 |               0 |                    0.729 |
| o2_raw        | sparse   | cross              |   1.25 |      150 |   0.117 |  0.34  | 0.177 | 0.534 |              30 |               0 |                    0.759 |
| o2_raw        | sparse   | cross              |   2.5  |      150 |   0.114 |  0.303 | 0.146 | 0.493 |              28 |               0 |                    0.738 |
| o2_raw        | sparse   | cross              |   5    |      150 |   0.106 |  0.251 | 0.138 | 0.427 |              28 |               0 |                    0.74  |
| o2_raw        | sparse   | cross              |   6.25 |      150 |   0.11  |  0.232 | 0.115 | 0.413 |              26 |               0 |                    0.697 |
| o2_raw        | sparse   | cross              |   7.5  |      150 |   0.109 |  0.23  | 0.124 | 0.385 |              26 |               0 |                    0.722 |
| o2_raw        | sparse   | repeat             |   0    |      150 |   1     |  0.966 | 0.873 | 0.995 |               0 |              28 |                    0.538 |
| o2_raw        | sparse   | repeat             |   1.25 |      150 |   1     |  0.933 | 0.783 | 0.99  |               0 |              30 |                    0.782 |
| o2_raw        | sparse   | repeat             |   2.5  |      150 |   0.999 |  0.848 | 0.628 | 0.98  |               0 |              30 |                    0.828 |
| o2_raw        | sparse   | repeat             |   5    |      150 |   0.998 |  0.686 | 0.43  | 0.956 |               0 |              30 |                    0.841 |
| o2_raw        | sparse   | repeat             |   6.25 |      150 |   0.995 |  0.648 | 0.383 | 0.96  |               0 |              30 |                    0.784 |
| o2_raw        | sparse   | repeat             |   7.5  |      150 |   0.984 |  0.638 | 0.378 | 0.944 |               0 |              30 |                    0.851 |
| o2_raw        | sparse   | within             |   1.25 |      150 |   1     |  0.977 | 0.858 | 1     |               0 |              23 |                    0.703 |
| o2_raw        | sparse   | within             |   2.5  |      150 |   1     |  0.909 | 0.692 | 0.999 |               0 |              29 |                    0.837 |
| o2_raw        | sparse   | within             |   5    |      150 |   1     |  0.755 | 0.491 | 0.984 |               0 |              30 |                    0.876 |
| o2_raw        | sparse   | within             |   6.25 |      150 |   0.997 |  0.708 | 0.453 | 0.98  |               0 |              30 |                    0.805 |
| o2_raw        | sparse   | within             |   7.5  |      150 |   0.989 |  0.7   | 0.417 | 0.979 |               0 |              29 |                    0.848 |
| o2_raw        | sparse   | GEN cross (d>=2mm) | nan    |      150 |   0.11  |  0.254 | 0.133 | 0.43  |             nan |             nan |                    0.802 |
| o2_reg        | dense    | cross              |   0    |      118 |   0.843 |  0.711 | 0.471 | 0.911 |               1 |              22 |                    0.798 |
| o2_reg        | dense    | cross              |   1    |      118 |   0.849 |  0.667 | 0.446 | 0.887 |               0 |              27 |                    0.823 |
| o2_reg        | dense    | cross              |   2    |      118 |   0.831 |  0.59  | 0.382 | 0.815 |               0 |              29 |                    0.841 |
| o2_reg        | dense    | cross              |   3    |      118 |   0.818 |  0.542 | 0.327 | 0.782 |               0 |              29 |                    0.832 |
| o2_reg        | dense    | cross              |   4    |      118 |   0.76  |  0.496 | 0.291 | 0.713 |               0 |              29 |                    0.763 |
| o2_reg        | dense    | within             |   1    |      118 |   1     |  0.986 | 0.886 | 1     |               0 |              22 |                    0.729 |
| o2_reg        | dense    | within             |   2    |      118 |   1     |  0.936 | 0.721 | 0.998 |               0 |              30 |                    0.867 |
| o2_reg        | dense    | within             |   3    |      118 |   1     |  0.907 | 0.63  | 1     |               0 |              29 |                    0.86  |
| o2_reg        | dense    | within             |   4    |      118 |   1     |  0.875 | 0.538 | 0.998 |               0 |              29 |                    0.805 |
| o2_reg        | dense    | GEN cross (d>=2mm) | nan    |      118 |   0.803 |  0.543 | 0.334 | 0.77  |             nan |             nan |                    0.846 |
| o2_reg        | sparse   | cross              |   0    |      118 |   0.877 |  0.752 | 0.454 | 0.929 |               1 |              20 |                    0.77  |
| o2_reg        | sparse   | cross              |   1    |      118 |   0.878 |  0.664 | 0.385 | 0.88  |               0 |              28 |                    0.789 |
| o2_reg        | sparse   | cross              |   2    |      118 |   0.851 |  0.521 | 0.301 | 0.754 |               0 |              30 |                    0.795 |
| o2_reg        | sparse   | cross              |   3    |      118 |   0.805 |  0.428 | 0.209 | 0.674 |               0 |              30 |                    0.809 |
| o2_reg        | sparse   | cross              |   4    |      118 |   0.728 |  0.379 | 0.178 | 0.629 |               0 |              30 |                    0.793 |
| o2_reg        | sparse   | cross              |   5    |      118 |   0.72  |  0.357 | 0.167 | 0.607 |               0 |              30 |                    0.789 |
| o2_reg        | sparse   | cross              |   6    |      118 |   0.64  |  0.336 | 0.161 | 0.598 |               0 |              29 |                    0.763 |
| o2_reg        | sparse   | cross              |   7    |      118 |   0.649 |  0.328 | 0.135 | 0.577 |               0 |              30 |                    0.745 |
| o2_reg        | sparse   | within             |   1    |      118 |   1     |  0.979 | 0.841 | 1     |               0 |              20 |                    0.586 |
| o2_reg        | sparse   | within             |   2    |      118 |   1     |  0.872 | 0.565 | 0.996 |               0 |              30 |                    0.821 |
| o2_reg        | sparse   | within             |   3    |      118 |   1     |  0.788 | 0.441 | 0.994 |               0 |              30 |                    0.83  |
| o2_reg        | sparse   | within             |   4    |      118 |   0.994 |  0.737 | 0.349 | 0.988 |               0 |              29 |                    0.823 |
| o2_reg        | sparse   | within             |   5    |      118 |   0.993 |  0.708 | 0.309 | 0.985 |               0 |              29 |                    0.816 |
| o2_reg        | sparse   | within             |   6    |      118 |   0.953 |  0.68  | 0.274 | 0.978 |               1 |              29 |                    0.83  |
| o2_reg        | sparse   | within             |   7    |      118 |   0.955 |  0.673 | 0.26  | 0.977 |               1 |              29 |                    0.805 |
| o2_reg        | sparse   | GEN cross (d>=2mm) | nan    |      118 |   0.732 |  0.391 | 0.198 | 0.637 |             nan |             nan |                    0.823 |
| o2_regmask    | dense    | cross              |   0    |      118 |   0.954 |  0.747 | 0.542 | 0.908 |               0 |              30 |                    0.777 |
| o2_regmask    | dense    | cross              |   1    |      118 |   0.941 |  0.632 | 0.411 | 0.824 |               0 |              30 |                    0.818 |
| o2_regmask    | dense    | cross              |   2    |      118 |   0.904 |  0.489 | 0.28  | 0.707 |               0 |              30 |                    0.805 |
| o2_regmask    | dense    | cross              |   3    |      118 |   0.844 |  0.403 | 0.213 | 0.625 |               0 |              30 |                    0.809 |
| o2_regmask    | dense    | cross              |   4    |      118 |   0.724 |  0.341 | 0.193 | 0.549 |               0 |              30 |                    0.706 |
| o2_regmask    | dense    | within             |   1    |      118 |   1     |  0.886 | 0.668 | 0.994 |               0 |              30 |                    0.871 |
| o2_regmask    | dense    | within             |   2    |      118 |   0.993 |  0.675 | 0.4   | 0.937 |               0 |              30 |                    0.876 |
| o2_regmask    | dense    | within             |   3    |      118 |   0.971 |  0.568 | 0.29  | 0.884 |               0 |              30 |                    0.841 |
| o2_regmask    | dense    | within             |   4    |      118 |   0.915 |  0.498 | 0.234 | 0.829 |               0 |              30 |                    0.754 |
| o2_regmask    | dense    | GEN cross (d>=2mm) | nan    |      118 |   0.824 |  0.411 | 0.229 | 0.627 |             nan |             nan |                    0.851 |
| o2_regmask    | sparse   | cross              |   0    |      118 |   0.968 |  0.797 | 0.555 | 0.948 |               0 |              29 |                    0.726 |
| o2_regmask    | sparse   | cross              |   1    |      118 |   0.961 |  0.622 | 0.405 | 0.85  |               0 |              30 |                    0.784 |
| o2_regmask    | sparse   | cross              |   2    |      118 |   0.918 |  0.399 | 0.234 | 0.613 |               0 |              30 |                    0.743 |
| o2_regmask    | sparse   | cross              |   3    |      118 |   0.796 |  0.261 | 0.127 | 0.446 |               0 |              30 |                    0.722 |
| o2_regmask    | sparse   | cross              |   4    |      118 |   0.584 |  0.219 | 0.097 | 0.401 |               0 |              30 |                    0.715 |
| o2_regmask    | sparse   | cross              |   5    |      118 |   0.413 |  0.195 | 0.087 | 0.334 |               0 |              30 |                    0.662 |
| o2_regmask    | sparse   | cross              |   6    |      118 |   0.299 |  0.173 | 0.075 | 0.314 |               0 |              27 |                    0.595 |
| o2_regmask    | sparse   | cross              |   7    |      118 |   0.276 |  0.158 | 0.065 | 0.297 |               0 |              27 |                    0.545 |
| o2_regmask    | sparse   | within             |   1    |      118 |   1     |  0.851 | 0.648 | 0.991 |               0 |              30 |                    0.782 |
| o2_regmask    | sparse   | within             |   2    |      118 |   0.995 |  0.546 | 0.341 | 0.861 |               0 |              30 |                    0.811 |
| o2_regmask    | sparse   | within             |   3    |      118 |   0.931 |  0.374 | 0.177 | 0.697 |               0 |              30 |                    0.759 |
| o2_regmask    | sparse   | within             |   4    |      118 |   0.788 |  0.316 | 0.14  | 0.627 |               0 |              30 |                    0.766 |
| o2_regmask    | sparse   | within             |   5    |      118 |   0.609 |  0.285 | 0.118 | 0.56  |               0 |              30 |                    0.74  |
| o2_regmask    | sparse   | within             |   6    |      118 |   0.462 |  0.255 | 0.115 | 0.523 |               1 |              27 |                    0.731 |
| o2_regmask    | sparse   | within             |   7    |      118 |   0.417 |  0.241 | 0.093 | 0.501 |               1 |              27 |                    0.674 |
| o2_regmask    | sparse   | GEN cross (d>=2mm) | nan    |      118 |   0.548 |  0.234 | 0.115 | 0.401 |             nan |             nan |                    0.777 |
| o1val_reg     | dense    | cross              |   0    |       16 |   0.985 |  0.962 | 0.833 | 1     |               0 |               6 |                    0.331 |
| o1val_reg     | dense    | cross              |   1    |       16 |   0.977 |  0.949 | 0.83  | 1     |               0 |               7 |                    0.513 |
| o1val_reg     | dense    | cross              |   2    |       16 |   0.991 |  0.897 | 0.733 | 0.994 |               0 |              23 |                    0.593 |
| o1val_reg     | dense    | cross              |   3    |       16 |   0.98  |  0.861 | 0.661 | 0.994 |               0 |              22 |                    0.586 |
| o1val_reg     | dense    | cross              |   4    |       16 |   0.96  |  0.831 | 0.56  | 0.987 |               0 |              15 |                    0.421 |
| o1val_reg     | dense    | within             |   1    |       16 |   1     |  0.995 | 0.95  | 1     |               0 |               5 |                    0.257 |
| o1val_reg     | dense    | within             |   2    |       16 |   1     |  0.957 | 0.803 | 1     |               0 |              20 |                    0.487 |
| o1val_reg     | dense    | within             |   3    |       16 |   1     |  0.94  | 0.696 | 1     |               0 |              24 |                    0.513 |
| o1val_reg     | dense    | within             |   4    |       16 |   1     |  0.91  | 0.573 | 1     |               0 |              15 |                    0.411 |
| o1val_reg     | dense    | GEN cross (d>=2mm) | nan    |       16 |   0.977 |  0.863 | 0.656 | 0.992 |             nan |             nan |                    0.593 |
| o1val_reg     | sparse   | cross              |   0    |       16 |   1     |  0.967 | 0.826 | 1     |               0 |               4 |                    0.186 |
| o1val_reg     | sparse   | cross              |   1    |       16 |   0.987 |  0.922 | 0.773 | 1     |               0 |              10 |                    0.303 |
| o1val_reg     | sparse   | cross              |   2    |       16 |   0.995 |  0.824 | 0.6   | 0.99  |               0 |              26 |                    0.579 |
| o1val_reg     | sparse   | cross              |   3    |       16 |   0.983 |  0.762 | 0.442 | 0.975 |               0 |              29 |                    0.52  |
| o1val_reg     | sparse   | cross              |   4    |       16 |   0.97  |  0.704 | 0.333 | 0.948 |               0 |              28 |                    0.566 |
| o1val_reg     | sparse   | cross              |   5    |       16 |   0.956 |  0.682 | 0.317 | 0.956 |               0 |              27 |                    0.563 |
| o1val_reg     | sparse   | cross              |   6    |       16 |   0.881 |  0.668 | 0.319 | 0.941 |               0 |              24 |                    0.529 |
| o1val_reg     | sparse   | cross              |   7    |       16 |   0.886 |  0.674 | 0.286 | 0.937 |               0 |              23 |                    0.492 |
| o1val_reg     | sparse   | within             |   1    |       16 |   1     |  0.983 | 0.867 | 1     |               0 |               4 |                    0.211 |
| o1val_reg     | sparse   | within             |   2    |       16 |   1     |  0.903 | 0.682 | 1     |               0 |              24 |                    0.575 |
| o1val_reg     | sparse   | within             |   3    |       16 |   1     |  0.848 | 0.5   | 0.992 |               0 |              25 |                    0.566 |
| o1val_reg     | sparse   | within             |   4    |       16 |   0.985 |  0.794 | 0.348 | 1     |               0 |              25 |                    0.589 |
| o1val_reg     | sparse   | within             |   5    |       16 |   0.989 |  0.776 | 0.344 | 1     |               0 |              28 |                    0.582 |
| o1val_reg     | sparse   | within             |   6    |       16 |   0.904 |  0.747 | 0.304 | 0.993 |               1 |              22 |                    0.492 |
| o1val_reg     | sparse   | within             |   7    |       16 |   0.918 |  0.752 | 0.337 | 1     |               1 |              23 |                    0.503 |
| o1val_reg     | sparse   | GEN cross (d>=2mm) | nan    |       16 |   0.945 |  0.719 | 0.383 | 0.958 |             nan |             nan |                    0.623 |
| o1val_regmask | dense    | cross              |   0    |       16 |   1     |  0.901 | 0.685 | 1     |               0 |              25 |                    0.526 |
| o1val_regmask | dense    | cross              |   1    |       16 |   1     |  0.801 | 0.617 | 0.957 |               0 |              30 |                    0.57  |
| o1val_regmask | dense    | cross              |   2    |       16 |   0.988 |  0.644 | 0.415 | 0.873 |               0 |              30 |                    0.589 |
| o1val_regmask | dense    | cross              |   3    |       16 |   0.986 |  0.562 | 0.307 | 0.852 |               0 |              30 |                    0.605 |
| o1val_regmask | dense    | cross              |   4    |       16 |   0.947 |  0.486 | 0.213 | 0.747 |               0 |              30 |                    0.411 |
| o1val_regmask | dense    | within             |   1    |       16 |   1     |  0.915 | 0.797 | 1     |               0 |              27 |                    0.559 |
| o1val_regmask | dense    | within             |   2    |       16 |   0.991 |  0.729 | 0.506 | 0.955 |               0 |              30 |                    0.683 |
| o1val_regmask | dense    | within             |   3    |       16 |   0.986 |  0.653 | 0.409 | 0.939 |               0 |              30 |                    0.641 |
| o1val_regmask | dense    | within             |   4    |       16 |   0.987 |  0.572 | 0.347 | 0.893 |               0 |              30 |                    0.513 |
| o1val_regmask | dense    | GEN cross (d>=2mm) | nan    |       16 |   0.973 |  0.564 | 0.328 | 0.824 |             nan |             nan |                    0.616 |
| o1val_regmask | sparse   | cross              |   0    |       16 |   1     |  0.939 | 0.759 | 1     |               0 |              15 |                    0.349 |
| o1val_regmask | sparse   | cross              |   1    |       16 |   1     |  0.765 | 0.56  | 0.947 |               0 |              29 |                    0.478 |
| o1val_regmask | sparse   | cross              |   2    |       16 |   0.99  |  0.531 | 0.338 | 0.749 |               0 |              30 |                    0.485 |
| o1val_regmask | sparse   | cross              |   3    |       16 |   0.942 |  0.404 | 0.208 | 0.65  |               0 |              30 |                    0.476 |
| o1val_regmask | sparse   | cross              |   4    |       16 |   0.837 |  0.348 | 0.178 | 0.593 |               0 |              30 |                    0.43  |
| o1val_regmask | sparse   | cross              |   5    |       16 |   0.644 |  0.314 | 0.111 | 0.561 |               0 |              28 |                    0.356 |
| o1val_regmask | sparse   | cross              |   6    |       16 |   0.533 |  0.292 | 0.133 | 0.556 |               0 |              27 |                    0.395 |
| o1val_regmask | sparse   | cross              |   7    |       16 |   0.549 |  0.267 | 0.125 | 0.486 |               0 |              27 |                    0.31  |
| o1val_regmask | sparse   | within             |   1    |       16 |   1     |  0.886 | 0.72  | 1     |               0 |              25 |                    0.423 |
| o1val_regmask | sparse   | within             |   2    |       16 |   1     |  0.612 | 0.41  | 0.862 |               0 |              30 |                    0.54  |
| o1val_regmask | sparse   | within             |   3    |       16 |   0.975 |  0.452 | 0.225 | 0.758 |               0 |              30 |                    0.549 |
| o1val_regmask | sparse   | within             |   4    |       16 |   0.881 |  0.398 | 0.207 | 0.704 |               0 |              30 |                    0.49  |
| o1val_regmask | sparse   | within             |   5    |       16 |   0.711 |  0.372 | 0.189 | 0.617 |               0 |              29 |                    0.451 |
| o1val_regmask | sparse   | within             |   6    |       16 |   0.607 |  0.331 | 0.178 | 0.63  |               0 |              27 |                    0.437 |
| o1val_regmask | sparse   | within             |   7    |       16 |   0.545 |  0.326 | 0.137 | 0.627 |               0 |              25 |                    0.393 |
| o1val_regmask | sparse   | GEN cross (d>=2mm) | nan    |       16 |   0.749 |  0.359 | 0.194 | 0.591 |             nan |             nan |                    0.54  |
| o1off_gfc     | dense    | cross              |   0    |       20 |   0.983 |  0.989 | 0.957 | 1     |               0 |               0 |                    0.191 |
| o1off_gfc     | dense    | cross              |   1    |       20 |   0.979 |  0.971 | 0.887 | 1     |               0 |               4 |                    0.513 |
| o1off_gfc     | dense    | cross              |   2    |       20 |   0.978 |  0.929 | 0.768 | 1     |               0 |              13 |                    0.607 |
| o1off_gfc     | dense    | cross              |   3    |       20 |   0.97  |  0.898 | 0.721 | 0.998 |               0 |              14 |                    0.641 |
| o1off_gfc     | dense    | cross              |   4    |       20 |   0.968 |  0.866 | 0.653 | 1     |               0 |              20 |                    0.455 |
| o1off_gfc     | dense    | within             |   1    |       20 |   1     |  0.995 | 0.937 | 1     |               0 |               4 |                    0.207 |
| o1off_gfc     | dense    | within             |   2    |       20 |   1     |  0.974 | 0.861 | 1     |               0 |              18 |                    0.522 |
| o1off_gfc     | dense    | within             |   3    |       20 |   1     |  0.957 | 0.769 | 1     |               0 |              22 |                    0.506 |
| o1off_gfc     | dense    | within             |   4    |       20 |   1     |  0.941 | 0.705 | 1     |               0 |              11 |                    0.379 |
| o1off_gfc     | dense    | GEN cross (d>=2mm) | nan    |       20 |   0.972 |  0.898 | 0.715 | 0.999 |             nan |             nan |                    0.639 |
| o1off_gfc     | sparse   | cross              |   0    |       20 |   0.984 |  0.991 | 0.927 | 1     |               0 |               1 |                    0.051 |
| o1off_gfc     | sparse   | cross              |   1    |       20 |   0.989 |  0.962 | 0.853 | 1     |               0 |               6 |                    0.336 |
| o1off_gfc     | sparse   | cross              |   2    |       20 |   0.988 |  0.873 | 0.668 | 1     |               0 |              24 |                    0.614 |
| o1off_gfc     | sparse   | cross              |   3    |       20 |   0.987 |  0.805 | 0.586 | 1     |               0 |              27 |                    0.584 |
| o1off_gfc     | sparse   | cross              |   4    |       20 |   0.947 |  0.75  | 0.503 | 0.977 |               0 |              26 |                    0.586 |
| o1off_gfc     | sparse   | cross              |   5    |       20 |   0.969 |  0.727 | 0.43  | 0.991 |               0 |              28 |                    0.543 |
| o1off_gfc     | sparse   | cross              |   6    |       20 |   0.889 |  0.707 | 0.363 | 0.982 |               1 |              25 |                    0.563 |
| o1off_gfc     | sparse   | cross              |   7    |       20 |   0.879 |  0.707 | 0.368 | 0.988 |               1 |              25 |                    0.533 |
| o1off_gfc     | sparse   | within             |   1    |       20 |   1     |  0.993 | 0.926 | 1     |               0 |               2 |                    0.115 |
| o1off_gfc     | sparse   | within             |   2    |       20 |   1     |  0.942 | 0.757 | 1     |               0 |              17 |                    0.52  |
| o1off_gfc     | sparse   | within             |   3    |       20 |   1     |  0.884 | 0.572 | 1     |               0 |              25 |                    0.609 |
| o1off_gfc     | sparse   | within             |   4    |       20 |   0.971 |  0.85  | 0.503 | 1     |               1 |              22 |                    0.621 |
| o1off_gfc     | sparse   | within             |   5    |       20 |   0.974 |  0.829 | 0.456 | 1     |               0 |              22 |                    0.602 |
| o1off_gfc     | sparse   | within             |   6    |       20 |   0.912 |  0.799 | 0.468 | 0.994 |               2 |              18 |                    0.593 |
| o1off_gfc     | sparse   | within             |   7    |       20 |   0.913 |  0.788 | 0.399 | 0.991 |               2 |              19 |                    0.543 |
| o1off_gfc     | sparse   | GEN cross (d>=2mm) | nan    |       20 |   0.943 |  0.761 | 0.497 | 0.99  |             nan |             nan |                    0.651 |
| o1off_masked  | dense    | cross              |   0    |       20 |   1     |  0.978 | 0.888 | 1     |               0 |               8 |                    0.34  |
| o1off_masked  | dense    | cross              |   1    |       20 |   1     |  0.863 | 0.689 | 0.989 |               0 |              29 |                    0.664 |
| o1off_masked  | dense    | cross              |   2    |       20 |   0.988 |  0.672 | 0.483 | 0.921 |               0 |              30 |                    0.602 |
| o1off_masked  | dense    | cross              |   3    |       20 |   0.97  |  0.562 | 0.378 | 0.856 |               0 |              30 |                    0.586 |
| o1off_masked  | dense    | cross              |   4    |       20 |   0.926 |  0.462 | 0.242 | 0.789 |               0 |              30 |                    0.389 |
| o1off_masked  | dense    | within             |   1    |       20 |   1     |  0.923 | 0.787 | 0.997 |               0 |              27 |                    0.625 |
| o1off_masked  | dense    | within             |   2    |       20 |   0.99  |  0.71  | 0.486 | 0.935 |               0 |              30 |                    0.653 |
| o1off_masked  | dense    | within             |   3    |       20 |   0.975 |  0.603 | 0.371 | 0.892 |               0 |              30 |                    0.646 |
| o1off_masked  | dense    | within             |   4    |       20 |   0.947 |  0.519 | 0.358 | 0.853 |               0 |              30 |                    0.434 |
| o1off_masked  | dense    | GEN cross (d>=2mm) | nan    |       20 |   0.962 |  0.565 | 0.368 | 0.855 |             nan |             nan |                    0.598 |
| o1off_masked  | sparse   | cross              |   0    |       20 |   1     |  0.991 | 0.927 | 1     |               0 |               3 |                    0.14  |
| o1off_masked  | sparse   | cross              |   1    |       20 |   1     |  0.841 | 0.6   | 0.989 |               0 |              27 |                    0.57  |
| o1off_masked  | sparse   | cross              |   2    |       20 |   0.988 |  0.568 | 0.413 | 0.903 |               0 |              30 |                    0.52  |
| o1off_masked  | sparse   | cross              |   3    |       20 |   0.941 |  0.394 | 0.211 | 0.717 |               0 |              30 |                    0.49  |
| o1off_masked  | sparse   | cross              |   4    |       20 |   0.778 |  0.333 | 0.17  | 0.661 |               0 |              30 |                    0.46  |
| o1off_masked  | sparse   | cross              |   5    |       20 |   0.557 |  0.294 | 0.127 | 0.627 |               0 |              28 |                    0.345 |
| o1off_masked  | sparse   | cross              |   6    |       20 |   0.415 |  0.266 | 0.094 | 0.637 |               1 |              19 |                    0.393 |
| o1off_masked  | sparse   | cross              |   7    |       20 |   0.409 |  0.263 | 0.105 | 0.622 |               1 |              19 |                    0.389 |
| o1off_masked  | sparse   | within             |   1    |       20 |   1     |  0.897 | 0.716 | 0.989 |               0 |              25 |                    0.467 |
| o1off_masked  | sparse   | within             |   2    |       20 |   0.988 |  0.597 | 0.372 | 0.911 |               0 |              30 |                    0.545 |
| o1off_masked  | sparse   | within             |   3    |       20 |   0.941 |  0.429 | 0.23  | 0.783 |               0 |              30 |                    0.52  |
| o1off_masked  | sparse   | within             |   4    |       20 |   0.819 |  0.36  | 0.17  | 0.702 |               0 |              30 |                    0.492 |
| o1off_masked  | sparse   | within             |   5    |       20 |   0.588 |  0.312 | 0.123 | 0.684 |               0 |              27 |                    0.485 |
| o1off_masked  | sparse   | within             |   6    |       20 |   0.474 |  0.28  | 0.111 | 0.649 |               1 |              24 |                    0.425 |
| o1off_masked  | sparse   | within             |   7    |       20 |   0.44  |  0.287 | 0.127 | 0.65  |               1 |              18 |                    0.359 |
| o1off_masked  | sparse   | GEN cross (d>=2mm) | nan    |       20 |   0.681 |  0.353 | 0.205 | 0.695 |             nan |             nan |                    0.572 |

## Significant factor differences on GEN

- o2_raw/dense pretraining: self-supervised minus supervised IN-1k = +0.056 [+0.039,+0.074]
- o2_raw/dense pretraining: self-supervised minus supervised IN-21k = +0.023 [+0.006,+0.042]
- o2_raw/dense pretraining: self-supervised minus vision-language = +0.192 [+0.166,+0.217]
- o2_raw/dense pretraining: self-supervised minus weakly supervised = +0.057 [+0.028,+0.085]
- o2_raw/dense pretraining: supervised IN-1k minus supervised IN-21k = -0.033 [-0.047,-0.020]
- o2_raw/dense pretraining: supervised IN-1k minus vision-language = +0.136 [+0.114,+0.157]
- o2_raw/dense pretraining: supervised IN-21k minus vision-language = +0.169 [+0.145,+0.193]
- o2_raw/dense pretraining: supervised IN-21k minus weakly supervised = +0.034 [+0.007,+0.059]
- o2_raw/dense pretraining: vision-language minus weakly supervised = -0.135 [-0.167,-0.104]
- o2_raw/dense family: CNN minus MLP/MetaFormer = -0.041 [-0.060,-0.021]
- o2_raw/dense family: Hybrid minus MLP/MetaFormer = -0.049 [-0.076,-0.021]
- o2_raw/dense family: MLP/MetaFormer minus Transformer = +0.031 [+0.011,+0.051]
- o2_raw/sparse pretraining: self-supervised minus supervised IN-1k = +0.063 [+0.048,+0.077]
- o2_raw/sparse pretraining: self-supervised minus supervised IN-21k = +0.036 [+0.022,+0.050]
- o2_raw/sparse pretraining: self-supervised minus vision-language = +0.175 [+0.153,+0.197]
- o2_raw/sparse pretraining: self-supervised minus weakly supervised = +0.107 [+0.084,+0.130]
- o2_raw/sparse pretraining: supervised IN-1k minus supervised IN-21k = -0.027 [-0.036,-0.017]
- o2_raw/sparse pretraining: supervised IN-1k minus vision-language = +0.113 [+0.097,+0.130]
- o2_raw/sparse pretraining: supervised IN-1k minus weakly supervised = +0.045 [+0.025,+0.064]
- o2_raw/sparse pretraining: supervised IN-21k minus vision-language = +0.140 [+0.121,+0.159]
- o2_raw/sparse pretraining: supervised IN-21k minus weakly supervised = +0.072 [+0.051,+0.093]
- o2_raw/sparse pretraining: vision-language minus weakly supervised = -0.068 [-0.089,-0.048]
- o2_raw/sparse family: CNN minus Hybrid = +0.024 [+0.008,+0.039]
- o2_raw/sparse family: CNN minus MLP/MetaFormer = -0.068 [-0.087,-0.050]
- o2_raw/sparse family: CNN minus Transformer = -0.015 [-0.025,-0.006]
- o2_raw/sparse family: Hybrid minus MLP/MetaFormer = -0.092 [-0.116,-0.071]
- o2_raw/sparse family: Hybrid minus Transformer = -0.039 [-0.053,-0.024]
- o2_raw/sparse family: MLP/MetaFormer minus Transformer = +0.053 [+0.035,+0.072]
- o2_reg/dense pretraining: self-supervised minus supervised IN-1k = +0.040 [+0.021,+0.058]
- o2_reg/dense pretraining: self-supervised minus vision-language = +0.167 [+0.144,+0.190]
- o2_reg/dense pretraining: supervised IN-1k minus supervised IN-21k = -0.057 [-0.072,-0.041]
- o2_reg/dense pretraining: supervised IN-1k minus vision-language = +0.127 [+0.105,+0.149]
- o2_reg/dense pretraining: supervised IN-1k minus weakly supervised = -0.044 [-0.069,-0.016]
- o2_reg/dense pretraining: supervised IN-21k minus vision-language = +0.185 [+0.159,+0.207]
- o2_reg/dense pretraining: vision-language minus weakly supervised = -0.171 [-0.203,-0.137]
- o2_reg/dense family: CNN minus Hybrid = +0.095 [+0.073,+0.120]
- o2_reg/dense family: CNN minus MLP/MetaFormer = -0.099 [-0.117,-0.081]
- o2_reg/dense family: Hybrid minus MLP/MetaFormer = -0.194 [-0.220,-0.168]
- o2_reg/dense family: Hybrid minus Transformer = -0.091 [-0.112,-0.070]
- o2_reg/dense family: MLP/MetaFormer minus Transformer = +0.103 [+0.082,+0.123]
- o2_reg/sparse pretraining: self-supervised minus supervised IN-1k = +0.078 [+0.059,+0.098]
- o2_reg/sparse pretraining: self-supervised minus vision-language = +0.175 [+0.151,+0.198]
- o2_reg/sparse pretraining: self-supervised minus weakly supervised = +0.070 [+0.038,+0.102]
- o2_reg/sparse pretraining: supervised IN-1k minus supervised IN-21k = -0.064 [-0.078,-0.049]
- o2_reg/sparse pretraining: supervised IN-1k minus vision-language = +0.096 [+0.075,+0.118]
- o2_reg/sparse pretraining: supervised IN-21k minus vision-language = +0.160 [+0.136,+0.185]
- o2_reg/sparse pretraining: supervised IN-21k minus weakly supervised = +0.055 [+0.025,+0.083]
- o2_reg/sparse pretraining: vision-language minus weakly supervised = -0.105 [-0.139,-0.073]
- o2_reg/sparse family: CNN minus Hybrid = +0.076 [+0.057,+0.096]
- o2_reg/sparse family: CNN minus MLP/MetaFormer = -0.075 [-0.094,-0.055]
- o2_reg/sparse family: CNN minus Transformer = -0.028 [-0.041,-0.013]
- o2_reg/sparse family: Hybrid minus MLP/MetaFormer = -0.151 [-0.176,-0.128]
- o2_reg/sparse family: Hybrid minus Transformer = -0.103 [-0.122,-0.085]
- o2_reg/sparse family: MLP/MetaFormer minus Transformer = +0.047 [+0.028,+0.068]
- o2_regmask/dense pretraining: self-supervised minus supervised IN-1k = +0.147 [+0.132,+0.163]
- o2_regmask/dense pretraining: self-supervised minus supervised IN-21k = +0.086 [+0.071,+0.102]
- o2_regmask/dense pretraining: self-supervised minus vision-language = +0.226 [+0.206,+0.246]
- o2_regmask/dense pretraining: self-supervised minus weakly supervised = +0.189 [+0.164,+0.214]
- o2_regmask/dense pretraining: supervised IN-1k minus supervised IN-21k = -0.061 [-0.071,-0.051]
- o2_regmask/dense pretraining: supervised IN-1k minus vision-language = +0.078 [+0.063,+0.094]
- o2_regmask/dense pretraining: supervised IN-1k minus weakly supervised = +0.042 [+0.023,+0.060]
- o2_regmask/dense pretraining: supervised IN-21k minus vision-language = +0.139 [+0.123,+0.157]
- o2_regmask/dense pretraining: supervised IN-21k minus weakly supervised = +0.103 [+0.081,+0.124]
- o2_regmask/dense pretraining: vision-language minus weakly supervised = -0.036 [-0.059,-0.013]
- o2_regmask/dense family: CNN minus Hybrid = +0.029 [+0.013,+0.045]
- o2_regmask/dense family: CNN minus MLP/MetaFormer = -0.067 [-0.082,-0.052]
- o2_regmask/dense family: CNN minus Transformer = -0.051 [-0.061,-0.041]
- o2_regmask/dense family: Hybrid minus MLP/MetaFormer = -0.097 [-0.116,-0.075]
- o2_regmask/dense family: Hybrid minus Transformer = -0.081 [-0.096,-0.066]
- o2_regmask/dense family: MLP/MetaFormer minus Transformer = +0.016 [+0.001,+0.031]
- o2_regmask/sparse pretraining: self-supervised minus supervised IN-1k = +0.120 [+0.104,+0.138]
- o2_regmask/sparse pretraining: self-supervised minus supervised IN-21k = +0.078 [+0.063,+0.094]
- o2_regmask/sparse pretraining: self-supervised minus vision-language = +0.162 [+0.145,+0.181]
- o2_regmask/sparse pretraining: self-supervised minus weakly supervised = +0.139 [+0.118,+0.161]
- o2_regmask/sparse pretraining: supervised IN-1k minus supervised IN-21k = -0.042 [-0.052,-0.032]
- o2_regmask/sparse pretraining: supervised IN-1k minus vision-language = +0.042 [+0.028,+0.055]
- o2_regmask/sparse pretraining: supervised IN-1k minus weakly supervised = +0.019 [+0.002,+0.034]
- o2_regmask/sparse pretraining: supervised IN-21k minus vision-language = +0.084 [+0.069,+0.100]
- o2_regmask/sparse pretraining: supervised IN-21k minus weakly supervised = +0.061 [+0.042,+0.080]
- o2_regmask/sparse pretraining: vision-language minus weakly supervised = -0.023 [-0.043,-0.003]
- o2_regmask/sparse family: CNN minus Hybrid = +0.021 [+0.009,+0.033]
- o2_regmask/sparse family: CNN minus MLP/MetaFormer = -0.036 [-0.050,-0.021]
- o2_regmask/sparse family: CNN minus Transformer = -0.043 [-0.053,-0.033]
- o2_regmask/sparse family: Hybrid minus MLP/MetaFormer = -0.057 [-0.077,-0.037]
- o2_regmask/sparse family: Hybrid minus Transformer = -0.064 [-0.078,-0.050]
- o1val_reg/dense pretraining: self-supervised minus supervised IN-1k = +0.072 [+0.047,+0.097]
- o1val_reg/dense pretraining: self-supervised minus vision-language = +0.167 [+0.091,+0.243]
- o1val_reg/dense pretraining: supervised IN-1k minus supervised IN-21k = -0.043 [-0.067,-0.016]
- o1val_reg/dense pretraining: supervised IN-1k minus vision-language = +0.095 [+0.031,+0.161]
- o1val_reg/dense pretraining: supervised IN-1k minus weakly supervised = -0.038 [-0.074,-0.001]
- o1val_reg/dense pretraining: supervised IN-21k minus vision-language = +0.138 [+0.082,+0.191]
- o1val_reg/dense pretraining: vision-language minus weakly supervised = -0.133 [-0.220,-0.056]
- o1val_reg/dense family: CNN minus Transformer = -0.017 [-0.032,-0.001]
- o1val_reg/sparse pretraining: self-supervised minus supervised IN-1k = +0.116 [+0.089,+0.145]
- o1val_reg/sparse pretraining: self-supervised minus supervised IN-21k = +0.056 [+0.020,+0.099]
- o1val_reg/sparse pretraining: self-supervised minus vision-language = +0.245 [+0.164,+0.325]
- o1val_reg/sparse pretraining: self-supervised minus weakly supervised = +0.100 [+0.043,+0.167]
- o1val_reg/sparse pretraining: supervised IN-1k minus supervised IN-21k = -0.060 [-0.087,-0.033]
- o1val_reg/sparse pretraining: supervised IN-1k minus vision-language = +0.128 [+0.048,+0.202]
- o1val_reg/sparse pretraining: supervised IN-21k minus vision-language = +0.188 [+0.110,+0.262]
- o1val_reg/sparse pretraining: vision-language minus weakly supervised = -0.145 [-0.244,-0.039]
- o1val_reg/sparse family: CNN minus Hybrid = +0.054 [+0.002,+0.109]
- o1val_reg/sparse family: CNN minus Transformer = -0.035 [-0.058,-0.015]
- o1val_reg/sparse family: Hybrid minus MLP/MetaFormer = -0.087 [-0.166,-0.016]
- o1val_reg/sparse family: Hybrid minus Transformer = -0.090 [-0.145,-0.039]
- o1val_regmask/dense pretraining: self-supervised minus supervised IN-1k = +0.169 [+0.140,+0.201]
- o1val_regmask/dense pretraining: self-supervised minus supervised IN-21k = +0.067 [+0.030,+0.106]
- o1val_regmask/dense pretraining: self-supervised minus vision-language = +0.235 [+0.171,+0.298]
- o1val_regmask/dense pretraining: self-supervised minus weakly supervised = +0.200 [+0.138,+0.266]
- o1val_regmask/dense pretraining: supervised IN-1k minus supervised IN-21k = -0.102 [-0.123,-0.077]
- o1val_regmask/dense pretraining: supervised IN-1k minus vision-language = +0.066 [+0.010,+0.116]
- o1val_regmask/dense pretraining: supervised IN-21k minus vision-language = +0.167 [+0.114,+0.216]
- o1val_regmask/dense pretraining: supervised IN-21k minus weakly supervised = +0.133 [+0.083,+0.182]
- o1val_regmask/dense family: CNN minus Hybrid = +0.052 [+0.001,+0.103]
- o1val_regmask/dense family: CNN minus MLP/MetaFormer = -0.094 [-0.136,-0.053]
- o1val_regmask/dense family: CNN minus Transformer = -0.068 [-0.089,-0.044]
- o1val_regmask/dense family: Hybrid minus MLP/MetaFormer = -0.146 [-0.198,-0.096]
- o1val_regmask/dense family: Hybrid minus Transformer = -0.120 [-0.160,-0.075]
- o1val_regmask/sparse pretraining: self-supervised minus supervised IN-1k = +0.148 [+0.105,+0.196]
- o1val_regmask/sparse pretraining: self-supervised minus supervised IN-21k = +0.066 [+0.035,+0.101]
- o1val_regmask/sparse pretraining: self-supervised minus vision-language = +0.190 [+0.137,+0.242]
- o1val_regmask/sparse pretraining: self-supervised minus weakly supervised = +0.190 [+0.128,+0.256]
- o1val_regmask/sparse pretraining: supervised IN-1k minus supervised IN-21k = -0.082 [-0.109,-0.054]
- o1val_regmask/sparse pretraining: supervised IN-21k minus vision-language = +0.124 [+0.081,+0.165]
- o1val_regmask/sparse pretraining: supervised IN-21k minus weakly supervised = +0.124 [+0.080,+0.171]
- o1val_regmask/sparse family: CNN minus Hybrid = +0.056 [+0.007,+0.110]
- o1val_regmask/sparse family: CNN minus MLP/MetaFormer = -0.111 [-0.148,-0.073]
- o1val_regmask/sparse family: CNN minus Transformer = -0.046 [-0.082,-0.012]
- o1val_regmask/sparse family: Hybrid minus MLP/MetaFormer = -0.167 [-0.222,-0.111]
- o1val_regmask/sparse family: Hybrid minus Transformer = -0.102 [-0.161,-0.053]
- o1val_regmask/sparse family: MLP/MetaFormer minus Transformer = +0.065 [+0.018,+0.108]
- o1off_gfc/dense pretraining: self-supervised minus supervised IN-1k = +0.048 [+0.028,+0.073]
- o1off_gfc/dense pretraining: self-supervised minus vision-language = +0.127 [+0.080,+0.179]
- o1off_gfc/dense pretraining: supervised IN-1k minus supervised IN-21k = -0.031 [-0.048,-0.014]
- o1off_gfc/dense pretraining: supervised IN-1k minus vision-language = +0.079 [+0.031,+0.131]
- o1off_gfc/dense pretraining: supervised IN-1k minus weakly supervised = -0.036 [-0.063,-0.010]
- o1off_gfc/dense pretraining: supervised IN-21k minus vision-language = +0.109 [+0.060,+0.162]
- o1off_gfc/dense pretraining: vision-language minus weakly supervised = -0.115 [-0.176,-0.061]
- o1off_gfc/dense family: CNN minus MLP/MetaFormer = -0.040 [-0.060,-0.022]
- o1off_gfc/dense family: Hybrid minus MLP/MetaFormer = -0.074 [-0.111,-0.041]
- o1off_gfc/dense family: Hybrid minus Transformer = -0.039 [-0.077,-0.006]
- o1off_gfc/dense family: MLP/MetaFormer minus Transformer = +0.035 [+0.019,+0.052]
- o1off_gfc/sparse pretraining: self-supervised minus supervised IN-1k = +0.077 [+0.054,+0.101]
- o1off_gfc/sparse pretraining: self-supervised minus supervised IN-21k = +0.046 [+0.020,+0.074]
- o1off_gfc/sparse pretraining: self-supervised minus vision-language = +0.182 [+0.130,+0.234]
- o1off_gfc/sparse pretraining: self-supervised minus weakly supervised = +0.062 [+0.013,+0.111]
- o1off_gfc/sparse pretraining: supervised IN-1k minus supervised IN-21k = -0.030 [-0.057,-0.007]
- o1off_gfc/sparse pretraining: supervised IN-1k minus vision-language = +0.105 [+0.051,+0.159]
- o1off_gfc/sparse pretraining: supervised IN-21k minus vision-language = +0.135 [+0.077,+0.193]
- o1off_gfc/sparse pretraining: vision-language minus weakly supervised = -0.119 [-0.187,-0.047]
- o1off_gfc/sparse family: CNN minus Hybrid = +0.061 [+0.018,+0.109]
- o1off_gfc/sparse family: Hybrid minus MLP/MetaFormer = -0.088 [-0.147,-0.029]
- o1off_gfc/sparse family: Hybrid minus Transformer = -0.067 [-0.108,-0.029]
- o1off_masked/dense pretraining: self-supervised minus supervised IN-1k = +0.177 [+0.150,+0.202]
- o1off_masked/dense pretraining: self-supervised minus supervised IN-21k = +0.142 [+0.110,+0.173]
- o1off_masked/dense pretraining: self-supervised minus vision-language = +0.268 [+0.227,+0.306]
- o1off_masked/dense pretraining: self-supervised minus weakly supervised = +0.212 [+0.163,+0.264]
- o1off_masked/dense pretraining: supervised IN-1k minus supervised IN-21k = -0.035 [-0.059,-0.010]
- o1off_masked/dense pretraining: supervised IN-1k minus vision-language = +0.091 [+0.045,+0.135]
- o1off_masked/dense pretraining: supervised IN-21k minus vision-language = +0.127 [+0.081,+0.169]
- o1off_masked/dense pretraining: supervised IN-21k minus weakly supervised = +0.070 [+0.020,+0.119]
- o1off_masked/dense family: CNN minus Hybrid = +0.057 [+0.009,+0.108]
- o1off_masked/dense family: CNN minus MLP/MetaFormer = -0.055 [-0.093,-0.017]
- o1off_masked/dense family: CNN minus Transformer = -0.043 [-0.068,-0.017]
- o1off_masked/dense family: Hybrid minus MLP/MetaFormer = -0.112 [-0.176,-0.055]
- o1off_masked/dense family: Hybrid minus Transformer = -0.100 [-0.149,-0.055]
- o1off_masked/sparse pretraining: self-supervised minus supervised IN-1k = +0.194 [+0.168,+0.223]
- o1off_masked/sparse pretraining: self-supervised minus supervised IN-21k = +0.154 [+0.125,+0.186]
- o1off_masked/sparse pretraining: self-supervised minus vision-language = +0.239 [+0.181,+0.299]
- o1off_masked/sparse pretraining: self-supervised minus weakly supervised = +0.245 [+0.198,+0.289]
- o1off_masked/sparse pretraining: supervised IN-1k minus supervised IN-21k = -0.040 [-0.067,-0.010]
- o1off_masked/sparse pretraining: supervised IN-21k minus vision-language = +0.085 [+0.032,+0.134]
- o1off_masked/sparse pretraining: supervised IN-21k minus weakly supervised = +0.091 [+0.039,+0.135]
- o1off_masked/sparse family: CNN minus Hybrid = +0.044 [+0.002,+0.086]
- o1off_masked/sparse family: CNN minus MLP/MetaFormer = -0.058 [-0.092,-0.023]
- o1off_masked/sparse family: CNN minus Transformer = -0.057 [-0.080,-0.036]
- o1off_masked/sparse family: Hybrid minus MLP/MetaFormer = -0.102 [-0.144,-0.057]
- o1off_masked/sparse family: Hybrid minus Transformer = -0.102 [-0.145,-0.059]

## Capacity (Spearman log-params vs GEN)

| cond          | design   | subset         |   n_models |   spearman |     lo |     hi |
|:--------------|:---------|:---------------|-----------:|-----------:|-------:|-------:|
| o2_raw        | dense    | all pretrained |         30 |     -0.25  | -0.321 | -0.193 |
| o2_raw        | dense    | CNN            |         14 |     -0.365 | -0.504 | -0.286 |
| o2_raw        | dense    | Transformer    |         12 |     -0.169 | -0.353 | -0.021 |
| o2_raw        | sparse   | all pretrained |         30 |     -0.246 | -0.3   | -0.19  |
| o2_raw        | sparse   | CNN            |         14 |     -0.528 | -0.587 | -0.418 |
| o2_raw        | sparse   | Transformer    |         12 |     -0.095 | -0.243 | -0.032 |
| o2_reg        | dense    | all pretrained |         30 |     -0.342 | -0.383 | -0.28  |
| o2_reg        | dense    | CNN            |         14 |     -0.678 | -0.728 | -0.557 |
| o2_reg        | dense    | Transformer    |         12 |      0.049 | -0.095 |  0.099 |
| o2_reg        | sparse   | all pretrained |         30 |     -0.246 | -0.292 | -0.171 |
| o2_reg        | sparse   | CNN            |         14 |     -0.55  | -0.695 | -0.392 |
| o2_reg        | sparse   | Transformer    |         12 |      0     | -0.071 |  0.148 |
| o2_regmask    | dense    | all pretrained |         30 |     -0.285 | -0.335 | -0.227 |
| o2_regmask    | dense    | CNN            |         14 |     -0.684 | -0.761 | -0.59  |
| o2_regmask    | dense    | Transformer    |         12 |     -0.342 | -0.392 | -0.236 |
| o2_regmask    | sparse   | all pretrained |         30 |     -0.204 | -0.299 | -0.144 |
| o2_regmask    | sparse   | CNN            |         14 |     -0.579 | -0.719 | -0.502 |
| o2_regmask    | sparse   | Transformer    |         12 |     -0.3   | -0.392 | -0.194 |
| o1val_reg     | dense    | all pretrained |         30 |     -0.18  | -0.317 | -0.099 |
| o1val_reg     | dense    | CNN            |         14 |     -0.44  | -0.599 | -0.372 |
| o1val_reg     | dense    | Transformer    |         12 |      0.099 | -0.176 |  0.18  |
| o1val_reg     | sparse   | all pretrained |         30 |     -0.142 | -0.26  | -0.084 |
| o1val_reg     | sparse   | CNN            |         14 |     -0.53  | -0.62  | -0.337 |
| o1val_reg     | sparse   | Transformer    |         12 |     -0.004 | -0.208 |  0.145 |
| o1val_regmask | dense    | all pretrained |         30 |     -0.287 | -0.355 | -0.186 |
| o1val_regmask | dense    | CNN            |         14 |     -0.675 | -0.766 | -0.455 |
| o1val_regmask | dense    | Transformer    |         12 |     -0.078 | -0.261 |  0.096 |
| o1val_regmask | sparse   | all pretrained |         30 |     -0.235 | -0.305 | -0.102 |
| o1val_regmask | sparse   | CNN            |         14 |     -0.59  | -0.695 | -0.383 |
| o1val_regmask | sparse   | Transformer    |         12 |      0.035 | -0.169 |  0.159 |
| o1off_gfc     | dense    | all pretrained |         30 |     -0.295 | -0.382 | -0.174 |
| o1off_gfc     | dense    | CNN            |         14 |     -0.612 | -0.744 | -0.407 |
| o1off_gfc     | dense    | Transformer    |         12 |      0.021 | -0.183 |  0.198 |
| o1off_gfc     | sparse   | all pretrained |         30 |     -0.252 | -0.354 | -0.17  |
| o1off_gfc     | sparse   | CNN            |         14 |     -0.552 | -0.717 | -0.407 |
| o1off_gfc     | sparse   | Transformer    |         12 |      0.063 | -0.176 |  0.19  |
| o1off_masked  | dense    | all pretrained |         30 |     -0.254 | -0.342 | -0.16  |
| o1off_masked  | dense    | CNN            |         14 |     -0.535 | -0.735 | -0.458 |
| o1off_masked  | dense    | Transformer    |         12 |     -0.205 | -0.307 |  0.025 |
| o1off_masked  | sparse   | all pretrained |         30 |     -0.248 | -0.387 | -0.094 |
| o1off_masked  | sparse   | CNN            |         14 |     -0.607 | -0.713 | -0.42  |
| o1off_masked  | sparse   | Transformer    |         12 |     -0.127 | -0.381 |  0.141 |

Note: no oasis_longitudinal sheet found; the time axis is the visit index, not years.
