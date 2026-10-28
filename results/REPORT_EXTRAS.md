# TIDE extras

Total time: 7.2 min; sheets: ['Datasets\\oasis_cross-sectional-5708aa0a98d82080.xlsx', 'Datasets\\oasis_longitudinal_demographics-8d83e569fa2e2d30 (1).xlsx']

## A. Privacy-utility (identity GEN vs diagnosis AUC across pretrained encoders)

| cond       |   n_encoders |   spearman_GEN_vs_AUC |     lo |     hi | best_AUC_model     |   best_AUC |   pixel_AUC |   age_only_AUC | pareto_low_identity_high_utility                                   |
|:-----------|-------------:|----------------------:|-------:|-------:|:-------------------|-----------:|------------:|---------------:|:-------------------------------------------------------------------|
| o1_masked  |           30 |                 0.308 | -0.095 |  0.625 | resnet50_swsl      |      0.818 |       0.758 |          0.661 | resnext50_in1k, inceptionv3_in1k, resnet50_swsl                    |
| o1_gfc     |           30 |                 0.032 | -0.299 |  0.346 | mobilenetv3_l_in1k |      0.786 |       0.75  |          0.661 | resnext50_in1k, vgg16bn_in1k, inceptionv3_in1k, mobilenetv3_l_in1k |
| o1_raw     |           30 |                 0.202 | -0.17  |  0.579 | mobilenetv3_l_in1k |      0.762 |       0.587 |          0.665 | inceptionv3_in1k, mobilenetv3_l_in1k, coatnet0_in1k, resnet50_swsl |
| o2_regmask |           30 |                 0.276 | -0.125 |  0.633 | resnet50_in1k      |      0.708 |       0.68  |          0.448 | resnet50_in1k, vgg16bn_in1k, inceptionv3_in1k, resnet50_swsl       |
| o2_reg     |           30 |                -0.002 | -0.299 |  0.329 | dinov2_vitb14      |      0.651 |       0.669 |          0.448 | vgg16bn_in1k, inceptionv3_in1k, dinov2_vitb14                      |
| o2_raw     |           30 |                -0.366 | -0.666 | -0.019 | dinov2_vitb14      |      0.652 |       0.616 |          0.502 | resnet50_in1k, inceptionv3_in1k, dinov2_vitb14, clip_vitb16_openai |

Top-5 AUC per condition:

| cond       | model                  |   AUC |   AUC_lo |   AUC_hi |   GEN |
|:-----------|:-----------------------|------:|---------:|---------:|------:|
| o1_gfc     | mobilenetv3_l_in1k     | 0.786 |    0.677 |    0.886 | 0.904 |
| o1_gfc     | resnext50_in1k         | 0.769 |    0.633 |    0.9   | 0.613 |
| o1_gfc     | coatnet0_in1k          | 0.767 |    0.69  |    0.843 | 0.752 |
| o1_gfc     | resnet18_in1k          | 0.766 |    0.67  |    0.859 | 0.791 |
| o1_gfc     | resnet50_swsl          | 0.765 |    0.665 |    0.869 | 0.766 |
| o1_masked  | resnet50_swsl          | 0.818 |    0.7   |    0.914 | 0.273 |
| o1_masked  | dinov2_vits14          | 0.794 |    0.711 |    0.906 | 0.397 |
| o1_masked  | resnet101_in1k         | 0.772 |    0.69  |    0.861 | 0.302 |
| o1_masked  | dinov2_vitb14          | 0.769 |    0.701 |    0.844 | 0.409 |
| o1_masked  | poolformer_s12_in1k    | 0.768 |    0.7   |    0.871 | 0.344 |
| o1_raw     | mobilenetv3_l_in1k     | 0.762 |    0.676 |    0.868 | 0.741 |
| o1_raw     | coatnet0_in1k          | 0.758 |    0.647 |    0.86  | 0.561 |
| o1_raw     | poolformer_s12_in1k    | 0.748 |    0.648 |    0.857 | 0.632 |
| o1_raw     | resnet50_swsl          | 0.747 |    0.628 |    0.859 | 0.399 |
| o1_raw     | efficientnet_b0_in1k   | 0.738 |    0.657 |    0.813 | 0.741 |
| o2_raw     | dinov2_vitb14          | 0.652 |    0.481 |    0.791 | 0.263 |
| o2_raw     | convnext_base_in1k     | 0.64  |    0.498 |    0.755 | 0.284 |
| o2_raw     | resnet50_in1k          | 0.635 |    0.513 |    0.762 | 0.215 |
| o2_raw     | inceptionv3_in1k       | 0.631 |    0.502 |    0.758 | 0.152 |
| o2_raw     | resnext50_in1k         | 0.628 |    0.493 |    0.79  | 0.18  |
| o2_reg     | pixel                  | 0.669 |    0.49  |    0.799 | 0.732 |
| o2_reg     | dinov2_vitb14          | 0.651 |    0.508 |    0.809 | 0.311 |
| o2_reg     | efficientnet_b0_in1k   | 0.645 |    0.494 |    0.784 | 0.504 |
| o2_reg     | efficientnetv2_s_in21k | 0.641 |    0.431 |    0.778 | 0.387 |
| o2_reg     | dino_vits16            | 0.634 |    0.428 |    0.797 | 0.588 |
| o2_regmask | resnet50_in1k          | 0.708 |    0.563 |    0.884 | 0.226 |
| o2_regmask | resnet50_swsl          | 0.702 |    0.559 |    0.845 | 0.194 |
| o2_regmask | mixer_b16_in21k        | 0.687 |    0.559 |    0.863 | 0.283 |
| o2_regmask | pixel                  | 0.68  |    0.534 |    0.818 | 0.548 |
| o2_regmask | densenet121_in1k       | 0.673 |    0.475 |    0.855 | 0.368 |

