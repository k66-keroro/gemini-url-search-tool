"""
Gemini API client for URL search and content analysis.
"""

import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import aiohttp
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..models.data_models import SearchResult, ContentAnalysis, SearchType, ContentType
from ..utils.error_handler import GeminiAPIError, RateLimitError, AuthenticationError


logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available Gemini model types."""
    GEMINI_2_0_FLASH = "gemini-2.0-flash-exp"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"


@dataclass
class APIResponse:
    """Represents an API response."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    model_used: Optional[str] = None
    response_time: float = 0.0


class GeminiClient:
    """
    Client for interacting with Google Gemini API.
    
    Provides URL search and content analysis capabilities with:
    - Multiple model fallback support
    - Rate limiting and retry logic
    - Error handling and logging
    """
    
    def __init__(
        self, 
        api_key: str, 
        models: Optional[List[str]] = None,
        max_retries: int = 3,
        timeout: int = 30,
        rate_limit_delay: float = 1.0
    ):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google AI API key
            models: List of model names to use (with fallback order)
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            rate_limit_delay: Base delay for rate limiting (seconds)
        """
        self.api_key = api_key
        self.models = models or [ModelType.GEMINI_2_0_FLASH.value, ModelType.GEMINI_1_5_FLASH.value]
        self.max_retries = max_retries
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Initialize model instances
        self._model_instances = {}
        self._initialize_models()
        
        # Rate limiting state
        self._last_request_time = 0.0
        self._request_count = 0
        
        logger.info(f"GeminiClient initialized with models: {self.models}")
    
    def _initialize_models(self) -> None:
        """Initialize Gemini model instances."""
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        for model_name in self.models:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    safety_settings=safety_settings
                )
                self._model_instances[model_name] = model
                logger.debug(f"Initialized model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize model {model_name}: {e}")
    
    async def search_urls(
        self, 
        query: str, 
        search_type: SearchType = SearchType.GENERAL,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Search for URLs using Gemini API.
        
        Args:
            query: Search query string
            search_type: Type of search (general or component)
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
            
        Raises:
            GeminiAPIError: If API request fails
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If API key is invalid
        """
        start_time = time.time()
        
        try:
            # Build search prompt
            prompt = self._build_search_prompt(query, search_type, max_results)
            
            # Make API request with fallback
            response = await self._make_request_with_fallback(prompt)
            
            if not response.success:
                raise GeminiAPIError(f"Search failed: {response.error}")
            
            # Parse search results
            results = self._parse_search_results(response.data, query)
            
            # Log successful search
            search_time = time.time() - start_time
            logger.info(
                f"Search completed: query='{query}', type={search_type.value}, "
                f"results={len(results)}, time={search_time:.2f}s, model={response.model_used}"
            )
            
            return results
            
        except Exception as e:
            search_time = time.time() - start_time
            logger.error(f"Search failed: query='{query}', error={str(e)}, time={search_time:.2f}s")
            raise
    
    async def analyze_content(self, url: str) -> ContentAnalysis:
        """
        Analyze content from a URL using Gemini API.
        
        Args:
            url: URL to analyze
            
        Returns:
            ContentAnalysis object with extracted information
            
        Raises:
            GeminiAPIError: If API request fails
        """
        start_time = time.time()
        
        try:
            # First, fetch the content
            content = await self._fetch_url_content(url)
            
            if not content:
                raise GeminiAPIError(f"Could not fetch content from URL: {url}")
            
            # Build analysis prompt
            prompt = self._build_analysis_prompt(url, content)
            
            # Make API request with fallback
            response = await self._make_request_with_fallback(prompt)
            
            if not response.success:
                raise GeminiAPIError(f"Content analysis failed: {response.error}")
            
            # Parse analysis results
            analysis = self._parse_content_analysis(url, response.data, len(content))
            analysis.extraction_time = time.time() - start_time
            
            logger.info(
                f"Content analysis completed: url={url}, "
                f"time={analysis.extraction_time:.2f}s, model={response.model_used}"
            )
            
            return analysis
            
        except Exception as e:
            extraction_time = time.time() - start_time
            logger.error(f"Content analysis failed: url={url}, error={str(e)}, time={extraction_time:.2f}s")
            raise
    
    async def summarize_content(
        self, 
        content: str, 
        focus: Optional[str] = None,
        max_length: int = 1000
    ) -> str:
        """
        Generate a summary of the given content.
        
        Args:
            content: Text content to summarize
            focus: Optional focus area for the summary
            max_length: Maximum length of the summary
            
        Returns:
            Summary text
            
        Raises:
            GeminiAPIError: If API request fails
        """
        start_time = time.time()
        
        try:
            # Build summary prompt
            prompt = self._build_summary_prompt(content, focus, max_length)
            
            # Make API request with fallback
            response = await self._make_request_with_fallback(prompt)
            
            if not response.success:
                raise GeminiAPIError(f"Content summarization failed: {response.error}")
            
            summary = response.data.strip()
            
            summary_time = time.time() - start_time
            logger.info(
                f"Content summarization completed: "
                f"content_length={len(content)}, summary_length={len(summary)}, "
                f"time={summary_time:.2f}s, model={response.model_used}"
            )
            
            return summary
            
        except Exception as e:
            summary_time = time.time() - start_time
            logger.error(f"Content summarization failed: error={str(e)}, time={summary_time:.2f}s")
            raise
    
    async def _make_request_with_fallback(self, prompt: str) -> APIResponse:
        """
        Make API request with model fallback support.
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            APIResponse object
        """
        last_error = None
        
        for model_name in self.models:
            if model_name not in self._model_instances:
                logger.warning(f"Model {model_name} not available, skipping")
                continue
            
            try:
                # Apply rate limiting
                await self._apply_rate_limit()
                
                # Make request with retry logic
                response = await self._make_request_with_retry(model_name, prompt)
                
                if response.success:
                    return response
                
                last_error = response.error
                logger.warning(f"Model {model_name} failed: {response.error}")
                
            except RateLimitError as e:
                logger.warning(f"Rate limit hit for model {model_name}: {e}")
                last_error = str(e)
                continue
            except AuthenticationError as e:
                logger.error(f"Authentication failed for model {model_name}: {e}")
                raise e
            except Exception as e:
                logger.warning(f"Unexpected error with model {model_name}: {e}")
                last_error = str(e)
                continue
        
        # All models failed
        error_msg = f"All models failed. Last error: {last_error}"
        return APIResponse(success=False, error=error_msg)
    
    async def _make_request_with_retry(self, model_name: str, prompt: str) -> APIResponse:
        """
        Make API request with retry logic for a specific model.
        
        Args:
            model_name: Name of the model to use
            prompt: The prompt to send
            
        Returns:
            APIResponse object
        """
        model = self._model_instances[model_name]
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                # Generate content
                response = await asyncio.wait_for(
                    asyncio.to_thread(model.generate_content, prompt),
                    timeout=self.timeout
                )
                
                response_time = time.time() - start_time
                
                # Validate response
                if not response or not response.text:
                    raise GeminiAPIError("Empty response from API")
                
                self._request_count += 1
                
                return APIResponse(
                    success=True,
                    data=response.text,
                    model_used=model_name,
                    response_time=response_time
                )
                
            except asyncio.TimeoutError:
                last_error = f"Request timeout after {self.timeout}s"
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.max_retries + 1}: {last_error}")
                
            except Exception as e:
                last_error = str(e)
                
                # Check for specific error types
                if "quota" in last_error.lower() or "rate" in last_error.lower():
                    raise RateLimitError(f"Rate limit exceeded: {last_error}")
                elif "auth" in last_error.lower() or "key" in last_error.lower():
                    raise AuthenticationError(f"Authentication failed: {last_error}")
                
                logger.warning(f"API error on attempt {attempt + 1}/{self.max_retries + 1}: {last_error}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                delay = self.rate_limit_delay * (2 ** attempt)
                logger.debug(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        return APIResponse(success=False, error=f"Max retries exceeded. Last error: {last_error}")
    
    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _build_search_prompt(self, query: str, search_type: SearchType, max_results: int) -> str:
        """Build search prompt based on query and search type."""
        if search_type == SearchType.COMPONENT:
            # Try to extract manufacturer and part number from query
            parts = query.split()
            if len(parts) >= 2:
                manufacturer = parts[0]
                part_number = " ".join(parts[1:])
                return f"""
メーカー「{manufacturer}」の品番「{part_number}」の公式仕様書・データシートのURLを検索してください。

以下の形式でJSONレスポンスを返してください：
{{
  "results": [
    {{
      "url": "実際のURL",
      "title": "ページタイトル",
      "description": "簡潔な説明",
      "is_official": true/false,
      "confidence_score": 0.0-1.0
    }}
  ]
}}

最大{max_results}件の結果を返してください。
公式メーカーサイトを優先し、信頼性の高い技術情報源を選択してください。
"""
            else:
                # Fallback to general component search
                return f"""
部品「{query}」に関する技術仕様書・データシートのURLを検索してください。

以下の形式でJSONレスポンスを返してください：
{{
  "results": [
    {{
      "url": "実際のURL",
      "title": "ページタイトル",
      "description": "簡潔な説明",
      "is_official": true/false,
      "confidence_score": 0.0-1.0
    }}
  ]
}}

最大{max_results}件の結果を返してください。
"""
        else:
            # General search
            return f"""
以下のキーワードに関連する有用なWebサイトのURLを検索してください: {query}

以下の形式でJSONレスポンスを返してください：
{{
  "results": [
    {{
      "url": "実際のURL",
      "title": "ページタイトル",
      "description": "簡潔な説明",
      "is_official": false,
      "confidence_score": 0.0-1.0
    }}
  ]
}}

最大{max_results}件の結果を返してください。
信頼性が高く、情報が豊富なサイトを優先してください。
"""
    
    def _build_analysis_prompt(self, url: str, content: str) -> str:
        """Build content analysis prompt."""
        # Truncate content if too long
        max_content_length = 8000  # Leave room for prompt
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        return f"""
以下のWebページ内容を分析し、構造化された情報を抽出してください。

URL: {url}
コンテンツ:
{content}

以下の形式でJSONレスポンスを返してください：
{{
  "content_type": "general/specification/datasheet",
  "summary": "コンテンツの要約",
  "key_points": ["重要なポイント1", "重要なポイント2", ...],
  "technical_specs": {{
    "仕様項目1": "値1",
    "仕様項目2": "値2"
  }}
}}

技術仕様がある場合は technical_specs に構造化して含めてください。
一般的なコンテンツの場合は key_points に主要な情報を含めてください。
"""
    
    def _build_summary_prompt(self, content: str, focus: Optional[str], max_length: int) -> str:
        """Build content summary prompt."""
        # Truncate content if too long
        max_content_length = 8000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        focus_instruction = f"\n特に「{focus}」に焦点を当てて要約してください。" if focus else ""
        
        return f"""
以下のコンテンツを{max_length}文字以内で要約してください。{focus_instruction}

コンテンツ:
{content}

要約は以下の点を含めてください：
- 主要なポイント
- 重要な情報
- 実用的な内容

簡潔で分かりやすい日本語で要約してください。
"""
    
    async def _fetch_url_content(self, url: str) -> Optional[str]:
        """
        Fetch content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Content text or None if failed
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.text()
                        return content
                    else:
                        logger.warning(f"HTTP {response.status} when fetching {url}")
                        return None
        except Exception as e:
            logger.error(f"Failed to fetch content from {url}: {e}")
            return None
    
    def _parse_search_results(self, response_text: str, query: str) -> List[SearchResult]:
        """Parse search results from API response."""
        try:
            # Try to extract JSON from response
            response_data = self._extract_json_from_response(response_text)
            
            if not response_data or "results" not in response_data:
                logger.warning("No results found in API response")
                return []
            
            results = []
            for i, result_data in enumerate(response_data["results"]):
                try:
                    result = SearchResult(
                        url=result_data.get("url", ""),
                        title=result_data.get("title", ""),
                        description=result_data.get("description", ""),
                        rank=i + 1,
                        is_official=result_data.get("is_official", False),
                        confidence_score=result_data.get("confidence_score", 0.0)
                    )
                    
                    # Validate URL
                    if result.url and result.url.startswith(("http://", "https://")):
                        results.append(result)
                    else:
                        logger.warning(f"Invalid URL in result: {result.url}")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse search result {i}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse search results: {e}")
            return []
    
    def _parse_content_analysis(self, url: str, response_text: str, content_size: int) -> ContentAnalysis:
        """Parse content analysis from API response."""
        try:
            # Try to extract JSON from response
            response_data = self._extract_json_from_response(response_text)
            
            if not response_data:
                # Fallback: treat entire response as summary
                return ContentAnalysis(
                    url=url,
                    content_type=ContentType.GENERAL.value,
                    summary=response_text[:1000],
                    key_points=[],
                    technical_specs={},
                    content_size=content_size
                )
            
            return ContentAnalysis(
                url=url,
                content_type=response_data.get("content_type", ContentType.GENERAL.value),
                summary=response_data.get("summary", ""),
                key_points=response_data.get("key_points", []),
                technical_specs=response_data.get("technical_specs", {}),
                content_size=content_size
            )
            
        except Exception as e:
            logger.error(f"Failed to parse content analysis: {e}")
            # Return basic analysis
            return ContentAnalysis(
                url=url,
                content_type=ContentType.GENERAL.value,
                summary="分析に失敗しました",
                key_points=[],
                technical_specs={},
                content_size=content_size
            )
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON data from API response text."""
        try:
            # First, try to parse the entire response as JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON within the response text
        import re
        
        # Look for JSON blocks
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Look for JSON-like structures
        json_pattern = r'\{[^{}]*"results"[^{}]*\[[^\]]*\][^{}]*\}'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        logger.warning("Could not extract JSON from API response")
        return None
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get client usage statistics."""
        return {
            "total_requests": self._request_count,
            "available_models": list(self._model_instances.keys()),
            "configured_models": self.models,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "rate_limit_delay": self.rate_limit_delay
        }