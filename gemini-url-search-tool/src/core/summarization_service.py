"""
Specialized summarization service for Gemini URL Search Tool.

Provides enhanced content summarization and technical specification extraction.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models.data_models import ContentAnalysis, ContentType, SearchResult
from ..utils.error_handler import ContentProcessingError
from .content_service import ContentService
from .gemini_client import GeminiClient


logger = logging.getLogger(__name__)


class SummarizationFocus(Enum):
    """Focus areas for summarization."""
    GENERAL = "general"
    TECHNICAL_SPECS = "technical_specs"
    KEY_FEATURES = "key_features"
    USAGE_INSTRUCTIONS = "usage_instructions"
    COMPATIBILITY = "compatibility"
    PERFORMANCE = "performance"


@dataclass
class SummarizationRequest:
    """Request for content summarization."""
    url: str
    content_type: ContentType
    focus_areas: List[SummarizationFocus]
    max_summary_length: int = 1000
    extract_technical_specs: bool = True
    include_key_points: bool = True
    language: str = "ja"  # Japanese by default


@dataclass
class TechnicalSpecification:
    """Structured technical specification."""
    category: str
    parameter: str
    value: str
    unit: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category,
            "parameter": self.parameter,
            "value": self.value,
            "unit": self.unit,
            "notes": self.notes
        }


@dataclass
class EnhancedSummary:
    """Enhanced summary with structured information."""
    url: str
    content_type: str
    executive_summary: str
    key_points: List[str]
    technical_specifications: List[TechnicalSpecification]
    usage_information: Dict[str, Any]
    compatibility_info: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    extraction_confidence: float
    processing_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "content_type": self.content_type,
            "executive_summary": self.executive_summary,
            "key_points": self.key_points,
            "technical_specifications": [spec.to_dict() for spec in self.technical_specifications],
            "usage_information": self.usage_information,
            "compatibility_info": self.compatibility_info,
            "performance_metrics": self.performance_metrics,
            "extraction_confidence": self.extraction_confidence,
            "processing_time": self.processing_time
        }


class SummarizationService:
    """
    Advanced summarization service for content analysis.
    
    Provides specialized functionality for:
    - Structured content summarization (要件 2.2)
    - Technical specification extraction (要件 3.3)
    - Multi-focus summarization
    - Quality assessment and confidence scoring
    """
    
    def __init__(self, content_service: ContentService, gemini_client: GeminiClient):
        """
        Initialize SummarizationService.
        
        Args:
            content_service: ContentService instance for basic content processing
            gemini_client: GeminiClient for advanced API interactions
        """
        self.content_service = content_service
        self.gemini_client = gemini_client
        
        # Technical specification categories for structured extraction
        self.tech_spec_categories = {
            "electrical": ["voltage", "current", "power", "frequency", "resistance", "capacitance"],
            "physical": ["dimensions", "weight", "size", "length", "width", "height", "diameter"],
            "environmental": ["temperature", "humidity", "pressure", "vibration", "shock"],
            "performance": ["speed", "accuracy", "resolution", "bandwidth", "latency", "throughput"],
            "interface": ["connector", "protocol", "communication", "pin", "signal"],
            "mechanical": ["torque", "force", "material", "finish", "mounting"]
        }
        
        # Focus area prompts in Japanese
        self.focus_prompts = {
            SummarizationFocus.GENERAL: "全般的な概要と主要な特徴",
            SummarizationFocus.TECHNICAL_SPECS: "技術仕様と性能パラメータ",
            SummarizationFocus.KEY_FEATURES: "主要機能と特徴",
            SummarizationFocus.USAGE_INSTRUCTIONS: "使用方法と操作手順",
            SummarizationFocus.COMPATIBILITY: "互換性と対応環境",
            SummarizationFocus.PERFORMANCE: "性能と効率"
        }
        
        logger.info("SummarizationService initialized")
    
    async def create_enhanced_summary(
        self, 
        url: str, 
        request: SummarizationRequest
    ) -> EnhancedSummary:
        """
        Create an enhanced summary with structured information extraction.
        
        Args:
            url: URL to analyze
            request: Summarization request parameters
            
        Returns:
            EnhancedSummary with structured information
            
        Raises:
            ContentProcessingError: If summarization fails
        """
        start_time = time.time()
        
        try:
            # First, fetch and analyze content using ContentService
            content = await self.content_service.fetch_content(url)
            content_type = self.content_service.detect_content_type(url, content)
            
            # Get basic analysis
            basic_analysis = await self.content_service.extract_key_info(url, content, content_type)
            
            # Create enhanced summary based on focus areas
            executive_summary = await self._create_executive_summary(
                content, content_type, request.focus_areas, request.max_summary_length
            )
            
            # Extract structured technical specifications
            tech_specs = []
            if request.extract_technical_specs and content_type in [ContentType.SPECIFICATION, ContentType.DATASHEET]:
                tech_specs = await self._extract_structured_specifications(content, url)
            
            # Extract usage and compatibility information
            usage_info = await self._extract_usage_information(content, content_type)
            compatibility_info = await self._extract_compatibility_information(content, content_type)
            performance_metrics = await self._extract_performance_metrics(content, content_type)
            
            # Calculate extraction confidence
            confidence = self._calculate_extraction_confidence(
                basic_analysis, tech_specs, usage_info, compatibility_info
            )
            
            processing_time = time.time() - start_time
            
            enhanced_summary = EnhancedSummary(
                url=url,
                content_type=content_type.value,
                executive_summary=executive_summary,
                key_points=basic_analysis.key_points,
                technical_specifications=tech_specs,
                usage_information=usage_info,
                compatibility_info=compatibility_info,
                performance_metrics=performance_metrics,
                extraction_confidence=confidence,
                processing_time=processing_time
            )
            
            logger.info(
                f"Enhanced summary created: url={url}, confidence={confidence:.2f}, "
                f"specs_count={len(tech_specs)}, time={processing_time:.2f}s"
            )
            
            return enhanced_summary
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Enhanced summarization failed for {url}: {str(e)}"
            logger.error(f"{error_msg}, time={processing_time:.2f}s")
            raise ContentProcessingError(error_msg)
    
    async def summarize_search_results(
        self, 
        search_results: List[SearchResult],
        focus_areas: List[SummarizationFocus] = None
    ) -> Dict[str, Any]:
        """
        Create summaries for multiple search results.
        
        Args:
            search_results: List of search results to summarize
            focus_areas: Optional focus areas for summarization
            
        Returns:
            Dictionary with summarization results
        """
        if focus_areas is None:
            focus_areas = [SummarizationFocus.GENERAL]
        
        summaries = []
        failed_urls = []
        
        for result in search_results:
            try:
                request = SummarizationRequest(
                    url=result.url,
                    content_type=ContentType.GENERAL,  # Will be detected automatically
                    focus_areas=focus_areas,
                    max_summary_length=500  # Shorter for multiple results
                )
                
                summary = await self.create_enhanced_summary(result.url, request)
                summaries.append({
                    "search_result": result.to_dict(),
                    "summary": summary.to_dict()
                })
                
            except Exception as e:
                logger.warning(f"Failed to summarize {result.url}: {e}")
                failed_urls.append(result.url)
        
        return {
            "summaries": summaries,
            "successful_count": len(summaries),
            "failed_count": len(failed_urls),
            "failed_urls": failed_urls,
            "focus_areas": [focus.value for focus in focus_areas]
        }
    
    async def _create_executive_summary(
        self, 
        content: str, 
        content_type: ContentType,
        focus_areas: List[SummarizationFocus],
        max_length: int
    ) -> str:
        """
        Create an executive summary focused on specific areas.
        
        Args:
            content: Content to summarize
            content_type: Type of content
            focus_areas: Areas to focus on
            max_length: Maximum summary length
            
        Returns:
            Executive summary text
        """
        # Build focus-specific prompt
        focus_descriptions = [self.focus_prompts[focus] for focus in focus_areas]
        focus_text = "、".join(focus_descriptions)
        
        prompt = f"""
