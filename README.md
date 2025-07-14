# 🏥 Sutherland Radiology Coding Analysis

A comprehensive AI-powered analysis system for evaluating medical coding accuracy between human coders and AI systems in radiology reports.

## 🎯 Overview

This application analyzes the accuracy of AI-generated medical codes compared to expert human coders (Sutherland Medical Coding) using advanced AI review processes and provides interactive visualizations through a Streamlit dashboard.

### Key Features

- **📊 Comprehensive Accuracy Analysis**: Chart-level and code-level accuracy metrics
- **🤖 AI-Powered Code Classification**: Intelligent classification of missed codes as relevant/not relevant
- **🔍 Multi-Stage Review Process**: 
  - Partial Match Review (AI vs Human accuracy analysis)
  - No Match Review (potential for case reclassification)
- **📈 Unified Post-Review Metrics**: Combined accuracy improvements from all review types
- **🌐 Interactive Dashboard**: Rich visualizations and detailed breakdowns
- **🔧 Robust JSON Parsing**: Advanced error handling for AI responses

## 📁 Repository Structure

```
sutherland_radiology_analysis/
├── src/                          # Core application files
│   ├── streamlit_dashboard.py    # Main Streamlit dashboard
│   ├── main_analysis.py          # Complete analysis pipeline
│   ├── ai_integration.py         # AI/LLM integration with robust JSON parsing
│   ├── accuracy_metrics.py       # Accuracy calculations and metrics
│   └── data_analysis.py          # Data processing utilities
├── data/                         # Input data
│   └── sutherland_radiology_results.csv
├── results/                      # Analysis outputs
│   ├── analysis_results.json     # Core analysis data
│   ├── code_classifications.json # AI code classifications
│   ├── partial_match_reviews.json# Partial match AI reviews
│   ├── comprehensive_metrics.json# All calculated metrics
│   ├── no_match_reviews.json     # No match AI reviews
│   ├── pipeline_summary.json     # Execution summary
│   └── analysis_changes.csv      # Changes tracking
├── docs/                         # Documentation
├── requirements.txt              # Python dependencies
├── config.py                     # Configuration settings
└── README.md                     # This file
```

## 🚀 Quick Start

### 1. Dashboard Only (Streamlit Cloud)

For dashboard deployment, you only need these files:
```
src/streamlit_dashboard.py
src/accuracy_metrics.py 
src/data_analysis.py
data/sutherland_radiology_results.csv
results/*.json
requirements.txt
```

