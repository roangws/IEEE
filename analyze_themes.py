#!/usr/bin/env python3
"""
Theme Analysis Tool
Analyzes the collection to identify research themes and suggest questions.
"""

import argparse
from query import QueryEngine
import json


def analyze_collection(collection_name="academic_papers_100"):
    """Analyze collection to identify themes and suggest questions."""
    
    print("="*70)
    print("THEMATIC ANALYSIS OF RESEARCH COLLECTION")
    print("="*70)
    print(f"\nAnalyzing collection: {collection_name}")
    print("This will take a few minutes...\n")
    
    engine = QueryEngine(collection_name=collection_name)
    
    # Exploratory questions to understand the collection
    exploratory_questions = [
        "What are the main research topics and themes covered in these papers?",
        "What methodologies and approaches are most commonly used?",
        "What are the key application domains or industries discussed?",
        "What technologies, tools, or frameworks are frequently mentioned?",
        "What are the main challenges or research problems being addressed?"
    ]
    
    themes = {}
    
    for i, question in enumerate(exploratory_questions, 1):
        print(f"\n[{i}/{len(exploratory_questions)}] Analyzing: {question}")
        print("-"*70)
        
        result = engine.search_and_answer(question, top_k=20)
        themes[question] = result['answer']
        
        # Print summary
        print(result['answer'][:500] + "...\n")
    
    # Generate comprehensive report
    print("\n" + "="*70)
    print("COMPREHENSIVE THEMATIC ANALYSIS REPORT")
    print("="*70)
    
    for question, answer in themes.items():
        print(f"\n## {question}")
        print("-"*70)
        print(answer)
        print()
    
    # Suggest research questions
    print("\n" + "="*70)
    print("SUGGESTED RESEARCH QUESTIONS TO EXPLORE")
    print("="*70)
    
    suggested_questions = [
        # Methodological questions
        "What are the most effective evaluation metrics used across these studies?",
        "How do different approaches compare in terms of performance and efficiency?",
        "What are the limitations of current methodologies?",
        
        # Application questions
        "What real-world applications have been successfully implemented?",
        "What industries or domains show the most promise for future applications?",
        "What are the scalability challenges in practical deployments?",
        
        # Technical questions
        "What are the emerging trends in algorithm design?",
        "How are machine learning techniques being integrated?",
        "What role does data quality play in the outcomes?",
        
        # Gap identification questions
        "What research areas are underexplored or have limited coverage?",
        "What contradictions or debates exist in the literature?",
        "What future research directions are suggested by the authors?",
        
        # Comparative questions
        "How have approaches evolved over time?",
        "What are the trade-offs between different methods?",
        "Which techniques work best for specific use cases?",
        
        # Impact questions
        "What are the practical implications of these findings?",
        "What ethical considerations are discussed?",
        "What are the economic or societal impacts mentioned?"
    ]
    
    print("\n### Methodological Questions:")
    for q in suggested_questions[:3]:
        print(f"  • {q}")
    
    print("\n### Application Questions:")
    for q in suggested_questions[3:6]:
        print(f"  • {q}")
    
    print("\n### Technical Questions:")
    for q in suggested_questions[6:9]:
        print(f"  • {q}")
    
    print("\n### Gap Identification Questions:")
    for q in suggested_questions[9:12]:
        print(f"  • {q}")
    
    print("\n### Comparative Questions:")
    for q in suggested_questions[12:15]:
        print(f"  • {q}")
    
    print("\n### Impact Questions:")
    for q in suggested_questions[15:]:
        print(f"  • {q}")
    
    # Save to file
    report = {
        "collection": collection_name,
        "thematic_analysis": themes,
        "suggested_questions": suggested_questions
    }
    
    with open("theme_analysis_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "="*70)
    print("REPORT SAVED")
    print("="*70)
    print("Full report saved to: theme_analysis_report.json")
    print("\nYou can now use these questions in the Q&A tab to explore your collection!")
    
    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze research collection themes"
    )
    parser.add_argument(
        '--collection',
        type=str,
        default='academic_papers_100',
        help='Qdrant collection name'
    )
    
    args = parser.parse_args()
    
    analyze_collection(args.collection)


if __name__ == '__main__':
    main()
