# Deployment Guide

This guide covers different deployment scenarios for the Sutherland Radiology Analysis application.

## 🌐 Streamlit Cloud Deployment (Recommended for Dashboard)

### Prerequisites
- GitHub account
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))

### Files Required
For dashboard-only deployment, you need these essential files:
```
src/
├── streamlit_dashboard.py
├── accuracy_metrics.py
└── data_analysis.py
data/
└── sutherland_radiology_results.csv
results/
├── analysis_results.json
├── code_classifications.json
├── partial_match_reviews.json
├── comprehensive_metrics.json
└── no_match_reviews.json
requirements.txt
```

### Step-by-Step Deployment

1. **Create GitHub Repository**
   ```bash
   # Clone or download this repository
   git clone <your-repo-url>
   cd sutherland_radiology_analysis
   
   # Create new repository on GitHub and push
   git remote add origin <your-github-repo-url>
   git add .
   git commit -m "Initial dashboard deployment"
   git push -u origin main
   ```

2. **Connect to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub account
   - Select your repository
   - Set main file path: `src/streamlit_dashboard.py`
   - Click "Deploy"

3. **Configure (if needed)**
   - App will automatically install requirements.txt
   - No environment variables needed for dashboard-only deployment
   - Public URL will be generated automatically

### Troubleshooting Streamlit Cloud

**Common Issues:**
- **File not found errors**: Ensure all file paths are relative and correct
- **Module import errors**: Check that all required files are in the repository
- **Memory limits**: Large JSON files may hit Streamlit Cloud limits

**Solutions:**
- Keep result files under 100MB total
- Use relative imports (already implemented)
- Check Streamlit Cloud logs for specific error messages

## 🖥️ Local Development

### Prerequisites
```bash
# Python 3.8+
python --version

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

1. **Dashboard Only**
   ```bash
   # Navigate to repository
   cd sutherland_radiology_analysis
   
   # Run dashboard
   streamlit run src/streamlit_dashboard.py
   ```

2. **Complete Analysis Pipeline**
   ```bash
   # Configure API keys first (see docs/API_SETUP.md)
   
   # Run full analysis
   python src/main_analysis.py --csv data/sutherland_radiology_results.csv
   
   # Then run dashboard
   streamlit run src/streamlit_dashboard.py
   ```

### Development Workflow

1. **Make changes** to source files
2. **Test locally** using above commands
3. **Commit changes** to git
4. **Push to GitHub** (will auto-deploy to Streamlit Cloud)

## 🏗️ Production Deployment

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY src/ ./src/
COPY data/ ./data/
COPY results/ ./results/

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run application
CMD ["streamlit", "run", "src/streamlit_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
# Build image
docker build -t sutherland-analysis .

# Run container
docker run -p 8501:8501 sutherland-analysis
```

### Cloud Platform Deployment

#### Heroku
```bash
# Install Heroku CLI and login
heroku create your-app-name

# Add Python buildpack
heroku buildpacks:set heroku/python

# Create Procfile
echo "web: streamlit run src/streamlit_dashboard.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# Deploy
git push heroku main
```

#### AWS EC2
```bash
# Launch EC2 instance (Ubuntu 20.04+)
# SSH into instance

# Install dependencies
sudo apt update
sudo apt install python3-pip git

# Clone repository
git clone <your-repo-url>
cd sutherland_radiology_analysis

# Install Python packages
pip3 install -r requirements.txt

# Run with PM2 for process management
npm install -g pm2
pm2 start "streamlit run src/streamlit_dashboard.py --server.port=8501 --server.address=0.0.0.0" --name sutherland-analysis

# Setup nginx reverse proxy (optional)
```

#### Google Cloud Platform
```bash
# Install gcloud CLI
gcloud init

# Create app.yaml for App Engine
cat > app.yaml << EOF
runtime: python39
entrypoint: streamlit run src/streamlit_dashboard.py --server.port=\$PORT --server.address=0.0.0.0

automatic_scaling:
  min_instances: 1
  max_instances: 10
EOF

# Deploy
gcloud app deploy
```

## 🔐 Environment Configuration

### Environment Variables

For production deployments, use environment variables for configuration:

```bash
# .env file (not in git)
STREAMLIT_THEME_BASE="light"
STREAMLIT_THEME_PRIMARY_COLOR="#FF6B6B"
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# For analysis pipeline
AZURE_OPENAI_KEY_1=your_api_key_here
AZURE_OPENAI_ENDPOINT_1=https://your-resource.openai.azure.com/
```

### Streamlit Configuration

Create `.streamlit/config.toml`:
```toml
[theme]
base = "light"
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[server]
port = 8501
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

## 📊 Performance Optimization

### For Large Datasets

1. **Data Preprocessing**
   ```python
   # Pre-process large CSV files
   df = pd.read_csv('large_file.csv')
   df_sample = df.sample(n=1000)  # Use sample for development
   df_sample.to_csv('data/sample_data.csv')
   ```

2. **Caching Strategy**
   ```python
   # Use Streamlit caching
   @st.cache_data
   def load_analysis_results():
       with open('results/comprehensive_metrics.json') as f:
           return json.load(f)
   ```

3. **Memory Management**
   - Keep JSON files under 100MB
   - Use pagination for large tables
   - Implement lazy loading for charts

### Load Testing

```bash
# Install locust for load testing
pip install locust

# Create locustfile.py for testing
# Run load tests
locust -f locustfile.py --host=http://localhost:8501
```

## 🔍 Monitoring and Logging

### Application Monitoring

```python
# Add to streamlit_dashboard.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log user interactions
if st.button('Run Analysis'):
    logging.info(f"User initiated analysis at {datetime.now()}")
```

### Health Checks

```python
# Add health check endpoint
def health_check():
    try:
        # Test data loading
        load_analysis_results()
        return {"status": "healthy", "timestamp": datetime.now()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 🚨 Troubleshooting

### Common Deployment Issues

1. **Import Errors**
   ```bash
   # Fix: Ensure all files are in correct directories
   # Check: requirements.txt has all dependencies
   ```

2. **Memory Issues**
   ```bash
   # Fix: Reduce data size or upgrade hosting plan
   # Check: Use data sampling for development
   ```

3. **Performance Issues**
   ```bash
   # Fix: Implement caching and pagination
   # Check: Profile app with streamlit profiler
   ```

### Debugging Tools

```bash
# Streamlit debugging
streamlit run src/streamlit_dashboard.py --logger.level=debug

# Python debugging
python -m pdb src/main_analysis.py

# Memory profiling
pip install memory-profiler
python -m memory_profiler src/streamlit_dashboard.py
```

## 📱 Mobile Optimization

Streamlit apps are automatically mobile-responsive, but for better experience:

```python
# Add mobile-friendly styling
st.markdown("""
<style>
    @media (max-width: 768px) {
        .metric-container {
            flex-direction: column;
        }
    }
</style>
""", unsafe_allow_html=True)
```

## 🔄 Continuous Deployment

### GitHub Actions

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Streamlit Cloud

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Test application
      run: |
        python -m pytest tests/ || echo "No tests yet"
    
    # Streamlit Cloud auto-deploys on push to main
```

This completes your deployment setup! Choose the method that best fits your needs and infrastructure. 