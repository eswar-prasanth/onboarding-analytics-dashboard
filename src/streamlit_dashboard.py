import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from typing import Dict, List
import numpy as np

# Set page config
st.set_page_config(
    page_title="Sutherland Radiology Coding Analysis",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

class SutherlandDashboard:
    def __init__(self):
        self.load_data()
    
    def load_data(self):
        """Load all analysis data"""
        try:
            # Load analysis results
            with open('analysis_results.json', 'r') as f:
                self.analysis_results = json.load(f)
            
            # Load classification results
            with open('code_classifications.json', 'r') as f:
                self.classification_results = json.load(f)
            
            # Load partial match reviews
            with open('partial_match_reviews.json', 'r') as f:
                self.partial_match_reviews = json.load(f)
            
            # Load No Match reviews
            try:
                with open('no_match_reviews.json', 'r') as f:
                    self.no_match_reviews = json.load(f)
            except FileNotFoundError:
                self.no_match_reviews = []
            
            # Load comprehensive metrics
            with open('comprehensive_metrics.json', 'r') as f:
                self.comprehensive_metrics = json.load(f)
            
            # Load original data
            self.original_df = pd.read_csv('sutherland_radiology_results.csv')
            
            self.data_loaded = True
            
        except FileNotFoundError as e:
            st.error(f"Data file not found: {e}")
            self.data_loaded = False
        except Exception as e:
            st.error(f"Error loading data: {e}")
            self.data_loaded = False
    
    def create_accuracy_overview(self):
        """Create comprehensive accuracy overview section with all key metrics on one screen"""
        st.header("📊 Comprehensive Accuracy Analysis")
        
        if not self.data_loaded:
            st.error("Data not loaded. Please run the analysis first.")
            return
        
        # Get all required metrics
        original = self.comprehensive_metrics['original_accuracy']
        post_review = self.comprehensive_metrics['post_ai_review']
        improvements = self.comprehensive_metrics['improvements']
        manual_analysis = self.comprehensive_metrics.get('manual_coding_analysis', {})
        corrected_accuracy = self.comprehensive_metrics.get('corrected_code_accuracy', {})
        pre_review = self.comprehensive_metrics.get('pre_review_code_accuracy', {})
        post_review_code = self.comprehensive_metrics.get('post_review_code_accuracy', {})
        
        # ========================
        # SECTION 1: CHART-LEVEL ACCURACY OVERVIEW
        # ========================
        st.subheader("📈 Chart-Level Accuracy Overview")
        
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Original Complete Match Rate",
                f"{original['chart_level']['complete_match_rate']:.1%}",
                delta=None
            )
        
        with col2:
            improvement = improvements['accuracy_improvement']
            st.metric(
                "Post-Review Complete Match Rate",
                f"{post_review['complete_match_rate']:.1%}",
                delta=f"{improvement:.1%}"
            )
        
        with col3:
            st.metric(
                "Code-Level Accuracy",
                f"{original['code_level']['overall_accuracy']:.1%}",
                delta=None
            )
        
        with col4:
            st.metric(
                "Partial → Complete Conversions",
                improvements['partial_to_complete_conversions'],
                delta=None
            )
        
        # Chart-level accuracy comparison
        st.subheader("📊 Chart-Level Accuracy Comparison")
        
        # Create comparison data
        comparison_data = {
            'Metric': ['Complete Match', 'Partial Match', 'No Match'],
            'Original': [
                original['chart_level']['complete_match_rate'],
                original['chart_level']['partial_match_rate'],
                original['chart_level']['no_match_rate']
            ],
            'Post-Review': [
                post_review['complete_match_rate'],
                post_review['partial_match_rate'],
                post_review['no_match_rate']
            ]
        }
        
        df_comparison = pd.DataFrame(comparison_data)
        df_melted = df_comparison.melt(id_vars=['Metric'], var_name='Analysis', value_name='Rate')
        
        fig = px.bar(
            df_melted,
            x='Metric',
            y='Rate',
            color='Analysis',
            barmode='group',
            title="Chart-Level Accuracy: Original vs Post-Review",
            labels={'Rate': 'Percentage', 'Metric': 'Match Type'}
        )
        fig.update_layout(yaxis_tickformat='.1%')
        st.plotly_chart(fig, use_container_width=True)
        
        # ========================
        # SECTION 2: PRE VS POST REVIEW CODE ACCURACY
        # ========================
        st.markdown("---")
        st.subheader("🔄 Pre vs Post Review Code Accuracy")
        
        if pre_review and post_review_code:
            pre_metrics = pre_review.get('pre_review_metrics', {})
            post_metrics = post_review_code.get('post_review_metrics', {})
            comparison_metrics = post_review_code.get('comparison_metrics', {})
            
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Pre-Review Accuracy",
                    f"{pre_metrics.get('overall_accuracy', 0):.1%}",
                    delta=None
                )
            
            with col2:
                post_acc = comparison_metrics.get('post_review_accuracy', 0)
                improvement = comparison_metrics.get('net_improvement', 0)
                st.metric(
                    "Post-Review Accuracy",
                    f"{post_acc:.1%}",
                    delta=f"{improvement:.1%}"
                )
            
            with col3:
                st.metric(
                    "Codes Reviewed by AI",
                    post_metrics.get('codes_reviewed_by_ai', 0),
                    delta=None
                )
            
            with col4:
                st.metric(
                    "AI Corrections Accepted",
                    post_metrics.get('ai_corrections_accepted', 0),
                    delta=None
                )
            
            # Pre vs Post comparison charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Accuracy comparison bar chart
                accuracy_data = {
                    'Phase': ['Pre-Review', 'Post-Review'],
                    'Accuracy': [
                        pre_metrics.get('overall_accuracy', 0),
                        comparison_metrics.get('post_review_accuracy', 0)
                    ]
                }
                
                fig = px.bar(
                    accuracy_data,
                    x='Phase',
                    y='Accuracy',
                    title="Code Accuracy: Pre vs Post Review",
                    color='Phase',
                    color_discrete_map={'Pre-Review': '#ff7f0e', 'Post-Review': '#2ca02c'}
                )
                fig.update_layout(yaxis_tickformat='.1%', showlegend=False)
                fig.update_yaxes(range=[0, 1])
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Error breakdown pie chart
                correct_codes = pre_metrics.get('correctly_coded_by_ai', 0)
                missed_codes = pre_metrics.get('missed_by_ai', 0)
                ai_corrections = post_metrics.get('ai_corrections_accepted', 0)
                
                # Calculate post-review breakdown
                post_missed = missed_codes - ai_corrections
                
                breakdown_data = {
                    'Category': ['Correctly Coded', 'Missed by AI', 'AI Corrections'],
                    'Count': [correct_codes, post_missed, ai_corrections],
                    'Color': ['#2ca02c', '#d62728', '#1f77b4']
                }
                
                fig = px.pie(
                    values=breakdown_data['Count'],
                    names=breakdown_data['Category'],
                    title="Post-Review Code Breakdown",
                    color_discrete_sequence=breakdown_data['Color']
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Pre/Post review code accuracy data not available. Please run the full analysis first.")
        
        # ========================
        # SECTION 3: AI vs HUMAN CODING ACCURACY COMPARISON
        # ========================
        st.markdown("---")
        st.subheader("✨ AI vs Human Coding Accuracy Comparison")
        st.markdown("*This section compares AI and human (Sutherland) coding accuracy after detailed review of discrepancies*")
        
        if corrected_accuracy and manual_analysis:
            # Calculate accuracy metrics
            total_reviewed = manual_analysis.get('total_reviewed_codes', 0)
            ai_correct = corrected_accuracy.get('ai_correct_codes', 0)
            sutherland_correct = corrected_accuracy.get('sutherland_correct_codes', 0)
            sutherland_errors = manual_analysis.get('sutherland_errors', 0)
            ai_corrections = manual_analysis.get('ai_corrections', 0)
            
            # Calculate individual accuracy rates
            ai_accuracy = ai_correct / total_reviewed if total_reviewed > 0 else 0
            human_accuracy = sutherland_correct / total_reviewed if total_reviewed > 0 else 0
            
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "📊 Total Codes Reviewed",
                    total_reviewed,
                    help="Total number of codes analyzed in discrepancy review"
                )
            
            with col2:
                st.metric(
                    "🤖 AI Accuracy",
                    f"{ai_accuracy:.1%}",
                    delta=f"{ai_correct} correct decisions",
                    help="Percentage of times AI was correct in coding decisions"
                )
            
            with col3:
                st.metric(
                    "👨‍⚕️ Human Accuracy", 
                    f"{human_accuracy:.1%}",
                    delta=f"{sutherland_correct} correct decisions",
                    help="Percentage of times Sutherland coders were correct"
                )
            
            with col4:
                accuracy_diff = ai_accuracy - human_accuracy
                st.metric(
                    "🔄 AI vs Human Difference",
                    f"{accuracy_diff:+.1%}",
                    delta="AI more accurate" if accuracy_diff > 0 else "Human more accurate",
                    help="Difference in accuracy between AI and human coding"
                )
            
            # Detailed comparison visualization
            col1, col2 = st.columns(2)
            
            with col1:
                # Accuracy comparison bar chart
                comparison_data = {
                    'Coder': ['AI', 'Human (Sutherland)'],
                    'Accuracy': [ai_accuracy, human_accuracy],
                    'Correct Codes': [ai_correct, sutherland_correct]
                }
                
                fig = px.bar(
                    comparison_data,
                    x='Coder',
                    y='Accuracy',
                    title="Coding Accuracy: AI vs Human",
                    color='Coder',
                    color_discrete_map={'AI': '#1f77b4', 'Human (Sutherland)': '#ff7f0e'},
                    text='Correct Codes'
                )
                fig.update_layout(yaxis_tickformat='.1%', showlegend=False)
                fig.update_traces(texttemplate='%{text} correct', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Error breakdown
                error_data = {
                    'Type': ['Human Errors', 'AI Corrections Made', 'Remaining Issues'],
                    'Count': [
                        sutherland_errors,
                        ai_corrections,
                        max(0, total_reviewed - ai_correct - sutherland_correct)
                    ]
                }
                
                fig = px.pie(
                    values=error_data['Count'],
                    names=error_data['Type'],
                    title="Error Distribution in Reviewed Codes",
                    color_discrete_sequence=['#d62728', '#2ca02c', '#ff7f0e']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # ========================
            # SECTION 4: MANUAL CODING ACCURACY DETAILS
            # ========================
            st.markdown("---")
            st.subheader("👨‍⚕️ Manual Coding Accuracy Details")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Manual Coding Accuracy",
                    f"{manual_analysis.get('manual_coding_accuracy', 0):.1%}",
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Sutherland Errors",
                    manual_analysis.get('sutherland_errors', 0),
                    delta=None
                )
            
            with col3:
                st.metric(
                    "AI Corrections",
                    manual_analysis.get('ai_corrections', 0),
                    delta=None
                )
            
            with col4:
                st.metric(
                    "Extra Codes by AI",
                    manual_analysis.get('extra_codes_by_ai', 0),
                    delta=None
                )
            
            # Manual coding accuracy breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                # Error rate visualization
                total_codes = manual_analysis.get('total_reviewed_codes', 0)
                errors = manual_analysis.get('sutherland_errors', 0)
                correct = total_codes - errors
                
                if total_codes > 0:
                    fig = px.pie(
                        values=[correct, errors],
                        names=['Correct', 'Errors'],
                        title="Manual Coding Accuracy Distribution",
                        color_discrete_map={'Correct': 'green', 'Errors': 'red'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # AI vs Manual comparison
                comparison_data = {
                    'Metric': ['AI Corrections', 'Sutherland Errors'],
                    'Count': [ai_corrections, sutherland_errors]
                }
                
                fig = px.bar(
                    comparison_data,
                    x='Metric',
                    y='Count',
                    title="AI Corrections vs Manual Errors",
                    color='Metric'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # ========================
            # SECTION 5: KEY INSIGHTS
            # ========================
            st.markdown("---")
            st.subheader("💡 Key Insights from Comprehensive Analysis")
            
            insights = []
            
            # Chart-level insights
            if improvement > 0:
                insights.append(f"📈 **Chart-level accuracy improved by {improvement:.1%}** after AI review")
            
            # Code-level insights
            if pre_review and post_review_code:
                code_improvement = comparison_metrics.get('net_improvement', 0)
                if code_improvement > 0:
                    insights.append(f"🔧 **Code-level accuracy improved by {code_improvement:.1%}** through AI corrections")
            
            # AI vs Human insights
            if ai_accuracy > human_accuracy:
                diff_pct = (ai_accuracy - human_accuracy) * 100
                insights.append(f"🎯 **AI outperforms human coding** by {diff_pct:.1f} percentage points")
                insights.append(f"✅ AI made {ai_corrections} corrections where humans were wrong")
            elif human_accuracy > ai_accuracy:
                diff_pct = (human_accuracy - ai_accuracy) * 100
                insights.append(f"👨‍⚕️ **Human coding outperforms AI** by {diff_pct:.1f} percentage points")
            else:
                insights.append("🤝 **AI and human coding accuracy are equivalent**")
            
            # Manual coding insights
            manual_acc = manual_analysis.get('manual_coding_accuracy', 1.0)
            if manual_acc < 0.8:
                insights.append("🔴 **Manual coding accuracy is below 80%** - significant improvement needed")
            elif manual_acc < 0.9:
                insights.append("🟡 **Manual coding accuracy has room for improvement**")
            else:
                insights.append("🟢 **Manual coding accuracy is good**")
            
            # Overall insights
            overall_corrected = corrected_accuracy.get('corrected_accuracy', 0)
            insights.append(f"📊 **Combined post-review accuracy: {overall_corrected:.1%}** (using best of AI + Human)")
            
            # Display insights
            for insight in insights:
                st.markdown(insight)
        
        else:
            st.warning("Manual coding analysis not available. Please run the AI review first.")
    
    def create_code_importance_analysis(self):
        """Create code importance analysis section"""
        st.header("🎯 Code Importance Analysis")
        
        if not self.data_loaded:
            return
        
        importance_data = self.comprehensive_metrics['code_importance_analysis']
        
        # Calculate total missed codes by AI
        original_accuracy = self.comprehensive_metrics['original_accuracy']['code_level']
        total_missed_by_ai = original_accuracy['total_missed_codes']
        
        # Overview metrics
        st.subheader("📊 Missed Code Analysis Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Missed Codes by AI",
                total_missed_by_ai,
                delta=None
            )
        
        with col2:
            relevant_codes = importance_data['important_codes']['missed_important_codes']
            st.metric(
                "Relevant Codes Missed",
                relevant_codes,
                delta=None
            )
        
        with col3:
            not_relevant_codes = importance_data['unimportant_codes']['missed_unimportant_codes']
            st.metric(
                "Not Relevant Codes Missed",
                not_relevant_codes,
                delta=None
            )
        
        with col4:
            relevant_accuracy = importance_data['important_codes']['important_code_accuracy']
            st.metric(
                "Accuracy (Relevant Codes Only)",
                f"{relevant_accuracy:.1%}",
                delta=None
            )
        
        # Detailed breakdown
        st.subheader("🔍 Detailed Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Relevant Codes")
            important = importance_data['important_codes']
            st.metric("Total Relevant Codes", important['total_important_codes'])
            st.metric("Missed Relevant Codes", important['missed_important_codes'])
            st.metric("Relevant Code Accuracy", f"{important['important_code_accuracy']:.1%}")
        
        with col2:
            st.subheader("Not Relevant Codes")
            unimportant = importance_data['unimportant_codes']
            st.metric("Total Not Relevant Codes", unimportant['total_unimportant_codes'])
            st.metric("Missed Not Relevant Codes", unimportant['missed_unimportant_codes'])
            st.metric("Not Relevant Code Accuracy", f"{unimportant['unimportant_code_accuracy']:.1%}")
        
        # Code classification table
        st.subheader("📋 Code Classification Details")
        
        # Create DataFrame from classification results
        classification_df = pd.DataFrame(self.classification_results)
        if not classification_df.empty:
            # Update terminology in the dataframe
            if 'classification' in classification_df.columns:
                classification_df['relevance'] = classification_df['classification'].replace({
                    'important': 'relevant',
                    'unimportant': 'not relevant'
                })
            
            # Select relevant columns with updated names
            display_columns = ['code', 'relevance', 'category', 'clinical_impact', 'reasoning']
            available_columns = [col for col in display_columns if col in classification_df.columns]
            
            if available_columns:
                # Rename columns for display
                display_df = classification_df[available_columns].copy()
                if 'relevance' in display_df.columns:
                    display_df = display_df.rename(columns={'relevance': 'Relevance'})
                if 'code' in display_df.columns:
                    display_df = display_df.rename(columns={'code': 'Code'})
                if 'category' in display_df.columns:
                    display_df = display_df.rename(columns={'category': 'Category'})
                if 'clinical_impact' in display_df.columns:
                    display_df = display_df.rename(columns={'clinical_impact': 'Clinical Impact'})
                if 'reasoning' in display_df.columns:
                    display_df = display_df.rename(columns={'reasoning': 'Reasoning'})
                
                st.dataframe(display_df, use_container_width=True)
    
    def create_missed_codes_analysis(self):
        """Create missed codes analysis section"""
        st.header("❌ Missed Codes Analysis")
        
        if not self.data_loaded:
            return
        
        # Top missed codes
        code_frequency = self.analysis_results.get('code_frequency', {})
        
        if code_frequency:
            st.subheader("Most Frequently Missed Codes")
            
            # Create DataFrame
            freq_df = pd.DataFrame([
                {'Code': code, 'Frequency': freq} 
                for code, freq in list(code_frequency.items())[:20]
            ])
            
            # Create bar chart
            fig = px.bar(
                freq_df,
                x='Code',
                y='Frequency',
                title="Top 20 Most Frequently Missed Codes"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display table
            st.dataframe(freq_df, use_container_width=True)
        
        # Patient-level analysis
        st.subheader("Patient-Level Missed Codes Distribution")
        
        patient_analysis = self.analysis_results.get('patient_level_analysis', [])
        if patient_analysis:
            # Create classification lookup
            classification_lookup = {}
            for result in self.classification_results:
                code = result.get('code', '')
                classification = result.get('classification', 'unknown')
                # Map to new terminology
                relevance = 'Relevant' if classification == 'important' else 'Not Relevant'
                classification_lookup[code] = relevance
            
            # Prepare data for stacked bar chart
            patient_data = []
            for patient in patient_analysis:
                patient_id = patient['patient_id']
                missed_codes = patient.get('missed_by_ai', [])
                
                relevant_count = 0
                not_relevant_count = 0
                
                for code in missed_codes:
                    if code in classification_lookup:
                        if classification_lookup[code] == 'Relevant':
                            relevant_count += 1
                        else:
                            not_relevant_count += 1
                    else:
                        # If not classified, assume not relevant
                        not_relevant_count += 1
                
                total_missed = relevant_count + not_relevant_count
                if total_missed > 0:  # Only include patients with missed codes
                    patient_data.append({
                        'Patient': f"Patient {patient_id}",
                        'Relevant': relevant_count,
                        'Not Relevant': not_relevant_count,
                        'Total': total_missed
                    })
            
            if patient_data:
                # Sort by total missed codes for better visualization
                patient_data.sort(key=lambda x: x['Total'], reverse=True)
                
                # Take top 20 patients with most missed codes for readability
                top_patients = patient_data[:20]
                
                # Create stacked bar chart
                patient_names = [p['Patient'] for p in top_patients]
                relevant_counts = [p['Relevant'] for p in top_patients]
                not_relevant_counts = [p['Not Relevant'] for p in top_patients]
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    name='Relevant',
                    x=patient_names,
                    y=relevant_counts,
                    marker_color='#d62728'  # Red for relevant (important) codes
                ))
                
                fig.add_trace(go.Bar(
                    name='Not Relevant',
                    x=patient_names,
                    y=not_relevant_counts,
                    marker_color='#2ca02c'  # Green for not relevant codes
                ))
                
                fig.update_layout(
                    title="Distribution of Missed Codes per Patient (Top 20)",
                    xaxis_title="Patients",
                    yaxis_title="Number of Missed Codes",
                    barmode='stack',
                    xaxis_tickangle=-45,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary statistics
                col1, col2, col3 = st.columns(3)
                
                total_relevant_missed = sum(p['Relevant'] for p in patient_data)
                total_not_relevant_missed = sum(p['Not Relevant'] for p in patient_data)
                total_patients_with_missed = len(patient_data)
                
                with col1:
                    st.metric("Patients with Missed Codes", total_patients_with_missed)
                
                with col2:
                    st.metric("Total Relevant Codes Missed", total_relevant_missed)
                
                with col3:
                    st.metric("Total Not Relevant Codes Missed", total_not_relevant_missed)
            else:
                st.info("No patient data available for missed codes distribution.")
    
    def create_ai_review_results(self):
        """Create AI review results section"""
        st.header("🤖 AI Review Results")
        
        if not self.data_loaded:
            return
        
        # Summary of changes
        changes = self.comprehensive_metrics.get('detailed_changes', [])
        
        if changes:
            st.subheader("Summary of Changes")
            changes_df = pd.DataFrame(changes)
            
            # Count changes by type
            change_counts = changes_df['new_match'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    values=change_counts.values,
                    names=change_counts.index,
                    title="Types of Changes Made"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Change Details")
                st.dataframe(changes_df, use_container_width=True)
        
        # Partial match review details
        st.subheader("Partial Match Review Details")
        
        review_summary = []
        for review in self.partial_match_reviews:
            if 'error' not in review:
                scores = review.get('coding_accuracy_score', {})
                review_summary.append({
                    'Patient ID': review.get('patient_id'),
                    'Sutherland Score': scores.get('sutherland_score', 0),
                    'AI Score': scores.get('ai_score', 0),
                    'Assessment': review.get('overall_assessment', 'N/A')
                })
        
        if review_summary:
            review_df = pd.DataFrame(review_summary)
            st.dataframe(review_df, use_container_width=True)
            
            # Score distribution
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=[r['Sutherland Score'] for r in review_summary],
                name='Sutherland Scores',
                opacity=0.7
            ))
            fig.add_trace(go.Histogram(
                x=[r['AI Score'] for r in review_summary],
                name='AI Scores',
                opacity=0.7
            ))
            fig.update_layout(
                title="Distribution of Coding Accuracy Scores",
                xaxis_title="Accuracy Score",
                yaxis_title="Number of Cases",
                barmode='overlay'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def create_no_match_review_results(self):
        """Create No Match review results section"""
        st.header("🔍 No Match Review Results")
        
        if not self.data_loaded:
            return
        
        no_match_analysis = self.comprehensive_metrics.get('no_match_analysis', {})
        
        if not no_match_analysis or not self.no_match_reviews:
            st.warning("No Match review data not available. Please run the No Match review analysis first.")
            return
        
        # Overview metrics
        st.subheader("📊 No Match Review Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total No Match Cases",
                no_match_analysis.get('total_no_match_cases', 0),
                delta=None
            )
        
        with col2:
            st.metric(
                "Successful Reviews",
                no_match_analysis.get('successful_reviews', 0),
                delta=f"{no_match_analysis.get('review_success_rate', 0):.1%} success rate"
            )
        
        with col3:
            st.metric(
                "Potential Upgrades",
                no_match_analysis.get('potential_upgrades', 0),
                delta=None
            )
        
        with col4:
            ai_better = no_match_analysis.get('ai_better_cases', 0)
            sutherland_better = no_match_analysis.get('sutherland_better_cases', 0)
            st.metric(
                "AI vs Human Performance",
                f"AI: {ai_better}, Human: {sutherland_better}",
                delta="AI leading" if ai_better > sutherland_better else "Human leading" if sutherland_better > ai_better else "Tied"
            )
        
        # Upgrade potential analysis
        st.subheader("📈 Upgrade Potential Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Upgrade potential pie chart
            upgrade_potential = no_match_analysis.get('upgrade_potential', {})
            to_partial = upgrade_potential.get('to_partial_match', 0)
            to_complete = upgrade_potential.get('to_complete_match', 0)
            no_upgrade = no_match_analysis.get('successful_reviews', 0) - to_partial - to_complete
            
            if to_partial > 0 or to_complete > 0 or no_upgrade > 0:
                upgrade_data = {
                    'Category': ['To Partial Match', 'To Complete Match', 'No Upgrade'],
                    'Count': [to_partial, to_complete, max(0, no_upgrade)]
                }
                
                fig = px.pie(
                    values=upgrade_data['Count'],
                    names=upgrade_data['Category'],
                    title="No Match Cases - Upgrade Potential",
                    color_discrete_sequence=['#ff7f0e', '#2ca02c', '#d62728']
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # AI vs Human performance
            performance_data = {
                'Performer': ['AI Better', 'Human Better', 'Equal'],
                'Count': [
                    no_match_analysis.get('ai_better_cases', 0),
                    no_match_analysis.get('sutherland_better_cases', 0),
                    max(0, no_match_analysis.get('successful_reviews', 0) - 
                        no_match_analysis.get('ai_better_cases', 0) - 
                        no_match_analysis.get('sutherland_better_cases', 0))
                ]
            }
            
            fig = px.bar(
                performance_data,
                x='Performer',
                y='Count',
                title="AI vs Human Performance in No Match Cases",
                color='Performer',
                color_discrete_map={'AI Better': '#1f77b4', 'Human Better': '#ff7f0e', 'Equal': '#2ca02c'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed review results
        st.subheader("📋 No Match Review Details")
        
        review_summary = []
        for review in self.no_match_reviews:
            if 'error' not in review:
                scores = review.get('coding_accuracy_score', {})
                match_potential = review.get('match_potential', {})
                
                review_summary.append({
                    'Patient ID': review.get('patient_id'),
                    'Sutherland Score': scores.get('sutherland_score', 0),
                    'AI Score': scores.get('ai_score', 0),
                    'Could be Partial': '✅' if match_potential.get('could_be_partial_match', False) else '❌',
                    'Could be Complete': '✅' if match_potential.get('could_be_complete_match', False) else '❌',
                    'Assessment': review.get('overall_assessment', 'N/A')
                })
        
        if review_summary:
            review_df = pd.DataFrame(review_summary)
            st.dataframe(review_df, use_container_width=True)
            
            # Score distribution
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=[r['Sutherland Score'] for r in review_summary],
                name='Sutherland Scores',
                opacity=0.7,
                marker_color='#ff7f0e'
            ))
            fig.add_trace(go.Histogram(
                x=[r['AI Score'] for r in review_summary],
                name='AI Scores',
                opacity=0.7,
                marker_color='#1f77b4'
            ))
            fig.update_layout(
                title="Distribution of Coding Accuracy Scores in No Match Cases",
                xaxis_title="Accuracy Score",
                yaxis_title="Number of Cases",
                barmode='overlay'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Key insights
        st.subheader("💡 Key Insights from No Match Reviews")
        
        insights = []
        
        total_cases = no_match_analysis.get('total_no_match_cases', 0)
        potential_upgrades = no_match_analysis.get('potential_upgrades', 0)
        ai_better = no_match_analysis.get('ai_better_cases', 0)
        sutherland_better = no_match_analysis.get('sutherland_better_cases', 0)
        
        if total_cases > 0:
            upgrade_rate = (potential_upgrades / total_cases) * 100
            insights.append(f"📈 **{upgrade_rate:.1f}% of No Match cases** have potential for upgrade to Partial or Complete Match")
        
        if ai_better > sutherland_better:
            insights.append(f"🤖 **AI coding is more accurate** in {ai_better} cases vs {sutherland_better} for human coding")
        elif sutherland_better > ai_better:
            insights.append(f"👨‍⚕️ **Human coding is more accurate** in {sutherland_better} cases vs {ai_better} for AI coding")
        else:
            insights.append(f"🤝 **AI and human coding perform equally** in No Match cases")
        
        upgrade_potential = no_match_analysis.get('upgrade_potential', {})
        to_complete = upgrade_potential.get('to_complete_match', 0)
        if to_complete > 0:
            insights.append(f"⭐ **{to_complete} No Match cases** could potentially be **Complete Matches**")
        
        to_partial = upgrade_potential.get('to_partial_match', 0)  
        if to_partial > 0:
            insights.append(f"📊 **{to_partial} No Match cases** could potentially be **Partial Matches**")
        
        success_rate = no_match_analysis.get('review_success_rate', 0)
        insights.append(f"✅ **Review success rate: {success_rate:.1%}** of No Match cases were successfully analyzed")
        
        for insight in insights:
            st.markdown(insight)
    
    def create_detailed_patient_view(self):
        """Create detailed patient view section"""
        st.header("👤 Detailed Patient Analysis")
        
        if not self.data_loaded:
            return
        
        # Patient selector
        patient_analysis = self.analysis_results.get('patient_level_analysis', [])
        if not patient_analysis:
            st.warning("No patient analysis data available")
            return
        
        patient_ids = [p['patient_id'] for p in patient_analysis]
        selected_patient = st.selectbox("Select Patient ID", patient_ids)
        
        # Find selected patient data
        patient_data = next((p for p in patient_analysis if p['patient_id'] == selected_patient), None)
        
        if patient_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Coding Information")
                st.write(f"**Patient ID:** {patient_data['patient_id']}")
                st.write(f"**Match Result:** {patient_data['match_result']}")
                st.write(f"**Sutherland Codes:** {', '.join(patient_data['sutherland_codes'])}")
                st.write(f"**AI Codes:** {', '.join(patient_data['ai_codes'])}")
                
                if patient_data['missed_by_ai']:
                    st.write(f"**Missed by AI:** {', '.join(patient_data['missed_by_ai'])}")
                
                if patient_data['extra_by_ai']:
                    st.write(f"**Extra by AI:** {', '.join(patient_data['extra_by_ai'])}")
            
            with col2:
                st.subheader("Statistics")
                st.metric("Total Sutherland Codes", len(patient_data['sutherland_codes']))
                st.metric("Total AI Codes", len(patient_data['ai_codes']))
                st.metric("Missed by AI", patient_data['missed_count'])
                st.metric("Extra by AI", patient_data['extra_count'])
            
            # Clinical text
            st.subheader("Clinical Text")
            with st.expander("View Clinical Text"):
                st.text_area("Clinical Text", patient_data['clinical_text'], height=300, disabled=True)
            
            # AI Review (if available)
            patient_review = next((r for r in self.partial_match_reviews 
                                 if r.get('patient_id') == selected_patient), None)
            
            if patient_review and 'error' not in patient_review:
                st.subheader("AI Review Results")
                
                scores = patient_review.get('coding_accuracy_score', {})
                col3, col4 = st.columns(2)
                
                with col3:
                    st.metric("Sutherland Accuracy Score", f"{scores.get('sutherland_score', 0):.2f}")
                
                with col4:
                    st.metric("AI Accuracy Score", f"{scores.get('ai_score', 0):.2f}")
                
                st.write("**Overall Assessment:**")
                st.write(patient_review.get('overall_assessment', 'No assessment available'))
    
    def create_pre_post_review_accuracy(self):
        """Create unified pre-review vs post-review accuracy analysis including no match conversions"""
        st.header("🔄 Unified Post-Review Accuracy Analysis")
        
        if not self.data_loaded:
            return
        
        # Get unified post-review metrics
        unified_metrics = self.comprehensive_metrics.get('unified_post_review_accuracy', {})
        
        if not unified_metrics:
            st.warning("Unified post-review accuracy data not available. Please run the full analysis first.")
            return
        
        original_acc = unified_metrics.get('original_accuracy', {})
        post_review_acc = unified_metrics.get('unified_post_review_accuracy', {})
        total_improvements = unified_metrics.get('total_improvements', {})
        improvement_breakdown = unified_metrics.get('improvement_breakdown', {})
        
        # Executive Summary
        st.subheader("📊 Executive Summary - All Improvements Combined")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Original Complete Match Rate",
                f"{original_acc.get('complete_match_rate', 0):.1%}",
                delta=None
            )
        
        with col2:
            unified_complete = post_review_acc.get('complete_match_rate', 0)
            complete_improvement = total_improvements.get('complete_match_improvement', 0)
            st.metric(
                "Post-Review Complete Match Rate",
                f"{unified_complete:.1%}",
                delta=f"+{complete_improvement:.1%}"
            )
        
        with col3:
            original_code_acc = original_acc.get('code_level_accuracy', 0)
            unified_code_acc = post_review_acc.get('code_level_accuracy', 0)
            code_improvement = total_improvements.get('code_level_improvement', 0)
            st.metric(
                "Code-Level Accuracy",
                f"{unified_code_acc:.1%}",
                delta=f"+{code_improvement:.1%}"
            )
        
        with col4:
            combined_improvement = total_improvements.get('combined_accuracy_improvement', 0)
            st.metric(
                "Total Combined Improvement",
                f"+{combined_improvement:.1%}",
                delta=None
            )
        
        # Bifurcated Improvement Analysis
        st.subheader("🔀 Improvement Source Breakdown")
        
        # Get breakdown data
        partial_match_data = improvement_breakdown.get('partial_match_improvements', {})
        no_match_data = improvement_breakdown.get('no_match_conversions', {})
        
        # Improvement sources visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Improvement contribution pie chart
            improvement_sources = {
                'Source': ['Partial Match Reviews', 'No Match Conversions'],
                'Contribution': [
                    partial_match_data.get('code_level_improvement', 0) * 100,  # Convert to percentage points
                    no_match_data.get('chart_level_improvement', 0) * 100
                ]
            }
            
            fig = px.pie(
                values=improvement_sources['Contribution'],
                names=improvement_sources['Source'],
                title="Accuracy Improvement by Source",
                color_discrete_sequence=['#1f77b4', '#ff7f0e']
            )
            fig.update_traces(texttemplate='%{label}<br>+%{value:.1f}pp')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Chart-level vs Code-level improvements
            improvement_types = {
                'Type': ['Chart-Level Improvement', 'Code-Level Improvement'],
                'Improvement': [
                    total_improvements.get('chart_level_improvement', 0) * 100,
                    total_improvements.get('code_level_improvement', 0) * 100
                ]
            }
            
            fig = px.bar(
                improvement_types,
                x='Type',
                y='Improvement',
                title="Improvement by Analysis Type",
                color='Type',
                color_discrete_sequence=['#2ca02c', '#9467bd']
            )
            fig.update_layout(yaxis_title="Improvement (Percentage Points)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Before vs After Comprehensive Comparison
        st.subheader("📈 Before vs After Comprehensive Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Chart-level accuracy comparison
            chart_data = {
                'Match Type': ['Complete Match', 'Partial Match', 'No Match'],
                'Original': [
                    original_acc.get('complete_match_rate', 0),
                    original_acc.get('partial_match_rate', 0),
                    original_acc.get('no_match_rate', 0)
                ],
                'Post-Review': [
                    post_review_acc.get('complete_match_rate', 0),
                    post_review_acc.get('partial_match_rate', 0),
                    post_review_acc.get('no_match_rate', 0)
                ]
            }
            
            chart_df = pd.DataFrame(chart_data)
            chart_melted = chart_df.melt(id_vars=['Match Type'], var_name='Phase', value_name='Rate')
            
            fig = px.bar(
                chart_melted,
                x='Match Type',
                y='Rate',
                color='Phase',
                barmode='group',
                title="Chart-Level Match Rates: Before vs After",
                color_discrete_map={'Original': '#ff7f0e', 'Post-Review': '#2ca02c'}
            )
            fig.update_layout(yaxis_tickformat='.1%')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Overall accuracy progression
            progression_data = {
                'Phase': ['Original', 'After Partial Match Review', 'After No Match Conversions'],
                'Chart Accuracy': [
                    original_acc.get('complete_match_rate', 0),
                    original_acc.get('complete_match_rate', 0),  # No change from partial match reviews at chart level
                    post_review_acc.get('complete_match_rate', 0)
                ],
                'Code Accuracy': [
                    original_acc.get('code_level_accuracy', 0),
                    original_acc.get('code_level_accuracy', 0) + partial_match_data.get('code_level_improvement', 0),
                    post_review_acc.get('code_level_accuracy', 0)
                ]
            }
            
            fig = px.line(
                progression_data,
                x='Phase',
                y=['Chart Accuracy', 'Code Accuracy'],
                title="Accuracy Progression Through Reviews",
                markers=True
            )
            fig.update_layout(yaxis_tickformat='.1%', yaxis_title="Accuracy Rate")
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed Breakdown by Source
        st.subheader("🔍 Detailed Improvement Breakdown")
        
        # Create tabs for each improvement source
        tab1, tab2 = st.tabs(["🔧 Partial Match Reviews", "🔄 No Match Conversions"])
        
        with tab1:
            st.write("**Source:** AI Review of Partial Match Cases")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Codes Reviewed",
                    partial_match_data.get('codes_reviewed', 0)
                )
            
            with col2:
                st.metric(
                    "Codes Corrected",
                    partial_match_data.get('codes_corrected', 0)
                )
            
            with col3:
                st.metric(
                    "Code-Level Improvement",
                    f"+{partial_match_data.get('code_level_improvement', 0):.1%}"
                )
            
            with col4:
                st.metric(
                    "AI Review Accuracy",
                    f"{partial_match_data.get('ai_accuracy_on_reviews', 0):.1%}"
                )
        
        with tab2:
            st.write("**Source:** No Match to Match Conversions")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Cases Reviewed",
                    no_match_data.get('cases_reviewed', 0)
                )
            
            with col2:
                st.metric(
                    "Potential Complete Conversions",
                    no_match_data.get('potential_complete_conversions', 0)
                )
            
            with col3:
                st.metric(
                    "Potential Partial Conversions",
                    no_match_data.get('potential_partial_conversions', 0)
                )
            
            with col4:
                st.metric(
                    "Chart-Level Improvement",
                    f"+{no_match_data.get('chart_level_improvement', 0):.1%}"
                )
        
        # Summary insights
        st.subheader("💡 Key Insights")
        
        insights = []
        
        # Calculate key metrics for insights
        total_chart_improvement = total_improvements.get('chart_level_improvement', 0) * 100
        total_code_improvement = total_improvements.get('code_level_improvement', 0) * 100
        
        if total_chart_improvement > 0:
            insights.append(f"📈 No Match conversions could improve chart-level complete match rate by **{total_chart_improvement:.1f} percentage points**")
        
        if total_code_improvement > 0:
            insights.append(f"🎯 Partial match reviews improved code-level accuracy by **{total_code_improvement:.1f} percentage points**")
        
        if partial_match_data.get('codes_corrected', 0) > 0:
            insights.append(f"🔧 AI successfully corrected **{partial_match_data.get('codes_corrected', 0)} coding errors** through partial match reviews")
        
        if no_match_data.get('total_conversions', 0) > 0:
            insights.append(f"🔄 **{no_match_data.get('total_conversions', 0)} no match cases** have potential for upgrade to partial or complete matches")
        
        combined_improvement = total_chart_improvement + total_code_improvement
        if combined_improvement > 0:
            insights.append(f"🚀 **Combined improvement potential: {combined_improvement:.1f} percentage points** across all review types")
        
        for insight in insights:
            st.write(insight)
    
    def create_manual_coding_accuracy(self):
        """Create manual coding accuracy analysis section"""
        st.header("👨‍⚕️ Manual Coding Accuracy Analysis")
        
        if not self.data_loaded:
            return
        
        manual_analysis = self.comprehensive_metrics.get('manual_coding_analysis', {})
        corrected_accuracy = self.comprehensive_metrics.get('corrected_code_accuracy', {})
        
        if not manual_analysis:
            st.warning("Manual coding analysis not available. Please run the AI review first.")
            return
        
        # Overview metrics
        st.subheader("📊 Manual Coding Performance Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Manual Coding Accuracy",
                f"{manual_analysis.get('manual_coding_accuracy', 0):.1%}",
                delta=None
            )
        
        with col2:
            st.metric(
                "Sutherland Errors",
                manual_analysis.get('sutherland_errors', 0),
                delta=None
            )
        
        with col3:
            st.metric(
                "AI Corrections",
                manual_analysis.get('ai_corrections', 0),
                delta=None
            )
        
        with col4:
            st.metric(
                "Extra Codes by AI",
                manual_analysis.get('extra_codes_by_ai', 0),
                delta=None
            )
        
        # Detailed breakdown
        st.subheader("🔍 Error Analysis Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Error rate visualization
            total_codes = manual_analysis.get('total_reviewed_codes', 0)
            errors = manual_analysis.get('sutherland_errors', 0)
            correct = total_codes - errors
            
            if total_codes > 0:
                fig = px.pie(
                    values=[correct, errors],
                    names=['Correct', 'Errors'],
                    title="Manual Coding Accuracy Distribution",
                    color_discrete_map={'Correct': 'green', 'Errors': 'red'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # AI vs Manual comparison
            ai_corrections = manual_analysis.get('ai_corrections', 0)
            sutherland_errors = manual_analysis.get('sutherland_errors', 0)
            
            comparison_data = {
                'Metric': ['AI Corrections', 'Sutherland Errors'],
                'Count': [ai_corrections, sutherland_errors]
            }
            
            fig = px.bar(
                comparison_data,
                x='Metric',
                y='Count',
                title="AI Corrections vs Manual Errors",
                color='Metric'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Enhanced post-review accuracy analysis
        if corrected_accuracy and manual_analysis:
            st.subheader("✨ AI vs Human Coding Accuracy Comparison")
            st.markdown("*This section compares AI and human (Sutherland) coding accuracy after detailed review of discrepancies*")
            
            # Calculate accuracy metrics
            total_reviewed = manual_analysis.get('total_reviewed_codes', 0)
            ai_correct = corrected_accuracy.get('ai_correct_codes', 0)
            sutherland_correct = corrected_accuracy.get('sutherland_correct_codes', 0)
            sutherland_errors = manual_analysis.get('sutherland_errors', 0)
            ai_corrections = manual_analysis.get('ai_corrections', 0)
            
            # Calculate individual accuracy rates
            ai_accuracy = ai_correct / total_reviewed if total_reviewed > 0 else 0
            human_accuracy = sutherland_correct / total_reviewed if total_reviewed > 0 else 0
            
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "📊 Total Codes Reviewed",
                    total_reviewed,
                    help="Total number of codes analyzed in discrepancy review"
                )
            
            with col2:
                st.metric(
                    "🤖 AI Accuracy",
                    f"{ai_accuracy:.1%}",
                    delta=f"{ai_correct} correct decisions",
                    help="Percentage of times AI was correct in coding decisions"
                )
            
            with col3:
                st.metric(
                    "👨‍⚕️ Human Accuracy", 
                    f"{human_accuracy:.1%}",
                    delta=f"{sutherland_correct} correct decisions",
                    help="Percentage of times Sutherland coders were correct"
                )
            
            with col4:
                accuracy_diff = ai_accuracy - human_accuracy
                st.metric(
                    "🔄 AI vs Human Difference",
                    f"{accuracy_diff:+.1%}",
                    delta="AI more accurate" if accuracy_diff > 0 else "Human more accurate",
                    help="Difference in accuracy between AI and human coding"
                )
            
            # Detailed comparison visualization
            col1, col2 = st.columns(2)
            
            with col1:
                # Accuracy comparison bar chart
                comparison_data = {
                    'Coder': ['AI', 'Human (Sutherland)'],
                    'Accuracy': [ai_accuracy, human_accuracy],
                    'Correct Codes': [ai_correct, sutherland_correct]
                }
                
                fig = px.bar(
                    comparison_data,
                    x='Coder',
                    y='Accuracy',
                    title="Coding Accuracy: AI vs Human",
                    color='Coder',
                    color_discrete_map={'AI': '#1f77b4', 'Human (Sutherland)': '#ff7f0e'},
                    text='Correct Codes'
                )
                fig.update_layout(yaxis_tickformat='.1%', showlegend=False)
                fig.update_traces(texttemplate='%{text} correct', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Error breakdown
                error_data = {
                    'Type': ['Human Errors', 'AI Corrections Made', 'Remaining Issues'],
                    'Count': [
                        sutherland_errors,
                        ai_corrections,
                        max(0, total_reviewed - ai_correct - sutherland_correct)
                    ]
                }
                
                fig = px.pie(
                    values=error_data['Count'],
                    names=error_data['Type'],
                    title="Error Distribution in Reviewed Codes",
                    color_discrete_sequence=['#d62728', '#2ca02c', '#ff7f0e']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Key insights
            st.subheader("💡 Key Insights from Accuracy Comparison")
            
            insights = []
            
            if ai_accuracy > human_accuracy:
                diff_pct = (ai_accuracy - human_accuracy) * 100
                insights.append(f"🎯 **AI outperforms human coding** by {diff_pct:.1f} percentage points")
                insights.append(f"✅ AI made {ai_corrections} corrections where humans were wrong")
            elif human_accuracy > ai_accuracy:
                diff_pct = (human_accuracy - ai_accuracy) * 100
                insights.append(f"👨‍⚕️ **Human coding outperforms AI** by {diff_pct:.1f} percentage points")
                insights.append(f"⚠️ AI needs improvement in {sutherland_errors - ai_corrections} areas")
            else:
                insights.append("🤝 **AI and human coding accuracy are equivalent**")
            
            if ai_corrections > 0:
                insights.append(f"🔧 AI identified and corrected {ai_corrections} human coding errors")
            
            if sutherland_errors > 0:
                error_rate = (sutherland_errors / total_reviewed) * 100
                insights.append(f"📊 Human coding error rate: {error_rate:.1f}% ({sutherland_errors}/{total_reviewed} codes)")
            
            overall_corrected = corrected_accuracy.get('corrected_accuracy', 0)
            insights.append(f"📈 **Combined post-review accuracy: {overall_corrected:.1%}** (using best of AI + Human)")
            
            for insight in insights:
                st.markdown(insight)
        
        # Corrected codes table
        corrected_codes = manual_analysis.get('corrected_codes', {})
        if corrected_codes:
            st.subheader("🔄 Code Corrections Made")
            
            corrections_list = []
            for original_code, correction in corrected_codes.items():
                corrections_list.append({
                    'Original Code': original_code,
                    'Correction': correction,
                    'Type': 'Should not code' if correction == 'should_not_code' else 
                           'Should code' if correction == 'should_code' else 'Substitute'
                })
            
            if corrections_list:
                corrections_df = pd.DataFrame(corrections_list)
                st.dataframe(corrections_df, use_container_width=True)
        
        # Insights and recommendations
        st.subheader("💡 Key Insights")
        
        manual_acc = manual_analysis.get('manual_coding_accuracy', 1.0)
        ai_corrections = manual_analysis.get('ai_corrections', 0)
        sutherland_errors = manual_analysis.get('sutherland_errors', 0)
        
        insights = []
        
        if manual_acc < 0.8:
            insights.append("🔴 Manual coding accuracy is below 80% - significant improvement needed")
        elif manual_acc < 0.9:
            insights.append("🟡 Manual coding accuracy has room for improvement")
        else:
            insights.append("🟢 Manual coding accuracy is good")
        
        if ai_corrections > sutherland_errors:
            insights.append(f"✅ AI made more corrections ({ai_corrections}) than Sutherland errors ({sutherland_errors})")
        else:
            insights.append(f"⚠️ Consider reviewing AI suggestions - AI corrections: {ai_corrections}, Manual errors: {sutherland_errors}")
        
        extra_codes = manual_analysis.get('extra_codes_by_ai', 0)
        if extra_codes > 0:
            insights.append(f"📝 AI provided {extra_codes} additional codes that may be clinically relevant")
        
        for insight in insights:
            st.write(insight)
    
    def create_summary_report(self):
        """Create summary report section"""
        st.header("📋 Summary Report")
        
        if not self.data_loaded:
            return
        
        # Generate text report
        from accuracy_metrics import AccuracyCalculator
        calculator = AccuracyCalculator('sutherland_radiology_results.csv')
        report = calculator.generate_accuracy_report(self.comprehensive_metrics)
        
        # Display report in expandable section
        with st.expander("View Full Report", expanded=True):
            st.text(report)
        
        # Key insights
        st.subheader("🔍 Key Insights")
        
        insights = []
        
        # Chart accuracy improvement
        original_rate = self.comprehensive_metrics['original_accuracy']['chart_level']['complete_match_rate']
        new_rate = self.comprehensive_metrics['post_ai_review']['complete_match_rate']
        improvement = new_rate - original_rate
        
        if improvement > 0:
            insights.append(f"✅ Chart-level accuracy improved by {improvement:.1%} after AI review")
        else:
            insights.append(f"⚠️ Chart-level accuracy did not improve significantly")
        
        # Code importance analysis
        importance = self.comprehensive_metrics['code_importance_analysis']
        important_miss_rate = importance['important_codes']['important_miss_rate']
        unimportant_miss_rate = importance['unimportant_codes']['unimportant_miss_rate']
        
        if important_miss_rate > unimportant_miss_rate:
            insights.append(f"⚠️ AI has higher miss rate for important codes ({important_miss_rate:.1%}) vs unimportant codes ({unimportant_miss_rate:.1%})")
        else:
            insights.append(f"✅ AI performs better on important codes than unimportant codes")
        
        # Most missed codes
        code_frequency = self.analysis_results.get('code_frequency', {})
        if code_frequency:
            top_missed = list(code_frequency.keys())[0]
            top_count = list(code_frequency.values())[0]
            insights.append(f"📊 Most frequently missed code: {top_missed} (missed {top_count} times)")
        
        # Display insights
        for insight in insights:
            st.write(insight)
    
    def run(self):
        """Run the Streamlit dashboard"""
        st.title("🏥 Sutherland Radiology Coding Analysis Dashboard")
        st.markdown("---")
        
        # Sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.selectbox("Choose a section", [
            "Accuracy Overview",
            "Unified Post-Review Accuracy",
            "Code Importance Analysis", 
            "Missed Codes Analysis",
            "AI Review Results",
            "No Match Review Results",
            "Manual Coding Accuracy",
            "Detailed Patient View",
            "Summary Report"
        ])
        
        # Display selected page
        if page == "Accuracy Overview":
            self.create_accuracy_overview()
        elif page == "Unified Post-Review Accuracy":
            self.create_pre_post_review_accuracy()
        elif page == "Code Importance Analysis":
            self.create_code_importance_analysis()
        elif page == "Missed Codes Analysis":
            self.create_missed_codes_analysis()
        elif page == "AI Review Results":
            self.create_ai_review_results()
        elif page == "No Match Review Results":
            self.create_no_match_review_results()
        elif page == "Manual Coding Accuracy":
            self.create_manual_coding_accuracy()
        elif page == "Detailed Patient View":
            self.create_detailed_patient_view()
        elif page == "Summary Report":
            self.create_summary_report()

if __name__ == "__main__":
    dashboard = SutherlandDashboard()
    dashboard.run() 