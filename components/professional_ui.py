import streamlit as st
from typing import Dict, List, Optional

class ProfessionalUI:
    """Professional UI components for medical applications"""
    
    def __init__(self):
        self.severity_colors = {
            'avoid': '#dc2626',      # Red
            'caution': '#f59e0b',    # Amber  
            'safe': '#22c55e',       # Green
            'unknown': '#6b7280'     # Gray
        }
        
        self.severity_labels = {
            'avoid': 'AVOID',
            'caution': 'CAUTION',
            'safe': 'MONITOR',
            'unknown': 'UNKNOWN'
        }
    
    def load_css(self):
        """Load professional CSS styling"""
        try:
            with open('styles/professional.css', 'r') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except FileNotFoundError:
            # Fallback inline CSS
            st.markdown("""
            <style>
            .stApp { font-family: 'Segoe UI', 'Roboto', sans-serif; }
            h1 { color: #1e3a8a; font-weight: 500; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }
            h2 { color: #374151; }
            h3 { color: #4b5563; }
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """, unsafe_allow_html=True)
    
    def page_header(self, title: str, subtitle: str = None):
        """Create professional page header"""
        st.markdown(f"""
        <div class="main-content">
            <h1>{title}</h1>
            {f'<p style="color: #6b7280; font-size: 1.1rem; margin-bottom: 2rem;">{subtitle}</p>' if subtitle else ''}
        </div>
        """, unsafe_allow_html=True)
    
    def section_header(self, title: str, description: str = None):
        """Create professional section header"""
        st.markdown(f"<h2>{title}</h2>", unsafe_allow_html=True)
        if description:
            st.markdown(f'<p style="color: #6b7280; margin-bottom: 1.5rem;">{description}</p>', unsafe_allow_html=True)
    
    def info_card(self, title: str, content: str, card_type: str = "default"):
        """Create professional info card"""
        
        type_styles = {
            'success': 'background-color: #f0fdf4; border-left: 4px solid #22c55e;',
            'warning': 'background-color: #fffbeb; border-left: 4px solid #f59e0b;',
            'error': 'background-color: #fef2f2; border-left: 4px solid #ef4444;',
            'info': 'background-color: #f0f9ff; border-left: 4px solid #3b82f6;',
            'default': 'background-color: #ffffff; border: 1px solid #e2e8f0;'
        }
        
        style = type_styles.get(card_type, type_styles['default'])
        
        st.markdown(f"""
        <div style="{style} border-radius: 8px; padding: 1.5rem; margin: 1rem 0;">
            <h4 style="margin: 0 0 0.5rem 0; color: #374151;">{title}</h4>
            <p style="margin: 0; color: #4b5563;">{content}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def status_indicator(self, label: str, status: str, value: str = None):
        """Create professional status indicator"""
        
        status_colors = {
            'operational': '#22c55e',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'info': '#3b82f6'
        }
        
        color = status_colors.get(status, '#6b7280')
        
        status_html = f"""
        <div style="display: flex; align-items: center; margin: 0.5rem 0;">
            <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; 
                        background-color: {color}; margin-right: 12px;"></span>
            <span style="color: #374151; font-weight: 500;">{label}</span>
            {f'<span style="color: #6b7280; margin-left: auto;">{value}</span>' if value else ''}
        </div>
        """
        
        st.markdown(status_html, unsafe_allow_html=True)
    
    def severity_badge(self, severity: str):
        """Create professional severity badge"""
        
        color = self.severity_colors.get(severity, self.severity_colors['unknown'])
        label = self.severity_labels.get(severity, severity.upper())
        
        badge_html = f"""
        <span style="
            background-color: {color};
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        ">{label}</span>
        """
        
        return badge_html
    
    def metric_grid(self, metrics: List[Dict]):
        """Create professional metrics grid"""
        
        cols = st.columns(len(metrics))
        
        for i, metric in enumerate(metrics):
            with cols[i]:
                self.metric_card(
                    metric.get('label', ''),
                    metric.get('value', ''),
                    metric.get('delta', None),
                    metric.get('help', None)
                )
    
    def metric_card(self, label: str, value: str, delta: str = None, help_text: str = None):
        """Create professional metric card"""
        
        delta_html = ""
        if delta:
            delta_color = "#22c55e" if delta.startswith("+") or "increase" in delta.lower() else "#6b7280"
            delta_html = f'<p style="color: {delta_color}; font-size: 0.875rem; margin: 0.25rem 0 0 0;">{delta}</p>'
        
        card_html = f"""
        <div style="
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        ">
            <h3 style="color: #6b7280; font-size: 0.875rem; font-weight: 500; margin: 0; text-transform: uppercase; letter-spacing: 0.05em;">{label}</h3>
            <p style="color: #111827; font-size: 1.875rem; font-weight: 700; margin: 0.5rem 0 0 0;">{value}</p>
            {delta_html}
        </div>
        """
        
        if help_text:
            st.markdown(card_html, help=help_text, unsafe_allow_html=True)
        else:
            st.markdown(card_html, unsafe_allow_html=True)
    
    def professional_button(self, label: str, button_type: str = "primary", key: str = None):
        """Create professional button with proper styling"""
        
        if button_type == "primary":
            return st.button(label, type="primary", key=key)
        elif button_type == "secondary":
            return st.button(label, type="secondary", key=key)
        else:
            return st.button(label, key=key)
    
    def section_divider(self):
        """Create professional section divider"""
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)