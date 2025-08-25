import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from data.database import DatabaseManager
from utils.fuzzy_matcher import FuzzyMatcher
from utils.error_handler import ErrorHandler, GracefulDegradation

class Severity(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    AVOID = "avoid"

class InteractionType(Enum):
    ABSORPTION = "absorption"
    METABOLISM = "metabolism" 
    EFFECTIVENESS = "effectiveness"
    TOXICITY = "toxicity"
    TIMING = "timing"

@dataclass
class InteractionResult:
    """Represents a single interaction finding"""
    medication: str
    food: str
    severity: Severity
    interaction_type: InteractionType
    mechanism: str
    clinical_effect: str
    timing_recommendation: str
    confidence: float
    evidence_level: str
    source: str = "Database"

@dataclass
@dataclass
class AnalysisResults:
    """Complete analysis results"""
    interactions: List[InteractionResult]
    medications_analyzed: List[str]
    foods_analyzed: List[str]
    overall_risk_level: Severity
    summary: str
    recommendations: List[str]
    confidence_score: float
    analysis_timestamp: str
    ai_analysis: Optional['AIAnalysisResult'] = None  # NEW: Add AI analysis

from utils.ai_analyzer import AIAnalyzer, AIAnalysisResult

class InteractionEngine:
    def __init__(self, db_manager: DatabaseManager, fuzzy_matcher: FuzzyMatcher):
        self.db = db_manager
        self.fuzzy_matcher = fuzzy_matcher
        self.ai_analyzer = AIAnalyzer()  # NEW: Add AI analyzer

    def analyze_interactions(self, medications: List[str], foods: List[str]) -> AnalysisResults:
        """Main method to analyze interactions between medications and foods with error handling"""
        
        # Validate input
        is_valid, validation_msg = ErrorHandler.validate_user_input(medications, foods)
        if not is_valid:
            # Return minimal safe results for invalid input
            from datetime import datetime
            return AnalysisResults(
                interactions=[],
                medications_analyzed=medications,
                foods_analyzed=foods,
                overall_risk_level=Severity.SAFE,
                summary=f"Input validation failed: {validation_msg}",
                recommendations=["Please adjust your selections and try again."],
                confidence_score=0.0,
                analysis_timestamp=datetime.now().isoformat()
            )
        
        logging.info(f"Analyzing interactions for {len(medications)} medications and {len(foods)} foods")
        
        try:
            # Find direct interactions from database
            direct_interactions = ErrorHandler.safe_execute(
                lambda: self._find_direct_interactions(medications, foods),
                fallback_value=[],
                error_message="Database lookup encountered issues, continuing with available data"
            )
            
            # Find fuzzy matches for better coverage
            fuzzy_interactions = ErrorHandler.safe_execute(
                lambda: self._find_fuzzy_interactions(medications, foods),
                fallback_value=[],
                error_message="Fuzzy matching unavailable"
            )
            
            # Combine and deduplicate
            all_interactions = self._combine_interactions(direct_interactions or [], fuzzy_interactions or [])
            
            # Calculate overall risk
            overall_risk = self._calculate_overall_risk(all_interactions)
            
            # Generate summary and recommendations
            summary = self._generate_summary(all_interactions, medications, foods)
            recommendations = self._generate_recommendations(all_interactions)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(all_interactions, medications, foods)
            
            # AI analysis with fallback
            ai_analysis = None
            try:
                interaction_dicts = []
                for interaction in all_interactions:
                    interaction_dicts.append({
                        'medication_name': interaction.medication,
                        'food_name': interaction.food,
                        'severity': interaction.severity.value,
                        'mechanism': interaction.mechanism,
                        'clinical_effect': interaction.clinical_effect,
                        'timing_recommendation': interaction.timing_recommendation
                    })
                
                ai_result = self.ai_analyzer.analyze_interactions(medications, foods, interaction_dicts)
                
                if ai_result:
                    summary = f"{ai_result.enhanced_summary}\n\n{summary}"
                    ai_advice = self.ai_analyzer.get_personalized_advice(interaction_dicts)
                    recommendations.extend(ai_advice)
                    ai_analysis = ai_result
                else:
                    # Fallback AI analysis
                    fallback_ai = GracefulDegradation.minimal_ai_analysis(interaction_dicts)
                    summary = f"{fallback_ai['summary']}\n\n{summary}"
                    recommendations.extend(fallback_ai['warnings'])
                    
            except Exception as e:
                logging.warning(f"AI analysis failed: {e}")
                st.info("Advanced AI analysis temporarily unavailable. Basic analysis provided.")
            
            from datetime import datetime
            results = AnalysisResults(
                interactions=all_interactions,
                medications_analyzed=medications,
                foods_analyzed=foods,
                overall_risk_level=overall_risk,
                summary=summary,
                recommendations=recommendations,
                confidence_score=confidence,
                analysis_timestamp=datetime.now().isoformat()
            )
            
            results.ai_analysis = ai_analysis
            return results
            
        except Exception as e:
            logging.error(f"Critical error in interaction analysis: {e}")
            # Return fallback analysis
            fallback_results = GracefulDegradation.fallback_interaction_analysis(medications, foods)
            
            from datetime import datetime
            return AnalysisResults(
                interactions=[],
                medications_analyzed=medications,
                foods_analyzed=foods,
                overall_risk_level=Severity.CAUTION,
                summary=fallback_results['summary'],
                recommendations=fallback_results['recommendations'],
                confidence_score=fallback_results['confidence'],
                analysis_timestamp=datetime.now().isoformat()
            )
    
    def _find_direct_interactions(self, medications: List[str], foods: List[str]) -> List[InteractionResult]:
        """Find interactions using exact database matches"""
        interactions = []
        
        # Get interactions from database
        db_interactions = self.db.find_interactions(medications, foods)
        
        for interaction in db_interactions:
            result = InteractionResult(
                medication=interaction['medication_name'],
                food=interaction['food_name'],
                severity=Severity(interaction['severity']),
                interaction_type=InteractionType(interaction.get('interaction_type', 'effectiveness')),
                mechanism=interaction.get('mechanism', 'Unknown mechanism'),
                clinical_effect=interaction.get('clinical_effect', 'See mechanism'),
                timing_recommendation=interaction.get('timing_recommendation', 'Consult healthcare provider'),
                confidence=0.95,  # High confidence for database matches
                evidence_level=interaction.get('evidence_level', 'established'),
                source=interaction.get('source', 'Medical database')
            )
            interactions.append(result)
        
        return interactions
    
    def _find_fuzzy_interactions(self, medications: List[str], foods: List[str]) -> List[InteractionResult]:
        """Find interactions using fuzzy matching for broader coverage"""
        interactions = []
        
        # Get all known interactions
        all_known_meds = set()
        all_known_foods = set()
        
        # This is a simplified approach - in a real system you'd query all unique values
        # For now, we'll skip fuzzy matching to keep it simple
        # You can enhance this later
        
        return interactions
    
    def _combine_interactions(self, direct: List[InteractionResult], 
                            fuzzy: List[InteractionResult]) -> List[InteractionResult]:
        """Combine and deduplicate interaction results"""
        all_interactions = direct + fuzzy
        
        # Remove duplicates based on medication-food pairs
        seen = set()
        unique_interactions = []
        
        for interaction in all_interactions:
            key = (interaction.medication, interaction.food)
            if key not in seen:
                seen.add(key)
                unique_interactions.append(interaction)
        
        # Sort by severity (most severe first)
        severity_order = {Severity.AVOID: 0, Severity.CAUTION: 1, Severity.SAFE: 2}
        unique_interactions.sort(key=lambda x: severity_order[x.severity])
        
        return unique_interactions
    
    def _calculate_overall_risk(self, interactions: List[InteractionResult]) -> Severity:
        """Calculate overall risk level based on all interactions"""
        if not interactions:
            return Severity.SAFE
        
        # If any interaction is "avoid", overall risk is "avoid"
        if any(i.severity == Severity.AVOID for i in interactions):
            return Severity.AVOID
        
        # If any interaction is "caution", overall risk is "caution"
        if any(i.severity == Severity.CAUTION for i in interactions):
            return Severity.CAUTION
        
        return Severity.SAFE
    
    def _generate_summary(self, interactions: List[InteractionResult], 
                         medications: List[str], foods: List[str]) -> str:
        """Generate a human-readable summary"""
        if not interactions:
            return f"No significant interactions found between {len(medications)} medications and {len(foods)} foods."
        
        avoid_count = sum(1 for i in interactions if i.severity == Severity.AVOID)
        caution_count = sum(1 for i in interactions if i.severity == Severity.CAUTION)
        safe_count = sum(1 for i in interactions if i.severity == Severity.SAFE)
        
        summary_parts = []
        
        if avoid_count > 0:
            summary_parts.append(f"{avoid_count} serious interaction(s) to avoid")
        
        if caution_count > 0:
            summary_parts.append(f"{caution_count} interaction(s) requiring caution")
        
        if safe_count > 0:
            summary_parts.append(f"{safe_count} low-risk interaction(s)")
        
        summary = f"Found {len(interactions)} interaction(s): " + ", ".join(summary_parts) + "."
        
        return summary
    
    def _generate_recommendations(self, interactions: List[InteractionResult]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if not interactions:
            recommendations.append("No specific precautions needed based on known interactions.")
            recommendations.append("Always consult your healthcare provider about medication and diet interactions.")
            return recommendations
        
        # Group by severity
        avoid_interactions = [i for i in interactions if i.severity == Severity.AVOID]
        caution_interactions = [i for i in interactions if i.severity == Severity.CAUTION]
        
        if avoid_interactions:
            recommendations.append("**Serious Interactions - Action Required:**")
            for interaction in avoid_interactions[:3]:  # Limit to top 3
                recommendations.append(f"   • Avoid {interaction.food} while taking {interaction.medication}")
        
        if caution_interactions:
            recommendations.append("**Interactions Requiring Caution:**")
            for interaction in caution_interactions[:3]:  # Limit to top 3
                if interaction.timing_recommendation:
                    recommendations.append(f"   • {interaction.timing_recommendation}")
                else:
                    recommendations.append(f"   • Monitor {interaction.medication} + {interaction.food} combination")
        
        recommendations.append("**Always consult your healthcare provider** before making changes to medications or diet.")
        
        return recommendations
    
    def _calculate_confidence(self, interactions: List[InteractionResult], 
                            medications: List[str], foods: List[str]) -> float:
        """Calculate confidence score for the analysis"""
        if not interactions:
            return 0.8  # Moderate confidence when no interactions found
        
        # Base confidence on evidence levels and number of interactions
        total_confidence = 0
        for interaction in interactions:
            if interaction.evidence_level == "established":
                total_confidence += 0.95
            elif interaction.evidence_level == "probable":
                total_confidence += 0.8
            else:
                total_confidence += 0.6
        
        average_confidence = total_confidence / len(interactions) if interactions else 0.8
        
        # Adjust based on coverage (how many items we found interactions for)
        total_items = len(medications) + len(foods)
        coverage = len(set(i.medication for i in interactions) | 
                      set(i.food for i in interactions)) / total_items if total_items > 0 else 0
        
        # Weighted confidence score
        final_confidence = (average_confidence * 0.7) + (coverage * 0.3)
        
        return min(final_confidence, 1.0)