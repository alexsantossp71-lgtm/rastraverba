"""
Querido Diário API Client
Searches official gazettes to find contracts and bidding processes
"""

import requests
import time
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

BASE_URL = "https://queridodiario.ok.org.br/api/gazettes"

# CNPJ regex pattern: XX.XXX.XXX/XXXX-XX
CNPJ_PATTERN = re.compile(r'\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}')

# Rate limiting: 60 requests per minute
REQUEST_DELAY = 1.0  # 1 second between requests


def search_gazettes(
    territory_id: str,
    published_since: str = None,
    published_until: str = None,
    querystring: str = None,
    size: int = 10
) -> List[Dict]:
    """
    Search official gazettes in Querido Diário.
    
    Args:
        territory_id: IBGE municipality code (7 digits)
        published_since: Start date (YYYY-MM-DD)
        published_until: End date (YYYY-MM-DD)
        querystring: Search terms
        size: Number of results (max 100)
    
    Returns:
        List of gazette records
    """
    params = {
        "territory_ids": territory_id,
        "size": min(size, 100),
    }
    
    if published_since:
        params["published_since"] = published_since
    
    if published_until:
        params["published_until"] = published_until
    
    if querystring:
        params["querystring"] = querystring
    
    try:
        # Rate limiting
        time.sleep(REQUEST_DELAY)
        
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        gazettes = data.get("gazettes", [])
        
        logger.info(f"Found {len(gazettes)} gazettes for territory {territory_id}")
        
        return gazettes
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching gazettes: {e}")
        return []


def search_contracts_and_bidding(
    ibge_code: str,
    transfer_date: str,
    days_range: int = 90
) -> List[Dict]:
    """
    Search for contracts and bidding processes related to a transfer.
    
    Args:
        ibge_code: IBGE municipality code
        transfer_date: Date of the transfer (YYYY-MM-DD)
        days_range: Number of days after transfer to search
    
    Returns:
        List of gazette records with contracts/bidding
    """
    try:
        start_date = datetime.strptime(transfer_date, "%Y-%m-%d")
        end_date = start_date + timedelta(days=days_range)
    except (ValueError, TypeError):
        logger.warning(f"Invalid date format: {transfer_date}")
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now()
    
    # Search for "Licitação" OR "Contrato"
    queries = ["Licitação", "Contrato", "Dispensa de Licitação", "Pregão"]
    
    all_gazettes = []
    
    for query in queries:
        gazettes = search_gazettes(
            territory_id=ibge_code,
            published_since=start_date.strftime("%Y-%m-%d"),
            published_until=end_date.strftime("%Y-%m-%d"),
            querystring=query,
            size=20
        )
        
        for gazette in gazettes:
            if gazette not in all_gazettes:
                all_gazettes.append(gazette)
    
    return all_gazettes


def extract_cnpjs(text: str) -> List[str]:
    """
    Extract CNPJ numbers from text using regex.
    
    Args:
        text: Text to search for CNPJs
    
    Returns:
        List of unique CNPJ numbers found
    """
    if not text:
        return []
    
    matches = CNPJ_PATTERN.findall(text)
    
    # Normalize CNPJs (remove formatting)
    normalized = []
    for cnpj in matches:
        clean = re.sub(r'[^\d]', '', cnpj)
        if len(clean) == 14 and clean not in normalized:
            # Format consistently
            formatted = f"{clean[:2]}.{clean[2:5]}.{clean[5:8]}/{clean[8:12]}-{clean[12:]}"
            normalized.append(formatted)
    
    return normalized


def link_transfer_to_gazettes(
    ibge_code: str,
    transfer_date: str,
    transfer_value: float = None
) -> List[Dict]:
    """
    Link a transfer to relevant gazette entries and extract beneficiaries.
    
    Args:
        ibge_code: IBGE municipality code
        transfer_date: Date of the transfer
        transfer_value: Optional value for additional filtering
    
    Returns:
        List of gazette matches with extracted CNPJs
    """
    gazettes = search_contracts_and_bidding(ibge_code, transfer_date)
    
    results = []
    
    for gazette in gazettes:
        # Extract text excerpts
        excerpts = gazette.get("excerpts", [])
        full_text = " ".join(excerpts) if excerpts else ""
        
        # Extract CNPJs from excerpts
        cnpjs = extract_cnpjs(full_text)
        
        # Check if value is mentioned (approximate matching)
        value_match = False
        if transfer_value:
            # Look for similar values in text
            value_str = f"{transfer_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if value_str in full_text or str(int(transfer_value)) in full_text:
                value_match = True
        
        result = {
            "gazette_id": gazette.get("id"),
            "territory_id": gazette.get("territory_id"),
            "territory_name": gazette.get("territory_name"),
            "date": gazette.get("date"),
            "url": gazette.get("url"),
            "txt_url": gazette.get("txt_url"),
            "excerpts": excerpts[:3] if excerpts else [],  # Limit excerpts
            "cnpjs_found": cnpjs,
            "value_mentioned": value_match,
            "source_url": f"https://queridodiario.ok.org.br/diario/{gazette.get('territory_id')}/{gazette.get('date')}"
        }
        
        results.append(result)
    
    return results


def get_gazette_text(gazette_id: str) -> Optional[str]:
    """
    Get full text content of a gazette.
    
    Args:
        gazette_id: ID of the gazette
    
    Returns:
        Full text content or None
    """
    try:
        time.sleep(REQUEST_DELAY)
        
        url = f"{BASE_URL}/{gazette_id}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Try to get text URL and fetch content
        txt_url = data.get("txt_url")
        if txt_url:
            time.sleep(REQUEST_DELAY)
            text_response = requests.get(txt_url, timeout=60)
            text_response.raise_for_status()
            return text_response.text
        
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching gazette text: {e}")
        return None
