import pytest
from scripts.generate_network_data import generate_synthetic_network_records, generate_minimum_synthetic_dataset
from src.enrichment.geoip import enrich_ip

def test_generate_minimum_dataset_schema():
    df = generate_minimum_synthetic_dataset(num_rows=20, seed=42)
    required_cols = {
        "timestamp", "src_ip", "dst_ip", "src_port", "dst_port", "txid",
        "input_addresses", "output_addresses", "input_amounts", "output_amounts",
        "fee", "script_type", "geo_country", "asn", "is_illicit"
    }
    assert required_cols.issubset(set(df.columns))
    assert len(df) == 20
    assert df["is_illicit"].isin([0, 1]).all()


def test_generate_synthetic_network_determinism():
    txids = ["tx_001", "tx_002", "tx_003"]
    df1 = generate_synthetic_network_records(txids=txids, num_rows=100, seed=42)
    df2 = generate_synthetic_network_records(txids=txids, num_rows=100, seed=42)
    
    assert len(df1) == 100
    assert len(df2) == 100
    assert df1.equals(df2)
    assert (df1["is_synthetic"] == True).all()

def test_geoip_enrichment():
    res = enrich_ip("185.220.100.240")
    assert res["is_valid"] is True
    assert res["geo_country"] == "DE"
    assert res["asn"] == "AS200651"

def test_geoip_private_ip():
    res = enrich_ip("192.168.1.1")
    assert res["is_private"] is True
    assert res["geo_country"] == "LOCAL"