## B. Verification (attack-style)

- o1_gfc @ 0 mm (S=20): pixel AUC 0.976 EER 0.009 TAR@1%FAR 0.970 rank-1(subject) 1.000; encoders AUC median 1.000 (range 0.959-1.000), best resnet18_in1k
- o1_gfc @ 1 mm (S=20): pixel AUC 0.979 EER 0.028 TAR@1%FAR 0.970 rank-1(subject) 1.000; encoders AUC median 0.996 (range 0.953-1.000), best mobilenetv3_l_in1k
- o1_gfc @ 2 mm (S=20): pixel AUC 0.977 EER 0.007 TAR@1%FAR 0.975 rank-1(subject) 1.000; encoders AUC median 0.973 (range 0.899-0.999), best mae_vitb16
- o1_gfc @ 4 mm (S=20): pixel AUC 0.971 EER 0.035 TAR@1%FAR 0.755 rank-1(subject) 1.000; encoders AUC median 0.871 (range 0.771-0.985), best mae_vitb16
- o1_masked @ 0 mm (S=20): pixel AUC 1.000 EER 0.000 TAR@1%FAR 1.000 rank-1(subject) 1.000; encoders AUC median 1.000 (range 0.952-1.000), best mixer_b16_in21k
- o1_masked @ 1 mm (S=20): pixel AUC 1.000 EER 0.000 TAR@1%FAR 1.000 rank-1(subject) 1.000; encoders AUC median 0.982 (range 0.908-0.999), best mae_vitb16
- o1_masked @ 2 mm (S=20): pixel AUC 1.000 EER 0.000 TAR@1%FAR 1.000 rank-1(subject) 1.000; encoders AUC median 0.897 (range 0.810-0.979), best mae_vitb16
- o1_masked @ 4 mm (S=20): pixel AUC 0.891 EER 0.174 TAR@1%FAR 0.150 rank-1(subject) 1.000; encoders AUC median 0.715 (range 0.658-0.845), best mae_vitb16
- o1_raw @ 0 mm (S=20): pixel AUC 0.791 EER 0.286 TAR@1%FAR 0.360 rank-1(subject) 0.350; encoders AUC median 0.912 (range 0.844-0.974), best mae_vitb16
- o1_raw @ 1.25 mm (S=20): pixel AUC 0.793 EER 0.288 TAR@1%FAR 0.370 rank-1(subject) 0.350; encoders AUC median 0.895 (range 0.806-0.971), best mae_vitb16
- o2_raw @ 0 mm (S=150): pixel AUC 0.731 EER 0.336 TAR@1%FAR 0.120 rank-1(subject) 0.113; encoders AUC median 0.860 (range 0.779-0.916), best mobilenetv3_l_in1k
- o2_raw @ 1.25 mm (S=150): pixel AUC 0.730 EER 0.339 TAR@1%FAR 0.119 rank-1(subject) 0.120; encoders AUC median 0.860 (range 0.779-0.918), best mobilenetv3_l_in1k
- o2_raw @ 2.5 mm (S=150): pixel AUC 0.731 EER 0.339 TAR@1%FAR 0.119 rank-1(subject) 0.127; encoders AUC median 0.842 (range 0.773-0.903), best mobilenetv3_l_in1k
- o2_raw @ 5 mm (S=150): pixel AUC 0.731 EER 0.338 TAR@1%FAR 0.109 rank-1(subject) 0.113; encoders AUC median 0.794 (range 0.728-0.862), best mae_vitb16
- o2_reg @ 0 mm (S=118): pixel AUC 0.986 EER 0.057 TAR@1%FAR 0.891 rank-1(subject) 0.966; encoders AUC median 0.985 (range 0.947-0.998), best densenet121_in1k
- o2_reg @ 1 mm (S=118): pixel AUC 0.986 EER 0.057 TAR@1%FAR 0.886 rank-1(subject) 0.958; encoders AUC median 0.975 (range 0.928-0.995), best densenet121_in1k
- o2_reg @ 2 mm (S=118): pixel AUC 0.984 EER 0.066 TAR@1%FAR 0.850 rank-1(subject) 0.949; encoders AUC median 0.943 (range 0.883-0.983), best mae_vitb16
- o2_reg @ 4 mm (S=118): pixel AUC 0.962 EER 0.102 TAR@1%FAR 0.517 rank-1(subject) 0.915; encoders AUC median 0.852 (range 0.762-0.953), best mae_vitb16
- o2_regmask @ 0 mm (S=118): pixel AUC 0.985 EER 0.040 TAR@1%FAR 0.947 rank-1(subject) 0.975; encoders AUC median 0.986 (range 0.930-0.997), best densenet121_in1k
- o2_regmask @ 1 mm (S=118): pixel AUC 0.985 EER 0.043 TAR@1%FAR 0.943 rank-1(subject) 0.975; encoders AUC median 0.963 (range 0.885-0.988), best densenet121_in1k
- o2_regmask @ 2 mm (S=118): pixel AUC 0.981 EER 0.054 TAR@1%FAR 0.848 rank-1(subject) 0.975; encoders AUC median 0.904 (range 0.818-0.959), best dino_vits16
- o2_regmask @ 4 mm (S=118): pixel AUC 0.886 EER 0.174 TAR@1%FAR 0.088 rank-1(subject) 0.949; encoders AUC median 0.776 (range 0.721-0.848), best dino_vits16

