#!/usr/bin/env python3
"""
Filter log component for displaying filtering results
"""

import streamlit as st
import pandas as pd
from datetime import datetime


def display_filter_log(filter_log: dict, search_query: str):
    """Display a comprehensive filter log in the UI."""
    
    with st.expander("📊 Filter Log", expanded=True):
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Original Papers", filter_log['original_count'])
        
        with col2:
            st.metric("After Filters", filter_log['final_count'])
        
        with col3:
            retention_rate = filter_log['retained_percentage']
            st.metric("Retention Rate", f"{retention_rate:.1f}%")
        
        with col4:
            filtered_out = filter_log['original_count'] - filter_log['final_count']
            st.metric("Filtered Out", filtered_out)
        
        # Detailed breakdown
        st.markdown("---")
        st.markdown("### Filter Breakdown")
        
        # Create breakdown data
        breakdown_data = []
        filters_applied = filter_log['filters_applied']
        
        filter_descriptions = {
            'min_relevance': f"Below relevance threshold",
            'no_abstract': "No abstract available",
            'generic_title': "Generic title",
            'too_old': f"Before min year",
            'wrong_venue_type': "Wrong venue type"
        }
        
        for filter_name, count in filters_applied.items():
            if count > 0:
                breakdown_data.append({
                    'Filter': filter_descriptions.get(filter_name, filter_name),
                    'Papers Removed': count,
                    'Percentage': (count / filter_log['original_count'] * 100)
                })
        
        if breakdown_data:
            df = pd.DataFrame(breakdown_data)
            st.dataframe(df, use_container_width=True)
        
        # Search info
        st.markdown("---")
        st.markdown("### Search Information")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Query:** {search_query}")
            st.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        with col2:
            if filter_log['final_count'] < 10:
                st.warning("⚠️ Low number of results. Consider relaxing filters.")
            elif filter_log['final_count'] > 50:
                st.info("ℹ️ High number of results. Consider tightening filters.")
            else:
                st.success("✅ Good number of results for integration.")
