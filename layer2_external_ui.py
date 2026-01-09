#!/usr/bin/env python3
"""
Layer 2A/2B/3 UI Components for External Reference Integration
Renders Streamlit UI for fetching, curating, and integrating external references.
"""

import streamlit as st
from external_reference_fetcher import ExternalReferenceFetcher
from filter_utils import apply_dynamic_filters
from FILTER_LOG_COMPONENT import display_filter_log
import sys


_UI_CACHE_DELETE = "__DELETE__"


def _get_app_module():
    return sys.modules.get("app") or sys.modules.get("__main__")


def _maybe_save_ui_cache(payload: dict):
    m = _get_app_module()
    fn = getattr(m, "_save_ui_cache", None) if m else None
    if callable(fn):
        fn(payload)


def _maybe_invalidate_steps_after(step_num: int):
    m = _get_app_module()
    fn = getattr(m, "_invalidate_steps_after", None) if m else None
    if callable(fn):
        fn(step_num)


def render_layer2a_fetch_external_refs():
    """Render Layer 2A: External Reference Discovery UI."""
    st.divider()
    st.markdown(
        """
<style>
.step_banner {
  padding: 10px 12px;
  border-radius: 8px;
  font-weight: 700;
  border: 1px solid rgba(0,0,0,0.08);
}
.step_2_banner { background: rgba(59,130,246,0.10); border-color: rgba(59,130,246,0.25); }
.step_3_banner { background: rgba(16,185,129,0.10); border-color: rgba(16,185,129,0.25); }
.step_4_banner { background: rgba(168,85,247,0.10); border-color: rgba(168,85,247,0.25); }
.step_5_banner { background: rgba(245,158,11,0.12); border-color: rgba(245,158,11,0.30); }
</style>
""",
        unsafe_allow_html=True,
    )
    st.markdown('<a id="step2a"></a><div class="step_banner step_2_banner">Step 2 — External Reference Discovery (Keywords + Internet Search)</div>', unsafe_allow_html=True)
    st.caption("Find external papers by extracting keywords from the generated article, then searching Semantic Scholar (API-based search; no ChatGPT required).")
    
    article_text = st.session_state.get('generated_article', '')
    citation_map = st.session_state.get('citation_map', {})
    
    if not article_text or not citation_map:
        st.warning("Please generate an article first (Layer 1) before fetching external references.")
        return
    
    # Initialize session state for keywords
    if 'extracted_keywords' not in st.session_state:
        st.session_state.extracted_keywords = []
    if 'selected_keywords' not in st.session_state:
        st.session_state.selected_keywords = []
    
    with st.container(border=True):
        st.markdown('<a id="step-2-1-extract-keywords"></a>', unsafe_allow_html=True)
        st.markdown("### Step 2.1 — Extract Keywords")
    
        # Model selection and parameters
        col1, col2, col3 = st.columns(3)
    
        with col1:
            extraction_model = st.selectbox(
                "LLM Model:",
                ["Ollama Gemma 3 27B (Local)", "Ollama Qwen 3 8B (Local)", "OpenAI GPT-4o-mini"],
                key="extraction_model_select",
                help="Select which LLM to use for keyword extraction"
            )
    
        with col2:
            num_keywords = st.slider(
                "Number of Keywords:",
                min_value=5,
                max_value=20,
                value=10,
                key="num_keywords_slider",
                help="How many keywords to extract from the article"
            )
    
        with col3:
            technical_level = st.slider(
                "Technical Level:",
                min_value=1,
                max_value=5,
                value=3,
                key="technical_level_slider",
                help="1=Generic/broad terms, 5=Highly technical/specific terms"
            )
            tech_labels = ["Generic", "Somewhat Generic", "Balanced", "Technical", "Highly Technical"]
            st.caption(f"Level: {tech_labels[technical_level-1]}")

        col1, col2, col3 = st.columns(3)
        with col1:
            words_per_keyword = st.slider(
                "Words per Keyword (max):",
                min_value=1,
                max_value=6,
                value=3,
                key="words_per_keyword_slider",
                help="Allow multi-word keyphrases (e.g., 'contrastive learning', 'federated averaging')"
            )

        action_col, metric_col = st.columns([2, 1])
        with action_col:
            if st.button("Extract Keywords from Article", use_container_width=True):
                # Map model selection to actual model
                if extraction_model == "Ollama Gemma 3 27B (Local)":
                    model_name = "gemma3:27b"
                    use_openai = False
                elif extraction_model == "Ollama Qwen 3 8B (Local)":
                    model_name = "qwen3:8b"
                    use_openai = False
                else:
                    model_name = "gpt-4o-mini"
                    use_openai = True

                with st.spinner(f"Extracting keywords using {extraction_model}..."):
                    try:
                        fetcher = ExternalReferenceFetcher()
                        keywords = fetcher.extract_keywords_with_llm(
                            article_text,
                            num_keywords=num_keywords,
                            technical_level=technical_level,
                            max_words_per_keyword=words_per_keyword,
                            model=model_name,
                            use_openai=use_openai,
                        )
                        st.session_state.extracted_keywords = keywords
                        st.session_state.selected_keywords = keywords  # Select all by default

                        # Regenerating keywords invalidates previously fetched external refs and all downstream steps.
                        st.session_state.external_references = None
                        st.session_state.external_enhanced_article = None
                        st.session_state.unified_citation_map = None
                        st.session_state.unified_reference_list = None
                        st.session_state.external_refs_integrated = None
                        st.session_state.full_enhanced_article = None

                        _maybe_save_ui_cache({
                            'extracted_keywords': st.session_state.extracted_keywords,
                            'selected_keywords': st.session_state.selected_keywords,
                            'external_references': _UI_CACHE_DELETE,
                            'external_enhanced_article': _UI_CACHE_DELETE,
                            'unified_citation_map': _UI_CACHE_DELETE,
                            'unified_reference_list': _UI_CACHE_DELETE,
                            'external_refs_integrated': _UI_CACHE_DELETE,
                            'full_enhanced_article': _UI_CACHE_DELETE,
                        })
                        _maybe_invalidate_steps_after(2)

                        st.success(f"Extracted {len(keywords)} keywords!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error extracting keywords: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

        with metric_col:
            if st.session_state.extracted_keywords:
                st.metric("Keywords Extracted", len(st.session_state.extracted_keywords))
    
    # Display extracted keywords with multi-select
    if st.session_state.extracted_keywords:
        st.markdown("---")
        st.markdown("**Extracted Keywords (select which to use for search):**")
        
        st.session_state.selected_keywords = st.multiselect(
            "Select keywords for search:",
            options=st.session_state.extracted_keywords,
            default=st.session_state.selected_keywords,
            key="keyword_multiselect",
            help="Select the keywords you want to use for searching papers"
        )
        
        if st.session_state.selected_keywords:
            st.caption(f"Selected keywords: {', '.join(st.session_state.selected_keywords)}")
        else:
            st.warning("Please select at least one keyword to search.")
    
    # Step 2: Search with GPT-4o
    if st.session_state.selected_keywords:
        st.markdown("---")
        with st.container(border=True):
            top_row_left, top_row_right = st.columns([12, 1])
            with top_row_left:
                st.markdown("### Step 2.2 — Search Semantic Scholar (API) *(Optional)*")
                st.caption("💡 This step is optional. You can skip it and go directly to Step 5 (Refinement) below.")

            # Load reference-analysis guidance (years/venues/source buckets) to improve search realism
            import json
            import os
            ref_analysis = None
            ref_analysis_path = "output/references_analysis_summary.json"
            if os.path.exists(ref_analysis_path):
                try:
                    with open(ref_analysis_path, "r") as f:
                        ref_analysis = json.load(f)
                except Exception:
                    ref_analysis = None
            with top_row_right:
                with st.popover("ℹ️", use_container_width=True):
                    st.markdown("**Search method**: Semantic Scholar API (keyword-based).")
                    st.markdown("**LLM used?** No (this step does not call ChatGPT/OpenAI).")
                    if not ref_analysis or not isinstance(ref_analysis, dict):
                        st.warning("No reference analysis summary found. Run the bibliography analysis to populate output/references_analysis_summary.json")
                    else:
                        proc = ref_analysis.get("processing", {}) if isinstance(ref_analysis, dict) else {}
                        refs_text = ref_analysis.get("references_text", {}) if isinstance(ref_analysis, dict) else {}
                        years = ref_analysis.get("cited_years", {}) if isinstance(ref_analysis, dict) else {}

                        st.markdown("**From `output/references_analysis_summary.json`**")
                        st.write(f"Papers OK / total: {proc.get('papers_ok', 'N/A')} / {proc.get('papers_total', 'N/A')}")
                        st.write(f"Total references extracted: {proc.get('total_reference_entries_extracted', 'N/A')}")
                        st.write(
                            "References section words (avg/p50/p90): "
                            f"{refs_text.get('ref_words_avg', 'N/A')} / {refs_text.get('ref_words_p50', 'N/A')} / {refs_text.get('ref_words_p90', 'N/A')}"
                        )
                        st.write(
                            "Cited-year percentiles (p25/p50/p75/p90): "
                            f"{years.get('p25', 'N/A')} / {years.get('p50', 'N/A')} / {years.get('p75', 'N/A')} / {years.get('p90', 'N/A')}"
                        )

            default_year_start = 2020
            default_year_end = 2025
            if ref_analysis and isinstance(ref_analysis, dict):
                cited_years = ref_analysis.get("cited_years", {})
                try:
                    p25 = int(cited_years.get("p25", default_year_start))
                    p90 = int(cited_years.get("p90", default_year_end))
                    default_year_start = max(2015, min(2025, p25))
                    default_year_end = max(default_year_start, min(2025, p90))
                except Exception:
                    pass
            
            col1, col2 = st.columns(2)
            with col1:
                num_external_refs = st.slider(
                    "Number of Papers:",
                    min_value=5,
                    max_value=200,
                    value=100,
                    step=5,
                    key="num_external_refs_2a",
                    help="Maximum number of papers to fetch (increased to 200 for better filtering)"
                )
            
            with col2:
                year_start = st.number_input(
                    "Year Range Start:",
                    min_value=2015,
                    max_value=2025,
                    value=default_year_start,
                    key="year_start_2a"
                )
                year_end = st.number_input(
                    "Year Range End:",
                    min_value=2015,
                    max_value=2025,
                    value=default_year_end,
                    key="year_end_2a"
                )
            
            # Dynamic filtering options
            with st.expander("🎛️ Advanced Filtering Options", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    min_relevance = st.slider(
                        "Min Relevance Score",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.3,
                        step=0.05,
                        help="Filter out papers below this relevance score"
                    )
                
                with col2:
                    require_abstract = st.checkbox(
                        "Require Abstract",
                        value=True,
                        help="Only include papers with available abstracts"
                    )
                
                with col3:
                    exclude_generic = st.checkbox(
                        "Exclude Generic Titles",
                        value=True,
                        help="Filter out papers with generic titles (e.g., 'Advanced Concepts', 'Review')"
                    )
                
                # Additional filtering options
                col1, col2 = st.columns(2)
                
                with col1:
                    min_year = st.number_input(
                        "Min Publication Year",
                        min_value=2000,
                        max_value=2025,
                        value=2018,
                        step=1,
                        help="Only include papers from this year or later"
                    )
                
                with col2:
                    venue_types = st.multiselect(
                        "Venue Types",
                        ["Conference", "Journal", "Workshop", "Preprint"],
                        default=["Conference", "Journal"],
                        help="Select which types of venues to include"
                    )
            
            if st.button("Search Semantic Scholar", type="primary", use_container_width=True):
                with st.spinner("Searching Semantic Scholar... (this may take 5-20 seconds)"):
                    try:
                        # Show what we're searching for
                        search_query = ', '.join(st.session_state.selected_keywords)
                        st.info(f"Searching for papers about: {search_query}")
                        
                        fetcher = ExternalReferenceFetcher()
                        external_refs = fetcher.search_internet_with_gpt4o(
                            keywords=st.session_state.selected_keywords,
                            num_papers=num_external_refs,
                            year_range=(year_start, year_end),
                            analysis_guidance=ref_analysis,
                        )

                        if external_refs:
                            if len(external_refs) < num_external_refs:
                                st.warning(
                                    f"Only found {len(external_refs)} papers (requested {num_external_refs}). "
                                    "Try broadening keywords or widening the year range."
                                )
                            # Apply dynamic filters
                            st.info("🔄 Applying dynamic filters to search results...")
                            
                            filtered_refs, filter_log = apply_dynamic_filters(
                                references=external_refs,
                                min_relevance=min_relevance,
                                require_abstract=require_abstract,
                                exclude_generic=exclude_generic,
                                min_year=min_year,
                                venue_types=venue_types
                            )
                            
                            # Display filter log
                            display_filter_log(filter_log, search_query)
                            
                            # Use filtered results
                            external_refs = filtered_refs
                            
                            # Show result summary
                            if filter_log['final_count'] > 0:
                                # Assign citation numbers
                                max_local_citation = max(citation_map.values()) if citation_map else 0
                                for i, ref in enumerate(external_refs):
                                    ref.citation_number = max_local_citation + i + 1

                                st.session_state.external_references = external_refs
                                st.success(f"✅ Found {filter_log['final_count']} high-quality papers from {filter_log['original_count']} total results!")
                            else:
                                st.error(
                                    f"❌ **Zero results:** Found {filter_log['original_count']} papers initially, "
                                    f"but all were filtered out.\n\n"
                                    f"**Suggestions:**\n"
                                    f"- Lower the minimum relevance score\n"
                                    f"- Disable 'Require Abstract'\n"
                                    f"- Broaden your keywords or year range\n"
                                    f"- Include more venue types"
                                )
                                # Don't save empty results - keeps next steps hidden
                                return

                            # Save to cache (only if we have results)
                            ext_refs_serialized = [ref.to_dict() for ref in external_refs]
                            _maybe_save_ui_cache({
                                'answer_result': st.session_state.get('answer_result'),
                                'generated_article': st.session_state.get('generated_article'),
                                'base_generated_article': st.session_state.get('base_generated_article'),
                                'article_sources': st.session_state.get('article_sources'),
                                'citation_map': st.session_state.get('citation_map'),
                                'citation_stats': st.session_state.get('citation_stats'),
                                'reference_list': st.session_state.get('reference_list'),
                                'article_topic_stored': st.session_state.get('article_topic_stored'),
                                'refined_article': st.session_state.get('refined_article'),
                                'refinement_report': st.session_state.get('refinement_report'),
                                'extracted_keywords': st.session_state.get('extracted_keywords'),
                                'selected_keywords': st.session_state.get('selected_keywords'),
                                'external_references': ext_refs_serialized,
                            })

                            # New external refs invalidate downstream steps (integration + rebuild + refinement)
                            _maybe_invalidate_steps_after(2)

                            st.rerun()
                        else:
                            st.warning("No relevant papers found. Try adjusting keywords or year range.")
                    except Exception as e:
                        st.error(f"Error searching internet: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
    
    # Display fetched references
    if st.session_state.get('external_references'):
        st.markdown("---")
        st.markdown("### Fetched External References")
        st.caption("Review and deselect any irrelevant papers before integration.")
        
        external_refs = st.session_state.external_references
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Fetched", len(external_refs))
        with col2:
            selected_count = sum(1 for ref in external_refs if ref.selected)
            st.metric("Selected", selected_count)
        with col3:
            avg_score = sum(ref.relevance_score for ref in external_refs) / len(external_refs)
            st.metric("Avg Relevance", f"{avg_score:.2f}")
        
        # Reference table with selection
        st.markdown("---")
        for i, ref in enumerate(external_refs):
            with st.expander(f"[{ref.citation_number}] {ref.title} ({ref.year}) - Relevance: {ref.relevance_score:.2f}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Authors:** {', '.join(ref.authors[:3])}" + (" et al." if len(ref.authors) > 3 else ""))
                    st.markdown(f"**Venue:** {ref.venue}")
                    if getattr(ref, 'journal', None):
                        st.markdown(f"**Journal:** {ref.journal}")
                    if getattr(ref, 'publisher', None):
                        st.markdown(f"**Publisher:** {ref.publisher}")
                    abstract_text = (ref.abstract or "")
                    abstract_preview = abstract_text[:300] + ("..." if len(abstract_text) > 300 else "")
                    st.markdown(f"**Abstract:** {abstract_preview}" if abstract_preview else "**Abstract:** (not available)")
                    
                    # Clickable links for verification
                    if ref.doi:
                        doi_url = f"https://doi.org/{ref.doi}" if not ref.doi.startswith('http') else ref.doi
                        st.markdown(f"**DOI:** [{ref.doi}]({doi_url})")
                    if ref.url:
                        st.markdown(f"**URL:** [{ref.url[:50]}...]({ref.url})" if len(ref.url) > 50 else f"**URL:** [{ref.url}]({ref.url})")
                    if not ref.doi and not ref.url:
                        # Generate search link
                        search_query = ref.title.replace(' ', '+')
                        st.markdown(f"**Search:** [Google Scholar](https://scholar.google.com/scholar?q={search_query})")
                
                with col2:
                    # Selection checkbox
                    new_selected = st.checkbox(
                        "Include",
                        value=ref.selected,
                        key=f"ext_ref_select_{i}"
                    )
                    if new_selected != ref.selected:
                        ref.selected = new_selected


def render_layer2b_integrate_external_refs():
    """Render Layer 2B: External Reference Integration UI.
    
    Fresh implementation based on documentation.
    Implements 8 phases: Pre-validation, LLM config, integration, token tracking,
    polishing, IEEE renumbering, validation, and finalization.
    """
    import os
    import time
    
    st.divider()
    st.markdown('<a id="step2b"></a><div class="step_banner step_3_banner">Step 3 — Integrate External References into Article</div>', unsafe_allow_html=True)
    st.caption("Intelligently integrate selected external references using LLM-powered citation placement.")
    
    # ========================================================================
    # PHASE 1: PRE-INTEGRATION VALIDATION
    # ========================================================================
    
    external_refs = st.session_state.get('external_references')
    if not external_refs:
        st.info("⚠️ Please fetch external references first (Step 2).")
        return
    
    selected_refs = [ref for ref in external_refs if ref.selected]
    if not selected_refs:
        st.warning("⚠️ No external references selected. Please select at least one reference in Step 2.")
        return
    
    article_text = st.session_state.get('generated_article', '')
    if not article_text:
        st.error("❌ No article found. Please generate an article first (Step 1).")
        return
    
    citation_map = st.session_state.get('citation_map', {})
    
    st.success(f"✅ Ready to integrate {len(selected_refs)} external references into your article.")
    
    # ========================================================================
    # UI: LLM SELECTION AND CONFIGURATION
    # ========================================================================
    
    col1, col2 = st.columns(2)
    
    with col1:
        integration_llm = st.selectbox(
            "Select LLM for Integration:",
            ["OpenAI GPT", "Claude (Anthropic)", "Ollama Gemma 3 27B (Local)"],
            key="integration_llm_choice",
            help="LLM to use for intelligent citation placement"
        )
    
    with col2:
        if integration_llm == "OpenAI GPT":
            integration_model = st.selectbox(
                "Select Model:",
                ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                index=1,  # Default to gpt-4o-mini (cheaper)
                key="integration_model_choice",
                help="gpt-4o-mini recommended for cost savings"
            )
        elif integration_llm == "Ollama Gemma 3 27B (Local)":
            integration_model = "gemma3:27b"
        else:
            integration_model = "claude-3-5-sonnet-20241022"
    
    # API key validation
    if integration_llm == "OpenAI GPT":
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            st.success(f"✓ OpenAI API Key detected (starts with: {api_key[:10]}...)")
        else:
            st.error("✗ OpenAI API Key not found!")
            st.warning("Start Streamlit with: ./run_streamlit.sh")
            return
    
    # Polish option
    st.markdown("---")
    polish_with_integration = st.checkbox(
        "✨ Also polish article during integration",
        value=False,  # Default to False to save costs
        help="Polish article for better flow after integration (adds ~50% to cost)"
    )
    
    # Progress displays
    st.markdown("### 📋 Integration Progress")
    log_display = st.empty()
    
    if st.session_state.get('integration_logs'):
        log_display.code("\n".join(st.session_state['integration_logs'][-20:]), language="text")
    else:
        log_display.code("Waiting for integration to start...\nClick 'Integrate External References' to begin.", language="text")
    
    # Token usage display
    with st.expander("💰 Token Usage & Cost", expanded=True):
        token_info_placeholder = st.empty()
        if st.session_state.get('integration_tokens'):
            tokens = st.session_state['integration_tokens']
            token_info_placeholder.markdown(f"""
            **Token Usage:**
            - Input: {tokens['input_tokens']:,} tokens
            - Output: {tokens['output_tokens']:,} tokens
            - **Total Cost: ${tokens['total_cost']:.4f} USD**
            - Processing Time: {tokens.get('processing_time', 0):.1f}s
            """)
        else:
            token_info_placeholder.markdown("**Waiting for integration...**")
    
    # ========================================================================
    # INTEGRATION BUTTON HANDLER
    # ========================================================================
    
    if st.button("🚀 Integrate External References", type="primary", use_container_width=True):
        from smart_citation_integratorator import SmartCitationIntegrator
        from config import InsufficientQuotaError
        
        # Initialize tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        if 'integration_logs' not in st.session_state:
            st.session_state.integration_logs = []
        if 'integration_tokens' not in st.session_state:
            st.session_state.integration_tokens = {"input_tokens": 0, "output_tokens": 0, "total_cost": 0.0}
        
        logs = st.session_state.integration_logs
        token_usage = st.session_state.integration_tokens
        
        # Reset tracking
        logs.clear()
        token_usage["input_tokens"] = 0
        token_usage["output_tokens"] = 0
        token_usage["total_cost"] = 0.0
        
        start_time = time.time()
        
        def update_log():
            """Update log display."""
            recent_logs = logs[-20:] if len(logs) > 20 else logs
            log_display.code("\n".join(recent_logs), language="text")
            st.session_state.integration_logs = logs.copy()
        
        def update_token_info():
            """Update token usage display."""
            processing_time = time.time() - start_time
            token_info_placeholder.markdown(f"""
            **Token Usage:**
            - Input: {token_usage['input_tokens']:,} tokens
            - Output: {token_usage['output_tokens']:,} tokens
            - **Total Cost: ${token_usage['total_cost']:.4f} USD**
            - Processing Time: {processing_time:.1f}s
            """)
            st.session_state.integration_tokens = {
                "input_tokens": token_usage["input_tokens"],
                "output_tokens": token_usage["output_tokens"],
                "total_cost": token_usage["total_cost"],
                "processing_time": processing_time
            }
        
        try:
            logs.append("="*60)
            logs.append("INTEGRATION STARTED")
            logs.append("="*60)
            logs.append(f"Selected references: {len(selected_refs)}")
            logs.append(f"LLM: {integration_llm} ({integration_model})")
            logs.append(f"Polish enabled: {polish_with_integration}")
            logs.append("")
            update_log()
            
            # ================================================================
            # PHASE 2: LLM CONFIGURATION
            # ================================================================
            
            logs.append("[Phase 2] Configuring LLM pricing...")
            
            if integration_llm == "OpenAI GPT":
                llm_type = "openai"
                if integration_model == "gpt-4o":
                    input_cost_per_1k = 0.005
                    output_cost_per_1k = 0.015
                elif integration_model == "gpt-4o-mini":
                    input_cost_per_1k = 0.00015
                    output_cost_per_1k = 0.0006
                else:  # gpt-4-turbo
                    input_cost_per_1k = 0.01
                    output_cost_per_1k = 0.03
            elif integration_llm == "Claude (Anthropic)":
                llm_type = "claude"
                input_cost_per_1k = 0.003
                output_cost_per_1k = 0.015
            else:  # Ollama
                llm_type = "ollama"
                input_cost_per_1k = 0
                output_cost_per_1k = 0
            
            logs.append(f"  Input: ${input_cost_per_1k}/1K tokens")
            logs.append(f"  Output: ${output_cost_per_1k}/1K tokens")
            logs.append("")
            update_log()
            
            # ================================================================
            # PHASE 3: SMART CITATION INTEGRATION
            # ================================================================
            
            logs.append("[Phase 3] Starting smart citation integration...")
            update_log()
            
            status_text.text("Processing article sections...")
            integrator = SmartCitationIntegrator()
            
            def section_progress(message):
                """Callback for section progress."""
                logs.append(f"  {message}")
                update_log()
                update_token_info()
            
            enhanced_article, usage = integrator.integrate_citations_smart(
                article_text=article_text,
                references=selected_refs,
                llm_type=llm_type,
                model=integration_model,
                return_usage=True,
                progress_callback=section_progress
            )
            
            logs.append("")
            logs.append("✅ Integration complete!")
            logs.append("")
            update_log()
            
            # ================================================================
            # PHASE 4: TOKEN TRACKING
            # ================================================================
            
            logs.append("[Phase 4] Calculating token usage...")
            
            if usage and llm_type == "openai":
                token_usage["input_tokens"] = usage.get("prompt_tokens", 0)
                token_usage["output_tokens"] = usage.get("completion_tokens", 0)
                token_usage["total_cost"] = (
                    (token_usage["input_tokens"] * input_cost_per_1k / 1000) +
                    (token_usage["output_tokens"] * output_cost_per_1k / 1000)
                )
                logs.append(f"  Input tokens: {token_usage['input_tokens']:,}")
                logs.append(f"  Output tokens: {token_usage['output_tokens']:,}")
                logs.append(f"  Cost: ${token_usage['total_cost']:.4f}")
            else:
                # Estimate for non-OpenAI
                estimated_input = len(article_text) // 4 + len(selected_refs) * 100
                estimated_output = len(enhanced_article) // 4
                token_usage["input_tokens"] = estimated_input
                token_usage["output_tokens"] = estimated_output
                token_usage["total_cost"] = (
                    (estimated_input * input_cost_per_1k / 1000) +
                    (estimated_output * output_cost_per_1k / 1000)
                )
                logs.append(f"  Estimated tokens: {estimated_input + estimated_output:,}")
            
            logs.append("")
            update_log()
            update_token_info()
            
            # ================================================================
            # PHASE 5: OPTIONAL POLISHING
            # ================================================================
            
            if polish_with_integration:
                logs.append("[Phase 5] Polishing article...")
                status_text.text("Polishing article for better flow...")
                update_log()
                
                try:
                    from article_refiner import OpenAIRefiner
                    refiner = OpenAIRefiner()
                    
                    polished_article = refiner.refine_article(
                        article_text=enhanced_article,
                        llm_model="gpt-4o",
                        preserve_citations=True
                    )
                    
                    # Estimate polish cost
                    polish_input = len(enhanced_article) // 4
                    polish_output = len(polished_article) // 4
                    polish_cost = (
                        (polish_input * input_cost_per_1k / 1000) +
                        (polish_output * output_cost_per_1k / 1000)
                    )
                    
                    token_usage["input_tokens"] += polish_input
                    token_usage["output_tokens"] += polish_output
                    token_usage["total_cost"] += polish_cost
                    
                    enhanced_article = polished_article
                    logs.append("  ✅ Polish complete")
                    logs.append(f"  Additional cost: ${polish_cost:.4f}")
                    
                except Exception as e:
                    logs.append(f"  ⚠️ Polish failed: {str(e)}")
                    st.warning("⚠️ Polishing failed, but integration succeeded.")
                
                logs.append("")
                update_log()
                update_token_info()
            
            # ================================================================
            # PHASE 8: FINALIZATION
            # ================================================================
            
            logs.append("[Phase 8] Finalizing...")
            
            # Store enhanced article
            st.session_state.external_enhanced_article = enhanced_article
            st.session_state.integration_complete = True
            
            # Save to cache
            ext_refs_serialized = None
            if st.session_state.get('external_references'):
                ext_refs_serialized = [ref.to_dict() if hasattr(ref, 'to_dict') else ref 
                                       for ref in st.session_state.external_references]
            
            _maybe_save_ui_cache({
                'answer_result': st.session_state.get('answer_result'),
                'generated_article': st.session_state.get('generated_article'),
                'base_generated_article': st.session_state.get('base_generated_article'),
                'article_sources': st.session_state.get('article_sources'),
                'citation_map': st.session_state.get('citation_map'),
                'citation_stats': st.session_state.get('citation_stats'),
                'reference_list': st.session_state.get('reference_list'),
                'article_topic_stored': st.session_state.get('article_topic_stored'),
                'refined_article': st.session_state.get('refined_article'),
                'refinement_report': st.session_state.get('refinement_report'),
                'extracted_keywords': st.session_state.get('extracted_keywords'),
                'selected_keywords': st.session_state.get('selected_keywords'),
                'external_references': ext_refs_serialized,
                'external_enhanced_article': st.session_state.external_enhanced_article,
                'integration_logs': st.session_state.integration_logs,
                'integration_tokens': st.session_state.integration_tokens,
                'integration_complete': True,
            })
            
            # Calculate final stats
            end_time = time.time()
            total_time = end_time - start_time
            
            logs.append("  ✅ Enhanced article stored")
            logs.append("  ✅ Saved to cache")
            logs.append("")
            logs.append("="*60)
            logs.append("INTEGRATION COMPLETE")
            logs.append("="*60)
            logs.append(f"Total time: {total_time:.1f}s")
            logs.append(f"Total cost: ${token_usage['total_cost']:.4f}")
            logs.append(f"Citations added: Check Step 4 for details")
            logs.append("="*60)
            
            update_log()
            update_token_info()
            
            # Update UI
            progress_bar.progress(1.0)
            status_text.text("✅ Integration complete!")
            
            st.success(f"🎉 Integration complete in {total_time:.1f}s! Cost: ${token_usage['total_cost']:.4f}")
            st.info("📍 Scroll down to **Step 4** to see your enhanced article with external citations.")
            
        except InsufficientQuotaError as e:
            progress_bar.progress(0)
            st.error(f"❌ OpenAI quota exceeded: {str(e)}")
            st.info("💡 Try using gpt-4o-mini (cheaper) or Ollama (free).")
            
        except Exception as e:
            import traceback
            progress_bar.progress(0)
            st.error(f"❌ Integration error: {str(e)}")
            
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())
            
            logs.append("")
            logs.append(f"❌ ERROR: {str(e)}")
            update_log()


def render_layer3_rebuild_references():
    """Render Layer 3: Rebuild References and Display Enhanced Article.
    
    Fresh implementation based on documentation.
    Implements Phase 6 (IEEE Renumbering) and displays the enhanced article.
    """
    enhanced_article = st.session_state.get('external_enhanced_article')
    
    if not enhanced_article:
        return
    
    st.divider()
    st.markdown('<a id="step4"></a><div class="step_banner step_4_banner">Step 4 — Enhanced Article (with External References)</div>', unsafe_allow_html=True)
    st.caption("Your article with integrated external references and IEEE-compliant sequential numbering.")
    
    # Get required data
    citation_map = st.session_state.get('citation_map', {})
    external_refs_raw = st.session_state.get('external_references', [])
    
    # Convert external refs to proper format
    from external_reference_fetcher import ExternalReference
    external_refs = []
    for item in external_refs_raw:
        if isinstance(item, ExternalReference):
            external_refs.append(item)
        elif isinstance(item, dict):
            try:
                external_refs.append(ExternalReference.from_dict(item))
            except Exception:
                continue
    
    # ========================================================================
    # DISPLAY INTEGRATION STATISTICS
    # ========================================================================
    
    integration_stats = st.session_state.get('citation_integration_stats', {})
    if integration_stats:
        st.markdown("### 📊 Integration Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Original Citations",
                integration_stats.get('original_count', 0),
                help="Citations in the original article"
            )
        
        with col2:
            st.metric(
                "External Available",
                integration_stats.get('external_available', 0),
                help="External references selected for integration"
            )
        
        with col3:
            st.metric(
                "External Integrated",
                integration_stats.get('external_integrated', 0),
                help="External citations actually added to text"
            )
        
        with col4:
            rate = integration_stats.get('integration_rate', 0)
            st.metric(
                "Integration Rate",
                f"{rate:.1f}%",
                delta=f"{'✅' if rate >= 60 else '⚠️'}",
                delta_color="normal" if rate >= 60 else "inverse",
                help="Percentage of external references integrated (target: ≥60%)"
            )
        
        # Show which external refs were not integrated
        not_integrated = integration_stats.get('external_not_integrated', [])
        if not_integrated:
            with st.expander(f"⚠️ {len(not_integrated)} external references not integrated", expanded=False):
                for ref_num in not_integrated:
                    # Find the reference
                    ref = next((r for r in external_refs if r.citation_number == ref_num), None)
                    if ref:
                        st.markdown(f"**[{ref_num}]** {ref.title[:80]}... ({ref.year})")
        
        st.markdown("---")
    
    # ========================================================================
    # PHASE 6: IEEE RENUMBERING
    # ========================================================================
    
    import re
    from citation_manager import CitationManager
    from citation_formatter import CitationFormatter
    
    cm = CitationManager()
    formatter = CitationFormatter()
    
    # Extract all citations from enhanced article
    cited_numbers = cm.extract_citations_from_article(enhanced_article)
    
    # Build unified reference list with sequential IEEE numbering
    all_refs = []
    old_to_new_number = {}
    cited_refs = []  # (old_num, type, data)
    
    # Map citation numbers to filenames
    number_to_filename = {num: filename for filename, num in citation_map.items()}
    
    # Collect cited references (local + external)
    for num in sorted(cited_numbers):
        if num in number_to_filename:
            # Local reference
            cited_refs.append((num, 'local', number_to_filename[num]))
        else:
            # External reference
            for ext_ref in external_refs:
                if ext_ref.citation_number == num and ext_ref.selected:
                    cited_refs.append((num, 'external', ext_ref))
                    break
    
    # Renumber sequentially and build reference list
    for new_num, (old_num, ref_type, ref_data) in enumerate(cited_refs, start=1):
        old_to_new_number[old_num] = new_num
        
        if ref_type == 'local':
            filename = ref_data
            ref_text = formatter.format_reference(filename, new_num)
            all_refs.append(ref_text)
        else:  # external
            ext_ref = ref_data
            ref_text = ext_ref.to_ieee_format()
            # Replace old number with new number
            ref_text = ref_text.replace(f"[{old_num}]", f"[{new_num}]", 1)
            all_refs.append(ref_text)
    
    # Update citation numbers in article text
    for old_num, new_num in sorted(old_to_new_number.items(), reverse=True):
        enhanced_article = enhanced_article.replace(f"[{old_num}]", f"[TEMP{new_num}]")
    
    for new_num in range(1, len(old_to_new_number) + 1):
        enhanced_article = enhanced_article.replace(f"[TEMP{new_num}]", f"[{new_num}]")
    
    # ========================================================================
    # DISPLAY ENHANCED ARTICLE
    # ========================================================================
    
    # Extract title
    extracted_title, article_body = cm.extract_title(enhanced_article)
    
    # Display title
    if extracted_title and extracted_title != "Research Article":
        st.title(extracted_title)
    else:
        st.title(st.session_state.get('article_topic_stored', 'Enhanced Article'))
    
    # Display article body
    st.markdown(article_body, unsafe_allow_html=True)
    
    # Add LaTeX validation button
    with st.expander("🔧 Validate & Fix LaTeX", expanded=False):
        st.write("Fix common LaTeX formatting issues in the article:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Validate LaTeX", help="Check for LaTeX formatting issues"):
                # Import validation function
                try:
                    from app import _validate_and_fix_latex_delimiters
                    import re
                    
                    # Check for common LaTeX issues
                    issues = []
                    
                    # Check for specific patterns in the article
                    if "\\left$" in enhanced_article:
                        issues.append("Found \\left$ (should be \\left()")
                    if "\\right$" in enhanced_article:
                        issues.append("Found \\right$ (should be \\right)")
                    if "$\\left(" in enhanced_article:
                        issues.append("Found $\\left( (should be \\left()")
                    if "\\right)$" in enhanced_article:
                        issues.append("Found \\right)$ (should be \\right)")
                    if "\\left\\frac" in enhanced_article:
                        issues.append("Found \\left\\frac (should be \\left(\\frac)")
                    
                    # Check for mismatched delimiters
                    left_count = enhanced_article.count("\\left")
                    right_count = enhanced_article.count("\\right")
                    if left_count != right_count:
                        issues.append(f"Mismatched delimiters: {left_count} \\left but {right_count} \\right")
                    
                    # Check for the specific equation pattern
                    if "q\\left(" in enhanced_article and "\\right)" in enhanced_article:
                        # Extract the equation to check its structure
                        equation_match = re.search(r'q\\left\(.*?\\right\)', enhanced_article, re.DOTALL)
                        if equation_match:
                            equation = equation_match.group()
                            st.code(equation)
                            st.write("Found equation with \\left and \\right delimiters")
                    
                    if issues:
                        st.warning(f"Found {len(issues)} LaTeX issues:")
                        for issue in issues:
                            st.write(f"• {issue}")
                    else:
                        st.success("✅ No common LaTeX issues found!")
                        
                except ImportError:
                    st.error("❌ LaTeX validation not available")
        
        with col2:
            if st.button("🔧 Apply LaTeX Fixes", help="Fix all LaTeX formatting issues"):
                try:
                    from app import _validate_and_fix_latex_delimiters
                    import re
                    
                    # First apply the standard fixes
                    fixed_article = _validate_and_fix_latex_delimiters(enhanced_article)
                    
                    # Apply additional fixes for specific issues
                    # Fix 1: Ensure \left and \right are properly matched
                    # Look for \left( without matching \right) or vice versa
                    fixed_article = re.sub(r'\\left\(', r'\\left(', fixed_article)
                    fixed_article = re.sub(r'\\right\)', r'\\right)', fixed_article)
                    
                    # Fix 2: Fix any remaining \left or \right without proper delimiters
                    # This is a more aggressive fix for the specific equation issue
                    patterns_to_fix = [
                        (r'\\left\s*\(', r'\\left('),
                        (r'\\left\s*\[', r'\\left['),
                        (r'\\left\s*\{', r'\\left\\{'),
                        (r'\\right\s*\)', r'\\right)'),
                        (r'\\right\s*\]', r'\\right]'),
                        (r'\\right\s*\}', r'\\right\\}'),
                    ]
                    
                    for pattern, replacement in patterns_to_fix:
                        fixed_article = re.sub(pattern, replacement, fixed_article)
                    
                    # Show what was fixed
                    changes = []
                    if enhanced_article != fixed_article:
                        changes.append("Fixed LaTeX delimiter formatting")
                        # Count specific fixes
                        if enhanced_article.count("\\left") != fixed_article.count("\\left"):
                            changes.append(f"Fixed \\left commands ({enhanced_article.count('\\left')} → {fixed_article.count('\\left')})")
                        if enhanced_article.count("\\right") != fixed_article.count("\\right"):
                            changes.append(f"Fixed \\right commands ({enhanced_article.count('\\right')} → {fixed_article.count('\\right')})")
                    else:
                        changes.append("No changes needed - LaTeX already properly formatted")
                    
                    # Update session state
                    st.session_state.external_enhanced_article = fixed_article
                    
                    # Show success message
                    st.success("✅ LaTeX fixes applied!")
                    st.info("🔄 Article updated with LaTeX fixes")
                    
                    if changes:
                        st.write("Changes made:")
                        for change in changes:
                            st.write(f"• {change}")
                    
                    # Force a rerun to refresh the display
                    st.rerun()
                    
                except ImportError:
                    st.error("❌ LaTeX fixing not available")
        
        st.markdown("---")
        st.write("**Common LaTeX fixes:**")
        st.code("""
\\left$ → \\left(
\\right$ → \\right)
$\\left( → \\left(
\\right)$ → \\right)
\\left\\frac → \\left(\\frac
        """)
    
    # ========================================================================
    # DISPLAY REFERENCES
    # ========================================================================
    
    st.markdown("---")
    st.markdown("## References")
    
    local_count = sum(1 for _, ref_type, _ in cited_refs if ref_type == 'local')
    external_count = sum(1 for _, ref_type, _ in cited_refs if ref_type == 'external')
    
    st.caption(f"Total: {len(all_refs)} references ({local_count} local + {external_count} external)")
    
    # Display references with indicators
    for i, ref in enumerate(all_refs, start=1):
        # Check if external
        is_external = any(
            old_num for old_num, ref_type, _ in cited_refs
            if ref_type == 'external' and old_to_new_number.get(old_num) == i
        )
        
        # Check if external reference was actually cited in text
        is_cited = False
        old_num = None
        for on, rt, _ in cited_refs:
            if rt == 'external' and old_to_new_number.get(on) == i:
                old_num = on
                is_cited = old_num not in integration_stats.get('external_not_integrated', [])
                break
        
        if is_external:
            if is_cited:
                st.markdown(f"🌐 {ref}")
            else:
                st.markdown(f"⚪ {ref} <small style='color:#666;'>(not cited in text)</small>", unsafe_allow_html=True)
        else:
            st.markdown(f"📚 {ref}")
    
    # ========================================================================
    # DOWNLOAD OPTIONS
    # ========================================================================
    
    st.markdown("---")
    st.markdown("### 📥 Download Options")
    
    # Create full article with references
    full_article = enhanced_article + "\n\n## References\n\n" + "\n".join(all_refs)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📄 Download Markdown",
            data=full_article,
            file_name="enhanced_article_with_external_refs.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    with col2:
        # Generate PDF for the enhanced article with external references
        try:
            # Import PDF generation function
            from app import generate_article_pdf
            import hashlib
            from datetime import datetime
            
            # Create a signature to detect changes
            article_sig_src = full_article + "|" + str(len(all_refs))
            article_sig = hashlib.sha256(article_sig_src.encode("utf-8", errors="ignore")).hexdigest()
            
            # Generate or get cached PDF
            if 'enhanced_article_pdf_bytes' not in st.session_state or st.session_state.get('enhanced_article_pdf_sig') != article_sig:
                st.session_state.enhanced_article_pdf_bytes = generate_article_pdf(
                    full_article,
                    extracted_title if extracted_title != "Research Article" else st.session_state.get('article_topic_stored', 'Enhanced Article'),
                    {},  # No citation map needed for final article
                    []   # No sources needed for final article
                )
                st.session_state.enhanced_article_pdf_sig = article_sig
            
            pdf_bytes = st.session_state.enhanced_article_pdf_bytes
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name=f"enhanced_article_with_external_refs_{timestamp}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except ImportError:
            st.error("❌ PDF generation not available")
        except Exception as e:
            st.error(f"❌ PDF generation failed: {str(e)}")
    
    # Store for next steps
    st.session_state.full_enhanced_article = full_article
    st.session_state.unified_reference_list = all_refs
    st.session_state.unified_citation_map = old_to_new_number
    st.session_state.external_refs_integrated = external_refs
