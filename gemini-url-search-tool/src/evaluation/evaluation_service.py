"""
Evaluation service for tracking search performance and user satisfaction.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..models.database import DatabaseManager
from ..models.repository import EvaluationRepository, SearchRepository, ContentRepository
from ..models.data_models import (
    SearchMetrics, UserEvaluation, SearchRecord, ContentAnalysis,
    SearchType, SearchFilters
)

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """Analysis of query patterns and performance."""
    most_common_queries: List[Tuple[str, int]]
    avg_results_per_query: float
    most_successful_query_types: List[Tuple[str, float]]
    query_performance_trends: Dict[str, float]


@dataclass
class EffectivenessReport:
    """Comprehensive effectiveness report."""
    overall_metrics: SearchMetrics
    query_analysis: QueryAnalysis
    improvement_suggestions: List[str]
    time_period: Tuple[datetime, datetime]
    user_satisfaction_trend: List[Tuple[datetime, float]]


@dataclass
class UserInteraction:
    """Represents a user interaction for tracking."""
    interaction_type: str  # 'search', 'content_view', 'evaluation'
    search_id: Optional[int] = None
    content_id: Optional[int] = None
    duration_seconds: float = 0.0
    success: bool = True
    metadata: Dict[str, Any] = None


class EvaluationService:
    """Service for evaluating search performance and user satisfaction."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize evaluation service.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.evaluation_repo = EvaluationRepository(db_manager)
        self.search_repo = SearchRepository(db_manager)
        self.content_repo = ContentRepository(db_manager)
        
        # Cache for performance metrics
        self._metrics_cache = {}
        self._cache_expiry = {}
        self._cache_duration = timedelta(minutes=5)
    
    async def calculate_search_metrics(self, 
                                     date_from: Optional[datetime] = None,
                                     date_to: Optional[datetime] = None) -> SearchMetrics:
        """
        Calculate comprehensive search metrics for the specified time range.
        
        Args:
            date_from: Start date for metrics calculation
            date_to: End date for metrics calculation
            
        Returns:
            SearchMetrics instance with calculated values
        """
        try:
            # Check cache first
            cache_key = f"metrics_{date_from}_{date_to}"
            if self._is_cache_valid(cache_key):
                logger.info("Returning cached search metrics")
                return self._metrics_cache[cache_key]
            
            # Calculate metrics from database
            metrics = self.evaluation_repo.get_search_metrics(date_from, date_to)
            
            # Enhance metrics with additional calculations
            enhanced_metrics = await self._enhance_search_metrics(metrics, date_from, date_to)
            
            # Cache the results
            self._cache_metrics(cache_key, enhanced_metrics)
            
            logger.info(f"Calculated search metrics: {enhanced_metrics.total_searches} searches, "
                       f"{enhanced_metrics.success_rate:.1f}% success rate")
            
            return enhanced_metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate search metrics: {e}")
            raise
    
    async def analyze_query_patterns(self, 
                                   date_from: Optional[datetime] = None,
                                   date_to: Optional[datetime] = None) -> QueryAnalysis:
        """
        Analyze query patterns and performance trends.
        
        Args:
            date_from: Start date for analysis
            date_to: End date for analysis
            
        Returns:
            QueryAnalysis instance with pattern analysis
        """
        try:
            # Get search history for analysis
            filters = SearchFilters(date_from=date_from, date_to=date_to)
            search_history = await self.search_repo.get_search_history(filters, limit=1000)
            
            # Analyze query patterns
            query_counts = {}
            query_results = {}
            type_performance = {'general': [], 'component': []}
            
            for search in search_history:
                # Count query frequency
                query = search.query.lower().strip()
                query_counts[query] = query_counts.get(query, 0) + 1
                
                # Track results per query
                if query not in query_results:
                    query_results[query] = []
                query_results[query].append(search.results_count)
                
                # Track performance by type
                success_rate = 1.0 if search.results_count > 0 else 0.0
                type_performance[search.search_type.value].append(success_rate)
            
            # Calculate most common queries
            most_common = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Calculate average results per query
            avg_results = sum(sum(results) for results in query_results.values()) / len(query_results) if query_results else 0
            
            # Calculate success rates by type
            most_successful_types = []
            for query_type, performances in type_performance.items():
                if performances:
                    avg_success = sum(performances) / len(performances) * 100
                    most_successful_types.append((query_type, avg_success))
            
            most_successful_types.sort(key=lambda x: x[1], reverse=True)
            
            # Calculate performance trends (simplified)
            performance_trends = await self._calculate_performance_trends(search_history)
            
            return QueryAnalysis(
                most_common_queries=most_common,
                avg_results_per_query=avg_results,
                most_successful_query_types=most_successful_types,
                query_performance_trends=performance_trends
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze query patterns: {e}")
            raise
    
    async def generate_effectiveness_report(self, 
                                          date_from: Optional[datetime] = None,
                                          date_to: Optional[datetime] = None) -> EffectivenessReport:
        """
        Generate comprehensive effectiveness report.
        
        Args:
            date_from: Start date for report
            date_to: End date for report
            
        Returns:
            EffectivenessReport instance
        """
        try:
            # Set default time range if not provided
            if not date_to:
                date_to = datetime.now()
            if not date_from:
                date_from = date_to - timedelta(days=30)
            
            # Calculate overall metrics
            overall_metrics = await self.calculate_search_metrics(date_from, date_to)
            
            # Analyze query patterns
            query_analysis = await self.analyze_query_patterns(date_from, date_to)
            
            # Generate improvement suggestions
            improvement_suggestions = await self._generate_improvement_suggestions(
                overall_metrics, query_analysis
            )
            
            # Calculate satisfaction trends
            satisfaction_trend = await self._calculate_satisfaction_trend(date_from, date_to)
            
            logger.info(f"Generated effectiveness report for period {date_from} to {date_to}")
            
            return EffectivenessReport(
                overall_metrics=overall_metrics,
                query_analysis=query_analysis,
                improvement_suggestions=improvement_suggestions,
                time_period=(date_from, date_to),
                user_satisfaction_trend=satisfaction_trend
            )
            
        except Exception as e:
            logger.error(f"Failed to generate effectiveness report: {e}")
            raise
    
    async def track_user_interaction(self, interaction: UserInteraction) -> None:
        """
        Track user interaction for analytics.
        
        Args:
            interaction: UserInteraction instance to track
        """
        try:
            # For now, we'll log the interaction
            # In a more sophisticated implementation, this could be stored in a separate table
            logger.info(f"User interaction tracked: {interaction.interaction_type}, "
                       f"success: {interaction.success}, duration: {interaction.duration_seconds}s")
            
            # Could implement interaction storage here if needed
            # This would require extending the database schema
            
        except Exception as e:
            logger.error(f"Failed to track user interaction: {e}")
    
    async def save_user_evaluation(self, evaluation: UserEvaluation) -> int:
        """
        Save user evaluation and update metrics.
        
        Args:
            evaluation: UserEvaluation instance to save
            
        Returns:
            ID of the saved evaluation
        """
        try:
            evaluation_id = self.evaluation_repo.save_user_evaluation(evaluation)
            
            # Clear metrics cache to ensure fresh calculations
            self._clear_metrics_cache()
            
            logger.info(f"Saved user evaluation with ratings: "
                       f"usefulness={evaluation.usefulness_rating}, "
                       f"accuracy={evaluation.accuracy_rating}")
            
            return evaluation_id
            
        except Exception as e:
            logger.error(f"Failed to save user evaluation: {e}")
            raise
    
    async def get_improvement_suggestions(self, 
                                        metrics: Optional[SearchMetrics] = None) -> List[str]:
        """
        Generate improvement suggestions based on current metrics.
        
        Args:
            metrics: Optional SearchMetrics to base suggestions on
            
        Returns:
            List of improvement suggestions
        """
        try:
            if not metrics:
                metrics = await self.calculate_search_metrics()
            
            suggestions = []
            
            # Analyze success rate
            if metrics.success_rate < 70:
                suggestions.append(
                    "検索成功率が低いです。より具体的なキーワードを使用することを推奨します。"
                )
            
            # Analyze search time
            if metrics.avg_search_time > 10.0:
                suggestions.append(
                    "検索時間が長いです。ネットワーク接続やAPI設定を確認してください。"
                )
            
            # Analyze user satisfaction
            if metrics.avg_usefulness_rating < 3.0:
                suggestions.append(
                    "検索結果の有用性が低いです。検索クエリの改善や結果フィルタリングの調整を検討してください。"
                )
            
            if metrics.avg_accuracy_rating < 3.0:
                suggestions.append(
                    "検索結果の精度が低いです。より専門的なキーワードや部品番号での検索を試してください。"
                )
            
            # Analyze search distribution
            total_searches = metrics.general_searches + metrics.component_searches
            if total_searches > 0:
                component_ratio = metrics.component_searches / total_searches
                if component_ratio < 0.2:
                    suggestions.append(
                        "部品検索の利用が少ないです。メーカー名と品番を使った専門検索も活用してください。"
                    )
            
            # Time savings analysis
            if metrics.time_saved_total < metrics.total_searches * 5:
                suggestions.append(
                    "時間節約効果が低いです。検索結果の保存機能を活用して効率を向上させてください。"
                )
            
            if not suggestions:
                suggestions.append("現在のパフォーマンスは良好です。継続して活用してください。")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate improvement suggestions: {e}")
            raise
    
    # Private helper methods
    
    async def _enhance_search_metrics(self, 
                                    base_metrics: SearchMetrics,
                                    date_from: Optional[datetime],
                                    date_to: Optional[datetime]) -> SearchMetrics:
        """Enhance base metrics with additional calculations."""
        # For now, return the base metrics as-is
        # Could add more sophisticated calculations here
        return base_metrics
    
    async def _calculate_performance_trends(self, 
                                          search_history: List[SearchRecord]) -> Dict[str, float]:
        """Calculate performance trends from search history."""
        trends = {}
        
        if not search_history:
            return trends
        
        # Group searches by week
        weekly_performance = {}
        for search in search_history:
            if search.created_at:
                week_key = search.created_at.strftime("%Y-W%U")
                if week_key not in weekly_performance:
                    weekly_performance[week_key] = {'total': 0, 'successful': 0}
                
                weekly_performance[week_key]['total'] += 1
                if search.results_count > 0:
                    weekly_performance[week_key]['successful'] += 1
        
        # Calculate weekly success rates
        for week, data in weekly_performance.items():
            success_rate = (data['successful'] / data['total']) * 100 if data['total'] > 0 else 0
            trends[week] = success_rate
        
        return trends
    
    async def _generate_improvement_suggestions(self, 
                                              metrics: SearchMetrics,
                                              query_analysis: QueryAnalysis) -> List[str]:
        """Generate improvement suggestions based on metrics and analysis."""
        return await self.get_improvement_suggestions(metrics)
    
    async def _calculate_satisfaction_trend(self, 
                                          date_from: datetime,
                                          date_to: datetime) -> List[Tuple[datetime, float]]:
        """Calculate user satisfaction trend over time."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        DATE(ue.created_at) as date,
                        AVG((ue.usefulness_rating + ue.accuracy_rating) / 2.0) as avg_satisfaction
                    FROM user_evaluations ue
                    WHERE ue.created_at >= ? AND ue.created_at <= ?
                    GROUP BY DATE(ue.created_at)
                    ORDER BY date
                """, (date_from.isoformat(), date_to.isoformat()))
                
                rows = cursor.fetchall()
                
                trend = []
                for row in rows:
                    date = datetime.fromisoformat(row['date'])
                    satisfaction = row['avg_satisfaction']
                    trend.append((date, satisfaction))
                
                return trend
                
        except Exception as e:
            logger.error(f"Failed to calculate satisfaction trend: {e}")
            return []
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached metrics are still valid."""
        if cache_key not in self._cache_expiry:
            return False
        
        return datetime.now() < self._cache_expiry[cache_key]
    
    def _cache_metrics(self, cache_key: str, metrics: SearchMetrics) -> None:
        """Cache metrics with expiry time."""
        self._metrics_cache[cache_key] = metrics
        self._cache_expiry[cache_key] = datetime.now() + self._cache_duration
    
    def _clear_metrics_cache(self) -> None:
        """Clear all cached metrics."""
        self._metrics_cache.clear()
        self._cache_expiry.clear()