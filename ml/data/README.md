# Convertir les CSV CICIDS2017 en Parquet

Le module `ml.data.parquet` convertit les CSV par lots pour limiter la mémoire
utilisée. Il conserve l'arborescence des sources dans `ml/data/processed/parquet`
et utilise la compression Snappy par défaut.

## Installation

Depuis la racine du dépôt, installez les dépendances ML si nécessaire :

```bash
pip install -r ml/requirements.txt
```

## Conversion en ligne de commande

Convertir récursivement tous les CSV de `ml/data/raw` :

```bash
python -m ml.data.parquet
```

Choisir un jeu de données et un dossier de sortie :

```bash
python -m ml.data.parquet \
  --source "ml/data/raw/MachineLearningCSV/MachineLearningCVE" \
  --destination "ml/data/processed/parquet/MachineLearningCVE"
```

Les options `--compression` (`snappy`, `gzip`, `brotli`, `lz4`, `zstd`,
`uncompressed`) et `--block-size` permettent d'ajuster la conversion.

## Utilisation depuis Python

```python
from ml.data.parquet import convert_csv_directory, read_parquet

files = convert_csv_directory(
    "ml/data/raw/MachineLearningCSV/MachineLearningCVE",
    "ml/data/processed/parquet/MachineLearningCVE",
)

# Charger un fichier, ou un dossier contenant des fichiers Parquet compatibles.
flows = read_parquet(files[0], columns=["Flow Duration", "Label"])
attacks = read_parquet(
    "ml/data/processed/parquet/MachineLearningCVE",
    columns=["Flow Duration", "Label"],
    filters=[("Label", "!=", "BENIGN")],
)
```

`convert_csv_to_parquet(source, destination)` convertit également un seul fichier.
Pour charger tout un jeu de données en mémoire, utilisez `read_parquet` sur son
dossier de sortie ; pour les analyses volumineuses, sélectionnez les colonnes ou
utilisez les filtres. Les octets de texte qui ne sont pas de l'UTF-8 valide sont
remplacés par le caractère Unicode de remplacement (`�`) durant la conversion.