## C. Cross-dataset linkage audit (OASIS-2 queries vs 416 OASIS-1 subjects)

| variant   | model            |   n_gallery |   n_queries |   n_calibration |   genuine_median |   impostor_q999 |     tau |   calibration_recall_at_tau |   queries_above_tau |   sex_agreement |   median_abs_age_diff |
|:----------|:-----------------|------------:|------------:|----------------:|-----------------:|----------------:|--------:|----------------------------:|--------------------:|----------------:|----------------------:|
| masked    | pixel            |         416 |         144 |              16 |            0.867 |           0.731 |   0.784 |                       0.938 |                  60 |          nan    |                   nan |
| masked    | dino_vits16      |         416 |         144 |              16 |            0.706 |           0.632 |   0.678 |                       0.812 |                  60 |          nan    |                   nan |
| masked    | mae_vitb16       |         416 |         144 |              16 |            0.682 |           0.608 |   0.608 |                       0.812 |                  45 |          nan    |                   nan |
| masked    | densenet121_in1k |         416 |         144 |              16 |            0.651 |           0.541 |   0.634 |                       0.75  |                  60 |          nan    |                   nan |
| masked    | random pairs     |         nan |         nan |             nan |          nan     |         nan     | nan     |                     nan     |                 nan |            0.52 |                    22 |
| gfc       | pixel            |         416 |         144 |              16 |            0.792 |           0.705 |   0.705 |                       0.812 |                   0 |          nan    |                   nan |
| gfc       | dino_vits16      |         416 |         144 |              16 |            0.688 |           0.566 |   0.566 |                       1     |                  22 |          nan    |                   nan |
| gfc       | mae_vitb16       |         416 |         144 |              16 |            0.625 |           0.591 |   0.591 |                       0.625 |                  15 |          nan    |                   nan |
| gfc       | densenet121_in1k |         416 |         144 |              16 |            0.659 |           0.43  |   0.508 |                       1     |                  48 |          nan    |                   nan |
| gfc       | random pairs     |         nan |         nan |             nan |          nan     |         nan     | nan     |                     nan     |                 nan |            0.52 |                    22 |

