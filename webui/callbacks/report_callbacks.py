"""
Report-related callbacks for TradingAgents WebUI
Enhanced with symbol-based pagination
"""

from dash import Input, Output, ctx, html, ALL, dash, dcc
import dash_bootstrap_components as dbc
from webui.utils.state import app_state
from webui.components.ui import render_researcher_debate, render_risk_debate
from webui.utils.report_validator import validate_reports_for_ui


def create_symbol_button(symbol, index, is_active=False):
    """Create a symbol button for pagination"""
    return dbc.Button(
        symbol,
        id={"type": "symbol-btn", "index": index, "component": "reports"},
        color="primary" if is_active else "outline-primary",
        size="sm",
        className=f"symbol-btn {'active' if is_active else ''}",
    )


def create_markdown_content(content, default_message="No content available yet."):
    """Create a markdown component with enhanced styling"""
    if not content or content.strip() == "":
        content = default_message
    
    return dcc.Markdown(
        content,
        mathjax=True,
        highlight_config={"theme": "dark"},
        dangerously_allow_html=False,
        className='enhanced-markdown-content',
        style={
            "background": "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)",
            "border-radius": "8px",
            "padding": "1.5rem",
            "border": "1px solid rgba(51, 65, 85, 0.3)",
            "min-height": "400px",
            "color": "#E2E8F0",
            "line-height": "1.6"
        }
    )


