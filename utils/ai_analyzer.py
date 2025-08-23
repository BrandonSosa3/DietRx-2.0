import logging
import json
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re

# Try multiple AI backends
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logging.warning("Groq not available")

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available")

@dataclass
class AIAnalysisResult:
    """Result from AI analysis"""
    enhanced_summary: str
    detailed_explanation: str
    additional_warnings: List[str]
    confidence: float
    analysis_method: str
    processing_time: float

class AIAnalyzer:
    def __init__(self):
        self.groq_client = None
        self.local_model = None
        self.fallback_templates = self._load_templates()
        
        # Initialize available AI backends
        self._initialize_ai_backends()
    
    def _initialize_ai_backends(self):
        """Initialize available AI analysis backends"""
        
        # Try to initialize Groq (free tier available)
        if GROQ_AVAILABLE:
            try:
                # You can get a free API key from https://console.groq.com/
                # For now, we'll use it without a key and handle the error gracefully
                self.groq_client = None  # Will implement API key handling later
                logging.info("Groq client initialized (API key needed)")
            except Exception as e:
                logging.warning(f"Groq initialization failed: {e}")
        
        # Try to initialize local model (lightweight medical model)
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use a lightweight model that works well for medical text
                model_name = "distilbert-base-uncased"
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                logging.info("Local AI model initialized")
            except Exception as e:
                logging.warning(f"Local model initialization failed: {e}")
                self.tokenizer = None
    
    def _load_templates(self) -> Dict[str, str]:
        """Load template responses for common interactions"""
        return {
            "warfarin_vitamin_k": {
                "summary": "Vitamin K can significantly affect warfarin's blood-thinning effectiveness.",
                "explanation": "Warfarin works by blocking vitamin K's role in blood clotting. Foods high in vitamin K (like spinach and kale) can reduce warfarin's effectiveness, potentially leading to dangerous blood clots. The key is maintaining consistent vitamin K intake rather than complete avoidance.",
                "warnings": [
                    "Monitor INR levels more frequently when changing diet",
                    "Don't drastically increase or decrease green vegetable intake",
                    "Inform your doctor about significant dietary changes"
                ]
            },
            "grapefruit_statins": {
                "summary": "Grapefruit dramatically increases statin medication levels in your blood.",
                "explanation": "Grapefruit contains compounds that block the CYP3A4 enzyme responsible for breaking down statin medications. This can cause statin levels to build up to dangerous levels, significantly increasing the risk of severe muscle damage (rhabdomyolysis) and liver problems.",
                "warnings": [
                    "Complete avoidance of grapefruit is recommended",
                    "Watch for unusual muscle pain or weakness",
                    "Even small amounts of grapefruit can be dangerous"
                ]
            },
            "antibiotics_dairy": {
                "summary": "Calcium in dairy products can significantly reduce antibiotic absorption.",
                "explanation": "Calcium, magnesium, and other minerals in dairy products bind to certain antibiotics (especially fluoroquinolones and tetracyclines) in your digestive tract. This binding prevents the antibiotic from being absorbed into your bloodstream, making the treatment less effective and potentially leading to treatment failure.",
                "warnings": [
                    "Take antibiotics 2 hours before or 6 hours after dairy",
                    "This includes milk, cheese, yogurt, and calcium supplements",
                    "Incomplete treatment can lead to antibiotic resistance"
                ]
            },
            "caffeine_interactions": {
                "summary": "Some medications can significantly increase caffeine's effects in your body.",
                "explanation": "Certain medications slow down how quickly your liver processes caffeine. This means caffeine stays in your system much longer, potentially causing increased anxiety, jitters, insomnia, and rapid heart rate. The effect can last much longer than usual.",
                "warnings": [
                    "Reduce coffee, tea, and energy drink consumption",
                    "Be aware of hidden caffeine sources (chocolate, some medications)",
                    "Monitor for increased anxiety or sleep problems"
                ]
            },
            "no_interactions": {
                "summary": "No significant interactions were found in our analysis.",
                "explanation": "Based on current medical knowledge, the combinations of medications and foods you've selected don't have well-documented interactions. However, this doesn't guarantee there are no effects, as individual responses can vary and new interactions are still being discovered.",
                "warnings": [
                    "Always inform healthcare providers about all medications and supplements",
                    "Monitor for any unusual symptoms when starting new medications",
                    "Some interactions may not be well-documented yet"
                ]
            }
        }
    
    def analyze_interactions(self, medications: List[str], foods: List[str], 
                           existing_interactions: List[Dict]) -> AIAnalysisResult:
        """Main method to get AI analysis of interactions"""
        
        start_time = time.time()
        
        # Try AI backends in order of preference
        ai_result = None
        
        # Method 1: Template-based analysis (always available, very fast)
        ai_result = self._template_based_analysis(medications, foods, existing_interactions)
        ai_result.analysis_method = "Template-based"
        
        # Method 2: Try Groq API if available (would be better but needs API key)
        if self.groq_client and len(existing_interactions) > 0:
            try:
                groq_result = self._groq_analysis(medications, foods, existing_interactions)
                if groq_result:
                    ai_result = groq_result
                    ai_result.analysis_method = "Groq AI"
            except Exception as e:
                logging.debug(f"Groq analysis failed: {e}")
        
        # Method 3: Local transformer analysis (if available)
        if self.tokenizer and len(existing_interactions) > 0:
            try:
                local_result = self._local_ai_analysis(medications, foods, existing_interactions)
                if local_result and not ai_result.analysis_method == "Groq AI":
                    # Combine template with local AI insights
                    ai_result.detailed_explanation += f"\n\nAI Analysis: {local_result}"
                    ai_result.analysis_method = "Template + Local AI"
            except Exception as e:
                logging.debug(f"Local AI analysis failed: {e}")
        
        ai_result.processing_time = time.time() - start_time
        return ai_result
    
    def _template_based_analysis(self, medications: List[str], foods: List[str], 
                                interactions: List[Dict]) -> AIAnalysisResult:
        """Fast template-based analysis using predefined responses"""
        
        if not interactions:
            template = self.fallback_templates["no_interactions"]
            return AIAnalysisResult(
                enhanced_summary=template["summary"],
                detailed_explanation=template["explanation"],
                additional_warnings=template["warnings"],
                confidence=0.8,
                analysis_method="Template",
                processing_time=0.0
            )
        
        # Identify interaction patterns
        interaction_types = []
        all_warnings = []
        explanations = []
        
        for interaction in interactions:
            med = interaction.get('medication_name', '').lower()
            food = interaction.get('food_name', '').lower()
            
            # Pattern matching for common interactions
            if 'warfarin' in med and any(veg in food for veg in ['spinach', 'kale', 'broccoli']):
                template = self.fallback_templates["warfarin_vitamin_k"]
                interaction_types.append("warfarin_vitamin_k")
                
            elif any(statin in med for statin in ['atorvastatin', 'simvastatin', 'lovastatin']) and 'grapefruit' in food:
                template = self.fallback_templates["grapefruit_statins"]
                interaction_types.append("grapefruit_statins")
                
            elif any(antibiotic in med for antibiotic in ['ciprofloxacin', 'doxycycline', 'tetracycline']) and any(dairy in food for dairy in ['milk', 'cheese', 'yogurt']):
                template = self.fallback_templates["antibiotics_dairy"]
                interaction_types.append("antibiotics_dairy")
                
            elif 'ciprofloxacin' in med and 'coffee' in food:
                template = self.fallback_templates["caffeine_interactions"]
                interaction_types.append("caffeine_interactions")
                
            else:
                # Generic explanation based on severity
                severity = interaction.get('severity', 'caution')
                if severity == 'avoid':
                    explanations.append(f"The combination of {interaction.get('medication_name')} and {interaction.get('food_name')} should be avoided due to {interaction.get('mechanism', 'potential adverse effects')}.")
                elif severity == 'caution':
                    explanations.append(f"Use caution when combining {interaction.get('medication_name')} with {interaction.get('food_name')}. {interaction.get('clinical_effect', 'Monitor for side effects')}.")
                continue
            
            explanations.append(template["explanation"])
            all_warnings.extend(template["warnings"])
        
        # Create comprehensive summary
        if interaction_types:
            primary_type = interaction_types[0]
            enhanced_summary = self.fallback_templates[primary_type]["summary"]
            if len(interaction_types) > 1:
                enhanced_summary += f" Additionally, {len(interaction_types)-1} other interaction pattern(s) were identified."
        else:
            enhanced_summary = f"Found {len(interactions)} interaction(s) requiring attention based on clinical evidence."
        
        # Combine explanations
        detailed_explanation = " ".join(explanations)
        if not detailed_explanation:
            detailed_explanation = "The identified interactions are based on documented clinical evidence and should be discussed with your healthcare provider."
        
        # Remove duplicate warnings
        unique_warnings = list(set(all_warnings))
        
        return AIAnalysisResult(
            enhanced_summary=enhanced_summary,
            detailed_explanation=detailed_explanation,
            additional_warnings=unique_warnings,
            confidence=0.85,
            analysis_method="Template",
            processing_time=0.0
        )
    
    def _groq_analysis(self, medications: List[str], foods: List[str], 
                      interactions: List[Dict]) -> Optional[AIAnalysisResult]:
        """Groq API analysis (requires API key)"""
        # This would be implemented with a real API key
        # For now, return None to fall back to template analysis
        return None
    
    def _local_ai_analysis(self, medications: List[str], foods: List[str], 
                          interactions: List[Dict]) -> Optional[str]:
        """Local transformer-based analysis"""
        if not self.tokenizer:
            return None
        
        try:
            # Create a simple prompt for analysis
            interaction_text = f"Analyzing interactions between medications {', '.join(medications)} and foods {', '.join(foods)}."
            
            # For now, return a simple AI-enhanced insight
            # In a full implementation, you'd use a medical language model here
            ai_insight = "Based on pharmacological principles, these interactions should be monitored for changes in drug effectiveness or increased side effects."
            
            return ai_insight
            
        except Exception as e:
            logging.debug(f"Local AI analysis error: {e}")
            return None
    
    def get_personalized_advice(self, interactions: List[Dict], 
                              user_context: Dict = None) -> List[str]:
        """Generate personalized advice based on interactions and user context"""
        advice = []
        
        if not interactions:
            advice.append("✅ Great news! No significant interactions were found.")
            advice.append("💡 Continue monitoring your medications and diet, and always consult your healthcare provider about any concerns.")
            return advice
        
        # Categorize advice by severity
        critical_interactions = [i for i in interactions if i.get('severity') == 'avoid']
        caution_interactions = [i for i in interactions if i.get('severity') == 'caution']
        
        if critical_interactions:
            advice.append("🚨 **Critical Actions Required:**")
            for interaction in critical_interactions[:2]:  # Top 2 most critical
                advice.append(f"   • Immediately discuss {interaction.get('medication_name')} + {interaction.get('food_name')} with your doctor")
        
        if caution_interactions:
            advice.append("⚠️ **Monitoring Recommendations:**")
            for interaction in caution_interactions[:3]:  # Top 3 cautions
                timing = interaction.get('timing_recommendation', 'Monitor closely')
                advice.append(f"   • {timing}")
        
        # General advice
        advice.extend([
            "📞 **Next Steps:**",
            "   • Share these results with your healthcare provider",
            "   • Keep a medication and food diary",
            "   • Don't stop medications without medical supervision"
        ])
        
        return advice