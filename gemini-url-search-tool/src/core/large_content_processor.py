"""
Large content processing service for Gemini URL Search Tool.

Handles content size limitations and chunk processing with summary quality optimization.
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import math

from ..models.data_models import ContentAnalysis, ContentType
from ..utils.error_handler import ContentProcessingError
from .content_service import ContentService
from .summarization_service import SummarizationService, SummarizationRequest, SummarizationFocus
from .gemini_client import GeminiClient


logger = logging.getLogger(__name__)


class ContentPriority(Enum):
    """Priority levels for content sections."""
    CRITICAL = "critical"      # Must include (titles, specs, key info)
    HIGH = "high"             # Should include (important details)
    MEDIUM = "medium"         # Nice to include (supporting info)
    LOW = "low"              # Can skip (filler content)


@dataclass
class ContentChunk:
    """Represents a chunk of content with metadata."""
    content: str
    priority: ContentPriority
    section_type: str  # e.g., "title", "specification", "description"
    position: int      # Original position in document
    size: int         # Character count
    importance_score: float  # 0.0 to 1.0
    
    def __post_init__(self):
        """Calculate size after initialization."""
        self.size = len(self.content)


@dataclass
class ProcessingStrategy:
    """Strategy for processing large content."""
    max_total_size: int
    chunk_size: int
    overlap_size: int
    priority_threshold: float  # Minimum importance score to include
    max_chunks: int
    preserve_structure: bool
    focus_areas: List[SummarizationFocus]


@dataclass
class OptimizedSummary:
    """Optimized summary for large content."""
    original_size: int
    processed_size: int
    chunks_processed: int
    chunks_skipped: int
    summary: str
    key_points: List[str]
    technical_specs: Dict[str, Any]
    quality_score: float
    processing_time: float
    strategy_used: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "original_size": self.original_size,
            "processed_size": self.processed_size,
            "chunks_processed": self.chunks_processed,
            "chunks_skipped": self.chunks_skipped,
            "summary": self.summary,
            "key_points": self.key_points,
            "technical_specs": self.technical_specs,
            "quality_score": self.quality_score,
            "processing_time": self.processing_time,
            "strategy_used": self.strategy_used
        }


class LargeContentProcessor:
    """
    Specialized processor for large content with quality optimization.
    
    Implements:
    - Content size limitations and chunking (要件 2.4)
    - Summary quality optimization for large content
    - Intelligent content prioritization
    - Adaptive processing strategies
    """
    
    def __init__(
        self, 
        content_service: ContentService,
        summarization_service: SummarizationService,
        gemini_client: GeminiClient
    ):
        """
        Initialize LargeContentProcessor.
        
        Args:
            content_service: ContentService for basic processing
            summarization_service: SummarizationService for advanced summarization
            gemini_client: GeminiClient for API interactions
        """
        self.content_service = content_service
        self.summarization_service = summarization_service
        self.gemini_client = gemini_client
        
        # Processing limits and thresholds
        self.size_thresholds = {
            "small": 5000,      # Process normally
            "medium": 20000,    # Use basic chunking
            "large": 50000,     # Use intelligent chunking
            "huge": 200000      # Use aggressive optimization
        }
        
        # Default processing strategies
        self.strategies = {
            "conservative": ProcessingStrategy(
                max_total_size=50000,
                chunk_size=8000,
                overlap_size=500,
                priority_threshold=0.3,
                max_chunks=10,
                preserve_structure=True,
                focus_areas=[SummarizationFocus.GENERAL]
            ),
            "balanced": ProcessingStrategy(
                max_total_size=30000,
                chunk_size=6000,
                overlap_size=300,
                priority_threshold=0.5,
                max_chunks=8,
                preserve_structure=True,
                focus_areas=[SummarizationFocus.GENERAL, SummarizationFocus.KEY_FEATURES]
            ),
            "aggressive": ProcessingStrategy(
                max_total_size=15000,
                chunk_size=4000,
                overlap_size=200,
                priority_threshold=0.7,
                max_chunks=5,
                preserve_structure=False,
                focus_areas=[SummarizationFocus.KEY_FEATURES, SummarizationFocus.TECHNICAL_SPECS]
            )
        }
        
        # Content section patterns for importance scoring
        self.section_patterns = {
            "title": [r"^#+ ", r"<h[1-6]", r"^\s*[A-Z][^.]*:?\s*$"],
            "specification": [r"仕様", r"spec", r"parameter", r"技術", r"性能"],
            "feature": [r"特徴", r"feature", r"機能", r"function"],
            "usage": [r"使用", r"用途", r"application", r"usage"],
            "compatibility": [r"対応", r"互換", r"compatible", r"support"],
            "performance": [r"性能", r"performance", r"速度", r"speed"]
        }
        
        logger.info("LargeContentProcessor initialized")
    
    async def process_large_content(
        self, 
        url: str, 
        content: str,
        content_type: ContentType,
        strategy_name: str = "balanced"
    ) -> OptimizedSummary:
        """
        Process large content with optimization for summary quality.
        
        Args:
            url: Source URL
            content: Large content to process
            content_type: Type of content
            strategy_name: Processing strategy to use
            
        Returns:
            OptimizedSummary with optimized results
            
        Raises:
            ContentProcessingError: If processing fails
        """
        start_time = time.time()
        original_size = len(content)
        
        try:
            # Determine processing strategy based on content size
            if strategy_name not in self.strategies:
                strategy_name = self._select_optimal_strategy(original_size)
            
            strategy = self.strategies[strategy_name]
            
            logger.info(
                f"Processing large content: url={url}, size={original_size}, "
                f"strategy={strategy_name}"
            )
            
            # Analyze and chunk content intelligently
            chunks = await self._create_intelligent_chunks(content, content_type, strategy)
            
            # Select most important chunks
            selected_chunks = self._select_priority_chunks(chunks, strategy)
            
            # Process selected chunks
            processed_content = self._combine_chunks(selected_chunks)
            processed_size = len(processed_content)
            
            # Generate optimized summary
            summary_result = await self._generate_optimized_summary(
                url, processed_content, content_type, strategy
            )
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                original_size, processed_size, len(selected_chunks), len(chunks), summary_result
            )
            
            processing_time = time.time() - start_time
            
            optimized_summary = OptimizedSummary(
                original_size=original_size,
                processed_size=processed_size,
                chunks_processed=len(selected_chunks),
                chunks_skipped=len(chunks) - len(selected_chunks),
                summary=summary_result.get("summary", ""),
                key_points=summary_result.get("key_points", []),
                technical_specs=summary_result.get("technical_specs", {}),
                quality_score=quality_score,
                processing_time=processing_time,
                strategy_used=strategy_name
            )
            
            logger.info(
                f"Large content processing completed: url={url}, "
                f"compression={processed_size/original_size:.2f}, "
                f"quality={quality_score:.2f}, time={processing_time:.2f}s"
            )
            
            return optimized_summary
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Large content processing failed for {url}: {str(e)}"
            logger.error(f"{error_msg}, time={processing_time:.2f}s")
            raise ContentProcessingError(error_msg)
    
    async def adaptive_process_content(
        self, 
        url: str, 
        content: str,
        content_type: ContentType,
        target_quality: float = 0.8
    ) -> OptimizedSummary:
        """
        Adaptively process content to achieve target quality.
        
        Args:
            url: Source URL
            content: Content to process
            content_type: Type of content
            target_quality: Target quality score (0.0 to 1.0)
            
        Returns:
            OptimizedSummary with best achievable quality
        """
        original_size = len(content)
        
        # If content is small enough, use normal processing
        if original_size <= self.size_thresholds["small"]:
            basic_analysis = await self.content_service.extract_key_info(url, content, content_type)
            return OptimizedSummary(
                original_size=original_size,
                processed_size=original_size,
                chunks_processed=1,
                chunks_skipped=0,
                summary=basic_analysis.summary,
                key_points=basic_analysis.key_points,
                technical_specs=basic_analysis.technical_specs,
                quality_score=1.0,  # Full content processed
                processing_time=basic_analysis.extraction_time,
                strategy_used="normal"
            )
        
        # Try different strategies to achieve target quality
        strategies_to_try = ["conservative", "balanced", "aggressive"]
        best_result = None
        
        for strategy_name in strategies_to_try:
            try:
                result = await self.process_large_content(url, content, content_type, strategy_name)
                
                if result.quality_score >= target_quality:
                    return result
                
                if best_result is None or result.quality_score > best_result.quality_score:
                    best_result = result
                    
            except Exception as e:
                logger.warning(f"Strategy {strategy_name} failed: {e}")
                continue
        
        if best_result is None:
            raise ContentProcessingError(f"All processing strategies failed for {url}")
        
        return best_result
    
    def _select_optimal_strategy(self, content_size: int) -> str:
        """
        Select optimal processing strategy based on content size.
        
        Args:
            content_size: Size of content in characters
            
        Returns:
            Strategy name
        """
        if content_size <= self.size_thresholds["medium"]:
            return "conservative"
        elif content_size <= self.size_thresholds["large"]:
            return "balanced"
        else:
            return "aggressive"
    
    async def _create_intelligent_chunks(
        self, 
        content: str, 
        content_type: ContentType,
        strategy: ProcessingStrategy
    ) -> List[ContentChunk]:
        """
        Create intelligent chunks with importance scoring.
        
        Args:
            content: Content to chunk
            content_type: Type of content
            strategy: Processing strategy
            
        Returns:
            List of ContentChunk objects with importance scores
        """
        # First, split content into logical sections
        sections = self._split_into_sections(content)
        
        chunks = []
        position = 0
        
        for section in sections:
            # Determine section type and priority
            section_type = self._classify_section(section)
            priority = self._determine_priority(section_type, content_type)
            
            # Calculate importance score
            importance_score = await self._calculate_importance_score(
                section, section_type, content_type
            )
            
            # Split large sections into smaller chunks if needed
            if len(section) > strategy.chunk_size:
                sub_chunks = self._split_section_into_chunks(section, strategy.chunk_size, strategy.overlap_size)
                for i, sub_chunk in enumerate(sub_chunks):
                    chunk = ContentChunk(
                        content=sub_chunk,
                        priority=priority,
                        section_type=section_type,
                        position=position + i,
                        size=len(sub_chunk),
                        importance_score=importance_score * (1.0 - i * 0.1)  # Decrease score for later chunks
                    )
                    chunks.append(chunk)
                position += len(sub_chunks)
            else:
                chunk = ContentChunk(
                    content=section,
                    priority=priority,
                    section_type=section_type,
                    position=position,
                    size=len(section),
                    importance_score=importance_score
                )
                chunks.append(chunk)
                position += 1
        
        return chunks
    
    def _split_into_sections(self, content: str) -> List[str]:
        """
        Split content into logical sections.
        
        Args:
            content: Content to split
            
        Returns:
            List of content sections
        """
        # Split by common section delimiters
        section_delimiters = [
            r'\n\s*#{1,6}\s+',  # Markdown headers
            r'\n\s*[A-Z][^.]*:\s*\n',  # Colon-terminated headers
            r'\n\s*\d+\.\s+',  # Numbered sections
            r'\n\s*[•·▪▫]\s+',  # Bullet points
            r'\n\s*[-*]\s+',   # Dash/asterisk bullets
        ]
        
        sections = [content]
        
        for delimiter in section_delimiters:
            new_sections = []
            for section in sections:
                parts = re.split(delimiter, section)
                new_sections.extend([part.strip() for part in parts if part.strip()])
            sections = new_sections
        
        # Filter out very short sections
        sections = [s for s in sections if len(s) > 50]
        
        return sections
    
    def _classify_section(self, section: str) -> str:
        """
        Classify a content section by type.
        
        Args:
            section: Content section to classify
            
        Returns:
            Section type string
        """
        section_lower = section.lower()
        
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, section_lower):
                    return section_type
        
        return "general"
    
    def _determine_priority(self, section_type: str, content_type: ContentType) -> ContentPriority:
        """
        Determine priority level for a section type.
        
        Args:
            section_type: Type of section
            content_type: Overall content type
            
        Returns:
            ContentPriority level
        """
        if content_type in [ContentType.SPECIFICATION, ContentType.DATASHEET]:
            priority_map = {
                "title": ContentPriority.CRITICAL,
                "specification": ContentPriority.CRITICAL,
                "feature": ContentPriority.HIGH,
                "performance": ContentPriority.HIGH,
                "usage": ContentPriority.MEDIUM,
                "compatibility": ContentPriority.MEDIUM,
                "general": ContentPriority.LOW
            }
        else:
            priority_map = {
                "title": ContentPriority.CRITICAL,
                "feature": ContentPriority.HIGH,
                "usage": ContentPriority.HIGH,
                "specification": ContentPriority.MEDIUM,
                "performance": ContentPriority.MEDIUM,
                "compatibility": ContentPriority.LOW,
                "general": ContentPriority.LOW
            }
        
        return priority_map.get(section_type, ContentPriority.LOW)
    
    async def _calculate_importance_score(
        self, 
        section: str, 
        section_type: str,
        content_type: ContentType
    ) -> float:
        """
        Calculate importance score for a content section.
        
        Args:
            section: Content section
            section_type: Type of section
            content_type: Overall content type
            
        Returns:
            Importance score between 0.0 and 1.0
        """
        score = 0.0
        
        # Base score from section type
        type_scores = {
            "title": 0.9,
            "specification": 0.8,
            "feature": 0.7,
            "performance": 0.7,
            "usage": 0.6,
            "compatibility": 0.5,
            "general": 0.3
        }
        score += type_scores.get(section_type, 0.3)
        
        # Adjust based on content type
        if content_type in [ContentType.SPECIFICATION, ContentType.DATASHEET]:
            if section_type in ["specification", "performance"]:
                score += 0.1
        
        # Score based on content characteristics
        section_lower = section.lower()
        
        # Technical terms boost
        tech_terms = ["voltage", "current", "frequency", "temperature", "dimension", "interface"]
        tech_count = sum(1 for term in tech_terms if term in section_lower)
        score += min(tech_count * 0.05, 0.2)
        
        # Numbers and units boost (indicates specifications)
        number_pattern = r'\d+\.?\d*\s*[a-zA-Z]+\b'
        number_count = len(re.findall(number_pattern, section))
        score += min(number_count * 0.03, 0.15)
        
        # Length penalty for very long sections
        if len(section) > 2000:
            score *= 0.9
        
        return min(score, 1.0)
    
    def _select_priority_chunks(
        self, 
        chunks: List[ContentChunk], 
        strategy: ProcessingStrategy
    ) -> List[ContentChunk]:
        """
        Select the most important chunks based on strategy.
        
        Args:
            chunks: List of all chunks
            strategy: Processing strategy
            
        Returns:
            List of selected chunks
        """
        # Filter by importance threshold
        candidate_chunks = [
            chunk for chunk in chunks 
            if chunk.importance_score >= strategy.priority_threshold
        ]
        
        # Sort by importance score (descending)
        candidate_chunks.sort(key=lambda x: x.importance_score, reverse=True)
        
        # Select chunks within size and count limits
        selected_chunks = []
        total_size = 0
        
        for chunk in candidate_chunks:
            if (len(selected_chunks) < strategy.max_chunks and 
                total_size + chunk.size <= strategy.max_total_size):
                selected_chunks.append(chunk)
                total_size += chunk.size
            else:
                break
        
        # If preserving structure, sort by original position
        if strategy.preserve_structure:
            selected_chunks.sort(key=lambda x: x.position)
        
        return selected_chunks
    
    def _split_section_into_chunks(
        self, 
        section: str, 
        chunk_size: int, 
        overlap_size: int
    ) -> List[str]:
        """
        Split a large section into overlapping chunks.
        
        Args:
            section: Section to split
            chunk_size: Maximum chunk size
            overlap_size: Overlap between chunks
            
        Returns:
            List of chunk strings
        """
        if len(section) <= chunk_size:
            return [section]
        
        chunks = []
        start = 0
        
        while start < len(section):
            end = min(start + chunk_size, len(section))
            
            # Try to break at sentence boundaries
            if end < len(section):
                # Look for sentence endings within the last 200 characters
                search_start = max(end - 200, start)
                sentence_end = -1
                
                for delimiter in ['. ', '。', '! ', '！', '? ', '？']:
                    pos = section.rfind(delimiter, search_start, end)
                    if pos > sentence_end:
                        sentence_end = pos + len(delimiter)
                
                if sentence_end > start:
                    end = sentence_end
            
            chunk = section[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(end - overlap_size, start + 1)
            
            if start >= len(section):
                break
        
        return chunks
    
    def _combine_chunks(self, chunks: List[ContentChunk]) -> str:
        """
        Combine selected chunks into a single content string.
        
        Args:
            chunks: List of chunks to combine
            
        Returns:
            Combined content string
        """
        if not chunks:
            return ""
        
        # Group chunks by section type for better organization
        sections = {}
        for chunk in chunks:
            if chunk.section_type not in sections:
                sections[chunk.section_type] = []
            sections[chunk.section_type].append(chunk)
        
        # Combine in priority order
        priority_order = ["title", "specification", "feature", "performance", "usage", "compatibility", "general"]
        combined_parts = []
        
        for section_type in priority_order:
            if section_type in sections:
                section_chunks = sections[section_type]
                section_chunks.sort(key=lambda x: x.position)  # Maintain order within section
                
                section_content = "\n\n".join(chunk.content for chunk in section_chunks)
                combined_parts.append(section_content)
        
        return "\n\n".join(combined_parts)
    
    async def _generate_optimized_summary(
        self, 
        url: str, 
        content: str, 
        content_type: ContentType,
        strategy: ProcessingStrategy
    ) -> Dict[str, Any]:
        """
        Generate optimized summary for processed content.
        
        Args:
            url: Source URL
            content: Processed content
            content_type: Content type
            strategy: Processing strategy
            
        Returns:
            Dictionary with summary results
        """
        try:
            # Use SummarizationService for enhanced summarization
            request = SummarizationRequest(
                url=url,
                content_type=content_type,
                focus_areas=strategy.focus_areas,
                max_summary_length=800,  # Slightly shorter for large content
                extract_technical_specs=True,
                include_key_points=True
            )
            
            enhanced_summary = await self.summarization_service.create_enhanced_summary(url, request)
            
            return {
                "summary": enhanced_summary.executive_summary,
                "key_points": enhanced_summary.key_points,
                "technical_specs": {
                    spec.parameter: spec.value 
                    for spec in enhanced_summary.technical_specifications
                }
            }
            
        except Exception as e:
            logger.warning(f"Enhanced summarization failed, using basic approach: {e}")
            
            # Fallback to basic summarization
            basic_analysis = await self.content_service.extract_key_info(url, content, content_type)
            
            return {
                "summary": basic_analysis.summary,
                "key_points": basic_analysis.key_points,
                "technical_specs": basic_analysis.technical_specs
            }
    
    def _calculate_quality_score(
        self, 
        original_size: int, 
        processed_size: int,
        chunks_processed: int, 
        total_chunks: int,
        summary_result: Dict[str, Any]
    ) -> float:
        """
        Calculate quality score for the processing result.
        
        Args:
            original_size: Original content size
            processed_size: Processed content size
            chunks_processed: Number of chunks processed
            total_chunks: Total number of chunks
            summary_result: Summary generation result
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0
        
        # Content coverage score (0.4 weight)
        coverage_ratio = processed_size / original_size if original_size > 0 else 0
        coverage_score = min(coverage_ratio * 2, 1.0)  # Up to 50% coverage gets full score
        score += coverage_score * 0.4
        
        # Chunk selection score (0.3 weight)
        chunk_ratio = chunks_processed / total_chunks if total_chunks > 0 else 0
        chunk_score = min(chunk_ratio * 3, 1.0)  # Up to 33% chunks gets full score
        score += chunk_score * 0.3
        
        # Summary quality score (0.3 weight)
        summary_quality = 0.0
        
        if summary_result.get("summary") and len(summary_result["summary"]) > 100:
            summary_quality += 0.4
        
        if summary_result.get("key_points") and len(summary_result["key_points"]) >= 3:
            summary_quality += 0.3
        
        if summary_result.get("technical_specs") and len(summary_result["technical_specs"]) > 0:
            summary_quality += 0.3
        
        score += summary_quality * 0.3
        
        return min(score, 1.0)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics and configuration.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            "size_thresholds": self.size_thresholds,
            "available_strategies": list(self.strategies.keys()),
            "section_types": list(self.section_patterns.keys()),
            "priority_levels": [p.value for p in ContentPriority]
        }