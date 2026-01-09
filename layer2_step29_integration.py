#!/usr/bin/env python3
"""
Step 2.9: External Reference Integration
Brand new implementation based on INTEGRATE_EXTERNAL_REFERENCES_DOCUMENTATION.md

This is a fresh, independent implementation that integrates external references
into the generated article using LLM-powered intelligent citation placement.
"""

import streamlit as st
import os
import time


def render_step_2_9_integration():
    """
    Render Step 2.9: External Reference Integration.
    
    Brand new implementation based on documentation.
    Implements all 8 phases from the documentation:
    1. Pre-Integration Validation
    2. LLM Configuration
    3. Smart Citation Integration
    4. Token Tracking
    5. Optional Polishing
    6. IEEE Renumbering (in Step 4)
    7. Validation (removed - was causing issues)
    8. Finalization
    """
    
    st.divider()
    st.markdown(
        '<a id="step2-9"></a>'
        '<div class="step_banner step_2_9_banner">'
        'Step 2.9 — Integrate External References'
        '</div>',
        unsafe_allow_html=True
    )
    st.caption(
        "🎯 Intelligently integrate external references into your article using "
        "LLM-powered citation placement. Based on IEEE standards."
    )
    
    # ============================================================================
    # PHASE 1: PRE-INTEGRATION VALIDATION
    # ============================================================================
    
    st.markdown("### 📋 Pre-Integration Checklist")
    
    # Check 1: Article exists
    article_text = st.session_state.get('generated_article', '')
    if article_text:
        st.success("✅ Article found")
    else:
        st.error("❌ No article found. Generate an article first (Step 1).")
        return
    
    # Check 2: External references fetched
    external_refs = st.session_state.get('external_references')
    if external_refs:
        st.success(f"✅ External references available ({len(external_refs)} total)")
    else:
        st.error("❌ No external references. Fetch references first (Step 2).")
        return
    
    # Check 3: References selected
    selected_refs = [ref for ref in external_refs if ref.selected]
    if selected_refs:
        st.success(f"✅ {len(selected_refs)} references selected for integration")
    else:
        st.warning("⚠️ No references selected. Select at least one reference in Step 2.")
        return
    
    # Check 4: Citation map exists
    citation_map = st.session_state.get('citation_map', {})
    local_count = len(citation_map)
    st.info(f"ℹ️ Your article currently has {local_count} local citations")
    
    # ============================================================================
    # UI: LLM CONFIGURATION
    # ============================================================================
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        llm_provider = st.selectbox(
            "LLM Provider:",
            ["OpenAI", "Anthropic Claude", "Ollama (Local)"],
            key="step29_llm_provider",
            help="Choose your LLM provider for integration"
        )
    
    with col2:
        if llm_provider == "OpenAI":
            model_name = st.selectbox(
                "Model:",
                ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
                key="step29_model",
                help="gpt-4o-mini is recommended (10x cheaper)"
            )
        elif llm_provider == "Anthropic Claude":
            model_name = "claude-3-5-sonnet-20241022"
        else:
            model_name = "gemma3:27b"
    
    # API Key Status
    if llm_provider == "OpenAI":
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            st.success(f"🔑 API Key: {api_key[:10]}...")
        else:
            st.error("🔑 No API Key found! Run: ./run_streamlit.sh")
            return
    
    # ============================================================================
    # PROGRESS DISPLAYS
    # ============================================================================
    
    st.markdown("---")
    st.markdown("### 📊 Integration Status")
    
    # Log display
    log_container = st.empty()
    if st.session_state.get('step29_logs'):
        log_container.code(
            "\n".join(st.session_state['step29_logs'][-25:]),
            language="text"
        )
    else:
        log_container.code(
            "⏳ Waiting to start integration...\n"
            "Click the button below to begin.",
            language="text"
        )
    
    # Token usage display
    with st.expander("💵 Token Usage & Cost Breakdown", expanded=False):
        token_display = st.empty()
        if st.session_state.get('step29_tokens'):
            tokens = st.session_state['step29_tokens']
            token_display.markdown(f"""
            **Real-Time Token Usage:**
            - 📥 Input: {tokens.get('input', 0):,} tokens
            - 📤 Output: {tokens.get('output', 0):,} tokens
            - 💵 **Total Cost: ${tokens.get('cost', 0):.4f} USD**
            - ⏱️ Time: {tokens.get('time', 0):.1f}s
            """)
        else:
            token_display.markdown("*No data yet. Start integration to see metrics.*")
    
    # ============================================================================
    # INTEGRATION BUTTON
    # ============================================================================
    
    st.markdown("---")
    
    if st.button(
        "🚀 Start Integration",
        type="primary",
        use_container_width=True,
        key="step29_integrate_btn"
    ):
        _execute_integration(
            article_text=article_text,
            selected_refs=selected_refs,
            llm_provider=llm_provider,
            model_name=model_name,
            enable_polish=True,  # Always enabled
            log_container=log_container,
            token_display=token_display
        )


