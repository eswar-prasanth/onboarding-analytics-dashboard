import json
import re
import time
from typing import Dict, List, Any, Union
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

class O3AIIntegration:
    def __init__(self):
        """Initialize the O3 AI integration with multiple deployment endpoints"""
        self.llm_deployments = [
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
        
        self.current_llm_index = 0
        self.llm = self.create_llm(self.llm_deployments[self.current_llm_index])
        self.total_sleep_time = 0
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking for robust JSON parsing
        self.api_calls_made = 0
        self.successful_calls = 0
        self.failed_calls = 0



    def robust_json_parse(self, response_text: str, retry_count: int = 0) -> Dict:
        """
        Robust JSON parsing that handles various formats and edge cases
        """
        if not response_text or not response_text.strip():
            return {"error": "Empty response", "raw_response": response_text}
        
        # Method 1: Direct JSON parsing
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass
        
        # Method 2: Extract JSON from markdown code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, response_text, re.DOTALL | re.IGNORECASE)
        if matches:
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        # Method 3: Find JSON-like structure without markdown
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        if matches:
            # Try the longest match first (most likely to be complete)
            matches.sort(key=len, reverse=True)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        # Method 4: Clean and fix common JSON issues
        cleaned_text = self.clean_json_text(response_text)
        if cleaned_text:
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError:
                pass
        
        # Method 5: Extract key-value pairs manually and reconstruct JSON
        extracted_data = self.extract_key_values(response_text)
        if extracted_data:
            return extracted_data
        
        # If all methods fail, return error with raw response for manual inspection
        return {
            "error": "Failed to parse JSON from response",
            "raw_response": response_text,
            "parsing_attempts": 5
        }

    def clean_json_text(self, text: str) -> str:
        """Clean text to make it more likely to be valid JSON"""
        # Remove common prefixes/suffixes
        text = re.sub(r'^[^{]*', '', text)  # Remove everything before first {
        text = re.sub(r'[^}]*$', '', text)  # Remove everything after last }
        
        # Fix common issues
        text = text.replace('\n', ' ')  # Replace newlines with spaces
        text = text.replace('\t', ' ')  # Replace tabs with spaces
        text = re.sub(r'\s+', ' ', text)  # Collapse multiple spaces
        text = text.replace(': true', ': True')  # Python boolean format
        text = text.replace(': false', ': False')  # Python boolean format
        text = text.replace(': null', ': None')  # Python null format
        
        # Fix unescaped quotes in strings
        text = re.sub(r'(?<!\\)"(?=([^"\\]*(\\.[^"\\]*)*)+")', '\\"', text)
        
        return text.strip()

    def extract_key_values(self, text: str) -> Dict:
        """Extract key-value pairs manually and reconstruct JSON"""
        try:
            # Common patterns for extracting structured data
            patterns = {
                'patient_id': r'"?patient_id"?\s*:\s*"?([^",\s]+)"?',
                'analysis': r'"?analysis"?\s*:\s*\[(.*?)\]',
                'coding_accuracy_score': r'"?coding_accuracy_score"?\s*:\s*\{(.*?)\}',
                'match_potential': r'"?match_potential"?\s*:\s*\{(.*?)\}',
                'overall_assessment': r'"?overall_assessment"?\s*:\s*"([^"]+)"'
            }
            
            extracted = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    if key == 'analysis':
                        # Handle analysis array
                        extracted[key] = []
                    elif key in ['coding_accuracy_score', 'match_potential']:
                        # Handle nested objects
                        try:
                            obj_content = '{' + match.group(1) + '}'
                            extracted[key] = json.loads(obj_content)
                        except:
                            extracted[key] = {}
                    else:
                        extracted[key] = match.group(1)
            
            return extracted if extracted else None
        except Exception:
            return None

    def invoke_llm_with_json_retry(self, messages, max_json_retries: int = 2) -> Dict:
        """
        Invoke LLM with automatic JSON retry if parsing fails
        """
        for attempt in range(max_json_retries + 1):
            try:
                # Add JSON format instruction on retry attempts
                if attempt > 0:
                    json_reminder = "\n\nIMPORTANT: Please ensure your response is valid JSON format only. No markdown, no explanations, just pure JSON."
                    if isinstance(messages[-1], HumanMessage):
                        messages[-1].content += json_reminder
                    else:
                        messages.append(HumanMessage(content=json_reminder))
                
                response = self.invoke_llm(messages)
                self.api_calls_made += 1
                
                # Try to parse JSON
                parsed_response = self.robust_json_parse(response.content)
                
                if "error" not in parsed_response:
                    self.successful_calls += 1
                    return parsed_response
                elif attempt < max_json_retries:
                    print(f"JSON parsing failed on attempt {attempt + 1}, retrying...")
                    time.sleep(1)  # Brief pause before retry
                else:
                    self.failed_calls += 1
                    return parsed_response
                    
            except Exception as e:
                self.failed_calls += 1
                if attempt < max_json_retries:
                    print(f"API error on attempt {attempt + 1}: {e}, retrying...")
                    time.sleep(2)
                else:
                    return {
                        "error": f"API error after {max_json_retries + 1} attempts: {str(e)}",
                        "raw_response": ""
                    }
        
        return {"error": "Maximum retry attempts exceeded", "raw_response": ""}

    def create_llm(self, deployment):
        """Create LLM instance with the given deployment"""
        print(f"Creating LLM with deployment: {deployment['model']}")
        return AzureChatOpenAI(
            openai_api_key=deployment["api_key"],
            azure_endpoint=deployment["api_base"],
            azure_deployment=deployment["model"],
            api_version=deployment["api_version"],
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

    def invoke_llm(self, messages):
        """Invoke the LLM API and handle errors by switching deployments"""
        max_cycles = 3
        cycle_count = 0
        
        while cycle_count < max_cycles:
            for _ in range(len(self.llm_deployments)):
                try:
                    response = self.llm.invoke(messages)
                    return response
                except Exception as e:
                    print(f"Error during LLM invocation with deployment {self.llm_deployments[self.current_llm_index]['model']}: {e}")
                    print("Switching to next deployment...")
                    self.current_llm_index = (self.current_llm_index + 1) % len(self.llm_deployments)
                    self.llm = self.create_llm(self.llm_deployments[self.current_llm_index])
            
            print(f"Completed cycle {cycle_count + 1}/{max_cycles}. Sleeping for 10 seconds...")
            time.sleep(10)
            self.total_sleep_time += 10
            cycle_count += 1
        
        raise Exception(f"Failed to get response after {max_cycles} cycles through all deployments")

    def get_code_classification_prompt(self) -> str:
        """Get the comprehensive prompt for code classification"""
        return """You are an expert medical coding specialist with deep knowledge of ICD-10-CM codes and their clinical significance. Your task is to classify ICD codes that were missed by an AI system as either "important" or "unimportant" based on their clinical significance in radiology reporting.

## Classification Guidelines:

### IMPORTANT CODES (Clinically Significant):
1. **Cancer Codes (C series)**: All malignant neoplasms and carcinomas
   - C00-C97: Malignant neoplasms
   - These directly impact patient prognosis and treatment decisions

2. **Acute Conditions**: 
   - Stroke codes (I60-I69): Cerebrovascular diseases
   - Heart attack codes (I20-I25): Ischemic heart diseases
   - Acute infections with systemic implications

3. **Structural Abnormalities**:
   - Congenital anomalies affecting major organs
   - Significant anatomical variants that impact treatment

4. **Procedural Complications**:
   - T80-T88: Complications of surgical and medical care
   - Device malfunction or failure codes

5. **Progressive Diseases**:
   - Codes indicating disease progression or worsening

### UNIMPORTANT CODES (Less Clinically Significant):
1. **Symptom Codes (R series)**: 
   - R00-R99: Symptoms, signs and abnormal clinical findings
   - Generally non-specific findings (unless indicating acute conditions)

2. **History Codes (Z series)**:
   - Z80-Z99: Personal history of diseases
   - Past medical history without current clinical impact

3. **Screening/Surveillance Codes**:
   - Z00-Z13: Persons encountering health services for examinations
   - Routine follow-up without active disease

4. **Minor Findings**:
   - Degenerative changes (unless severe)
   - Incidental findings without clinical significance
   - Normal variants

5. **Administrative Codes**:
   - Encounter codes for routine procedures
   - Status codes for completed treatments

## Response Format:
Provide your response as a JSON object with the following structure:

```json
{
  "code": "ICD_CODE",
  "classification": "important|unimportant",
  "category": "specific_category_from_above",
  "reasoning": "detailed_explanation_of_classification",
  "clinical_impact": "high|medium|low",
  "radiology_relevance": "explanation_of_relevance_to_radiology_reporting"
}
```

## Examples:

**Example 1 - Important Code:**
```json
{
  "code": "C78.7",
  "classification": "important",
  "category": "Cancer Codes",
  "reasoning": "Secondary malignant neoplasm of liver and intrahepatic bile duct indicates metastatic cancer, which is crucial for staging, prognosis, and treatment planning",
  "clinical_impact": "high",
  "radiology_relevance": "Critical for radiologists to report metastatic disease as it directly impacts oncological management and staging"
}
```

**Example 2 - Unimportant Code:**
```json
{
  "code": "Z87.891",
  "classification": "unimportant",
  "category": "History Codes",
  "reasoning": "Personal history of nicotine dependence is historical information that doesn't change current imaging interpretation or immediate patient management",
  "clinical_impact": "low",
  "radiology_relevance": "Historical context but doesn't affect current radiology findings or reporting requirements"
}
```

**Example 3 - Important Code:**
```json
{
  "code": "I63.512",
  "classification": "important",
  "category": "Acute Conditions",
  "reasoning": "Cerebral infarction due to unspecified occlusion or stenosis of left middle cerebral artery is an acute stroke requiring immediate intervention",
  "clinical_impact": "high",
  "radiology_relevance": "Critical finding that radiologists must report immediately as it requires emergent treatment and affects patient outcomes"
}
```

Analyze the provided ICD code and classify it according to these guidelines."""

    def classify_missed_codes(self, missed_codes: List[str]) -> List[Dict]:
        """Classify a list of missed codes as important or unimportant"""
        results = []
        
        system_prompt = self.get_code_classification_prompt()
        
        for code in missed_codes:
            try:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Please classify this ICD code: {code}")
                ]
                
                response = self.invoke_llm_with_json_retry(messages)
                
                # Response is already parsed by invoke_llm_with_json_retry
                if "error" not in response:
                    response['original_code'] = code
                    results.append(response)
                else:
                    # Fallback if JSON parsing fails
                    results.append({
                        'code': code,
                        'classification': 'unimportant',
                        'category': 'parsing_error',
                        'reasoning': 'Failed to parse AI response',
                        'clinical_impact': 'unknown',
                        'radiology_relevance': 'unknown',
                        'original_code': code,
                        'raw_response': response.get('raw_response', '')
                    })
                
                print(f"Classified code {code}: {response.get('classification', 'error')}")
                
            except Exception as e:
                print(f"Error classifying code {code}: {e}")
                results.append({
                    'code': code,
                    'classification': 'error',
                    'category': 'api_error',
                    'reasoning': f'API error: {str(e)}',
                    'clinical_impact': 'unknown',
                    'radiology_relevance': 'unknown',
                    'original_code': code
                })
        
        return results

    def get_partial_match_review_prompt(self) -> str:
        """Get the comprehensive prompt for partial match review"""
        return """You are an expert medical coder specializing in radiology reports with extensive knowledge of ICD-10-CM coding guidelines. You are reviewing cases where there are discrepancies between manual Sutherland coding and AI coding to determine which is more accurate.

## Radiology Coding Guidelines for Reference:

### General Guidelines:
1. **Definitive Diagnoses**: Code all definitive diagnoses documented in the report
2. **Signs/Symptoms**: Related signs/symptoms to definitive conditions are NOT coded separately
3. **Unrelated Findings**: Signs/symptoms unrelated to definitive conditions MAY be coded as additional diagnoses
4. **Medical Necessity**: Primary diagnosis codes should meet medical necessity
5. **Comprehensive Coding**: Code all related/pertinent diagnosis codes from the entire report including findings

### Specific Guidelines:
1. **Low Dose CT Lung Screening**: 
   - Smoking status is First-Listed/Primary diagnosis
   - History: Z87.891 (personal history of tobacco use)
   - Current smoker: F17.210-F17.219 series

2. **Injury/Trauma/Fall**:
   - General indications (Fall, MVC, Assault) → Code to Z04 series
   - Specific injury documented → Code site-specific injury + external cause code
   - Incidental findings NOT coded for trauma
   - Fall as "current condition" if injury within one month

3. **Specific Conditions**:
   - Osteoarthritis + Joint Effusion → Code only Osteoarthritis
   - Elevated D-Dimer → R79.1
   - Discoid lung changes without atelectasis → R91.8
   - Infant lung opacity → R91.8

## Analysis Framework:

For each code discrepancy, determine:
1. **Code Status**: "missed" (Sutherland coded but AI didn't) or "substituted" (AI used different code)
2. **Correctness**: Which coding is more accurate based on guidelines
3. **Reasoning**: Detailed explanation citing specific guidelines
4. **Clinical Context**: Relevance to the radiology findings

## Response Format:

Provide your response as a JSON object:

```json
{
  "patient_id": "PATIENT_ID",
  "analysis": [
    {
      "sutherland_code": "CODE",
      "ai_code": "CODE_OR_NULL",
      "status": "missed|substituted",
      "is_sutherland_correct": true|false,
      "is_ai_correct": true|false,
      "reasoning": "detailed_explanation_with_guideline_citations",
      "guideline_reference": "specific_guideline_section",
      "clinical_context": "relevance_to_radiology_findings",
      "recommended_action": "keep_sutherland|keep_ai|use_both|neither"
    }
  ],
  "overall_assessment": "summary_of_coding_accuracy",
  "coding_accuracy_score": {
    "sutherland_score": 0.0-1.0,
    "ai_score": 0.0-1.0
  }
}
```

## Examples:

**Example 1 - Missed Important Code:**
```json
{
  "patient_id": "12345",
  "analysis": [
    {
      "sutherland_code": "I63.512",
      "ai_code": null,
      "status": "missed",
      "is_sutherland_correct": true,
      "is_ai_correct": false,
      "reasoning": "The clinical text clearly documents 'acute left middle cerebral artery territory infarct' which directly corresponds to I63.512. This is a definitive diagnosis that must be coded per general guidelines.",
      "guideline_reference": "General Guidelines: Definitive Diagnoses",
      "clinical_context": "Primary finding in stroke protocol imaging requiring immediate clinical attention",
      "recommended_action": "keep_sutherland"
    }
  ],
  "overall_assessment": "Sutherland coding is more accurate - missed critical stroke diagnosis",
  "coding_accuracy_score": {
    "sutherland_score": 1.0,
    "ai_score": 0.0
  }
}
```

**Example 2 - AI Substitution More Accurate:**
```json
{
  "patient_id": "67890",
  "analysis": [
    {
      "sutherland_code": "R91.8",
      "ai_code": "J44.1",
      "status": "substituted",
      "is_sutherland_correct": false,
      "is_ai_correct": true,
      "reasoning": "Clinical text documents 'COPD exacerbation with increased dyspnea'. While lung findings are present, the definitive diagnosis of COPD exacerbation should be coded rather than the non-specific lung finding.",
      "guideline_reference": "General Guidelines: Definitive diagnoses over signs/symptoms",
      "clinical_context": "COPD exacerbation is the primary condition explaining the radiological findings",
      "recommended_action": "keep_ai"
    }
  ],
  "overall_assessment": "AI coding is more accurate - correctly identified definitive diagnosis",
  "coding_accuracy_score": {
    "sutherland_score": 0.3,
    "ai_score": 1.0
  }
}
```

Analyze the provided case and determine the coding accuracy based on the clinical text and established guidelines."""

    def review_partial_match_case(self, case: Dict) -> Dict:
        """Review a single partial match case"""
        system_prompt = self.get_partial_match_review_prompt()
        
        # Prepare case information
        case_info = f"""
Patient ID: {case['patient_id']}

Sutherland Codes: {', '.join(case['sutherland_codes'])}
AI Codes: {', '.join(case['ai_codes'])}

Codes Missed by AI: {', '.join(case['missed_by_ai'])}
Extra Codes by AI: {', '.join(case['extra_by_ai'])}

Clinical Text:
{case['clinical_text']}

Please analyze each code discrepancy and provide your assessment.
"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=case_info)
            ]
            
            response = self.invoke_llm_with_json_retry(messages)
            
            # Response is already parsed by invoke_llm_with_json_retry
            if "error" not in response:
                return response
            else:
                return {
                    'patient_id': case['patient_id'],
                    'error': 'Failed to parse AI response',
                    'raw_response': response.get('raw_response', '')
                }
                
        except Exception as e:
            return {
                'patient_id': case['patient_id'],
                'error': f'API error: {str(e)}'
            }

    def review_partial_matches_parallel(self, cases: List[Dict], max_workers: int = 5) -> List[Dict]:
        """Review multiple partial match cases in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_case = {
                executor.submit(self.review_partial_match_case, case): case 
                for case in cases
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_case):
                case = future_to_case[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"Completed review for patient {case['patient_id']}")
                except Exception as e:
                    print(f"Error reviewing patient {case['patient_id']}: {e}")
                    results.append({
                        'patient_id': case['patient_id'],
                        'error': f'Execution error: {str(e)}'
                    })
        
        return results

    def save_results(self, results: List[Dict], filename: str):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to {filename}")

    def get_no_match_review_prompt(self) -> str:
        """Get the system prompt for reviewing No Match cases"""
        return """You are a medical coding expert reviewing radiology cases with No Match between Sutherland manual coders and AI coding systems.

Your task is to analyze cases where Sutherland and AI coding have significant discrepancies (No Match cases), and determine:
1. Which coding approach is more accurate for each code
2. Whether the No Match case could potentially be upgraded to Partial Match or Complete Match
3. Assess the clinical significance of the discrepancies

## Analysis Framework:

For each code present in either system:
- **Sutherland-only codes**: Evaluate if these codes are clinically justified
- **AI-only codes**: Evaluate if these codes are clinically justified  
- **Overall assessment**: Determine which coding approach is more accurate

## Response Format:
Respond with a JSON object containing:

```json
{
  "patient_id": "patient_identifier",
  "analysis": [
    {
      "sutherland_code": "code or null",
      "ai_code": "code or null", 
      "status": "sutherland_only|ai_only|different_approach",
      "is_sutherland_correct": true/false,
      "is_ai_correct": true/false,
      "clinical_justification": "explanation of which is correct and why",
      "severity": "critical|moderate|minor"
    }
  ],
  "coding_accuracy_score": {
    "sutherland_score": 0.0-1.0,
    "ai_score": 0.0-1.0
  },
  "match_potential": {
    "could_be_partial_match": true/false,
    "could_be_complete_match": true/false,
    "reasoning": "explanation"
  },
  "overall_assessment": "detailed summary of findings and recommendations"
}
```

## Guidelines:
- Be thorough in clinical justification
- Consider that No Match cases often have fundamental differences in coding approach
- Focus on patient safety and billing accuracy
- Assess whether discrepancies are due to different interpretations or actual errors
- Determine if the case classification could be improved with better alignment"""

    def review_no_match_case(self, case: Dict) -> Dict:
        """Review a single No Match case"""
        system_prompt = self.get_no_match_review_prompt()
        
        # Prepare case information
        case_info = f"""
Patient ID: {case['patient_id']}

Sutherland Codes: {', '.join(case['sutherland_codes'])}
AI Codes: {', '.join(case['ai_codes'])}

Clinical Text:
{case['clinical_text']}

Please analyze this No Match case and provide your assessment of coding accuracy and potential for reclassification.
"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=case_info)
            ]
            
            response = self.invoke_llm_with_json_retry(messages)
            
            # Response is already parsed by invoke_llm_with_json_retry
            if "error" not in response:
                return response
            else:
                return {
                    'patient_id': case['patient_id'],
                    'error': 'Failed to parse AI response',
                    'raw_response': response.get('raw_response', '')
                }
                
        except Exception as e:
            return {
                'patient_id': case['patient_id'],
                'error': f'API error: {str(e)}'
            }

    def review_no_matches_parallel(self, cases: List[Dict], max_workers: int = 5) -> List[Dict]:
        """Review multiple No Match cases in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_case = {
                executor.submit(self.review_no_match_case, case): case 
                for case in cases
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_case):
                case = future_to_case[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"Completed No Match review for patient {case['patient_id']}")
                except Exception as e:
                    print(f"Error reviewing No Match patient {case['patient_id']}: {e}")
                    results.append({
                        'patient_id': case['patient_id'],
                        'error': f'Execution error: {str(e)}'
                    })
        
        return results

if __name__ == "__main__":
    # Test the AI integration
    ai = O3AIIntegration()
    
    # Test code classification
    test_codes = ["C78.7", "Z87.891", "I63.512", "R91.8"]
    classifications = ai.classify_missed_codes(test_codes)
    print("Code Classifications:")
    for c in classifications:
        print(f"  {c['code']}: {c['classification']}")
    
    ai.save_results(classifications, 'test_classifications.json') 