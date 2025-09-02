"""
Search service for handling URL searches using Gemini API.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import re

from .gemini_client import GeminiClient
from .component_search import ComponentSearchEngine
from .result_processor import ResultProcessor
try:
    from src.core.cache_service import get_cache_service
except ImportError:
    # Fallback if cache service is not available
    def get_cache_service():
        return None
from ..models.data_models import (
    SearchResult, SearchRecord, SearchType, SearchFilters
)
from ..models.repository import SearchRepository
from ..utils.error_handler import SearchError, ValidationError


logger = logging.getLogger(__name__)


class SearchService:
    """
    Service for handling search operations.
    
    Provides:
    - General keyword search functionality
    - Component specification search
    - Search result filtering and ranking
    - Search history management
    """
    
    def __init__(
        self, 
        gemini_client: GeminiClient,
        search_repository: SearchRepository,
        max_results: int = 10
    ):
        """
        Initialize SearchService.
        
        Args:
            gemini_client: Gemini API client instance
            search_repository: Repository for search data persistence
            max_results: Maximum number of results to return per search
        """
        self.gemini_client = gemini_client
        self.search_repository = search_repository
        self.max_results = max_results
        self.component_search_engine = ComponentSearchEngine()
        self.result_processor = ResultProcessor()
        self.cache_service = get_cache_service()
        
        logger.info("SearchService initialized")
    
    async def search_general(
        self, 
        keywords: str,
        max_results: Optional[int] = None
    ) -> SearchRecord:
        """
        Perform general keyword search.
        
        Args:
            keywords: Search keywords or phrase
            max_results: Maximum number of results (overrides default)
            
        Returns:
            SearchRecord with search results
            
        Raises:
            ValidationError: If keywords are invalid
            SearchError: If search fails
        """
        # Validate input
        if not keywords or not keywords.strip():
            raise ValidationError("Search keywords cannot be empty")
        
        keywords = keywords.strip()
        if len(keywords) > 500:
            raise ValidationError("Search keywords too long (max 500 characters)")
        
        start_time = time.time()
        results_limit = max_results or self.max_results
        
        try:
            logger.info(f"Starting general search: '{keywords}'")
            
            # Perform search using Gemini API
            raw_results = await self.gemini_client.search_urls(
                query=keywords,
                search_type=SearchType.GENERAL,
                max_results=results_limit
            )
            
            # Apply advanced filtering and ranking
            processed_results = self.result_processor.filter_and_rank_results(
                raw_results, keywords, SearchType.GENERAL, results_limit
            )
            
            # Create search record
            search_time = time.time() - start_time
            search_record = SearchRecord(
                query=keywords,
                search_type=SearchType.GENERAL,
                results_count=len(processed_results),
                search_time=search_time,
                results=processed_results
            )
            
            # Save to database
            search_id = await self.search_repository.save_search_record(search_record)
            search_record.id = search_id
            
            # Update result IDs with search_id
            for result in processed_results:
                result.search_id = search_id
            
            logger.info(
                f"General search completed: '{keywords}' -> {len(processed_results)} results "
                f"in {search_time:.2f}s"
            )
            
            return search_record
            
        except Exception as e:
            search_time = time.time() - start_time
            logger.error(f"General search failed: '{keywords}' -> {str(e)} in {search_time:.2f}s")
            
            if isinstance(e, (ValidationError, SearchError)):
                raise
            else:
                raise SearchError(f"Search failed: {str(e)}")
    
    async def search_component_specs(
        self, 
        manufacturer: str, 
        part_number: str,
        max_results: Optional[int] = None
    ) -> SearchRecord:
        """
        Perform component specification search.
        
        Args:
            manufacturer: Component manufacturer name
            part_number: Component part number
            max_results: Maximum number of results (overrides default)
            
        Returns:
            SearchRecord with search results
            
        Raises:
            ValidationError: If manufacturer or part_number are invalid
            SearchError: If search fails
        """
        # Validate input
        if not manufacturer or not manufacturer.strip():
            raise ValidationError("Manufacturer name cannot be empty")
        if not part_number or not part_number.strip():
            raise ValidationError("Part number cannot be empty")
        
        manufacturer = manufacturer.strip()
        part_number = part_number.strip()
        
        if len(manufacturer) > 100:
            raise ValidationError("Manufacturer name too long (max 100 characters)")
        if len(part_number) > 100:
            raise ValidationError("Part number too long (max 100 characters)")
        
        start_time = time.time()
        results_limit = max_results or self.max_results
        
        try:
            logger.info(f"Starting component search: '{manufacturer}' '{part_number}'")
            
            # Parse component information using specialized engine
            query = f"{manufacturer} {part_number}"
            component_info = self.component_search_engine.parse_component_query(query)
            
            # Build specialized component search prompt
            specialized_prompt = self.component_search_engine.build_component_search_prompt(
                component_info, results_limit
            )
            
            # Perform search using Gemini API with specialized prompt
            raw_results = await self.gemini_client.search_urls(
                query=specialized_prompt,
                search_type=SearchType.COMPONENT,
                max_results=results_limit
            )
            
            # Apply component-specific enhancements first
            enhanced_results = self.component_search_engine.enhance_component_results(
                raw_results, component_info
            )
            
            # Apply advanced filtering and ranking
            processed_results = self.result_processor.filter_and_rank_results(
                enhanced_results, query, SearchType.COMPONENT, results_limit
            )
            
            # Create search record (use original query format for storage)
            original_query = f"{manufacturer} {part_number}"
            search_time = time.time() - start_time
            search_record = SearchRecord(
                query=original_query,
                search_type=SearchType.COMPONENT,
                manufacturer=manufacturer,
                part_number=part_number,
                results_count=len(processed_results),
                search_time=search_time,
                results=processed_results
            )
            
            # Save to database
            search_id = await self.search_repository.save_search_record(search_record)
            search_record.id = search_id
            
            # Update result IDs with search_id
            for result in processed_results:
                result.search_id = search_id
            
            logger.info(
                f"Component search completed: '{manufacturer}' '{part_number}' -> "
                f"{len(processed_results)} results in {search_time:.2f}s"
            )
            
            return search_record
            
        except Exception as e:
            search_time = time.time() - start_time
            logger.error(
                f"Component search failed: '{manufacturer}' '{part_number}' -> "
                f"{str(e)} in {search_time:.2f}s"
            )
            
            if isinstance(e, (ValidationError, SearchError)):
                raise
            else:
                raise SearchError(f"Component search failed: {str(e)}")
    
    def _build_search_prompt(self, query: str, search_type: SearchType) -> str:
        """
        Build search prompt based on query and search type.
        
        Args:
            query: Search query
            search_type: Type of search
            
        Returns:
            Formatted prompt string
        """
        if search_type == SearchType.COMPONENT:
            # Component-specific search prompt
            return f"""
