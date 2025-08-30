import streamlit as st
from streamlit_searchbox import st_searchbox
from typing import List, Dict, Optional, Tuple
import logging
from utils.fuzzy_matcher import FuzzyMatcher

class SearchInterface:
    def __init__(self, fuzzy_matcher: FuzzyMatcher):
        self.fuzzy_matcher = fuzzy_matcher
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize search-related session state"""
        if 'selected_medications' not in st.session_state:
            st.session_state.selected_medications = []
        if 'selected_foods' not in st.session_state:
            st.session_state.selected_foods = []
        if 'search_history' not in st.session_state:
            st.session_state.search_history = {'medications': [], 'foods': []}
    
    def medication_search_callback(self, search_term: str) -> List[str]:
        """Callback function for medication searchbox"""
        if not search_term or len(search_term) < 2:
            # Return recent searches for empty/short queries
            recent = st.session_state.search_history.get('medications', [])
            return recent[:10]
        
        # Get medication names from session state
        medication_names = st.session_state.get('medication_names', [])
        
        # Find matches using fuzzy matcher
        matches = self.fuzzy_matcher.find_best_matches(
            search_term, 
            medication_names, 
            limit=10,
            score_cutoff=50
        )
        
        return [match[0] for match in matches]
    
    def food_search_callback(self, search_term: str) -> List[str]:
        """Callback function for food searchbox"""
        if not search_term or len(search_term) < 2:
            # Return recent searches for empty/short queries
            recent = st.session_state.search_history.get('foods', [])
            return recent[:10]
        
        # Get food names from session state
        food_names = st.session_state.get('food_names', [])
        
        # Find matches using fuzzy matcher
        matches = self.fuzzy_matcher.find_best_matches(
            search_term, 
            food_names, 
            limit=10,
            score_cutoff=50
        )
        
        return [match[0] for match in matches]
    
    def add_to_search_history(self, item: str, item_type: str):
        """Add item to search history"""
        if item_type not in st.session_state.search_history:
            st.session_state.search_history[item_type] = []
        
        history = st.session_state.search_history[item_type]
        if item not in history:
            history.insert(0, item)  # Add to beginning
            # Keep only last 20 items
            st.session_state.search_history[item_type] = history[:20]
    
    def render_medication_search(self) -> Optional[str]:
        """Render single medication search interface"""
        st.subheader("Select Medication (One at a time)")
        
        # Search box
        selected_med = st_searchbox(
            search_function=self.medication_search_callback,
            placeholder="Type medication name (e.g., ibuprofen, aspirin)...",
            label="Search Medications",
            key="medication_searchbox",
            clear_on_submit=True
        )
        
        # Handle selection - SINGLE ITEM ONLY (NO IMMEDIATE RERUN)
        if selected_med and selected_med not in st.session_state.selected_medications:
            # Replace any existing selection with the new one
            st.session_state.selected_medications = [selected_med]
            self.add_to_search_history(selected_med, 'medications')
            # REMOVED st.rerun() - this was causing the loop!
        
        # Display selected medication
        if st.session_state.selected_medications:
            current_med = st.session_state.selected_medications[0]
            
            # Show selected medication in a nice box
            st.success(f"**Selected Medication:** {current_med}")
            
            # Simple clear button
            if st.button("Choose Different Medication", key="clear_med"):
                st.session_state.selected_medications = []
                st.rerun()  # Only rerun on explicit button click
        
        return selected_med

    def render_food_search(self) -> Optional[str]:
        """Render single food search interface"""
        st.subheader("Select Food (One at a time)")
        
        # Always show the search box first
        selected_food = st_searchbox(
            search_function=self.food_search_callback,
            placeholder="Type food name (e.g., grapefruit, spinach)...",
            label="Search Foods",
            key="food_search_unique_key",
            clear_on_submit=False
        )
        
        # Handle new selection
        if selected_food:
            if not st.session_state.selected_foods or selected_food != st.session_state.selected_foods[0]:
                st.session_state.selected_foods = [selected_food]
                self.add_to_search_history(selected_food, 'foods')
        
        # Always display current selection if exists
        if st.session_state.selected_foods:
            current_food = st.session_state.selected_foods[0]
            st.success(f"Selected Food: {current_food}")
            
            # Clear button
            if st.button("Choose Different Food", key="clear_food_btn"):
                st.session_state.selected_foods = []
                if 'food_search_unique_key' in st.session_state:
                    del st.session_state['food_search_unique_key']
                st.rerun()
        
        return st.session_state.selected_foods[0] if st.session_state.selected_foods else None
    
    def render_batch_input(self):
        """Render batch input interface"""
        with st.expander("📝 Batch Input (Add Multiple Items)"):
            st.write("**Add multiple medications or foods at once:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Medications** (one per line):")
                med_batch_input = st.text_area(
                    "Enter medications:",
                    placeholder="Ibuprofen\nAspirin\nMetformin",
                    key="med_batch_input",
                    height=100
                )
                
                if st.button("Add Medications", key="add_med_batch"):
                    if med_batch_input:
                        new_meds = [med.strip() for med in med_batch_input.split('\n') if med.strip()]
                        added_count = 0
                        
                        for med in new_meds:
                            # Try to find best match
                            matches = self.fuzzy_matcher.find_best_matches(
                                med, 
                                st.session_state.get('medication_names', []), 
                                limit=1,
                                score_cutoff=70
                            )
                            
                            if matches and matches[0][0] not in st.session_state.selected_medications:
                                st.session_state.selected_medications.append(matches[0][0])
                                self.add_to_search_history(matches[0][0], 'medications')
                                added_count += 1
                            elif not matches:
                                st.warning(f"Could not find medication: {med}")
                        
                        if added_count > 0:
                            st.success(f"Added {added_count} medications!")
                            st.rerun()
            
            with col2:
                st.write("**Foods** (one per line):")
                food_batch_input = st.text_area(
                    "Enter foods:",
                    placeholder="Grapefruit\nSpinach\nMilk",
                    key="food_batch_input",
                    height=100
                )
                
                if st.button("Add Foods", key="add_food_batch"):
                    if food_batch_input:
                        new_foods = [food.strip() for food in food_batch_input.split('\n') if food.strip()]
                        added_count = 0
                        
                        for food in new_foods:
                            # Try to find best match
                            matches = self.fuzzy_matcher.find_best_matches(
                                food, 
                                st.session_state.get('food_names', []), 
                                limit=1,
                                score_cutoff=70
                            )
                            
                            if matches and matches[0][0] not in st.session_state.selected_foods:
                                st.session_state.selected_foods.append(matches[0][0])
                                self.add_to_search_history(matches[0][0], 'foods')
                                added_count += 1
                            elif not matches:
                                st.warning(f"Could not find food: {food}")
                        
                        if added_count > 0:
                            st.success(f"Added {added_count} foods!")
                            st.rerun()
    
    def get_selected_items(self) -> Tuple[List[str], List[str]]:
        """Get currently selected medications and foods"""
        return (
            st.session_state.selected_medications.copy(),
            st.session_state.selected_foods.copy()
        )
    
    def has_selections(self) -> bool:
        """Check if user has made any selections"""
        return bool(st.session_state.selected_medications or st.session_state.selected_foods)


    def validate_selections(self) -> tuple[bool, str]:
        """Validate user selections before analysis"""
        medications = st.session_state.selected_medications
        foods = st.session_state.selected_foods
        
        if not medications:
            return False, "Please select a medication."
        
        if not foods:
            return False, "Please select a food."
        
        if len(medications) > 1:
            return False, "Please select only one medication at a time."
        
        if len(foods) > 1:
            return False, "Please select only one food at a time."
        
        return True, "Ready for analysis"

    def has_selections(self) -> bool:
        """Check if user has made valid selections"""
        return bool(st.session_state.selected_medications or st.session_state.selected_foods)

    def display_selection_warnings(self):
        """Display warnings about current selections"""
        total_meds = len(st.session_state.selected_medications)
        total_foods = len(st.session_state.selected_foods)
        
        if total_meds > 15:
            st.warning(f"⚠️ You have {total_meds} medications selected. Consider reducing for better analysis accuracy.")
        
        if total_foods > 25:
            st.warning(f"⚠️ You have {total_foods} foods selected. Consider focusing on your most common foods.")
        
        if total_meds + total_foods > 35:
            st.error("❌ Too many items selected. Please reduce your selection for optimal analysis.")
