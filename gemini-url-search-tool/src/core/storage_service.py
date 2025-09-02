"""
Storage service for managing search results and content analysis data.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib

from ..models.database import DatabaseManager, get_database_manager
from ..models.repository import (
    SearchRepository, ContentRepository, EvaluationRepository, SettingsRepository
)
from ..models.data_models import (
    SearchRecord, SearchResult, ContentAnalysis, UserEvaluation,
    SearchMetrics, SearchFilters, AppSetting, SearchType, ContentType
)
try:
    from src.core.cache_service import get_cache_service
except ImportError:
    # Fallback if cache service is not available
    def get_cache_service():
        return None

logger = logging.getLogger(__name__)


class StorageService:
    """
    High-level storage service for managing search results and content analysis.
    
    This service provides a unified interface for all storage operations,
    including duplicate detection, metadata management, and search history.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize storage service.
        
        Args:
            db_path: Optional custom database path
        """
        self.db_manager = get_database_manager(db_path)
        self.search_repo = SearchRepository(self.db_manager)
        self.content_repo = ContentRepository(self.db_manager)
        self.evaluation_repo = EvaluationRepository(self.db_manager)
        self.settings_repo = SettingsRepository(self.db_manager)
        
        # Initialize cache service
        self.cache_service = get_cache_service()
        
        # Initialize database if needed
        self._ensure_database_initialized()
    
    def _ensure_database_initialized(self) -> None:
        """Ensure database is properly initialized."""
        try:
            if not self.db_manager.check_database_health():
                logger.info("Initializing database...")
                self.db_manager.initialize_database()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def save_search_result(self, search: SearchRecord) -> int:
        """
        Save search record with metadata management.
        
        Args:
            search: SearchRecord to save
            
        Returns:
            ID of the saved search record
        """
        try:
            # Add metadata
            search.created_at = datetime.now()
            
            # Save search record
            search_id = await self.search_repo.save_search_record(search)
            
            # Save individual search results
            for result in search.results:
                result.search_id = search_id
                result_id = self.search_repo.save_search_result(result)
                result.id = result_id
            
            logger.info(f"Saved search with {len(search.results)} results")
            return search_id
            
        except Exception as e:
            logger.error(f"Failed to save search result: {e}")
            raise
    
    def save_content_analysis(self, analysis: ContentAnalysis) -> int:
        """
        Save content analysis with duplicate detection.
        
        Args:
            analysis: ContentAnalysis to save
            
        Returns:
            ID of the saved content analysis
        """
        try:
            # Check for existing analysis of the same URL
            existing = self.detect_duplicate(analysis.url)
            
            if existing:
                logger.info(f"Found existing analysis for URL: {analysis.url}")
                # Update existing analysis if new one is more recent or comprehensive
                if self._should_update_analysis(existing, analysis):
                    return self._update_content_analysis(existing.id, analysis)
                else:
                    return existing.id
            
            # Add metadata
            analysis.created_at = datetime.now()
            
            # Save new analysis
            analysis_id = self.content_repo.save_content_analysis(analysis)
            
            logger.info(f"Saved new content analysis for: {analysis.url}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Failed to save content analysis: {e}")
            raise
    
    def detect_duplicate(self, url: str) -> Optional[ContentAnalysis]:
        """
        Detect duplicate content by URL.
        
        Args:
            url: URL to check for duplicates
            
        Returns:
            Existing ContentAnalysis if found, None otherwise
        """
        try:
            # Normalize URL for comparison
            normalized_url = self._normalize_url(url)
            
            # Check for exact URL match
            existing = self.content_repo.get_content_analysis_by_url(normalized_url)
            
            if existing:
                return existing
            
            # Check for original URL if different from normalized
            if url != normalized_url:
                existing = self.content_repo.get_content_analysis_by_url(url)
                if existing:
                    return existing
            
            # Check for similar URLs (without query parameters, fragments)
            base_url = self._get_base_url(normalized_url)
            if base_url != normalized_url:
                existing = self.content_repo.get_content_analysis_by_url(base_url)
                if existing:
                    return existing
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to detect duplicate: {e}")
            return None
    
    async def get_search_history(self, filters: Optional[SearchFilters] = None,
                          limit: int = 100, offset: int = 0) -> List[SearchRecord]:
        """
        Get search history with filtering and pagination.
        
        Args:
            filters: Optional filters to apply
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of SearchRecord instances
        """
        try:
            # Create cache key based on filters and pagination
            cache_params = {
                'filters': filters.__dict__ if filters else None,
                'limit': limit,
                'offset': offset
            }
            
            # Try to get from cache first
            cached_result = self.cache_service.get_cached_query_result(
                "get_search_history", cache_params
            )
            
            if cached_result is not None:
                return cached_result
            
            # Get from database
            start_time = time.time()
            result = await self.search_repo.get_search_history(filters, limit, offset)
            execution_time = time.time() - start_time
            
            # Cache the result
            self.cache_service.cache_query_result(
                "get_search_history", cache_params, result
            )
            
            # Track performance
            self.cache_service.track_query_performance(
                "get_search_history", execution_time
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get search history: {e}")
            raise
    
    def get_saved_content(self, content_id: int) -> Optional[ContentAnalysis]:
        """
        Get saved content analysis by ID.
        
        Args:
            content_id: ID of the content analysis
            
        Returns:
            ContentAnalysis instance if found, None otherwise
        """
        try:
            # Try cache first
            cache_params = {'content_id': content_id}
            cached_result = self.cache_service.get_cached_query_result(
                "get_content_by_id", cache_params
            )
            
            if cached_result is not None:
                return cached_result
            
            # Get from database
            start_time = time.time()
            result = self.content_repo.get_content_analysis_by_id(content_id)
            execution_time = time.time() - start_time
            
            # Cache the result if found
            if result:
                self.cache_service.cache_query_result(
                    "get_content_by_id", cache_params, result
                )
            
            # Track performance
            self.cache_service.track_query_performance(
                "get_content_by_id", execution_time
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get saved content: {e}")
            return None
    
    def update_evaluation(self, content_id: int, rating: int, feedback: str = None,
                         time_saved_minutes: int = 0) -> int:
        """
        Update or create user evaluation for content.
        
        Args:
            content_id: ID of the content being evaluated
            rating: Usefulness rating (1-5)
            feedback: Optional feedback text
            time_saved_minutes: Estimated time saved in minutes
            
        Returns:
            ID of the evaluation record
        """
        try:
            evaluation = UserEvaluation(
                content_id=content_id,
                usefulness_rating=rating,
                accuracy_rating=rating,  # Using same rating for both for simplicity
                feedback=feedback,
                time_saved_minutes=time_saved_minutes
            )
            
            return self.evaluation_repo.save_user_evaluation(evaluation)
            
        except Exception as e:
            logger.error(f"Failed to update evaluation: {e}")
            raise
    
    def get_search_metrics(self, days_back: int = 30) -> SearchMetrics:
        """
        Get search performance metrics for the specified time period.
        
        Args:
            days_back: Number of days to look back for metrics
            
        Returns:
            SearchMetrics instance
        """
        try:
            date_from = datetime.now() - timedelta(days=days_back)
            return self.evaluation_repo.get_search_metrics(date_from=date_from)
        except Exception as e:
            logger.error(f"Failed to get search metrics: {e}")
            raise
    
    def save_setting(self, key: str, value: str) -> None:
        """
        Save application setting.
        
        Args:
            key: Setting key
            value: Setting value
        """
        try:
            setting = AppSetting(key=key, value=value)
            self.settings_repo.save_setting(setting)
        except Exception as e:
            logger.error(f"Failed to save setting: {e}")
            raise
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """
        Get application setting value.
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        try:
            setting = self.settings_repo.get_setting(key)
            return setting.value if setting else default
        except Exception as e:
            logger.error(f"Failed to get setting: {e}")
            return default
    
    def get_all_settings(self) -> Dict[str, str]:
        """
        Get all application settings.
        
        Returns:
            Dictionary of all settings
        """
        try:
            return self.settings_repo.get_all_settings()
        except Exception as e:
            logger.error(f"Failed to get all settings: {e}")
            return {}
    
    async def search_saved_content(self, filters: SearchFilters) -> List[ContentAnalysis]:
        """
        Search through saved content with filters.
        
        Args:
            filters: Search filters to apply
            
        Returns:
            List of matching ContentAnalysis instances
        """
        try:
            # Get search history that matches filters
            search_records = await self.get_search_history(filters)
            
            # Collect all content analyses from matching searches
            content_analyses = []
            
            for search_record in search_records:
                for result in search_record.results:
                    if result.id:
                        analysis = self.content_repo.get_content_analysis_by_url(result.url)
                        if analysis:
                            # Apply additional content-specific filters
                            if self._matches_content_filters(analysis, filters):
                                content_analyses.append(analysis)
            
            # Remove duplicates and sort by creation date
            unique_analyses = {analysis.url: analysis for analysis in content_analyses}
            sorted_analyses = sorted(
                unique_analyses.values(),
                key=lambda x: x.created_at or datetime.min,
                reverse=True
            )
            
            return sorted_analyses
            
        except Exception as e:
            logger.error(f"Failed to search saved content: {e}")
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Clean up old data beyond the retention period.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with self.db_manager.get_connection() as conn:
                # Count records to be deleted
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM search_history 
                    WHERE created_at < ?
                """, (cutoff_date.isoformat(),))
                
                old_searches = cursor.fetchone()[0]
                
                # Delete old records (cascading deletes will handle related records)
                cursor = conn.execute("""
                    DELETE FROM search_history 
                    WHERE created_at < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_searches = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_searches} old search records")
                
                return {
                    'deleted_searches': deleted_searches,
                    'cutoff_date': cutoff_date.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {'error': str(e)}
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get storage usage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            with self.db_manager.get_connection() as conn:
                stats = {}
                
                # Count records in each table
                tables = [
                    'search_history', 'search_results', 'content_analysis',
                    'user_evaluations', 'app_settings'
                ]
                
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f'{table}_count'] = cursor.fetchone()[0]
                
                # Get database file size
                cursor = conn.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                
                cursor = conn.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                
                stats['database_size_bytes'] = page_count * page_size
                stats['database_size_mb'] = round(stats['database_size_bytes'] / (1024 * 1024), 2)
                
                # Get date range of data
                cursor = conn.execute("""
                    SELECT MIN(created_at), MAX(created_at) 
                    FROM search_history
                """)
                
                date_range = cursor.fetchone()
                if date_range[0]:
                    stats['oldest_record'] = date_range[0]
                    stats['newest_record'] = date_range[1]
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get storage statistics: {e}")
            return {'error': str(e)}
    
    def optimize_performance(self) -> Dict[str, Any]:
        """
        Optimize storage and cache performance.
        
        Returns:
            Dictionary with optimization results
        """
        try:
            optimization_results = {}
            
            # Optimize database
            db_optimization = self.db_manager.optimize_database()
            optimization_results['database'] = db_optimization
            
            # Optimize cache
            cache_optimization = self.cache_service.optimize_memory()
            optimization_results['cache'] = cache_optimization
            
            # Clean up old data
            cleanup_results = self.cleanup_old_data(days_to_keep=90)
            optimization_results['cleanup'] = cleanup_results
            
            logger.info(f"Performance optimization completed: {optimization_results}")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Failed to optimize performance: {e}")
            return {'error': str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            metrics = {}
            
            # Database performance
            metrics['database'] = self.db_manager.get_performance_stats()
            
            # Cache performance
            metrics['cache'] = self.cache_service.get_cache_stats()
            
            # Storage statistics
            metrics['storage'] = self.get_storage_statistics()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}
    
    def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries.
        
        Args:
            pattern: Pattern to match for selective invalidation
            
        Returns:
            Number of entries invalidated
        """
        try:
            return self.cache_service.invalidate_cache(pattern)
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return 0
    
    # Private helper methods
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent comparison."""
        # Remove trailing slashes, convert to lowercase
        normalized = url.strip().lower()
        if normalized.endswith('/'):
            normalized = normalized[:-1]
        return normalized
    
    def _get_base_url(self, url: str) -> str:
        """Get base URL without query parameters and fragments."""
        # Simple implementation - remove everything after ? or #
        for char in ['?', '#']:
            if char in url:
                url = url[:url.index(char)]
        return url
    
    def _should_update_analysis(self, existing: ContentAnalysis, 
                              new: ContentAnalysis) -> bool:
        """
        Determine if existing analysis should be updated with new one.
        
        Args:
            existing: Existing ContentAnalysis
            new: New ContentAnalysis
            
        Returns:
            True if should update, False otherwise
        """
        # Update if new analysis has more content or better summary
        if len(new.summary) > len(existing.summary) * 1.2:
            return True
        
        if len(new.key_points) > len(existing.key_points):
            return True
        
        if len(new.technical_specs) > len(existing.technical_specs):
            return True
        
        # Update if existing analysis is older than 7 days
        if existing.created_at:
            age_days = (datetime.now() - existing.created_at).days
            if age_days > 7:
                return True
        
        return False
    
    def _update_content_analysis(self, analysis_id: int, 
                               new_analysis: ContentAnalysis) -> int:
        """
        Update existing content analysis with new data.
        
        Args:
            analysis_id: ID of existing analysis
            new_analysis: New analysis data
            
        Returns:
            ID of the updated analysis
        """
        try:
            with self.db_manager.get_connection() as conn:
                from ..models.data_models import serialize_key_points, serialize_technical_specs
                
                conn.execute("""
                    UPDATE content_analysis 
                    SET summary = ?, key_points = ?, technical_specs = ?,
                        extraction_time = ?, content_size = ?,
                        created_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    new_analysis.summary,
                    serialize_key_points(new_analysis.key_points),
                    serialize_technical_specs(new_analysis.technical_specs),
                    new_analysis.extraction_time,
                    new_analysis.content_size,
                    analysis_id
                ))
                
                conn.commit()
                logger.info(f"Updated content analysis ID: {analysis_id}")
                return analysis_id
                
        except Exception as e:
            logger.error(f"Failed to update content analysis: {e}")
            raise
    
    def _matches_content_filters(self, analysis: ContentAnalysis, 
                               filters: SearchFilters) -> bool:
        """
        Check if content analysis matches the given filters.
        
        Args:
            analysis: ContentAnalysis to check
            filters: SearchFilters to apply
            
        Returns:
            True if matches, False otherwise
        """
        if filters.content_type and analysis.content_type != filters.content_type.value:
            return False
        
        if filters.min_rating:
            # This would require joining with evaluations table
            # For now, we'll skip this filter in content search
            pass
        
        return True


def get_storage_service(db_path: Optional[str] = None) -> StorageService:
    """
    Factory function to get StorageService instance.
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        StorageService instance
    """
    return StorageService(db_path)