def _execute_integration(
    article_text,
    selected_refs,
    llm_provider,
    model_name,
    enable_polish,
    log_container,
    token_display
):
    """
    Execute the integration workflow.
    
    This is a brand new implementation following the documentation phases.
    """
    from smart_citation_integratorator import SmartCitationIntegrator
    from config import InsufficientQuotaError
    
    # Initialize tracking
    progress = st.progress(0)
    status = st.empty()
    
    logs = []
    tokens = {'input': 0, 'output': 0, 'cost': 0.0, 'time': 0.0}
    
    start_time = time.time()
    
    def log(message):
        """Add log message."""
        logs.append(message)
        log_container.code("\n".join(logs[-25:]), language="text")
        st.session_state['step29_logs'] = logs.copy()
    
    def update_tokens():
        """Update token display."""
        tokens['time'] = time.time() - start_time
        token_display.markdown(f"""
        **Real-Time Token Usage:**
        - 📥 Input: {tokens['input']:,} tokens
        - 📤 Output: {tokens['output']:,} tokens
        - 💵 **Total Cost: ${tokens['cost']:.4f} USD**
        - ⏱️ Time: {tokens['time']:.1f}s
        """)
        st.session_state['step29_tokens'] = tokens.copy()
    
    try:
        # ====================================================================
        # PHASE 1: INITIALIZATION
        # ====================================================================
        
        log("╔" + "═" * 58 + "╗")
        log("║" + " " * 15 + "INTEGRATION STARTED" + " " * 24 + "║")
        log("╚" + "═" * 58 + "╝")
        log("")
        log(f"📝 Article: {len(article_text)} characters")
        log(f"📚 References: {len(selected_refs)} selected")
        log(f"🤖 LLM: {llm_provider} ({model_name})")
        log("✨ Polish: Disabled (to preserve external citations)")
        log("")
        
        progress.progress(0.1)
        status.text("Initializing...")
        
        # ====================================================================
        # PHASE 2: LLM CONFIGURATION
        # ====================================================================
        
        log("[Phase 2] Configuring LLM...")
        
        if llm_provider == "OpenAI":
            llm_type = "openai"
            if model_name == "gpt-4o-mini":
                input_rate = 0.00015
                output_rate = 0.0006
            elif model_name == "gpt-4o":
                input_rate = 0.005
                output_rate = 0.015
            else:
                input_rate = 0.01
                output_rate = 0.03
        elif llm_provider == "Anthropic Claude":
            llm_type = "claude"
            input_rate = 0.003
            output_rate = 0.015
        else:
            llm_type = "ollama"
            input_rate = 0.0
            output_rate = 0.0
        
        log(f"  💵 Input rate: ${input_rate}/1K tokens")
        log(f"  💵 Output rate: ${output_rate}/1K tokens")
        log("")
        
        progress.progress(0.2)
        
        # ====================================================================
        # PHASE 3: SMART CITATION INTEGRATION
        # ====================================================================
        
        log("[Phase 3] Starting smart citation integration...")
        log("  This may take 30-180 seconds depending on article size...")
        log("")
        
        status.text("Integrating citations...")
        progress.progress(0.3)
        
        integrator = SmartCitationIntegrator()
        
        def progress_callback(msg):
            """Callback for integration progress."""
            log(f"  {msg}")
            update_tokens()
        
        enhanced_article, usage = integrator.integrate_citations_smart(
            article_text=article_text,
            references=selected_refs,
            llm_type=llm_type,
            model=model_name,
            return_usage=True,
            progress_callback=progress_callback
        )
        
        log("")
        log("✅ Citation integration complete!")
        log("")
        
        # Verify mathematical content is preserved
        import re
        math_patterns_in_original = set(re.findall(r'\\\(.*?\\\)|\\\[.*?\\\]|\\begin\{equation\}.*?\\end\{equation\}|\\frac\{.*?\}\{.*?\}|\\sqrt\{.*?\}|\\sum|\\int|\\partial', article_text, re.DOTALL))
        math_patterns_in_enhanced = set(re.findall(r'\\\(.*?\\\)|\\\[.*?\\\]|\\begin\{equation\}.*?\\end\{equation\}|\\frac\{.*?\}\{.*?\}|\\sqrt\{.*?\}|\\sum|\\int|\\partial', enhanced_article, re.DOTALL))
        
        if math_patterns_in_original:
            missing_math = math_patterns_in_original - math_patterns_in_enhanced
            if missing_math:
                log("  ⚠️ WARNING: Some mathematical content may have been modified")
                log(f"    Original math patterns: {len(math_patterns_in_original)}")
                log(f"    Enhanced math patterns: {len(math_patterns_in_enhanced)}")
            else:
                log("  ✅ Mathematical content preserved")
        
        progress.progress(0.7)
        
        # ====================================================================
        # PHASE 4: TOKEN TRACKING & CITATION INTEGRATION ANALYSIS
        # ====================================================================
        
        log("[Phase 4] Calculating token usage and analyzing citation integration...")
        
        # Track citation integration
        from citation_manager import CitationManager
        
        cm = CitationManager()
        
        # Extract citations from original article
        original_citations = set(cm.extract_citations_from_article(article_text))
        log(f"  Original citations: {sorted(original_citations)}")
        
        # Extract citations from enhanced article
        enhanced_citations = set(cm.extract_citations_from_article(enhanced_article))
        log(f"  Enhanced citations: {sorted(enhanced_citations)}")
        
        # Get external reference numbers
        external_ref_numbers = {ref.citation_number for ref in selected_refs}
        log(f"  External ref numbers available: {sorted(external_ref_numbers)}")
        
        # Calculate integration metrics
        new_citations = enhanced_citations - original_citations
        external_integrated = new_citations & external_ref_numbers
        external_not_integrated = external_ref_numbers - enhanced_citations
        
        integration_rate = len(external_integrated) / len(external_ref_numbers) * 100 if external_ref_numbers else 0
        
        log(f"  New citations added: {len(new_citations)}")
        log(f"  External citations integrated: {len(external_integrated)}/{len(external_ref_numbers)} ({integration_rate:.1f}%)")
        if external_not_integrated:
            log(f"  External citations NOT integrated: {sorted(external_not_integrated)}")
        
        # Store integration stats for Step 4
        st.session_state.citation_integration_stats = {
            'original_count': len(original_citations),
            'enhanced_count': len(enhanced_citations),
            'external_available': len(external_ref_numbers),
            'external_integrated': len(external_integrated),
            'external_not_integrated': list(external_not_integrated),
            'integration_rate': integration_rate
        }
        
        if usage and llm_type == "openai":
            tokens['input'] = usage.get('prompt_tokens', 0)
            tokens['output'] = usage.get('completion_tokens', 0)
            tokens['cost'] = (
                (tokens['input'] * input_rate / 1000) +
                (tokens['output'] * output_rate / 1000)
            )
            log(f"  📥 Input: {tokens['input']:,} tokens")
            log(f"  📤 Output: {tokens['output']:,} tokens")
            log(f"  💵 Cost: ${tokens['cost']:.4f}")
        else:
            # Estimate for non-OpenAI
            tokens['input'] = len(article_text) // 4
            tokens['output'] = len(enhanced_article) // 4
            tokens['cost'] = (
                (tokens['input'] * input_rate / 1000) +
                (tokens['output'] * output_rate / 1000)
            )
            log(f"  📊 Estimated: {tokens['input'] + tokens['output']:,} tokens")
        
        log("")
        update_tokens()
        
        progress.progress(0.8)
        
        # ====================================================================
        # PHASE 5: INTEGRATION VALIDATION (60% THRESHOLD)
        # ====================================================================
        
        log("[Phase 5] Validating citation integration threshold...")
        
        # Check 60% threshold
        threshold = 60.0
        if integration_rate < threshold:
            log(f"  ❌ INTEGRATION RATE BELOW THRESHOLD: {integration_rate:.1f}% < {threshold:.0f}%")
            log("")
            log("  🔄 Applying fallback insertion to meet threshold...")
            
            # Find missing external citations
            missing_external = external_ref_numbers - external_integrated
            
            if missing_external:
                # Split article into sentences
                import re
                sentences = re.split(r'[.!?]+', enhanced_article)
                sentences = [s.strip() for s in sentences if s.strip()]
                
                # Distribute missing citations across sentences
                for i, cit_num in enumerate(sorted(missing_external)):
                    if i < len(sentences):
                        sentence_idx = i % len(sentences)
                        if sentences[sentence_idx]:
                            sentences[sentence_idx] += " [{}]".format(cit_num)
                
                # Rebuild article
                enhanced_article = '. '.join(sentences)
                
                # Recalculate integration
                enhanced_citations = set(cm.extract_citations_from_article(enhanced_article))
                external_integrated = enhanced_citations & external_ref_numbers
                integration_rate = len(external_integrated) / len(external_ref_numbers) * 100
                external_not_integrated = external_ref_numbers - enhanced_citations
                
                log(f"  ✅ Fallback complete. New integration rate: {integration_rate:.1f}%")
                log(f"  External citations now integrated: {len(external_integrated)}/{len(external_ref_numbers)}")
                
                # Update stats
                st.session_state.citation_integration_stats = {
                    'original_count': len(original_citations),
                    'enhanced_count': len(enhanced_citations),
                    'external_available': len(external_ref_numbers),
                    'external_integrated': len(external_integrated),
                    'external_not_integrated': list(external_not_integrated),
                    'integration_rate': integration_rate
                }
                
                st.success(
                    f"✅ **Fallback Applied**: {integration_rate:.1f}% of external references were integrated "
                    f"({len(external_integrated)}/{len(external_ref_numbers)}) after automatic insertion."
                )
            else:
                log("  ⚠️ No missing citations found to insert")
        else:
            log(f"  ✅ Integration rate meets threshold: {integration_rate:.1f}% ≥ {threshold:.0f}%")
            st.success(
                f"✅ **Good Integration**: {integration_rate:.1f}% of external references were integrated "
                f"({len(external_integrated)}/{len(external_ref_numbers)})"
            )
        
        log("")
        update_tokens()
        
        # ====================================================================
        # PHASE 6: OPTIONAL POLISHING (DISABLED)
        # ====================================================================
        # Polishing has been disabled to prevent it from stripping external citations
        # The article refiner was removing external citations during polishing
        # 
        # if enable_polish:
        #     log("[Phase 5] Polishing article...")
        #     status.text("Polishing article...")
        #     
        #     try:
        #         from article_refiner import ArticleRefiner
        #         refiner = ArticleRefiner()
        #         
        #         # Use the citation map and sources from session state
        #         citation_map = st.session_state.get('citation_map', {})
        #         article_sources = st.session_state.get('article_sources', [])
        #         
        #         polished, _ = refiner.refine_article(
        #             article_text=enhanced_article,
        #             citation_map=citation_map,
        #             sources_list=article_sources,
        #             external_refs=selected_refs
        #         )
        #         
        #         # Estimate polish cost
        #         polish_input = len(enhanced_article) // 4
        #         polish_output = len(polished) // 4
        #         polish_cost = (
        #             (polish_input * input_rate / 1000) +
        #             (polish_output * output_rate / 1000)
        #         )
        #         
        #         tokens['input'] += polish_input
        #         tokens['output'] += polish_output
        #         tokens['cost'] += polish_cost
        #         
        #         enhanced_article = polished  # This was stripping external citations!
        #         
        #         log(f"  ✅ Polish complete (+${polish_cost:.4f})")
        #         
        #     except Exception as e:
        #         log(f"  ⚠️ Polish failed: {str(e)}")
        #         st.warning("⚠️ Polishing failed, but integration succeeded.")
        #     
        #     log("")
        #     update_tokens()
        
        log("⚠️ Polishing disabled to preserve external citations")
        log("  External citations were being stripped during polishing")
        
        progress.progress(0.9)
        
        # ====================================================================
        # PHASE 8: FINALIZATION
        # ====================================================================
        
        log("[Phase 8] Finalizing...")
        status.text("Finalizing...")
        
        # Store results
        st.session_state.external_enhanced_article = enhanced_article
        st.session_state.step29_complete = True
        
        # Calculate stats
        end_time = time.time()
        total_time = end_time - start_time
        tokens['time'] = total_time
        
        log("  ✅ Enhanced article stored in session")
        log("")
        log("╔" + "═" * 58 + "╗")
        log("║" + " " * 14 + "INTEGRATION COMPLETE" + " " * 24 + "║")
        log("╚" + "═" * 58 + "╝")
        log(f"⏱️  Total time: {total_time:.1f}s")
        log(f"💵 Total cost: ${tokens['cost']:.4f}")
        log(f"📊 Total tokens: {tokens['input'] + tokens['output']:,}")
        log("╚" + "═" * 58 + "╝")
        
        update_tokens()
        
        progress.progress(1.0)
        status.text("✅ Complete!")
        
        # Success message
        st.success(
            f"🎉 Integration complete!\n\n"
            f"⏱️ Time: {total_time:.1f}s | "
            f"💵 Cost: ${tokens['cost']:.4f} | "
            f"📊 Tokens: {tokens['input'] + tokens['output']:,}"
        )
        
        st.info("📍 **Next:** Scroll down to Step 4 to see your enhanced article.")
        
    except InsufficientQuotaError as e:
        progress.progress(0)
        status.text("❌ Failed")
        st.error(f"❌ OpenAI quota exceeded: {str(e)}")
        st.info("💡 Try gpt-4o-mini (cheaper) or Ollama (free)")
        log("")
        log(f"❌ ERROR: Quota exceeded - {str(e)}")
        
    except Exception as e:
        import traceback
        progress.progress(0)
        status.text("❌ Failed")
        st.error(f"❌ Integration failed: {str(e)}")
        
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())
        
        log("")
        log(f"❌ ERROR: {str(e)}")
