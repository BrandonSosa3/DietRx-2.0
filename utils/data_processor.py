import logging
from typing import List, Dict, Set
from data.database import DatabaseManager
from data.api_clients import APIManager
import time

class DataProcessor:
    def __init__(self, db_manager: DatabaseManager, api_manager: APIManager):
        self.db = db_manager
        self.api = api_manager
        self.processed_drugs = set()
        self.processed_foods = set()


    def _process_medication(self, med_name: str) -> bool:
        """Process a single medication - prioritize simple names"""
        if med_name in self.processed_drugs:
            return False

        # ALWAYS insert the simple name first, regardless of API results
        try:
            # Start by inserting the simple name we want
            self.db.insert_medication(name=med_name)
            self.processed_drugs.add(med_name)
            logging.debug(f"Added simple medication: {med_name}")
            
            # Now try to enhance with API data, but don't add complex names
            try:
                drug_results = self.api.search_all_drugs(med_name)
                
                # Look for additional simple brand names only
                brand_names = []
                drug_class = None
                
                # Process RxNav results
                rxnav_results = drug_results.get('rxnav', [])
                for result in rxnav_results:
                    result_name = result.get('name', '').strip()
                    tty = result.get('tty', '')
                    
                    # Only add very simple brand names
                    if tty == 'BN' and len(result_name.split()) <= 2 and result_name != med_name:
                        if not any(char.isdigit() for char in result_name):  # No dosages
                            brand_names.append(result_name)
                
                # Process FDA results for brand names
                fda_results = drug_results.get('fda', [])
                for result in fda_results[:1]:
                    if 'openfda' in result:
                        openfda = result['openfda']
                        
                        if 'brand_name' in openfda:
                            for brand in openfda['brand_name']:
                                # Only add simple brand names
                                if (len(brand.split()) <= 2 and 
                                    brand != med_name and 
                                    not any(char.isdigit() for char in brand) and
                                    '[' not in brand and ']' not in brand):
                                    brand_names.append(brand)
                        
                        if 'pharm_class_epc' in openfda and not drug_class:
                            drug_class = openfda['pharm_class_epc'][0] if openfda['pharm_class_epc'] else None
                
                # Update the medication with additional info if we found any
                if brand_names or drug_class:
                    # We'll update this by deleting and reinserting with more info
                    conn = self.db.get_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute("DELETE FROM medications WHERE name = ?", (med_name,))
                    conn.commit()
                    conn.close()
                    
                    self.db.insert_medication(
                        name=med_name,
                        generic_name=med_name,  # Use the simple name as generic too
                        brand_names=list(set(brand_names))[:3] if brand_names else None,  # Limit to 3
                        drug_class=drug_class
                    )
                    
            except Exception as api_error:
                logging.debug(f"API enhancement failed for {med_name}, keeping simple entry: {api_error}")
            
            return True
            
        except Exception as e:
            logging.debug(f"Error processing medication {med_name}: {e}")
            return False

    def _process_food(self, food_name: str) -> bool:
        """Process a single food item"""
        if food_name in self.processed_foods:
            return False

        try:
            # Search food APIs
            food_results = self.api.search_all_foods(food_name)
            
            # Extract information
            category = None
            aliases = []
            nutritional_info = {}
            
            # Process USDA data
            usda_results = food_results.get('usda', [])
            if usda_results:
                for result in usda_results[:1]:  # Take first result
                    if 'foodCategory' in result:
                        category = result['foodCategory']
                    if 'description' in result:
                        description = result['description']
                        # Extract simple aliases from description
                        if ',' in description:
                            potential_aliases = [alias.strip() for alias in description.split(',')[:3]]
                            # Only add simple aliases (not long descriptions)
                            for alias in potential_aliases:
                                if len(alias.split()) <= 3 and alias.lower() != food_name.lower():
                                    aliases.append(alias)
                    
                    # Skip complex nutritional info for now to keep it simple
            
            # Process Open Food Facts data
            openfood_results = food_results.get('openfood', [])
            if openfood_results and not category:
                for result in openfood_results[:1]:
                    if 'categories' in result:
                        categories = result['categories']
                        # Extract first category
                        if categories:
                            category = categories.split(',')[0].strip()
                    if 'product_name' in result:
                        product_name = result['product_name']
                        if product_name and product_name != food_name and len(product_name.split()) <= 3:
                            aliases.append(product_name)

            # Always insert the original search term as the primary name
            self.db.insert_food(
                name=food_name,  # Use the simple search term as primary name
                category=category,
                aliases=list(set(aliases)) if aliases else None,
                nutritional_info=None  # Keep it simple for now
            )
            
            self.processed_foods.add(food_name)
            logging.debug(f"Processed food: {food_name}")
            return True
            
        except Exception as e:
            logging.debug(f"Error processing food {food_name}: {e}")
            # Still add to database with minimal info
            try:
                self.db.insert_food(name=food_name)
                self.processed_foods.add(food_name)
                return True
            except:
                return False
    
    def _add_fallback_medications(self):
        """Add medications manually - this is our primary data source"""
        fallback_meds = [
            ("Ibuprofen", "Ibuprofen", ["Advil", "Motrin"], "NSAID"),
            ("Acetaminophen", "Acetaminophen", ["Tylenol"], "Analgesic"),
            ("Aspirin", "Aspirin", ["Bayer"], "NSAID"),
            ("Metformin", "Metformin", ["Glucophage"], "Antidiabetic"),
            ("Lisinopril", "Lisinopril", ["Prinivil", "Zestril"], "ACE Inhibitor"),
            ("Omeprazole", "Omeprazole", ["Prilosec"], "Proton Pump Inhibitor"),
            ("Sertraline", "Sertraline", ["Zoloft"], "SSRI"),
            ("Amoxicillin", "Amoxicillin", ["Amoxil"], "Antibiotic"),
            ("Warfarin", "Warfarin", ["Coumadin"], "Anticoagulant"),
            ("Atorvastatin", "Atorvastatin", ["Lipitor"], "Statin"),
            ("Fluoxetine", "Fluoxetine", ["Prozac"], "SSRI"),
            ("Simvastatin", "Simvastatin", ["Zocor"], "Statin"),
            ("Losartan", "Losartan", ["Cozaar"], "ARB"),
            ("Gabapentin", "Gabapentin", ["Neurontin"], "Anticonvulsant"),
            ("Tramadol", "Tramadol", ["Ultram"], "Opioid"),
            ("Citalopram", "Citalopram", ["Celexa"], "SSRI"),
            ("Naproxen", "Naproxen", ["Aleve"], "NSAID"),
            ("Prednisone", "Prednisone", ["Deltasone"], "Corticosteroid")
        ]
        
        for name, generic, brands, drug_class in fallback_meds:
            if name not in self.processed_drugs:
                try:
                    self.db.insert_medication(
                        name=name,
                        generic_name=generic,
                        brand_names=brands,
                        drug_class=drug_class
                    )
                    self.processed_drugs.add(name)
                    logging.debug(f"Added fallback medication: {name}")
                except Exception as e:
                    logging.debug(f"Error adding fallback medication {name}: {e}")
        
        logging.info(f"Added {len(fallback_meds)} fallback medications")

    def _add_fallback_foods(self):
        """Add foods manually if API calls fail"""
        fallback_foods = [
            ("Grapefruit", "Citrus Fruits", ["Pink grapefruit", "White grapefruit", "Ruby red grapefruit"]),
            ("Spinach", "Leafy Greens", ["Baby spinach", "Fresh spinach", "Raw spinach"]),
            ("Milk", "Dairy", ["Whole milk", "2% milk", "Skim milk"]),
            ("Coffee", "Beverages", ["Black coffee", "Espresso", "Brewed coffee"]),
            ("Banana", "Fruits", ["Yellow banana", "Ripe banana", "Fresh banana"]),
            ("Broccoli", "Vegetables", ["Fresh broccoli", "Broccoli florets", "Steamed broccoli"]),
            ("Chicken", "Meat", ["Chicken breast", "Chicken thigh", "Grilled chicken"]),
            ("Rice", "Grains", ["White rice", "Brown rice", "Jasmine rice"]),
            ("Orange", "Citrus Fruits", ["Fresh orange", "Navel orange", "Blood orange"]),
            ("Kale", "Leafy Greens", ["Fresh kale", "Baby kale", "Curly kale"]),
            ("Cheese", "Dairy", ["Cheddar cheese", "Swiss cheese", "Mozzarella"]),
            ("Green tea", "Beverages", ["Matcha", "Sencha", "Green tea bags"])
        ]
        
        for name, category, aliases in fallback_foods:
            if name not in self.processed_foods:
                try:
                    self.db.insert_food(
                        name=name,
                        category=category,
                        aliases=aliases
                    )
                    self.processed_foods.add(name)
                    logging.debug(f"Added fallback food: {name}")
                except Exception as e:
                    logging.debug(f"Error adding fallback food {name}: {e}")
        
        logging.info("Added fallback foods")
    
    def update_medication_from_api(self, med_name: str) -> bool:
        """Update/add a medication from API if not in database"""
        return self._process_medication(med_name)
    
    def update_food_from_api(self, food_name: str) -> bool:
        """Update/add a food from API if not in database"""
        return self._process_food(food_name)
    
    def get_medication_names(self) -> List[str]:
        """Get all medication names for fuzzy matching"""
        medications = self.db.get_all_medications()
        names = set()
        
        for med in medications:
            names.add(med['name'])
            if med.get('generic_name'):
                names.add(med['generic_name'])
            if med.get('brand_names'):
                names.update(med['brand_names'])
        
        return sorted(list(names))
    
    def get_food_names(self) -> List[str]:
        """Get all food names for fuzzy matching"""
        foods = self.db.get_all_foods()
        names = set()
        
        for food in foods:
            names.add(food['name'])
            if food.get('aliases'):
                names.update(food['aliases'])
        
        return sorted(list(names))

    def cleanup_complex_medication_names(self):
        """Remove overly complex medication names from database"""
        try:
            medications = self.db.get_all_medications()
            removed_count = 0
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            for med in medications:
                name = med['name']
                
                # Remove if name contains dosage info, is too long, or has brackets
                should_remove = (
                    any(char.isdigit() for char in name) or  # Contains numbers
                    len(name.split()) > 3 or  # Too many words
                    '[' in name or ']' in name or  # Has brackets
                    'MG' in name.upper() or 'ML' in name.upper()  # Has dosage units
                )
                
                if should_remove:
                    cursor.execute("DELETE FROM medications WHERE id = ?", (med['id'],))
                    removed_count += 1
                    logging.debug(f"Removed complex medication: {name}")
            
            conn.commit()
            conn.close()
            
            logging.info(f"Cleaned up {removed_count} complex medication names")
            return removed_count
            
        except Exception as e:
            logging.error(f"Error cleaning up medication names: {e}")
            return 0


    def is_database_populated(self) -> bool:
        """Check if database already has initial data"""
        try:
            medications = self.db.get_all_medications()
            foods = self.db.get_all_foods()
            
            # Check if we have interaction data
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM known_interactions")
            interaction_count = cursor.fetchone()[0]
            conn.close()
            
            # Consider populated if we have reasonable amounts of each
            has_meds = len(medications) >= 15  # At least 15 medications
            has_foods = len(foods) >= 8        # At least 8 foods  
            has_interactions = interaction_count >= 10  # At least 10 interactions
            
            logging.info(f"DB status - Meds: {len(medications)}, Foods: {len(foods)}, Interactions: {interaction_count}")
            
            return has_meds and has_foods and has_interactions
            
        except Exception as e:
            logging.error(f"Error checking database population: {e}")
            return False

    def populate_common_medications(self) -> int:
        """Populate database with common medications - only if not already done"""
        
        # Check if we already have enough medications
        existing_meds = self.db.get_all_medications()
        if len(existing_meds) >= 15:
            logging.info(f"Medications already populated ({len(existing_meds)} found)")
            return len(existing_meds)
        
        # Use fallback data as primary source for better control
        self._add_fallback_medications()
        
        # Only try a few API calls for testing, but don't let them override our clean data
        api_test_meds = ["Metformin", "Lisinopril"]  # Just test a couple
        
        for med_name in api_test_meds:
            if med_name not in self.processed_drugs:
                self._process_medication(med_name)
                time.sleep(0.5)  # Rate limiting
        
        medications_count = len(self.db.get_all_medications())
        logging.info(f"Total medications in database: {medications_count}")
        return medications_count

    def populate_common_foods(self) -> int:
        """Populate database with common foods - only if not already done"""
        
        # Check if we already have enough foods
        existing_foods = self.db.get_all_foods()
        if len(existing_foods) >= 8:
            logging.info(f"Foods already populated ({len(existing_foods)} found)")
            return len(existing_foods)
        
        # Use fallback data as primary source
        self._add_fallback_foods()
        
        # Only try a few API calls for testing
        api_test_foods = ["Banana", "Broccoli"]  # Just test a couple
        
        for food_name in api_test_foods:
            if food_name not in self.processed_foods:
                self._process_food(food_name)
                time.sleep(0.5)  # Rate limiting
        
        foods_count = len(self.db.get_all_foods())
        logging.info(f"Total foods in database: {foods_count}")
        return foods_count

    def populate_interaction_database(self) -> int:
        """Populate the interaction database with known interactions - only if needed"""
        try:
            # Check if interactions already exist
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM known_interactions")
            existing_count = cursor.fetchone()[0]
            conn.close()
            
            if existing_count >= 10:
                logging.info(f"Interactions already populated ({existing_count} found)")
                return existing_count
            
            # Import here to avoid circular imports
            from utils.interaction_data_loader import InteractionDataLoader
            
            loader = InteractionDataLoader(self.db)
            interactions_loaded = loader.load_common_interactions()
            
            logging.info(f"Populated interaction database with {interactions_loaded} interactions")
            return interactions_loaded
        except Exception as e:
            logging.error(f"Error populating interactions: {e}")
            return 0

    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics"""
        try:
            medications = self.db.get_all_medications()
            foods = self.db.get_all_foods()
            med_names = self.get_medication_names()
            food_names = self.get_food_names()
            
            # Get interaction count
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM known_interactions")
            interaction_count = cursor.fetchone()[0]
            conn.close()
            
            return {
                'total_medications': len(medications),
                'total_foods': len(foods),
                'searchable_med_names': len(med_names),
                'searchable_food_names': len(food_names),
                'total_interactions': interaction_count
            }
        except Exception as e:
            logging.error(f"Error getting database stats: {e}")
            return {}

    def expand_database(self, med_target: int = 300, food_target: int = 150) -> Dict[str, int]:
        """Expand database with comprehensive medication and food data"""
        from utils.database_expander import DatabaseExpander
        
        expander = DatabaseExpander(self.db, self.api)
        
        # Expand medications
        med_count = expander.expand_medication_database(med_target)
        
        # Expand foods  
        food_count = expander.expand_food_database(food_target)
        
        return {
            'medications': med_count,
            'foods': food_count
        }