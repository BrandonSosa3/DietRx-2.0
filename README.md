DietRx Enhanced – Drug-Food Interaction Analysis Platform

A clinical decision support system that analyzes drug-food interactions using FDA data, AI-enhanced analysis, and professional reporting for healthcare professionals and patients.

Project Overview

DietRx Enhanced provides intelligent analysis of medication and food interactions through a user-friendly web interface. The platform integrates official FDA data with advanced analytics to deliver evidence-based interaction assessments and professional clinical reports.

Note: This application is deployed on Streamlit Community Cloud. Initial loading may take 30–60 seconds while the system initializes and loads FDA interaction data. Once running, the application is fast and responsive.

Live Links

Live Application: https://dietrx-20.streamlit.app/

GitHub Repository: https://github.com/yourusername/dietrx-enhanced

Live Demo Walkthrough - Be sure to check out all pages on the sidebar you can toggle between them with the radio buttons

Interaction Analysis – Select a medication and food item to analyze potential interactions with clinical evidence.

FDA Data Integration – Explore official FDA interaction data with 100+ documented drug-food combinations.

Professional Reports – Generate comprehensive PDF reports suitable for healthcare providers and patients.

Analytics Dashboard – View interaction patterns, database statistics, and data quality metrics.

Performance Monitoring – Access system health metrics and database performance insights.

Key Features

Clinical Interaction Analysis – Evidence-based drug-food interaction checking with severity classifications.

FDA Data Integration – Real-time access to official FDA OpenFDA API for authoritative interaction data.

Professional PDF Reports – Medical-grade reports with clinical recommendations and safety guidelines.

Advanced Analytics Dashboard – Interactive visualizations of interaction patterns and database insights.

Performance Monitoring – System health tracking and database optimization metrics.

AI-Enhanced Analysis – Template-based intelligent analysis with clinical insights and recommendations.

Technical Architecture

Frontend (Streamlit)

Streamlit web framework

Professional UI components

Interactive visualizations with Plotly

PDF generation with ReportLab

Backend

SQLite database with dynamic schema

FDA OpenFDA API integration

Fuzzy matching for medication/food search

Performance monitoring and caching

External APIs

FDA OpenFDA API – official drug interaction data

Custom analytics engine – interaction pattern analysis

Local Setup

Requirements: Python 3.8+, Git

Clone the repository:

git clone https://github.com/BrandonSosa3/DietRx-2.0.git
cd dietrx-enhanced


Environment setup:

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt


Run the application:

streamlit run app.py


Access locally:

Application: http://localhost:8501

Database: SQLite (automatically created)

Performance Notes

Initial startup: 30–60 seconds (FDA data loading)

Warm performance: Near-instant response times

Database: Automatically populates with FDA interaction data

Reports: PDF generation typically under 5 seconds

Technical Highlights

Data Integration: FDA OpenFDA API integration with rate limiting and error handling

Database Management: Dynamic SQLite schema with automated FDA data ingestion

Professional UI: Clean, medical-grade interface

Document Generation: Comprehensive PDF reports with charts and clinical formatting

Analytics: Interactive dashboards with Plotly visualizations and performance metrics

Best Practices: Modular architecture, error handling, professional logging, data validation

Contact

Developer: Brandon Sosa

LinkedIn: https://www.linkedin.com/in/brandonsosa123/

GitHub: https://github.com/BrandonSosa3

Email: brandonsosa10101@gmail.com

Phone: 1(818)-309-6961