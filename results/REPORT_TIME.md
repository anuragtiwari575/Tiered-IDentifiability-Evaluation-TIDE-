# Time effect at matched pool size

S = 16, repeats = 50, delay sheets: ['Datasets\\oasis_longitudinal_demographics-8d83e569fa2e2d30 (1).xlsx', 'Datasets\\oasis_cross-sectional-5708aa0a98d82080.xlsx']

## reg / dense (cross-session)

| point             |   years |   0mm pixel |   0mm enc-median |   1mm pixel |   1mm enc-median |   2mm pixel |   2mm enc-median |   3mm pixel |   3mm enc-median |   4mm pixel |   4mm enc-median |
|:------------------|--------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|
| OASIS-1 rescan    |    0.06 |       0.985 |            0.974 |       0.977 |            0.963 |       0.991 |            0.924 |       0.98  |            0.871 |       0.96  |            0.84  |
| OASIS-2 0.0-1.5 y |    1.2  |       0.886 |            0.89  |       0.89  |            0.86  |       0.869 |            0.801 |       0.857 |            0.77  |       0.832 |            0.743 |
| OASIS-2 1.5-2.5 y |    1.94 |       0.863 |            0.84  |       0.864 |            0.806 |       0.851 |            0.748 |       0.836 |            0.712 |       0.799 |            0.653 |
| OASIS-2 2.5-3.5 y |    2.96 |       0.878 |            0.877 |       0.88  |            0.839 |       0.873 |            0.789 |       0.859 |            0.733 |       0.815 |            0.716 |
| OASIS-2 3.5-8.0 y |    4.54 |       0.854 |            0.846 |       0.856 |            0.822 |       0.849 |            0.777 |       0.842 |            0.737 |       0.825 |            0.701 |

- 0 mm: encoders with significant decline over years 24/30; median slope -0.0235/yr; pixel slope -0.0243/yr [-0.0530,+0.0012]; median mm-equivalent of one year 1.024 mm
- 1 mm: encoders with significant decline over years 28/30; median slope -0.0268/yr; pixel slope -0.0227/yr [-0.0485,+0.0052]; median mm-equivalent of one year 1.064 mm
- 2 mm: encoders with significant decline over years 22/30; median slope -0.0258/yr; pixel slope -0.0253/yr [-0.0526,+0.0027]; median mm-equivalent of one year 1.170 mm

## reg / sparse (cross-session)

| point             |   years |   0mm pixel |   0mm enc-median |   1mm pixel |   1mm enc-median |   2mm pixel |   2mm enc-median |   3mm pixel |   3mm enc-median |   4mm pixel |   4mm enc-median |
|:------------------|--------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|
| OASIS-1 rescan    |    0.06 |       1     |            0.99  |       0.987 |            0.927 |       0.995 |            0.818 |       0.983 |            0.767 |       0.97  |            0.707 |
| OASIS-2 0.0-1.5 y |    1.2  |       0.92  |            0.9   |       0.914 |            0.836 |       0.893 |            0.728 |       0.861 |            0.653 |       0.811 |            0.611 |
| OASIS-2 1.5-2.5 y |    1.94 |       0.906 |            0.861 |       0.905 |            0.799 |       0.879 |            0.68  |       0.838 |            0.609 |       0.785 |            0.549 |
| OASIS-2 2.5-3.5 y |    2.96 |       0.911 |            0.886 |       0.908 |            0.827 |       0.897 |            0.715 |       0.874 |            0.631 |       0.802 |            0.581 |
| OASIS-2 3.5-8.0 y |    4.54 |       0.877 |            0.85  |       0.875 |            0.789 |       0.866 |            0.708 |       0.846 |            0.614 |       0.813 |            0.568 |

- 0 mm: encoders with significant decline over years 19/30; median slope -0.0231/yr; pixel slope -0.0234/yr [-0.0489,+0.0016]; median mm-equivalent of one year 0.362 mm
- 1 mm: encoders with significant decline over years 15/30; median slope -0.0241/yr; pixel slope -0.0211/yr [-0.0451,+0.0072]; median mm-equivalent of one year 0.372 mm
- 2 mm: encoders with significant decline over years 14/30; median slope -0.0253/yr; pixel slope -0.0232/yr [-0.0512,+0.0020]; median mm-equivalent of one year 0.392 mm

