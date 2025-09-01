"""
Specialized component search functionality for electronic parts and specifications.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

from ..models.data_models import SearchResult, SearchType


logger = logging.getLogger(__name__)


@dataclass
class ComponentInfo:
    """Information extracted from component search query."""
    manufacturer: str
    part_number: str
    category: Optional[str] = None
    package_type: Optional[str] = None
    specifications: Dict[str, str] = None
    
    def __post_init__(self):
        if self.specifications is None:
            self.specifications = {}


class ComponentSearchEngine:
    """
    Specialized search engine for electronic components.
    
    Provides enhanced search capabilities for:
    - Component datasheets and specifications
    - Official manufacturer documentation
    - Technical reference materials
    """
    
    def __init__(self):
        """Initialize component search engine."""
        self.manufacturer_domains = self._load_manufacturer_domains()
        self.component_patterns = self._load_component_patterns()
        
        logger.info("ComponentSearchEngine initialized")
    
    def parse_component_query(self, query: str) -> ComponentInfo:
        """
        Parse component search query to extract structured information.
        
        Args:
            query: Raw search query string
            
        Returns:
            ComponentInfo with extracted details
        """
        # Clean and normalize query
        query = query.strip()
        
        # Try to extract manufacturer and part number
        manufacturer, part_number = self._extract_manufacturer_part(query)
        
        # Extract additional component information
        category = self._extract_component_category(query)
        package_type = self._extract_package_type(query)
        specifications = self._extract_specifications(query)
        
        return ComponentInfo(
            manufacturer=manufacturer,
            part_number=part_number,
            category=category,
            package_type=package_type,
            specifications=specifications
        )
    
    def build_component_search_prompt(self, component_info: ComponentInfo, max_results: int = 10) -> str:
        """
        Build specialized search prompt for component specifications.
        
        Args:
            component_info: Parsed component information
            max_results: Maximum number of results to request
            
        Returns:
            Formatted search prompt for Gemini API
        """
        manufacturer = component_info.manufacturer
        part_number = component_info.part_number
        
        # Build comprehensive search prompt
        prompt = f"""
電子部品検索: {manufacturer} {part_number}

以下の優先順位で技術仕様書・データシートを検索してください：

1. 公式メーカーサイト（最優先）
   - {manufacturer}の公式ウェブサイト
   - 公式データシート（PDF形式）
   - 公式技術仕様書
   - 公式アプリケーションノート

2. 信頼性の高い技術情報源
   - 認定代理店のサイト
   - 技術データベース（Digi-Key, Mouser, RS Components等）
   - 標準化団体の資料

3. 検索対象ファイル形式
   - PDF データシート
   - 技術仕様書
   - アプリケーションノート
   - リファレンスデザイン

検索結果は以下の形式でJSONで返してください：
{{
  "results": [
    {{
      "url": "実際のURL",
      "title": "文書タイトル",
      "description": "内容の説明",
      "is_official": true/false,
      "confidence_score": 0.0-1.0,
      "document_type": "datasheet/specification/application_note/reference"
    }}
  ]
}}

