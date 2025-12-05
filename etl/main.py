"""
RastraVerba ETL Main Pipeline
Orchestrates data fetching, linking, and processing

Usage:
    python etl/main.py [--year YEAR] [--dry-run] [--limit N]
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from apis.camara import fetch_emendas
from apis.transferegov import trace_transfer, get_emendas_pix
from apis.querido_diario import link_transfer_to_gazettes, extract_cnpjs
from utils import setup_logging, RateLimiter, parse_date

logger = logging.getLogger(__name__)

# Output path
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "emendas_rastreadas.parquet"


def process_emendas(year: int, limit: int = None) -> pd.DataFrame:
    """
    Fetch and process parliamentary amendments.
    
    Args:
        year: Year to process
        limit: Maximum number of emendas to process (for testing)
    
    Returns:
        DataFrame with processed emendas
    """
    logger.info(f"Fetching emendas for year {year}...")
    
    # Try TransfereGov Emendas Pix first (more complete data)
    emendas = get_emendas_pix(ano=year)
    
    if not emendas:
        # Fallback to Câmara API
        logger.info("Falling back to Câmara API...")
        emendas = fetch_emendas(year=year)
    
    if limit:
        emendas = emendas[:limit]
    
    logger.info(f"Found {len(emendas)} emendas")
    
    return pd.DataFrame(emendas)


def trace_transfers(emendas_df: pd.DataFrame) -> pd.DataFrame:
    """
    Trace transfers for each emenda to find destinations.
    
    Args:
        emendas_df: DataFrame with emendas
    
    Returns:
        DataFrame with transfer traces
    """
    logger.info("Tracing transfers...")
    
    traced = []
    rate_limiter = RateLimiter(requests_per_minute=60)
    
    for idx, row in emendas_df.iterrows():
        emenda_id = row.get("emenda_id") or row.get("id")
        
        if emenda_id:
            rate_limiter.wait()
            
            transfers = trace_transfer(
                str(emenda_id),
                valor=row.get("valor")
            )
            
            if transfers:
                for t in transfers:
                    t["emenda_autor"] = row.get("autor") or row.get("autor_nome")
                    t["emenda_valor"] = row.get("valor")
                    t["emenda_ano"] = row.get("ano") or row.get("year")
                    traced.append(t)
            else:
                # Keep record even without transfer trace
                traced.append({
                    "emenda_id": emenda_id,
                    "emenda_autor": row.get("autor") or row.get("autor_nome"),
                    "emenda_valor": row.get("valor"),
                    "emenda_ano": row.get("ano") or row.get("year"),
                    "trace_status": "not_found"
                })
        
        # Progress logging
        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx + 1}/{len(emendas_df)} emendas")
    
    return pd.DataFrame(traced)


def link_to_gazettes(transfers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Link transfers to official gazettes using Querido Diário API.
    
    Args:
        transfers_df: DataFrame with transfer traces
    
    Returns:
        DataFrame with gazette links
    """
    logger.info("Linking to gazettes...")
    
    linked = []
    rate_limiter = RateLimiter(requests_per_minute=60)
    
    for idx, row in transfers_df.iterrows():
        ibge_code = row.get("municipio_ibge")
        transfer_date = row.get("data_publicacao") or row.get("data_assinatura")
        
        if ibge_code and transfer_date:
            rate_limiter.wait()
            
            # Parse date to standard format
            parsed_date = parse_date(str(transfer_date))
            
            if parsed_date:
                gazettes = link_transfer_to_gazettes(
                    ibge_code=str(ibge_code),
                    transfer_date=parsed_date,
                    transfer_value=row.get("valor") or row.get("emenda_valor")
                )
                
                if gazettes:
                    for gazette in gazettes:
                        record = row.to_dict()
                        record.update({
                            "gazette_date": gazette.get("date"),
                            "gazette_url": gazette.get("url"),
                            "gazette_source_url": gazette.get("source_url"),
                            "cnpjs_encontrados": ", ".join(gazette.get("cnpjs_found", [])),
                            "evidencia_excerpts": " | ".join(gazette.get("excerpts", [])[:2]),
                            "link_status": "found"
                        })
                        linked.append(record)
                else:
                    record = row.to_dict()
                    record["link_status"] = "no_gazette"
                    linked.append(record)
        else:
            record = row.to_dict()
            record["link_status"] = "missing_data"
            linked.append(record)
        
        # Progress logging
        if (idx + 1) % 10 == 0:
            logger.info(f"Linked {idx + 1}/{len(transfers_df)} transfers")
    
    return pd.DataFrame(linked)


