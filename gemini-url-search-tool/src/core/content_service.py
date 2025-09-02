"""
Content processing service for Gemini URL Search Tool.

Handles URL content fetching, analysis, and summarization.
"""

import asyncio
import logging
import time
import re
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup
import chardet

from ..models.data_models import ContentAnalysis, ContentType
from ..utils.error_handler import ContentFetchError, ContentProcessingError
from .gemini_client import GeminiClient
try:
    from src.core.cache_service import get_cache_service
except ImportError:
    # Fallback if cache service is not available
    def get_cache_service():
        return None


logger = logging.getLogger(__name__)


class ContentService:
    """
    Service for processing web content.
    
    Provides functionality for:
    - Fetching content from URLs
    - Automatic content type detection
    - Content summarization using Gemini API
    - Technical specification extraction
    - Large content handling with chunking
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize ContentService.
        
        Args:
            gemini_client: Configured GeminiClient instance
        """
        self.gemini_client = gemini_client
        self.cache_service = get_cache_service()
        
        # Content processing limits
        self.max_content_size = 50000  # Maximum content size to process
        self.chunk_size = 8000  # Size of content chunks for large content
        self.fetch_timeout = 30  # Timeout for URL fetching
        
        # Content type detection patterns
        self.spec_patterns = [
            r'datasheet', r'specification', r'spec', r'manual',
            r'データシート', r'仕様書', r'マニュアル', r'技術資料'
        ]
        
        self.component_patterns = [
            r'arduino', r'raspberry', r'sensor', r'module',
            r'ic\b', r'mcu', r'cpu', r'gpio', r'i2c', r'spi',
            r'部品', r'モジュール', r'センサー', r'マイコン'
        ]
        
        logger.info("ContentService initialized")
    
    async def fetch_content(self, url: str) -> str:
        """
        Fetch content from a URL.
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Cleaned text content from the URL
            
        Raises:
            ContentFetchError: If content cannot be fetched
        """
        start_time = time.time()
        
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ContentFetchError(f"Invalid URL format: {url}")
            
            # Set up headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.fetch_timeout),
                headers=headers
            ) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise ContentFetchError(
                            f"HTTP {response.status} error when fetching {url}"
                        )
                    
                    # Get content with proper encoding detection
                    content_bytes = await response.read()
                    
                    # Detect encoding
                    encoding = self._detect_encoding(content_bytes, response.headers)
                    
                    try:
                        content_text = content_bytes.decode(encoding)
                    except UnicodeDecodeError:
                        # Fallback to utf-8 with error handling
                        content_text = content_bytes.decode('utf-8', errors='ignore')
                        logger.warning(f"Encoding detection failed for {url}, using UTF-8 with error handling")
                    
                    # Clean and extract text content
                    cleaned_content = self._clean_content(content_text, url)
                    
                    fetch_time = time.time() - start_time
                    logger.info(
                        f"Content fetched successfully: url={url}, "
                        f"size={len(cleaned_content)}, time={fetch_time:.2f}s"
                    )
                    
                    return cleaned_content
                    
        except aiohttp.ClientError as e:
            fetch_time = time.time() - start_time
            error_msg = f"Network error fetching {url}: {str(e)}"
            logger.error(f"{error_msg}, time={fetch_time:.2f}s")
            raise ContentFetchError(error_msg)
        
        except Exception as e:
            fetch_time = time.time() - start_time
            error_msg = f"Unexpected error fetching {url}: {str(e)}"
            logger.error(f"{error_msg}, time={fetch_time:.2f}s")
            raise ContentFetchError(error_msg)
    
    def detect_content_type(self, url: str, content: str) -> ContentType:
        """
        Automatically detect content type based on URL and content.
        
        Args:
            url: The source URL
            content: The content text
            
        Returns:
            Detected ContentType
        """
        url_lower = url.lower()
        content_lower = content.lower()
        
        # Check for specification/datasheet indicators
        spec_score = 0
        for pattern in self.spec_patterns:
            if re.search(pattern, url_lower) or re.search(pattern, content_lower):
                spec_score += 1
        
        # Check for component-related content
        component_score = 0
        for pattern in self.component_patterns:
            if re.search(pattern, url_lower) or re.search(pattern, content_lower):
                component_score += 1
        
        # Determine content type based on scores and specific indicators
        if spec_score > 0:
            # Check if it's specifically a datasheet
            if any(pattern in url_lower or pattern in content_lower 
                   for pattern in ['datasheet', 'データシート']):
                return ContentType.DATASHEET
            else:
                return ContentType.SPECIFICATION
        elif component_score > 0:
            return ContentType.SPECIFICATION
        else:
            return ContentType.GENERAL
    
    async def extract_key_info(
        self, 
        url: str, 
        content: str, 
        content_type: ContentType
    ) -> ContentAnalysis:
        """
        Extract key information from content using Gemini API.
        
        Args:
            url: Source URL
            content: Content text
            content_type: Detected content type
            
        Returns:
            ContentAnalysis with extracted information
            
        Raises:
            ContentProcessingError: If content processing fails
        """
        start_time = time.time()
        
        try:
            # Handle large content by chunking
            if len(content) > self.max_content_size:
                logger.info(f"Large content detected ({len(content)} chars), using chunking approach")
                analysis = await self._process_large_content(url, content, content_type)
            else:
                analysis = await self._process_content_chunk(url, content, content_type)
            
            analysis.extraction_time = time.time() - start_time
            analysis.content_size = len(content)
            
            logger.info(
                f"Content analysis completed: url={url}, type={content_type.value}, "
                f"time={analysis.extraction_time:.2f}s"
            )
            
            return analysis
            
        except Exception as e:
            extraction_time = time.time() - start_time
            error_msg = f"Content processing failed for {url}: {str(e)}"
            logger.error(f"{error_msg}, time={extraction_time:.2f}s")
            raise ContentProcessingError(error_msg)
    
    async def generate_summary(
        self, 
        content: str, 
        focus_areas: Optional[List[str]] = None,
        max_length: int = 1000
    ) -> str:
        """
        Generate a summary of content using Gemini API.
        
        Args:
            content: Content to summarize
            focus_areas: Optional list of areas to focus on
            max_length: Maximum length of summary
            
        Returns:
            Generated summary text
            
        Raises:
            ContentProcessingError: If summarization fails
        """
        try:
            focus = ", ".join(focus_areas) if focus_areas else None
            summary = await self.gemini_client.summarize_content(
                content=content,
                focus=focus,
                max_length=max_length
            )
            
            return summary
            
        except Exception as e:
            error_msg = f"Content summarization failed: {str(e)}"
            logger.error(error_msg)
            raise ContentProcessingError(error_msg)
    
    async def _process_content_chunk(
        self, 
        url: str, 
        content: str, 
        content_type: ContentType
    ) -> ContentAnalysis:
        """
        Process a single chunk of content.
        
        Args:
            url: Source URL
            content: Content chunk
            content_type: Content type
            
        Returns:
            ContentAnalysis result
        """
        # Build analysis prompt based on content type
        prompt = self._build_analysis_prompt(content, content_type)
        
        # Use GeminiClient's existing analyze_content method as base
        # but with our custom prompt
        response = await self.gemini_client._make_request_with_fallback(prompt)
        
        if not response.success:
            raise ContentProcessingError(f"Gemini API analysis failed: {response.error}")
        
        # Parse the response
        analysis_data = self.gemini_client._extract_json_from_response(response.data)
        
        if analysis_data:
            return ContentAnalysis(
                url=url,
                content_type=analysis_data.get("content_type", content_type.value),
                summary=analysis_data.get("summary", ""),
                key_points=analysis_data.get("key_points", []),
                technical_specs=analysis_data.get("technical_specs", {}),
                content_size=len(content)
            )
        else:
            # Fallback: use the raw response as summary
            return ContentAnalysis(
                url=url,
                content_type=content_type.value,
                summary=response.data[:1000],
                key_points=[],
                technical_specs={},
                content_size=len(content)
            )
    
    async def _process_large_content(
        self, 
        url: str, 
        content: str, 
        content_type: ContentType
    ) -> ContentAnalysis:
        """
        Process large content by splitting into chunks and combining results.
        
        Args:
            url: Source URL
            content: Large content text
            content_type: Content type
            
        Returns:
            Combined ContentAnalysis result
        """
        # Split content into chunks
        chunks = self._split_content_into_chunks(content)
        
        logger.info(f"Processing large content in {len(chunks)} chunks")
        
        # Process each chunk
        chunk_analyses = []
        for i, chunk in enumerate(chunks):
            try:
                logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
                analysis = await self._process_content_chunk(url, chunk, content_type)
                chunk_analyses.append(analysis)
                
                # Add delay between chunks to respect rate limits
                if i < len(chunks) - 1:
                    await asyncio.sleep(1.0)
                    
            except Exception as e:
                logger.warning(f"Failed to process chunk {i+1}: {e}")
                continue
        
        if not chunk_analyses:
            raise ContentProcessingError("Failed to process any content chunks")
        
        # Combine results from all chunks
        return self._combine_chunk_analyses(url, chunk_analyses, content_type)
    
    def _split_content_into_chunks(self, content: str) -> List[str]:
        """
        Split large content into manageable chunks.
        
        Args:
            content: Content to split
            
        Returns:
            List of content chunks
        """
        chunks = []
        
        # Try to split by paragraphs first
        paragraphs = content.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    # Single paragraph is too large, split by sentences
                    sentences = re.split(r'[.!?。！？]\s+', paragraph)
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) > self.chunk_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = sentence
                            else:
                                # Single sentence is too large, force split
                                chunks.append(sentence[:self.chunk_size])
                        else:
                            current_chunk += sentence + ". "
            else:
                current_chunk += paragraph + "\n\n"
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _combine_chunk_analyses(
        self, 
        url: str, 
        analyses: List[ContentAnalysis], 
        content_type: ContentType
    ) -> ContentAnalysis:
        """
        Combine multiple chunk analyses into a single result.
        
        Args:
            url: Source URL
            analyses: List of ContentAnalysis from chunks
            content_type: Overall content type
            
        Returns:
            Combined ContentAnalysis
        """
        # Combine summaries
        summaries = [a.summary for a in analyses if a.summary]
        combined_summary = " ".join(summaries)
        
        # If combined summary is too long, summarize it
        if len(combined_summary) > 2000:
            # Take the first few summaries that fit
            combined_summary = ""
            for summary in summaries:
                if len(combined_summary) + len(summary) <= 2000:
                    combined_summary += summary + " "
                else:
                    break
        
        # Combine key points (remove duplicates)
        all_key_points = []
        for analysis in analyses:
            all_key_points.extend(analysis.key_points)
        
        # Remove duplicates while preserving order
        unique_key_points = []
        seen = set()
        for point in all_key_points:
            if point.lower() not in seen:
                unique_key_points.append(point)
                seen.add(point.lower())
        
        # Limit to most important points
        key_points = unique_key_points[:10]
        
        # Combine technical specs
        combined_specs = {}
        for analysis in analyses:
            combined_specs.update(analysis.technical_specs)
        
        # Calculate total content size
        total_size = sum(a.content_size for a in analyses)
        
        return ContentAnalysis(
            url=url,
            content_type=content_type.value,
            summary=combined_summary.strip(),
            key_points=key_points,
            technical_specs=combined_specs,
            content_size=total_size
        )
    
    def _build_analysis_prompt(self, content: str, content_type: ContentType) -> str:
        """
        Build analysis prompt based on content type.
        
        Args:
            content: Content to analyze
            content_type: Type of content
            
        Returns:
            Formatted prompt for Gemini API
        """
        # Truncate content if needed
        max_content_length = 8000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        if content_type == ContentType.SPECIFICATION or content_type == ContentType.DATASHEET:
            return f"""
以下の技術文書を分析し、構造化された情報を抽出してください。

コンテンツ:
{content}

以下の形式でJSONレスポンスを返してください：
{{
  "content_type": "{content_type.value}",
  "summary": "技術文書の要約（主要な機能、用途、特徴を含む）",
  "key_points": [
    "重要な技術的特徴1",
    "重要な技術的特徴2",
    "用途・応用例",
    "注意事項・制限"
  ],
  "technical_specs": {{
    "動作電圧": "値と単位",
    "動作温度": "値と単位",
    "寸法": "値と単位",
    "インターフェース": "種類",
    "消費電力": "値と単位",
    "その他の仕様": "値"
  }}
}}

技術仕様は可能な限り具体的な数値と単位を含めてください。
仕様が明記されていない項目は含めないでください。
"""
        else:
            return f"""
以下のWebページ内容を分析し、構造化された情報を抽出してください。

コンテンツ:
{content}

以下の形式でJSONレスポンスを返してください：
{{
  "content_type": "general",
  "summary": "コンテンツの要約（主要なポイントを含む）",
  "key_points": [
    "重要なポイント1",
    "重要なポイント2",
    "実用的な情報",
    "注意すべき点"
  ],
  "technical_specs": {{}}
}}

主要な情報を分かりやすく整理し、実用的な内容を重視してください。
"""
    
    def _detect_encoding(self, content_bytes: bytes, headers: Dict[str, str]) -> str:
        """
        Detect content encoding from headers and content.
        
        Args:
            content_bytes: Raw content bytes
            headers: HTTP response headers
            
        Returns:
            Detected encoding name
        """
        # First, try to get encoding from headers
        content_type = headers.get('content-type', '').lower()
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[1].split(';')[0].strip()
            if charset:
                return charset
        
        # Use chardet for automatic detection
        try:
            detected = chardet.detect(content_bytes)
            if detected and detected['encoding']:
                confidence = detected.get('confidence', 0)
                if confidence > 0.7:  # Only use if confidence is high
                    return detected['encoding']
        except Exception as e:
            logger.warning(f"Encoding detection failed: {e}")
        
        # Default fallback
        return 'utf-8'
    
    def _clean_content(self, html_content: str, url: str) -> str:
        """
        Clean HTML content and extract readable text.
        
        Args:
            html_content: Raw HTML content
            url: Source URL for context
            
        Returns:
            Cleaned text content
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            logger.warning(f"HTML parsing failed for {url}: {e}")
            # Fallback: basic text cleaning
            text = re.sub(r'<[^>]+>', '', html_content)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get content processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            "max_content_size": self.max_content_size,
            "chunk_size": self.chunk_size,
            "fetch_timeout": self.fetch_timeout,
            "spec_patterns_count": len(self.spec_patterns),
            "component_patterns_count": len(self.component_patterns)
        }