## regmask / dense (cross-session)

| point             |   years |   0mm pixel |   0mm enc-median |   1mm pixel |   1mm enc-median |   2mm pixel |   2mm enc-median |   3mm pixel |   3mm enc-median |   4mm pixel |   4mm enc-median |
|:------------------|--------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|
| OASIS-1 rescan    |    0.06 |       1     |            0.909 |       1     |            0.808 |       0.988 |            0.632 |       0.986 |            0.541 |       0.947 |            0.493 |
| OASIS-2 0.0-1.5 y |    1.2  |       0.967 |            0.891 |       0.964 |            0.823 |       0.956 |            0.723 |       0.945 |            0.642 |       0.898 |            0.569 |
| OASIS-2 1.5-2.5 y |    1.94 |       0.968 |            0.859 |       0.957 |            0.785 |       0.937 |            0.671 |       0.893 |            0.595 |       0.81  |            0.531 |
| OASIS-2 2.5-3.5 y |    2.96 |       0.953 |            0.882 |       0.946 |            0.812 |       0.92  |            0.69  |       0.878 |            0.615 |       0.783 |            0.551 |
| OASIS-2 3.5-8.0 y |    4.54 |       0.951 |            0.835 |       0.946 |            0.773 |       0.929 |            0.661 |       0.9   |            0.586 |       0.841 |            0.534 |

- 0 mm: encoders with significant decline over years 8/30; median slope -0.0153/yr; pixel slope -0.0103/yr [-0.0308,+0.0034]; median mm-equivalent of one year 0.122 mm
- 1 mm: encoders with significant decline over years 2/30; median slope -0.0077/yr; pixel slope -0.0113/yr [-0.0332,+0.0037]; median mm-equivalent of one year 0.065 mm
- 2 mm: encoders with significant decline over years 0/30; median slope +0.0016/yr; pixel slope -0.0133/yr [-0.0316,+0.0020]; median mm-equivalent of one year -0.011 mm

## regmask / sparse (cross-session)

| point             |   years |   0mm pixel |   0mm enc-median |   1mm pixel |   1mm enc-median |   2mm pixel |   2mm enc-median |   3mm pixel |   3mm enc-median |   4mm pixel |   4mm enc-median |
|:------------------|--------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|------------:|-----------------:|
| OASIS-1 rescan    |    0.06 |       1     |            0.951 |       1     |            0.76  |       0.99  |            0.515 |       0.942 |            0.392 |       0.837 |            0.333 |
| OASIS-2 0.0-1.5 y |    1.2  |       0.974 |            0.926 |       0.978 |            0.811 |       0.961 |            0.614 |       0.92  |            0.468 |       0.841 |            0.425 |
| OASIS-2 1.5-2.5 y |    1.94 |       0.983 |            0.879 |       0.979 |            0.764 |       0.949 |            0.579 |       0.87  |            0.45  |       0.765 |            0.39  |
| OASIS-2 2.5-3.5 y |    2.96 |       0.954 |            0.904 |       0.956 |            0.777 |       0.941 |            0.589 |       0.865 |            0.452 |       0.74  |            0.42  |
| OASIS-2 3.5-8.0 y |    4.54 |       0.963 |            0.865 |       0.957 |            0.768 |       0.938 |            0.579 |       0.883 |            0.44  |       0.791 |            0.399 |

- 0 mm: encoders with significant decline over years 8/30; median slope -0.0175/yr; pixel slope -0.0083/yr [-0.0233,+0.0040]; median mm-equivalent of one year 0.080 mm
- 1 mm: encoders with significant decline over years 0/30; median slope -0.0078/yr; pixel slope -0.0098/yr [-0.0271,+0.0033]; median mm-equivalent of one year 0.038 mm
- 2 mm: encoders with significant decline over years 0/30; median slope +0.0051/yr; pixel slope -0.0111/yr [-0.0279,+0.0021]; median mm-equivalent of one year -0.027 mm