**Deploy to Streamlit Cloud:**
1. Upload these files to a GitHub repository
2. Connect to [Streamlit Cloud](https://share.streamlit.io)
3. Set entry point: `src/streamlit_dashboard.py`

### 2. Complete Analysis Pipeline

**Prerequisites:**
- Python 3.8+
- Azure OpenAI API access
- Required Python packages (see requirements.txt)

**Setup:**
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys in config.py
# Add your Azure OpenAI credentials

# Run complete analysis
python src/main_analysis.py --csv data/sutherland_radiology_results.csv
```

**Launch Dashboard:**
```bash
streamlit run src/streamlit_dashboard.py
```

## 🔧 Configuration

### API Configuration (config.py)
```python
# Azure OpenAI API Keys (required for analysis generation)
OPENAI_API_KEY_1 = "your_api_key_here"
OPENAI_API_KEY_2 = "your_api_key_here" 
OPENAI_API_KEY_3 = "your_api_key_here"
```

### Analysis Options
- `--skip_classification`: Skip code classification step
- `--skip_review`: Skip partial match review step  
- `--skip_no_match_review`: Skip no match review step

## 📊 Analysis Pipeline

### Step 1: Data Analysis
- Identifies missed codes by AI system
- Calculates basic accuracy metrics
- Generates chart-level match distribution

### Step 2: AI Code Classification
- Classifies missed codes as "relevant" or "not relevant"
- Uses advanced medical knowledge prompts
- Provides clinical justification for each classification

### Step 3: Partial Match Review
- AI reviews cases where codes partially match
- Determines which system (AI vs Human) is more accurate
- Identifies specific coding errors and corrections

### Step 3.5: No Match Review (New!)
- Reviews cases with no code overlap
- Assesses potential for reclassification
- Identifies upgrade opportunities (No Match → Partial/Complete Match)

### Step 4: Unified Accuracy Calculation
- Combines improvements from all review types
- Calculates comprehensive before/after metrics
- Provides bifurcated analysis by improvement source

## 🎨 Dashboard Features

### 1. **Accuracy Overview**
- Chart-level and code-level accuracy metrics
- Match distribution visualization
- Key performance indicators

### 2. **Unified Post-Review Accuracy** (New!)
- Combined improvement metrics from all review types
- Bifurcated analysis showing improvement sources:
  - Partial Match Reviews (code-level improvements)
  - No Match Conversions (chart-level improvements)
- Before/after comprehensive comparison

### 3. **Code Importance Analysis**
- Breakdown of missed codes by clinical relevance
- Patient-level distribution analysis
- Relevant vs not relevant code visualization

### 4. **AI Review Results**
- Detailed partial match review outcomes
- AI vs human accuracy comparison
- Code-specific analysis and justifications

### 5. **No Match Review Results** (New!)
- Upgrade potential analysis
- AI vs human performance in no match cases
- Detailed review outcomes and insights

### 6. **Manual Coding Accuracy**
- Human coder performance analysis
- Error identification and patterns
- Improvement recommendations

## 🛠 Technical Architecture

### Robust AI Integration
- **Multi-deployment failover**: Automatic switching between API endpoints
- **Advanced JSON parsing**: 5-layer parsing strategy for reliable data extraction
- **Automatic retry logic**: Handles malformed responses and API errors
- **Progress tracking**: Monitors API call success/failure rates

### Unified Metrics System
- **Combined accuracy calculation**: Integrates partial match and no match improvements
- **Bifurcated analysis**: Separates chart-level vs code-level improvements
- **Comprehensive tracking**: Before/after metrics with detailed breakdowns

### Error Handling
- **Graceful degradation**: System continues even with partial failures
- **Raw response preservation**: Failed parsing attempts saved for inspection
- **Detailed error reporting**: Comprehensive error logging and reporting

## 🔍 Key Metrics Explained

### Chart-Level Metrics
- **Complete Match Rate**: Percentage of charts with identical coding
- **Partial Match Rate**: Percentage of charts with some code overlap
- **No Match Rate**: Percentage of charts with no code overlap

### Code-Level Metrics
- **Overall Accuracy**: Percentage of correctly coded individual codes
- **Miss Rate**: Percentage of human codes missed by AI
- **Precision/Recall**: Standard ML metrics for code prediction

### Unified Post-Review Metrics (New!)
- **Total Combined Improvement**: Chart-level + code-level improvements
- **Improvement by Source**: Breakdown showing contribution from each review type
- **Potential Upgrade Rate**: Percentage of no match cases upgradeable

## 🚀 Enhancement Opportunities

### 1. **Extend Analysis Types**
- Add support for different medical specialties
- Implement trend analysis over time
- Add comparative analysis between different AI models

### 2. **Dashboard Enhancements**
- Add real-time analysis capabilities
- Implement user authentication and role-based access
- Add export functionality for reports

### 3. **AI Integration Improvements**
- Add support for additional LLM providers
- Implement custom fine-tuned models
- Add confidence scoring for AI decisions

### 4. **Data Pipeline Extensions**
- Add automated data ingestion
- Implement data validation and quality checks
- Add support for different input formats

## 📈 Results Summary

Latest analysis results:
- **Original Complete Match Rate**: 48.5%
- **Post-Review Complete Match Rate**: 79.8%
- **Total Improvement**: +31.3 percentage points
- **Code Classifications**: 93 unique codes classified
- **AI Review Success Rate**: 100% (robust JSON parsing)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Sutherland Medical Coding for providing expert coding data
- Azure OpenAI for providing the AI analysis capabilities
- Streamlit for the dashboard framework 