def register_report_callbacks(app):
    """Register all report-related callbacks including symbol pagination"""

    @app.callback(
        Output("report-pagination-container", "children"),
        [Input("app-store", "data"),
         Input("refresh-interval", "n_intervals")]
    )
    def update_report_symbol_pagination(store_data, n_intervals):
        """Update the symbol pagination buttons for reports"""
        if not app_state.symbol_states:
            return html.Div("No symbols available", 
                          className="text-muted text-center",
                          style={"padding": "10px"})
        
        symbols = list(app_state.symbol_states.keys())
        current_symbol = app_state.current_symbol
        
        # Find active symbol index
        active_index = 0
        if current_symbol and current_symbol in symbols:
            active_index = symbols.index(current_symbol)
        
        buttons = []
        for i, symbol in enumerate(symbols):
            is_active = i == active_index
            buttons.append(create_symbol_button(symbol, i, is_active))
        
        if len(symbols) > 1:
            # Add navigation info
            nav_info = html.Div([
                html.I(className="fas fa-info-circle me-2"),
                f"Showing {len(symbols)} symbols"
            ], className="text-muted small text-center mt-2")
            
            return html.Div([
                dbc.ButtonGroup(buttons, className="d-flex flex-wrap justify-content-center"),
                nav_info
            ], className="symbol-pagination-wrapper")
        else:
            return dbc.ButtonGroup(buttons, className="d-flex justify-content-center")

    @app.callback(
        [Output("report-pagination", "active_page", allow_duplicate=True),
         Output("chart-pagination", "active_page", allow_duplicate=True),
         Output("report-pagination-container", "children", allow_duplicate=True)],
        [Input({"type": "symbol-btn", "index": ALL, "component": "reports"}, "n_clicks")],
        prevent_initial_call=True
    )
    def handle_report_symbol_click(symbol_clicks):
        """Handle symbol button clicks for reports with immediate visual feedback"""
        if not any(symbol_clicks) or not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update
        
        # Find which button was clicked
        button_id = ctx.triggered[0]["prop_id"]
        if "symbol-btn" in button_id:
            # Extract index from the button ID
            import json
            button_data = json.loads(button_id.split('.')[0])
            clicked_index = button_data["index"]
            
            # Update current symbol
            symbols = list(app_state.symbol_states.keys())
            if 0 <= clicked_index < len(symbols):
                app_state.current_symbol = symbols[clicked_index]
                page_number = clicked_index + 1
                
                # ⚡ IMMEDIATE BUTTON UPDATE - No waiting for refresh!
                buttons = []
                for i, symbol in enumerate(symbols):
                    is_active = i == clicked_index  # Active state based on click
                    buttons.append(create_symbol_button(symbol, i, is_active))
                
                if len(symbols) > 1:
                    # Add navigation info
                    nav_info = html.Div([
                        html.I(className="fas fa-info-circle me-2"),
                        f"Showing {len(symbols)} symbols"
                    ], className="text-muted small text-center mt-2")
                    
                    button_container = html.Div([
                        dbc.ButtonGroup(buttons, className="d-flex flex-wrap justify-content-center"),
                        nav_info
                    ], className="symbol-pagination-wrapper")
                else:
                    button_container = dbc.ButtonGroup(buttons, className="d-flex justify-content-center")
                
                return page_number, page_number, button_container
        
        return dash.no_update, dash.no_update, dash.no_update

    @app.callback(
        Output("researcher-debate-tab-content", "children"),
        [Input("report-pagination", "active_page"),
         Input("medium-refresh-interval", "n_intervals")]
    )
    def update_researcher_debate(active_page, n_intervals):
        """Update the researcher debate tab"""
        if not app_state.symbol_states or not active_page:
            return create_markdown_content("", "No researcher debate available yet.")

        # Safeguard against accessing invalid page index (e.g., after page refresh)
        symbols_list = list(app_state.symbol_states.keys())
        if active_page > len(symbols_list):
            return create_markdown_content("", "Page index out of range. Please refresh or restart analysis.")

        symbol = symbols_list[active_page - 1]
        
        # Use the proper render_researcher_debate function from ui.py
        from webui.components.ui import render_researcher_debate
        debate_html = render_researcher_debate(symbol)
        
        # Return an iframe to display the chat-like interface
        return html.Iframe(
            srcDoc=debate_html,
            style={
                "width": "100%", 
                "height": "500px", 
                "border": "none",
                "border-radius": "8px",
                "background": "#1E293B"
            },
            className="debate-iframe"
        )

    @app.callback(
        Output("risk-debate-tab-content", "children"),
        [Input("report-pagination", "active_page"),
         Input("medium-refresh-interval", "n_intervals")]
    )
    def update_risk_debate(active_page, n_intervals):
        """Update the risk debate tab"""
        if not app_state.symbol_states or not active_page:
            return create_markdown_content("", "No risk debate available yet.")

        # Safeguard against accessing invalid page index (e.g., after page refresh)
        symbols_list = list(app_state.symbol_states.keys())
        if active_page > len(symbols_list):
            return create_markdown_content("", "Page index out of range. Please refresh or restart analysis.")

        symbol = symbols_list[active_page - 1]
        
        # Use the proper render_risk_debate function from ui.py
        from webui.components.ui import render_risk_debate
        debate_html = render_risk_debate(symbol)
        
        # Return an iframe to display the chat-like interface
        return html.Iframe(
            srcDoc=debate_html,
            style={
                "width": "100%", 
                "height": "500px", 
                "border": "none",
                "border-radius": "8px",
                "background": "#1E293B"
            },
            className="debate-iframe"
        )

    @app.callback(
        [Output("market-analysis-tab-content", "children"),
         Output("social-sentiment-tab-content", "children"),
         Output("news-analysis-tab-content", "children"),
         Output("fundamentals-analysis-tab-content", "children"),
         Output("macro-analysis-tab-content", "children"),
         Output("research-manager-tab-content", "children"),
         Output("trader-plan-tab-content", "children"),
         Output("final-decision-tab-content", "children")],
        [Input("report-pagination", "active_page"),
         Input("medium-refresh-interval", "n_intervals")]
    )
    def update_tabs_content(active_page, n_intervals):
        """Update the content of all tabs with validation to ensure complete reports"""
        # print(f"[REPORTS] Called with active_page={active_page}, symbol_states={list(app_state.symbol_states.keys()) if app_state.symbol_states else []}")
        
        if not app_state.symbol_states or not active_page:
            # print(f"[REPORTS] No symbol states or no active page, returning default content")
            return [create_markdown_content("", "No analysis available yet.")] * 8
        
        # Safeguard against accessing invalid page index (e.g., after page refresh)
        symbols_list = list(app_state.symbol_states.keys())
        if active_page > len(symbols_list):
            return [create_markdown_content("", "Page index out of range. Please refresh or restart analysis.")] * 8
        
        symbol = symbols_list[active_page - 1]
        # print(f"[REPORTS] Selected symbol: {symbol} (page {active_page})")
        state = app_state.get_state(symbol)
        
        if not state:
            return [create_markdown_content("", "No data for this symbol.")] * 8
            
        reports = state["current_reports"]
        agent_statuses = state["agent_statuses"]
        
        # 🛡️ VALIDATION: Only show complete reports in UI
        # For analysts marked as "completed", validate reports are actually complete
        analyst_reports = {
            "market_report": reports.get("market_report"),
            "sentiment_report": reports.get("sentiment_report"), 
            "news_report": reports.get("news_report"),
            "fundamentals_report": reports.get("fundamentals_report"),
            "macro_report": reports.get("macro_report")
        }
        
        # Check which analysts are completed
        analyst_status_map = {
            "market_report": agent_statuses.get("Market Analyst"),
            "sentiment_report": agent_statuses.get("Social Analyst"),
            "news_report": agent_statuses.get("News Analyst"), 
            "fundamentals_report": agent_statuses.get("Fundamentals Analyst"),
            "macro_report": agent_statuses.get("Macro Analyst")
        }
        
        # 🛡️ PRIORITY: Analyst status takes precedence over content validation
        # If analyst is completed, always show the report regardless of content validation
        validated_reports = {}
        
        for report_type, content in analyst_reports.items():
            status = analyst_status_map.get(report_type)
            
            if status == "completed" and content:
                # Analyst is done - show the final report
                validated_reports[report_type] = content
            elif status == "in_progress":
                validated_reports[report_type] = f"🔄 {report_type.replace('_', ' ').title()} - Analysis in progress..."
            elif status == "pending":
                validated_reports[report_type] = f"⏳ {report_type.replace('_', ' ').title()} - Waiting to start..."
            elif content:
                # Analyst status unknown but we have content - validate it
                content_validated = validate_reports_for_ui({report_type: content})
                validated_reports[report_type] = content_validated[report_type]
            else:
                validated_reports[report_type] = f"No {report_type.replace('_', ' ').title()} available yet."
        
        # Get final validated reports or defaults
        market_report = validated_reports.get("market_report", "No market analysis available yet.")
        sentiment_report = validated_reports.get("sentiment_report", "No sentiment analysis available yet.")
        news_report = validated_reports.get("news_report", "No news analysis available yet.")
        fundamentals_report = validated_reports.get("fundamentals_report", "No fundamentals analysis available yet.")
        macro_report = validated_reports.get("macro_report", "No macro analysis available yet.")
        
        # Research team reports (no validation needed - these come as complete chunks)
        research_manager_report = reports.get("research_manager_report") or "No research manager decision available yet."
        trader_report = reports.get("trader_investment_plan") or "No trader report available yet."
        
        # Final Decision tab shows the Portfolio Manager Decision
        portfolio_report = reports.get("final_trade_decision") or "No final decision available yet."
        
        return (
            create_markdown_content(market_report),
            create_markdown_content(sentiment_report),
            create_markdown_content(news_report),
            create_markdown_content(fundamentals_report),
            create_markdown_content(macro_report),
            create_markdown_content(research_manager_report),
            create_markdown_content(trader_report),
            create_markdown_content(portfolio_report)
        )

    @app.callback(
        Output("decision-summary", "children"),
        [Input("report-pagination", "active_page"),
         Input("medium-refresh-interval", "n_intervals")]
    )
    def update_decision_summary(active_page, n_intervals):
        """Update the decision summary"""
        if not app_state.symbol_states or not active_page:
            return "Analysis not complete yet."

        # Safeguard against accessing invalid page index (e.g., after page refresh)
        symbols_list = list(app_state.symbol_states.keys())
        if active_page > len(symbols_list):
            return "Page index out of range. Please refresh or restart analysis."

        symbol = symbols_list[active_page - 1]
        state = app_state.get_state(symbol)

        if not state:
            return "No data for this symbol."

        reports = state["current_reports"]
        final_report_content = reports.get("final_trade_decision")

        # A race condition can occur where the final report is generated but the analysis_complete flag is not yet set.
        # We should only show the final decision when the state is confirmed as complete.
        if state.get("analysis_complete") and final_report_content is not None:
            if state["analysis_results"]:
                decision_text = f"## Final Decision for {state['ticker_symbol']}\n\n"
                decision_text += f"**Trade Action:** {state['analysis_results'].get('decision', 'No decision')}\n\n"
                decision_text += "**Date:** " + state['analysis_results'].get("date", "N/A")
            else:
                # Show the recommended action if available
                decision_text = f"## Final Decision for {state['ticker_symbol']}\n\n"
                
                # Display the extracted recommendation prominently
                if "recommended_action" in state and state["recommended_action"]:
                    decision_text += f"**📈 RECOMMENDED ACTION: {state['recommended_action']}**\n\n"
                
                decision_text += "**Full Analysis:**\n"
                decision_text += final_report_content
        else:
            # Show partial decision summary based on available reports
            available_reports = []
            if state["current_reports"].get("market_report"):
                available_reports.append("Market Analysis")
            if state["current_reports"].get("sentiment_report"):
                available_reports.append("Social Media Sentiment")
            if state["current_reports"].get("news_report"):
                available_reports.append("News Analysis")
            if state["current_reports"].get("fundamentals_report"):
                available_reports.append("Fundamentals Analysis")
            if state["current_reports"].get("macro_report"):
                available_reports.append("Macro Analysis")
            if state["current_reports"].get("research_manager_report"):
                available_reports.append("Research Manager Decision")
            if state["current_reports"].get("trader_investment_plan"):
                available_reports.append("Trader Investment Plan")
            if state.get("risk_debate_state", {}).get("history"):
                available_reports.append("Risk Debate")
            if final_report_content is not None:
                available_reports.append("Portfolio Manager Final Decision")
            
            if available_reports:
                decision_text = f"## Partial Analysis for {state['ticker_symbol']}\n\n"
                decision_text += "**Completed Reports:** " + ", ".join(available_reports) + "\n\n"
                
                # Show the latest available decision as "Current Decision"
                risk_debate_latest = ""
                if state.get("risk_debate_state", {}).get("history"):
                    # Get the last message from risk debate
                    risk_history = state["risk_debate_state"]["history"]
                    if risk_history:
                        risk_debate_latest = risk_history.split('\n')[-1] if risk_history else ""
                
                current_decision = (
                    final_report_content or
                    risk_debate_latest or
                    state["current_reports"].get("trader_investment_plan") or
                    state["current_reports"].get("research_manager_report")
                )
                
                if current_decision:
                    decision_text += "**Current Decision:** Based on completed analysis\n\n"
                    decision_text += current_decision
            else:
                decision_text = "Analysis not complete yet."
        
        return decision_text

    @app.callback(
        Output("current-symbol-report-display", "children"),
        [Input("report-pagination", "active_page")]
    )
    def update_report_display_text(active_page):
        if not app_state.symbol_states or not active_page:
            return ""
        
        # Safeguard against accessing invalid page index (e.g., after page refresh)
        symbols_list = list(app_state.symbol_states.keys())
        if active_page > len(symbols_list):
            return "Invalid page"
        
        symbol = symbols_list[active_page - 1]
        return f"📊 {symbol}"

    @app.callback(
        Output("tabs", "active_tab"),
        [Input("nav-market", "n_clicks"),
         Input("nav-social", "n_clicks"),
         Input("nav-news", "n_clicks"),
         Input("nav-fundamentals", "n_clicks"),
         Input("nav-researcher", "n_clicks"),
         Input("nav-research-mgr", "n_clicks"),
         Input("nav-trader", "n_clicks"),
         Input("nav-risk-agg", "n_clicks"),
         Input("nav-risk-cons", "n_clicks"),
         Input("nav-risk-neut", "n_clicks"),
         Input("nav-final", "n_clicks")]
    )
    def switch_tab(*args):
        """Switch between tabs based on navigation clicks"""
        ctx = dash.callback_context
        if not ctx.triggered:
            return "market-analysis"
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        tab_mapping = {
            "nav-market": "market-analysis",
            "nav-social": "social-sentiment", 
            "nav-news": "news-analysis",
            "nav-fundamentals": "fundamentals-analysis",
            "nav-researcher": "researcher-debate",
            "nav-research-mgr": "research-manager",
            "nav-trader": "trader-plan",
            "nav-risk-agg": "risk-debate",
            "nav-risk-cons": "risk-debate", 
            "nav-risk-neut": "risk-debate",
            "nav-final": "final-decision"
        }
        
        return tab_mapping.get(trigger_id, "market-analysis") 