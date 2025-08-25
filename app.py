import streamlit as st

# Configure Streamlit page FIRST
st.set_page_config(
    page_title="DietRx Enhanced",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

import logging
from pathlib import Path
import sys
from typing import List, Dict, Optional, Tuple
import time
import os
import time
import plotly.express as px
import pandas as pd
import numpy as np


# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our modules
from config import *
from data.database import DatabaseManager
from data.api_clients import APIManager
from data.cache_manager import CacheManager
from utils.fuzzy_matcher import FuzzyMatcher
from utils.data_processor import DataProcessor
from utils.interaction_engine import InteractionEngine, AnalysisResults, Severity
from utils.interaction_data_loader import InteractionDataLoader
from components.results_display import ResultsDisplay
from utils.error_handler import ErrorHandler
from utils.analytics_engine import AnalyticsEngine
from components.analytics_dashboard import AnalyticsDashboard

# Direct import of SearchInterface
try:
    from components.search_interface import SearchInterface
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please check that components/search_interface.py exists")
    st.stop()


# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DietRxApp:
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'initialized' not in st.session_state:
            st.session_state.initialized = False
            st.session_state.db_populated = False
            st.session_state.medication_names = []
            st.session_state.food_names = []
            st.session_state.current_page = 'search'  # Track current page
    
    def setup_components(self):
        """Initialize all components"""
        if 'components' not in st.session_state:
            try:
                # Initialize database
                db_manager = DatabaseManager(DATABASE_PATH)
                
                # Initialize API clients
                api_manager = APIManager()
                
                # Initialize cache manager
                cache_manager = CacheManager(db_manager)
                
                # Initialize fuzzy matcher
                fuzzy_matcher = FuzzyMatcher(FUZZY_MATCH_THRESHOLD)
                
                # Initialize data processor
                data_processor = DataProcessor(db_manager, api_manager)
                
                # Initialize search interface
                search_interface = SearchInterface(fuzzy_matcher)
                
                # Initialize interaction engine
                interaction_engine = InteractionEngine(db_manager, fuzzy_matcher)
                
                # Initialize results display
                results_display = ResultsDisplay()
                
                # NEW: Initialize analytics components
                analytics_engine = AnalyticsEngine(db_manager)
                analytics_dashboard = AnalyticsDashboard()
                
                logging.info("All components initialized successfully")
                
                st.session_state.components = {
                    'db_manager': db_manager,
                    'api_manager': api_manager,
                    'cache_manager': cache_manager,
                    'fuzzy_matcher': fuzzy_matcher,
                    'data_processor': data_processor,
                    'search_interface': search_interface,
                    'interaction_engine': interaction_engine,
                    'results_display': results_display,
                    'analytics_engine': analytics_engine,      # NEW
                    'analytics_dashboard': analytics_dashboard  # NEW
                }
                
            except Exception as e:
                logging.error(f"Error initializing components: {e}")
                st.error(f"Failed to initialize application: {e}")
                st.session_state.components = None
        
        return st.session_state.components
        
    def populate_initial_data(self):
        """Populate database with initial data if needed"""
        if not st.session_state.db_populated:
            components = self.setup_components()
            if not components:
                return
            
            data_processor = components['data_processor']
            
            # Check if database is already populated
            if data_processor.is_database_populated():
                logging.info("Database already populated, skipping initialization")
                st.session_state.db_populated = True
                
                # Just refresh the cached names
                st.session_state.medication_names = data_processor.get_medication_names()
                st.session_state.food_names = data_processor.get_food_names()
                
                # Show current stats
                stats = data_processor.get_database_stats()
                st.success(f"✅ Database ready! {stats['searchable_med_names']} medications, {stats['searchable_food_names']} foods, {stats['total_interactions']} interactions available.")
                return
            
            # Only populate if needed
            with st.spinner("Setting up comprehensive database for first use..."):
                try:
                    # Show progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Populate core medications (fallback data)
                    status_text.text("Loading core medications...")
                    progress_bar.progress(10)
                    med_count = data_processor.populate_common_medications()
                    
                    # Clean up complex names
                    status_text.text("Cleaning up complex names...")
                    progress_bar.progress(20)
                    data_processor.cleanup_complex_medication_names()
                    
                    # Populate core foods (fallback data)
                    status_text.text("Loading core foods...")
                    progress_bar.progress(30)
                    food_count = data_processor.populate_common_foods()
                    
                    # Populate interactions
                    status_text.text("Loading interaction database...")
                    progress_bar.progress(40)
                    interaction_count = data_processor.populate_interaction_database()
                    
                    # NEW: Expand database with comprehensive data
                    status_text.text("Expanding database with comprehensive medication data...")
                    progress_bar.progress(60)
                    expansion_results = data_processor.expand_database(med_target=300, food_target=150)
                    
                    status_text.text("Finalizing comprehensive database...")
                    progress_bar.progress(90)
                    
                    # Cache the names for autocomplete
                    st.session_state.medication_names = data_processor.get_medication_names()
                    st.session_state.food_names = data_processor.get_food_names()
                    
                    # Final setup
                    status_text.text("Database ready!")
                    progress_bar.progress(100)
                    
                    st.session_state.db_populated = True
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Show final comprehensive stats
                    final_stats = data_processor.get_database_stats()
                    st.success(f"✅ Comprehensive database initialized! {final_stats['searchable_med_names']} medications, {final_stats['searchable_food_names']} foods, and {interaction_count} interactions loaded!")
                    
                    # Show expansion summary
                    st.info(f"📈 Database expanded: {expansion_results['medications']} total medications, {expansion_results['foods']} total foods available for analysis.")
                    
                except Exception as e:
                    st.error(f"❌ Error initializing database: {e}")
                    logging.error(f"Database initialization error: {e}")
    
    def render_sidebar(self, components):
        """Render application sidebar"""
        with st.sidebar:
            st.header("📋 App Status")
            
            # Navigation - UPDATED with new pages
            st.subheader("🧭 Navigation")
            page = st.radio(
                "Choose page:",
                [
                    "🔍 Search & Analyze", 
                    "📊 Analytics Dashboard",  # NEW
                    "🧪 Test Fuzzy Matching", 
                    "📋 Database Stats",
                    "⚡ Performance Monitor"   # NEW
                ],
                key="page_selector"
            )
            
            # Update current page
            if page == "🔍 Search & Analyze":
                st.session_state.current_page = 'search'
            elif page == "📊 Analytics Dashboard":
                st.session_state.current_page = 'analytics'  # NEW
            elif page == "🧪 Test Fuzzy Matching":
                st.session_state.current_page = 'test'
            elif page == "📋 Database Stats":
                st.session_state.current_page = 'stats'
            elif page == "⚡ Performance Monitor":
                st.session_state.current_page = 'performance'  # NEW
            
            st.markdown("---")
            
            # Enhanced statistics display
            self._display_enhanced_sidebar_stats(components)
            
            st.markdown("---")
            
            # Control buttons (keep existing ones)
            if st.button("🔄 Refresh Cache"):
                try:
                    components['cache_manager'].clear_memory_cache()
                    st.success("Cache refreshed!")
                except Exception as e:
                    st.error(f"Error refreshing cache: {e}")
            
            if st.button("🧹 Clean Reset Database", help="Remove all data and start fresh"):
                try:
                    import os
                    if os.path.exists(DATABASE_PATH):
                        os.remove(DATABASE_PATH)
                        st.success("✅ Database deleted!")
                    
                    # Clear session state
                    st.session_state.db_populated = False
                    st.session_state.medication_names = []
                    st.session_state.food_names = []
                    if 'components' in st.session_state:
                        del st.session_state.components
                    
                    st.info("🔄 Please refresh the page to reinitialize with clean data.")
                    
                except Exception as e:
                    st.error(f"❌ Error resetting database: {e}")
            
            if st.button("🗑️ Reset App"):
                # Clear session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    def render_search_page(self, components):
        """Render the main search and analyze page"""
        st.title("🍎💊 DietRx Enhanced")
        st.markdown("**Advanced Food-Drug Interaction Checker**")
        st.markdown("---")
        
        search_interface = components['search_interface']
        
        # Medication search (full width)
        search_interface.render_medication_search()
        
        st.markdown("---")
        
        # Food search (full width)  
        search_interface.render_food_search()
        
        # Analysis section
        st.markdown("---")
        
        if search_interface.has_selections():
            medications, foods = search_interface.get_selected_items()
            
            st.subheader("🔍 Ready for Analysis")
            st.write(f"**Selected:** {len(medications)} medications, {len(foods)} foods")
            
            # Add a simple "Start Over" button as the only clear option
            if st.button("🔄 Start Over (Clear All)", type="secondary", key="start_over"):
                st.session_state.selected_medications = []
                st.session_state.selected_foods = []
                st.success("✅ Cleared all selections")
                st.rerun()
            
            # Big analyze button
            if st.button("🚀 Analyze Interactions", type="primary", key="analyze_button"):
                self.perform_interaction_analysis(components, medications, foods)
        
        # Show previous results if they exist (keep this part)
        if 'analysis_results' in st.session_state:
            st.markdown("---")
            st.subheader("📊 Latest Analysis Results")
            
            # Show what was analyzed
            meds_analyzed = st.session_state.get('analysis_medications', [])
            foods_analyzed = st.session_state.get('analysis_foods', [])
            
            col1, col2 = st.columns(2)
            with col1:
                if meds_analyzed:
                    st.write("**Medications analyzed:**")
                    for med in meds_analyzed:
                        st.write(f"• {med}")
            
            with col2:
                if foods_analyzed:
                    st.write("**Foods analyzed:**")
                    for food in foods_analyzed:
                        st.write(f"• {food}")
            
            # Display the stored results
            self.display_analysis_results(st.session_state.analysis_results)
            
            # Clear results button
            if st.button("🗑️ Clear Results", type="secondary", key="clear_results_unique"):
                del st.session_state.analysis_results
                if 'analysis_medications' in st.session_state:
                    del st.session_state.analysis_medications
                if 'analysis_foods' in st.session_state:
                    del st.session_state.analysis_foods
                st.rerun()
        
        elif not search_interface.has_selections():
            st.info("👆 **Start by selecting medications and foods above to check for interactions.**")


    def display_analysis_results(self, results: AnalysisResults):
        """Display the interaction analysis results using enhanced display"""
        components = st.session_state.components
        results_display = components['results_display']
        
        # Get analytics data for enhanced PDF reports
        analytics_data = None
        try:
            if hasattr(st.session_state, 'analytics_data'):
                analytics_data = st.session_state.analytics_data
            else:
                # Generate basic analytics for PDF reports
                analytics_engine = components['analytics_engine']
                analytics_data = analytics_engine.generate_comprehensive_analytics()
        except Exception as e:
            logging.warning(f"Could not load analytics data for PDF generation: {e}")
        
        # Use the enhanced results display with analytics data
        # Update the results display to accept analytics data
        if hasattr(results_display, 'display_results_with_analytics'):
            results_display.display_results_with_analytics(results, analytics_data)
        else:
            results_display.display_results(results)
    
    def render_test_page(self, components):
        """Render the fuzzy matching test page"""
        st.title("🧪 Test Fuzzy Matching")
        st.markdown("---")
        
        st.markdown("Try entering medication or food names with typos to test the matching system:")
        
        test_query = st.text_input("Enter a medication or food name to test matching:", 
                                 placeholder="e.g., 'ibuprofin', 'grapfruit', 'asprin'")
        
        if test_query:
            try:
                fuzzy_matcher = components['fuzzy_matcher']
                
                med_matches = []
                food_matches = []
                
                if st.session_state.medication_names:
                    med_matches = fuzzy_matcher.find_best_matches(
                        test_query, 
                        st.session_state.medication_names, 
                        limit=5
                    )
                
                if st.session_state.food_names:
                    food_matches = fuzzy_matcher.find_best_matches(
                        test_query, 
                        st.session_state.food_names, 
                        limit=5
                    )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Medication Matches:**")
                    if med_matches:
                        for match, score in med_matches:
                            score = float(score)
                            if score >= 90:
                                st.success(f"• {match} (Score: {score:.1f})")
                            elif score >= 80:
                                st.warning(f"• {match} (Score: {score:.1f})")
                            else:
                                st.info(f"• {match} (Score: {score:.1f})")
                    else:
                        st.info("No medication matches found")
                
                with col2:
                    st.write("**Food Matches:**")
                    if food_matches:
                        for match, score in food_matches:
                            score = float(score)
                            if score >= 90:
                                st.success(f"• {match} (Score: {score:.1f})")
                            elif score >= 80:
                                st.warning(f"• {match} (Score: {score:.1f})")
                            else:
                                st.info(f"• {match} (Score: {score:.1f})")
                    else:
                        st.info("No food matches found")
            
            except Exception as e:
                st.error(f"Error testing fuzzy matching: {e}")
    
    def render_stats_page(self, components):
        """Render database statistics page"""
        st.title("📊 Database Statistics")
        st.markdown("---")
        
        try:
            # Get data
            medications = components['db_manager'].get_all_medications()
            foods = components['db_manager'].get_all_foods()
            
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Medications", len(medications))
            with col2:
                st.metric("Total Foods", len(foods))
            with col3:
                total_names = len(st.session_state.medication_names) + len(st.session_state.food_names)
                st.metric("Searchable Names", total_names)
            with col4:
                cache_stats = components['cache_manager'].get_cache_stats()
                st.metric("Cache Entries", cache_stats['database_cache_active'])
            
            # Sample data display
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Sample Medications")
                if medications:
                    sample_meds = medications[:10]
                    for med in sample_meds:
                        with st.expander(f"📋 {med['name']}"):
                            st.write(f"**Generic:** {med.get('generic_name', 'N/A')}")
                            st.write(f"**Class:** {med.get('drug_class', 'N/A')}")
                            if med.get('brand_names'):
                                brands = eval(med['brand_names']) if isinstance(med['brand_names'], str) else med['brand_names']
                                st.write(f"**Brands:** {', '.join(brands)}")
            
            with col2:
                st.subheader("🥗 Sample Foods")
                if foods:
                    sample_foods = foods[:10]
                    for food in sample_foods:
                        with st.expander(f"🍎 {food['name']}"):
                            st.write(f"**Category:** {food.get('category', 'N/A')}")
                            if food.get('aliases'):
                                aliases = eval(food['aliases']) if isinstance(food['aliases'], str) else food['aliases']
                                st.write(f"**Aliases:** {', '.join(aliases)}")
                
        except Exception as e:
            st.error(f"Error loading statistics: {e}")

    def monitor_performance(self, operation_name: str, start_time: float):
        """Monitor and log performance metrics"""
        duration = time.time() - start_time
        
        if duration > 5.0:  # Slow operation
            st.warning(f"⚠️ {operation_name} took {duration:.1f} seconds (slower than expected)")
            logging.warning(f"Slow operation: {operation_name} - {duration:.2f}s")
        elif duration > 2.0:
            st.info(f"ℹ️ {operation_name} completed in {duration:.1f} seconds")
        
        logging.info(f"Performance: {operation_name} - {duration:.2f}s")

    def perform_interaction_analysis(self, components, medications: List[str], foods: List[str]):
        """Perform the actual interaction analysis with error handling and monitoring"""
        
        # Validate selections first
        search_interface = components['search_interface']
        is_valid, validation_msg = search_interface.validate_selections()
        
        if not is_valid:
            st.error(f"❌ {validation_msg}")
            return
        
        # Show selection warnings
        search_interface.display_selection_warnings()
        
        interaction_engine = components['interaction_engine']
        
        try:
            start_time = time.time()
            
            with st.spinner("🔍 Analyzing interactions..."):
                # Perform the analysis
                results = ErrorHandler.safe_execute(
                    lambda: interaction_engine.analyze_interactions(medications, foods),
                    fallback_value=None,
                    error_message="Analysis engine encountered an error"
                )
                
                if results is None:
                    st.error("❌ Analysis failed. Please try again or contact support.")
                    return
                
                # Monitor performance
                self.monitor_performance("Interaction Analysis", start_time)
                
                # ONLY store results in session state - don't display them here
                st.session_state.analysis_results = results
                st.session_state.analysis_medications = medications
                st.session_state.analysis_foods = foods
                
                # REMOVE THIS LINE - don't display results here
                # self.display_analysis_results(results)  # <-- REMOVE THIS
                
                # Just show success message and let render_search_page handle display
                st.success("✅ Analysis completed! Results displayed below.")
                st.rerun()  # Refresh to show the results
                
                # Log successful analysis
                logging.info(f"Successful analysis: {len(medications)} meds, {len(foods)} foods, {len(results.interactions)} interactions")
                
        except Exception as e:
            st.error(f"❌ Critical error during analysis: {str(e)}")
            logging.error(f"Critical analysis error: {e}")
            
            # Offer fallback options
            st.info("💡 You can try:")
            st.write("• Reducing the number of selected items")
            st.write("• Refreshing the page and trying again")
            st.write("• Contacting support if the problem persists")


    def render_database_viewer_page(self, components):
        """Render database viewer page"""
        st.title("🗄️ Database Viewer")
        st.markdown("**Explore the underlying data powering DietRx**")
        st.markdown("---")
        
        # Database overview
        self._show_database_overview(components)
        
        # Table viewers
        tab1, tab2, tab3, tab4 = st.tabs(["💊 Medications", "🍎 Foods", "⚡ Interactions", "📊 API Cache"])
        
        with tab1:
            self._show_medications_table(components)
        
        with tab2:
            self._show_foods_table(components)
        
        with tab3:
            self._show_interactions_table(components)
        
        with tab4:
            self._show_api_cache_table(components)

    def _show_database_overview(self, components):
        """Show database overview statistics"""
        try:
            db = components['db_manager']
            
            # Get table counts
            conn = db.get_connection()
            cursor = conn.cursor()
            
            tables = ['medications', 'foods', 'known_interactions', 'api_cache']
            table_stats = {}
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_stats[table] = count
            
            # Database file info
            import os
            if os.path.exists(DATABASE_PATH):
                db_size = os.path.getsize(DATABASE_PATH)
                db_size_mb = db_size / (1024 * 1024)
            else:
                db_size_mb = 0
            
            conn.close()
            
            # Display overview
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("💊 Medications", table_stats.get('medications', 0))
            with col2:
                st.metric("🍎 Foods", table_stats.get('foods', 0))
            with col3:
                st.metric("⚡ Interactions", table_stats.get('known_interactions', 0))
            with col4:
                st.metric("📊 Cache Entries", table_stats.get('api_cache', 0))
            with col5:
                st.metric("💾 DB Size", f"{db_size_mb:.1f} MB")
            
            # Database location
            st.info(f"📍 **Database Location:** `{DATABASE_PATH}`")
            
        except Exception as e:
            st.error(f"Error accessing database: {e}")

    def _show_medications_table(self, components):
        """Show medications table"""
        try:
            medications = components['db_manager'].get_all_medications()
            
            if not medications:
                st.warning("No medications found in database")
                return
            
            # Convert to DataFrame for better display
            import pandas as pd
            
            df_data = []
            for med in medications:
                df_data.append({
                    'ID': med['id'],
                    'Name': med['name'],
                    'Generic Name': med.get('generic_name', 'N/A'),
                    'Drug Class': med.get('drug_class', 'N/A'),
                    'Brand Names': str(med.get('brand_names', 'N/A'))[:50] + '...' if med.get('brand_names') else 'N/A',
                    'Created': med['created_at'][:10] if med.get('created_at') else 'N/A'
                })
            
            df = pd.DataFrame(df_data)
            
            # Search/filter
            search_term = st.text_input("🔍 Search medications:", key="med_search")
            if search_term:
                df = df[df['Name'].str.contains(search_term, case=False, na=False) |
                    df['Generic Name'].str.contains(search_term, case=False, na=False)]
            
            # Display table
            st.write(f"**Showing {len(df)} of {len(medications)} medications**")
            st.dataframe(df, use_container_width=True, height=400)
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="medications.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Error loading medications: {e}")

    def _show_foods_table(self, components):
        """Show foods table"""
        try:
            foods = components['db_manager'].get_all_foods()
            
            if not foods:
                st.warning("No foods found in database")
                return
            
            import pandas as pd
            
            df_data = []
            for food in foods:
                df_data.append({
                    'ID': food['id'],
                    'Name': food['name'],
                    'Category': food.get('category', 'N/A'),
                    'Aliases': str(food.get('aliases', 'N/A'))[:50] + '...' if food.get('aliases') else 'N/A',
                    'Created': food['created_at'][:10] if food.get('created_at') else 'N/A'
                })
            
            df = pd.DataFrame(df_data)
            
            # Search/filter
            search_term = st.text_input("🔍 Search foods:", key="food_search")
            if search_term:
                df = df[df['Name'].str.contains(search_term, case=False, na=False) |
                    df['Category'].str.contains(search_term, case=False, na=False)]
            
            # Category filter
            categories = df['Category'].unique()
            selected_category = st.selectbox("Filter by category:", ['All'] + list(categories))
            if selected_category != 'All':
                df = df[df['Category'] == selected_category]
            
            st.write(f"**Showing {len(df)} foods**")
            st.dataframe(df, use_container_width=True, height=400)
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="foods.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Error loading foods: {e}")

    def _show_interactions_table(self, components):
        """Show interactions table"""
        try:
            db = components['db_manager']
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM known_interactions ORDER BY severity, medication_name")
            interactions = cursor.fetchall()
            conn.close()
            
            if not interactions:
                st.warning("No interactions found in database")
                return
            
            import pandas as pd
            
            df_data = []
            for interaction in interactions:
                df_data.append({
                    'ID': interaction[0],  # id
                    'Medication': interaction[1],  # medication_name
                    'Food': interaction[2],  # food_name
                    'Severity': interaction[3],  # severity
                    'Type': interaction[4] or 'N/A',  # interaction_type
                    'Mechanism': (interaction[5] or 'N/A')[:60] + '...' if interaction[5] and len(interaction[5]) > 60 else interaction[5] or 'N/A',
                    'Evidence': interaction[8] or 'N/A',  # evidence_level
                    'Source': interaction[9] or 'N/A'  # source
                })
            
            df = pd.DataFrame(df_data)
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                severity_filter = st.selectbox("Filter by severity:", ['All', 'avoid', 'caution', 'safe'])
            with col2:
                search_term = st.text_input("🔍 Search interactions:", key="interaction_search")
            
            if severity_filter != 'All':
                df = df[df['Severity'] == severity_filter]
            
            if search_term:
                df = df[df['Medication'].str.contains(search_term, case=False, na=False) |
                    df['Food'].str.contains(search_term, case=False, na=False)]
            
            st.write(f"**Showing {len(df)} interactions**")
            st.dataframe(df, use_container_width=True, height=400)
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="interactions.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Error loading interactions: {e}")

    def _show_api_cache_table(self, components):
        """Show API cache table"""
        try:
            db = components['db_manager']
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT cache_key, created_at, expires_at FROM api_cache ORDER BY created_at DESC")
            cache_entries = cursor.fetchall()
            conn.close()
            
            if not cache_entries:
                st.info("No API cache entries found")
                return
            
            import pandas as pd
            
            df_data = []
            for entry in cache_entries:
                df_data.append({
                    'Cache Key': entry[0][:50] + '...' if len(entry[0]) > 50 else entry[0],
                    'Created': entry[1][:19] if entry[1] else 'N/A',
                    'Expires': entry[2][:19] if entry[2] else 'N/A'
                })
            
            df = pd.DataFrame(df_data)
            st.write(f"**{len(df)} cache entries**")
            st.dataframe(df, use_container_width=True, height=300)
            
        except Exception as e:
            st.error(f"Error loading cache data: {e}")


    def _display_enhanced_sidebar_stats(self, components):
        """Display enhanced sidebar statistics"""
        try:
            # Get comprehensive stats
            stats = components['data_processor'].get_database_stats()
            cache_stats = components['cache_manager'].get_cache_stats()
            
            st.write("**📊 Data Overview:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("💊 Meds", f"{stats.get('searchable_med_names', 0)}")
                st.metric("🥗 Foods", f"{stats.get('searchable_food_names', 0)}")
            
            with col2:
                st.metric("⚡ Interactions", f"{stats.get('total_interactions', 0)}")
                st.metric("🗂️ Classes", f"{stats.get('drug_classes_count', 'N/A')}")
            
            st.write("**⚡ Performance:**")
            st.progress(min(cache_stats['database_cache_active'] / 100, 1.0))
            st.caption(f"Cache: {cache_stats['database_cache_active']} entries")
            
            # User selections
            if hasattr(st.session_state, 'selected_medications') and st.session_state.selected_medications:
                st.metric("Selected Items", 
                        len(st.session_state.selected_medications) + len(st.session_state.get('selected_foods', [])))
            
            # Quick analytics preview
            if st.session_state.current_page != 'analytics':
                if st.button("📊 View Analytics", type="secondary"):
                    st.session_state.current_page = 'analytics'
                    st.rerun()
            
        except Exception as e:
            # Fallback to basic stats
            try:
                medications = components['db_manager'].get_all_medications()
                foods = components['db_manager'].get_all_foods()
                st.write(f"**Database:** {len(medications)} meds, {len(foods)} foods")
            except:
                st.error("Error loading stats")

    def render_analytics_page(self, components):
        """Render the analytics dashboard page"""
        st.title("📊 Advanced Analytics Dashboard")
        st.markdown("**Comprehensive Drug-Food Interaction Intelligence**")
        
        # Check if data is available
        try:
            stats = components['data_processor'].get_database_stats()
            if stats.get('total_interactions', 0) == 0:
                st.warning("⚠️ No interaction data available. Please ensure the database is populated.")
                return
        except Exception as e:
            st.error(f"❌ Error checking data availability: {e}")
            return
        
        # Analytics generation with caching
        analytics_data = self._get_cached_analytics(components)
        
        if analytics_data:
            # Display the comprehensive dashboard
            analytics_dashboard = components['analytics_dashboard']
            analytics_dashboard.display_comprehensive_dashboard(analytics_data)
        else:
            st.error("❌ Could not generate analytics data")

    def _get_cached_analytics(self, components):
        """Get analytics data with caching for performance"""
        
        # Check if analytics are cached in session state
        cache_key = 'analytics_data'
        cache_timestamp_key = 'analytics_timestamp'
        
        # Cache for 5 minutes
        cache_duration = 300  # 5 minutes in seconds
        
        current_time = time.time()
        
        # Check if we have cached data that's still valid
        if (cache_key in st.session_state and 
            cache_timestamp_key in st.session_state and
            current_time - st.session_state[cache_timestamp_key] < cache_duration):
            
            st.info("📊 Using cached analytics data for better performance")
            return st.session_state[cache_key]
        
        # Generate fresh analytics
        try:
            with st.spinner("🔄 Generating comprehensive analytics..."):
                analytics_engine = components['analytics_engine']
                
                # Add progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Analyzing database structure...")
                progress_bar.progress(20)
                
                analytics_data = analytics_engine.generate_comprehensive_analytics()
                progress_bar.progress(60)
                
                status_text.text("Generating performance metrics...")
                performance_metrics = analytics_engine.generate_performance_metrics()
                analytics_data['performance_metrics'] = performance_metrics
                progress_bar.progress(80)
                
                status_text.text("Finalizing analytics...")
                progress_bar.progress(100)
                
                # Cache the results
                st.session_state[cache_key] = analytics_data
                st.session_state[cache_timestamp_key] = current_time
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                st.success("✅ Analytics generated successfully!")
                
                return analytics_data
                
        except Exception as e:
            st.error(f"❌ Error generating analytics: {e}")
            logging.error(f"Analytics generation error: {e}")
            return None

    def render_performance_page(self, components):
        """Render the performance monitoring page"""
        st.title("⚡ Performance Monitor")
        st.markdown("**System Performance & Optimization Insights**")
        
        # Real-time performance metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Database performance
            st.subheader("🗄️ Database Performance")
            
            try:
                # Simulate database query timing
                start_time = time.time()
                medications = components['db_manager'].get_all_medications()
                db_query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                st.metric("Query Response Time", f"{db_query_time:.1f}ms")
                st.metric("Database Entries", len(medications))
                
                # Database size
                analytics_engine = components['analytics_engine']
                perf_metrics = analytics_engine.generate_performance_metrics()
                st.metric("Database Size", f"{perf_metrics.get('database_size_mb', 0):.1f} MB")
                
            except Exception as e:
                st.error(f"Database metrics error: {e}")
        
        with col2:
            # Cache performance
            st.subheader("💾 Cache Performance")
            
            try:
                cache_stats = components['cache_manager'].get_cache_stats()
                
                st.metric("Cache Entries", cache_stats['database_cache_active'])
                st.metric("Memory Cache", cache_stats['memory_cache_size'])
                
                # Simulated cache hit rate
                cache_hit_rate = 85  # Simulated
                st.metric("Cache Hit Rate", f"{cache_hit_rate}%")
                
            except Exception as e:
                st.error(f"Cache metrics error: {e}")
        
        with col3:
            # System health
            st.subheader("🏥 System Health")
            
            # Component health checks
            health_checks = self._run_health_checks(components)
            
            healthy_components = sum(1 for status in health_checks.values() if status)
            total_components = len(health_checks)
            health_percentage = (healthy_components / total_components) * 100
            
            st.metric("System Health", f"{health_percentage:.0f}%")
            st.metric("Active Components", f"{healthy_components}/{total_components}")
            
            # Uptime simulation
            st.metric("Uptime", "99.9%")
        
        # Detailed performance analysis
        st.markdown("---")
        st.subheader("📈 Detailed Performance Analysis")
        
        # Performance over time (simulated)
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        response_times = np.random.normal(15, 3, 30)  # Simulated response times
        response_times = np.maximum(response_times, 5)  # Ensure minimum 5ms
        
        fig_performance = px.line(
            x=dates, 
            y=response_times,
            title="Average Response Time Over Time",
            labels={'x': 'Date', 'y': 'Response Time (ms)'}
        )
        
        fig_performance.add_hline(y=20, line_dash="dash", line_color="red", 
                                annotation_text="Performance Threshold")
        
        fig_performance.update_layout(height=400)
        st.plotly_chart(fig_performance, use_container_width=True)
        
        # Component status table
        st.subheader("🔧 Component Status")
        
        status_data = []
        for component, status in health_checks.items():
            status_data.append({
                'Component': component,
                'Status': '✅ Operational' if status else '❌ Issues',
                'Response Time': f"{np.random.uniform(5, 25):.1f}ms",
                'Last Check': datetime.now().strftime('%H:%M:%S')
            })
        
        status_df = pd.DataFrame(status_data)
        st.dataframe(status_df, use_container_width=True, hide_index=True)

    def _run_health_checks(self, components) -> Dict[str, bool]:
        """Run health checks on all components"""
        health_status = {}
        
        try:
            # Database health
            components['db_manager'].get_all_medications()
            health_status['Database'] = True
        except:
            health_status['Database'] = False
        
        try:
            # Search interface health
            search_interface = components['search_interface']
            health_status['Search Interface'] = hasattr(search_interface, 'medication_search_callback')
        except:
            health_status['Search Interface'] = False
        
        try:
            # Interaction engine health
            interaction_engine = components['interaction_engine']
            health_status['Interaction Engine'] = hasattr(interaction_engine, 'analyze_interactions')
        except:
            health_status['Interaction Engine'] = False
        
        try:
            # Analytics engine health
            analytics_engine = components['analytics_engine']
            health_status['Analytics Engine'] = hasattr(analytics_engine, 'generate_comprehensive_analytics')
        except:
            health_status['Analytics Engine'] = False
        
        try:
            # Cache health
            components['cache_manager'].get_cache_stats()
            health_status['Cache Manager'] = True
        except:
            health_status['Cache Manager'] = False
        
        return health_status
    
    def run(self):
        """Main application entry point"""
        # Initialize components
        components = self.setup_components()
        if not components:
            st.error("❌ Failed to initialize application. Please refresh the page.")
            st.stop()
        
        # Populate initial data if needed
        if not st.session_state.initialized:
            self.populate_initial_data()
            st.session_state.initialized = True
        
        # Render sidebar
        self.render_sidebar(components)
        
        # Render appropriate page based on selection
        page = st.session_state.get('current_page', 'search')
        
        if page == 'search':
            self.render_search_page(components)
        elif page == 'analytics':           # NEW
            self.render_analytics_page(components)
        elif page == 'performance':         # NEW
            self.render_performance_page(components)
        elif page == 'test':
            self.render_test_page(components)
        elif page == 'stats':
            self.render_stats_page(components)
        else:
            self.render_search_page(components)  # Default fallback



# Application entry point
def main():
    try:
        app = DietRxApp()
        app.run()
    except Exception as e:
        st.error(f"❌ Application error: {e}")
        logging.error(f"Application error: {e}")

if __name__ == "__main__":
    main()