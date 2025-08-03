import json
import pathlib
from typing import List, Dict, Optional
from collections import Counter, defaultdict

def load_all_previous_metadata(session_id: str, iteration: int) -> List[Dict]:
    """Load metadata from ALL previous iterations"""
    if iteration <= 1:
        return []
    
    all_metadata = []
    session_dir = pathlib.Path(f"generated_images/session_{session_id}")
    
    # Load metadata from all previous iterations (1 to iteration-1)
    for i in range(1, iteration):
        metadata_file = session_dir / f"metadata_iteration_{i:02d}.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                all_metadata.append(metadata)
                print(f"✅ Loaded metadata from iteration {i}")
            except Exception as e:
                print(f"❌ Failed to load metadata from iteration {i}: {e}")
        else:
            print(f"⚠️  No metadata found for iteration {i}")
    
    print(f"📚 Loaded {len(all_metadata)} previous iterations of metadata")
    return all_metadata

def analyze_historical_patterns(session_id: str, current_iteration: int) -> str:
    """Analyze patterns from all previous iterations to provide intelligent insights"""
    if current_iteration <= 2:
        return ""
    
    all_metadata = load_all_previous_metadata(session_id, current_iteration)
    if not all_metadata:
        return ""
    
    # Analyze patterns
    recurring_issues = []
    score_trends = []
    improvements = []
    remaining_issues = []
    
    # Track issues across iterations
    issue_counter = Counter()
    score_history = []
    
    for i, metadata in enumerate(all_metadata, 1):
        scores = metadata.get('evaluation_results', {}).get('scores', {})
        suggestions = metadata.get('evaluation_results', {}).get('suggestions_for_improvement', '').lower()
        metadata_suggestions = metadata.get('evaluation_results', {}).get('metadata_suggestions', '').lower()
        
        # Track scores
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        score_history.append(avg_score)
        score_trends.append(f"Iteration {i}: {avg_score:.1f}")
        
        # Analyze recurring issues
        if "lighting" in suggestions or "lighting" in metadata_suggestions:
            issue_counter["lighting consistency"] += 1
        if "angle" in suggestions or "angle" in metadata_suggestions:
            issue_counter["angle diversity"] += 1
        if "grid" in suggestions or "grid" in metadata_suggestions:
            issue_counter["grid layout"] += 1
        if "background" in suggestions or "background" in metadata_suggestions:
            issue_counter["background issues"] += 1
        if "object" in suggestions or "object" in metadata_suggestions:
            issue_counter["object consistency"] += 1
        if "quality" in suggestions or "quality" in metadata_suggestions:
            issue_counter["image quality"] += 1
        if "completeness" in suggestions or "completeness" in metadata_suggestions:
            issue_counter["view completeness"] += 1
        # Add specific grid-related issue tracking
        if any(grid_term in suggestions.lower() or grid_term in metadata_suggestions.lower() 
               for grid_term in ["4x4", "4x4 grid", "grid layout", "sub-image", "sub-images", "individual", "separated"]):
            issue_counter["4x4 grid structure"] += 1
        if any(single_term in suggestions.lower() or single_term in metadata_suggestions.lower()
               for single_term in ["single image", "one image", "large image", "not grid", "no grid"]):
            issue_counter["single image instead of grid"] += 1
        # Add specific background-related issue tracking
        if any(bg_term in suggestions.lower() or bg_term in metadata_suggestions.lower()
               for bg_term in ["background", "shadow", "texture", "pattern", "surface", "table", "prop", "accessory", "additional object", "environmental"]):
            issue_counter["background/extra elements"] += 1
        if any(clean_term in suggestions.lower() or clean_term in metadata_suggestions.lower()
               for clean_term in ["pure white", "clean background", "no background", "floating", "white space"]):
            issue_counter["clean background requirement"] += 1
        # Add specific object consistency issue tracking
        if any(consistency_term in suggestions.lower() or consistency_term in metadata_suggestions.lower()
               for consistency_term in ["object consistency", "same object", "identical object", "object changed", "different object", "object variation", "object details", "object appearance"]):
            issue_counter["object consistency issues"] += 1
        if any(iteration_term in suggestions.lower() or iteration_term in metadata_suggestions.lower()
               for iteration_term in ["previous iteration", "same as before", "maintain object", "keep object", "object continuity"]):
            issue_counter["iteration consistency"] += 1
    
    # Identify recurring issues (mentioned in 2+ iterations)
    recurring_issues = [issue for issue, count in issue_counter.items() if count >= 2]
    
    # Analyze score trends
    if len(score_history) >= 2:
        if score_history[-1] > score_history[-2]:
            improvements.append("Recent score improvement detected")
        else:
            remaining_issues.append("Scores not improving - need different approach")
    
    # Identify most critical remaining issues
    most_critical_issues = issue_counter.most_common(3)
    
    # Create intelligent analysis
    analysis = f"""
    📊 HISTORICAL PATTERN ANALYSIS:
    
    Score Progression: {' → '.join(score_trends)}
    
    🔍 RECURRING ISSUES (mentioned in multiple iterations):
    {', '.join(recurring_issues) if recurring_issues else 'No recurring issues detected'}
    
    🎯 MOST CRITICAL REMAINING ISSUES:
    {', '.join([f"{issue} ({count} times)" for issue, count in most_critical_issues]) if most_critical_issues else 'No critical issues identified'}
    
    📈 IMPROVEMENTS DETECTED:
    {', '.join(improvements) if improvements else 'No clear improvements detected'}
    
    ⚠️  REMAINING CHALLENGES:
    {', '.join(remaining_issues) if remaining_issues else 'No remaining challenges identified'}
    
    💡 RECOMMENDED FOCUS AREAS:
    {', '.join([issue for issue, count in most_critical_issues[:2]]) if most_critical_issues else 'Focus on general quality improvement'}
    """
    
    return analysis

