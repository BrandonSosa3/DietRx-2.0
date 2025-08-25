import requests
import logging
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
import re
from data.database import DatabaseManager

class FDAInteractionFetcher:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.base_url = "https://api.fda.gov/drug/label.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DietRx-Enhanced/1.0 (Educational Research Tool)'
        })
        
        # Rate limiting (FDA allows 240 requests per minute for non-authenticated users)
        self.rate_limit_delay = 0.25  # 250ms between requests
        self.last_request_time = 0
        
    def fetch_drug_food_interactions(self, limit: int = 100) -> List[Dict]:
        """Fetch drug-food interactions from FDA OpenFDA API"""
        
        interactions = []
        
        try:
            # Search for drug labels mentioning food interactions
            search_terms = [
                'drug_interactions:food',
                'food_effect_clinical_pharmacology:*',
                'dosage_and_administration:*food*',
                'contraindications:*food*',
                'warnings:*food*'
            ]
            
            for search_term in search_terms:
                logging.info(f"Searching FDA API with term: {search_term}")
                
                params = {
                    'search': search_term,
                    'limit': min(limit, 100),  # FDA max is 100 per request
                    'skip': 0
                }
                
                batch_interactions = self._fetch_batch(params)
                interactions.extend(batch_interactions)
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
                logging.info(f"Found {len(batch_interactions)} interactions for search: {search_term}")
            
            # Remove duplicates
            unique_interactions = self._deduplicate_interactions(interactions)
            
            logging.info(f"Total unique FDA interactions fetched: {len(unique_interactions)}")
            return unique_interactions
            
        except Exception as e:
            logging.error(f"Error fetching FDA interactions: {e}")
            return []
    
    def _fetch_batch(self, params: Dict) -> List[Dict]:
        """Fetch a batch of results from FDA API"""
        
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - time_since_last)
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                
                if 'results' in data:
                    return self._parse_fda_results(data['results'])
                else:
                    logging.warning("No results found in FDA API response")
                    return []
                    
            elif response.status_code == 429:
                logging.warning("FDA API rate limit hit, waiting...")
                time.sleep(60)  # Wait 1 minute
                return []
                
            else:
                logging.error(f"FDA API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"FDA API request error: {e}")
            return []
    
    def _parse_fda_results(self, results: List[Dict]) -> List[Dict]:
        """Parse FDA API results into interaction format"""
        
        interactions = []
        
        for result in results:
            try:
                # Extract drug name
                drug_name = self._extract_drug_name(result)
                if not drug_name:
                    continue
                
                # Look for food interaction information in various fields
                food_interactions = []
                
                # Check drug_interactions field
                if 'drug_interactions' in result:
                    food_interactions.extend(self._extract_food_interactions_from_text(
                        result['drug_interactions'], drug_name
                    ))
                
                # Check food_effect_clinical_pharmacology field
                if 'food_effect_clinical_pharmacology' in result:
                    food_interactions.extend(self._extract_food_effects(
                        result['food_effect_clinical_pharmacology'], drug_name
                    ))
                
                # Check dosage_and_administration for food instructions
                if 'dosage_and_administration' in result:
                    food_interactions.extend(self._extract_dosage_food_info(
                        result['dosage_and_administration'], drug_name
                    ))
                
                # Check warnings for food-related warnings
                if 'warnings' in result:
                    food_interactions.extend(self._extract_warning_food_info(
                        result['warnings'], drug_name
                    ))
                
                interactions.extend(food_interactions)
                
            except Exception as e:
                logging.warning(f"Error parsing FDA result: {e}")
                continue
        
        return interactions
    
    def _extract_drug_name(self, result: Dict) -> Optional[str]:
        """Extract drug name from FDA result"""
        
        # Try different fields for drug name
        name_fields = ['openfda.brand_name', 'openfda.generic_name', 'active_ingredient']
        
        for field in name_fields:
            try:
                if '.' in field:
                    # Handle nested fields like 'openfda.brand_name'
                    parts = field.split('.')
                    value = result
                    for part in parts:
                        if part in value:
                            value = value[part]
                        else:
                            value = None
                            break
                else:
                    value = result.get(field)
                
                if value:
                    if isinstance(value, list):
                        return value[0].strip()
                    return str(value).strip()
                    
            except Exception:
                continue
        
        return None
    
    def _extract_food_interactions_from_text(self, drug_interactions: List[str], drug_name: str) -> List[Dict]:
        """Extract food interactions from drug_interactions field"""
        
        interactions = []
        food_keywords = [
            'food', 'meal', 'dairy', 'milk', 'grapefruit', 'alcohol', 'caffeine',
            'vitamin K', 'calcium', 'iron', 'antacid', 'juice', 'coffee', 'tea'
        ]
        
        for text in drug_interactions:
            text_lower = text.lower()
            
            # Look for food-related interactions
            for food_keyword in food_keywords:
                if food_keyword in text_lower:
                    interaction = self._create_interaction_from_text(
                        drug_name, food_keyword, text, 'drug_interactions'
                    )
                    if interaction:
                        interactions.append(interaction)
        
        return interactions
    
    def _extract_food_effects(self, food_effects: List[str], drug_name: str) -> List[Dict]:
        """Extract interactions from food_effect_clinical_pharmacology field"""
        
        interactions = []
        
        for text in food_effects:
            # These are specifically about food effects, so create interactions
            foods_mentioned = self._identify_foods_in_text(text)
            
            for food in foods_mentioned:
                interaction = self._create_interaction_from_text(
                    drug_name, food, text, 'food_effect_clinical_pharmacology'
                )
                if interaction:
                    interactions.append(interaction)
        
        return interactions
    
    def _extract_dosage_food_info(self, dosage_info: List[str], drug_name: str) -> List[Dict]:
        """Extract food-related dosage information"""
        
        interactions = []
        
        for text in dosage_info:
            text_lower = text.lower()
            
            if any(keyword in text_lower for keyword in ['food', 'meal', 'empty stomach']):
                foods_mentioned = self._identify_foods_in_text(text)
                
                if not foods_mentioned:
                    foods_mentioned = ['food']  # Generic food interaction
                
                for food in foods_mentioned:
                    interaction = self._create_interaction_from_text(
                        drug_name, food, text, 'dosage_administration'
                    )
                    if interaction:
                        interactions.append(interaction)
        
        return interactions
    
    def _extract_warning_food_info(self, warnings: List[str], drug_name: str) -> List[Dict]:
        """Extract food-related warnings"""
        
        interactions = []
        
        for text in warnings:
            text_lower = text.lower()
            
            food_warning_keywords = ['food', 'alcohol', 'grapefruit', 'dairy', 'vitamin k']
            
            if any(keyword in text_lower for keyword in food_warning_keywords):
                foods_mentioned = self._identify_foods_in_text(text)
                
                for food in foods_mentioned:
                    interaction = self._create_interaction_from_text(
                        drug_name, food, text, 'warnings', severity='avoid'
                    )
                    if interaction:
                        interactions.append(interaction)
        
        return interactions
    
    def _identify_foods_in_text(self, text: str) -> List[str]:
        """Identify specific foods mentioned in text"""
        
        foods = []
        text_lower = text.lower()
        
        # Common foods that interact with medications
        food_patterns = {
            'grapefruit': ['grapefruit', 'grapefruit juice'],
            'alcohol': ['alcohol', 'alcoholic beverages', 'ethanol'],
            'dairy': ['dairy', 'milk', 'cheese', 'yogurt'],
            'vitamin k foods': ['vitamin k', 'leafy greens', 'spinach', 'kale'],
            'calcium': ['calcium', 'calcium-rich'],
            'caffeine': ['caffeine', 'coffee', 'tea'],
            'iron': ['iron', 'iron supplements'],
            'high fat foods': ['high fat', 'fatty foods', 'fat'],
            'antacids': ['antacid', 'antacids'],
            'citrus': ['citrus', 'orange juice', 'lemon'],
        }
        
        for food_name, patterns in food_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                foods.append(food_name)
        
        # If no specific foods found but "food" is mentioned, add generic food
        if not foods and 'food' in text_lower:
            foods.append('food')
        
        return foods
    
    def _create_interaction_from_text(self, drug_name: str, food: str, text: str, source: str, severity: str = None) -> Optional[Dict]:
        """Create interaction dictionary from parsed text"""
        
        try:
            # Determine severity from text content
            if not severity:
                text_lower = text.lower()
                
                if any(word in text_lower for word in ['avoid', 'contraindicated', 'should not', 'do not']):
                    severity = 'avoid'
                elif any(word in text_lower for word in ['caution', 'monitor', 'may', 'consider']):
                    severity = 'caution'
                else:
                    severity = 'safe'
            
            # Extract mechanism and effects from text
            mechanism = self._extract_mechanism(text)
            clinical_effect = self._extract_clinical_effect(text)
            timing = self._extract_timing_recommendation(text)
            
            interaction = {
                'medication_name': drug_name,
                'food_name': food,
                'severity': severity,
                'mechanism': mechanism,
                'clinical_effect': clinical_effect,
                'timing_recommendation': timing,
                'evidence_level': 'established',  # FDA data is well-established
                'interaction_type': 'pharmacokinetic',  # Default assumption
                'source': f'FDA OpenFDA - {source}',
                'original_text': text[:500],  # Store original text (truncated)
                'date_added': datetime.now().isoformat()
            }
            
            return interaction
            
        except Exception as e:
            logging.warning(f"Error creating interaction: {e}")
            return None
    
    def _extract_mechanism(self, text: str) -> str:
        """Extract interaction mechanism from text"""
        
        # Look for common mechanism keywords
        mechanism_patterns = {
            'absorption': 'affects drug absorption',
            'cyp3a4': 'CYP3A4 enzyme inhibition/induction',
            'protein binding': 'affects protein binding',
            'metabolism': 'affects drug metabolism',
            'bioavailability': 'affects drug bioavailability',
            'vitamin k': 'vitamin K antagonism',
            'calcium': 'calcium binding/chelation',
            'ph': 'affects gastric pH',
        }
        
        text_lower = text.lower()
        
        for pattern, mechanism in mechanism_patterns.items():
            if pattern in text_lower:
                return mechanism
        
        # Default mechanism
        return "Food may affect drug pharmacokinetics"
    
    def _extract_clinical_effect(self, text: str) -> str:
        """Extract clinical effect from text"""
        
        # Look for effect descriptions
        if 'increase' in text.lower():
            return "May increase drug levels or effects"
        elif 'decrease' in text.lower() or 'reduce' in text.lower():
            return "May decrease drug levels or effectiveness"
        elif 'delay' in text.lower():
            return "May delay drug absorption"
        elif 'enhance' in text.lower():
            return "May enhance drug effects"
        else:
            return "May affect drug absorption, distribution, metabolism, or excretion"
    
    def _extract_timing_recommendation(self, text: str) -> str:
        """Extract timing recommendation from text"""
        
        text_lower = text.lower()
        
        if 'empty stomach' in text_lower:
            return "Take on empty stomach (1 hour before or 2 hours after meals)"
        elif 'with food' in text_lower:
            return "Take with food to reduce stomach irritation"
        elif 'avoid' in text_lower:
            return "Avoid this food while taking medication"
        elif 'separate' in text_lower:
            return "Separate medication and food by 2-4 hours"
        else:
            return "Follow standard dosing instructions"
    
    def _deduplicate_interactions(self, interactions: List[Dict]) -> List[Dict]:
        """Remove duplicate interactions"""
        
        seen = set()
        unique_interactions = []
        
        for interaction in interactions:
            # Create a key for deduplication
            key = (
                interaction['medication_name'].lower().strip(),
                interaction['food_name'].lower().strip(),
                interaction['severity']
            )
            
            if key not in seen:
                seen.add(key)
                unique_interactions.append(interaction)
        
        return unique_interactions
    
    def store_fda_interactions(self, interactions: List[Dict]) -> int:
        """Store FDA interactions in database"""
        
        if not interactions:
            return 0
        
        stored_count = 0
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            for interaction in interactions:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO known_interactions 
                        (medication_name, food_name, severity, mechanism, clinical_effect, 
                         timing_recommendation, evidence_level, interaction_type, source, date_added)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        interaction['medication_name'],
                        interaction['food_name'],
                        interaction['severity'],
                        interaction['mechanism'],
                        interaction['clinical_effect'],
                        interaction['timing_recommendation'],
                        interaction['evidence_level'],
                        interaction['interaction_type'],
                        interaction['source'],
                        interaction['date_added']
                    ))
                    
                    stored_count += 1
                    
                except Exception as e:
                    logging.warning(f"Error storing interaction: {e}")
                    continue
            
            conn.commit()
            
        except Exception as e:
            logging.error(f"Database error storing FDA interactions: {e}")
            conn.rollback()
        
        finally:
            conn.close()
        
        logging.info(f"Stored {stored_count} FDA interactions in database")
        return stored_count
    
    def fetch_and_store_all(self, limit: int = 500) -> Dict[str, int]:
        """Fetch and store all FDA interactions"""
        
        logging.info("Starting FDA interaction fetch and store process...")
        
        # Fetch interactions
        interactions = self.fetch_drug_food_interactions(limit)
        
        # Store in database
        stored_count = self.store_fda_interactions(interactions)
        
        result = {
            'fetched': len(interactions),
            'stored': stored_count,
            'duplicates_removed': len(interactions) - stored_count
        }
        
        logging.info(f"FDA fetch complete: {result}")
        return result