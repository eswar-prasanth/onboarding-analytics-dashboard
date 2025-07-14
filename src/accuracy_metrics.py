import pandas as pd
import numpy as np
from typing import Dict, List, Set, Tuple
import json
from dataclasses import dataclass

@dataclass
class AccuracyMetrics:
    """Data class to hold accuracy metrics"""
    total_patients: int
    complete_matches: int
    partial_matches: int
    no_matches: int
    complete_match_rate: float
    partial_match_rate: float
    no_match_rate: float
    
    # Code-level metrics
    total_sutherland_codes: int
    total_ai_codes: int
    total_missed_codes: int
    total_extra_codes: int
    code_level_accuracy: float
    
    # Important vs Unimportant code metrics
    important_missed_codes: int
    unimportant_missed_codes: int
    important_code_accuracy: float
    unimportant_code_accuracy: float

class AccuracyCalculator:
    def __init__(self, original_data_file: str):
        """Initialize with original CSV data"""
        self.original_df = pd.read_csv(original_data_file)
        self.original_df['SMC Coded'] = self.original_df['SMC Coded'].fillna('')
        self.original_df['Rapidclaims Codes'] = self.original_df['Rapidclaims Codes'].fillna('')
        
    def parse_codes(self, code_string: str) -> Set[str]:
        """Parse comma-separated codes and return as set"""
        if pd.isna(code_string) or code_string == '':
            return set()
        codes = [code.strip() for code in str(code_string).split(',')]
        return set(code for code in codes if code)
    
    def calculate_original_accuracy(self) -> AccuracyMetrics:
        """Calculate accuracy metrics for original data before AI review"""
        total_patients = len(self.original_df)
        
        # Chart-level matches
        complete_matches = len(self.original_df[self.original_df['Match Result'] == 'Complete Match'])
        partial_matches = len(self.original_df[self.original_df['Match Result'] == 'Partial Match'])
        no_matches = len(self.original_df[self.original_df['Match Result'] == 'No Match'])
        
        # Code-level analysis
        total_sutherland_codes = 0
        total_ai_codes = 0
        total_missed_codes = 0
        total_extra_codes = 0
        
        for _, row in self.original_df.iterrows():
            sutherland_codes = self.parse_codes(row['SMC Coded'])
            ai_codes = self.parse_codes(row['Rapidclaims Codes'])
            
            total_sutherland_codes += len(sutherland_codes)
            total_ai_codes += len(ai_codes)
            total_missed_codes += len(sutherland_codes - ai_codes)
            total_extra_codes += len(ai_codes - sutherland_codes)
        
        return AccuracyMetrics(
            total_patients=total_patients,
            complete_matches=complete_matches,
            partial_matches=partial_matches,
            no_matches=no_matches,
            complete_match_rate=complete_matches / total_patients,
            partial_match_rate=partial_matches / total_patients,
            no_match_rate=no_matches / total_patients,
            total_sutherland_codes=total_sutherland_codes,
            total_ai_codes=total_ai_codes,
            total_missed_codes=total_missed_codes,
            total_extra_codes=total_extra_codes,
            code_level_accuracy=(total_ai_codes - total_missed_codes) / total_ai_codes if total_sutherland_codes > 0 else 0,
            important_missed_codes=0,  # Will be calculated separately
            unimportant_missed_codes=0,
            important_code_accuracy=0,
            unimportant_code_accuracy=0
        )
    
    def calculate_code_importance_metrics(self, classification_results: List[Dict]) -> Tuple[int, int]:
        """Calculate metrics for important vs unimportant missed codes"""
        important_missed = 0
        unimportant_missed = 0
        
        for result in classification_results:
            if result.get('classification') == 'important':
                important_missed += 1
            elif result.get('classification') == 'unimportant':
                unimportant_missed += 1
        
        return important_missed, unimportant_missed
    
    def calculate_post_ai_review_accuracy(self, partial_match_reviews: List[Dict]) -> Dict:
        """Calculate accuracy metrics after AI review of partial matches"""
        # Create a copy of original data to modify
        reviewed_df = self.original_df.copy()
        
        changes_made = []
        partial_to_complete = 0
        
        # Detailed metrics for manual coding accuracy
        sutherland_errors = 0
        total_reviewed_codes = 0
        ai_corrections = 0
        extra_codes_by_ai = 0
        corrected_codes = {}
        
        for review in partial_match_reviews:
            # Try to handle cases where there's an error but raw_response has valid data
            if 'error' in review:
                raw_response = review.get('raw_response', '')
                if raw_response:
                    try:
                        # Try to parse the raw_response as JSON
                        import json
                        import re
                        # Clean invalid control characters
                        cleaned_response = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', raw_response)
                        parsed_response = json.loads(cleaned_response)
                        if 'analysis' in parsed_response:
                            # Use the parsed response instead
                            review = parsed_response
                        else:
                            continue
                    except Exception as e:
                        continue
                else:
                    continue
                
            patient_id = review.get('patient_id')
            if not patient_id:
                continue
            
            # Convert patient_id to string if it's an integer
            patient_id = str(patient_id)
                
            # Find the patient in the dataframe (convert both to string for comparison)
            patient_idx = reviewed_df[reviewed_df['Patient ID'].astype(str) == str(patient_id)].index
            if len(patient_idx) == 0:
                continue
                
            patient_idx = patient_idx[0]
            
            # Analyze the review results
            analysis = review.get('analysis', [])
            sutherland_score = review.get('coding_accuracy_score', {}).get('sutherland_score', 0.5)
            ai_score = review.get('coding_accuracy_score', {}).get('ai_score', 0.5)
            
            # Analyze each code discrepancy
            patient_sutherland_errors = 0
            patient_total_codes = 0
            patient_ai_corrections = 0
            patient_extra_codes = 0
            
            for code_analysis in analysis:
                total_reviewed_codes += 1
                patient_total_codes += 1
                
                sutherland_code = code_analysis.get('sutherland_code')
                ai_code = code_analysis.get('ai_code')
                is_sutherland_correct = code_analysis.get('is_sutherland_correct', False)
                is_ai_correct = code_analysis.get('is_ai_correct', False)
                status = code_analysis.get('status', '')
                

                
                # Track different types of discrepancies
                if sutherland_code and not ai_code:
                    # Sutherland coded something AI didn't
                    if not is_sutherland_correct:
                        sutherland_errors += 1
                        patient_sutherland_errors += 1
                        corrected_codes[sutherland_code] = 'should_not_code'
                        
                elif ai_code and not sutherland_code:
                    # AI coded something Sutherland didn't (extra code)
                    extra_codes_by_ai += 1
                    patient_extra_codes += 1
                    if is_ai_correct:
                        ai_corrections += 1
                        patient_ai_corrections += 1
                        corrected_codes[ai_code] = 'should_code'
                        
                elif sutherland_code and ai_code and sutherland_code != ai_code:
                    # Different codes used (substitution)
                    if not is_sutherland_correct and is_ai_correct:
                        sutherland_errors += 1
                        patient_sutherland_errors += 1
                        ai_corrections += 1
                        patient_ai_corrections += 1
                        corrected_codes[sutherland_code] = ai_code
                        

            
            # Determine if this should become a complete match
            # More nuanced logic based on actual code analysis
            should_be_complete = False
            reason = ""
            
            if ai_score > 0.8 and ai_score > sutherland_score:
                # AI is significantly more accurate
                should_be_complete = True
                reason = f'AI coding more accurate (AI: {ai_score:.2f}, Sutherland: {sutherland_score:.2f})'
                
            elif patient_ai_corrections > patient_sutherland_errors:
                # AI made more corrections than Sutherland errors
                should_be_complete = True
                reason = f'AI corrections ({patient_ai_corrections}) > Sutherland errors ({patient_sutherland_errors})'
                
            elif patient_total_codes > 0 and (patient_sutherland_errors / patient_total_codes) < 0.2:
                # Low error rate, could be considered complete
                should_be_complete = True
                reason = f'Low Sutherland error rate: {patient_sutherland_errors}/{patient_total_codes}'
            
            if should_be_complete:
                changes_made.append({
                    'patient_id': str(patient_id),
                    'original_match': 'Partial Match',
                    'new_match': 'Complete Match (Post-Review)',
                    'reason': reason,
                    'sutherland_errors': patient_sutherland_errors,
                    'ai_corrections': patient_ai_corrections,
                    'extra_codes': patient_extra_codes,
                    'sutherland_score': sutherland_score,
                    'ai_score': ai_score
                })
                reviewed_df.loc[patient_idx, 'Match Result'] = 'Complete Match'
                partial_to_complete += 1
        
        # Calculate new metrics
        new_complete_matches = len(reviewed_df[reviewed_df['Match Result'] == 'Complete Match'])
        new_partial_matches = len(reviewed_df[reviewed_df['Match Result'] == 'Partial Match'])
        new_no_matches = len(reviewed_df[reviewed_df['Match Result'] == 'No Match'])
        
        total_patients = len(reviewed_df)
        
        # Calculate manual coding accuracy
        manual_coding_accuracy = (total_reviewed_codes - sutherland_errors) / total_reviewed_codes if total_reviewed_codes > 0 else 1.0
        
        return {
            'post_review_metrics': {
                'complete_matches': new_complete_matches,
                'partial_matches': new_partial_matches,
                'no_matches': new_no_matches,
                'complete_match_rate': new_complete_matches / total_patients,
                'partial_match_rate': new_partial_matches / total_patients,
                'no_match_rate': new_no_matches / total_patients
            },
            'improvements': {
                'partial_to_complete_conversions': partial_to_complete,
                'accuracy_improvement': (new_complete_matches - self.calculate_original_accuracy().complete_matches) / total_patients
            },
            'manual_coding_analysis': {
                'total_reviewed_codes': total_reviewed_codes,
                'sutherland_errors': sutherland_errors,
                'manual_coding_accuracy': manual_coding_accuracy,
                'ai_corrections': ai_corrections,
                'extra_codes_by_ai': extra_codes_by_ai,
                'corrected_codes': corrected_codes
            },
            'changes_made': changes_made,
            'reviewed_dataframe': reviewed_df
        }
    
    def calculate_corrected_code_accuracy(self, partial_match_reviews: List[Dict]) -> Dict:
        """Calculate code-level accuracy considering AI corrections"""
        corrected_metrics = {
            'total_codes_reviewed': 0,
            'ai_correct_codes': 0,
            'sutherland_correct_codes': 0,
            'corrected_accuracy': 0.0,
            'improvement_over_original': 0.0
        }
        
        for review in partial_match_reviews:
            if 'error' in review:
                continue
                
            analysis = review.get('analysis', [])
            
            for code_analysis in analysis:
                corrected_metrics['total_codes_reviewed'] += 1
                
                is_sutherland_correct = code_analysis.get('is_sutherland_correct', False)
                is_ai_correct = code_analysis.get('is_ai_correct', False)
                
                # In cases where AI is correct, count it as correct
                if is_ai_correct:
                    corrected_metrics['ai_correct_codes'] += 1
                elif is_sutherland_correct:
                    corrected_metrics['sutherland_correct_codes'] += 1
        
        total_reviewed = corrected_metrics['total_codes_reviewed']
        if total_reviewed > 0:
            total_correct = corrected_metrics['ai_correct_codes'] + corrected_metrics['sutherland_correct_codes']
            corrected_metrics['corrected_accuracy'] = total_correct / total_reviewed
        
        return corrected_metrics
    
    def calculate_comprehensive_metrics(self, 
                                      classification_results: List[Dict],
                                      partial_match_reviews: List[Dict],
                                      no_match_reviews: List[Dict] = None) -> Dict:
        """Calculate comprehensive accuracy metrics"""
        
        # Original accuracy
        original_metrics = self.calculate_original_accuracy()
        
        # Code importance metrics
        important_missed, unimportant_missed = self.calculate_code_importance_metrics(classification_results)
        
        # Post-AI review metrics
        post_review = self.calculate_post_ai_review_accuracy(partial_match_reviews)
        
        # Calculate corrected code accuracy
        corrected_code_metrics = self.calculate_corrected_code_accuracy(partial_match_reviews)
        
        # Calculate detailed pre/post review code accuracy
        pre_review_code_accuracy = self.calculate_pre_review_code_accuracy()
        post_review_code_accuracy = self.calculate_post_review_code_accuracy(partial_match_reviews)
        
        # Calculate unified post-review accuracy including no match conversions
        unified_post_review = self.calculate_unified_post_review_accuracy(partial_match_reviews, no_match_reviews)
        
        # Process No Match reviews if provided
        no_match_analysis = {}
        if no_match_reviews:
            no_match_analysis = self.analyze_no_match_reviews(no_match_reviews)

        # Calculate code-level accuracy with importance weighting
        total_important_codes = self._count_important_codes_in_dataset(classification_results)
        total_unimportant_codes = original_metrics.total_sutherland_codes - total_important_codes
        
        important_code_accuracy = (total_important_codes - important_missed) / total_important_codes if total_important_codes > 0 else 1.0
        unimportant_code_accuracy = (total_unimportant_codes - unimportant_missed) / total_unimportant_codes if total_unimportant_codes > 0 else 1.0
        
        # Comprehensive metrics
        comprehensive_metrics = {
            'original_accuracy': {
                'chart_level': {
                    'complete_match_rate': original_metrics.complete_match_rate,
                    'partial_match_rate': original_metrics.partial_match_rate,
                    'no_match_rate': original_metrics.no_match_rate,
                    'complete_matches': original_metrics.complete_matches,
                    'partial_matches': original_metrics.partial_matches,
                    'no_matches': original_metrics.no_matches,
                    'total_patients': original_metrics.total_patients
                },
                'code_level': {
                    'overall_accuracy': original_metrics.code_level_accuracy,
                    'total_sutherland_codes': original_metrics.total_sutherland_codes,
                    'total_missed_codes': original_metrics.total_missed_codes,
                    'total_extra_codes': original_metrics.total_extra_codes,
                    'miss_rate': original_metrics.total_missed_codes / original_metrics.total_sutherland_codes if original_metrics.total_sutherland_codes > 0 else 0
                }
            },
            'code_importance_analysis': {
                'important_codes': {
                    'total_important_codes': total_important_codes,
                    'missed_important_codes': important_missed,
                    'important_code_accuracy': important_code_accuracy,
                    'important_miss_rate': important_missed / total_important_codes if total_important_codes > 0 else 0
                },
                'unimportant_codes': {
                    'total_unimportant_codes': total_unimportant_codes,
                    'missed_unimportant_codes': unimportant_missed,
                    'unimportant_code_accuracy': unimportant_code_accuracy,
                    'unimportant_miss_rate': unimportant_missed / total_unimportant_codes if total_unimportant_codes > 0 else 0
                }
            },
            'post_ai_review': post_review['post_review_metrics'],
            'improvements': post_review['improvements'],
            'manual_coding_analysis': post_review['manual_coding_analysis'],
            'corrected_code_accuracy': corrected_code_metrics,
            'detailed_changes': post_review['changes_made'],
            'pre_review_code_accuracy': pre_review_code_accuracy,
            'post_review_code_accuracy': post_review_code_accuracy,
            'unified_post_review_accuracy': unified_post_review,
            'no_match_analysis': no_match_analysis
        }
        
        return comprehensive_metrics
    
    def analyze_no_match_reviews(self, no_match_reviews: List[Dict]) -> Dict:
        """Analyze No Match review results"""
        total_no_match_cases = len(no_match_reviews)
        successful_reviews = sum(1 for r in no_match_reviews if 'error' not in r)
        
        # Analysis counters
        potential_upgrades = 0
        ai_better_cases = 0
        sutherland_better_cases = 0
        
        upgrade_potential = {
            'to_partial_match': 0,
            'to_complete_match': 0
        }
        
        for review in no_match_reviews:
            if 'error' in review:
                continue
                
            # Check for potential upgrades
            match_potential = review.get('match_potential', {})
            if match_potential.get('could_be_partial_match', False):
                upgrade_potential['to_partial_match'] += 1
                potential_upgrades += 1
            if match_potential.get('could_be_complete_match', False):
                upgrade_potential['to_complete_match'] += 1
                potential_upgrades += 1
            
            # Compare coding accuracy
            scores = review.get('coding_accuracy_score', {})
            sutherland_score = scores.get('sutherland_score', 0.5)
            ai_score = scores.get('ai_score', 0.5)
            
            if ai_score > sutherland_score:
                ai_better_cases += 1
            elif sutherland_score > ai_score:
                sutherland_better_cases += 1
        
        return {
            'total_no_match_cases': total_no_match_cases,
            'successful_reviews': successful_reviews,
            'potential_upgrades': potential_upgrades,
            'upgrade_potential': upgrade_potential,
            'ai_better_cases': ai_better_cases,
            'sutherland_better_cases': sutherland_better_cases,
            'review_success_rate': successful_reviews / total_no_match_cases if total_no_match_cases > 0 else 0
        }

    def _count_important_codes_in_dataset(self, classification_results: List[Dict]) -> int:
        """Count total important codes in the dataset based on classification"""
        # This would need to match all Sutherland codes against the classification results
        # For now, return a reasonable estimate
        important_classifications = [r for r in classification_results if r.get('classification') == 'important']
        return len(important_classifications)
    
    def generate_accuracy_report(self, metrics: Dict) -> str:
        """Generate a comprehensive accuracy report"""
        report = []
        
        # Header
        report.append("="*80)
        report.append("SUTHERLAND RADIOLOGY CODING ACCURACY ANALYSIS REPORT")
        report.append("="*80)
        
        # Original Accuracy
        orig = metrics['original_accuracy']
        report.append("\n1. ORIGINAL ACCURACY (Before AI Review)")
        report.append("-" * 50)
        report.append(f"Chart-Level Accuracy:")
        report.append(f"  Complete Matches: {orig['chart_level']['complete_matches']:,} ({orig['chart_level']['complete_match_rate']:.1%})")
        report.append(f"  Partial Matches:  {orig['chart_level']['partial_matches']:,} ({orig['chart_level']['partial_match_rate']:.1%})")
        report.append(f"  No Matches:       {orig['chart_level']['no_matches']:,} ({orig['chart_level']['no_match_rate']:.1%})")
        report.append(f"  Total Patients:   {orig['chart_level']['total_patients']:,}")
        
        report.append(f"\nCode-Level Accuracy:")
        report.append(f"  Overall Accuracy: {orig['code_level']['overall_accuracy']:.1%}")
        report.append(f"  Total Codes:      {orig['code_level']['total_sutherland_codes']:,}")
        report.append(f"  Missed Codes:     {orig['code_level']['total_missed_codes']:,}")
        report.append(f"  Miss Rate:        {orig['code_level']['miss_rate']:.1%}")
        
        # Code Importance Analysis
        importance = metrics['code_importance_analysis']
        report.append("\n2. CODE IMPORTANCE ANALYSIS")
        report.append("-" * 50)
        report.append(f"Important Codes:")
        report.append(f"  Total Important:  {importance['important_codes']['total_important_codes']:,}")
        report.append(f"  Missed Important: {importance['important_codes']['missed_important_codes']:,}")
        report.append(f"  Important Accuracy: {importance['important_codes']['important_code_accuracy']:.1%}")
        
        report.append(f"\nUnimportant Codes:")
        report.append(f"  Total Unimportant:  {importance['unimportant_codes']['total_unimportant_codes']:,}")
        report.append(f"  Missed Unimportant: {importance['unimportant_codes']['missed_unimportant_codes']:,}")
        report.append(f"  Unimportant Accuracy: {importance['unimportant_codes']['unimportant_code_accuracy']:.1%}")
        
        # Post AI Review
        post = metrics['post_ai_review']
        improvements = metrics['improvements']
        manual_analysis = metrics.get('manual_coding_analysis', {})
        corrected_accuracy = metrics.get('corrected_code_accuracy', {})
        
        report.append("\n3. POST AI REVIEW ACCURACY")
        report.append("-" * 50)
        report.append(f"Revised Chart-Level Accuracy:")
        report.append(f"  Complete Matches: {post['complete_matches']:,} ({post['complete_match_rate']:.1%})")
        report.append(f"  Partial Matches:  {post['partial_matches']:,} ({post['partial_match_rate']:.1%})")
        report.append(f"  No Matches:       {post['no_matches']:,} ({post['no_match_rate']:.1%})")
        
        report.append(f"\nImprovements:")
        report.append(f"  Partial → Complete: {improvements['partial_to_complete_conversions']:,}")
        report.append(f"  Accuracy Improvement: {improvements['accuracy_improvement']:.1%}")
        
        report.append("\n4. MANUAL CODING ACCURACY ANALYSIS")
        report.append("-" * 50)
        if manual_analysis:
            report.append(f"Manual Coding Performance:")
            report.append(f"  Total Reviewed Codes: {manual_analysis.get('total_reviewed_codes', 0):,}")
            report.append(f"  Sutherland Errors: {manual_analysis.get('sutherland_errors', 0):,}")
            report.append(f"  Manual Coding Accuracy: {manual_analysis.get('manual_coding_accuracy', 0):.1%}")
            report.append(f"  AI Corrections Made: {manual_analysis.get('ai_corrections', 0):,}")
            report.append(f"  Extra Codes by AI: {manual_analysis.get('extra_codes_by_ai', 0):,}")
        
        report.append("\n5. CORRECTED CODE-LEVEL ACCURACY")
        report.append("-" * 50)
        if corrected_accuracy:
            report.append(f"Post-Review Code Accuracy:")
            report.append(f"  Total Codes Reviewed: {corrected_accuracy.get('total_codes_reviewed', 0):,}")
            report.append(f"  AI Correct Codes: {corrected_accuracy.get('ai_correct_codes', 0):,}")
            report.append(f"  Sutherland Correct Codes: {corrected_accuracy.get('sutherland_correct_codes', 0):,}")
            report.append(f"  Corrected Accuracy: {corrected_accuracy.get('corrected_accuracy', 0):.1%}")
        
        # Summary
        original_complete_rate = orig['chart_level']['complete_match_rate']
        new_complete_rate = post['complete_match_rate']
        improvement = new_complete_rate - original_complete_rate
        
        report.append("\n6. SUMMARY")
        report.append("-" * 50)
        report.append(f"Overall Chart Accuracy Improvement: {improvement:.1%}")
        report.append(f"From {original_complete_rate:.1%} to {new_complete_rate:.1%}")
        
        # Add manual coding accuracy insights
        if manual_analysis:
            manual_acc = manual_analysis.get('manual_coding_accuracy', 1.0)
            if manual_acc < 0.9:
                report.append(f"\n⚠️  Manual coding accuracy is {manual_acc:.1%} - significant room for improvement")
            else:
                report.append(f"\n✅ Manual coding accuracy is good at {manual_acc:.1%}")
        
        if importance['important_codes']['important_code_accuracy'] < importance['unimportant_codes']['unimportant_code_accuracy']:
            report.append(f"\n⚠️  AI has higher miss rate for IMPORTANT codes ({importance['important_codes']['important_miss_rate']:.1%}) vs unimportant codes ({importance['unimportant_codes']['unimportant_miss_rate']:.1%})")
        else:
            report.append(f"\n✅ AI performs better on important codes than unimportant codes")
        
        return "\n".join(report)
    
    def save_comprehensive_analysis(self, metrics: Dict, filename: str):
        """Save comprehensive analysis to JSON file"""
        with open(filename, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        print(f"Comprehensive analysis saved to {filename}")
    
    def create_changes_dataframe(self, changes: List[Dict]) -> pd.DataFrame:
        """Create a DataFrame of all changes made during review"""
        if not changes:
            return pd.DataFrame()
        
        return pd.DataFrame(changes)

    def calculate_pre_review_code_accuracy(self) -> Dict:
        """Calculate detailed code-level accuracy metrics before AI review"""
        total_sutherland_codes = 0
        total_ai_codes = 0
        correctly_coded_by_ai = 0
        missed_by_ai = 0
        extra_by_ai = 0
        patient_level_data = []
        
        for _, row in self.original_df.iterrows():
            sutherland_codes = self.parse_codes(row['SMC Coded'])
            ai_codes = self.parse_codes(row['Rapidclaims Codes'])
            
            missed_codes = sutherland_codes - ai_codes
            extra_codes = ai_codes - sutherland_codes
            correct_codes = sutherland_codes & ai_codes
            
            total_sutherland_codes += len(sutherland_codes)
            total_ai_codes += len(ai_codes)
            correctly_coded_by_ai += len(correct_codes)
            missed_by_ai += len(missed_codes)
            extra_by_ai += len(extra_codes)
            
            patient_level_data.append({
                'patient_id': str(row['Patient ID']),
                'sutherland_codes': len(sutherland_codes),
                'ai_codes': len(ai_codes),
                'correct_codes': len(correct_codes),
                'missed_codes': len(missed_codes),
                'extra_codes': len(extra_codes),
                'accuracy_rate': len(correct_codes) / len(sutherland_codes) if len(sutherland_codes) > 0 else 1.0
            })
        
        # Calculate overall metrics
        overall_accuracy = correctly_coded_by_ai / total_sutherland_codes if total_sutherland_codes > 0 else 0
        miss_rate = missed_by_ai / total_sutherland_codes if total_sutherland_codes > 0 else 0
        extra_rate = extra_by_ai / total_ai_codes if total_ai_codes > 0 else 0
        
        return {
            'pre_review_metrics': {
                'total_sutherland_codes': total_sutherland_codes,
                'total_ai_codes': total_ai_codes,
                'correctly_coded_by_ai': correctly_coded_by_ai,
                'missed_by_ai': missed_by_ai,
                'extra_by_ai': extra_by_ai,
                'overall_accuracy': overall_accuracy,
                'miss_rate': miss_rate,
                'extra_rate': extra_rate,
                'precision': correctly_coded_by_ai / total_ai_codes if total_ai_codes > 0 else 0,
                'recall': correctly_coded_by_ai / total_sutherland_codes if total_sutherland_codes > 0 else 0
            },
            'patient_level_data': patient_level_data
        }
    
    def calculate_unified_post_review_accuracy(self, partial_match_reviews: List[Dict], no_match_reviews: List[Dict] = None) -> Dict:
        """Calculate unified post-review accuracy including both partial match improvements and no match conversions"""
        
        # Get baseline metrics
        original_metrics = self.calculate_original_accuracy()
        pre_review_code = self.calculate_pre_review_code_accuracy()
        
        # Calculate partial match improvements
        partial_match_improvements = self.calculate_post_review_code_accuracy(partial_match_reviews)
        
        # Initialize no match conversion metrics
        no_match_conversions = {
            'cases_reviewed': 0,
            'potential_complete_matches': 0,
            'potential_partial_matches': 0,
            'total_potential_upgrades': 0,
            'chart_level_improvement': 0,
            'complete_match_rate_improvement': 0,
            'partial_match_rate_improvement': 0
        }
        
        # Calculate no match conversion improvements if data available
        if no_match_reviews:
            for review in no_match_reviews:
                if 'error' in review:
                    continue
                    
                no_match_conversions['cases_reviewed'] += 1
                
                match_potential = review.get('match_potential', {})
                if match_potential.get('could_be_complete_match', False):
                    no_match_conversions['potential_complete_matches'] += 1
                    no_match_conversions['total_potential_upgrades'] += 1
                elif match_potential.get('could_be_partial_match', False):
                    no_match_conversions['potential_partial_matches'] += 1
                    no_match_conversions['total_potential_upgrades'] += 1
            
            # Calculate potential chart-level improvements
            total_patients = original_metrics.total_patients
            if total_patients > 0:
                no_match_conversions['complete_match_rate_improvement'] = no_match_conversions['potential_complete_matches'] / total_patients
                no_match_conversions['partial_match_rate_improvement'] = no_match_conversions['potential_partial_matches'] / total_patients
                no_match_conversions['chart_level_improvement'] = no_match_conversions['total_potential_upgrades'] / total_patients
        
        # Calculate unified post-review metrics
        # Chart level improvements
        original_complete_rate = original_metrics.complete_match_rate
        original_partial_rate = original_metrics.partial_match_rate
        original_no_match_rate = original_metrics.no_match_rate
        
        # After all improvements
        unified_complete_rate = original_complete_rate + no_match_conversions['complete_match_rate_improvement']
        unified_partial_rate = original_partial_rate + no_match_conversions['partial_match_rate_improvement']
        unified_no_match_rate = original_no_match_rate - no_match_conversions['chart_level_improvement']
        
        # Code level improvements (from partial match reviews)
        code_level_improvement = partial_match_improvements['comparison_metrics']['net_improvement']
        unified_code_accuracy = pre_review_code['pre_review_metrics']['overall_accuracy'] + code_level_improvement
        
        # Total improvement calculation
        total_chart_improvement = no_match_conversions['chart_level_improvement']
        total_code_improvement = code_level_improvement
        
        # Improvement breakdown
        improvement_breakdown = {
            'partial_match_improvements': {
                'source': 'AI Review of Partial Matches',
                'code_level_improvement': code_level_improvement,
                'codes_corrected': partial_match_improvements['post_review_metrics']['ai_corrections_accepted'],
                'codes_reviewed': partial_match_improvements['post_review_metrics']['codes_reviewed_by_ai'],
                'ai_accuracy_on_reviews': partial_match_improvements['post_review_metrics']['ai_decision_accuracy']
            },
            'no_match_conversions': {
                'source': 'No Match to Match Conversions',
                'chart_level_improvement': total_chart_improvement,
                'cases_reviewed': no_match_conversions['cases_reviewed'],
                'potential_complete_conversions': no_match_conversions['potential_complete_matches'],
                'potential_partial_conversions': no_match_conversions['potential_partial_matches'],
                'total_conversions': no_match_conversions['total_potential_upgrades']
            }
        }
        
        # Unified metrics summary
        unified_metrics = {
            'original_accuracy': {
                'complete_match_rate': original_complete_rate,
                'partial_match_rate': original_partial_rate,
                'no_match_rate': original_no_match_rate,
                'code_level_accuracy': pre_review_code['pre_review_metrics']['overall_accuracy']
            },
            'unified_post_review_accuracy': {
                'complete_match_rate': unified_complete_rate,
                'partial_match_rate': unified_partial_rate,
                'no_match_rate': unified_no_match_rate,
                'code_level_accuracy': unified_code_accuracy
            },
            'total_improvements': {
                'chart_level_improvement': total_chart_improvement,
                'code_level_improvement': total_code_improvement,
                'complete_match_improvement': no_match_conversions['complete_match_rate_improvement'],
                'partial_match_improvement': no_match_conversions['partial_match_rate_improvement'],
                'combined_accuracy_improvement': total_chart_improvement + total_code_improvement
            },
            'improvement_breakdown': improvement_breakdown,
            'detailed_metrics': {
                'partial_match_details': partial_match_improvements,
                'no_match_details': no_match_conversions
            }
        }
        
        return unified_metrics

    def calculate_post_review_code_accuracy(self, partial_match_reviews: List[Dict]) -> Dict:
        """Calculate detailed code-level accuracy metrics after AI review with corrections"""
        # Start with pre-review metrics
        pre_review = self.calculate_pre_review_code_accuracy()
        
        # Initialize post-review metrics with pre-review values
        post_review_metrics = pre_review['pre_review_metrics'].copy()
        
        # Track corrections and improvements
        ai_correct_decisions = 0
        sutherland_errors_found = 0
        codes_reviewed = 0
        ai_corrections_accepted = 0
        patient_corrections = []
        
        for review in partial_match_reviews:
            # Handle error cases with raw_response
            if 'error' in review:
                raw_response = review.get('raw_response', '')
                if raw_response:
                    try:
                        import json
                        import re
                        cleaned_response = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', raw_response)
                        parsed_response = json.loads(cleaned_response)
                        if 'analysis' in parsed_response:
                            review = parsed_response
                        else:
                            continue
                    except Exception:
                        continue
                else:
                    continue
            
            patient_id = str(review.get('patient_id', ''))
            analysis = review.get('analysis', [])
            
            patient_ai_correct = 0
            patient_sutherland_errors = 0
            patient_codes_reviewed = 0
            
            for code_analysis in analysis:
                codes_reviewed += 1
                patient_codes_reviewed += 1
                
                is_sutherland_correct = code_analysis.get('is_sutherland_correct', False)
                is_ai_correct = code_analysis.get('is_ai_correct', False)
                
                if is_ai_correct:
                    ai_correct_decisions += 1
                    patient_ai_correct += 1
                    
                if not is_sutherland_correct:
                    sutherland_errors_found += 1
                    patient_sutherland_errors += 1
                    
                # If AI is correct and Sutherland is not, it's a correction
                if is_ai_correct and not is_sutherland_correct:
                    ai_corrections_accepted += 1
            
            if patient_codes_reviewed > 0:
                patient_corrections.append({
                    'patient_id': patient_id,
                    'codes_reviewed': patient_codes_reviewed,
                    'ai_correct': patient_ai_correct,
                    'sutherland_errors': patient_sutherland_errors,
                    'improvement_rate': patient_ai_correct / patient_codes_reviewed
                })
        
        # Calculate corrected accuracy
        corrected_accuracy = 0
        if codes_reviewed > 0:
            # Original accuracy on reviewed codes + AI corrections
            baseline_correct = codes_reviewed - sutherland_errors_found
            total_correct_after_review = baseline_correct + ai_corrections_accepted
            corrected_accuracy = total_correct_after_review / codes_reviewed
        
        # Calculate improvement metrics
        improvement_in_accuracy = ai_corrections_accepted / post_review_metrics['total_sutherland_codes'] if post_review_metrics['total_sutherland_codes'] > 0 else 0
        error_reduction_rate = sutherland_errors_found / codes_reviewed if codes_reviewed > 0 else 0
        
        return {
            'post_review_metrics': {
                'codes_reviewed_by_ai': codes_reviewed,
                'ai_correct_decisions': ai_correct_decisions,
                'sutherland_errors_found': sutherland_errors_found,
                'ai_corrections_accepted': ai_corrections_accepted,
                'corrected_accuracy': corrected_accuracy,
                'improvement_in_accuracy': improvement_in_accuracy,
                'error_reduction_rate': error_reduction_rate,
                'ai_decision_accuracy': ai_correct_decisions / codes_reviewed if codes_reviewed > 0 else 0
            },
            'comparison_metrics': {
                'original_accuracy': post_review_metrics['overall_accuracy'],
                'post_review_accuracy': post_review_metrics['overall_accuracy'] + improvement_in_accuracy,
                'net_improvement': improvement_in_accuracy,
                'relative_improvement': improvement_in_accuracy / post_review_metrics['overall_accuracy'] if post_review_metrics['overall_accuracy'] > 0 else 0
            },
            'patient_corrections': patient_corrections,
            'baseline_metrics': post_review_metrics
        }

if __name__ == "__main__":
    # Test the accuracy calculator
    calculator = AccuracyCalculator('sutherland_radiology_results.csv')
    original_metrics = calculator.calculate_original_accuracy()
    print(f"Original complete match rate: {original_metrics.complete_match_rate:.2%}")
    print(f"Original code accuracy: {original_metrics.code_level_accuracy:.2%}") 