def create_intelligent_context(historical_data: List[Dict], current_iteration: int) -> str:
    """Create intelligent context based on historical analysis"""
    if not historical_data:
        return ""
    
    # Get the most recent iteration
    latest_metadata = historical_data[-1]
    latest_scores = latest_metadata.get('evaluation_results', {}).get('scores', {})
    latest_suggestions = latest_metadata.get('evaluation_results', {}).get('suggestions_for_improvement', '')
    latest_metadata_suggestions = latest_metadata.get('evaluation_results', {}).get('metadata_suggestions', '')
    
    # Analyze patterns
    analysis = analyze_historical_patterns_from_data(historical_data)
    
    # Create intelligent context
    context = f"""
    🧠 INTELLIGENT HISTORICAL CONTEXT:
    
    {analysis}
    
    🎯 IMMEDIATE FOCUS (from most recent iteration):
    - Latest scores: {latest_scores}
    - Most recent suggestions: {latest_suggestions}
    - Metadata suggestions: {latest_metadata_suggestions}
    
    🚀 STRATEGIC IMPROVEMENT APPROACH:
    - Address the most critical recurring issues first
    - Build on what has worked in previous iterations
    - Avoid repeating failed approaches
    - Focus on the specific issues that haven't been resolved
    """
    
    return context

def analyze_historical_patterns_from_data(historical_data: List[Dict]) -> str:
    """Analyze patterns from historical data"""
    if not historical_data:
        return ""
    
    # Analyze patterns
    issue_counter = Counter()
    score_history = []
    
    for i, metadata in enumerate(historical_data, 1):
        scores = metadata.get('evaluation_results', {}).get('scores', {})
        suggestions = metadata.get('evaluation_results', {}).get('suggestions_for_improvement', '').lower()
        metadata_suggestions = metadata.get('evaluation_results', {}).get('metadata_suggestions', '').lower()
        
        # Track scores
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        score_history.append(avg_score)
        
        # Analyze recurring issues
        if "lighting" in suggestions or "lighting" in metadata_suggestions:
            issue_counter["lighting consistency"] += 1
        if "angle" in suggestions or "angle" in metadata_suggestions:
            issue_counter["angle diversity"] += 1
        if "grid" in suggestions or "grid" in metadata_suggestions:
            issue_counter["grid layout"] += 1
        if "background" in suggestions or "background" in metadata_suggestions:
            issue_counter["background issues"] += 1
        if "object" in suggestions or "object" in metadata_suggestions:
            issue_counter["object consistency"] += 1
        if "quality" in suggestions or "quality" in metadata_suggestions:
            issue_counter["image quality"] += 1
        if "completeness" in suggestions or "completeness" in metadata_suggestions:
            issue_counter["view completeness"] += 1
        # Add specific grid-related issue tracking
        if any(grid_term in suggestions.lower() or grid_term in metadata_suggestions.lower() 
               for grid_term in ["4x4", "4x4 grid", "grid layout", "sub-image", "sub-images", "individual", "separated"]):
            issue_counter["4x4 grid structure"] += 1
        if any(single_term in suggestions.lower() or single_term in metadata_suggestions.lower()
               for single_term in ["single image", "one image", "large image", "not grid", "no grid"]):
            issue_counter["single image instead of grid"] += 1
        # Add specific background-related issue tracking
        if any(bg_term in suggestions.lower() or bg_term in metadata_suggestions.lower()
               for bg_term in ["background", "shadow", "texture", "pattern", "surface", "table", "prop", "accessory", "additional object", "environmental"]):
            issue_counter["background/extra elements"] += 1
        if any(clean_term in suggestions.lower() or clean_term in metadata_suggestions.lower()
               for clean_term in ["pure white", "clean background", "no background", "floating", "white space"]):
            issue_counter["clean background requirement"] += 1
        # Add specific object consistency issue tracking
        if any(consistency_term in suggestions.lower() or consistency_term in metadata_suggestions.lower()
               for consistency_term in ["object consistency", "same object", "identical object", "object changed", "different object", "object variation", "object details", "object appearance"]):
            issue_counter["object consistency issues"] += 1
        if any(iteration_term in suggestions.lower() or iteration_term in metadata_suggestions.lower()
               for iteration_term in ["previous iteration", "same as before", "maintain object", "keep object", "object continuity"]):
            issue_counter["iteration consistency"] += 1
    
    # Identify most critical issues
    most_critical_issues = issue_counter.most_common(3)
    
    # Analyze score trends
    score_trends = [f"Iteration {i+1}: {score:.1f}" for i, score in enumerate(score_history)]
    
    analysis = f"""
    📊 PATTERN ANALYSIS:
    Score Progression: {' → '.join(score_trends)}
    
    🔍 MOST CRITICAL ISSUES:
    {', '.join([f"{issue} ({count} times)" for issue, count in most_critical_issues]) if most_critical_issues else 'No critical issues identified'}
    
    💡 RECOMMENDED FOCUS:
    {', '.join([issue for issue, count in most_critical_issues[:2]]) if most_critical_issues else 'General quality improvement'}
    """
    
    return analysis 