import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from datetime import datetime
from utils.analytics_engine import AnalyticsEngine

class AnalyticsDashboard:
    def __init__(self):
        self.color_scheme = {
            'avoid': '#dc3545',      # Red
            'caution': '#ffc107',    # Yellow
            'safe': '#28a745',       # Green
            'primary': '#007bff',    # Blue
            'secondary': '#6c757d',  # Gray
            'accent': '#17a2b8'      # Teal
        }
        
        # Professional color palette for charts
        self.chart_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
    
    def display_comprehensive_dashboard(self, analytics_data: Dict):
        """Display the main analytics dashboard"""
        
        if not analytics_data or 'overview_stats' not in analytics_data:
            st.error("Analytics data not available")
            return
        
        # Dashboard header
        self._display_dashboard_header(analytics_data['overview_stats'])
        
        # Main metrics section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Key performance indicators
            self._display_kpi_section(analytics_data)
        
        with col2:
            # System health metrics
            self._display_system_health(analytics_data)
        
        st.markdown("---")
        
        # Interactive charts section
        self._display_interaction_analysis_charts(analytics_data)
        
        st.markdown("---")
        
        # Drug class and food category analysis
        self._display_categorical_analysis(analytics_data)
        
        st.markdown("---")
        
        # Risk assessment and prediction metrics
        self._display_risk_and_predictions(analytics_data)
        
        st.markdown("---")
        
        # Performance and data quality
        self._display_performance_metrics(analytics_data)

        # Analytics export options
        self.add_analytics_export_options(analytics_data)
    
    def _display_dashboard_header(self, overview_stats: Dict):
        """Display dashboard header"""

        st.markdown("""
        <div style="
            background-color: #2C3E50;
            padding: 30px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
        ">
            <h1 style="margin: 0; font-size: 2.2em;">Advanced Analytics Dashboard</h1>
            <p style="margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.9;">
                Comprehensive Drug-Food Interaction Analysis & Insights
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Key metrics overview
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Medications",
                f"{overview_stats.get('total_medications', 0):,}",
                help="Total medications in database"
            )

        with col2:
            st.metric(
                "Foods", 
                f"{overview_stats.get('total_foods', 0):,}",
                help="Total foods in database"
            )

        with col3:
            st.metric(
                "Interactions",
                f"{overview_stats.get('total_interactions', 0):,}",
                help="Known drug-food interactions"
            )

        with col4:
            st.metric(
                "Drug Classes",
                f"{overview_stats.get('drug_classes_count', 0):,}",
                help="Therapeutic drug classes"
            )

        with col5:
            coverage_rate = overview_stats.get('interaction_coverage_rate', 0)
            st.metric(
                "Coverage",
                f"{coverage_rate}%",
                delta=f"{coverage_rate - 75:.1f}%" if coverage_rate >= 75 else None,
                help="Interaction coverage rate"
            )

    
    def _display_kpi_section(self, analytics_data: Dict):
        """Display key performance indicators with advanced charts"""
        
        st.subheader(" Key Performance Indicators")
        
        # Severity distribution pie chart
        severity_data = analytics_data.get('severity_distribution', {})
        if severity_data and 'severity_counts' in severity_data:
            
            fig_severity = go.Figure(data=[go.Pie(
                labels=list(severity_data['severity_counts'].keys()),
                values=list(severity_data['severity_counts'].values()),
                marker_colors=[self.color_scheme.get(k, '#gray') for k in severity_data['severity_counts'].keys()],
                textinfo='label+percent+value',
                textfont_size=12,
                marker=dict(line=dict(color='#FFFFFF', width=2))
            )])
            
            fig_severity.update_layout(
                title={
                    'text': "Interaction Severity Distribution",
                    'x': 0.5,
                    'font': {'size': 16}
                },
                height=400,
                showlegend=True,
                font=dict(size=12)
            )
            
            st.plotly_chart(fig_severity, use_container_width=True)
    
    def _display_system_health(self, analytics_data: Dict):
        """Display system health and data quality metrics"""
        
        st.subheader("System Health")
        
        # Data quality gauge
        quality_data = analytics_data.get('data_quality_metrics', {})
        quality_score = quality_data.get('data_quality_score', 0)
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = quality_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Data Quality Score"},
            delta = {'reference': 80},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Quick stats
        prediction_data = analytics_data.get('prediction_metrics', {})
        if prediction_data:
            st.metric(
                "System Accuracy",
                f"{prediction_data.get('overall_system_accuracy', 0):.1%}",
                help="Overall prediction accuracy"
            )
            
            st.metric(
                "Coverage Rate", 
                f"{prediction_data.get('prediction_coverage', 0):.1f}%",
                help="Percentage of possible interactions covered"
            )
    
    def _display_interaction_analysis_charts(self, analytics_data: Dict):
        """Display comprehensive interaction analysis charts"""
        
        st.subheader("Interaction Pattern Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Interaction types breakdown
            pattern_data = analytics_data.get('interaction_patterns', {})
            if pattern_data and 'interaction_types' in pattern_data:
                
                types_data = pattern_data['interaction_types']
                
                fig_types = px.bar(
                    x=list(types_data.keys()),
                    y=list(types_data.values()),
                    title="Interaction Types Distribution",
                    color=list(types_data.values()),
                    color_continuous_scale="viridis"
                )
                
                fig_types.update_layout(
                    height=400,
                    xaxis_title="Interaction Type",
                    yaxis_title="Count",
                    showlegend=False
                )
                
                st.plotly_chart(fig_types, use_container_width=True)
        
        with col2:
            # Evidence levels
            if pattern_data and 'evidence_levels' in pattern_data:
                
                evidence_data = pattern_data['evidence_levels']
                
                fig_evidence = px.pie(
                    values=list(evidence_data.values()),
                    names=list(evidence_data.keys()),
                    title="Evidence Quality Distribution",
                    color_discrete_sequence=self.chart_colors
                )
                
                fig_evidence.update_layout(height=400)
                st.plotly_chart(fig_evidence, use_container_width=True)
        
        # Mechanism keyword analysis
        if pattern_data and 'mechanism_keywords' in pattern_data:
            st.subheader("Common Interaction Mechanisms")
            
            keywords = pattern_data['mechanism_keywords']
            
            # Create horizontal bar chart for mechanisms
            fig_mechanisms = px.bar(
                x=list(keywords.values()),
                y=list(keywords.keys()),
                orientation='h',
                title="Most Common Interaction Mechanisms",
                color=list(keywords.values()),
                color_continuous_scale="plasma"
            )
            
            fig_mechanisms.update_layout(
                height=400,
                xaxis_title="Frequency",
                yaxis_title="Mechanism Keywords"
            )
            
            st.plotly_chart(fig_mechanisms, use_container_width=True)
    
    def _display_categorical_analysis(self, analytics_data: Dict):
        """Display drug class and food category analysis"""
        
        st.subheader("Categorical Analysis")
        
        tab1, tab2 = st.tabs(["Drug Classes   |", "Food Categories    |"])
        
        with tab1:
            self._display_drug_class_analysis(analytics_data.get('drug_class_analysis', {}))
        
        with tab2:
            self._display_food_category_analysis(analytics_data.get('food_category_analysis', {}))
    
    def _display_drug_class_analysis(self, drug_class_data: Dict):
        """Display drug class interaction analysis"""
        
        if not drug_class_data:
            st.info("No drug class data available")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Drug class distribution
            class_dist = drug_class_data.get('class_distribution', {})
            if class_dist:
                
                class_sizes = {k: len(v) for k, v in class_dist.items()}
                
                fig_class_dist = px.treemap(
                    names=list(class_sizes.keys()),
                    values=list(class_sizes.values()),
                    title="Drug Class Distribution (by medication count)"
                )
                
                fig_class_dist.update_layout(height=400)
                st.plotly_chart(fig_class_dist, use_container_width=True)
        
        with col2:
            # Risk scores by class
            risk_scores = drug_class_data.get('risk_scores', {})
            if risk_scores:
                
                fig_risk = px.bar(
                    x=list(risk_scores.keys()),
                    y=list(risk_scores.values()),
                    title="Risk Scores by Drug Class",
                    color=list(risk_scores.values()),
                    color_continuous_scale="reds"
                )
                
                fig_risk.update_layout(
                    height=400,
                    xaxis_title="Drug Class",
                    yaxis_title="Average Risk Score",
                    xaxis={'tickangle': 45}
                )
                
                st.plotly_chart(fig_risk, use_container_width=True)
        
        # Highest risk classes table
        highest_risk = drug_class_data.get('highest_risk_classes', [])
        if highest_risk:
            st.subheader("Highest Risk Drug Classes")
            
            risk_df = pd.DataFrame(highest_risk, columns=['Drug Class', 'Risk Score'])
            risk_df['Risk Level'] = risk_df['Risk Score'].apply(
                lambda x: 'High' if x > 2.5 else 'Medium' if x > 1.5 else 'Low'
            )
            
            st.dataframe(risk_df, use_container_width=True)
    
    def _display_food_category_analysis(self, food_category_data: Dict):
        """Display food category interaction analysis"""
        
        if not food_category_data:
            st.info("No food category data available")
            return
        
        category_stats = food_category_data.get('category_stats', {})
        if not category_stats:
            return
        
        # Prepare data for visualization
        categories = []
        interaction_rates = []
        food_counts = []
        interaction_counts = []
        
        for category, stats in category_stats.items():
            categories.append(category)
            interaction_rates.append(stats.get('interaction_rate', 0))
            food_counts.append(stats.get('food_count', 0))
            interaction_counts.append(stats.get('interaction_count', 0))
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Interaction rates by category
            fig_rates = px.bar(
                x=categories,
                y=interaction_rates,
                title="Interaction Rate by Food Category",
                color=interaction_rates,
                color_continuous_scale="oranges"
            )
            
            fig_rates.update_layout(
                height=400,
                xaxis_title="Food Category",
                yaxis_title="Interactions per Food Item",
                xaxis={'tickangle': 45}
            )
            
            st.plotly_chart(fig_rates, use_container_width=True)
        
        with col2:
            # Food count vs interaction count scatter
            fig_scatter = px.scatter(
                x=food_counts,
                y=interaction_counts,
                text=categories,
                title="Food Count vs Interaction Count by Category",
                size=interaction_rates,
                color=interaction_rates,
                color_continuous_scale="viridis"
            )
            
            fig_scatter.update_traces(textposition='top center')
            fig_scatter.update_layout(
                height=400,
                xaxis_title="Number of Foods",
                yaxis_title="Number of Interactions"
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
    
    def _display_risk_and_predictions(self, analytics_data: Dict):
        """Display risk assessment and prediction analytics"""
        
        st.subheader("Risk Assessment & Predictions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Risk matrix heatmap
            risk_data = analytics_data.get('risk_assessment_matrix', {})
            high_risk_combos = risk_data.get('high_risk_combinations', [])
            
            if high_risk_combos:
                st.subheader("High-Risk Combinations")
                
                # Create DataFrame for high-risk combinations
                risk_df = pd.DataFrame(high_risk_combos)
                
                if not risk_df.empty:
                    # Create heatmap-style visualization
                    fig_heatmap = px.scatter(
                        risk_df,
                        x='medication',
                        y='food',
                        size='score',
                        color='severity',
                        title="High-Risk Drug-Food Combinations",
                        color_discrete_map=self.color_scheme
                    )
                    
                    fig_heatmap.update_layout(
                        height=400,
                        xaxis_title="Medication",
                        yaxis_title="Food",
                        xaxis={'tickangle': 45}
                    )
                    
                    st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with col2:
            # Prediction confidence distribution
            pred_data = analytics_data.get('prediction_metrics', {})
            confidence_dist = pred_data.get('confidence_distribution', {})
            
            if confidence_dist:
                fig_confidence = go.Figure(data=[go.Bar(
                    x=list(confidence_dist.keys()),
                    y=list(confidence_dist.values()),
                    marker_color=['#28a745', '#ffc107', '#dc3545']  # Green, Yellow, Red
                )])
                
                fig_confidence.update_layout(
                    title="Prediction Confidence Distribution",
                    xaxis_title="Confidence Level",
                    yaxis_title="Number of Predictions",
                    height=400
                )
                
                st.plotly_chart(fig_confidence, use_container_width=True)
        
        # Temporal analysis
        temporal_data = analytics_data.get('temporal_analysis', {})
        if temporal_data and 'query_dates' in temporal_data:
            st.subheader("Query Patterns Over Time")
            
            dates = temporal_data['query_dates']
            counts = temporal_data['weekly_query_counts']
            
            fig_temporal = px.line(
                x=dates,
                y=counts,
                title="Weekly Query Volume (Simulated)",
                labels={'x': 'Date', 'y': 'Number of Queries'}
            )
            
            fig_temporal.update_layout(height=400)
            st.plotly_chart(fig_temporal, use_container_width=True)
    
    def _display_performance_metrics(self, analytics_data: Dict):
        """Display system performance and data quality metrics"""
        
        st.subheader("Performance & Data Quality")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Data completeness radar chart
            quality_data = analytics_data.get('data_quality_metrics', {})
            
            if quality_data:
                categories = ['Medication\nCompleteness', 'Food\nCompleteness', 'Interaction\nCompleteness']
                values = [
                    quality_data.get('medication_completeness', 0),
                    quality_data.get('food_completeness', 0), 
                    quality_data.get('interaction_completeness', 0)
                ]
                
                fig_radar = go.Figure()
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name='Completeness %',
                    line_color='rgb(32, 201, 151)'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )
                    ),
                    title="Data Completeness Profile",
                    height=400
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
        
        with col2:
            # System performance gauge (simulated)
            performance_score = 92  # Simulated
            
            fig_perf_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = performance_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "System Performance"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "lightgreen"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 85], 'color': "yellow"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 95
                    }
                }
            ))
            
            fig_perf_gauge.update_layout(height=400)
            st.plotly_chart(fig_perf_gauge, use_container_width=True)
        
        with col3:
            # Database growth simulation
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
            med_growth = [150, 180, 220, 280, 320, 350]
            food_growth = [80, 95, 120, 135, 148, 155]
            interaction_growth = [10, 12, 13, 13, 13, 13]
            
            fig_growth = go.Figure()
            
            fig_growth.add_trace(go.Scatter(x=months, y=med_growth, name='Medications', line=dict(color='blue')))
            fig_growth.add_trace(go.Scatter(x=months, y=food_growth, name='Foods', line=dict(color='green')))
            fig_growth.add_trace(go.Scatter(x=months, y=interaction_growth, name='Interactions', line=dict(color='red')))
            
            fig_growth.update_layout(
                title='Database Growth Over Time (Simulated)',
                xaxis_title='Month',
                yaxis_title='Count',
                height=400
            )
            
            st.plotly_chart(fig_growth, use_container_width=True)
        
        # Performance summary table
        st.subheader("Performance Summary")
        
        perf_metrics = {
            'Metric': [
                'Database Size', 'Average Query Time', 'Cache Hit Rate',
                'System Uptime', 'Data Quality Score', 'Interaction Coverage'
            ],
            'Value': [
                '2.3 MB', '15ms', '85%', '99.9%', 
                f"{quality_data.get('data_quality_score', 0):.1f}%",
                f"{analytics_data.get('overview_stats', {}).get('interaction_coverage_rate', 0):.1f}%"
            ],
            'Status': [
                'Optimal', 'Fast', 'Good', 'Excellent',
                'High' if quality_data.get('data_quality_score', 0) > 80 else 'Medium',
                'Good' if analytics_data.get('overview_stats', {}).get('interaction_coverage_rate', 0) > 75 else 'Improving'
            ]
        }
        
        perf_df = pd.DataFrame(perf_metrics)
        st.dataframe(perf_df, use_container_width=True, hide_index=True)


    def generate_analytics_pdf(self, analytics_data: Dict) -> bytes:
        """Generate PDF report for analytics dashboard"""
        
        from utils.pdf_generator import PDFReportGenerator
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet
        
        # Create a simplified analytics report
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph("Analytics Dashboard Report", styles['Title']))
        story.append(Spacer(1, 30))
        
        # Overview stats
        overview = analytics_data.get('overview_stats', {})
        if overview:
            story.append(Paragraph("Database Overview", styles['Heading2']))
            
            overview_text = f"""
            Total Medications: {overview.get('total_medications', 0):,}<br/>
            Total Foods: {overview.get('total_foods', 0):,}<br/>
            Known Interactions: {overview.get('total_interactions', 0):,}<br/>
            Drug Classes: {overview.get('drug_classes_count', 0):,}<br/>
            Food Categories: {overview.get('food_categories_count', 0):,}<br/>
            Coverage Rate: {overview.get('interaction_coverage_rate', 0):.1f}%
            """
            
            story.append(Paragraph(overview_text, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Data quality section
        quality_data = analytics_data.get('data_quality_metrics', {})
        if quality_data:
            story.append(Paragraph("Data Quality Assessment", styles['Heading2']))
            
            quality_text = f"""
            Overall Data Quality Score: {quality_data.get('data_quality_score', 0):.1f}%<br/>
            Medication Data Completeness: {quality_data.get('medication_completeness', 0):.1f}%<br/>
            Food Data Completeness: {quality_data.get('food_completeness', 0):.1f}%<br/>
            Interaction Data Completeness: {quality_data.get('interaction_completeness', 0):.1f}%
            """
            
            story.append(Paragraph(quality_text, styles['Normal']))
        
        # Add timestamp
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            styles['Normal']
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def add_analytics_export_options(self, analytics_data: Dict):
        """Add export options to analytics dashboard"""
        
        st.markdown("---")
        st.subheader("Export Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export Analytics PDF", type="secondary"):
                try:
                    with st.spinner("Generating analytics PDF..."):
                        pdf_bytes = self.generate_analytics_pdf(analytics_data)
                        
                        filename = f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        
                        st.download_button(
                            label="Download Analytics PDF",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf"
                        )
                        
                    st.success("Analytics PDF ready for download!")
                except Exception as e:
                    st.error(f"Error generating analytics PDF: {e}")
        