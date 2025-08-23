import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import sqlite3
from data.database import DatabaseManager
from collections import defaultdict, Counter
import json

class AnalyticsEngine:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
    def generate_comprehensive_analytics(self) -> Dict:
        """Generate comprehensive analytics for dashboard"""
        try:
            # Get all data for analysis
            medications = self.db.get_all_medications()
            foods = self.db.get_all_foods()
            interactions = self._get_all_interactions()
            
            analytics = {
                'overview_stats': self._calculate_overview_stats(medications, foods, interactions),
                'drug_class_analysis': self._analyze_drug_classes(medications, interactions),
                'interaction_patterns': self._analyze_interaction_patterns(interactions),
                'severity_distribution': self._analyze_severity_distribution(interactions),
                'food_category_analysis': self._analyze_food_categories(foods, interactions),
                'risk_assessment_matrix': self._create_risk_matrix(interactions),
                'temporal_analysis': self._analyze_temporal_patterns(),
                'prediction_metrics': self._calculate_prediction_metrics(interactions),
                'data_quality_metrics': self._assess_data_quality(medications, foods, interactions)
            }
            
            return analytics
            
        except Exception as e:
            logging.error(f"Error generating analytics: {e}")
            return self._get_fallback_analytics()
    
    def _get_all_interactions(self) -> List[Dict]:
        """Get all known interactions from database"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM known_interactions")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"Error getting interactions: {e}")
            return []
        finally:
            conn.close()
    
    def _calculate_overview_stats(self, medications: List[Dict], foods: List[Dict], interactions: List[Dict]) -> Dict:
        """Calculate high-level overview statistics"""
        
        # Basic counts
        total_meds = len(medications)
        total_foods = len(foods)
        total_interactions = len(interactions)
        
        # Drug classes
        drug_classes = set()
        for med in medications:
            if med.get('drug_class'):
                drug_classes.add(med['drug_class'])
        
        # Food categories
        food_categories = set()
        for food in foods:
            if food.get('category'):
                food_categories.add(food['category'])
        
        # Interaction severity breakdown
        severity_counts = Counter()
        for interaction in interactions:
            severity_counts[interaction.get('severity', 'unknown')] += 1
        
        # Coverage analysis
        meds_with_interactions = set(i.get('medication_name') for i in interactions)
        foods_with_interactions = set(i.get('food_name') for i in interactions)
        
        coverage_rate = (len(meds_with_interactions) + len(foods_with_interactions)) / (total_meds + total_foods) if (total_meds + total_foods) > 0 else 0
        
        return {
            'total_medications': total_meds,
            'total_foods': total_foods,
            'total_interactions': total_interactions,
            'drug_classes_count': len(drug_classes),
            'food_categories_count': len(food_categories),
            'severity_breakdown': dict(severity_counts),
            'interaction_coverage_rate': round(coverage_rate * 100, 1),
            'meds_with_interactions': len(meds_with_interactions),
            'foods_with_interactions': len(foods_with_interactions)
        }
    
    def _analyze_drug_classes(self, medications: List[Dict], interactions: List[Dict]) -> Dict:
        """Analyze interaction patterns by drug class"""
        
        # Group medications by class
        class_to_meds = defaultdict(list)
        for med in medications:
            drug_class = med.get('drug_class', 'Unclassified')
            class_to_meds[drug_class].append(med['name'])
        
        # Count interactions by drug class
        class_interactions = defaultdict(lambda: {'total': 0, 'avoid': 0, 'caution': 0, 'safe': 0})
        
        for interaction in interactions:
            med_name = interaction.get('medication_name')
            severity = interaction.get('severity', 'unknown')
            
            # Find the drug class for this medication
            med_class = 'Unclassified'
            for med in medications:
                if med['name'] == med_name:
                    med_class = med.get('drug_class', 'Unclassified')
                    break
            
            class_interactions[med_class]['total'] += 1
            if severity in class_interactions[med_class]:
                class_interactions[med_class][severity] += 1
        
        # Calculate risk scores for each class
        class_risk_scores = {}
        for drug_class, counts in class_interactions.items():
            if counts['total'] > 0:
                risk_score = (counts.get('avoid', 0) * 3 + counts.get('caution', 0) * 2 + counts.get('safe', 0) * 1) / counts['total']
                class_risk_scores[drug_class] = round(risk_score, 2)
        
        # Sort by risk score
        sorted_classes = sorted(class_risk_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'class_distribution': dict(class_to_meds),
            'interaction_counts_by_class': dict(class_interactions),
            'risk_scores': class_risk_scores,
            'highest_risk_classes': sorted_classes[:5],
            'total_classes': len(class_to_meds)
        }
    
    def _analyze_interaction_patterns(self, interactions: List[Dict]) -> Dict:
        """Analyze patterns in interactions"""
        
        # Interaction types
        interaction_types = Counter()
        for interaction in interactions:
            interaction_types[interaction.get('interaction_type', 'unknown')] += 1
        
        # Evidence levels
        evidence_levels = Counter()
        for interaction in interactions:
            evidence_levels[interaction.get('evidence_level', 'unknown')] += 1
        
        # Most common food-drug pairs
        common_pairs = Counter()
        for interaction in interactions:
            med = interaction.get('medication_name', 'Unknown')
            food = interaction.get('food_name', 'Unknown')
            common_pairs[f"{med} + {food}"] += 1
        
        # Mechanism analysis
        mechanisms = Counter()
        for interaction in interactions:
            mechanism = interaction.get('mechanism', 'Unknown mechanism')
            # Extract key terms from mechanism
            key_terms = self._extract_mechanism_keywords(mechanism)
            for term in key_terms:
                mechanisms[term] += 1
        
        return {
            'interaction_types': dict(interaction_types),
            'evidence_levels': dict(evidence_levels),
            'most_common_pairs': dict(common_pairs.most_common(10)),
            'mechanism_keywords': dict(mechanisms.most_common(15)),
            'total_unique_pairs': len(common_pairs)
        }
    
    def _extract_mechanism_keywords(self, mechanism: str) -> List[str]:
        """Extract key terms from interaction mechanisms"""
        if not mechanism:
            return []
        
        # Common pharmacological terms to look for
        key_terms = [
            'absorption', 'metabolism', 'CYP3A4', 'enzyme', 'inhibition',
            'vitamin K', 'calcium', 'binding', 'effectiveness', 'levels',
            'blood', 'concentration', 'clearance', 'bioavailability'
        ]
        
        mechanism_lower = mechanism.lower()
        found_terms = []
        
        for term in key_terms:
            if term.lower() in mechanism_lower:
                found_terms.append(term)
        
        return found_terms
    
    def _analyze_severity_distribution(self, interactions: List[Dict]) -> Dict:
        """Analyze distribution of interaction severities"""
        
        severity_counts = Counter()
        severity_by_type = defaultdict(lambda: Counter())
        
        for interaction in interactions:
            severity = interaction.get('severity', 'unknown')
            interaction_type = interaction.get('interaction_type', 'unknown')
            
            severity_counts[severity] += 1
            severity_by_type[interaction_type][severity] += 1
        
        # Calculate percentages
        total = sum(severity_counts.values())
        severity_percentages = {}
        for severity, count in severity_counts.items():
            severity_percentages[severity] = round((count / total) * 100, 1) if total > 0 else 0
        
        return {
            'severity_counts': dict(severity_counts),
            'severity_percentages': severity_percentages,
            'severity_by_interaction_type': dict(severity_by_type),
            'total_interactions': total
        }
    
    def _analyze_food_categories(self, foods: List[Dict], interactions: List[Dict]) -> Dict:
        """Analyze interaction patterns by food category"""
        
        # Group foods by category
        category_to_foods = defaultdict(list)
        for food in foods:
            category = food.get('category', 'Unclassified')
            category_to_foods[category].append(food['name'])
        
        # Count interactions by food category
        category_interactions = defaultdict(lambda: Counter())
        
        for interaction in interactions:
            food_name = interaction.get('food_name')
            severity = interaction.get('severity', 'unknown')
            
            # Find the category for this food
            food_category = 'Unclassified'
            for food in foods:
                if food['name'] == food_name:
                    food_category = food.get('category', 'Unclassified')
                    break
            
            category_interactions[food_category][severity] += 1
        
        # Calculate interaction rates for each category
        category_stats = {}
        for category, foods_list in category_to_foods.items():
            interactions_count = sum(category_interactions[category].values())
            foods_count = len(foods_list)
            interaction_rate = interactions_count / foods_count if foods_count > 0 else 0
            
            category_stats[category] = {
                'food_count': foods_count,
                'interaction_count': interactions_count,
                'interaction_rate': round(interaction_rate, 2),
                'severity_breakdown': dict(category_interactions[category])
            }
        
        return {
            'category_distribution': dict(category_to_foods),
            'category_stats': category_stats,
            'total_categories': len(category_to_foods)
        }
    
    def _create_risk_matrix(self, interactions: List[Dict]) -> Dict:
        """Create a risk assessment matrix"""
        
        # Create matrix of medications vs foods with risk levels
        risk_matrix = defaultdict(dict)
        medication_risk_scores = defaultdict(list)
        food_risk_scores = defaultdict(list)
        
        severity_scores = {'avoid': 3, 'caution': 2, 'safe': 1}
        
        for interaction in interactions:
            med = interaction.get('medication_name', 'Unknown')
            food = interaction.get('food_name', 'Unknown')
            severity = interaction.get('severity', 'safe')
            
            score = severity_scores.get(severity, 1)
            risk_matrix[med][food] = {'severity': severity, 'score': score}
            
            medication_risk_scores[med].append(score)
            food_risk_scores[food].append(score)
        
        # Calculate average risk scores
        med_avg_scores = {}
        for med, scores in medication_risk_scores.items():
            med_avg_scores[med] = round(np.mean(scores), 2)
        
        food_avg_scores = {}
        for food, scores in food_risk_scores.items():
            food_avg_scores[food] = round(np.mean(scores), 2)
        
        # Find highest risk combinations
        high_risk_combinations = []
        for med, foods in risk_matrix.items():
            for food, data in foods.items():
                if data['score'] >= 2.5:  # Caution or above
                    high_risk_combinations.append({
                        'medication': med,
                        'food': food,
                        'severity': data['severity'],
                        'score': data['score']
                    })
        
        high_risk_combinations.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'risk_matrix': dict(risk_matrix),
            'medication_risk_scores': med_avg_scores,
            'food_risk_scores': food_avg_scores,
            'high_risk_combinations': high_risk_combinations[:10],
            'total_combinations': sum(len(foods) for foods in risk_matrix.values())
        }
    
    def _analyze_temporal_patterns(self) -> Dict:
        """Analyze temporal patterns (simulated for demo)"""
        # Since this is a resume project, we'll simulate temporal data
        
        # Simulate user query patterns over time
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
        query_counts = np.random.poisson(lam=15, size=len(dates))  # Average 15 queries per week
        
        # Simulate seasonal patterns
        seasonal_multiplier = 1 + 0.3 * np.sin(2 * np.pi * np.arange(len(dates)) / 52)
        query_counts = (query_counts * seasonal_multiplier).astype(int)
        
        # Most common query patterns (simulated)
        common_queries = {
            'warfarin + vitamin k foods': 45,
            'statins + grapefruit': 38,
            'antibiotics + dairy': 32,
            'blood pressure meds + potassium': 28,
            'diabetes medication + alcohol': 25
        }
        
        return {
            'weekly_query_counts': query_counts.tolist(),
            'query_dates': [d.strftime('%Y-%m-%d') for d in dates],
            'total_simulated_queries': int(np.sum(query_counts)),
            'average_weekly_queries': round(np.mean(query_counts), 1),
            'peak_query_week': dates[np.argmax(query_counts)].strftime('%Y-%m-%d'),
            'common_query_patterns': common_queries
        }
    
    def _calculate_prediction_metrics(self, interactions: List[Dict]) -> Dict:
        """Calculate metrics for interaction prediction accuracy"""
        
        # Simulate prediction accuracy metrics for demo
        total_predictions = len(interactions)
        
        # Simulate confidence distributions
        high_confidence = int(total_predictions * 0.6)  # 60% high confidence
        medium_confidence = int(total_predictions * 0.3)  # 30% medium confidence  
        low_confidence = total_predictions - high_confidence - medium_confidence
        
        # Simulate accuracy by evidence level
        evidence_accuracy = {
            'established': 0.95,
            'probable': 0.85,
            'possible': 0.70
        }
        
        # Calculate overall system confidence
        evidence_counts = Counter()
        for interaction in interactions:
            evidence_counts[interaction.get('evidence_level', 'possible')] += 1
        
        weighted_accuracy = 0
        total_weight = 0
        for evidence, accuracy in evidence_accuracy.items():
            count = evidence_counts.get(evidence, 0)
            weighted_accuracy += accuracy * count
            total_weight += count
        
        overall_accuracy = weighted_accuracy / total_weight if total_weight > 0 else 0.8
        
        return {
            'total_predictions': total_predictions,
            'confidence_distribution': {
                'high': high_confidence,
                'medium': medium_confidence,
                'low': low_confidence
            },
            'accuracy_by_evidence': evidence_accuracy,
            'overall_system_accuracy': round(overall_accuracy, 3),
            'prediction_coverage': round((total_predictions / 1000) * 100, 1)  # Assuming 1000 possible combinations
        }
    
    def _assess_data_quality(self, medications: List[Dict], foods: List[Dict], interactions: List[Dict]) -> Dict:
        """Assess data quality metrics"""
        
        # Check completeness
        meds_with_class = sum(1 for med in medications if med.get('drug_class'))
        foods_with_category = sum(1 for food in foods if food.get('category'))
        interactions_with_mechanism = sum(1 for interaction in interactions if interaction.get('mechanism'))
        
        # Check for missing data
        missing_mechanisms = sum(1 for interaction in interactions if not interaction.get('mechanism'))
        missing_timing = sum(1 for interaction in interactions if not interaction.get('timing_recommendation'))
        
        # Data completeness scores
        med_completeness = (meds_with_class / len(medications)) * 100 if medications else 0
        food_completeness = (foods_with_category / len(foods)) * 100 if foods else 0
        interaction_completeness = (interactions_with_mechanism / len(interactions)) * 100 if interactions else 0
        
        return {
            'medication_completeness': round(med_completeness, 1),
            'food_completeness': round(food_completeness, 1),
            'interaction_completeness': round(interaction_completeness, 1),
            'missing_data_counts': {
                'mechanisms': missing_mechanisms,
                'timing_recommendations': missing_timing
            },
            'data_quality_score': round((med_completeness + food_completeness + interaction_completeness) / 3, 1),
            'total_data_points': len(medications) + len(foods) + len(interactions)
        }
    
    def _get_fallback_analytics(self) -> Dict:
        """Fallback analytics if main analysis fails"""
        return {
            'overview_stats': {
                'total_medications': 0,
                'total_foods': 0,
                'total_interactions': 0,
                'error': 'Analytics generation failed'
            }
        }

    def generate_performance_metrics(self) -> Dict:
        """Generate system performance metrics"""
        
        # Database size metrics
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]
            
            # Get table sizes
            table_sizes = {}
            tables = ['medications', 'foods', 'known_interactions', 'api_cache']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                table_sizes[table] = cursor.fetchone()[0]
            
            return {
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'table_sizes': table_sizes,
                'cache_hit_rate': 0.85,  # Simulated
                'average_query_time_ms': 15,  # Simulated
                'system_uptime': '99.9%'  # Simulated
            }
            
        except Exception as e:
            logging.error(f"Error generating performance metrics: {e}")
            return {'error': 'Could not generate performance metrics'}
        finally:
            conn.close()