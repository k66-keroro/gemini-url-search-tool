"""
Data models for Gemini URL Search Tool.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class SearchType(Enum):
    """Search type enumeration."""
    GENERAL = "general"
    COMPONENT = "component"


class ContentType(Enum):
    """Content type enumeration."""
    GENERAL = "general"
    SPECIFICATION = "specification"
    DATASHEET = "datasheet"


@dataclass
class SearchResult:
    """Represents a single search result."""
    url: str
    title: str
    description: str
    rank: int
    is_official: bool = False
    confidence_score: float = 0.0
    search_id: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'search_id': self.search_id,
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'rank': self.rank,
            'is_official': self.is_official,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Create instance from dictionary."""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        return cls(
            id=data.get('id'),
            search_id=data.get('search_id'),
            url=data['url'],
            title=data['title'],
            description=data['description'],
            rank=data['rank'],
            is_official=data.get('is_official', False),
            confidence_score=data.get('confidence_score', 0.0),
            created_at=created_at
        )


@dataclass
class ContentAnalysis:
    """Represents content analysis results."""
    url: str
    content_type: str
    summary: str
    key_points: List[str] = field(default_factory=list)
    technical_specs: Dict[str, Any] = field(default_factory=dict)
    extraction_time: float = 0.0
    content_size: int = 0
    result_id: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'result_id': self.result_id,
            'url': self.url,
            'content_type': self.content_type,
            'summary': self.summary,
            'key_points': self.key_points,
            'technical_specs': self.technical_specs,
            'extraction_time': self.extraction_time,
            'content_size': self.content_size,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentAnalysis':
        """Create instance from dictionary."""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        return cls(
            id=data.get('id'),
            result_id=data.get('result_id'),
            url=data['url'],
            content_type=data['content_type'],
            summary=data['summary'],
            key_points=data.get('key_points', []),
            technical_specs=data.get('technical_specs', {}),
            extraction_time=data.get('extraction_time', 0.0),
            content_size=data.get('content_size', 0),
            created_at=created_at
        )


@dataclass
class SearchRecord:
    """Represents a search history record."""
    query: str
    search_type: SearchType
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    results_count: int = 0
    search_time: float = 0.0
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    results: List[SearchResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'query': self.query,
            'search_type': self.search_type.value,
            'manufacturer': self.manufacturer,
            'part_number': self.part_number,
            'results_count': self.results_count,
            'search_time': self.search_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'results': [result.to_dict() for result in self.results]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchRecord':
        """Create instance from dictionary."""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        results = []
        if data.get('results'):
            results = [SearchResult.from_dict(r) for r in data['results']]
        
        return cls(
            id=data.get('id'),
            query=data['query'],
            search_type=SearchType(data['search_type']),
            manufacturer=data.get('manufacturer'),
            part_number=data.get('part_number'),
            results_count=data.get('results_count', 0),
            search_time=data.get('search_time', 0.0),
            created_at=created_at,
            results=results
        )


@dataclass
class UserEvaluation:
    """Represents user evaluation of content."""
    content_id: int
    usefulness_rating: int  # 1-5 scale
    accuracy_rating: int    # 1-5 scale
    feedback: Optional[str] = None
    time_saved_minutes: int = 0
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate ratings after initialization."""
        if not (1 <= self.usefulness_rating <= 5):
            raise ValueError("usefulness_rating must be between 1 and 5")
        if not (1 <= self.accuracy_rating <= 5):
            raise ValueError("accuracy_rating must be between 1 and 5")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'content_id': self.content_id,
            'usefulness_rating': self.usefulness_rating,
            'accuracy_rating': self.accuracy_rating,
            'feedback': self.feedback,
            'time_saved_minutes': self.time_saved_minutes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserEvaluation':
        """Create instance from dictionary."""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        return cls(
            id=data.get('id'),
            content_id=data['content_id'],
            usefulness_rating=data['usefulness_rating'],
            accuracy_rating=data['accuracy_rating'],
            feedback=data.get('feedback'),
            time_saved_minutes=data.get('time_saved_minutes', 0),
            created_at=created_at
        )


@dataclass
class SearchMetrics:
    """Represents search performance metrics."""
    total_searches: int
    avg_search_time: float
    success_rate: float
    avg_usefulness_rating: float
    avg_accuracy_rating: float
    time_saved_total: int
    general_searches: int = 0
    component_searches: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_searches': self.total_searches,
            'avg_search_time': self.avg_search_time,
            'success_rate': self.success_rate,
            'avg_usefulness_rating': self.avg_usefulness_rating,
            'avg_accuracy_rating': self.avg_accuracy_rating,
            'time_saved_total': self.time_saved_total,
            'general_searches': self.general_searches,
            'component_searches': self.component_searches
        }


@dataclass
class SearchFilters:
    """Filters for searching through saved data."""
    search_type: Optional[SearchType] = None
    manufacturer: Optional[str] = None
    content_type: Optional[ContentType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_rating: Optional[int] = None
    query_contains: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'search_type': self.search_type.value if self.search_type else None,
            'manufacturer': self.manufacturer,
            'content_type': self.content_type.value if self.content_type else None,
            'date_from': self.date_from.isoformat() if self.date_from else None,
            'date_to': self.date_to.isoformat() if self.date_to else None,
            'min_rating': self.min_rating,
            'query_contains': self.query_contains
        }


@dataclass
class AppSetting:
    """Represents an application setting."""
    key: str
    value: str
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSetting':
        """Create instance from dictionary."""
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        
        return cls(
            key=data['key'],
            value=data['value'],
            updated_at=updated_at
        )


# Utility functions for data conversion
def serialize_key_points(key_points: List[str]) -> str:
    """Serialize key points list to JSON string for database storage."""
    return json.dumps(key_points, ensure_ascii=False)


def deserialize_key_points(key_points_json: str) -> List[str]:
    """Deserialize key points from JSON string."""
    if not key_points_json:
        return []
    try:
        return json.loads(key_points_json)
    except json.JSONDecodeError:
        return []


def serialize_technical_specs(specs: Dict[str, Any]) -> str:
    """Serialize technical specs dict to JSON string for database storage."""
    return json.dumps(specs, ensure_ascii=False)


def deserialize_technical_specs(specs_json: str) -> Dict[str, Any]:
    """Deserialize technical specs from JSON string."""
    if not specs_json:
        return {}
    try:
        return json.loads(specs_json)
    except json.JSONDecodeError:
        return {}