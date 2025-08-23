from rapidfuzz import fuzz, process
from typing import List, Dict, Tuple, Optional
import logging
import re

class FuzzyMatcher:
    def __init__(self, match_threshold: int = 80):
        self.match_threshold = match_threshold
        
        # Common medication/food name transformations
        self.common_typos = {
            'ph': 'f',  # ibuprofen -> ibuprofin
            'tion': 'shun',  # action -> akshun
            'que': 'k',  # technique -> teknik
            'ough': 'uff',  # rough -> ruff
        }
        
        # Common endings that are often misspelled
        self.common_endings = {
            'in': 'en',  # ibuprofin -> ibuprofen
            'ine': 'een',
            'an': 'en',
        }
        
    def clean_string(self, text: str) -> str:
        """Clean and normalize string for better matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove dosage information and common medical suffixes
        text = re.sub(r'\s+\d+(\.\d+)?\s*(mg|ml|g|mcg|units?)\b', '', text)
        text = re.sub(r'\s+(tablet|capsule|pills?|caps?|oral|injection)\b', '', text)
        text = re.sub(r'\s+\[.*?\]', '', text)  # Remove bracketed brand names
        text = re.sub(r'^(generic|brand)\s+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep letters, numbers, spaces, hyphens
        text = re.sub(r'[^\w\s\-]', '', text)
        
        return text.strip()
    
    def generate_typo_variations(self, text: str) -> List[str]:
        """Generate common typo variations"""
        variations = []
        
        # Apply common typo patterns
        for wrong, right in self.common_typos.items():
            if wrong in text:
                variations.append(text.replace(wrong, right))
            if right in text:
                variations.append(text.replace(right, wrong))
        
        # Apply common ending variations
        for wrong, right in self.common_endings.items():
            if text.endswith(wrong):
                variations.append(text[:-len(wrong)] + right)
            if text.endswith(right):
                variations.append(text[:-len(right)] + wrong)
        
        return variations
    
    def generate_variations(self, text: str) -> List[str]:
        """Generate comprehensive variations of a text"""
        if not text:
            return []
            
        variations = [text]
        cleaned = self.clean_string(text)
        
        if cleaned != text:
            variations.append(cleaned)
        
        # Add typo variations
        typo_vars = self.generate_typo_variations(text)
        variations.extend(typo_vars)
        
        # Add typo variations for cleaned text too
        if cleaned != text:
            cleaned_typo_vars = self.generate_typo_variations(cleaned)
            variations.extend(cleaned_typo_vars)
        
        # Add plural/singular variations
        if text.endswith('s') and len(text) > 3:
            variations.append(text[:-1])  # Remove 's'
        elif not text.endswith('s'):
            variations.append(text + 's')  # Add 's'
        
        # Add variations with/without hyphens
        if '-' in text:
            variations.append(text.replace('-', ' '))
            variations.append(text.replace('-', ''))
        
        # Add variations with/without spaces
        if ' ' in text:
            variations.append(text.replace(' ', ''))
            variations.append(text.replace(' ', '-'))
        
        return list(set(variations))  # Remove duplicates
    
    def calculate_enhanced_score(self, query: str, candidate: str) -> float:
        """Calculate enhanced similarity score with typo-awareness"""
        
        # Start with basic scores
        ratio_score = fuzz.ratio(query, candidate)
        partial_score = fuzz.partial_ratio(query, candidate)
        token_sort_score = fuzz.token_sort_ratio(query, candidate)
        token_set_score = fuzz.token_set_ratio(query, candidate)
        
        # Calculate weighted average
        base_score = (ratio_score * 0.4 + partial_score * 0.2 + 
                     token_sort_score * 0.2 + token_set_score * 0.2)
        
        # Boost score for common typo patterns
        query_clean = self.clean_string(query.lower())
        candidate_clean = self.clean_string(candidate.lower())
        
        # Check for common medication typo: "in" ending vs "en" ending
        if (query_clean.endswith('in') and candidate_clean.endswith('en') and 
            query_clean[:-2] == candidate_clean[:-2]):
            base_score = min(100, base_score + 15)  # Boost for ibuprofin -> ibuprofen
        
        # Check for ph/f substitution
        if ('ph' in candidate_clean and 'f' in query_clean and 
            candidate_clean.replace('ph', 'f') == query_clean):
            base_score = min(100, base_score + 10)
        
        # Check for single character differences
        if abs(len(query_clean) - len(candidate_clean)) <= 1:
            # Count character differences
            max_len = max(len(query_clean), len(candidate_clean))
            if max_len > 0:
                diff_count = sum(1 for i in range(max_len) 
                               if i >= len(query_clean) or i >= len(candidate_clean) or 
                               query_clean[i] != candidate_clean[i])
                
                if diff_count <= 2:  # Very similar
                    base_score = min(100, base_score + 10)
        
        return base_score
    
    def find_best_matches(self, query: str, candidates: List[str], 
                         limit: int = 5, score_cutoff: int = None) -> List[Tuple[str, float]]:
        """Find best matching strings from candidates with enhanced scoring"""
        if not query or not candidates:
            return []

        if score_cutoff is None:
            score_cutoff = max(50, self.match_threshold - 30)  # More lenient threshold
        
        try:
            # Generate query variations
            query_variations = self.generate_variations(query)
            
            # Find matches using multiple approaches
            all_matches = []
            
            # Approach 1: Standard rapidfuzz matching
            for query_var in query_variations:
                if not query_var:
                    continue
                    
                matches = process.extract(
                    query_var, 
                    candidates, 
                    scorer=fuzz.WRatio,
                    limit=limit * 3,
                    score_cutoff=score_cutoff
                )
                
                for match_result in matches:
                    if len(match_result) >= 2:
                        match_text = match_result[0]
                        match_score = match_result[1]
                        all_matches.append((match_text, float(match_score)))
            
            # Approach 2: Enhanced scoring for all candidates
            for candidate in candidates:
                enhanced_score = self.calculate_enhanced_score(query, candidate)
                if enhanced_score >= score_cutoff:
                    all_matches.append((candidate, enhanced_score))
            
            # Remove duplicates and keep best scores
            unique_matches = {}
            for match, score in all_matches:
                if match not in unique_matches or score > unique_matches[match]:
                    unique_matches[match] = score
            
            # Convert back to list and sort
            final_matches = [(match, score) for match, score in unique_matches.items()]
            final_matches.sort(key=lambda x: x[1], reverse=True)
            
            return final_matches[:limit]
            
        except Exception as e:
            logging.error(f"Error in fuzzy matching: {e}")
            return self._simple_string_match(query, candidates, limit)
    
    def _simple_string_match(self, query: str, candidates: List[str], limit: int) -> List[Tuple[str, float]]:
        """Fallback simple string matching"""
        matches = []
        query_lower = query.lower()
        
        for candidate in candidates:
            candidate_lower = candidate.lower()
            
            # Exact match
            if query_lower == candidate_lower:
                matches.append((candidate, 100.0))
            # Very close match (one character difference)
            elif len(query_lower) == len(candidate_lower):
                diff_count = sum(1 for a, b in zip(query_lower, candidate_lower) if a != b)
                if diff_count == 1:
                    matches.append((candidate, 95.0))
                elif diff_count == 2:
                    matches.append((candidate, 85.0))
            # Starts with
            elif candidate_lower.startswith(query_lower):
                matches.append((candidate, 90.0))
            # Contains
            elif query_lower in candidate_lower:
                matches.append((candidate, 80.0))
            # Reverse contains (query contains candidate)
            elif candidate_lower in query_lower:
                matches.append((candidate, 70.0))
        
        # Sort by score and return top matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]
    
    def find_matches_in_data(self, query: str, data_list: List[Dict], 
                           name_field: str = 'name', include_aliases: bool = True,
                           limit: int = 5) -> List[Dict]:
        """Find matches in a list of dictionaries with names and aliases"""
        if not query or not data_list:
            return []
        
        try:
            # Collect all searchable names
            search_candidates = {}  # name -> original_data_item
            
            for item in data_list:
                name = item.get(name_field, '')
                if name:
                    search_candidates[name] = item
                    
                    # Add aliases if available and requested
                    if include_aliases:
                        aliases = item.get('aliases', []) or item.get('brand_names', [])
                        if aliases:
                            for alias in aliases:
                                if alias and alias not in search_candidates:
                                    search_candidates[alias] = item
            
            # Find best matches
            candidate_names = list(search_candidates.keys())
            matches = self.find_best_matches(query, candidate_names, limit)
            
            # Convert back to data items
            result_items = []
            seen_items = set()
            
            for match_name, score in matches:
                item = search_candidates[match_name]
                item_id = id(item)  # Use object id to avoid duplicates
                
                if item_id not in seen_items:
                    # Add match score to item
                    result_item = item.copy()
                    result_item['match_score'] = score
                    result_item['matched_name'] = match_name
                    result_items.append(result_item)
                    seen_items.add(item_id)
            
            return result_items
            
        except Exception as e:
            logging.error(f"Error in find_matches_in_data: {e}")
            return []
    
    def is_good_match(self, query: str, candidate: str) -> bool:
        """Check if a candidate is a good match for the query"""
        try:
            score = self.calculate_enhanced_score(query, candidate)
            return score >= self.match_threshold
        except:
            # Fallback to simple comparison
            return query.lower() in candidate.lower() or candidate.lower() in query.lower()
    
    def get_suggestions(self, query: str, candidates: List[str], 
                       max_suggestions: int = 5) -> List[str]:
        """Get suggestions for misspelled or partial queries"""
        try:
            matches = self.find_best_matches(
                query, 
                candidates, 
                limit=max_suggestions,
                score_cutoff=40  # Even more lenient for suggestions
            )
            
            return [match[0] for match in matches]
        except Exception as e:
            logging.error(f"Error getting suggestions: {e}")
            return []