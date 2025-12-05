"""
Câmara dos Deputados Open Data API Client
Fetches parliamentary amendments (emendas) data
"""

import requests
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"


def fetch_emendas(year: int = None) -> List[Dict]:
    """
    Fetch parliamentary amendments from Câmara dos Deputados API.
    
    Args:
        year: Year to fetch amendments for. Defaults to current year.
    
    Returns:
        List of amendment dictionaries with author, value, and ID.
    """
    if year is None:
        year = datetime.now().year
    
    emendas = []
    page = 1
    items_per_page = 100
    
    logger.info(f"Fetching emendas for year {year}...")
    
    while True:
        try:
            # Fetch proposições (which include emendas)
            url = f"{BASE_URL}/proposicoes"
            params = {
                "siglaTipo": "EMC,EMP,EMR,EMS",  # Types of amendments
                "ano": year,
                "pagina": page,
                "itens": items_per_page,
                "ordem": "ASC",
                "ordenarPor": "id"
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("dados", [])
            
            if not items:
                break
            
            for item in items:
                emenda = {
                    "id": item.get("id"),
                    "sigla_tipo": item.get("siglaTipo"),
                    "numero": item.get("numero"),
                    "ano": item.get("ano"),
                    "ementa": item.get("ementa", ""),
                }
                
                # Fetch author details
                author_info = fetch_autor(item.get("id"))
                if author_info:
                    emenda.update(author_info)
                
                emendas.append(emenda)
            
            logger.info(f"Fetched page {page}, total items so far: {len(emendas)}")
            page += 1
            
            # Rate limiting
            time.sleep(0.5)
            
            # Safety limit for development
            if page > 10:
                logger.warning("Reached page limit, stopping fetch")
                break
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching emendas page {page}: {e}")
            break
    
    return emendas


def fetch_autor(proposicao_id: int) -> Optional[Dict]:
    """
    Fetch author information for a specific proposition.
    
    Args:
        proposicao_id: ID of the proposition
    
    Returns:
        Dictionary with author information or None
    """
    try:
        url = f"{BASE_URL}/proposicoes/{proposicao_id}/autores"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        autores = data.get("dados", [])
        
        if autores:
            autor = autores[0]  # Get primary author
            return {
                "autor_nome": autor.get("nome"),
                "autor_tipo": autor.get("tipo"),
                "autor_uri": autor.get("uri"),
            }
        
        return None
        
    except requests.exceptions.RequestException as e:
        logger.debug(f"Could not fetch author for {proposicao_id}: {e}")
        return None


def fetch_deputado_details(deputado_id: int) -> Optional[Dict]:
    """
    Fetch detailed information about a deputy.
    
    Args:
        deputado_id: ID of the deputy
    
    Returns:
        Dictionary with deputy details or None
    """
    try:
        url = f"{BASE_URL}/deputados/{deputado_id}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        deputado = data.get("dados", {})
        
        return {
            "deputado_id": deputado.get("id"),
            "deputado_nome": deputado.get("nomeCivil"),
            "deputado_partido": deputado.get("ultimoStatus", {}).get("siglaPartido"),
            "deputado_uf": deputado.get("ultimoStatus", {}).get("siglaUf"),
        }
        
    except requests.exceptions.RequestException as e:
        logger.debug(f"Could not fetch deputy {deputado_id}: {e}")
        return None
