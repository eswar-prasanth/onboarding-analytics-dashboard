#!/usr/bin/env python3
"""
Main Analysis Script for Sutherland Radiology Coding Analysis

This script orchestrates the complete analysis pipeline:
1. Data analysis to identify missed codes
2. AI classification of missed codes (important vs unimportant)
3. AI review of partial match cases
4. Accuracy metrics calculation
5. Results export for dashboard

Usage:
    python main_analysis.py [--csv_file path_to_csv] [--max_workers N] [--skip_classification] [--skip_review]
"""

import argparse
import json
import time
from datetime import datetime
from typing import Dict, List
import pandas as pd
import os

# Import our modules
from data_analysis import SutherlandDataAnalyzer
from ai_integration import O3AIIntegration
from accuracy_metrics import AccuracyCalculator

class SutherlandAnalysisPipeline:
    def __init__(self, csv_file: str, max_workers: int = 3):
        """Initialize the analysis pipeline"""
        self.csv_file = csv_file
        self.max_workers = max_workers
        self.start_time = datetime.now()
        
        # Initialize components
        print("Initializing analysis components...")
        self.analyzer = SutherlandDataAnalyzer(csv_file)
        self.ai_integration = O3AIIntegration()
        self.accuracy_calculator = AccuracyCalculator(csv_file)
        
        # Results storage
        self.results = {
            'analysis_results': None,
            'classification_results': None,
            'partial_match_reviews': None,
            'no_match_reviews': None,
            'comprehensive_metrics': None
        }
        
        print(f"Pipeline initialized successfully.")
        print(f"Data loaded: {len(self.analyzer.df)} patients")
    
    def step_1_data_analysis(self) -> Dict:
        """Step 1: Analyze the data to identify missed codes"""
        print("\n" + "="*60)
        print("STEP 1: DATA ANALYSIS - Identifying Missed Codes")
        print("="*60)
        
        start_time = time.time()
        
        # Run the analysis
        analysis_results = self.analyzer.analyze_missed_codes()
        
        # Print summary
        self.analyzer.print_summary(analysis_results)
        
        # Save results
        self.analyzer.save_analysis_results(analysis_results, 'analysis_results.json')
        self.results['analysis_results'] = analysis_results
        
        elapsed = time.time() - start_time
        print(f"\n✅ Step 1 completed in {elapsed:.2f} seconds")
        
        return analysis_results
    
    def step_2_classify_codes(self, analysis_results: Dict) -> List[Dict]:
        """Step 2: Classify missed codes as important or unimportant using AI"""
        print("\n" + "="*60)
        print("STEP 2: AI CODE CLASSIFICATION - Important vs Unimportant")
        print("="*60)
        
        start_time = time.time()
        
        # Get unique missed codes
        missed_codes = list(analysis_results['code_frequency'].keys())
        print(f"Classifying {len(missed_codes)} unique missed codes...")
        
        # Classify codes
        classification_results = self.ai_integration.classify_missed_codes(missed_codes)
        
        # Print summary
        important_count = sum(1 for r in classification_results if r.get('classification') == 'important')
        unimportant_count = sum(1 for r in classification_results if r.get('classification') == 'unimportant')
        error_count = sum(1 for r in classification_results if r.get('classification') in ['error', 'parsing_error'])
        
        print(f"\nClassification Summary:")
        print(f"  Important codes: {important_count}")
        print(f"  Unimportant codes: {unimportant_count}")
        print(f"  Errors/Unknown: {error_count}")
        
        # Save results
        self.ai_integration.save_results(classification_results, 'code_classifications.json')
        self.results['classification_results'] = classification_results
        
        elapsed = time.time() - start_time
        print(f"\n✅ Step 2 completed in {elapsed:.2f} seconds")
        
        return classification_results
    
    def step_3_review_partial_matches(self, analysis_results: Dict) -> List[Dict]:
        """Step 3: Review partial match cases using AI"""
        print("\n" + "="*60)
        print("STEP 3: AI PARTIAL MATCH REVIEW - Determining Correctness")
        print("="*60)
        
        start_time = time.time()
        
        # Get partial match cases
        partial_match_cases = self.analyzer.get_partial_match_cases()
        print(f"Reviewing {len(partial_match_cases)} partial match cases...")
        
        # Review cases in parallel
        review_results = self.ai_integration.review_partial_matches_parallel(
            partial_match_cases, 
            max_workers=self.max_workers
        )
        
        # Print summary
        successful_reviews = sum(1 for r in review_results if 'error' not in r)
        error_reviews = len(review_results) - successful_reviews
        
        print(f"\nReview Summary:")
        print(f"  Successful reviews: {successful_reviews}")
        print(f"  Failed reviews: {error_reviews}")
        
        # Save results
        self.ai_integration.save_results(review_results, 'partial_match_reviews.json')
        self.results['partial_match_reviews'] = review_results
        
        elapsed = time.time() - start_time
        print(f"\n✅ Step 3 completed in {elapsed:.2f} seconds")
        
        return review_results
    
    def step_3_5_review_no_matches(self, analysis_results: Dict) -> List[Dict]:
        """Step 3.5: Review No Match cases using AI"""
        print("\n" + "="*60)
        print("STEP 3.5: AI NO MATCH REVIEW - Review Non-Matching Charts")
        print("="*60)
        
        start_time = time.time()
        
        # Get No Match cases
        no_match_cases = self.analyzer.get_no_match_cases()
        print(f"Reviewing {len(no_match_cases)} No Match cases...")
        
        # Review cases in parallel
        review_results = self.ai_integration.review_no_matches_parallel(
            no_match_cases, 
            max_workers=self.max_workers
        )
        
        # Print summary
        successful_reviews = sum(1 for r in review_results if 'error' not in r)
        error_reviews = len(review_results) - successful_reviews
        
        print(f"\nNo Match Review Summary:")
        print(f"  Successful reviews: {successful_reviews}")
        print(f"  Failed reviews: {error_reviews}")
        
        # Save results
        self.ai_integration.save_results(review_results, 'no_match_reviews.json')
        self.results['no_match_reviews'] = review_results
        
        elapsed = time.time() - start_time
        print(f"\n✅ Step 3.5 completed in {elapsed:.2f} seconds")
        
        return review_results
    
    def step_4_calculate_metrics(self, classification_results: List[Dict], 
                                 review_results: List[Dict], 
                                 no_match_reviews: List[Dict]) -> Dict:
        """Step 4: Calculate comprehensive accuracy metrics"""
        print("\n" + "="*60)
        print("STEP 4: ACCURACY METRICS CALCULATION")
        print("="*60)
        
        start_time = time.time()
        
        # Calculate comprehensive metrics including No Match reviews
        comprehensive_metrics = self.accuracy_calculator.calculate_comprehensive_metrics(
            classification_results, 
            review_results,
            no_match_reviews
        )
        
        # Save comprehensive metrics
        with open('comprehensive_metrics.json', 'w') as f:
            json.dump(comprehensive_metrics, f, indent=2, default=str)
        
        self.results['comprehensive_metrics'] = comprehensive_metrics
        
        elapsed = time.time() - start_time
        print(f"\n✅ Step 4 completed in {elapsed:.2f} seconds")
        print(f"Comprehensive metrics calculated and saved.")
        
        return comprehensive_metrics
    
    def step_5_export_results(self):
        """Step 5: Export final results for dashboard"""
        print("\n" + "="*60)
        print("STEP 5: EXPORT RESULTS")
        print("="*60)
        
        # Create summary report
        summary = {
            'pipeline_info': {
                'csv_file': self.csv_file,
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_runtime_minutes': (datetime.now() - self.start_time).total_seconds() / 60
            },
            'file_exports': {
                'analysis_results': 'analysis_results.json',
                'code_classifications': 'code_classifications.json',
                'partial_match_reviews': 'partial_match_reviews.json',
                'comprehensive_metrics': 'comprehensive_metrics.json',
                'changes_csv': 'analysis_changes.csv'
            }
        }
        
        with open('pipeline_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print("📁 Files exported:")
        for name, filename in summary['file_exports'].items():
            if os.path.exists(filename):
                size = os.path.getsize(filename) / 1024  # KB
                print(f"  ✅ {filename} ({size:.1f} KB)")
            else:
                print(f"  ❌ {filename} (not found)")
        
        print(f"\n📊 Ready for dashboard! Run: streamlit run streamlit_dashboard.py")
        
        return summary
    
    def run_complete_analysis(self, skip_classification: bool = False, 
                            skip_review: bool = False, 
                            skip_no_match_review: bool = False):
        """Run the complete analysis pipeline"""
        print(f"\n🏥 STARTING SUTHERLAND RADIOLOGY CODING ANALYSIS")
        print(f"Timestamp: {self.start_time}")
        print(f"CSV File: {self.csv_file}")
        print(f"Max Workers: {self.max_workers}")
        print("="*80)
        
        try:
            # Step 1: Data Analysis
            analysis_results = self.step_1_data_analysis()
            
            # Step 2: Code Classification (optional)
            if skip_classification:
                print("\n⏭️  Skipping code classification (loading existing results)")
                if os.path.exists('code_classifications.json'):
                    with open('code_classifications.json', 'r') as f:
                        classification_results = json.load(f)
                    self.results['classification_results'] = classification_results
                else:
                    print("⚠️  No existing classification results found, creating empty list")
                    classification_results = []
            else:
                classification_results = self.step_2_classify_codes(analysis_results)
            
            # Step 3: Partial Match Review (optional)
            if skip_review:
                print("\n⏭️  Skipping partial match review (loading existing results)")
                if os.path.exists('partial_match_reviews.json'):
                    with open('partial_match_reviews.json', 'r') as f:
                        review_results = json.load(f)
                    self.results['partial_match_reviews'] = review_results
                else:
                    print("⚠️  No existing partial match review results found, creating empty list")
                    review_results = []
            else:
                review_results = self.step_3_review_partial_matches(analysis_results)
            
            # Step 3.5: No Match Review (optional)
            if skip_no_match_review:
                print("\n⏭️  Skipping No Match review (loading existing results)")
                if os.path.exists('no_match_reviews.json'):
                    with open('no_match_reviews.json', 'r') as f:
                        no_match_reviews = json.load(f)
                    self.results['no_match_reviews'] = no_match_reviews
                else:
                    print("⚠️  No existing No Match review results found, creating empty list")
                    no_match_reviews = []
            else:
                no_match_reviews = self.step_3_5_review_no_matches(analysis_results)
            
            # Step 4: Calculate Metrics
            comprehensive_metrics = self.step_4_calculate_metrics(
                classification_results, 
                review_results,
                no_match_reviews
            )
            
            # Step 5: Export Results
            self.step_5_export_results()
            
            # Final Summary
            total_time = (datetime.now() - self.start_time).total_seconds()
            print(f"\n🎉 ANALYSIS COMPLETED SUCCESSFULLY!")
            print(f"Total execution time: {total_time:.2f} seconds")
            print(f"Results saved to comprehensive_metrics.json")
            
            # Print key findings
            original_accuracy = comprehensive_metrics['original_accuracy']['chart_level']['complete_match_rate']
            post_accuracy = comprehensive_metrics['post_ai_review']['complete_match_rate']
            improvement = post_accuracy - original_accuracy
            
            print(f"\n📊 KEY FINDINGS:")
            print(f"Original complete match rate: {original_accuracy:.1%}")
            print(f"Post-review complete match rate: {post_accuracy:.1%}")
            print(f"Improvement: {improvement:+.1%}")
            
        except Exception as e:
            print(f"\n❌ ANALYSIS FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description='Sutherland Radiology Coding Analysis Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_analysis.py                                    # Run full analysis
  python main_analysis.py --csv_file custom_data.csv        # Use custom CSV file
  python main_analysis.py --max_workers 5                   # Use 5 parallel workers
  python main_analysis.py --skip_classification              # Skip AI classification step
  python main_analysis.py --skip_review                     # Skip partial match review
  python main_analysis.py --skip_no_match_review             # Skip No Match review
  python main_analysis.py --skip_classification --skip_review --skip_no_match_review  # Only calculate metrics
        """
    )
    
    parser.add_argument(
        '--csv_file', 
        type=str, 
        default='sutherland_radiology_results.csv',
        help='Path to the CSV file containing coding results (default: sutherland_radiology_results.csv)'
    )
    
    parser.add_argument(
        '--max_workers',
        type=int,
        default=3,
        help='Maximum number of parallel workers for AI calls (default: 3)'
    )
    
    parser.add_argument(
        '--skip_classification',
        action='store_true',
        help='Skip AI classification of missed codes (loads existing results if available)'
    )
    
    parser.add_argument(
        '--skip_review',
        action='store_true',
        help='Skip AI review of partial match cases (loads existing results if available)'
    )
    
    parser.add_argument(
        '--skip_no_match_review',
        action='store_true',
        help='Skip AI review of No Match cases (loads existing results if available)'
    )
    
    args = parser.parse_args()
    
    # Validate CSV file exists
    if not os.path.exists(args.csv_file):
        print(f"❌ Error: CSV file '{args.csv_file}' not found")
        return
    
    # Initialize and run pipeline
    pipeline = SutherlandAnalysisPipeline(
        csv_file=args.csv_file,
        max_workers=args.max_workers
    )
    
    pipeline.run_complete_analysis(
        skip_classification=args.skip_classification,
        skip_review=args.skip_review,
        skip_no_match_review=args.skip_no_match_review
    )

if __name__ == "__main__":
    main() 