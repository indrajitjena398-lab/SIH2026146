"""
Dataset Scanner API Router.
Handles file uploads (CSV, JSON, Excel .xlsx/.xls, XML), runs multi-layer threat analysis,
and generates sample downloadable datasets for instant testing.
"""

import os
import io
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
import pandas as pd

from backend.services.scanner_service import DatasetScannerService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Scanner"])

@router.post("/scan")
async def scan_dataset_alias(
    file: Optional[UploadFile] = File(None),
    use_demo: bool = Form(False)
):
    """Alias for scan endpoint matching ApiService.scanDataset."""
    if use_demo:
        demo_path = "data/demo/demo_transactions.csv"
        if os.path.exists(demo_path):
            with open(demo_path, "rb") as f:
                content = f.read()
            df = DatasetScannerService.parse_file_to_dataframe(content, "demo_transactions.csv")
            analysis = DatasetScannerService.analyze_dataset(df, max_rows=500)
            analysis["filename"] = "demo_transactions.csv"
            analysis["file_size_bytes"] = len(content)
            return analysis
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    return await scan_dataset_file(file)

@router.post("/file")
async def scan_dataset_file(
    file: UploadFile = File(...)
):
    """
    Accepts CSV, JSON, Excel (.xlsx/.xls), or XML dataset files.
    Performs multi-layer threat detection and returns complete classification breakdown.
    """
    filename = file.filename or "uploaded_dataset.csv"
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Parse dataframe
        df = DatasetScannerService.parse_file_to_dataframe(content, filename)
        
        # Analyze up to 500 rows for high-speed sub-second responsiveness
        analysis = DatasetScannerService.analyze_dataset(df, max_rows=500)
        analysis["filename"] = filename
        analysis["file_size_bytes"] = len(content)

        return analysis
    except Exception as e:
        logger.error("Error scanning file %s: %s", filename, e)
        raise HTTPException(status_code=400, detail=f"Analysis failed: {str(e)}")

@router.get("/sample/{file_format}")
def download_sample_dataset(file_format: str):
    """
    Generates a realistic demo dataset with mixed attack (Ransomware, Mixer, P2P flood)
    and normal traffic records in CSV, JSON, or Excel format.
    """
    fmt = file_format.lower()
    
    sample_records = [
        {
            "txid": "TX_RANSOM_001",
            "amount": 14.5,
            "fee": 0.005,
            "input_count": 1,
            "output_count": 18,
            "src_ip": "185.220.101.5",
            "asn": "AS200651",
            "country": "IS",
            "scenario": "rapid_movement",
            "time_step": 48
        },
        {
            "txid": "TX_NORMAL_002",
            "amount": 0.25,
            "fee": 0.0001,
            "input_count": 2,
            "output_count": 2,
            "src_ip": "88.198.54.2",
            "asn": "AS24940",
            "country": "DE",
            "scenario": "normal_propagation",
            "time_step": 48
        },
        {
            "txid": "TX_MIXER_003",
            "amount": 8.0,
            "fee": 0.002,
            "input_count": 1,
            "output_count": 24,
            "src_ip": "194.26.29.112",
            "asn": "AS206264",
            "country": "SC",
            "scenario": "layering_pattern",
            "time_step": 48
        },
        {
            "txid": "TX_NORMAL_004",
            "amount": 1.2,
            "fee": 0.0001,
            "input_count": 1,
            "output_count": 2,
            "src_ip": "142.250.180.206",
            "asn": "AS15169",
            "country": "US",
            "scenario": "normal_propagation",
            "time_step": 47
        },
        {
            "txid": "TX_FLOOD_005",
            "amount": 0.05,
            "fee": 0.008,
            "input_count": 5,
            "output_count": 2,
            "src_ip": "185.220.100.240",
            "asn": "AS200651",
            "country": "DE",
            "scenario": "burst_behavior",
            "time_step": 48
        },
        {
            "txid": "TX_NORMAL_006",
            "amount": 3.45,
            "fee": 0.0002,
            "input_count": 2,
            "output_count": 1,
            "src_ip": "104.18.32.11",
            "asn": "AS13335",
            "country": "US",
            "scenario": "normal_propagation",
            "time_step": 46
        },
        {
            "txid": "TX_DARKNET_007",
            "amount": 5.75,
            "fee": 0.001,
            "input_count": 1,
            "output_count": 10,
            "src_ip": "185.107.56.88",
            "asn": "AS51852",
            "country": "CH",
            "scenario": "repeated_connections",
            "time_step": 49
        },
        {
            "txid": "TX_NORMAL_008",
            "amount": 0.08,
            "fee": 0.00005,
            "input_count": 1,
            "output_count": 2,
            "src_ip": "51.15.210.88",
            "asn": "AS12876",
            "country": "FR",
            "scenario": "normal_propagation",
            "time_step": 49
        }
    ]

    df_sample = pd.DataFrame(sample_records)

    if fmt in ["xlsx", "excel"]:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_sample.to_excel(writer, index=False, sheet_name="Transactions")
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=sample_bitcoin_threat_dataset.xlsx"}
        )
    elif fmt == "json":
        json_str = json.dumps(sample_records, indent=2)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=sample_bitcoin_threat_dataset.json"}
        )
    else:
        # Default CSV
        csv_str = df_sample.to_csv(index=False)
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sample_bitcoin_threat_dataset.csv"}
        )
