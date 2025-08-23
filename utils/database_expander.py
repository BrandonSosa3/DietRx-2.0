import logging
import time
from typing import List, Dict, Set
from data.database import DatabaseManager
from data.api_clients import APIManager
import requests

class DatabaseExpander:
    def __init__(self, db_manager: DatabaseManager, api_manager: APIManager):
        self.db = db_manager
        self.api = api_manager
        self.processed_items = set()
    
    def expand_medication_database(self, target_count: int = 500) -> int:
        """Expand medication database using multiple strategies"""
        
        current_count = len(self.db.get_all_medications())
        if current_count >= target_count:
            logging.info(f"Medication database already has {current_count} entries")
            return current_count
        
        logging.info(f"Expanding medication database from {current_count} to {target_count}")
        
        # Strategy 1: Common medication classes
        added_count = self._add_common_medication_classes()
        
        # Strategy 2: RxNav API systematic expansion
        if len(self.db.get_all_medications()) < target_count:
            added_count += self._expand_from_rxnav_systematic()
        
        # Strategy 3: FDA drug database expansion
        if len(self.db.get_all_medications()) < target_count:
            added_count += self._expand_from_fda_drugs()
        
        final_count = len(self.db.get_all_medications())
        logging.info(f"Medication database expanded to {final_count} entries")
        return final_count
    
    def expand_food_database(self, target_count: int = 200) -> int:
        """Expand food database using USDA data"""
        
        current_count = len(self.db.get_all_foods())
        if current_count >= target_count:
            logging.info(f"Food database already has {current_count} entries")
            return current_count
        
        logging.info(f"Expanding food database from {current_count} to {target_count}")
        
        # Strategy 1: Common food categories
        added_count = self._add_common_food_categories()
        
        # Strategy 2: USDA systematic expansion
        if len(self.db.get_all_foods()) < target_count:
            added_count += self._expand_from_usda_systematic()
        
        final_count = len(self.db.get_all_foods())
        logging.info(f"Food database expanded to {final_count} entries")
        return final_count
    
    def _add_common_medication_classes(self) -> int:
        """Add medications by therapeutic class"""
        
        medication_classes = {
            # Pain & Inflammation
            "NSAIDs": ["Ibuprofen", "Naproxen", "Diclofenac", "Celecoxib", "Meloxicam", "Indomethacin"],
            "Analgesics": ["Acetaminophen", "Tramadol", "Codeine", "Morphine", "Oxycodone", "Hydrocodone"],
            
            # Heart & Blood Pressure
            "ACE Inhibitors": ["Lisinopril", "Enalapril", "Captopril", "Benazepril", "Ramipril"],
            "Beta Blockers": ["Metoprolol", "Atenolol", "Propranolol", "Carvedilol", "Bisoprolol"],
            "Calcium Channel Blockers": ["Amlodipine", "Nifedipine", "Diltiazem", "Verapamil"],
            "Diuretics": ["Hydrochlorothiazide", "Furosemide", "Spironolactone", "Chlorthalidone"],
            
            # Cholesterol
            "Statins": ["Atorvastatin", "Simvastatin", "Rosuvastatin", "Pravastatin", "Lovastatin"],
            
            # Diabetes
            "Diabetes": ["Metformin", "Glipizide", "Glyburide", "Pioglitazone", "Sitagliptin", "Insulin"],
            
            # Mental Health
            "SSRIs": ["Sertraline", "Fluoxetine", "Escitalopram", "Paroxetine", "Citalopram"],
            "Benzodiazepines": ["Lorazepam", "Alprazolam", "Clonazepam", "Diazepam", "Temazepam"],
            "Antipsychotics": ["Quetiapine", "Risperidone", "Olanzapine", "Aripiprazole"],
            
            # Antibiotics
            "Penicillins": ["Amoxicillin", "Ampicillin", "Penicillin"],
            "Fluoroquinolones": ["Ciprofloxacin", "Levofloxacin", "Moxifloxacin"],
            "Macrolides": ["Azithromycin", "Clarithromycin", "Erythromycin"],
            "Tetracyclines": ["Doxycycline", "Tetracycline", "Minocycline"],
            
            # Stomach & GI
            "PPIs": ["Omeprazole", "Pantoprazole", "Esomeprazole", "Lansoprazole"],
            "H2 Blockers": ["Ranitidine", "Famotidine", "Cimetidine"],
            
            # Blood Thinners
            "Anticoagulants": ["Warfarin", "Rivaroxaban", "Apixaban", "Dabigatran"],
            
            # Thyroid
            "Thyroid": ["Levothyroxine", "Methimazole", "Propylthiouracil"],
            
            # Seizure/Nerve Pain
            "Anticonvulsants": ["Gabapentin", "Pregabalin", "Phenytoin", "Carbamazepine", "Lamotrigine"]
        }
        
        added_count = 0
        for drug_class, medications in medication_classes.items():
            for med_name in medications:
                if med_name not in self.processed_items:
                    try:
                        self.db.insert_medication(
                            name=med_name,
                            generic_name=med_name,
                            drug_class=drug_class
                        )
                        self.processed_items.add(med_name)
                        added_count += 1
                    except Exception as e:
                        logging.debug(f"Error adding {med_name}: {e}")
                    
                    # Rate limiting
                    time.sleep(0.01)
        
        logging.info(f"Added {added_count} medications from therapeutic classes")
        return added_count
    
    def _add_common_food_categories(self) -> int:
        """Add foods by category"""
        
        food_categories = {
            "Fruits": [
                "Apple", "Banana", "Orange", "Grapefruit", "Lemon", "Lime", "Strawberry",
                "Blueberry", "Raspberry", "Blackberry", "Grape", "Pineapple", "Mango",
                "Papaya", "Peach", "Pear", "Plum", "Cherry", "Watermelon", "Cantaloupe",
                "Honeydew", "Kiwi", "Pomegranate", "Cranberry", "Avocado"
            ],
            "Vegetables": [
                "Spinach", "Kale", "Lettuce", "Broccoli", "Cauliflower", "Carrots",
                "Celery", "Cucumber", "Tomato", "Bell Pepper", "Onion", "Garlic",
                "Mushroom", "Zucchini", "Eggplant", "Asparagus", "Green Beans",
                "Peas", "Corn", "Potato", "Sweet Potato", "Brussels Sprouts",
                "Cabbage", "Radish", "Beets", "Turnip"
            ],
            "Proteins": [
                "Chicken", "Turkey", "Beef", "Pork", "Lamb", "Fish", "Salmon",
                "Tuna", "Cod", "Shrimp", "Crab", "Lobster", "Eggs", "Tofu",
                "Beans", "Lentils", "Chickpeas", "Quinoa", "Nuts", "Almonds",
                "Walnuts", "Peanuts", "Cashews"
            ],
            "Dairy": [
                "Milk", "Cheese", "Yogurt", "Butter", "Cream", "Ice Cream",
                "Cottage Cheese", "Sour Cream", "Mozzarella", "Cheddar",
                "Swiss Cheese", "Parmesan"
            ],
            "Grains": [
                "Rice", "Bread", "Pasta", "Oats", "Wheat", "Barley", "Quinoa",
                "Cereal", "Crackers", "Bagel", "Tortilla", "Couscous"
            ],
            "Beverages": [
                "Coffee", "Tea", "Green Tea", "Black Tea", "Herbal Tea",
                "Soda", "Juice", "Water", "Wine", "Beer", "Alcohol",
                "Energy Drink", "Sports Drink"
            ],
            "Herbs & Spices": [
                "Ginger", "Turmeric", "Cinnamon", "Basil", "Oregano", "Thyme",
                "Rosemary", "Parsley", "Cilantro", "Dill", "Sage", "Mint",
                "Black Pepper", "Cayenne", "Paprika", "Cumin", "Garlic Powder"
            ]
        }
        
        added_count = 0
        for category, foods in food_categories.items():
            for food_name in foods:
                if food_name not in self.processed_items:
                    try:
                        self.db.insert_food(
                            name=food_name,
                            category=category
                        )
                        self.processed_items.add(food_name)
                        added_count += 1
                    except Exception as e:
                        logging.debug(f"Error adding {food_name}: {e}")
                    
                    time.sleep(0.01)
        
        logging.info(f"Added {added_count} foods from categories")
        return added_count
    
    def _expand_from_rxnav_systematic(self, limit: int = 200) -> int:
        """Systematically expand from RxNav API"""
        # This would query RxNav for additional medications
        # For now, return 0 to keep it simple
        logging.info("RxNav systematic expansion not implemented yet")
        return 0
    
    def _expand_from_fda_drugs(self, limit: int = 100) -> int:
        """Expand from FDA drug database"""
        # This would query FDA for additional medications
        # For now, return 0 to keep it simple
        logging.info("FDA systematic expansion not implemented yet")
        return 0
    
    def _expand_from_usda_systematic(self, limit: int = 100) -> int:
        """Systematically expand from USDA"""
        # This would query USDA for additional foods
        # For now, return 0 to keep it simple
        logging.info("USDA systematic expansion not implemented yet")
        return 0