- masked: 59 candidate cross-dataset matches; sex agreement 1.00; median |age difference| 0.0 y (compare with random pairs above)
(Candidate IDs are in linkage_candidates.csv for internal verification only - report counts, not identities.)

## D. Identity correlation length (lambda, mm)

| curve                                 | subset         |   spearman_logparams_vs_lambda |   pixel_lambda |   median_lambda |
|:--------------------------------------|:---------------|-------------------------------:|---------------:|----------------:|
| OASIS-1 t88_masked all within         | all pretrained |                         -0.108 |          3.619 |           1.803 |
| OASIS-1 t88_masked reliability rescan | all pretrained |                         -0.203 |          8.143 |           3.863 |
| OASIS-1 t88_gfc all within            | all pretrained |                         -0.121 |         38.1   |          12.469 |
| OASIS-1 t88_gfc reliability rescan    | all pretrained |                         -0.258 |         61.215 |          18.45  |
| OASIS-2 o2_regmask cross              | all pretrained |                          0.089 |          5.982 |           3.233 |
| OASIS-2 o2_regmask within             | all pretrained |                          0.139 |          7.001 |           3.603 |
| OASIS-2 o2_reg cross                  | all pretrained |                          0.102 |         19.986 |           6.722 |

- OASIS-1 t88_gfc all within: top3 mae_vitb16 184.93, densenet121_in1k 54.96, efficientnet_b0_in1k 30.81; bottom3 resnext50_in1k 5.27, vgg16bn_in1k 4.18, inceptionv3_in1k 2.86; median R2 0.95
- OASIS-1 t88_gfc reliability rescan: top3 mae_vitb16 371.56, densenet121_in1k 66.83, dino_vits16 46.16; bottom3 resnext50_in1k 9.24, vgg16bn_in1k 8.99, inceptionv3_in1k 5.99; median R2 0.92
- OASIS-1 t88_masked all within: top3 mae_vitb16 4.73, dino_vits16 3.67, densenet121_in1k 2.95; bottom3 inceptionv3_in1k 1.31, resnext50_in1k 1.18, vgg16bn_in1k 1.12; median R2 0.96
- OASIS-1 t88_masked reliability rescan: top3 mae_vitb16 11.86, dino_vits16 7.25, densenet121_in1k 5.69; bottom3 inceptionv3_in1k 2.77, vgg16bn_in1k 2.62, resnext50_in1k 2.49; median R2 0.95
- OASIS-2 o2_reg cross: top3 mae_vitb16 16.85, dino_vits16 11.76, densenet121_in1k 10.78; bottom3 vgg16bn_in1k 4.12, resnext50_in1k 3.95, inceptionv3_in1k 3.17; median R2 0.95
- OASIS-2 o2_regmask cross: top3 mae_vitb16 5.37, dino_vits16 5.04, densenet121_in1k 4.44; bottom3 vgg16bn_in1k 2.35, resnext50_in1k 2.35, inceptionv3_in1k 2.26; median R2 0.97
- OASIS-2 o2_regmask within: top3 mae_vitb16 7.90, dino_vits16 7.26, densenet121_in1k 5.54; bottom3 vgg16bn_in1k 2.04, resnext50_in1k 2.04, inceptionv3_in1k 1.88; median R2 0.92