部品検索: {query}

以下の条件で技術仕様書・データシートのURLを検索してください：
1. 公式メーカーサイトを最優先
2. 信頼性の高い技術情報源を選択
3. PDF仕様書やデータシートを優先
4. サードパーティサイトは補助的に使用

検索結果は以下の形式で返してください：
- URL: 実際のリンク
- タイトル: ページまたは文書のタイトル
- 説明: 内容の簡潔な説明
- 公式性: メーカー公式サイトかどうか
- 信頼度: 0.0-1.0のスコア
"""
        else:
            # General search prompt
            return f"""
一般検索: {query}

以下の条件で有用なWebリソースを検索してください：
1. 信頼性の高い情報源を優先
2. 実用的で詳細な情報を含むサイト
3. 最新の情報を提供するサイト
4. 教育的価値の高いコンテンツ

検索結果は以下の形式で返してください：
- URL: 実際のリンク
- タイトル: ページのタイトル
- 説明: 内容の簡潔な説明
- 関連性: クエリとの関連度
- 信頼度: 0.0-1.0のスコア
"""
    
    def _filter_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """
        Filter search results to remove invalid or low-quality entries.
        
        Args:
            results: Raw search results
            query: Original search query
            
        Returns:
            Filtered search results
        """
        filtered = []
        seen_urls = set()
        seen_content_hashes = set()
        
        for result in results:
            # Skip if URL is invalid
            if not self._is_valid_url(result.url):
                logger.debug(f"Skipping invalid URL: {result.url}")
                continue
            
            # Skip duplicates (normalize URL for comparison)
            normalized_url = self._normalize_url(result.url)
            if normalized_url in seen_urls:
                logger.debug(f"Skipping duplicate URL: {result.url}")
                continue
            seen_urls.add(normalized_url)
            
            # Skip near-duplicate content (based on title + description hash)
            content_hash = self._calculate_content_hash(result.title, result.description)
            if content_hash in seen_content_hashes:
                logger.debug(f"Skipping near-duplicate content: {result.title}")
                continue
            seen_content_hashes.add(content_hash)
            
            # Skip if title or description is too short/generic
            if len(result.title) < 3 or len(result.description) < 10:
                logger.debug(f"Skipping low-quality result: {result.title}")
                continue
            
            # Skip obvious spam or irrelevant results
            if self._is_spam_result(result, query):
                logger.debug(f"Skipping spam result: {result.title}")
                continue
            
            # Skip results with poor quality indicators
            if self._has_poor_quality_indicators(result):
                logger.debug(f"Skipping poor quality result: {result.title}")
                continue
            
            filtered.append(result)
        
        logger.debug(f"Filtered {len(results)} -> {len(filtered)} results")
        return filtered
    
    def _rank_results(
        self, 
        results: List[SearchResult], 
        query: str, 
        search_type: SearchType
    ) -> List[SearchResult]:
        """
        Rank and sort search results by relevance and quality.
        
        Args:
            results: Filtered search results
            query: Original search query
            search_type: Type of search performed
            
        Returns:
            Ranked and sorted search results
        """
        if not results:
            return results
        
        # Calculate ranking scores
        for result in results:
            score = self._calculate_relevance_score(result, query, search_type)
            result.confidence_score = score
        
        # Sort by confidence score (descending)
        ranked_results = sorted(results, key=lambda r: r.confidence_score, reverse=True)
        
        # Update rank positions
        for i, result in enumerate(ranked_results):
            result.rank = i + 1
        
        logger.debug(f"Ranked {len(ranked_results)} results")
        return ranked_results
    
    def _prioritize_official_sources(
        self, 
        results: List[SearchResult], 
        manufacturer: str
    ) -> List[SearchResult]:
        """
        Prioritize official manufacturer sources for component searches.
        
        Args:
            results: Ranked search results
            manufacturer: Manufacturer name
            
        Returns:
            Re-ranked results with official sources prioritized
        """
        official_results = []
        other_results = []
        
        for result in results:
            # Use ComponentSearchEngine to check if URL is from official source
            if self.component_search_engine._is_official_manufacturer_source(result.url, manufacturer):
                result.is_official = True
                official_results.append(result)
            else:
                other_results.append(result)
        
        # Combine with official sources first
        prioritized = official_results + other_results
        
        # Update rank positions
        for i, result in enumerate(prioritized):
            result.rank = i + 1
        
        logger.debug(
            f"Prioritized {len(official_results)} official sources for '{manufacturer}'"
        )
        return prioritized
    
    def _parse_component_query(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse a component query to extract manufacturer and part number.
        
        Args:
            query: Component search query
            
        Returns:
            Tuple of (manufacturer, part_number) or (None, None) if parsing fails
        """
        # Clean the query
        query = query.strip()
        
        # Common patterns for component queries
        patterns = [
            # "Manufacturer PartNumber" format
            r'^([A-Za-z][A-Za-z\s&]+?)\s+([A-Za-z0-9\-_/\.]+)$',
            # "Manufacturer: PartNumber" format
            r'^([A-Za-z][A-Za-z\s&]+?):\s*([A-Za-z0-9\-_/\.]+)$',
            # "PartNumber by Manufacturer" format
            r'^([A-Za-z0-9\-_/\.]+)\s+by\s+([A-Za-z][A-Za-z\s&]+?)$',
            # "PartNumber (Manufacturer)" format
            r'^([A-Za-z0-9\-_/\.]+)\s*\(([A-Za-z][A-Za-z\s&]+?)\)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, query, re.IGNORECASE)
            if match:
                if "by" in pattern:
                    # "PartNumber by Manufacturer" format
                    part_number, manufacturer = match.groups()
                else:
                    manufacturer, part_number = match.groups()
                
                # Clean up the extracted values
                manufacturer = manufacturer.strip()
                part_number = part_number.strip()
                
                # Validate extracted values
                if len(manufacturer) > 1 and len(part_number) > 1:
                    return manufacturer, part_number
        
        return None, None
    
    def _enhance_component_search_query(self, manufacturer: str, part_number: str) -> str:
        """
        Enhance component search query with additional search terms.
        
        Args:
            manufacturer: Manufacturer name
            part_number: Part number
            
        Returns:
            Enhanced search query string
        """
        # Base query
        base_query = f"{manufacturer} {part_number}"
        
        # Add common technical document keywords
        tech_keywords = ["datasheet", "specification", "specs", "technical", "manual"]
        
        # Add file type hints
        file_hints = ["PDF", "document"]
        
        # Combine into enhanced query
        enhanced_parts = [base_query]
        enhanced_parts.extend(tech_keywords[:2])  # Add first 2 tech keywords
        enhanced_parts.extend(file_hints[:1])     # Add first file hint
        
        return " ".join(enhanced_parts)
    
    def _calculate_relevance_score(
        self, 
        result: SearchResult, 
        query: str, 
        search_type: SearchType
    ) -> float:
        """
        Calculate relevance score for a search result.
        
        Args:
            result: Search result to score
            query: Original search query
            search_type: Type of search
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        query_lower = query.lower()
        title_lower = result.title.lower()
        desc_lower = result.description.lower()
        url_lower = result.url.lower()
        
        # Base score from API confidence (30% weight)
        score += result.confidence_score * 0.3
        
        # Title relevance (high weight - 25%)
        title_matches = self._count_query_matches(query_lower, title_lower)
        title_score = min(title_matches * 0.05, 0.25)
        
        # Exact phrase matching bonus in title
        if self._has_exact_phrase_match(query_lower, title_lower):
            title_score += 0.1
        
        score += title_score
        
        # Description relevance (medium weight - 15%)
        desc_matches = self._count_query_matches(query_lower, desc_lower)
        desc_score = min(desc_matches * 0.03, 0.15)
        
        # Exact phrase matching bonus in description
        if self._has_exact_phrase_match(query_lower, desc_lower):
            desc_score += 0.05
        
        score += desc_score
        
        # URL relevance (low weight - 10%)
        url_matches = self._count_query_matches(query_lower, url_lower)
        score += min(url_matches * 0.02, 0.1)
        
        # Domain authority and trust signals (15% weight)
        domain_score = self._calculate_domain_authority_score(result.url, search_type)
        score += domain_score * 0.15
        
        # Content type and format bonuses (10% weight)
        content_score = self._calculate_content_type_score(result, search_type)
        score += content_score * 0.1
        
        # Official source bonus (component searches)
        if search_type == SearchType.COMPONENT and result.is_official:
            score += 0.15
        
        # Freshness and quality indicators (5% weight)
        quality_score = self._calculate_quality_score(result)
        score += quality_score * 0.05
        
        # Apply penalties for low-quality indicators
        penalties = self._calculate_penalties(result, query_lower)
        score -= penalties
        
        # Ensure score is within bounds
        return max(0.0, min(1.0, score))
    
    def _count_query_matches(self, query: str, text: str) -> int:
        """Count how many query terms appear in the text."""
        query_terms = set(re.findall(r'\w+', query.lower()))
        text_terms = set(re.findall(r'\w+', text.lower()))
        return len(query_terms.intersection(text_terms))
    
    def _has_exact_phrase_match(self, query: str, text: str) -> bool:
        """Check if query phrase appears exactly in text."""
        # Remove extra whitespace and normalize
        query_clean = re.sub(r'\s+', ' ', query.strip())
        text_clean = re.sub(r'\s+', ' ', text.strip())
        
        return query_clean in text_clean
    
    def _calculate_domain_authority_score(self, url: str, search_type: SearchType) -> float:
        """Calculate domain authority score based on URL characteristics."""
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc
            
            # Remove www prefix
            domain = re.sub(r'^www\.', '', domain)
            
            # High authority domains
            high_authority_domains = {
                # Educational and research
                '.edu', '.ac.', '.org',
                # Government
                '.gov', '.mil',
                # Major tech companies
                'github.com', 'stackoverflow.com', 'microsoft.com', 'google.com',
                # Technical documentation sites
                'readthedocs.io', 'gitbook.io', 'notion.so',
                # Standards organizations
                'ieee.org', 'ietf.org', 'w3.org', 'iso.org'
            }
            
            # Medium authority domains for technical content
            medium_authority_domains = {
                'medium.com', 'dev.to', 'hackernoon.com', 'towards', 'analytics',
                'researchgate.net', 'arxiv.org', 'semanticscholar.org'
            }
            
            # Check for high authority
            for auth_domain in high_authority_domains:
                if auth_domain in domain:
                    return 1.0
            
            # Check for medium authority
            for auth_domain in medium_authority_domains:
                if auth_domain in domain:
                    return 0.7
            
            # Check for HTTPS (security bonus)
            https_bonus = 0.2 if parsed.scheme == 'https' else 0.0
            
            # Check for subdomain structure (often indicates organized content)
            subdomain_bonus = 0.1 if len(domain.split('.')) > 2 else 0.0
            
            return 0.5 + https_bonus + subdomain_bonus
            
        except Exception:
            return 0.5  # Default score
    
    def _calculate_content_type_score(self, result: SearchResult, search_type: SearchType) -> float:
        """Calculate score based on content type indicators."""
        url_lower = result.url.lower()
        title_lower = result.title.lower()
        desc_lower = result.description.lower()
        
        score = 0.0
        
        if search_type == SearchType.COMPONENT:
            # Prefer technical documentation formats
            if any(ext in url_lower for ext in ['.pdf', '.doc', '.docx']):
                score += 0.4
            
            # Technical keywords in title/description
            tech_keywords = ['datasheet', 'specification', 'manual', 'guide', 'reference', 'technical']
            for keyword in tech_keywords:
                if keyword in title_lower or keyword in desc_lower:
                    score += 0.1
                    break
            
            # File type indicators in URL path
            if any(indicator in url_lower for indicator in ['datasheet', 'spec', 'manual', 'doc']):
                score += 0.2
        
        else:  # General search
            # Prefer comprehensive content
            if any(keyword in title_lower for keyword in ['guide', 'tutorial', 'documentation', 'reference']):
                score += 0.3
            
            # Structured content indicators
            if any(indicator in url_lower for indicator in ['docs/', 'documentation/', 'guide/', 'tutorial/']):
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_quality_score(self, result: SearchResult) -> float:
        """Calculate quality score based on various indicators."""
        score = 0.5  # Base score
        
        # Title quality
        title_words = len(result.title.split())
        if 3 <= title_words <= 15:  # Reasonable title length
            score += 0.2
        
        # Description quality
        desc_words = len(result.description.split())
        if 10 <= desc_words <= 50:  # Reasonable description length
            score += 0.2
        
        # Check for professional language patterns
        professional_indicators = [
            r'\b(technical|specification|documentation|official|standard)\b',
            r'\b(version|release|updated|latest)\b',
            r'\b(company|corporation|inc|ltd|llc)\b'
        ]
        
        combined_text = f"{result.title} {result.description}".lower()
        for pattern in professional_indicators:
            if re.search(pattern, combined_text):
                score += 0.1
                break
        
        return min(score, 1.0)
    
    def _calculate_penalties(self, result: SearchResult, query: str) -> float:
        """Calculate penalties for low-quality indicators."""
        penalties = 0.0
        
        url_lower = result.url.lower()
        title_lower = result.title.lower()
        desc_lower = result.description.lower()
        
        # Penalty for commercial/sales content
        commercial_patterns = [
            'buy', 'purchase', 'order', 'cart', 'checkout', 'price', 'cost',
            'sale', 'discount', 'offer', 'deal', 'shop', 'store'
        ]
        
        combined_text = f"{title_lower} {desc_lower}"
        commercial_count = sum(1 for pattern in commercial_patterns if pattern in combined_text)
        penalties += min(commercial_count * 0.05, 0.2)
        
        # Penalty for social media and forums
        social_patterns = ['forum', 'discussion', 'comment', 'reply', 'facebook', 'twitter', 'reddit']
        for pattern in social_patterns:
            if pattern in url_lower or pattern in combined_text:
                penalties += 0.1
                break
        
        # Penalty for file sharing sites
        fileshare_patterns = ['rapidshare', 'mediafire', 'dropbox', 'drive.google']
        for pattern in fileshare_patterns:
            if pattern in url_lower:
                penalties += 0.15
                break
        
        # Penalty for very short or generic content
        if len(result.title) < 10 or len(result.description) < 20:
            penalties += 0.1
        
        return min(penalties, 0.5)  # Cap penalties at 50%
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and accessible."""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for duplicate detection."""
        try:
            parsed = urlparse(url.lower())
            # Remove common tracking parameters
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        except Exception:
            return url.lower()
    
    def _is_spam_result(self, result: SearchResult, query: str) -> bool:
        """Check if result appears to be spam or irrelevant."""
        # Check for common spam indicators
        spam_indicators = [
            'click here', 'free download', 'best price', 'buy now',
            'advertisement', 'sponsored', 'affiliate'
        ]
        
        text_to_check = (result.title + ' ' + result.description).lower()
        
        for indicator in spam_indicators:
            if indicator in text_to_check:
                return True
        
        # Check for excessive repetition
        words = text_to_check.split()
        if len(set(words)) < len(words) * 0.5:  # More than 50% repeated words
            return True
        
        return False
    
    def _calculate_content_hash(self, title: str, description: str) -> str:
        """Calculate a hash for content similarity detection."""
        import hashlib
        
        # Normalize text for comparison
        normalized_title = re.sub(r'[^\w\s]', '', title.lower()).strip()
        normalized_desc = re.sub(r'[^\w\s]', '', description.lower()).strip()
        
        # Create content signature
        content = f"{normalized_title}|{normalized_desc}"
        
        # Use first 100 chars to avoid exact duplicates but catch near-duplicates
        content_sample = content[:100]
        
        return hashlib.md5(content_sample.encode()).hexdigest()
    
    def _has_poor_quality_indicators(self, result: SearchResult) -> bool:
        """Check if result has indicators of poor quality."""
        title_lower = result.title.lower()
        desc_lower = result.description.lower()
        url_lower = result.url.lower()
        
        # Poor quality indicators
        poor_quality_patterns = [
            # Generic or unhelpful titles
            r'^(page|document|file|untitled|no title)',
            r'(404|not found|error|access denied)',
            r'^(home|index|main|default)$',
            
            # Commercial/sales focused (not technical)
            r'(buy now|purchase|order|cart|checkout|price|cost|\$)',
            r'(sale|discount|offer|deal|promotion)',
            r'(shop|store|marketplace|vendor)',
            
            # Low-quality content indicators
            r'(lorem ipsum|placeholder|test|example)',
            r'(under construction|coming soon|maintenance)',
            r'(login|register|sign up|account)',
            
            # Social media and forums (often less reliable)
            r'(facebook|twitter|instagram|linkedin|reddit)',
            r'(forum|discussion|comment|reply|post)',
            
            # File sharing and download sites (often unreliable)
            r'(download|torrent|rapidshare|mediafire)',
            r'(scribd|slideshare|docstoc)'
        ]
        
        combined_text = f"{title_lower} {desc_lower} {url_lower}"
        
        for pattern in poor_quality_patterns:
            if re.search(pattern, combined_text):
                return True
        
        # Check for excessive repetition in title
        title_words = title_lower.split()
        if len(title_words) > 3:
            unique_words = set(title_words)
            if len(unique_words) / len(title_words) < 0.6:  # Less than 60% unique words
                return True
        
        # Check for very short or very long descriptions
        if len(result.description) < 20 or len(result.description) > 500:
            return True
        
        return False
    
    def _is_official_source(self, url: str, manufacturer: str) -> bool:
        """Check if URL appears to be from official manufacturer source."""
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc
            
            # Remove common prefixes
            domain = re.sub(r'^(www\.|m\.)', '', domain)
            
            # Check if manufacturer name is in domain
            manufacturer_clean = re.sub(r'[^a-z0-9]', '', manufacturer.lower())
            
            # Direct match
            if manufacturer_clean in domain:
                return True
            
            # Check for common manufacturer domain patterns
            manufacturer_parts = manufacturer_clean.split()
            if len(manufacturer_parts) > 1:
                # Check if any part of manufacturer name is in domain
                for part in manufacturer_parts:
                    if len(part) > 3 and part in domain:
                        return True
            
            # Known official domains for common manufacturers
            official_domains = {
                'arduino': ['arduino.cc'],
                'raspberry': ['raspberrypi.org', 'raspberrypi.com'],
                'stmicroelectronics': ['st.com'],
                'texas instruments': ['ti.com'],
                'analog devices': ['analog.com'],
                'microchip': ['microchip.com'],
                'intel': ['intel.com'],
                'nvidia': ['nvidia.com'],
                'amd': ['amd.com'],
                'atmel': ['microchip.com'],  # Atmel was acquired by Microchip
                'maxim': ['maximintegrated.com', 'analog.com'],  # Maxim was acquired by Analog Devices
                'linear technology': ['analog.com'],  # Linear Technology was acquired by Analog Devices
                'infineon': ['infineon.com'],
                'nxp': ['nxp.com'],
                'cypress': ['infineon.com'],  # Cypress was acquired by Infineon
                'freescale': ['nxp.com'],  # Freescale was acquired by NXP
                'broadcom': ['broadcom.com'],
                'qualcomm': ['qualcomm.com'],
                'marvell': ['marvell.com'],
                'renesas': ['renesas.com'],
                'rohm': ['rohm.com'],
                'toshiba': ['toshiba.com'],
                'panasonic': ['panasonic.com'],
                'sony': ['sony.com'],
                'samsung': ['samsung.com'],
                'lg': ['lge.com'],
                'fairchild': ['onsemi.com'],  # Fairchild was acquired by ON Semiconductor
                'on semiconductor': ['onsemi.com'],
                'vishay': ['vishay.com'],
                'murata': ['murata.com'],
                'tdk': ['tdk.com'],
                'kemet': ['kemet.com'],
                'avx': ['avx.com'],
                'yageo': ['yageo.com'],
                'bourns': ['bourns.com'],
                'te connectivity': ['te.com'],
                'molex': ['molex.com'],
                'amphenol': ['amphenol.com'],
                'jst': ['jst.com'],
                'hirose': ['hirose.com'],
                'samtec': ['samtec.com'],
                'harwin': ['harwin.com'],
                'phoenix contact': ['phoenixcontact.com'],
                'wago': ['wago.com'],
                'wurth': ['we-online.com'],
                'coilcraft': ['coilcraft.com'],
                'pulse': ['pulseelectronics.com'],
                'epcos': ['tdk.com'],  # EPCOS was acquired by TDK
                'littelfuse': ['littelfuse.com'],
                'schurter': ['schurter.com'],
                'bel fuse': ['belfuse.com'],
                'traco': ['tracopower.com'],
                'mean well': ['meanwell.com'],
                'cui': ['cuidevices.com'],
                'recom': ['recom-power.com'],
                'xp power': ['xppower.com'],
                'artesyn': ['artesyn.com'],
                'vicor': ['vicorpower.com'],
                'delta': ['deltapsu.com'],
                'cincon': ['cincon.com'],
                'minmax': ['minmaxtechnology.com']
            }
            
            for mfg, domains in official_domains.items():
                if mfg in manufacturer.lower():
                    for official_domain in domains:
                        if official_domain in domain:
                            return True
            
            # Check for common official domain patterns
            # Many manufacturers use their name directly in domain
            manufacturer_words = re.findall(r'\w+', manufacturer.lower())
            for word in manufacturer_words:
                if len(word) > 4:  # Only check meaningful words
                    if word in domain and not any(generic in domain for generic in ['forum', 'wiki', 'blog', 'store']):
                        return True
            
            return False
            
        except Exception:
            return False
    
    async def get_search_history(
        self, 
        filters: Optional[SearchFilters] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SearchRecord]:
        """
        Get search history with optional filtering.
        
        Args:
            filters: Optional search filters
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of search records
        """
        try:
            return await self.search_repository.get_search_history(
                filters=filters,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Failed to get search history: {e}")
            raise SearchError(f"Failed to retrieve search history: {str(e)}")
    
    async def get_search_by_id(self, search_id: int) -> Optional[SearchRecord]:
        """
        Get specific search record by ID.
        
        Args:
            search_id: Search record ID
            
        Returns:
            SearchRecord if found, None otherwise
        """
        try:
            return await self.search_repository.get_search_by_id(search_id)
        except Exception as e:
            logger.error(f"Failed to get search {search_id}: {e}")
            raise SearchError(f"Failed to retrieve search: {str(e)}")
    
    async def search_intelligent(
        self, 
        query: str,
        max_results: Optional[int] = None
    ) -> SearchRecord:
        """
        Perform intelligent search that automatically detects search type.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            SearchRecord with search results
        """
        # Try to parse as component query first
        manufacturer, part_number = self._parse_component_query(query)
        
        if manufacturer and part_number:
            logger.info(f"Detected component query: '{manufacturer}' + '{part_number}'")
            return await self.search_component_specs(manufacturer, part_number, max_results)
        else:
            logger.info(f"Using general search for: '{query}'")
            return await self.search_general(query, max_results)
    
    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search service statistics.
        
        Returns:
            Dictionary with service statistics
        """
        return {
            'max_results': self.max_results,
            'gemini_stats': self.gemini_client.get_usage_stats(),
            'processor_stats': self.result_processor.get_processing_stats()
        }