def save_parquet(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save DataFrame to Parquet file optimized for web reading.
    
    Args:
        df: DataFrame to save
        output_path: Output file path
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to PyArrow Table
    table = pa.Table.from_pandas(df)
    
    # Write with compression optimized for web
    pq.write_table(
        table,
        output_path,
        compression='snappy',  # Good balance of speed and size
        use_dictionary=True,
        write_statistics=True
    )
    
    file_size = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Saved {len(df)} records to {output_path} ({file_size:.2f} MB)")


def generate_sample_data() -> pd.DataFrame:
    """
    Generate sample data for development/testing.
    
    Returns:
        DataFrame with sample data
    """
    logger.info("Generating sample data...")
    
    sample = [
        {
            "emenda_id": "EMD001",
            "emenda_autor": "Deputado Exemplo Silva",
            "emenda_valor": 500000.00,
            "emenda_ano": 2024,
            "municipio_nome": "São Paulo",
            "municipio_ibge": "3550308",
            "uf": "SP",
            "executor_cnpj": "12.345.678/0001-90",
            "data_publicacao": "2024-01-15",
            "gazette_url": "https://queridodiario.ok.org.br/diario/3550308/2024-01-20",
            "cnpjs_encontrados": "12.345.678/0001-90, 98.765.432/0001-10",
            "evidencia_excerpts": "CONTRATO Nº 001/2024 - Objeto: Pavimentação",
            "link_status": "found"
        },
        {
            "emenda_id": "EMD002",
            "emenda_autor": "Deputado Teste Oliveira",
            "emenda_valor": 250000.00,
            "emenda_ano": 2024,
            "municipio_nome": "Rio de Janeiro",
            "municipio_ibge": "3304557",
            "uf": "RJ",
            "executor_cnpj": "11.222.333/0001-44",
            "data_publicacao": "2024-02-10",
            "gazette_url": "https://queridodiario.ok.org.br/diario/3304557/2024-02-15",
            "cnpjs_encontrados": "11.222.333/0001-44",
            "evidencia_excerpts": "PREGÃO ELETRÔNICO Nº 015/2024",
            "link_status": "found"
        },
        {
            "emenda_id": "EMD003",
            "emenda_autor": "Deputado Demo Santos",
            "emenda_valor": 750000.00,
            "emenda_ano": 2024,
            "municipio_nome": "Belo Horizonte",
            "municipio_ibge": "3106200",
            "uf": "MG",
            "executor_cnpj": "55.666.777/0001-88",
            "data_publicacao": "2024-03-01",
            "gazette_url": None,
            "cnpjs_encontrados": "",
            "evidencia_excerpts": "",
            "link_status": "no_gazette"
        }
    ]
    
    return pd.DataFrame(sample)


def main():
    """Main ETL pipeline entry point."""
    parser = argparse.ArgumentParser(description="RastraVerba ETL Pipeline")
    parser.add_argument("--year", type=int, default=datetime.now().year,
                        help="Year to process (default: current year)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate sample data instead of fetching APIs")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of emendas to process")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logger.info("=" * 60)
    logger.info("RastraVerba ETL Pipeline")
    logger.info(f"Year: {args.year} | Dry Run: {args.dry_run} | Limit: {args.limit}")
    logger.info("=" * 60)
    
    try:
        if args.dry_run:
            # Generate sample data
            final_df = generate_sample_data()
        else:
            # Step 1: Fetch emendas
            emendas_df = process_emendas(args.year, limit=args.limit)
            
            if emendas_df.empty:
                logger.warning("No emendas found, generating sample data")
                final_df = generate_sample_data()
            else:
                # Step 2: Trace transfers
                transfers_df = trace_transfers(emendas_df)
                
                # Step 3: Link to gazettes
                final_df = link_to_gazettes(transfers_df)
        
        # Step 4: Save to Parquet
        save_parquet(final_df, OUTPUT_FILE)
        
        logger.info("=" * 60)
        logger.info("ETL Pipeline completed successfully!")
        logger.info(f"Output: {OUTPUT_FILE}")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"ETL Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
