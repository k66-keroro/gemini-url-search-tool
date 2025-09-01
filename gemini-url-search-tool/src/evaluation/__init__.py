"""
Evaluation module for Gemini URL Search Tool.
"""

from .evaluation_service import (
    EvaluationService,
    QueryAnalysis,
    EffectivenessReport,
    UserInteraction
)

__all__ = [
    'EvaluationService',
    'QueryAnalysis', 
    'EffectivenessReport',
    'UserInteraction'
]