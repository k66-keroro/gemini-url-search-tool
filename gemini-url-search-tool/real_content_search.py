#!/usr/bin/env python3
"""
Real Content Search - 実際のコンテンツURLを取得する検索ツール
"""

import streamlit as st
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import google.generativeai as genai
import time
from urllib.parse import quote_plus, urlparse, urljoin
import re

# Load environment variables
load_dotenv()

def search_with_real_urls(query, num_results=8):
    """実際のコンテンツURLを取得する検索"""
    results = []
    
    # 1. Wikipedia検索（実際の記事URL）
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(query)}&limit=3&format=json"
        response = requests.get(wiki_url, timeout=10)
        data = response.json()
        
        if len(data) >= 4:
            titles = data[1]
            descriptions = data[2]
            urls = data[3]
            
            for i in range(min(len(titles), 3)):
                results.append({
                    'title': f"{titles[i]} - Wikipedia",
                    'url': urls[i],
                    'description': descriptions[i] if i < len(descriptions) else "Wikipedia article",
                    'source': 'Wikipedia',
                    'confidence': 0.9
                })
    except:
        pass
    
    # 2. GitHub検索（実際のリポジトリURL）
    try:
        tech_keywords = ['python', 'javascript', 'react', 'vue', 'angular', 'node', 'docker', 'kubernetes', 'aws', 'api', 'framework', 'library', 'vba', 'visual basic', 'excel', 'code', 'programming']
        if any(keyword in query.lower() for keyword in tech_keywords):
            github_url = f"https://api.github.com/search/repositories?q={quote_plus(query)}&sort=stars&order=desc&per_page=2"
            response = requests.get(github_url, timeout=10)
            data = response.json()
            
            if 'items' in data:
                for repo in data['items'][:2]:
                    results.append({
                        'title': f"{repo['name']} - GitHub",
                        'url': repo['html_url'],
                        'description': repo.get('description', 'GitHub repository'),
                        'source': 'GitHub',
                        'confidence': 0.8
                    })
    except:
        pass
    
    # 3. DuckDuckGo Instant Answer（実際のURL）
    try:
        ddg_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        response = requests.get(ddg_url, timeout=10)
        data = response.json()
        
        # Related Topics から実際のURL
        if 'RelatedTopics' in data:
            for topic in data['RelatedTopics'][:3]:
                if isinstance(topic, dict) and 'FirstURL' in topic and topic.get('FirstURL'):
                    results.append({
                        'title': topic.get('Text', 'DuckDuckGo Result')[:80] + '...',
                        'url': topic.get('FirstURL'),
                        'description': topic.get('Text', 'Related information'),
                        'source': 'DuckDuckGo',
                        'confidence': 0.7
                    })
        
        # Abstract URL
        if data.get('AbstractURL') and data.get('Abstract'):
            results.append({
                'title': data.get('Heading', 'Main Result'),
                'url': data.get('AbstractURL'),
                'description': data.get('Abstract', 'Main information'),
                'source': 'DuckDuckGo',
                'confidence': 0.8
            })
    except:
        pass
    
    # 4. 手動で厳選した実際のURL
    manual_sites = {
        'python': [
            {'title': 'Python.org - Official Site', 'url': 'https://www.python.org/', 'description': 'Official Python programming language website', 'confidence': 1.0},
            {'title': 'Python Tutorial', 'url': 'https://docs.python.org/3/tutorial/', 'description': 'Official Python tutorial', 'confidence': 1.0},
            {'title': 'Real Python', 'url': 'https://realpython.com/', 'description': 'High-quality Python tutorials', 'confidence': 0.9},
        ],
        'vba': [
            {'title': 'Microsoft VBA Documentation', 'url': 'https://docs.microsoft.com/en-us/office/vba/', 'description': 'Official Microsoft VBA documentation', 'confidence': 1.0},
            {'title': 'Excel VBA Tutorial', 'url': 'https://www.excel-easy.com/vba.html', 'description': 'Excel VBA tutorial and examples', 'confidence': 0.9},
        ],
        'javascript': [
            {'title': 'MDN JavaScript Guide', 'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide', 'description': 'Comprehensive JavaScript guide', 'confidence': 1.0},
            {'title': 'JavaScript.info', 'url': 'https://javascript.info/', 'description': 'Modern JavaScript tutorial', 'confidence': 0.9},
        ],
        'react': [
            {'title': 'React Official Tutorial', 'url': 'https://react.dev/learn', 'description': 'Official React learning guide', 'confidence': 1.0},
        ],
        '料理': [
            {'title': 'キッコーマン レシピ', 'url': 'https://www.kikkoman.co.jp/homecook/search/', 'description': 'キッコーマンの料理レシピサイト', 'confidence': 0.9},
            {'title': 'クラシル', 'url': 'https://www.kurashiru.com/', 'description': '動画で学べる料理レシピ', 'confidence': 0.8},
            {'title': 'Delish Kitchen', 'url': 'https://delishkitchen.tv/', 'description': '動画レシピサイト', 'confidence': 0.8},
        ],
        'レシピ': [
            {'title': 'キッコーマン レシピ', 'url': 'https://www.kikkoman.co.jp/homecook/search/', 'description': 'キッコーマンの料理レシピサイト', 'confidence': 0.9},
            {'title': 'クラシル', 'url': 'https://www.kurashiru.com/', 'description': '動画で学べる料理レシピ', 'confidence': 0.8},
            {'title': 'みんなのきょうの料理', 'url': 'https://www.kyounoryouri.jp/', 'description': 'NHKの料理番組レシピサイト', 'confidence': 0.8},
        ],
        '健康': [
            {'title': '厚生労働省', 'url': 'https://www.mhlw.go.jp/', 'description': '公式健康情報', 'confidence': 1.0},
            {'title': 'ヘルスケア大学', 'url': 'https://www.skincare-univ.com/', 'description': '医師監修の健康情報', 'confidence': 0.8},
        ],
        '旅行': [
            {'title': 'じゃらん', 'url': 'https://www.jalan.net/', 'description': '国内旅行予約サイト', 'confidence': 0.9},
            {'title': '楽天トラベル', 'url': 'https://travel.rakuten.co.jp/', 'description': '旅行予約・ホテル検索', 'confidence': 0.9},
        ],
        '学習': [
            {'title': 'Khan Academy', 'url': 'https://www.khanacademy.org/', 'description': '無料オンライン学習プラットフォーム', 'confidence': 0.9},
            {'title': 'Coursera', 'url': 'https://www.coursera.org/', 'description': '大学レベルのオンライン講座', 'confidence': 0.9},
        ],
    }
    
    query_lower = query.lower()
    for keyword, sites in manual_sites.items():
        if keyword in query_lower:
            for site in sites:
                site['source'] = 'Curated'
                results.append(site)
    
    return results[:num_results]

