import pandas as pd
import numpy as np
from typing import Dict, List, Set, Tuple
import json
import re

class SutherlandDataAnalyzer:
    def __init__(self, csv_file_path: str):
        """Initialize the analyzer with the CSV data"""
        self.csv_file_path = csv_file_path
        self.df = None
        self.load_data()
        
    def load_data(self):
        """Load and preprocess the CSV data"""
        try:
            self.df = pd.read_csv(self.csv_file_path)
            print(f"Loaded {len(self.df)} records from {self.csv_file_path}")
            
            # Clean and preprocess the data
            self.df['SMC Coded'] = self.df['SMC Coded'].fillna('')
            self.df['Rapidclaims Codes'] = self.df['Rapidclaims Codes'].fillna('')
            
            print(f"Data columns: {list(self.df.columns)}")
            print(f"Match Result distribution:\n{self.df['Match Result'].value_counts()}")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def parse_codes(self, code_string: str) -> Set[str]:
        """Parse comma-separated codes and return as set"""
        if pd.isna(code_string) or code_string == '':
            return set()
        
        # Split by comma and clean codes
        codes = [code.strip() for code in str(code_string).split(',')]
        return set(code for code in codes if code)
    
    def analyze_missed_codes(self) -> Dict:
        """Analyze codes missed by AI compared to Sutherland manual coding"""
        results = {
            'missed_code_analysis': [],
            'code_frequency': {},
            'patient_level_analysis': [],
            'summary_stats': {}
        }
        
        total_sutherland_codes = 0
        total_missed_codes = 0
        missed_code_freq = {}
        
        for idx, row in self.df.iterrows():
            patient_id = row['Patient ID']
            sutherland_codes = self.parse_codes(row['SMC Coded'])
            ai_codes = self.parse_codes(row['Rapidclaims Codes'])
            match_result = row['Match Result']
            
            # Find codes that Sutherland coded but AI missed
            missed_by_ai = sutherland_codes - ai_codes
            
            # Find codes that AI added (extra codes)
            extra_by_ai = ai_codes - sutherland_codes
            
            total_sutherland_codes += len(sutherland_codes)
            total_missed_codes += len(missed_by_ai)
            
            # Track frequency of missed codes
            for code in missed_by_ai:
                missed_code_freq[code] = missed_code_freq.get(code, 0) + 1
            
            # Store patient-level analysis
            patient_analysis = {
                'patient_id': patient_id,
                'sutherland_codes': list(sutherland_codes),
                'ai_codes': list(ai_codes),
                'missed_by_ai': list(missed_by_ai),
                'extra_by_ai': list(extra_by_ai),
                'match_result': match_result,
                'missed_count': len(missed_by_ai),
                'extra_count': len(extra_by_ai),
                'clinical_text': row['clinical text']
            }
            
            results['patient_level_analysis'].append(patient_analysis)
            
            # Add to missed code analysis for each missed code
            for code in missed_by_ai:
                results['missed_code_analysis'].append({
                    'patient_id': patient_id,
                    'missed_code': code,
                    'all_sutherland_codes': list(sutherland_codes),
                    'all_ai_codes': list(ai_codes),
                    'match_result': match_result,
                    'clinical_text': row['clinical text']
                })
        
        # Sort missed codes by frequency
        results['code_frequency'] = dict(sorted(missed_code_freq.items(), 
                                               key=lambda x: x[1], reverse=True))
        
        # Calculate summary statistics
        results['summary_stats'] = {
            'total_patients': len(self.df),
            'total_sutherland_codes': total_sutherland_codes,
            'total_missed_codes': total_missed_codes,
            'miss_rate': total_missed_codes / total_sutherland_codes if total_sutherland_codes > 0 else 0,
            'unique_missed_codes': len(missed_code_freq),
            'avg_missed_per_patient': total_missed_codes / len(self.df),
            'match_distribution': self.df['Match Result'].value_counts().to_dict()
        }
        
        return results
    
    def get_partial_match_cases(self) -> List[Dict]:
        """Get all partial match cases for AI review"""
        partial_matches = self.df[self.df['Match Result'] == 'Partial Match'].copy()
        
        cases = []
        for idx, row in partial_matches.iterrows():
            sutherland_codes = self.parse_codes(row['SMC Coded'])
            ai_codes = self.parse_codes(row['Rapidclaims Codes'])
            
            case = {
                'patient_id': row['Patient ID'],
                'sutherland_codes': list(sutherland_codes),
                'ai_codes': list(ai_codes),
                'missed_by_ai': list(sutherland_codes - ai_codes),
                'extra_by_ai': list(ai_codes - sutherland_codes),
                'clinical_text': row['clinical text']
            }
            cases.append(case)
        
        return cases
    
    def get_no_match_cases(self) -> List[Dict]:
        """Get all no match cases for analysis"""
        no_matches = self.df[self.df['Match Result'] == 'No Match'].copy()
        
        cases = []
        for idx, row in no_matches.iterrows():
            sutherland_codes = self.parse_codes(row['SMC Coded'])
            ai_codes = self.parse_codes(row['Rapidclaims Codes'])
            
            case = {
                'patient_id': row['Patient ID'],
                'sutherland_codes': list(sutherland_codes),
                'ai_codes': list(ai_codes),
                'clinical_text': row['clinical text']
            }
            cases.append(case)
        
        return cases
    
    def save_analysis_results(self, results: Dict, output_file: str):
        """Save analysis results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Analysis results saved to {output_file}")
    
    def print_summary(self, results: Dict):
        """Print summary of analysis results"""
        stats = results['summary_stats']
        
        print("\n=== SUTHERLAND CODING ANALYSIS SUMMARY ===")
        print(f"Total Patients: {stats['total_patients']}")
        print(f"Total Sutherland Codes: {stats['total_sutherland_codes']}")
        print(f"Total Missed by AI: {stats['total_missed_codes']}")
        print(f"Miss Rate: {stats['miss_rate']:.2%}")
        print(f"Unique Missed Codes: {stats['unique_missed_codes']}")
        print(f"Average Missed per Patient: {stats['avg_missed_per_patient']:.2f}")
        
        print(f"\nMatch Distribution:")
        for match_type, count in stats['match_distribution'].items():
            print(f"  {match_type}: {count}")
        
        print(f"\nTop 10 Most Frequently Missed Codes:")
        for i, (code, freq) in enumerate(list(results['code_frequency'].items())[:10]):
            print(f"  {i+1}. {code}: {freq} times")

if __name__ == "__main__":
    # Test the analyzer
    analyzer = SutherlandDataAnalyzer('sutherland_radiology_results.csv')
    results = analyzer.analyze_missed_codes()
    analyzer.print_summary(results)
    analyzer.save_analysis_results(results, 'analysis_results.json') 