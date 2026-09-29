import pytest
import pandas as pd
from src.ingestion.schema_validator import SchemaValidator
from src.ingestion.normalizer import DataNormalizer
from src.data.dataset_adapter import DatasetAdapter
from src.ingestion.converter import FileFormatConverter

def test_schema_validator_valid_tx():
    rec = {"txid": "230425000", "input_amount": 1.5, "fee": 0.0001, "time_step": 5}
    is_valid, errors = SchemaValidator.validate_transaction_record(rec)
    assert is_valid is True
    assert len(errors) == 0

def test_schema_validator_invalid_tx():
    rec = {"txid": "", "input_amount": -10.0, "time_step": 150}
    is_valid, errors = SchemaValidator.validate_transaction_record(rec)
    assert is_valid is False
    assert len(errors) >= 2

def test_normalizer_timestamp():
    iso_ts = DataNormalizer.normalize_timestamp("2025-01-01 12:00:00")
    assert "2025-01-01" in iso_ts
    assert "T" in iso_ts

def test_dataset_adapter_validation():
    adapter = DatasetAdapter("elliptic")
    df_feat = pd.DataFrame({"txid": ["1", "2"], "time_step": [1, 2], "feat_0": [0.1, 0.2]})
    df_cls = pd.DataFrame({"txid": ["1", "2"], "label": ["licit", "illicit"]})
    df_edge = pd.DataFrame({"source_txid": ["1"], "target_txid": ["2"]})
    
    is_valid, errors = adapter.validate_schema({"features": df_feat, "classes": df_cls, "edges": df_edge})
    assert is_valid is True
    assert len(errors) == 0


def test_converter_normalizes_csv_and_returns_success(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "transaction_id,amount,src_ip,dst_ip\nTX-1,1.5,1.1.1.1,2.2.2.2\n",
        encoding="utf-8"
    )

    converter = FileFormatConverter(
        converted_dir=str(tmp_path / "converted"),
        error_dir=str(tmp_path / "errors")
    )

    output_path, metadata = converter.convert_to_standardized_csv(
        str(csv_path),
        output_filename="converted_sample.csv"
    )

    assert output_path.endswith("converted_sample.csv")
    assert metadata["status"] == "success"
    converted = pd.read_csv(output_path)
    assert len(converted) == 1
    assert "txid" in converted.columns or "transaction_id" in converted.columns