def scrape_search_results(query, num_results=3):
    """検索エンジンから実際の結果URLをスクレイピング（実験的）"""
    results = []
    
    try:
        # DuckDuckGo HTMLページをスクレイピング（robots.txtに注意）
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # DuckDuckGoの検索結果を解析
            search_results = soup.find_all('a', class_='result__a')
            
            for i, link in enumerate(search_results[:num_results]):
                href = link.get('href')
                title = link.get_text().strip()
                
                if href and title and not href.startswith('/'):
                    # 相対URLを絶対URLに変換
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = 'https://duckduckgo.com' + href
                    
                    results.append({
                        'title': title[:100] + '...' if len(title) > 100 else title,
                        'url': href,
                        'description': f'Search result for {query}',
                        'source': 'DuckDuckGo Scrape',
                        'confidence': 0.6
                    })
    except Exception as e:
        st.warning(f"Scraping failed: {e}")
    
    return results

def fetch_and_analyze_content(url, query, api_key):
    """コンテンツを取得して分析"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # タイトル取得
        title = soup.find('title')
        page_title = title.get_text().strip() if title else "No Title"
        
        # 不要な要素を削除
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # テキスト抽出
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        if len(text) > 8000:
            text = text[:8000] + "..."
        
        # Gemini分析
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        analysis_prompt = f"""
以下のWebページを検索クエリ「{query}」の観点から分析してください。

