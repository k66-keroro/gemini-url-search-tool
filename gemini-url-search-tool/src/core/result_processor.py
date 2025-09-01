"""
Advanced result processing for search result filtering and ranking.
"""

import re
import logging
from typing import List, Dict, Any, Set, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass
from datetime import datetime

from ..models.data_models import SearchResult, SearchType


logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for search results."""
    relevance_score: float
    authority_score: float
    freshness_score: float
    technical_score: float
    overall_score: float


class ResultProcessor:
    """
    Advanced processor for search result filtering and ranking.
    
    Provides:
    - Quality-based filtering
    - Duplicate detection and removal
    - Multi-factor ranking algorithm
    - Content type classification
    """
    
    def __init__(self):
        """Initialize result processor."""
        self.spam_patterns = self._load_spam_patterns()
        self.quality_indicators = self._load_quality_indicators()
        self.authority_domains = self._load_authority_domains()
        
        logger.info("ResultProcessor initialized")
    
    def filter_and_rank_results(
        self, 
        results: List[SearchResult], 
        query: str,
        search_type: SearchType,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Apply comprehensive filtering and ranking to search results.
        
        Args:
            results: Raw search results
            query: Original search query
            search_type: Type of search performed
            max_results: Maximum number of results to return
            
        Returns:
            Filtered and ranked search results
        """
        if not results:
            return results
        
        logger.info(f"Processing {len(results)} results for query: '{query}'")
        
        # Step 1: Remove invalid and low-quality results
        filtered_results = self._filter_invalid_results(results)
        logger.debug(f"After invalid filtering: {len(filtered_results)} results")
        
        # Step 2: Remove duplicates
        deduplicated_results = self._remove_duplicates(filtered_results)
        logger.debug(f"After deduplication: {len(deduplicated_results)} results")
        
        # Step 3: Filter spam and low-quality content
        quality_filtered = self._filter_spam_and_low_quality(deduplicated_results, query)
        logger.debug(f"After quality filtering: {len(quality_filtered)} results")
        
        # Step 4: Calculate quality metrics for each result
        scored_results = self._calculate_quality_metrics(quality_filtered, query, search_type)
        
        # Step 5: Rank by overall quality score
        ranked_results = self._rank_by_quality(scored_results)
        
        # Step 6: Apply final result limit
        final_results = ranked_results[:max_results]
        
        # Step 7: Update rank positions
        for i, result in enumerate(final_results):
            result.rank = i + 1
        
        logger.info(f"Final results: {len(final_results)} high-quality results")
        return final_results
    
    def _filter_invalid_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Filter out results with invalid URLs or missing content."""
        filtered = []
        
        for result in results:
            # Check URL validity
            if not self._is_valid_url(result.url):
                logger.debug(f"Filtered invalid URL: {result.url}")
                continue
            
            # Check minimum content requirements
            if not result.title or len(result.title.strip()) < 3:
                logger.debug(f"Filtered result with insufficient title: {result.title}")
                continue
            
            if not result.description or len(result.description.strip()) < 10:
                logger.debug(f"Filtered result with insufficient description")
                continue
            
            filtered.append(result)
        
        return filtered
    
    def _remove_duplicates(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate URLs with intelligent merging."""
        seen_urls: Dict[str, SearchResult] = {}
        
        for result in results:
            normalized_url = self._normalize_url(result.url)
            
            if normalized_url in seen_urls:
                # Keep the result with higher confidence or better content
                existing = seen_urls[normalized_url]
                if self._is_better_result(result, existing):
                    seen_urls[normalized_url] = result
                    logger.debug(f"Replaced duplicate with better result: {result.url}")
            else:
                seen_urls[normalized_url] = result
        
        return list(seen_urls.values())
    
    def _filter_spam_and_low_quality(
        self, 
        results: List[SearchResult], 
        query: str
    ) -> List[SearchResult]:
        """Filter out spam and low-quality results."""
        filtered = []
        
        for result in results:
            # Check for spam patterns
            if self._is_spam_result(result):
                logger.debug(f"Filtered spam result: {result.title}")
                continue
            
            # Check content quality
            if not self._meets_quality_threshold(result, query):
                logger.debug(f"Filtered low-quality result: {result.title}")
                continue
            
            filtered.append(result)
        
        return filtered
    
    def _calculate_quality_metrics(
        self, 
        results: List[SearchResult], 
        query: str,
        search_type: SearchType
    ) -> List[Tuple[SearchResult, QualityMetrics]]:
        """Calculate comprehensive quality metrics for each result."""
        scored_results = []
        
        for result in results:
            metrics = QualityMetrics(
                relevance_score=self._calculate_relevance_score(result, query),
                authority_score=self._calculate_authority_score(result),
                freshness_score=self._calculate_freshness_score(result),
                technical_score=self._calculate_technical_score(result, search_type),
                overall_score=0.0  # Will be calculated below
            )
            
            # Calculate weighted overall score
            metrics.overall_score = self._calculate_overall_score(metrics, search_type)
            
            # Update result confidence score
            result.confidence_score = metrics.overall_score
            
            scored_results.append((result, metrics))
        
        return scored_results
    
    def _rank_by_quality(
        self, 
        scored_results: List[Tuple[SearchResult, QualityMetrics]]
    ) -> List[SearchResult]:
        """Rank results by overall quality score."""
        # Sort by overall score (descending)
        sorted_results = sorted(
            scored_results, 
            key=lambda x: x[1].overall_score, 
            reverse=True
        )
        
        return [result for result, metrics in sorted_results]
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and accessible."""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc and parsed.scheme in ['http', 'https'])
        except Exception:
            return False
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for duplicate detection."""
        try:
            parsed = urlparse(url.lower())
            
            # Remove common tracking parameters
            path = parsed.path.rstrip('/')
            
            # Remove www prefix
            netloc = parsed.netloc
            if netloc.startswith('www.'):
                netloc = netloc[4:]
            
            return f"{parsed.scheme}://{netloc}{path}"
        except Exception:
            return url.lower()
    
    def _is_better_result(self, result1: SearchResult, result2: SearchResult) -> bool:
        """Determine which result is better when handling duplicates."""
        # Prefer official sources
        if result1.is_official and not result2.is_official:
            return True
        if result2.is_official and not result1.is_official:
            return False
        
        # Prefer higher confidence
        if result1.confidence_score > result2.confidence_score:
            return True
        if result2.confidence_score > result1.confidence_score:
            return False
        
        # Prefer longer, more detailed descriptions
        if len(result1.description) > len(result2.description):
            return True
        
        return False
    
    def _is_spam_result(self, result: SearchResult) -> bool:
        """Check if result appears to be spam."""
        text_to_check = f"{result.title} {result.description} {result.url}".lower()
        
        # Check against spam patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, text_to_check):
                return True
        
        # Check for excessive repetition
        words = text_to_check.split()
        if len(words) > 10:
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)
            if repetition_ratio < 0.4:  # More than 60% repeated words
                return True
        
        # Check for suspicious URL patterns
        if self._has_suspicious_url_patterns(result.url):
            return True
        
        return False
    
    def _meets_quality_threshold(self, result: SearchResult, query: str) -> bool:
        """Check if result meets minimum quality threshold."""
        # Check title quality
        title_words = len(result.title.split())
        if title_words < 2 or title_words > 50:
            return False
        
        # Check description quality
        desc_words = len(result.description.split())
        if desc_words < 5 or desc_words > 200:
            return False
        
        # Check for minimum relevance
        query_terms = set(query.lower().split())
        result_terms = set((result.title + " " + result.description).lower().split())
        
        if query_terms and result_terms:
            overlap = len(query_terms.intersection(result_terms))
            relevance_ratio = overlap / len(query_terms)
            if relevance_ratio < 0.1:  # Less than 10% term overlap
                return False
        
        return True
    
    def _calculate_relevance_score(self, result: SearchResult, query: str) -> float:
        """Calculate relevance score based on query matching."""
        query_terms = set(re.findall(r'\w+', query.lower()))
        
        if not query_terms:
            return 0.0
        
        title_terms = set(re.findall(r'\w+', result.title.lower()))
        desc_terms = set(re.findall(r'\w+', result.description.lower()))
        url_terms = set(re.findall(r'\w+', result.url.lower()))
        
        # Calculate term overlap scores
        title_overlap = len(query_terms.intersection(title_terms)) / len(query_terms)
        desc_overlap = len(query_terms.intersection(desc_terms)) / len(query_terms)
        url_overlap = len(query_terms.intersection(url_terms)) / len(query_terms)
        
        # Weighted relevance score
        relevance_score = (
            title_overlap * 0.5 +      # Title has highest weight
            desc_overlap * 0.3 +       # Description has medium weight
            url_overlap * 0.2          # URL has lowest weight
        )
        
        return min(1.0, relevance_score)
    
    def _calculate_authority_score(self, result: SearchResult) -> float:
        """Calculate authority score based on domain reputation."""
        try:
            domain = urlparse(result.url).netloc.lower()
            domain = domain.replace('www.', '')
            
            # Check against known authority domains
            for authority_domain, score in self.authority_domains.items():
                if authority_domain in domain:
                    return score
            
            # Check for official source indicators
            if result.is_official:
                return 0.9
            
            # Check for educational/government domains
            if any(tld in domain for tld in ['.edu', '.gov', '.org']):
                return 0.7
            
            # Default score for unknown domains
            return 0.5
            
        except Exception:
            return 0.3
    
    def _calculate_freshness_score(self, result: SearchResult) -> float:
        """Calculate freshness score (placeholder - would need actual date info)."""
        # This would ideally use actual publication/modification dates
        # For now, return a neutral score
        return 0.5
    
    def _calculate_technical_score(self, result: SearchResult, search_type: SearchType) -> float:
        """Calculate technical relevance score."""
        score = 0.0
        
        text_to_check = f"{result.title} {result.description} {result.url}".lower()
        
        if search_type == SearchType.COMPONENT:
            # Technical indicators for component searches
            technical_terms = [
                'datasheet', 'specification', 'manual', 'technical', 'pdf',
                'schematic', 'pinout', 'electrical', 'mechanical', 'thermal'
            ]
            
            for term in technical_terms:
                if term in text_to_check:
                    score += 0.1
            
            # File type bonuses
            if '.pdf' in result.url.lower():
                score += 0.2
            
        else:
            # General technical quality indicators
            quality_terms = [
                'documentation', 'guide', 'tutorial', 'reference',
                'official', 'specification', 'standard'
            ]
            
            for term in quality_terms:
                if term in text_to_check:
                    score += 0.05
        
        return min(1.0, score)
    
    def _calculate_overall_score(
        self, 
        metrics: QualityMetrics, 
        search_type: SearchType
    ) -> float:
        """Calculate weighted overall quality score."""
        if search_type == SearchType.COMPONENT:
            # For component searches, prioritize technical content and authority
            weights = {
                'relevance': 0.25,
                'authority': 0.35,
                'freshness': 0.10,
                'technical': 0.30
            }
        else:
            # For general searches, balance all factors
            weights = {
                'relevance': 0.35,
                'authority': 0.25,
                'freshness': 0.15,
                'technical': 0.25
            }
        
        overall_score = (
            metrics.relevance_score * weights['relevance'] +
            metrics.authority_score * weights['authority'] +
            metrics.freshness_score * weights['freshness'] +
            metrics.technical_score * weights['technical']
        )
        
        return min(1.0, overall_score)
    
    def _has_suspicious_url_patterns(self, url: str) -> bool:
        """Check for suspicious URL patterns that might indicate spam."""
        suspicious_patterns = [
            r'\.tk$', r'\.ml$', r'\.ga$',  # Suspicious TLDs
            r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',  # IP addresses
            r'[a-z0-9]{20,}',  # Very long random strings
            r'(bit\.ly|tinyurl|t\.co)',  # URL shorteners
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, url.lower()):
                return True
        
        return False
    
    def _load_spam_patterns(self) -> List[str]:
        """Load spam detection patterns."""
        return [
            r'\b(click here|free download|buy now|best price)\b',
            r'\b(advertisement|sponsored|affiliate)\b',
            r'\b(casino|poker|viagra|cialis)\b',
            r'\$\d+.*\b(discount|sale|offer)\b',
            r'\b(limited time|act now|hurry)\b',
        ]
    
    def _load_quality_indicators(self) -> List[str]:
        """Load quality content indicators."""
        return [
            'documentation', 'specification', 'manual', 'guide',
            'tutorial', 'reference', 'official', 'technical',
            'datasheet', 'whitepaper', 'standard', 'protocol'
        ]
    
    def _load_authority_domains(self) -> Dict[str, float]:
        """Load authority domain scores."""
        return {
            # Technical documentation sites
            'github.com': 0.8,
            'stackoverflow.com': 0.8,
            'docs.python.org': 0.9,
            'developer.mozilla.org': 0.9,
            
            # Component manufacturer sites
            'arduino.cc': 0.9,
            'raspberrypi.org': 0.9,
            'ti.com': 0.9,
            'st.com': 0.9,
            'microchip.com': 0.9,
            'analog.com': 0.9,
            'intel.com': 0.9,
            'nvidia.com': 0.9,
            
            # Distributor sites
            'digikey.com': 0.8,
            'mouser.com': 0.8,
            'rs-online.com': 0.8,
            'farnell.com': 0.8,
            
            # Educational sites
            'mit.edu': 0.9,
            'stanford.edu': 0.9,
            'ieee.org': 0.9,
            
            # Standards organizations
            'iso.org': 0.9,
            'iec.ch': 0.9,
            'nist.gov': 0.9,
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            'spam_patterns_count': len(self.spam_patterns),
            'quality_indicators_count': len(self.quality_indicators),
            'authority_domains_count': len(self.authority_domains)
        }