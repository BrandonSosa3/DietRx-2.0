import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ensure_database_exists()
        self.create_tables()
    
    def ensure_database_exists(self):
        """Create database directory if it doesn't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper settings"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def create_tables(self):
        """Create all necessary tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Medications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    generic_name TEXT,
                    brand_names TEXT,  -- JSON array of brand names
                    drug_class TEXT,
                    active_ingredients TEXT,  -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Foods table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS foods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    aliases TEXT,  -- JSON array of alternative names
                    nutritional_info TEXT,  -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Cache table for API responses
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    cache_data TEXT NOT NULL,  -- JSON data
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Interactions cache (keeping your existing table)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medication_name TEXT NOT NULL,
                    food_name TEXT NOT NULL,
                    interaction_data TEXT,  -- JSON object
                    severity TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # NEW: Known interactions table - stores documented food-drug interactions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS known_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medication_name TEXT NOT NULL,
                    food_name TEXT NOT NULL,
                    severity TEXT NOT NULL,  -- 'safe', 'caution', 'avoid'
                    interaction_type TEXT,   -- 'absorption', 'metabolism', 'effectiveness', 'toxicity'
                    mechanism TEXT,          -- How the interaction works
                    clinical_effect TEXT,    -- What happens to the patient
                    timing_recommendation TEXT,  -- When to take relative to food
                    evidence_level TEXT,     -- 'established', 'probable', 'possible'
                    source TEXT,            -- Where this info came from
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(medication_name, food_name)
                )
            """)
            
            # NEW: Interaction analysis results - cache analysis results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medication_list TEXT NOT NULL,  -- JSON array of medications
                    food_list TEXT NOT NULL,        -- JSON array of foods
                    analysis_results TEXT NOT NULL, -- JSON object with full results
                    confidence_score REAL,
                    ai_analysis TEXT,              -- AI-generated analysis
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            # NEW: Drug classes table - for broader interaction rules
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drug_classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    common_interactions TEXT,  -- JSON array of common food interactions
                    monitoring_requirements TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # NEW: Food categories table - for categorical interactions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS food_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    common_drug_interactions TEXT,  -- JSON array of drug classes that interact
                    nutritional_factors TEXT,       -- JSON object with relevant nutrients
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance (existing)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_medications_name ON medications(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_foods_name ON foods(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON api_cache(cache_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions ON interaction_cache(medication_name, food_name)")
            
            # NEW: Create indexes for new tables
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_known_interactions_med ON known_interactions(medication_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_known_interactions_food ON known_interactions(food_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_known_interactions_severity ON known_interactions(severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_interaction_results_meds ON interaction_results(medication_list)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drug_classes_name ON drug_classes(class_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_food_categories_name ON food_categories(category_name)")
            
            conn.commit()
            logging.info("Database tables created successfully")
            
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def insert_medication(self, name: str, generic_name: str = None, 
                         brand_names: List[str] = None, drug_class: str = None,
                         active_ingredients: List[str] = None) -> int:
        """Insert a new medication"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO medications 
                (name, generic_name, brand_names, drug_class, active_ingredients)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                generic_name,
                json.dumps(brand_names) if brand_names else None,
                drug_class,
                json.dumps(active_ingredients) if active_ingredients else None
            ))
            
            medication_id = cursor.lastrowid
            conn.commit()
            return medication_id
            
        except sqlite3.Error as e:
            logging.error(f"Error inserting medication: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def insert_food(self, name: str, category: str = None, 
                   aliases: List[str] = None, nutritional_info: Dict = None) -> int:
        """Insert a new food item"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO foods 
                (name, category, aliases, nutritional_info)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                category,
                json.dumps(aliases) if aliases else None,
                json.dumps(nutritional_info) if nutritional_info else None
            ))
            
            food_id = cursor.lastrowid
            conn.commit()
            return food_id
            
        except sqlite3.Error as e:
            logging.error(f"Error inserting food: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_all_medications(self) -> List[Dict]:
        """Get all medications from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM medications ORDER BY name")
            rows = cursor.fetchall()
            
            medications = []
            for row in rows:
                med = dict(row)
                # Parse JSON fields
                if med['brand_names']:
                    med['brand_names'] = json.loads(med['brand_names'])
                if med['active_ingredients']:
                    med['active_ingredients'] = json.loads(med['active_ingredients'])
                medications.append(med)
            
            return medications
            
        except sqlite3.Error as e:
            logging.error(f"Error getting medications: {e}")
            return []
        finally:
            conn.close()
    
    def get_all_foods(self) -> List[Dict]:
        """Get all foods from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM foods ORDER BY name")
            rows = cursor.fetchall()
            
            foods = []
            for row in rows:
                food = dict(row)
                # Parse JSON fields
                if food['aliases']:
                    food['aliases'] = json.loads(food['aliases'])
                if food['nutritional_info']:
                    food['nutritional_info'] = json.loads(food['nutritional_info'])
                foods.append(food)
            
            return foods
            
        except sqlite3.Error as e:
            logging.error(f"Error getting foods: {e}")
            return []
        finally:
            conn.close()
    
    def cache_api_response(self, cache_key: str, data: Dict, expiry_hours: int = 24):
        """Cache API response data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(hours=expiry_hours)
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO api_cache 
                (cache_key, cache_data, expires_at)
                VALUES (?, ?, ?)
            """, (cache_key, json.dumps(data), expires_at))
            
            conn.commit()
            
        except sqlite3.Error as e:
            logging.error(f"Error caching data: {e}")
        finally:
            conn.close()
    
    def get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached API response if not expired"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT cache_data FROM api_cache 
                WHERE cache_key = ? AND expires_at > ?
            """, (cache_key, datetime.now()))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row['cache_data'])
            return None
            
        except sqlite3.Error as e:
            logging.error(f"Error getting cached data: {e}")
            return None
        finally:
            conn.close()
    
    def clean_expired_cache(self):
        """Remove expired cache entries"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM api_cache WHERE expires_at < ?
            """, (datetime.now(),))
            
            deleted = cursor.rowcount
            conn.commit()
            logging.info(f"Cleaned {deleted} expired cache entries")
            
        except sqlite3.Error as e:
            logging.error(f"Error cleaning cache: {e}")
        finally:
            conn.close()



    def insert_known_interaction(self, medication_name: str, food_name: str, 
                           severity: str, interaction_type: str = None,
                           mechanism: str = None, clinical_effect: str = None,
                           timing_recommendation: str = None, 
                           evidence_level: str = "established",
                           source: str = None) -> int:
        """Insert a known interaction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO known_interactions 
                (medication_name, food_name, severity, interaction_type, mechanism, 
                clinical_effect, timing_recommendation, evidence_level, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                medication_name, food_name, severity, interaction_type, mechanism,
                clinical_effect, timing_recommendation, evidence_level, source
            ))
            
            interaction_id = cursor.lastrowid
            conn.commit()
            return interaction_id
            
        except sqlite3.Error as e:
            logging.error(f"Error inserting interaction: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_interactions_for_medication(self, medication_name: str) -> List[Dict]:
        """Get all known interactions for a medication"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM known_interactions 
                WHERE medication_name = ?
                ORDER BY severity DESC, food_name
            """, (medication_name,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logging.error(f"Error getting interactions: {e}")
            return []
        finally:
            conn.close()

    def get_interactions_for_food(self, food_name: str) -> List[Dict]:
        """Get all known interactions for a food"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM known_interactions 
                WHERE food_name = ?
                ORDER BY severity DESC, medication_name
            """, (food_name,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logging.error(f"Error getting food interactions: {e}")
            return []
        finally:
            conn.close()

    def find_interactions(self, medications: List[str], foods: List[str]) -> List[Dict]:
        """Find all interactions between lists of medications and foods - case insensitive"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create placeholders for the IN clauses
            med_placeholders = ','.join(['?'] * len(medications))
            food_placeholders = ','.join(['?'] * len(foods))
            
            # Use LOWER() for case-insensitive matching
            query = f"""
                SELECT * FROM known_interactions 
                WHERE LOWER(medication_name) IN ({','.join(['LOWER(?)'] * len(medications))})
                AND LOWER(food_name) IN ({','.join(['LOWER(?)'] * len(foods))})
                ORDER BY 
                    CASE severity 
                        WHEN 'avoid' THEN 1 
                        WHEN 'caution' THEN 2 
                        WHEN 'safe' THEN 3 
                    END,
                    medication_name, food_name
            """
            
            # Convert all inputs to lowercase for matching
            all_params = [med.lower() for med in medications] + [food.lower() for food in foods]
            
            cursor.execute(query, all_params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logging.error(f"Error finding interactions: {e}")
            return []
        finally:
            conn.close()

    def cache_interaction_results(self, medications: List[str], foods: List[str], 
                                results: Dict, confidence: float, 
                                ai_analysis: str = None, expiry_hours: int = 24):
        """Cache interaction analysis results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(hours=expiry_hours)
        
        try:
            cursor.execute("""
                INSERT INTO interaction_results 
                (medication_list, food_list, analysis_results, confidence_score, ai_analysis, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                json.dumps(sorted(medications)), 
                json.dumps(sorted(foods)),
                json.dumps(results),
                confidence,
                ai_analysis,
                expires_at
            ))
            
            conn.commit()
            
        except sqlite3.Error as e:
            logging.error(f"Error caching results: {e}")
        finally:
            conn.close()


    def ensure_fda_columns_exist(self):
        """Ensure FDA-related columns exist in known_interactions table"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get existing columns
            cursor.execute("PRAGMA table_info(known_interactions)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            # Required columns for FDA data
            required_columns = {
                'source': 'TEXT DEFAULT "manual"',
                'date_added': 'TEXT DEFAULT ""',
                'original_text': 'TEXT DEFAULT ""'
            }
            
            # Add missing columns
            added_columns = []
            for col_name, col_def in required_columns.items():
                if col_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE known_interactions ADD COLUMN {col_name} {col_def}")
                    added_columns.append(col_name)
                    logging.info(f"Added column: {col_name}")
            
            conn.commit()
            
            if added_columns:
                logging.info(f"Successfully added FDA columns: {added_columns}")
            else:
                logging.info("All FDA columns already exist")
                
            return added_columns
            
        except Exception as e:
            logging.error(f"Error ensuring FDA columns: {e}")
            conn.rollback()
            return []
        finally:
            conn.close()


    def update_interactions_table_for_fda(self):
        """Update known_interactions table to support FDA data"""
        return self.ensure_fda_columns_exist()