以下のコンテンツについて、{focus_text}に焦点を当てた要約を{max_length}文字以内で作成してください。

コンテンツタイプ: {content_type.value}
コンテンツ:
{content[:8000]}  # Limit content length

要約は以下の構造で作成してください：
1. 概要（何についての文書か）
2. 主要なポイント（{focus_text}に関連する重要な情報）
3. 実用的な情報（使用者にとって有用な具体的な情報）

簡潔で分かりやすい日本語で要約してください。
"""
        
        try:
            summary = await self.gemini_client.summarize_content(
                content=prompt,
                max_length=max_length
            )
            return summary
        except Exception as e:
            logger.warning(f"Executive summary creation failed: {e}")
            # Fallback to basic summary
            return await self.content_service.generate_summary(content, max_length=max_length)
    
    async def _extract_structured_specifications(
        self, 
        content: str, 
        url: str
    ) -> List[TechnicalSpecification]:
        """
        Extract structured technical specifications from content.
        
        Args:
            content: Content to analyze
            url: Source URL
            
        Returns:
            List of structured technical specifications
        """
        prompt = f"""
以下の技術文書から技術仕様を構造化して抽出してください。

コンテンツ:
{content[:8000]}

以下の形式でJSONレスポンスを返してください：
{{
  "specifications": [
    {{
      "category": "electrical/physical/environmental/performance/interface/mechanical",
      "parameter": "パラメータ名",
      "value": "値",
      "unit": "単位（あれば）",
      "notes": "補足情報（あれば）"
    }}
  ]
}}

