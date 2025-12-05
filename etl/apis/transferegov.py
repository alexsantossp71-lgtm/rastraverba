"""
TransfereGov API Client
Traces transfers to find executor_especial (bank account and municipality)
"""

import requests
import time
import logging
import os
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://api.transferegov.gestao.gov.br"


def get_api_key() -> Optional[str]:
    """Get API key from environment variable."""
    return os.environ.get("TRANSFARENCY_API_KEY")


def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate delay with exponential backoff."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    return delay


def make_request(url: str, params: Dict = None, max_retries: int = 5) -> Optional[Dict]:
    """
    Make HTTP request with exponential backoff for rate limiting.
    
    Args:
        url: API endpoint URL
        params: Query parameters
        max_retries: Maximum number of retry attempts
    
    Returns:
        JSON response or None
    """
    headers = {}
    api_key = get_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 429:
                delay = exponential_backoff(attempt)
                logger.warning(f"Rate limited, waiting {delay:.1f}s before retry...")
                time.sleep(delay)
                continue
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                delay = exponential_backoff(attempt)
                logger.warning(f"Request failed, retrying in {delay:.1f}s: {e}")
                time.sleep(delay)
            else:
                logger.error(f"Request failed after {max_retries} attempts: {e}")
                return None
    
    return None


def search_convenios(termo: str = None, ano: int = None) -> List[Dict]:
    """
    Search for convenios (agreements) in TransfereGov.
    
    Args:
        termo: Search term
        ano: Year filter
    
    Returns:
        List of convenio records
    """
    url = f"{BASE_URL}/convenios"
    params = {}
    
    if termo:
        params["termo"] = termo
    if ano:
        params["ano"] = ano
    
    data = make_request(url, params)
    
    if data:
        return data.get("data", [])
    return []


def get_executor_especial(convenio_id: str) -> Optional[Dict]:
    """
    Get executor especial details for a convenio.
    This reveals the specific bank account and municipality (IBGE ID).
    
    Args:
        convenio_id: ID of the convenio/transfer
    
    Returns:
        Dictionary with executor details including IBGE code
    """
    url = f"{BASE_URL}/convenios/{convenio_id}/executor-especial"
    
    data = make_request(url)
    
    if data:
        executor = data.get("data", {})
        return {
            "convenio_id": convenio_id,
            "executor_nome": executor.get("nome"),
            "executor_cnpj": executor.get("cnpj"),
            "municipio_nome": executor.get("municipio"),
            "municipio_ibge": executor.get("codigoIbge"),
            "uf": executor.get("uf"),
            "banco": executor.get("banco"),
            "agencia": executor.get("agencia"),
            "conta": executor.get("conta"),
        }
    
    return None


def trace_transfer(emenda_id: str, valor: float = None) -> Optional[Dict]:
    """
    Trace a transfer from an emenda to find the final destination.
    
    Args:
        emenda_id: Parliamentary amendment ID
        valor: Optional value for filtering
    
    Returns:
        Dictionary with transfer trace information
    """
    # Search for related convenios
    url = f"{BASE_URL}/emendas/{emenda_id}/transferencias"
    
    data = make_request(url)
    
    if not data:
        # Try alternative endpoint
        url = f"{BASE_URL}/transferencias"
        params = {"emenda": emenda_id}
        if valor:
            params["valor"] = valor
        data = make_request(url, params)
    
    if data:
        transferencias = data.get("data", [])
        
        results = []
        for t in transferencias:
            convenio_id = t.get("convenioId") or t.get("id")
            
            if convenio_id:
                # Get executor details
                executor = get_executor_especial(str(convenio_id))
                
                result = {
                    "emenda_id": emenda_id,
                    "transferencia_id": t.get("id"),
                    "valor": t.get("valor") or t.get("valorTotal"),
                    "data_assinatura": t.get("dataAssinatura"),
                    "data_publicacao": t.get("dataPublicacao"),
                    "situacao": t.get("situacao"),
                }
                
                if executor:
                    result.update(executor)
                
                results.append(result)
                
                # Rate limiting
                time.sleep(0.5)
        
        return results if results else None
    
    return None


def get_emendas_pix(ano: int = None) -> List[Dict]:
    """
    Get Emendas Pix (special parliamentary amendments with direct transfers).
    
    Args:
        ano: Year filter
    
    Returns:
        List of Emendas Pix records
    """
    url = f"{BASE_URL}/emendas-pix"
    params = {}
    
    if ano:
        params["ano"] = ano
    
    data = make_request(url, params)
    
    if data:
        emendas = data.get("data", [])
        
        results = []
        for e in emendas:
            result = {
                "emenda_id": e.get("id"),
                "emenda_numero": e.get("numero"),
                "autor": e.get("autor"),
                "valor": e.get("valor"),
                "ano": e.get("ano"),
                "tipo": e.get("tipo"),
            }
            
            # Try to get executor details
            if e.get("id"):
                executor = get_executor_especial(str(e.get("id")))
                if executor:
                    result.update(executor)
            
            results.append(result)
        
        return results
    
    return []
