import pandas as pd
from src.ingestion.converter import FileFormatConverter

path = 'data/demo/testsample.csv'
df = pd.read_csv(path)
print('RAW_COLUMNS', df.columns.tolist())
conv = FileFormatConverter()
out, meta = conv.convert_to_standardized_csv(path, output_filename='testsample_fixed_verify.csv')
converted = pd.read_csv(out)
print('CONVERTED_COLUMNS', converted.columns.tolist())
print('ROWS', len(converted))
print('FIRST_ROW', converted.head(1).to_dict(orient='records')[0])
print('META', meta['total_rows'], meta['total_columns'])
