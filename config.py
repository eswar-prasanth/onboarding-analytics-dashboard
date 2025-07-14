import os
from datetime import datetime

# MongoDB Configuration
MONGO_URL = "mongodb+srv://rcdbuser:Sd3b8WfFzSs94lHa@cluster0.sjf0s.mongodb.net/"
DB_NAME = "rapid-claims-9ead3739-1f5a-439a-913d-1035e71d0679"
COLLECTION_NAME = "charts"

# Date Range Configuration
START_DATE = datetime(2025, 2, 10)   # February 10th, 2025
END_DATE = datetime(2025, 7, 10, 23, 59, 59)  # July 10th, 2025 end of day

# Duke Organization ID (you may need to adjust this based on your data structure)
DUKE_ORG_ID = "Duke"  # This might need to be updated based on actual data

# Claim Status Configuration
TARGET_CLAIM_STATUSES = [4, 12]  # 4 = hold, 12 = EHR declined

# OpenAI Deployment Configurations
OPENAI_DEPLOYMENTS = [
    {
        "api_key": "d16e859b58c64ad195d214f2a552924c",
        "api_base": "https://openai-australia-setup.openai.azure.com/",
        "model": "o3-mini",
        "api_version": "2025-01-01-preview",
        "max_tokens_per_request": 128000
    },
    {
        "api_key": "d16e859b58c64ad195d214f2a552924c",
        "api_base": "https://openai-australia-setup.openai.azure.com/",
        "model": "gpt-4o-vision",
        "api_version": "2024-02-15-preview",
        "max_tokens_per_request": 128000
    },
    {
        "api_key": "69e9e7ecc3354a87be17d5ca199af9c2",
        "api_base": "https://rapid-openai-eastus.openai.azure.com/",
        "model": "rapid-eastus-gpt4o",
        "api_version": "2024-02-15-preview",
        "max_tokens_per_request": 128000
    },
    {
        "api_key": "127dfbf25c5145a4994fb7ae1bd8181e",
        "api_base": "https://rapid-openai-east2.openai.azure.com/",
        "model": "rapid-eastus2-gpt4o",
        "api_version": "2024-02-15-preview",
        "max_tokens_per_request": 128000
    },
    {
        "api_key": "42539d7acabd458faf68b5d1142b6c4b",
        "api_base": "https://openai-sweden-setup.openai.azure.com/",
        "model": "rapid-swedencentral-gpt4o",
        "api_version": "2024-02-15-preview",
        "max_tokens_per_request": 128000
    },
    {
        "api_key": "1NB5r6pCKKJ3DZHtbEvBKAjV4Fhy3L5sP45aZHNoiDY30PXIpaULJQQJ99AKAC4f1cMXJ3w3AAABACOGDz3r",
        "api_base": "https://rapid-openai-west.openai.azure.com/",
        "model": "rapid-west-gpt4o",
        "api_version": "2024-02-15-preview",
        "max_tokens_per_request": 128000
    }
]

# Processing Configuration
BATCH_SIZE = 10  # Smaller batch size to prevent timeouts
MAX_WORKERS = 10  # Reduce workers to prevent overwhelming the API

# Output Configuration
OUTPUT_FILE = "duke_hold_analysis_results.csv" 