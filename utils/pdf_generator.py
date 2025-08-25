import io
import logging
from typing import Dict, List, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from utils.interaction_engine import AnalysisResults, Severity

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def generate_comprehensive_report(self, results: AnalysisResults, analytics_data: Optional[Dict] = None) -> bytes:
        """Generate a comprehensive PDF report with enhanced information"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        story = []
        
        # Enhanced title page
        story.extend(self._create_enhanced_title_page(results))
        story.append(PageBreak())
        
        # Executive summary with more detail
        story.extend(self._create_detailed_executive_summary(results))
        story.append(PageBreak())
        
        # Comprehensive interaction analysis
        story.extend(self._create_comprehensive_interaction_analysis(results))
        
        # Safety recommendations
        if results.interactions:
            story.append(PageBreak())
            story.extend(self._create_safety_recommendations(results))
        
        # Analytics insights
        if analytics_data:
            story.append(PageBreak())
            story.extend(self._create_analytics_insights(analytics_data))
        
        # Enhanced appendix
        story.append(PageBreak())
        story.extend(self._create_enhanced_appendix(results))
        
        # Build the PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_enhanced_title_page(self, results: AnalysisResults) -> List:
        """Create enhanced title page with more information"""
        story = []
        
        # Main title with styling
        story.append(Paragraph("COMPREHENSIVE DRUG-FOOD INTERACTION REPORT", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        # Risk assessment box
        risk_level = results.overall_risk_level.value.upper()
        risk_color = self._get_risk_color(results.overall_risk_level)
        
        story.append(Paragraph(f'<b>OVERALL RISK ASSESSMENT: <font color="{risk_color}">{risk_level}</font></b>', self.styles['Heading2']))
        story.append(Spacer(1, 30))
        
        # Enhanced report details
        report_data = [
            ['Report Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
            ['Analysis Confidence:', f"{int(results.confidence_score * 100)}% (Based on scientific evidence)"],
            ['Total Interactions Found:', f"{len(results.interactions)} documented interactions"],
            ['Medications Analyzed:', f"{len(results.medications_analyzed)} medications"],
            ['Foods Analyzed:', f"{len(results.foods_analyzed)} food items"],
            ['Critical Interactions:', str(sum(1 for i in results.interactions if i.severity == Severity.AVOID))],
            ['Caution Interactions:', str(sum(1 for i in results.interactions if i.severity == Severity.CAUTION))],
            ['Analysis Time:', results.analysis_timestamp],
        ]
        
        report_table = Table(report_data, colWidths=[2.5*inch, 3.5*inch])
        report_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.lightyellow])
        ]))
        
        story.append(report_table)
        story.append(Spacer(1, 40))
        
        # Enhanced medication and food lists
        story.append(Paragraph("ANALYZED MEDICATIONS:", self.styles['Heading3']))
        for med in results.medications_analyzed:
            story.append(Paragraph(f"• {med}", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("ANALYZED FOODS:", self.styles['Heading3']))
        for food in results.foods_analyzed:
            story.append(Paragraph(f"• {food}", self.styles['Normal']))
        
        story.append(Spacer(1, 30))
        
        # Enhanced disclaimer
        disclaimer = """
        <b>MEDICAL DISCLAIMER:</b><br/>
        This comprehensive analysis is for informational and educational purposes only. 
        It should not replace professional medical advice, diagnosis, or treatment. 
        Always consult qualified healthcare providers before making changes to medications or diet.
        Individual responses to drug-food interactions may vary based on genetics, health conditions, 
        dosage, timing, and other medications. This report is based on available scientific literature 
        and may not account for all possible interactions or individual factors.
        """
        story.append(Paragraph(disclaimer, self.styles['Normal']))
        
        return story
    
    def _create_detailed_executive_summary(self, results: AnalysisResults) -> List:
        """Create detailed executive summary"""
        story = []
        
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        # Enhanced analysis overview
        story.append(Paragraph("ANALYSIS OVERVIEW", self.styles['Heading2']))
        story.append(Paragraph(results.summary, self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Detailed findings
        story.append(Paragraph("KEY FINDINGS", self.styles['Heading2']))
        
        if results.interactions:
            # Categorize interactions
            avoid_interactions = [i for i in results.interactions if i.severity == Severity.AVOID]
            caution_interactions = [i for i in results.interactions if i.severity == Severity.CAUTION]
            safe_interactions = [i for i in results.interactions if i.severity == Severity.SAFE]
            
            findings = [
                f"• Total drug-food interactions identified: {len(results.interactions)}",
                f"• Analysis confidence level: {int(results.confidence_score * 100)}%"
            ]
            
            if avoid_interactions:
                findings.append(f"• CRITICAL: {len(avoid_interactions)} interaction(s) requiring immediate attention and avoidance")
                findings.append("  - These combinations may cause serious adverse effects")
                findings.append("  - Immediate consultation with healthcare provider recommended")
            
            if caution_interactions:
                findings.append(f"• CAUTION: {len(caution_interactions)} interaction(s) requiring monitoring")
                findings.append("  - These combinations may reduce effectiveness or cause mild side effects")
                findings.append("  - Timing adjustments or monitoring may be necessary")
            
            if safe_interactions:
                findings.append(f"• INFORMATIONAL: {len(safe_interactions)} low-risk interaction(s) noted")
                findings.append("  - These combinations are generally safe but worth awareness")
            
            for finding in findings:
                story.append(Paragraph(finding, self.styles['Normal']))
        else:
            story.append(Paragraph("• No significant drug-food interactions were identified in this analysis", self.styles['Normal']))
            story.append(Paragraph("• This suggests a generally safe profile for the analyzed combinations", self.styles['Normal']))
            story.append(Paragraph("• Continue following standard medication instructions and dietary guidelines", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # AI Analysis summary (if available)
        if hasattr(results, 'ai_analysis') and results.ai_analysis:
            story.append(Paragraph("ENHANCED AI ANALYSIS", self.styles['Heading2']))
            story.append(Paragraph(results.ai_analysis.enhanced_summary, self.styles['Normal']))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"Analysis Method: {results.ai_analysis.analysis_method}", self.styles['Normal']))
            story.append(Paragraph(f"Processing Confidence: {int(results.ai_analysis.confidence * 100)}%", self.styles['Normal']))
        
        return story
    
    def _create_comprehensive_interaction_analysis(self, results: AnalysisResults) -> List:
        """Create comprehensive interaction analysis with detailed tables"""
        story = []
        
        story.append(Paragraph("DETAILED INTERACTION ANALYSIS", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        if not results.interactions:
            story.append(Paragraph(
                "No significant drug-food interactions were identified. This indicates a generally safe "
                "profile for your analyzed medications and foods. However, always continue to follow "
                "medication instructions and consult healthcare providers for any concerns.",
                self.styles['Normal']
            ))
            return story
        
        # Group interactions by severity
        interactions_by_severity = {
            Severity.AVOID: [],
            Severity.CAUTION: [],
            Severity.SAFE: []
        }
        
        for interaction in results.interactions:
            interactions_by_severity[interaction.severity].append(interaction)
        
        # Display each severity group with enhanced details
        severity_info = {
            Severity.AVOID: ("CRITICAL INTERACTIONS - AVOID THESE COMBINATIONS", 
                           "These drug-food combinations should be completely avoided due to serious risk of adverse effects:"),
            Severity.CAUTION: ("INTERACTIONS REQUIRING CAUTION", 
                             "These combinations require careful monitoring and may need timing adjustments:"),
            Severity.SAFE: ("LOW-RISK INTERACTIONS - INFORMATIONAL", 
                          "These combinations are generally safe but included for completeness:")
        }
        
        for severity in [Severity.AVOID, Severity.CAUTION, Severity.SAFE]:
            interactions = interactions_by_severity[severity]
            if not interactions:
                continue
            
            title, description = severity_info[severity]
            
            story.append(Paragraph(title, self.styles['Heading2']))
            story.append(Paragraph(description, self.styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Enhanced interaction details for each item
            for idx, interaction in enumerate(interactions, 1):
                story.append(Paragraph(f"{idx}. {interaction.medication} + {interaction.food}", self.styles['Heading3']))
                
                # Detailed interaction information
                details = [
                    f"<b>Severity Level:</b> {interaction.severity.value.upper()}",
                    f"<b>Mechanism of Interaction:</b> {interaction.mechanism}",
                    f"<b>Clinical Effect:</b> {interaction.clinical_effect}",
                ]
                
                if interaction.timing_recommendation:
                    details.append(f"<b>Timing Guidance:</b> {interaction.timing_recommendation}")
                
                if hasattr(interaction, 'evidence_level'):
                    details.append(f"<b>Evidence Level:</b> {interaction.evidence_level}")
                
                if hasattr(interaction, 'interaction_type'):
                    details.append(f"<b>Interaction Type:</b> {interaction.interaction_type}")
                
                for detail in details:
                    story.append(Paragraph(detail, self.styles['Normal']))
                
                story.append(Spacer(1, 10))
        
        return story
    
    def _create_safety_recommendations(self, results: AnalysisResults) -> List:
        """Create enhanced safety recommendations section"""
        story = []
        
        story.append(Paragraph("SAFETY RECOMMENDATIONS & CLINICAL GUIDANCE", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        if results.recommendations:
            story.append(Paragraph("SPECIFIC RECOMMENDATIONS FOR YOUR ANALYSIS:", self.styles['Heading2']))
            
            for i, rec in enumerate(results.recommendations, 1):
                clean_rec = rec.replace("🚨", "").replace("⚠️", "").replace("📞", "").replace("✅", "").replace("**", "").strip()
                story.append(Paragraph(f"{i}. {clean_rec}", self.styles['Normal']))
            
            story.append(Spacer(1, 20))
        
        # General safety guidelines
        story.append(Paragraph("GENERAL SAFETY GUIDELINES:", self.styles['Heading2']))
        
        general_guidelines = [
            "Always take medications as prescribed by your healthcare provider",
            "Inform all healthcare providers about all medications, supplements, and dietary habits",
            "Read medication labels and patient information leaflets carefully",
            "Never stop or change medications without consulting your healthcare provider",
            "Keep a current list of all medications and supplements you take",
            "Be aware that herbal supplements can also interact with medications",
            "Consider timing: some interactions can be avoided by spacing medication and food intake",
            "Monitor for any unusual symptoms and report them to your healthcare provider",
            "Regular medication reviews with your pharmacist or doctor are recommended"
        ]
        
        for guideline in general_guidelines:
            story.append(Paragraph(f"• {guideline}", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Emergency information
        story.append(Paragraph("WHEN TO SEEK IMMEDIATE MEDICAL ATTENTION:", self.styles['Heading3']))
        
        emergency_signs = [
            "Severe allergic reactions (difficulty breathing, swelling, rash)",
            "Unusual bleeding or bruising",
            "Severe nausea, vomiting, or abdominal pain",
            "Dizziness, fainting, or rapid heartbeat",
            "Any sudden, severe, or concerning symptoms after taking medication with food"
        ]
        
        for sign in emergency_signs:
            story.append(Paragraph(f"• {sign}", self.styles['Normal']))
        
        return story
    
    def _create_analytics_insights(self, analytics_data: Dict) -> List:
        """Create analytics insights section"""
        story = []
        
        story.append(Paragraph("ANALYTICS INSIGHTS", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        # Database overview
        overview = analytics_data.get('overview_stats', {})
        if overview:
            story.append(Paragraph("DATABASE COVERAGE ANALYSIS:", self.styles['Heading2']))
            
            insights = [
                f"Total medications in database: {overview.get('total_medications', 0):,}",
                f"Total foods in database: {overview.get('total_foods', 0):,}",
                f"Known interactions documented: {overview.get('total_interactions', 0):,}",
                f"Drug classes covered: {overview.get('drug_classes_count', 0):,}",
                f"Food categories covered: {overview.get('food_categories_count', 0):,}",
                f"Interaction coverage rate: {overview.get('interaction_coverage_rate', 0):.1f}%"
            ]
            
            for insight in insights:
                story.append(Paragraph(f"• {insight}", self.styles['Normal']))
            
            story.append(Spacer(1, 15))
        
        # Data quality information
        quality_data = analytics_data.get('data_quality_metrics', {})
        if quality_data:
            story.append(Paragraph("DATA QUALITY ASSESSMENT:", self.styles['Heading2']))
            
            quality_info = [
                f"Overall data quality score: {quality_data.get('data_quality_score', 0):.1f}%",
                f"Medication data completeness: {quality_data.get('medication_completeness', 0):.1f}%",
                f"Food data completeness: {quality_data.get('food_completeness', 0):.1f}%",
                f"Interaction data completeness: {quality_data.get('interaction_completeness', 0):.1f}%"
            ]
            
            for info in quality_info:
                story.append(Paragraph(f"• {info}", self.styles['Normal']))
        
        return story
    
    def _create_enhanced_appendix(self, results: AnalysisResults) -> List:
        """Create enhanced appendix with technical details"""
        story = []
        
        story.append(Paragraph("TECHNICAL APPENDIX", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        # Methodology
        story.append(Paragraph("ANALYSIS METHODOLOGY:", self.styles['Heading2']))
        
        methodology_text = """
        This analysis uses a comprehensive database of documented drug-food interactions compiled from:
        • FDA-approved drug labeling and prescribing information
        • Peer-reviewed medical and pharmaceutical literature
        • Clinical pharmacy references and databases
        • Pharmacokinetic and pharmacodynamic studies
        • Post-market surveillance reports
        
        The analysis engine evaluates interactions based on:
        • Severity classification (Avoid, Caution, Safe)
        • Clinical evidence quality and strength
        • Documented mechanisms of action
        • Frequency and significance of reported effects
        
        Confidence scores reflect the quality and consistency of available evidence, 
        with higher scores indicating well-established interactions supported by multiple 
        high-quality sources.
        """
        
        story.append(Paragraph(methodology_text, self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Limitations
        story.append(Paragraph("ANALYSIS LIMITATIONS:", self.styles['Heading2']))
        
        limitations = [
            "Individual patient factors (genetics, kidney/liver function, age) may affect interactions",
            "Dosage amounts and timing can influence interaction severity",
            "Some interactions may be theoretical and not clinically proven",
            "New interactions may be discovered as research continues",
            "This analysis cannot account for all possible medication combinations",
            "Herbal supplements and over-the-counter medications may not be fully covered"
        ]
        
        for limitation in limitations:
            story.append(Paragraph(f"• {limitation}", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Report metadata
        story.append(Paragraph("REPORT METADATA:", self.styles['Heading2']))
        
        metadata_data = [
            ['Report Generation Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')],
            ['Analysis Engine Version:', 'DietRx Enhanced v2.0'],
            ['Database Last Updated:', 'Current'],
            ['Analysis Confidence Score:', f"{int(results.confidence_score * 100)}%"],
            ['Total Processing Time:', f"{getattr(results, 'processing_time', 'N/A')} seconds"],
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2.5*inch, 3.5*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        
        story.append(metadata_table)
        
        return story
    
    def _get_risk_color(self, severity):
        """Get color for risk level"""
        if severity == Severity.AVOID:
            return "red"
        elif severity == Severity.CAUTION:
            return "orange"
        else:
            return "green"
    
    def generate_summary_report(self, results: AnalysisResults) -> bytes:
        """Generate enhanced summary report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        story = []
        
        # Enhanced title
        story.append(Paragraph("Drug-Food Interaction Analysis Summary", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        # Key information
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", self.styles['Normal']))
        story.append(Paragraph(f"Overall Risk Level: {results.overall_risk_level.value.upper()}", self.styles['Heading2']))
        story.append(Paragraph(f"Analysis Confidence: {int(results.confidence_score * 100)}%", self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Enhanced summary
        story.append(Paragraph("SUMMARY:", self.styles['Heading3']))
        story.append(Paragraph(results.summary, self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Key interactions with more detail
        if results.interactions:
            story.append(Paragraph("KEY INTERACTIONS:", self.styles['Heading3']))
            for interaction in results.interactions[:5]:  # Top 5
                story.append(Paragraph(
                    f"• {interaction.medication} + {interaction.food} ({interaction.severity.value.upper()})",
                    self.styles['Normal']
                ))
                story.append(Paragraph(f"  Effect: {interaction.clinical_effect}", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Enhanced recommendations
        if results.recommendations:
            story.append(Paragraph("KEY RECOMMENDATIONS:", self.styles['Heading3']))
            for rec in results.recommendations[:3]:  # Top 3
                clean_rec = rec.replace("🚨", "").replace("⚠️", "").replace("📞", "").replace("✅", "").replace("**", "").strip()
                story.append(Paragraph(f"• {clean_rec}", self.styles['Normal']))
        
        # Disclaimer
        story.append(Spacer(1, 20))
        story.append(Paragraph("DISCLAIMER:", self.styles['Heading3']))
        story.append(Paragraph(
            "This summary is for informational purposes only. Always consult healthcare providers before making changes to medications or diet.",
            self.styles['Normal']
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()