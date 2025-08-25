import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Optional
import json
from datetime import datetime
from utils.interaction_engine import AnalysisResults, InteractionResult, Severity
import base64
from utils.pdf_generator import PDFReportGenerator
import base64

class ResultsDisplay:
    def __init__(self):
        self.severity_colors = {
            Severity.SAFE: "#28a745",      # Green
            Severity.CAUTION: "#ffc107",   # Yellow
            Severity.AVOID: "#dc3545"      # Red
        }
        
        self.severity_icons = {
            Severity.SAFE: "🟢",
            Severity.CAUTION: "🟡",
            Severity.AVOID: "🔴"
        }
    
    def display_results(self, results: AnalysisResults):
        """Main method to display comprehensive results"""
        
        # Header with overall risk
        self._display_risk_header(results)
        
        # Key metrics dashboard
        self._display_metrics_dashboard(results)
        
        # AI Analysis (if available)
        if hasattr(results, 'ai_analysis') and results.ai_analysis:
            self._display_ai_analysis(results.ai_analysis)
        
        # Interactive visualization
        if results.interactions:
            self._display_interaction_chart(results.interactions)
        
        # Detailed interaction cards
        self._display_interaction_cards(results.interactions)
        
        # Recommendations with priority
        self._display_recommendations(results.recommendations)
        
        # Export options
        self._display_export_options(results)
        
        # Analysis metadata
        self._display_metadata(results)
    
    def _display_risk_header(self, results: AnalysisResults):
        """Display the main risk level header"""
        st.markdown("---")
        
        # Create a prominent header with color coding
        risk_level = results.overall_risk_level
        icon = self.severity_icons[risk_level]
        color = self.severity_colors[risk_level]
        
        # Custom CSS for the risk header
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, {color}20, {color}10);
            border-left: 5px solid {color};
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        ">
            <h1 style="
                color: {color};
                margin: 0;
                font-size: 2.5em;
                text-align: center;
            ">
                {icon} {risk_level.value.upper()} RISK LEVEL
            </h1>
        </div>
        """, unsafe_allow_html=True)
    
    def _display_metrics_dashboard(self, results: AnalysisResults):
        """Display key metrics in a dashboard format"""
        st.subheader("Analysis Overview")
        
        # Calculate metrics
        total_interactions = len(results.interactions)
        avoid_count = sum(1 for i in results.interactions if i.severity == Severity.AVOID)
        caution_count = sum(1 for i in results.interactions if i.severity == Severity.CAUTION)
        safe_count = sum(1 for i in results.interactions if i.severity == Severity.SAFE)
        
        # Create metrics columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Interactions",
                total_interactions,
                help="Total number of interactions found"
            )
        
        with col2:
            st.metric(
                "Critical",
                avoid_count,
                delta=f"-{avoid_count}" if avoid_count > 0 else None,
                delta_color="inverse",
                help="Interactions to avoid completely"
            )
        
        with col3:
            st.metric(
                "Caution",
                caution_count,
                delta=f"±{caution_count}" if caution_count > 0 else None,
                delta_color="off",
                help="Interactions requiring monitoring"
            )
        
        with col4:
            st.metric(
                "Safe",
                safe_count,
                delta=f"+{safe_count}" if safe_count > 0 else None,
                delta_color="normal",
                help="Low-risk or beneficial interactions"
            )
        
        with col5:
            confidence_pct = int(results.confidence_score * 100)
            st.metric(
                "Confidence",
                f"{confidence_pct}%",
                help="Analysis confidence level"
            )
    
    def _display_ai_analysis(self, ai_analysis):
        """Display AI analysis in an attractive format"""
        with st.expander("AI-Enhanced Analysis", expanded=True):
            
            # AI metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("AI Confidence", f"{int(ai_analysis.confidence * 100)}%")
            with col2:
                st.metric("Method", ai_analysis.analysis_method)
            with col3:
                st.metric("Processing Time", f"{ai_analysis.processing_time:.2f}s")
            
            # AI explanation
            st.markdown("AI Explanation")
            st.info(ai_analysis.detailed_explanation)
            
            # AI warnings
            if ai_analysis.additional_warnings:
                st.markdown("AI-Identified Warnings")
                for warning in ai_analysis.additional_warnings:
                    st.warning(f"• {warning}")
    
    def _display_interaction_chart(self, interactions: List[InteractionResult]):
        """Create an interactive chart of interactions"""
        st.subheader("Interaction Visualization")
        
        if not interactions:
            return
        
        # Prepare data for chart
        chart_data = []
        for interaction in interactions:
            chart_data.append({
                'Medication': interaction.medication,
                'Food': interaction.food,
                'Severity': interaction.severity.value.title(),
                'Confidence': interaction.confidence,
                'Type': interaction.interaction_type.value.title(),
                'Evidence': interaction.evidence_level.title()
            })
        
        # Create interactive scatter plot
        fig = px.scatter(
            chart_data,
            x='Medication',
            y='Food',
            color='Severity',
            size='Confidence',
            hover_data=['Type', 'Evidence'],
            color_discrete_map={
                'Avoid': '#dc3545',
                'Caution': '#ffc107', 
                'Safe': '#28a745'
            },
            title="Drug-Food Interaction Map"
        )
        
        fig.update_layout(
            height=400,
            showlegend=True,
            xaxis_title="Medications",
            yaxis_title="Foods"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary pie chart
        severity_counts = {}
        for interaction in interactions:
            severity = interaction.severity.value.title()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if len(severity_counts) > 1:
            fig_pie = px.pie(
                values=list(severity_counts.values()),
                names=list(severity_counts.keys()),
                title="Interactions by Severity",
                color_discrete_map={
                    'Avoid': '#dc3545',
                    'Caution': '#ffc107',
                    'Safe': '#28a745'
                }
            )
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    def _display_interaction_cards(self, interactions: List[InteractionResult]):
        """Display detailed interaction cards"""
        if not interactions:
            st.success("No significant interactions found!")
            return
        
        st.subheader("Detailed Interaction Analysis")
        
        # Group interactions by severity
        grouped_interactions = {
            Severity.AVOID: [],
            Severity.CAUTION: [],
            Severity.SAFE: []
        }
        
        for interaction in interactions:
            grouped_interactions[interaction.severity].append(interaction)
        
        # Display each group
        for severity in [Severity.AVOID, Severity.CAUTION, Severity.SAFE]:
            severity_interactions = grouped_interactions[severity]
            if not severity_interactions:
                continue
            
            icon = self.severity_icons[severity]
            color = self.severity_colors[severity]
            
            st.markdown(f"### {icon} {severity.value.title()} Interactions ({len(severity_interactions)})")
            
            for interaction in severity_interactions:
                self._display_interaction_card(interaction, color)
    
    def _display_interaction_card(self, interaction: InteractionResult, color: str):
        """Display a single interaction card"""
        
        # Create expandable card
        with st.expander(f"{interaction.medication} + {interaction.food}", expanded=False):
            
            # Main interaction info
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("Clinical Details:**")
                st.write(f"**Mechanism:** {interaction.mechanism}")
                st.write(f"**Clinical Effect:** {interaction.clinical_effect}")
                st.write(f"**Interaction Type:** {interaction.interaction_type.value.title()}")
                
                if interaction.timing_recommendation:
                    st.markdown("**Timing Guidance:**")
                    st.success(interaction.timing_recommendation)
            
            with col2:
                st.markdown("**Evidence Quality:**")
                st.write(f"**Evidence Level:** {interaction.evidence_level.title()}")
                st.write(f"**Confidence:** {int(interaction.confidence * 100)}%")
                st.write(f"**Source:** {interaction.source}")
                
                # Visual confidence indicator
                confidence_pct = interaction.confidence * 100
                if confidence_pct >= 90:
                    st.success(f"High Confidence ({confidence_pct:.0f}%)")
                elif confidence_pct >= 70:
                    st.warning(f"Moderate Confidence ({confidence_pct:.0f}%)")
                else:
                    st.error(f"Low Confidence ({confidence_pct:.0f}%)")
    
    def _display_recommendations(self, recommendations: List[str]):
        """Display prioritized recommendations"""
        if not recommendations:
            return
        
        st.subheader("Personalized Recommendations")
        
        # Categorize recommendations
        critical_recs = []
        warning_recs = []
        info_recs = []
        general_recs = []
        
        for rec in recommendations:
            if rec.startswith("🚨"):
                critical_recs.append(rec)
            elif rec.startswith("⚠️"):
                warning_recs.append(rec)
            elif rec.startswith("📞") or rec.startswith("✅"):
                info_recs.append(rec)
            else:
                general_recs.append(rec)
        
        # Display by priority
        if critical_recs:
            st.markdown("Immediate Action Required")
            for rec in critical_recs:
                st.error(rec)
        
        if warning_recs:
            st.markdown("Important Precautions")
            for rec in warning_recs:
                st.warning(rec)
        
        if info_recs:
            st.markdown("General Guidance")
            for rec in info_recs:
                st.info(rec)
        
        if general_recs:
            st.markdown("Additional Notes")
            for rec in general_recs:
                st.write(rec)
    
    def _display_export_options(self, results: AnalysisResults, analytics_data: Optional[Dict] = None):
        """Display export and sharing options including PDF generation"""
        st.subheader("Export & Share Results")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Simpler test - just show the download button directly
            try:
                from utils.pdf_generator import PDFReportGenerator
                pdf_generator = PDFReportGenerator()
                pdf_bytes = pdf_generator.generate_summary_report(results)
                
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"interaction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    key="download_pdf_report_unique"  # ADD UNIQUE KEY
                )
                st.success(f"PDF ready! ({len(pdf_bytes)} bytes)")
                
            except Exception as e:
                st.error(f"PDF Error: {str(e)}")
                # Show simple text download as fallback
                report_text = self._generate_text_report(results)
                st.download_button(
                    label="Download Text Report",
                    data=report_text,
                    file_name=f"interaction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_text_report_unique"  # ADD UNIQUE KEY
                )
        
        with col2:
            # JSON export
            if st.button("Export JSON", type="secondary", key="export_json_unique"):  # ADD UNIQUE KEY
                json_data = self._generate_json_export(results)
                self._download_json_export(json_data, results)
        
        with col3:
            # Copy summary
            if st.button("Copy Summary", type="secondary", key="copy_summary_unique"):  # ADD UNIQUE KEY
                summary_text = self._generate_summary_text(results)
                st.code(summary_text, language="text")
                st.success("Summary ready to copy!")
        
        with col4:
            st.write("**Export Status:**")
            st.write(f"Results stored")
            st.write(f"{len(results.interactions)} interactions")
            st.write(f"Risk: {results.overall_risk_level.value}")

    def _download_pdf_report(self, pdf_bytes: bytes, results: AnalysisResults, report_type: str):
        """Provide download link for PDF report"""
        
        # Generate filename based on report type and timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        risk_level = results.overall_risk_level.value.lower()
        filename = f"drug_food_interaction_{report_type}_{risk_level}_{timestamp}.pdf"
        
        # Create download button
        st.download_button(
            label=f"Download {report_type.title()} PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            help=f"Download {report_type} PDF report to your device"
        )
        
        # Display file info
        file_size_mb = len(pdf_bytes) / (1024 * 1024)
        st.info(f"Report size: {file_size_mb:.1f} MB | Format: PDF | Type: {report_type.title()}")

    def _display_pdf_preview(self, results: AnalysisResults, analytics_data: Optional[Dict]):
        """Display preview of what will be included in PDF reports"""
        
        st.markdown("PDF Report Content Preview")
        
        tab1, tab2 = st.tabs(["📄 Comprehensive Report", "📋 Summary Report"])
        
        with tab1:
            st.write("**Comprehensive PDF Report will include:**")
            
            sections = [
                "**Title Page** - Report details, risk level, disclaimer",
                "**Executive Summary** - Key findings and AI analysis",
                "**Detailed Analysis** - Complete interaction breakdown by severity",
                "**Visual Charts** - Severity distribution and drug class analysis",
                "**Clinical Recommendations** - Categorized by urgency and importance", 
                "**Technical Appendix** - Methodology, data sources, disclaimers"
            ]
            
            for section in sections:
                st.write(section)
            
            # Show estimated metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Estimated Pages", "6-12")
            with col2:
                st.metric("Charts Included", "2-4")
            with col3:
                st.metric("File Size", "~2-5 MB")
        
        with tab2:
            st.write("**Summary PDF Report will include:**")
            
            summary_sections = [
                "**Header** - Basic report information and risk level",
                "**Summary** - Condensed analysis overview", 
                "**Key Interactions** - Top 5 most important interactions",
                "**Essential Recommendations** - Top 3 critical recommendations"
            ]
            
            for section in summary_sections:
                st.write(section)
            
            # Show estimated metrics  
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Estimated Pages", "1-2")
            with col2:
                st.metric("Charts Included", "0-1")
            with col3:
                st.metric("File Size", "~500 KB")

    
    def _generate_text_report(self, results: AnalysisResults) -> str:
        """Generate a comprehensive text report"""
        report_lines = [
            "=" * 60,
            "DRUG-FOOD INTERACTION ANALYSIS REPORT",
            "=" * 60,
            "",
            f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            f"Overall Risk Level: {results.overall_risk_level.value.upper()}",
            f"Analysis Confidence: {int(results.confidence_score * 100)}%",
            "",
            "MEDICATIONS ANALYZED:",
            "-" * 20
        ]
        
        for med in results.medications_analyzed:
            report_lines.append(f"• {med}")
        
        report_lines.extend([
            "",
            "FOODS ANALYZED:",
            "-" * 15
        ])
        
        for food in results.foods_analyzed:
            report_lines.append(f"• {food}")
        
        report_lines.extend([
            "",
            "SUMMARY:",
            "-" * 8,
            results.summary,
            ""
        ])
        
        if results.interactions:
            report_lines.extend([
                "DETAILED INTERACTIONS:",
                "-" * 22
            ])
            
            for interaction in results.interactions:
                report_lines.extend([
                    f"",
                    f"{interaction.severity.value.upper()}: {interaction.medication} + {interaction.food}",
                    f"  Mechanism: {interaction.mechanism}",
                    f"  Clinical Effect: {interaction.clinical_effect}",
                    f"  Recommendation: {interaction.timing_recommendation}",
                    f"  Evidence: {interaction.evidence_level} ({int(interaction.confidence * 100)}% confidence)"
                ])
        
        report_lines.extend([
            "",
            "RECOMMENDATIONS:",
            "-" * 15
        ])
        
        for i, rec in enumerate(results.recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        
        report_lines.extend([
            "",
            "DISCLAIMER:",
            "-" * 11,
            "This analysis is for informational purposes only and should not",
            "replace professional medical advice. Always consult your healthcare",
            "provider before making changes to medications or diet.",
            "",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
    
    def _download_text_report(self, report_text: str, results: AnalysisResults):
        """Provide download link for text report"""
        filename = f"interaction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        st.download_button(
            label="Download Report",
            data=report_text,
            file_name=filename,
            mime="text/plain"
        )
    
    def _generate_json_export(self, results: AnalysisResults) -> str:
        """Generate JSON export of results"""
        export_data = {
            "analysis_timestamp": results.analysis_timestamp,
            "overall_risk_level": results.overall_risk_level.value,
            "confidence_score": results.confidence_score,
            "medications_analyzed": results.medications_analyzed,
            "foods_analyzed": results.foods_analyzed,
            "summary": results.summary,
            "recommendations": results.recommendations,
            "interactions": []
        }
        
        for interaction in results.interactions:
            export_data["interactions"].append({
                "medication": interaction.medication,
                "food": interaction.food,
                "severity": interaction.severity.value,
                "interaction_type": interaction.interaction_type.value,
                "mechanism": interaction.mechanism,
                "clinical_effect": interaction.clinical_effect,
                "timing_recommendation": interaction.timing_recommendation,
                "confidence": interaction.confidence,
                "evidence_level": interaction.evidence_level,
                "source": interaction.source
            })
        
        # Add AI analysis if available
        if hasattr(results, 'ai_analysis') and results.ai_analysis:
            export_data["ai_analysis"] = {
                "enhanced_summary": results.ai_analysis.enhanced_summary,
                "detailed_explanation": results.ai_analysis.detailed_explanation,
                "additional_warnings": results.ai_analysis.additional_warnings,
                "confidence": results.ai_analysis.confidence,
                "analysis_method": results.ai_analysis.analysis_method,
                "processing_time": results.ai_analysis.processing_time
            }
        
        return json.dumps(export_data, indent=2)
    
    def _download_json_export(self, json_data: str, results: AnalysisResults):
        """Provide download link for JSON export"""
        filename = f"interaction_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name=filename,
            mime="application/json"
        )
    
    def _generate_summary_text(self, results: AnalysisResults) -> str:
        """Generate a brief summary for copying"""
        summary_lines = [
            f"Drug-Food Interaction Analysis Summary",
            f"Risk Level: {results.overall_risk_level.value.upper()}",
            f"Medications: {', '.join(results.medications_analyzed)}",
            f"Foods: {', '.join(results.foods_analyzed)}",
            f"Interactions Found: {len(results.interactions)}",
            f"Confidence: {int(results.confidence_score * 100)}%",
            "",
            results.summary
        ]
        
        if results.interactions:
            summary_lines.append("\nKey Interactions:")
            for interaction in results.interactions[:3]:  # Top 3
                summary_lines.append(f"• {interaction.medication} + {interaction.food} ({interaction.severity.value})")
        
        return "\n".join(summary_lines)
    
    
    def _display_metadata(self, results: AnalysisResults):
        """Display analysis metadata"""
        with st.expander("Analysis Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Analysis completed:** {results.analysis_timestamp}")
                st.write(f"**Total interactions found:** {len(results.interactions)}")
                st.write(f"**Items analyzed:** {len(results.medications_analyzed) + len(results.foods_analyzed)}")
            
            with col2:
                if hasattr(results, 'ai_analysis') and results.ai_analysis:
                    st.write(f"**AI Method:** {results.ai_analysis.analysis_method}")
                    st.write(f"**AI Processing:** {results.ai_analysis.processing_time:.2f}s")
                
                # Interaction breakdown
                if results.interactions:
                    severity_counts = {}
                    for interaction in results.interactions:
                        severity = interaction.severity.value
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    
                    st.write("**Breakdown by severity:**")
                    for severity, count in severity_counts.items():
                        st.write(f"  {severity.title()}: {count}")


    def display_app_status(self, components):
        """Display comprehensive app status"""
        with st.expander("App Health Status"):
            
            # Component status
            st.write("**Component Status:**")
            
            status_checks = [
                ("Database", self._check_database_health(components)),
                ("Search Interface", self._check_search_health(components)),  
                ("Interaction Engine", self._check_interaction_engine_health(components)),
                ("AI Analysis", self._check_ai_health(components)),
                ("Results Display", True)  # Always available
            ]
            
            for component, status in status_checks:
                if status:
                    st.success(f" {component}: Operational")
                else:
                    st.error(f" {component}: Issues detected")
            
            # Performance metrics
            st.write("**Performance Metrics:**")
            stats = components['data_processor'].get_database_stats()
            st.write(f"• Database entries: {stats.get('total_medications', 0) + stats.get('total_foods', 0)}")
            st.write(f"• Searchable items: {stats.get('searchable_med_names', 0) + stats.get('searchable_food_names', 0)}")
            st.write(f"• Known interactions: {stats.get('total_interactions', 0)}")

    def _check_database_health(self, components) -> bool:
        try:
            components['db_manager'].get_all_medications()
            return True
        except:
            return False

    def _check_search_health(self, components) -> bool:
        return hasattr(components.get('search_interface'), 'medication_search_callback')

    def _check_interaction_engine_health(self, components) -> bool:
        return hasattr(components.get('interaction_engine'), 'analyze_interactions')

    def _check_ai_health(self, components) -> bool:
        try:
            ai_analyzer = components['interaction_engine'].ai_analyzer
            return ai_analyzer is not None
        except:
            return False

    def display_results_with_analytics(self, results: AnalysisResults, analytics_data: Optional[Dict] = None):
        """Display results with analytics data for enhanced PDF generation"""
        
        # Header with overall risk
        self._display_risk_header(results)
        
        # Key metrics dashboard
        self._display_metrics_dashboard(results)
        
        # AI Analysis (if available)
        if hasattr(results, 'ai_analysis') and results.ai_analysis:
            self._display_ai_analysis(results.ai_analysis)
        
        # Interactive visualization
        if results.interactions:
            self._display_interaction_chart(results.interactions)
        
        # Detailed interaction cards
        self._display_interaction_cards(results.interactions)
        
        # Recommendations with priority
        self._display_recommendations(results.recommendations)
        
        # Enhanced export options with analytics data
        self._display_export_options(results, analytics_data)
        
        # Analysis metadata
        self._display_metadata(results)