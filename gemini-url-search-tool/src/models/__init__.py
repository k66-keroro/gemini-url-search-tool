"""
Models package for Gemini URL Search Tool.
"""

from .database import DatabaseManager, get_database_manager
from .data_models import (
    SearchType, ContentType, SearchResult, ContentAnalysis, 
    SearchRecord, UserEvaluation, SearchMetrics, SearchFilters, 
    AppSetting, serialize_key_points, deserialize_key_points,
    serialize_technical_specs, deserialize_technical_specs
)
from .repository import (
    SearchRepository, ContentRepository, EvaluationRepository, 
    SettingsRepository
)

__all__ = [
    # Database management
    'DatabaseManager',
    'get_database_manager',
    
    # Data models
    'SearchType',
    'ContentType', 
    'SearchResult',
    'ContentAnalysis',
    'SearchRecord',
    'UserEvaluation',
    'SearchMetrics',
    'SearchFilters',
    'AppSetting',
    
    # Utility functions
    'serialize_key_points',
    'deserialize_key_points',
    'serialize_technical_specs',
    'deserialize_technical_specs',
    
    # Repository classes
    'SearchRepository',
    'ContentRepository',
    'EvaluationRepository',
    'SettingsRepository',
]