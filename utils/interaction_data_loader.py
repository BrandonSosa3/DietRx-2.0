import logging
from data.database import DatabaseManager

class InteractionDataLoader:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def load_common_interactions(self):
        """Load well-documented food-drug interactions"""
        
        # Critical interactions to avoid
        critical_interactions = [
            # Warfarin interactions
            ("Warfarin", "Spinach", "caution", "metabolism", 
             "High vitamin K content can reduce warfarin effectiveness",
             "May require INR monitoring and dose adjustment",
             "Maintain consistent vitamin K intake", "established", "FDA"),
            
            ("Warfarin", "Kale", "caution", "metabolism",
             "Very high vitamin K content can significantly reduce warfarin effectiveness", 
             "INR may drop below therapeutic range",
             "Limit intake or maintain very consistent amounts", "established", "FDA"),
            
            # Grapefruit interactions
            ("Atorvastatin", "Grapefruit", "avoid", "metabolism",
             "Grapefruit inhibits CYP3A4 enzyme, increasing statin levels",
             "Increased risk of muscle damage and liver toxicity",
             "Avoid grapefruit entirely while taking statins", "established", "FDA"),
            
            ("Simvastatin", "Grapefruit", "avoid", "metabolism",
             "Grapefruit dramatically increases simvastatin blood levels",
             "High risk of rhabdomyolysis and liver damage", 
             "Complete avoidance recommended", "established", "FDA"),
            
            # Calcium interactions
            ("Ciprofloxacin", "Milk", "caution", "absorption",
             "Calcium binds to ciprofloxacin, reducing absorption",
             "Reduced antibiotic effectiveness",
             "Take antibiotic 2 hours before or 6 hours after dairy", "established", "FDA"),
            
            ("Doxycycline", "Milk", "caution", "absorption",
             "Calcium and magnesium reduce tetracycline absorption",
             "Antibiotic may be less effective",
             "Separate by 2-3 hours from dairy products", "established", "FDA"),
            
            # Tyramine interactions (MAOIs)
            ("Sertraline", "Cheese", "caution", "metabolism",
             "Aged cheeses contain tyramine which can interact with some antidepressants",
             "Potential for increased blood pressure",
             "Limit aged cheeses, monitor for headaches", "probable", "Medical literature"),
            
            # Iron interactions
            ("Lisinopril", "Spinach", "safe", "absorption",
             "No significant interaction between ACE inhibitors and leafy greens",
             "No adverse effects expected",
             "No special precautions needed", "established", "Clinical studies"),
            
            # Coffee/caffeine interactions
            ("Ciprofloxacin", "Coffee", "caution", "metabolism",
             "Ciprofloxacin reduces caffeine metabolism",
             "May experience increased caffeine effects (jitters, insomnia)",
             "Reduce caffeine intake while taking ciprofloxacin", "established", "FDA"),
            
            # More common medications
            ("Metformin", "Grapefruit", "safe", "metabolism",
             "No significant interaction between metformin and grapefruit",
             "No adverse effects expected",
             "No special precautions needed", "established", "Clinical studies"),
            
            ("Ibuprofen", "Milk", "safe", "absorption",
             "Taking ibuprofen with food/milk may reduce stomach irritation",
             "May help prevent gastric side effects",
             "Taking with food is actually recommended", "established", "FDA"),
            
            ("Aspirin", "Grapefruit", "safe", "metabolism",
             "No significant interaction between aspirin and grapefruit",
             "No adverse effects expected", 
             "No special precautions needed", "established", "Clinical studies"),
            
            # Omeprazole interactions
            ("Omeprazole", "Coffee", "caution", "absorption",
             "PPIs can affect absorption of certain nutrients",
             "Long-term use may affect B12 and magnesium levels",
             "Monitor nutritional status with long-term use", "probable", "Medical literature"),
        ]
        
        # Load critical interactions
        for interaction_data in critical_interactions:
            try:
                self.db.insert_known_interaction(*interaction_data)
                logging.debug(f"Loaded interaction: {interaction_data[0]} + {interaction_data[1]}")
            except Exception as e:
                logging.error(f"Error loading interaction {interaction_data[0]} + {interaction_data[1]}: {e}")
        
        logging.info(f"Loaded {len(critical_interactions)} known interactions")
        return len(critical_interactions)
    
    def get_interaction_stats(self):
        """Get statistics about loaded interactions"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Count by severity
            cursor.execute("SELECT severity, COUNT(*) FROM known_interactions GROUP BY severity")
            severity_counts = dict(cursor.fetchall())
            
            # Total count
            cursor.execute("SELECT COUNT(*) FROM known_interactions")
            total_count = cursor.fetchone()[0]
            
            return {
                'total': total_count,
                'by_severity': severity_counts
            }
            
        except Exception as e:
            logging.error(f"Error getting interaction stats: {e}")
            return {'total': 0, 'by_severity': {}}
        finally:
            conn.close()