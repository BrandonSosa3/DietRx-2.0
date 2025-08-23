import io
import logging
from typing import Dict, List, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from utils.interaction_engine import AnalysisResults, InteractionResult, Severity
from PIL import Image as PILImage
import base64

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
        # Color scheme for professional medical reports
        self.colors = {
            'primary': colors.Color(0.2, 0.4, 0.7),      # Professional blue
            'secondary': colors.Color(0.5, 0.5, 0.5),     # Gray
            'danger': colors.Color(0.8, 0.2, 0.2),        # Red for avoid
            'warning': colors.Color(0.9, 0.6, 0.1),       # Orange for caution
            'success': colors.Color(0.2, 0.7, 0.3),       # Green for safe
            'light_gray': colors.Color(0.95, 0.95, 0.95), # Light background
            'dark_gray': colors.Color(0.3, 0.3, 0.3)      # Dark text
        }
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        
        # Check if style exists before adding
        def add_style_safely(name, **kwargs):
            if name not in self.styles:
                self.styles.add(ParagraphStyle(name=name, **kwargs))
        
        # Title style
        add_style_safely(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.Color(0.2, 0.4, 0.7),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Subtitle style
        add_style_safely(
            'Subtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.Color(0.3, 0.3, 0.3),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        # Section header
        add_style_safely(
            'SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.Color(0.2, 0.4, 0.7),
            fontName='Helvetica-Bold'
        )
        
        # Body text
        add_style_safely(
            'BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leading=12,
            fontName='Helvetica'
        )
        
        # Warning text
        add_style_safely(
            'WarningText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.Color(0.8, 0.2, 0.2),
            fontName='Helvetica-Bold'
        )
        
        # Footer style
        add_style_safely(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        )
    
    def generate_comprehensive_report(self, results: AnalysisResults, 
                                    analytics_data: Optional[Dict] = None) -> bytes:
        """Generate a comprehensive PDF report"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build the report content
        story = []
        
        # Title page
        story.extend(self._create_title_page(results))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._create_executive_summary(results))
        story.append(PageBreak())
        
        # Detailed analysis
        story.extend(self._create_detailed_analysis(results))
        
        # Charts and visualizations
        if analytics_data:
            story.append(PageBreak())
            story.extend(self._create_charts_section(results, analytics_data))
        
        # Recommendations
        story.append(PageBreak())
        story.extend(self._create_recommendations_section(results))
        
        # Appendix
        story.append(PageBreak())
        story.extend(self._create_appendix(results))
        
        # Build the PDF
        doc.build(story)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_title_page(self, results: AnalysisResults) -> List:
        """Create the title page"""
        story = []
        
        # Main title
        story.append(Paragraph(
            "Drug-Food Interaction Analysis Report",
            self.styles['CustomTitle']
        ))
        
        story.append(Spacer(1, 30))
        
        # Subtitle with risk level
        risk_level = results.overall_risk_level.value.upper()
        risk_color = self._get_severity_color(results.overall_risk_level)
        
        story.append(Paragraph(
            f'<font color="{risk_color}">Overall Risk Level: {risk_level}</font>',
            self.styles['Subtitle']
        ))
        
        story.append(Spacer(1, 40))
        
        # Report details table
        report_data = [
            ['Report Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
            ['Analysis Confidence:', f"{int(results.confidence_score * 100)}%"],
            ['Medications Analyzed:', ', '.join(results.medications_analyzed)],
            ['Foods Analyzed:', ', '.join(results.foods_analyzed)],
            ['Total Interactions Found:', str(len(results.interactions))],
        ]
        
        report_table = Table(report_data, colWidths=[2*inch, 4*inch])
        report_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), self.colors['light_gray'])
        ]))
        
        story.append(report_table)
        story.append(Spacer(1, 60))
        
        # Important disclaimer
        disclaimer = """
        <para align="center">
        <b>IMPORTANT MEDICAL DISCLAIMER</b><br/>
        <br/>
        This report is for informational purposes only and should not replace professional medical advice. 
        Always consult your healthcare provider before making changes to medications or diet. 
        The information in this report is based on available scientific literature and may not account 
        for individual health conditions or other medications not listed.
        </para>
        """
        
        story.append(Paragraph(disclaimer, self.styles['BodyText']))
        
        return story
    
    def _create_executive_summary(self, results: AnalysisResults) -> List:
        """Create executive summary section"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Summary overview
        story.append(Paragraph("Analysis Overview", self.styles['SectionHeader']))
        story.append(Paragraph(results.summary, self.styles['BodyText']))
        story.append(Spacer(1, 15))
        
        # Key findings
        story.append(Paragraph("Key Findings", self.styles['SectionHeader']))
        
        if results.interactions:
            # Categorize interactions
            avoid_count = sum(1 for i in results.interactions if i.severity == Severity.AVOID)
            caution_count = sum(1 for i in results.interactions if i.severity == Severity.CAUTION)
            safe_count = sum(1 for i in results.interactions if i.severity == Severity.SAFE)
            
            findings = []
            if avoid_count > 0:
                findings.append(f"• {avoid_count} critical interaction(s) requiring immediate attention")
            if caution_count > 0:
                findings.append(f"• {caution_count} interaction(s) requiring careful monitoring")
            if safe_count > 0:
                findings.append(f"• {safe_count} low-risk interaction(s) identified")
            
            findings.append(f"• Analysis confidence level: {int(results.confidence_score * 100)}%")
            
            for finding in findings:
                story.append(Paragraph(finding, self.styles['BodyText']))
        else:
            story.append(Paragraph(
                "• No significant drug-food interactions were identified",
                self.styles['BodyText']
            ))
        
        story.append(Spacer(1, 15))
        
        # AI Analysis summary (if available)
        if hasattr(results, 'ai_analysis') and results.ai_analysis:
            story.append(Paragraph("AI-Enhanced Analysis", self.styles['SectionHeader']))
            story.append(Paragraph(
                results.ai_analysis.enhanced_summary,
                self.styles['BodyText']
            ))
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"AI Analysis Method: {results.ai_analysis.analysis_method}",
                self.styles['BodyText']
            ))
        
        return story
    
    def _create_detailed_analysis(self, results: AnalysisResults) -> List:
        """Create detailed interaction analysis section"""
        story = []
        
        story.append(Paragraph("Detailed Interaction Analysis", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        if not results.interactions:
            story.append(Paragraph(
                "No significant drug-food interactions were identified in your analysis. "
                "This is generally positive, but always consult your healthcare provider "
                "about any concerns regarding medication and dietary interactions.",
                self.styles['BodyText']
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
        
        # Display each severity group
        severity_info = {
            Severity.AVOID: ("Critical Interactions - Avoid", "These combinations should be avoided completely:"),
            Severity.CAUTION: ("Interactions Requiring Caution", "These combinations require careful monitoring:"),
            Severity.SAFE: ("Low-Risk Interactions", "These combinations are generally safe but noteworthy:")
        }
        
        for severity in [Severity.AVOID, Severity.CAUTION, Severity.SAFE]:
            interactions = interactions_by_severity[severity]
            if not interactions:
                continue
            
            title, description = severity_info[severity]
            
            story.append(Paragraph(title, self.styles['SectionHeader']))
            story.append(Paragraph(description, self.styles['BodyText']))
            story.append(Spacer(1, 10))
            
            # Create table for interactions
            table_data = [['Medication', 'Food', 'Mechanism', 'Clinical Effect', 'Timing Guidance']]
            
            for interaction in interactions:
                table_data.append([
                    interaction.medication,
                    interaction.food,
                    interaction.mechanism[:80] + "..." if len(interaction.mechanism) > 80 else interaction.mechanism,
                    interaction.clinical_effect[:60] + "..." if len(interaction.clinical_effect) > 60 else interaction.clinical_effect,
                    interaction.timing_recommendation[:50] + "..." if len(interaction.timing_recommendation) > 50 else interaction.timing_recommendation
                ])
            
            # Create and style the table
            interaction_table = Table(table_data, colWidths=[1.2*inch, 1*inch, 2*inch, 1.5*inch, 1.3*inch])
            
            # Base table style
            table_style = [
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['light_gray'])
            ]
            
            # Add severity-specific coloring
            severity_color = self._get_severity_color(severity)
            table_style.append(('BACKGROUND', (0, 0), (-1, 0), colors.toColor(severity_color)))
            
            interaction_table.setStyle(TableStyle(table_style))
            
            story.append(interaction_table)
            story.append(Spacer(1, 20))
        
        return story
    
    def _create_charts_section(self, results: AnalysisResults, analytics_data: Dict) -> List:
        """Create charts and visualizations section"""
        story = []
        
        story.append(Paragraph("Visual Analysis", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Severity distribution chart
        if results.interactions:
            story.extend(self._create_severity_chart(results.interactions))
            story.append(Spacer(1, 20))
        
        # Drug class analysis chart (if available)
        if analytics_data and 'drug_class_analysis' in analytics_data:
            story.extend(self._create_drug_class_chart(analytics_data['drug_class_analysis']))
        
        return story
    
    def _create_severity_chart(self, interactions: List[InteractionResult]) -> List:
        """Create severity distribution chart"""
        story = []
        
        story.append(Paragraph("Interaction Severity Distribution", self.styles['SectionHeader']))
        
        # Count interactions by severity
        severity_counts = {}
        for interaction in interactions:
            severity = interaction.severity.value.title()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Create matplotlib pie chart
        fig, ax = plt.subplots(figsize=(8, 6))
        
        colors_map = {
            'Avoid': '#dc3545',
            'Caution': '#ffc107',
            'Safe': '#28a745'
        }
        
        colors_list = [colors_map.get(severity, '#gray') for severity in severity_counts.keys()]
        
        ax.pie(severity_counts.values(), labels=severity_counts.keys(), autopct='%1.1f%%',
               colors=colors_list, startangle=90)
        ax.set_title('Interaction Severity Distribution', fontsize=14, fontweight='bold')
        
        # Save plot to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        # Add image to story
        img = Image(img_buffer, width=5*inch, height=3.75*inch)
        story.append(img)
        
        return story
    
    def _create_drug_class_chart(self, drug_class_data: Dict) -> List:
        """Create drug class analysis chart"""
        story = []
        
        story.append(Paragraph("Drug Class Risk Analysis", self.styles['SectionHeader']))
        
        risk_scores = drug_class_data.get('risk_scores', {})
        if not risk_scores:
            return story
        
        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        classes = list(risk_scores.keys())[:10]  # Top 10 classes
        scores = [risk_scores[cls] for cls in classes]
        
        bars = ax.barh(classes, scores, color='skyblue')
        
        # Color bars by risk level
        for bar, score in zip(bars, scores):
            if score > 2.5:
                bar.set_color('#dc3545')  # Red for high risk
            elif score > 1.5:
                bar.set_color('#ffc107')  # Yellow for medium risk
            else:
                bar.set_color('#28a745')  # Green for low risk
        
        ax.set_xlabel('Average Risk Score')
        ax.set_title('Risk Scores by Drug Class', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        # Add image to story
        img = Image(img_buffer, width=6*inch, height=3.6*inch)
        story.append(img)
        
        return story
    
    def _create_recommendations_section(self, results: AnalysisResults) -> List:
        """Create recommendations section"""
        story = []
        
        story.append(Paragraph("Clinical Recommendations", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        if not results.recommendations:
            story.append(Paragraph(
                "No specific recommendations were generated for your analysis.",
                self.styles['BodyText']
            ))
            return story
        
        # Categorize recommendations
        critical_recs = []
        warning_recs = []
        info_recs = []
        general_recs = []
        
        for rec in results.recommendations:
            if rec.startswith("🚨") or "Critical" in rec or "Action Required" in rec:
                critical_recs.append(rec)
            elif rec.startswith("⚠️") or "Caution" in rec or "Warning" in rec:
                warning_recs.append(rec)
            elif rec.startswith("📞") or rec.startswith("✅") or "consult" in rec.lower():
                info_recs.append(rec)
            else:
                general_recs.append(rec)
        
        # Display categorized recommendations
        if critical_recs:
            story.append(Paragraph("Immediate Actions Required", self.styles['SectionHeader']))
            for rec in critical_recs:
                clean_rec = rec.replace("🚨", "").replace("**", "").strip()
                story.append(Paragraph(f"• {clean_rec}", self.styles['WarningText']))
            story.append(Spacer(1, 15))
        
        if warning_recs:
            story.append(Paragraph("Important Precautions", self.styles['SectionHeader']))
            for rec in warning_recs:
                clean_rec = rec.replace("⚠️", "").replace("**", "").strip()
                story.append(Paragraph(f"• {clean_rec}", self.styles['BodyText']))
            story.append(Spacer(1, 15))
        
        if info_recs:
            story.append(Paragraph("General Guidance", self.styles['SectionHeader']))
            for rec in info_recs:
                clean_rec = rec.replace("📞", "").replace("✅", "").replace("**", "").strip()
                story.append(Paragraph(f"• {clean_rec}", self.styles['BodyText']))
            story.append(Spacer(1, 15))
        
        if general_recs:
            story.append(Paragraph("Additional Notes", self.styles['SectionHeader']))
            for rec in general_recs:
                clean_rec = rec.replace("**", "").strip()
                story.append(Paragraph(f"• {clean_rec}", self.styles['BodyText']))
        
        return story
    
    def _create_appendix(self, results: AnalysisResults) -> List:
        """Create appendix with technical details"""
        story = []
        
        story.append(Paragraph("Technical Appendix", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Analysis metadata
        story.append(Paragraph("Analysis Metadata", self.styles['SectionHeader']))
        
        metadata_data = [
            ['Analysis Timestamp:', results.analysis_timestamp],
            ['Analysis Confidence:', f"{int(results.confidence_score * 100)}%"],
            ['Total Interactions Evaluated:', str(len(results.interactions))],
            ['Medications in Analysis:', str(len(results.medications_analyzed))],
            ['Foods in Analysis:', str(len(results.foods_analyzed))],
        ]
        
        # Add AI analysis info if available
        if hasattr(results, 'ai_analysis') and results.ai_analysis:
            metadata_data.extend([
                ['AI Analysis Method:', results.ai_analysis.analysis_method],
                ['AI Processing Time:', f"{results.ai_analysis.processing_time:.2f} seconds"],
                ['AI Confidence:', f"{int(results.ai_analysis.confidence * 100)}%"]
            ])
        
        metadata_table = Table(metadata_data, colWidths=[2.5*inch, 3.5*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), self.colors['light_gray'])
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 20))
        
        # Data sources
        story.append(Paragraph("Data Sources & Methodology", self.styles['SectionHeader']))
        
        methodology_text = """
        This analysis was conducted using a comprehensive database of known drug-food interactions 
        compiled from multiple authoritative sources including FDA drug labeling, peer-reviewed 
        medical literature, and clinical pharmacy references. The analysis engine evaluates 
        interactions based on severity classification, clinical evidence levels, and documented 
        mechanisms of action.
        
        Confidence scores are calculated based on the quality and quantity of available evidence, 
        with higher scores indicating well-established interactions supported by multiple sources 
        or clinical studies.
        """
        
        story.append(Paragraph(methodology_text, self.styles['BodyText']))
        story.append(Spacer(1, 15))
        
        # Disclaimer
        story.append(Paragraph("Important Disclaimers", self.styles['SectionHeader']))
        
        disclaimer_text = """
        This report is generated by an automated analysis system and is intended for informational 
        purposes only. It should not be considered a substitute for professional medical advice, 
        diagnosis, or treatment. Always seek the advice of your physician or other qualified 
        health provider with any questions you may have regarding a medical condition or treatment.
        
        The information in this report may not be complete and may not account for individual 
        health conditions, other medications, or personal risk factors. Drug and food interactions 
        can vary significantly between individuals.
        """
        
        story.append(Paragraph(disclaimer_text, self.styles['BodyText']))
        
        return story
    
    def _get_severity_color(self, severity: Severity) -> str:
        """Get color for severity level"""
        color_map = {
            Severity.AVOID: '#dc3545',
            Severity.CAUTION: '#ffc107',
            Severity.SAFE: '#28a745'
        }
        return color_map.get(severity, '#6c757d')
    
    def generate_summary_report(self, results: AnalysisResults) -> bytes:
        """Generate a shorter summary report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Title
        story.append(Paragraph(
            "Drug-Food Interaction Summary",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 20))
        
        # Key info
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", self.styles['BodyText']))
        story.append(Paragraph(f"Risk Level: {results.overall_risk_level.value.upper()}", self.styles['BodyText']))
        story.append(Spacer(1, 15))
        
        # Summary
        story.append(Paragraph("Summary", self.styles['SectionHeader']))
        story.append(Paragraph(results.summary, self.styles['BodyText']))
        
        # Key interactions (if any)
        if results.interactions:
            story.append(Spacer(1, 15))
            story.append(Paragraph("Key Interactions", self.styles['SectionHeader']))
            
            for interaction in results.interactions[:5]:  # Top 5
                story.append(Paragraph(
                    f"• {interaction.medication} + {interaction.food} ({interaction.severity.value})",
                    self.styles['BodyText']
                ))
        
        # Key recommendations
        if results.recommendations:
            story.append(Spacer(1, 15))
            story.append(Paragraph("Key Recommendations", self.styles['SectionHeader']))
            
            for rec in results.recommendations[:3]:  # Top 3
                clean_rec = rec.replace("🚨", "").replace("⚠️", "").replace("📞", "").replace("✅", "").replace("**", "").strip()
                story.append(Paragraph(f"• {clean_rec}", self.styles['BodyText']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()