最大{max_results}件の結果を返してください。
公式ソースを最優先し、PDFファイルを優先してください。
"""
        
        # Add category-specific search terms if available
        if component_info.category:
            prompt += f"\n部品カテゴリ: {component_info.category}"
        
        if component_info.package_type:
            prompt += f"\nパッケージタイプ: {component_info.package_type}"
        
        if component_info.specifications:
            specs_text = ", ".join([f"{k}: {v}" for k, v in component_info.specifications.items()])
            prompt += f"\n仕様: {specs_text}"
        
        return prompt
    
    def enhance_component_results(
        self, 
        results: List[SearchResult], 
        component_info: ComponentInfo
    ) -> List[SearchResult]:
        """
        Enhance search results with component-specific scoring and filtering.
        
        Args:
            results: Raw search results
            component_info: Component information for context
            
        Returns:
            Enhanced and re-ranked search results
        """
        enhanced_results = []
        
        for result in results:
            # Create enhanced copy
            enhanced_result = SearchResult(
                url=result.url,
                title=result.title,
                description=result.description,
                rank=result.rank,
                is_official=result.is_official,
                confidence_score=result.confidence_score,
                search_id=result.search_id,
                id=result.id,
                created_at=result.created_at
            )
            
            # Apply component-specific enhancements
            enhanced_result.is_official = self._is_official_manufacturer_source(
                result.url, component_info.manufacturer
            )
            
            # Recalculate confidence score with component-specific factors
            enhanced_result.confidence_score = self._calculate_component_confidence(
                result, component_info
            )
            
            enhanced_results.append(enhanced_result)
        
        # Sort by enhanced confidence score
        enhanced_results.sort(key=lambda r: r.confidence_score, reverse=True)
        
        # Update ranks
        for i, result in enumerate(enhanced_results):
            result.rank = i + 1
        
        return enhanced_results
    
    def _extract_manufacturer_part(self, query: str) -> Tuple[str, str]:
        """Extract manufacturer and part number from query."""
        # Common patterns for manufacturer + part number
        patterns = [
            # "Manufacturer PartNumber" format
            r'^([A-Za-z][A-Za-z\s&]+?)\s+([A-Z0-9][A-Z0-9\-_\.]+)$',
            # "Manufacturer-PartNumber" format
            r'^([A-Za-z][A-Za-z\s&]+?)-([A-Z0-9][A-Z0-9\-_\.]+)$',
            # "PartNumber by Manufacturer" format
            r'^([A-Z0-9][A-Z0-9\-_\.]+)\s+(?:by|from)\s+([A-Za-z][A-Za-z\s&]+?)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, query.strip(), re.IGNORECASE)
            if match:
                if 'by' in pattern or 'from' in pattern:
                    # Part number comes first in this pattern
                    return match.group(2).strip(), match.group(1).strip()
                else:
                    # Manufacturer comes first
                    return match.group(1).strip(), match.group(2).strip()
        
        # Fallback: split on first space and assume manufacturer + part
        parts = query.strip().split(None, 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            return query.strip(), ""
    
    def _extract_component_category(self, query: str) -> Optional[str]:
        """Extract component category from query."""
        categories = {
            'microcontroller': ['mcu', 'microcontroller', 'micro controller'],
            'sensor': ['sensor', 'accelerometer', 'gyroscope', 'temperature'],
            'ic': ['ic', 'integrated circuit', 'chip'],
            'resistor': ['resistor', 'resistance'],
            'capacitor': ['capacitor', 'cap'],
            'inductor': ['inductor', 'coil'],
            'diode': ['diode', 'led'],
            'transistor': ['transistor', 'mosfet', 'bjt'],
            'connector': ['connector', 'header', 'socket'],
            'crystal': ['crystal', 'oscillator', 'xtal']
        }
        
        query_lower = query.lower()
        for category, keywords in categories.items():
            if any(keyword in query_lower for keyword in keywords):
                return category
        
        return None
    
    def _extract_package_type(self, query: str) -> Optional[str]:
        """Extract package type from query."""
        packages = [
            'dip', 'sop', 'soic', 'ssop', 'tssop', 'qfp', 'qfn', 'bga',
            'lga', 'smd', 'smt', 'through-hole', 'surface-mount'
        ]
        
        query_lower = query.lower()
        for package in packages:
            if package in query_lower:
                return package.upper()
        
        return None
    
    def _extract_specifications(self, query: str) -> Dict[str, str]:
        """Extract technical specifications from query."""
        specs = {}
        
        # Voltage patterns
        voltage_match = re.search(r'(\d+(?:\.\d+)?)\s*v(?:olt)?', query, re.IGNORECASE)
        if voltage_match:
            specs['voltage'] = f"{voltage_match.group(1)}V"
        
        # Current patterns
        current_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ma|amp|a)', query, re.IGNORECASE)
        if current_match:
            specs['current'] = current_match.group(0)
        
        # Frequency patterns
        freq_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:mhz|khz|ghz|hz)', query, re.IGNORECASE)
        if freq_match:
            specs['frequency'] = freq_match.group(0)
        
        # Temperature patterns
        temp_match = re.search(r'(-?\d+(?:\.\d+)?)\s*°?c', query, re.IGNORECASE)
        if temp_match:
            specs['temperature'] = f"{temp_match.group(1)}°C"
        
        return specs
    
    def _is_official_manufacturer_source(self, url: str, manufacturer: str) -> bool:
        """Check if URL is from official manufacturer source."""
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc.replace('www.', '')
            
            manufacturer_lower = manufacturer.lower()
            
            # Direct domain match
            if manufacturer_lower in domain:
                return True
            
            # Check known manufacturer domains
            if manufacturer_lower in self.manufacturer_domains:
                official_domains = self.manufacturer_domains[manufacturer_lower]
                return any(official_domain in domain for official_domain in official_domains)
            
            # Check for common manufacturer domain patterns
            manufacturer_clean = re.sub(r'[^a-z0-9]', '', manufacturer_lower)
            if manufacturer_clean in domain:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _calculate_component_confidence(
        self, 
        result: SearchResult, 
        component_info: ComponentInfo
    ) -> float:
        """Calculate component-specific confidence score."""
        score = result.confidence_score * 0.4  # Base score from API
        
        url_lower = result.url.lower()
        title_lower = result.title.lower()
        desc_lower = result.description.lower()
        
        # Manufacturer name matching
        manufacturer_lower = component_info.manufacturer.lower()
        if manufacturer_lower in title_lower:
            score += 0.2
        if manufacturer_lower in desc_lower:
            score += 0.1
        if manufacturer_lower in url_lower:
            score += 0.1
        
        # Part number matching
        part_lower = component_info.part_number.lower()
        if part_lower in title_lower:
            score += 0.2
        if part_lower in desc_lower:
            score += 0.1
        
        # Official source bonus
        if result.is_official:
            score += 0.3
        
        # Document type bonuses
        if any(term in url_lower for term in ['datasheet', 'spec', '.pdf']):
            score += 0.2
        
        if any(term in title_lower for term in ['datasheet', 'specification', 'manual']):
            score += 0.15
        
        # Category matching bonus
        if component_info.category:
            category_lower = component_info.category.lower()
            if category_lower in title_lower or category_lower in desc_lower:
                score += 0.1
        
        # Penalty for non-technical sources
        if any(term in url_lower for term in ['forum', 'blog', 'wiki', 'reddit']):
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _load_manufacturer_domains(self) -> Dict[str, List[str]]:
        """Load known manufacturer domain mappings."""
        return {
            'arduino': ['arduino.cc'],
            'raspberry pi': ['raspberrypi.org', 'raspberrypi.com'],
            'stmicroelectronics': ['st.com'],
            'texas instruments': ['ti.com'],
            'analog devices': ['analog.com'],
            'microchip': ['microchip.com'],
            'intel': ['intel.com'],
            'nvidia': ['nvidia.com'],
            'amd': ['amd.com'],
            'infineon': ['infineon.com'],
            'nxp': ['nxp.com'],
            'maxim': ['maximintegrated.com', 'analog.com'],
            'linear technology': ['analog.com'],
            'atmel': ['microchip.com'],
            'freescale': ['nxp.com'],
            'cypress': ['infineon.com'],
            'broadcom': ['broadcom.com'],
            'qualcomm': ['qualcomm.com'],
            'renesas': ['renesas.com'],
            'rohm': ['rohm.com'],
            'toshiba': ['toshiba-semicon.com'],
            'panasonic': ['panasonic.com'],
            'murata': ['murata.com'],
            'tdk': ['tdk.com'],
            'vishay': ['vishay.com'],
            'bourns': ['bourns.com'],
            'yageo': ['yageo.com']
        }
    
    def _load_component_patterns(self) -> Dict[str, List[str]]:
        """Load component identification patterns."""
        return {
            'microcontroller_prefixes': ['PIC', 'ATMEGA', 'STM32', 'ESP', 'ARM'],
            'sensor_suffixes': ['SENSOR', 'ACCEL', 'GYRO', 'TEMP'],
            'package_types': ['DIP', 'SOP', 'QFP', 'BGA', 'QFN', 'SOIC'],
            'voltage_regulators': ['LM', 'LP', 'TPS', 'AMS'],
            'op_amps': ['LM', 'TL', 'AD', 'OPA']
        }