可能な限り多くの技術仕様を抽出し、数値と単位を正確に記録してください。
カテゴリは electrical, physical, environmental, performance, interface, mechanical のいずれかを使用してください。
"""
        
        try:
            response = await self.gemini_client._make_request_with_fallback(prompt)
            
            if response.success:
                data = self.gemini_client._extract_json_from_response(response.data)
                
                if data and "specifications" in data:
                    specs = []
                    for spec_data in data["specifications"]:
                        try:
                            spec = TechnicalSpecification(
                                category=spec_data.get("category", "general"),
                                parameter=spec_data.get("parameter", ""),
                                value=spec_data.get("value", ""),
                                unit=spec_data.get("unit"),
                                notes=spec_data.get("notes")
                            )
                            specs.append(spec)
                        except Exception as e:
                            logger.warning(f"Failed to parse specification: {e}")
                            continue
                    
                    return specs
            
            return []
            
        except Exception as e:
            logger.warning(f"Structured specification extraction failed for {url}: {e}")
            return []
    
    async def _extract_usage_information(
        self, 
        content: str, 
        content_type: ContentType
    ) -> Dict[str, Any]:
        """
        Extract usage and application information.
        
        Args:
            content: Content to analyze
            content_type: Type of content
            
        Returns:
            Dictionary with usage information
        """
        if content_type == ContentType.GENERAL:
            return {}
        
        prompt = f"""
以下の技術文書から使用方法と応用に関する情報を抽出してください。

コンテンツ:
{content[:6000]}

以下の形式でJSONレスポンスを返してください：
{{
  "applications": ["用途1", "用途2"],
  "setup_instructions": ["手順1", "手順2"],
  "operating_conditions": {{
    "temperature": "動作温度範囲",
    "power": "電源要件",
    "environment": "環境条件"
  }},
  "precautions": ["注意事項1", "注意事項2"]
}}

使用方法、応用例、動作条件、注意事項に関する情報を抽出してください。
"""
        
        try:
            response = await self.gemini_client._make_request_with_fallback(prompt)
            
            if response.success:
                data = self.gemini_client._extract_json_from_response(response.data)
                return data or {}
            
            return {}
            
        except Exception as e:
            logger.warning(f"Usage information extraction failed: {e}")
            return {}
    
    async def _extract_compatibility_information(
        self, 
        content: str, 
        content_type: ContentType
    ) -> Dict[str, Any]:
        """
        Extract compatibility and interface information.
        
        Args:
            content: Content to analyze
            content_type: Type of content
            
        Returns:
            Dictionary with compatibility information
        """
        if content_type == ContentType.GENERAL:
            return {}
        
        prompt = f"""
