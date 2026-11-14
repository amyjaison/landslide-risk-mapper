# Real ML Landslide Model

This folder upgrades the transparent risk engine with a real Random Forest model trained on the public Mendeley Data V2 dataset:

**A Geo-Environmental Feature Dataset for Landslide Susceptibility Modelling in Himachal Pradesh, India**
Mirothali Chand (2026), DOI 10.17632/mxpg845z62.2, CC BY 4.0.

The dataset contains 12,409 modelling samples: 6,531 landslide and 5,878 pseudo-absence samples, with seven standardised predictors plus raw values and land cover. This app trains on the three predictors that are also available in its live analysis pipeline: **slope, rainfall and elevation**. The source dataset notes that pseudo-absence points are random and not verified stable ground, so metrics should be interpreted as benchmark results rather than field-validated accuracy.

## Train
From the project root:

```bash
python ml_model/train_model.py
```

This downloads the public dataset archive, automatically finds the modelling CSV, trains/tunes the Random Forest, evaluates a held-out 20% test set, and saves:

- `ml_model/artifacts/landslide_rf.joblib`
- `ml_model/artifacts/metrics.json`
- `ml_model/artifacts/feature_map.json`

## Metrics
The script prints Accuracy, Precision, Recall, F1 and ROC-AUC. Do not claim a metric until this script has actually been run successfully on the dataset.