【ページ情報】
タイトル: {page_title}
URL: {url}

【分析要求】
1. 要約（200文字程度）
2. 重要なポイント（3-5個）
3. 検索クエリとの関連性（1-5で評価）
4. このページから得られる具体的な価値

【内容】
{text[:6000]}

【分析結果】
"""
        
        analysis_response = model.generate_content(analysis_prompt)
        
        return {
            'success': True,
            'title': page_title,
            'url': url,
            'content_length': len(text),
            'analysis': analysis_response.text
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    st.set_page_config(
        page_title="Real Content Search Tool",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Real Content Search Tool")
    st.markdown("**実際のコンテンツURLを取得する検索ツール**")
    st.markdown("---")
    
    # API key check
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        st.success("✅ Gemini API key configured")
    else:
        st.error("❌ Gemini API key not found")
        st.stop()
    
    # Search Section
    st.subheader("🔍 Real URL Search")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="例: Python 学習",
            help="検索したいキーワードを入力"
        )
    
    with col2:
        include_scraping = st.checkbox("Include Scraping", value=True, help="実験的なスクレイピング検索を含める（推奨）")
    
    if st.button("🎯 Search Real URLs", type="primary"):
        if query:
            with st.spinner("Searching for real content URLs..."):
                # 基本検索
                results = search_with_real_urls(query, 6)
                
                # スクレイピング検索（オプション）
                if include_scraping:
                    scraped_results = scrape_search_results(query, 3)
                    results.extend(scraped_results)
                
                if results:
                    st.session_state.search_results = results
                    st.session_state.search_query = query
                    st.success(f"✅ Found {len(results)} real content URLs")
                else:
                    st.warning("No results found")
        else:
            st.warning("Please enter a search query")
    
    # Results Display
    if hasattr(st.session_state, 'search_results'):
        st.markdown("---")
        st.subheader("🎯 Real Content URLs")
        
        results = st.session_state.search_results
        
        for i, result in enumerate(results, 1):
            # 信頼度に応じて色を変更
            confidence = result.get('confidence', 0.5)
            if confidence >= 0.8:
                border_color = "#28a745"  # Green
            elif confidence >= 0.6:
                border_color = "#ffc107"  # Yellow
            else:
                border_color = "#dc3545"  # Red
            
            with st.container():
                st.markdown(f"""
                <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <h4 style="margin: 0; color: #333;">{result['title']}</h4>
                            <p style="margin: 5px 0; color: #666; font-size: 14px;">
                                <strong>URL:</strong> {result['url']}
                            </p>
                            <p style="margin: 5px 0; color: #666; font-size: 14px;">
                                <strong>Description:</strong> {result['description']}
                            </p>
                            <p style="margin: 5px 0; color: #888; font-size: 12px;">
                                <strong>Source:</strong> {result.get('source', 'Unknown')} | 
                                <strong>Confidence:</strong> {confidence:.1f}/1.0
                            </p>
                        </div>
                        <div style="margin-left: 20px;">
                            <a href="{result['url']}" target="_blank" style="text-decoration: none; margin-right: 10px;">🔗</a>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 詳細分析ボタン
                if st.button(f"📄 Analyze Content", key=f"analyze_{i}"):
                    with st.spinner("Analyzing content..."):
                        analysis = fetch_and_analyze_content(
                            result['url'], 
                            st.session_state.search_query, 
                            api_key
                        )
                        
                        if analysis['success']:
                            st.markdown("---")
                            st.subheader(f"🔍 Content Analysis: {analysis['title']}")
                            
                            st.markdown(f"""
                            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                            {analysis['analysis']}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.write(f"**Content Length:** {analysis['content_length']} characters")
                        else:
                            st.error(f"❌ Analysis failed: {analysis['error']}")
    
    # Clear button
    if st.button("🗑️ Clear Results"):
        for key in ['search_results', 'search_query']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()