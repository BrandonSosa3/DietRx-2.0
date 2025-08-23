import streamlit as st
import logging
import traceback
from typing import Optional, Callable, Any
from functools import wraps
import time
from datetime import datetime

class ErrorHandler:
    def __init__(self):
        self.error_counts = {}
        self.last_errors = {}
    
    @staticmethod
    def handle_gracefully(fallback_message: str = "An error occurred", 
                         show_details: bool = False):
        """Decorator for graceful error handling"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    ErrorHandler._log_error(func.__name__, e)
                    
                    if show_details:
                        st.error(f"❌ {fallback_message}: {str(e)}")
                    else:
                        st.error(f"❌ {fallback_message}")
                    
                    return None
            return wrapper
        return decorator
    
    @staticmethod
    def _log_error(function_name: str, error: Exception):
        """Log error details"""
        error_msg = f"Error in {function_name}: {str(error)}"
        logging.error(error_msg)
        logging.debug(traceback.format_exc())
    
    @staticmethod
    def safe_execute(func: Callable, fallback_value: Any = None, 
                    error_message: str = "Operation failed") -> Any:
        """Safely execute a function with fallback"""
        try:
            return func()
        except Exception as e:
            ErrorHandler._log_error(func.__name__ if hasattr(func, '__name__') else 'anonymous', e)
            st.warning(f"⚠️ {error_message}")
            return fallback_value
    
    @staticmethod
    def validate_user_input(medications: list, foods: list) -> tuple[bool, str]:
        """Validate user input for analysis"""
        if not medications and not foods:
            return False, "Please select at least one medication or food item."
        
        if len(medications) > 20:
            return False, "Too many medications selected. Please limit to 20 items for optimal analysis."
        
        if len(foods) > 30:
            return False, "Too many foods selected. Please limit to 30 items for optimal analysis."
        
        # Check for potentially harmful combinations
        total_items = len(medications) + len(foods)
        if total_items > 40:
            return False, "Too many total items selected. Please reduce the selection for better analysis."
        
        return True, "Input validation passed"
    
    @staticmethod
    def handle_api_failure(api_name: str, fallback_action: str = "using cached data"):
        """Handle API failures gracefully"""
        st.warning(f"⚠️ {api_name} API temporarily unavailable. Continuing {fallback_action}.")
        logging.warning(f"API failure: {api_name}")
    
    @staticmethod
    def handle_database_error(operation: str, fallback_action: str = "Please try again"):
        """Handle database errors"""
        st.error(f"❌ Database error during {operation}. {fallback_action}")
        logging.error(f"Database error in operation: {operation}")
    
    @staticmethod
    def create_error_report() -> dict:
        """Create error report for debugging"""
        return {
            "timestamp": datetime.now().isoformat(),
            "streamlit_version": st.__version__,
            "error_summary": "Error report generated"
        }

class GracefulDegradation:
    """Handle graceful degradation when components fail"""
    
    @staticmethod
    def fallback_fuzzy_matching(query: str, candidates: list) -> list:
        """Simple fallback when fuzzy matching fails"""
        query_lower = query.lower()
        matches = []
        
        for candidate in candidates:
            if query_lower in candidate.lower():
                matches.append(candidate)
        
        return matches[:10]  # Return top 10
    
    @staticmethod
    def fallback_interaction_analysis(medications: list, foods: list) -> dict:
        """Fallback analysis when main engine fails"""
        return {
            "summary": f"Basic analysis completed for {len(medications)} medications and {len(foods)} foods.",
            "recommendations": [
                "⚠️ Advanced analysis temporarily unavailable",
                "📞 Please consult your healthcare provider about these combinations",
                "💡 Monitor for any unusual symptoms when taking medications with food"
            ],
            "confidence": 0.5,
            "method": "Fallback analysis"
        }
    
    @staticmethod
    def minimal_ai_analysis(interactions: list) -> dict:
        """Minimal AI analysis when full AI fails"""
        if not interactions:
            return {
                "summary": "No significant interactions detected.",
                "explanation": "Based on available data, no major interactions were found.",
                "warnings": [],
                "confidence": 0.7
            }
        
        critical_count = sum(1 for i in interactions if i.get('severity') == 'avoid')
        
        if critical_count > 0:
            summary = f"⚠️ {critical_count} critical interaction(s) require immediate attention."
            explanation = "Critical interactions detected. Please review recommendations carefully."
        else:
            summary = "Some interactions detected that may require monitoring."
            explanation = "Monitor these combinations and consult your healthcare provider if you experience any unusual symptoms."
        
        return {
            "summary": summary,
            "explanation": explanation,
            "warnings": ["Advanced AI analysis temporarily unavailable"],
            "confidence": 0.6
        }