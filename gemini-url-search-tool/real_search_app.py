#!/usr/bin/env python3
"""
Real Web Search App - Gemini URL Search Tool with actual web search
"""

import streamlit as st
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus
import time

# Load environment variables
load_dotenv()

def search_duckduckgo(query, num_results=5):
    """
    DuckDuckGo Instant Answer APIを使用した検索
    """
    try:
        # DuckDuckGo Instant Answer API
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        results = []
        
        # Related Topics から結果を取得
        if 'RelatedTopics' in data:
            for topic in data['RelatedTopics'][:num_results]:
                if isinstance(topic, dict) and 'FirstURL' in topic:
                    results.append({
                        'title': topic.get('Text', 'No Title')[:100] + '...' if len(topic.get('Text', '')) > 100 else topic.get('Text', 'No Title'),
                        'url': topic.get('FirstURL', ''),
                        'description': topic.get('Text', 'No description available')
                    })
        
        # Abstract から結果を取得
        if len(results) < num_results and data.get('Abstract'):
            results.append({
                'title': data.get('Heading', 'Main Result'),
                'url': data.get('AbstractURL', ''),
                'description': data.get('Abstract', 'No description available')
            })
        
        return results
        
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return []

def search_with_requests(query, num_results=5):
    """
    シンプルなWeb検索（検索エンジンのHTMLを解析）
    """
    try:
        # Google検索のURL（簡易版）
        search_url = f"https://www.google.com/search?q={quote_plus(query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 注意: これは教育目的のデモです。実際の使用では適切なAPIを使用してください
        st.warning("⚠️ 実際のGoogle検索は利用規約により制限されています。デモ用の結果を表示します。")
        
        # デモ用の現実的な結果を生成
        demo_results = [
            {
                'title': f'{query} - 公式ドキュメント',
                'url': f'https://docs.python.org/3/search.html?q={quote_plus(query)}',
                'description': f'{query}に関する公式ドキュメントです。'
            },
            {
                'title': f'{query} - Stack Overflow',
                'url': f'https://stackoverflow.com/search?q={quote_plus(query)}',
                'description': f'{query}に関するStack Overflowの質問と回答です。'
            },
            {
                'title': f'{query} - GitHub',
                'url': f'https://github.com/search?q={quote_plus(query)}',
                'description': f'{query}に関するGitHubリポジトリとコードです。'
            },
            {
                'title': f'{query} - Wikipedia',
                'url': f'https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(query)}',
                'description': f'{query}に関するWikipediaの記事です。'
            },
            {
                'title': f'{query} - YouTube',
                'url': f'https://www.youtube.com/results?search_query={quote_plus(query)}',
                'description': f'{query}に関するYouTube動画です。'
            }
        ]
        
        return demo_results[:num_results]
        
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return []

def main():
    """Main application"""
    st.set_page_config(
        page_title="Real Web Search Tool",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Real Web Search Tool")
    st.markdown("---")
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    debug_mode = st.checkbox("🐛 Enable Debug Mode", value=False)
    
    if api_key:
        st.success("✅ API key configured")
    else:
        st.warning("⚠️ Gemini API key not configured (optional for web search)")
    
    # Search interface
    st.subheader("🌐 Real Web Search")
    
    search_method = st.selectbox(
        "Search Method",
        ["DuckDuckGo API", "Demo Search (Safe)"],
        help="Choose how to search the web"
    )
    
    keywords = st.text_input(
        "Search Keywords",
        placeholder="Enter keywords to search for...",
        help="Enter keywords or phrases to search for"
    )
    
    num_results = st.slider("Number of Results", 1, 10, 5)
    
    if st.button("🔍 Search Web", type="primary"):
        if keywords:
            with st.spinner("Searching the web..."):
                if search_method == "DuckDuckGo API":
                    results = search_duckduckgo(keywords, num_results)
                else:
                    results = search_with_requests(keywords, num_results)
                
                if results:
                    st.success(f"✅ Found {len(results)} results for: {keywords}")
                    
                    st.subheader("🌐 Web Search Results")
                    
                    for i, result in enumerate(results, 1):
                        with st.expander(f"Result {i}: {result['title']}"):
                            st.write(f"**URL:** {result['url']}")
                            if result['url']:
                                st.markdown(f"[🔗 Open Link]({result['url']})")
                            st.write(f"**Description:** {result['description']}")
                            
                            # URL validation
                            if result['url']:
                                try:
                                    response = requests.head(result['url'], timeout=5)
                                    if response.status_code == 200:
                                        st.success("✅ URL is accessible")
                                    else:
                                        st.warning(f"⚠️ URL returned status: {response.status_code}")
                                except:
                                    st.error("❌ URL is not accessible")
                            
                            if debug_mode:
                                st.json(result)
                else:
                    st.warning("No results found. Try different keywords.")
        else:
            st.warning("Please enter keywords to search")
    
    # AI Enhancement section
    if api_key:
        st.markdown("---")
        st.subheader("🤖 AI-Enhanced Analysis")
        
        if st.button("🧠 Analyze Search Results with AI"):
            if 'results' in locals() and results:
                try:
                    import google.generativeai as genai
                    
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Create analysis prompt
                    results_text = "\n".join([f"Title: {r['title']}\nURL: {r['url']}\nDescription: {r['description']}\n" for r in results])
                    
                    analysis_prompt = f"""
                    Analyze these web search results for the query "{keywords}":
                    
                    {results_text}
                    
                    Please provide:
                    1. A summary of what these results cover
                    2. Which results are most relevant
                    3. Any gaps or additional resources that might be helpful
                    4. Recommendations for further research
                    """
                    
                    response = model.generate_content(analysis_prompt)
                    
                    st.subheader("🧠 AI Analysis")
                    st.write(response.text)
                    
                except Exception as e:
                    st.error(f"AI analysis failed: {str(e)}")
            else:
                st.warning("Please perform a web search first")
    
    # System status
    st.markdown("---")
    with st.expander("📋 System Status"):
        st.write("**Search Methods:**")
        st.write("- DuckDuckGo API: Free web search")
        st.write("- Demo Search: Safe demonstration mode")
        
        st.write("**Features:**")
        st.write("- ✅ Real web search")
        st.write("- ✅ URL validation")
        st.write("- ✅ AI analysis (if API key provided)")
        st.write("- ✅ Debug mode")

if __name__ == "__main__":
    main()