以下の技術文書から互換性とインターフェースに関する情報を抽出してください。

コンテンツ:
{content[:6000]}

以下の形式でJSONレスポンスを返してください：
{{
  "compatible_systems": ["対応システム1", "対応システム2"],
  "interfaces": ["インターフェース1", "インターフェース2"],
  "protocols": ["プロトコル1", "プロトコル2"],
  "software_requirements": {{
    "os": "対応OS",
    "drivers": "必要ドライバ",
    "software": "必要ソフトウェア"
  }},
  "hardware_requirements": ["ハードウェア要件1", "ハードウェア要件2"]
}}

互換性、対応システム、インターフェース、必要な環境に関する情報を抽出してください。
"""
        
        try:
            response = await self.gemini_client._make_request_with_fallback(prompt)
            
            if response.success:
                data = self.gemini_client._extract_json_from_response(response.data)
                return data or {}
            
            return {}
            
        except Exception as e:
            logger.warning(f"Compatibility information extraction failed: {e}")
            return {}
    
    async def _extract_performance_metrics(
        self, 
        content: str, 
        content_type: ContentType
    ) -> Dict[str, Any]:
        """
        Extract performance metrics and benchmarks.
        
        Args:
            content: Content to analyze
            content_type: Type of content
            
        Returns:
            Dictionary with performance metrics
        """
        if content_type == ContentType.GENERAL:
            return {}
        
        prompt = f"""
以下の技術文書から性能指標とベンチマークに関する情報を抽出してください。

コンテンツ:
{content[:6000]}

以下の形式でJSONレスポンスを返してください：
{{
  "speed_metrics": {{
    "processing_speed": "処理速度",
    "response_time": "応答時間",
    "throughput": "スループット"
  }},
  "accuracy_metrics": {{
    "precision": "精度",
    "resolution": "分解能",
    "error_rate": "エラー率"
  }},
  "efficiency_metrics": {{
    "power_consumption": "消費電力",
    "efficiency": "効率",
    "heat_generation": "発熱"
  }},
  "benchmarks": ["ベンチマーク1", "ベンチマーク2"]
}}

性能、速度、精度、効率に関する数値データを抽出してください。
"""
        
        try:
            response = await self.gemini_client._make_request_with_fallback(prompt)
            
            if response.success:
                data = self.gemini_client._extract_json_from_response(response.data)
                return data or {}
            
            return {}
            
        except Exception as e:
            logger.warning(f"Performance metrics extraction failed: {e}")
            return {}
    
    def _calculate_extraction_confidence(
        self,
        basic_analysis: ContentAnalysis,
        tech_specs: List[TechnicalSpecification],
        usage_info: Dict[str, Any],
        compatibility_info: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for information extraction.
        
        Args:
            basic_analysis: Basic content analysis
            tech_specs: Extracted technical specifications
            usage_info: Usage information
            compatibility_info: Compatibility information
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.0
        
        # Base score from summary quality
        if basic_analysis.summary and len(basic_analysis.summary) > 50:
            score += 0.3
        
        # Score from key points
        if basic_analysis.key_points and len(basic_analysis.key_points) >= 3:
            score += 0.2
        
        # Score from technical specifications
        if tech_specs:
            spec_score = min(len(tech_specs) / 10.0, 0.3)  # Max 0.3 for specs
            score += spec_score
        
        # Score from usage information
        if usage_info and any(usage_info.values()):
            score += 0.1
        
        # Score from compatibility information
        if compatibility_info and any(compatibility_info.values()):
            score += 0.1
        
        return min(score, 1.0)
    
    def get_summarization_stats(self) -> Dict[str, Any]:
        """
        Get summarization service statistics.
        
        Returns:
            Dictionary with service statistics
        """
        return {
            "tech_spec_categories": list(self.tech_spec_categories.keys()),
            "focus_areas": list(self.focus_prompts.keys()),
            "supported_content_types": [ct.value for ct in ContentType],
            "max_content_length": 8000
        }