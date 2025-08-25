import requests
import logging
from typing import List, Dict, Optional, Union
import time
from config import *

class APIClient:
    def __init__(self):
        self.session = requests.Session()
        # Set reasonable timeouts
        self.session.timeout = 10
        # Add headers to appear more legitimate
        self.session.headers.update({
            'User-Agent': 'DietRx-Enhanced/1.0',
            'Accept': 'application/json'
        })
        
    def _make_request(self, url: str, params: Dict = None, retries: int = 2) -> Optional[Dict]:
        """Make HTTP request with retries and error handling"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params)
                
                # Check if we got a successful response
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logging.debug(f"404 Not Found for URL: {url} with params: {params}")
                    return None  # Don't retry on 404
                elif response.status_code == 429:
                    logging.warning(f"Rate limited, waiting before retry...")
                    time.sleep(2)  # Wait longer for rate limits
                    continue
                else:
                    logging.warning(f"HTTP {response.status_code} for URL: {url}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logging.debug(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt == retries - 1:
                    logging.debug(f"All retry attempts failed for URL: {url}")
                    return None
                time.sleep(0.5)  # Brief wait before retry
                
        return None

class FDAClient(APIClient):
    """Client for FDA Drug API"""
    
    def search_drugs(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for drugs in FDA database"""
        # FDA API is very strict about queries, so we'll be more conservative
        url = f"{FDA_BASE_URL}label.json"
        
        # Try different search strategies
        search_terms = [
            f'openfda.generic_name:"{query.lower()}"',
            f'openfda.brand_name:"{query.lower()}"',
            f'openfda.substance_name:"{query.lower()}"'
        ]
        
        for search_term in search_terms:
            params = {
                'search': search_term,
                'limit': min(limit, 5)  # Keep it small to avoid issues
            }
            
            try:
                response = self._make_request(url, params)
                if response and 'results' in response:
                    logging.debug(f"FDA API success for {query}")
                    return response['results']
            except Exception as e:
                logging.debug(f"FDA API search term failed: {search_term}")
                continue
        
        logging.debug(f"No FDA results for {query}")
        return []
    
    def get_drug_interactions(self, drug_name: str) -> List[Dict]:
        """Get drug interaction data from FDA"""
        # This API is often unavailable or restricted, so we'll make it optional
        return []

class RxNavClient(APIClient):
    """Client for RxNav API (National Library of Medicine)"""
    
    def search_drugs(self, query: str) -> List[Dict]:
        """Search for drugs in RxNav"""
        url = f"{RXNAV_BASE_URL}drugs.json"
        params = {'name': query}
        
        try:
            response = self._make_request(url, params)
            if response and 'drugGroup' in response:
                drugs = []
                drug_group = response['drugGroup']
                if 'conceptGroup' in drug_group:
                    for group in drug_group['conceptGroup']:
                        if 'conceptProperties' in group:
                            for concept in group['conceptProperties']:
                                drugs.append({
                                    'name': concept.get('name', ''),
                                    'rxcui': concept.get('rxcui', ''),
                                    'synonym': concept.get('synonym', ''),
                                    'tty': concept.get('tty', '')
                                })
                logging.debug(f"RxNav found {len(drugs)} results for {query}")
                return drugs
            else:
                logging.debug(f"No RxNav results for {query}")
                return []
            
        except Exception as e:
            logging.debug(f"RxNav API error for {query}: {e}")
            return []
    
    def get_drug_interactions(self, rxcui: str) -> List[Dict]:
        """Get drug interactions from RxNav"""
        url = f"{RXNAV_BASE_URL}interaction/interaction.json"
        params = {'rxcui': rxcui}
        
        try:
            response = self._make_request(url, params)
            if response and 'interactionTypeGroup' in response:
                interactions = []
                for group in response['interactionTypeGroup']:
                    if 'interactionType' in group:
                        for interaction in group['interactionType']:
                            if 'interactionPair' in interaction:
                                interactions.extend(interaction['interactionPair'])
                return interactions
            return []
            
        except Exception as e:
            logging.debug(f"RxNav interaction API error: {e}")
            return []

class USDAClient(APIClient):
    """Client for USDA Food Data Central API"""
    
    def search_foods(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for foods in USDA database"""
        url = f"{USDA_BASE_URL}foods/search"
        params = {
            'query': query,
            'pageSize': min(limit, 25),  # Keep it reasonable
            'dataType': ['Foundation', 'SR Legacy'],
            'sortBy': 'dataType.keyword',
            'sortOrder': 'asc'
        }
        
        # Add API key if available
        if USDA_API_KEY:
            params['api_key'] = USDA_API_KEY
        
        try:
            response = self._make_request(url, params)
            if response and 'foods' in response:
                logging.debug(f"USDA found {len(response['foods'])} results for {query}")
                return response['foods']
            else:
                logging.debug(f"No USDA results for {query}")
                return []
            
        except Exception as e:
            logging.debug(f"USDA API error for {query}: {e}")
            return []
    
    def get_food_details(self, fdc_id: str) -> Optional[Dict]:
        """Get detailed food information"""
        url = f"{USDA_BASE_URL}food/{fdc_id}"
        params = {}
        
        if USDA_API_KEY:
            params['api_key'] = USDA_API_KEY
        
        try:
            response = self._make_request(url, params)
            return response
            
        except Exception as e:
            logging.debug(f"USDA food details API error: {e}")
            return None

class OpenFoodFactsClient(APIClient):
    """Client for Open Food Facts API"""
    
    def search_foods(self, query: str, limit: int = 10) -> List[Dict]:
        """Search foods in Open Food Facts"""
        url = f"{OPENFOOD_BASE_URL}search.json"
        params = {
            'search_terms': query,
            'page_size': min(limit, 20),
            'json': 1,
            'fields': 'product_name,categories,nutrition_grades'
        }
        
        try:
            response = self._make_request(url, params)
            if response and 'products' in response:
                logging.debug(f"OpenFood found {len(response['products'])} results for {query}")
                return response['products']
            else:
                logging.debug(f"No OpenFood results for {query}")
                return []
            
        except Exception as e:
            logging.debug(f"Open Food Facts API error for {query}: {e}")
            return []

class APIManager:
    """Manages all API clients"""
    
    def __init__(self):
        self.fda_client = FDAClient()
        self.rxnav_client = RxNavClient()
        self.usda_client = USDAClient()
        self.openfood_client = OpenFoodFactsClient()
    
    def search_all_drugs(self, query: str) -> Dict[str, List[Dict]]:
        """Search all drug APIs with error handling"""
        results = {}
        
        # Try RxNav first (more reliable)
        try:
            results['rxnav'] = self.rxnav_client.search_drugs(query)
        except Exception as e:
            logging.debug(f"RxNav search failed for {query}: {e}")
            results['rxnav'] = []
        
        # Try FDA (often fails, so it's optional)
        try:
            results['fda'] = self.fda_client.search_drugs(query)
        except Exception as e:
            logging.debug(f"FDA search failed for {query}: {e}")
            results['fda'] = []
            
        return results
    
    def search_all_foods(self, query: str) -> Dict[str, List[Dict]]:
        """Search all food APIs with error handling"""
        results = {}
        
        # Try USDA first
        try:
            results['usda'] = self.usda_client.search_foods(query)
        except Exception as e:
            logging.debug(f"USDA search failed for {query}: {e}")
            results['usda'] = []
        
        # Try OpenFood Facts
        try:
            results['openfood'] = self.openfood_client.search_foods(query)
        except Exception as e:
            logging.debug(f"OpenFood search failed for {query}: {e}")
            results['openfood'] = []
            
        return results