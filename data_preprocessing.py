"""
data_preprocessing.py
Data preprocessing module for US neighborhood typology clustering project.
Function: Load, clean, rename, and standardize ACS data.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


def load_and_preprocess_data(data_df=None):
    """
    Load and preprocess acs_data/acs_data.csv or provided DataFrame.
    - Keep only specified columns
    - Rename indicator columns
    - Fill missing values with median
    - Perform Z-score standardization, create *_scaled columns
    Return: Processed DataFrame, standardized feature matrix (np.ndarray)
    """
    if data_df is None:
        filepath = 'acs_data/acs_data.csv'
        try:
            df = pd.read_csv(filepath, low_memory=False, dtype=str)
        except Exception as e:
            raise RuntimeError(f"Cannot read data file {filepath}: {e}")
    else:
        df = data_df.copy()

    required_columns = [
        'GISJOIN', 'STATE', 'COUNTY', 'YEAR', 'NAME_E',
        'AQQIE001',
        'AQP5E001', 'AQP5E007', 'AQP5E008', 'AQP5E009', 'AQP5E010', 'AQP5E011', 'AQP5E012', 'AQP5E013', 'AQP5E014', 'AQP5E015', 'AQP5E016', 'AQP5E017',
        'AQQOE001', 'AQQOE003',
        'AQQKE001', 'AQQKE002'
    ]
    indicator_cols = ['Income', 'Education', 'Employment', 'Diversity']

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Data missing required columns: {missing_cols}")

    # Convert source columns to numeric before derived feature creation.
    numeric_columns = [
        'AQQIE001', 'AQP5E001', 'AQP5E007', 'AQP5E008', 'AQP5E009',
        'AQP5E010', 'AQP5E011', 'AQP5E012', 'AQP5E013', 'AQP5E014',
        'AQP5E015', 'AQP5E016', 'AQP5E017', 'AQQOE001', 'AQQOE003',
        'AQQKE001', 'AQQKE002'
    ]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Build derived indicators using actual available NHGIS ACS field codes.
    df['Income'] = df['AQQIE001']

    education_numerators = df[['AQP5E007', 'AQP5E008', 'AQP5E009', 'AQP5E015', 'AQP5E016', 'AQP5E017']].sum(axis=1, skipna=True)
    df['Education'] = 100.0 * education_numerators / df['AQP5E001']

    df['Employment'] = 100.0 * df['AQQOE003'] / df['AQQOE001']
    df['Diversity'] = 100.0 * (df['AQQKE001'] - df['AQQKE002']) / df['AQQKE001']

    for col in ['Education', 'Employment', 'Diversity']:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan)
        df[col] = df[col].fillna(df[col].median())
        df[col] = df[col].clip(lower=0.0, upper=100.0)

    df['Income'] = df['Income'].fillna(df['Income'].median())

    selected_columns = ['GISJOIN', 'STATE', 'COUNTY', 'YEAR', 'NAME_E'] + indicator_cols
    output_df = df[selected_columns].copy()

    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(output_df[indicator_cols])
    for idx, col in enumerate(indicator_cols):
        output_df[f'{col}_scaled'] = scaled_values[:, idx]

    return output_df, scaled_values


if __name__ == '__main__':
    df, scaled = load_and_preprocess_data()
    print(df.head())
    print(scaled[:5])
