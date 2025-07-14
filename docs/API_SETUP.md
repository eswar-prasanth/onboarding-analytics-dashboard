# API Setup Guide

This guide explains how to configure Azure OpenAI API access for running the complete analysis pipeline.

## 🔑 Azure OpenAI Setup

### 1. Create Azure OpenAI Resource

1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new "Azure OpenAI" resource
3. Choose your subscription and resource group
4. Select a region that supports your desired models
5. Wait for deployment to complete

### 2. Deploy Models

You'll need access to GPT-4 or similar models. Deploy at least one of:
- `gpt-4`
- `gpt-4-turbo`
- `gpt-4o`
- `o1-preview` (if available)

### 3. Get API Credentials

From your Azure OpenAI resource:
1. Go to "Keys and Endpoint"
2. Copy your API key and endpoint
3. Note your deployment names

### 4. Configure API Keys

Edit `config.py` with your credentials:

```python
# Azure OpenAI API Configuration
OPENAI_API_KEY_1 = "your_primary_api_key_here"
OPENAI_API_KEY_2 = "your_secondary_api_key_here"  # Optional backup
OPENAI_API_KEY_3 = "your_tertiary_api_key_here"   # Optional backup

# Update the deployment configurations in ai_integration.py
# Replace the model names and endpoints with your actual deployments
```

### 5. Update Deployment Configuration

In `src/ai_integration.py`, update the `llm_deployments` list:

```python
self.llm_deployments = [
    {
        "api_key": "your_api_key_here",
        "api_base": "https://your-resource-name.openai.azure.com/",
        "model": "your-deployment-name",
        "api_version": "2024-02-15-preview",
        "max_tokens_per_request": 128000
    },
    # Add more deployments for redundancy
]
```

## 🔐 Security Best Practices

### Environment Variables (Recommended)

Instead of hardcoding API keys, use environment variables:

1. Create a `.env` file (already in .gitignore):
```bash
AZURE_OPENAI_KEY_1=your_api_key_here
AZURE_OPENAI_ENDPOINT_1=https://your-resource.openai.azure.com/
AZURE_OPENAI_MODEL_1=your-deployment-name
```

2. Update `config.py` to use environment variables:
```python
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY_1 = os.getenv('AZURE_OPENAI_KEY_1')
OPENAI_API_ENDPOINT_1 = os.getenv('AZURE_OPENAI_ENDPOINT_1')
OPENAI_MODEL_1 = os.getenv('AZURE_OPENAI_MODEL_1')
```

### API Key Rotation

The system supports multiple API keys for:
- **High availability**: Automatic failover if one endpoint fails
- **Rate limiting**: Distribute load across multiple deployments
- **Cost management**: Use different tiers for different operations

## 💰 Cost Considerations

### Token Usage Estimates

For a typical analysis of 100 patients:
- **Code Classification**: ~50,000 tokens ($0.50-1.00)
- **Partial Match Review**: ~200,000 tokens ($2.00-4.00)
- **No Match Review**: ~50,000 tokens ($0.50-1.00)
- **Total**: ~300,000 tokens ($3.00-6.00)

### Cost Optimization Tips

1. **Use appropriate models**: GPT-4 for complex analysis, GPT-3.5 for simple tasks
2. **Skip unnecessary steps**: Use skip flags for testing
3. **Batch processing**: Process larger datasets to amortize costs
4. **Cache results**: Reuse classification results across analyses

## 🧪 Testing Your Setup

Run a small test to verify your configuration:

```bash
# Test with minimal data
python src/main_analysis.py --csv data/sutherland_radiology_results.csv --skip_review --skip_no_match_review
```

This will only run data analysis and code classification, using minimal API calls.

## 🔧 Troubleshooting

### Common Issues

1. **"API key not found"**
   - Check your config.py file
   - Verify environment variables are loaded

2. **"Model not found"**
   - Verify your deployment names in Azure
   - Check the model is deployed and available

3. **"Rate limit exceeded"**
   - Add delays between requests
   - Use multiple API keys for load balancing

4. **"Authentication failed"**
   - Regenerate your API keys in Azure
   - Check endpoint URLs are correct

### API Limits

Azure OpenAI has various limits:
- **Requests per minute**: Varies by model and tier
- **Tokens per minute**: Varies by model and tier
- **Monthly quotas**: Check your subscription limits

The system includes automatic retry logic and deployment switching to handle these limits gracefully.

## 📞 Support

For Azure OpenAI specific issues:
- [Azure OpenAI Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure Support](https://azure.microsoft.com/en-us/support/)

For application-specific issues:
- Check the main README.md
- Review error logs in the console output
- Create an issue in the repository 