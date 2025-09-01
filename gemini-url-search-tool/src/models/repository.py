"""
Repository classes for database CRUD operations.
"""

import sqlite3
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .database import DatabaseManager
from .data_models import (
    SearchRecord, SearchResult, ContentAnalysis, UserEvaluation,
    SearchMetrics, SearchFilters, AppSetting, SearchType, ContentType,
    serialize_key_points, deserialize_key_points,
    serialize_technical_specs, deserialize_technical_specs
)

logger = logging.getLogger(__name__)


class SearchRepository:
    """Repository for search-related database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def save_search_record(self, search_record: SearchRecord) -> int:
        """
        Save search record to database.
        
        Args:
            search_record: SearchRecord instance to save
            
        Returns:
            ID of the saved search record
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO search_history 
                    (query, search_type, manufacturer, part_number, results_count, search_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    search_record.query,
                    search_record.search_type.value,
                    search_record.manufacturer,
                    search_record.part_number,
                    search_record.results_count,
                    search_record.search_time
                ))
                
                search_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Saved search record with ID: {search_id}")
                return search_id
                
        except Exception as e:
            logger.error(f"Failed to save search record: {e}")
            raise
    
    def save_search_result(self, search_result: SearchResult) -> int:
        """
        Save search result to database.
        
        Args:
            search_result: SearchResult instance to save
            
        Returns:
            ID of the saved search result
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO search_results 
                    (search_id, url, title, description, rank_position, 
                     is_official_source, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    search_result.search_id,
                    search_result.url,
                    search_result.title,
                    search_result.description,
                    search_result.rank,
                    search_result.is_official,
                    search_result.confidence_score
                ))
                
                result_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Saved search result with ID: {result_id}")
                return result_id
                
        except Exception as e:
            logger.error(f"Failed to save search result: {e}")
            raise
    
    async def get_search_history(self, filters: Optional[SearchFilters] = None, 
                          limit: int = 100, offset: int = 0) -> List[SearchRecord]:
        """
        Get search history with optional filters.
        
        Args:
            filters: Optional SearchFilters to apply
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of SearchRecord instances
        """
        try:
            with self.db_manager.get_connection() as conn:
                query = "SELECT * FROM search_history"
                params = []
                
                if filters:
                    conditions = []
                    
                    if filters.search_type:
                        conditions.append("search_type = ?")
                        params.append(filters.search_type.value)
                    
                    if filters.manufacturer:
                        conditions.append("manufacturer LIKE ?")
                        params.append(f"%{filters.manufacturer}%")
                    
                    if filters.date_from:
                        conditions.append("created_at >= ?")
                        params.append(filters.date_from.isoformat())
                    
                    if filters.date_to:
                        conditions.append("created_at <= ?")
                        params.append(filters.date_to.isoformat())
                    
                    if filters.query_contains:
                        conditions.append("query LIKE ?")
                        params.append(f"%{filters.query_contains}%")
                    
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                records = []
                for row in rows:
                    record = SearchRecord(
                        id=row['id'],
                        query=row['query'],
                        search_type=SearchType(row['search_type']),
                        manufacturer=row['manufacturer'],
                        part_number=row['part_number'],
                        results_count=row['results_count'],
                        search_time=row['search_time'],
                        created_at=datetime.fromisoformat(row['created_at'])
                    )
                    records.append(record)
                
                return records
                
        except Exception as e:
            logger.error(f"Failed to get search history: {e}")
            raise
    
    async def get_search_by_id(self, search_id: int) -> Optional[SearchRecord]:
        """
        Get search record by ID with its results.
        
        Args:
            search_id: ID of the search record
            
        Returns:
            SearchRecord instance if found, None otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                # Get search record
                cursor = conn.execute("""
                    SELECT * FROM search_history WHERE id = ?
                """, (search_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Create search record
                search_record = SearchRecord(
                    id=row['id'],
                    query=row['query'],
                    search_type=SearchType(row['search_type']),
                    manufacturer=row['manufacturer'],
                    part_number=row['part_number'],
                    results_count=row['results_count'],
                    search_time=row['search_time'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                
                # Get associated results
                search_record.results = self.get_search_results_by_search_id(search_id)
                
                return search_record
                
        except Exception as e:
            logger.error(f"Failed to get search by ID: {e}")
            raise
    
    def get_search_results_by_search_id(self, search_id: int) -> List[SearchResult]:
        """
        Get search results for a specific search.
        
        Args:
            search_id: ID of the search
            
        Returns:
            List of SearchResult instances
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM search_results 
                    WHERE search_id = ? 
                    ORDER BY rank_position
                """, (search_id,))
                
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = SearchResult(
                        id=row['id'],
                        search_id=row['search_id'],
                        url=row['url'],
                        title=row['title'],
                        description=row['description'],
                        rank=row['rank_position'],
                        is_official=bool(row['is_official_source']),
                        confidence_score=row['confidence_score'],
                        created_at=datetime.fromisoformat(row['created_at'])
                    )
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get search results: {e}")
            raise
    
    async def get_search_by_id(self, search_id: int) -> Optional[SearchRecord]:
        """
        Get search record by ID with its results.
        
        Args:
            search_id: ID of the search record
            
        Returns:
            SearchRecord instance if found, None otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                # Get search record
                cursor = conn.execute("""
                    SELECT * FROM search_history WHERE id = ?
                """, (search_id,))
                
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                # Create search record
                search_record = SearchRecord(
                    id=row['id'],
                    query=row['query'],
                    search_type=SearchType(row['search_type']),
                    manufacturer=row['manufacturer'],
                    part_number=row['part_number'],
                    results_count=row['results_count'],
                    search_time=row['search_time'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                
                # Get associated results
                search_record.results = await self.get_search_results_by_search_id(search_id)
                
                return search_record
                
        except Exception as e:
            logger.error(f"Failed to get search by ID: {e}")
            raise


class ContentRepository:
    """Repository for content analysis database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_content_analysis(self, content_analysis: ContentAnalysis) -> int:
        """
        Save content analysis to database.
        
        Args:
            content_analysis: ContentAnalysis instance to save
            
        Returns:
            ID of the saved content analysis
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO content_analysis 
                    (result_id, url, content_type, summary, key_points, 
                     technical_specs, extraction_time, content_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    content_analysis.result_id,
                    content_analysis.url,
                    content_analysis.content_type,
                    content_analysis.summary,
                    serialize_key_points(content_analysis.key_points),
                    serialize_technical_specs(content_analysis.technical_specs),
                    content_analysis.extraction_time,
                    content_analysis.content_size
                ))
                
                analysis_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Saved content analysis with ID: {analysis_id}")
                return analysis_id
                
        except Exception as e:
            logger.error(f"Failed to save content analysis: {e}")
            raise
    
    def get_content_analysis_by_url(self, url: str) -> Optional[ContentAnalysis]:
        """
        Get content analysis by URL.
        
        Args:
            url: URL to search for
            
        Returns:
            ContentAnalysis instance if found, None otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM content_analysis 
                    WHERE url = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (url,))
                
                row = cursor.fetchone()
                
                if row:
                    return ContentAnalysis(
                        id=row['id'],
                        result_id=row['result_id'],
                        url=row['url'],
                        content_type=row['content_type'],
                        summary=row['summary'],
                        key_points=deserialize_key_points(row['key_points']),
                        technical_specs=deserialize_technical_specs(row['technical_specs']),
                        extraction_time=row['extraction_time'],
                        content_size=row['content_size'],
                        created_at=datetime.fromisoformat(row['created_at'])
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get content analysis: {e}")
            raise
    
    def get_content_analysis_by_id(self, analysis_id: int) -> Optional[ContentAnalysis]:
        """
        Get content analysis by ID.
        
        Args:
            analysis_id: ID of the content analysis
            
        Returns:
            ContentAnalysis instance if found, None otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM content_analysis WHERE id = ?
                """, (analysis_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return ContentAnalysis(
                        id=row['id'],
                        result_id=row['result_id'],
                        url=row['url'],
                        content_type=row['content_type'],
                        summary=row['summary'],
                        key_points=deserialize_key_points(row['key_points']),
                        technical_specs=deserialize_technical_specs(row['technical_specs']),
                        extraction_time=row['extraction_time'],
                        content_size=row['content_size'],
                        created_at=datetime.fromisoformat(row['created_at'])
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get content analysis by ID: {e}")
            raise


class EvaluationRepository:
    """Repository for user evaluation database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_user_evaluation(self, evaluation: UserEvaluation) -> int:
        """
        Save user evaluation to database.
        
        Args:
            evaluation: UserEvaluation instance to save
            
        Returns:
            ID of the saved evaluation
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO user_evaluations 
                    (content_id, usefulness_rating, accuracy_rating, 
                     feedback, time_saved_minutes)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    evaluation.content_id,
                    evaluation.usefulness_rating,
                    evaluation.accuracy_rating,
                    evaluation.feedback,
                    evaluation.time_saved_minutes
                ))
                
                evaluation_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Saved user evaluation with ID: {evaluation_id}")
                return evaluation_id
                
        except Exception as e:
            logger.error(f"Failed to save user evaluation: {e}")
            raise
    
    def get_search_metrics(self, date_from: Optional[datetime] = None,
                          date_to: Optional[datetime] = None) -> SearchMetrics:
        """
        Calculate search metrics for the specified time range.
        
        Args:
            date_from: Start date for metrics calculation
            date_to: End date for metrics calculation
            
        Returns:
            SearchMetrics instance
        """
        try:
            with self.db_manager.get_connection() as conn:
                # Base query conditions
                conditions = []
                params = []
                
                if date_from:
                    conditions.append("sh.created_at >= ?")
                    params.append(date_from.isoformat())
                
                if date_to:
                    conditions.append("sh.created_at <= ?")
                    params.append(date_to.isoformat())
                
                where_clause = ""
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
                
                # Get basic search statistics
                cursor = conn.execute(f"""
                    SELECT 
                        COUNT(*) as total_searches,
                        AVG(search_time) as avg_search_time,
                        SUM(CASE WHEN search_type = 'general' THEN 1 ELSE 0 END) as general_searches,
                        SUM(CASE WHEN search_type = 'component' THEN 1 ELSE 0 END) as component_searches,
                        SUM(CASE WHEN results_count > 0 THEN 1 ELSE 0 END) as successful_searches
                    FROM search_history sh
                    {where_clause}
                """, params)
                
                stats = cursor.fetchone()
                
                # Get evaluation statistics
                eval_params = params.copy()
                cursor = conn.execute(f"""
                    SELECT 
                        AVG(ue.usefulness_rating) as avg_usefulness,
                        AVG(ue.accuracy_rating) as avg_accuracy,
                        SUM(ue.time_saved_minutes) as total_time_saved
                    FROM user_evaluations ue
                    JOIN content_analysis ca ON ue.content_id = ca.id
                    JOIN search_results sr ON ca.result_id = sr.id
                    JOIN search_history sh ON sr.search_id = sh.id
                    {where_clause}
                """, eval_params)
                
                eval_stats = cursor.fetchone()
                
                # Calculate success rate
                total_searches = stats['total_searches'] or 0
                successful_searches = stats['successful_searches'] or 0
                success_rate = (successful_searches / total_searches * 100) if total_searches > 0 else 0
                
                return SearchMetrics(
                    total_searches=total_searches,
                    avg_search_time=stats['avg_search_time'] or 0.0,
                    success_rate=success_rate,
                    avg_usefulness_rating=eval_stats['avg_usefulness'] or 0.0,
                    avg_accuracy_rating=eval_stats['avg_accuracy'] or 0.0,
                    time_saved_total=eval_stats['total_time_saved'] or 0,
                    general_searches=stats['general_searches'] or 0,
                    component_searches=stats['component_searches'] or 0
                )
                
        except Exception as e:
            logger.error(f"Failed to calculate search metrics: {e}")
            raise


class SettingsRepository:
    """Repository for application settings database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_setting(self, setting: AppSetting) -> None:
        """
        Save application setting to database.
        
        Args:
            setting: AppSetting instance to save
        """
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (setting.key, setting.value))
                
                conn.commit()
                logger.info(f"Saved setting: {setting.key}")
                
        except Exception as e:
            logger.error(f"Failed to save setting: {e}")
            raise
    
    def get_setting(self, key: str) -> Optional[AppSetting]:
        """
        Get application setting by key.
        
        Args:
            key: Setting key to retrieve
            
        Returns:
            AppSetting instance if found, None otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM app_settings WHERE key = ?
                """, (key,))
                
                row = cursor.fetchone()
                
                if row:
                    return AppSetting(
                        key=row['key'],
                        value=row['value'],
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get setting: {e}")
            raise
    
    def get_all_settings(self) -> Dict[str, str]:
        """
        Get all application settings as a dictionary.
        
        Returns:
            Dictionary of setting key-value pairs
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT key, value FROM app_settings")
                rows = cursor.fetchall()
                
                return {row['key']: row['value'] for row in rows}
                
        except Exception as e:
            logger.error(f"Failed to get all settings: {e}")
            raise