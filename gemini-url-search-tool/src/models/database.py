"""
Database initialization and schema management for Gemini URL Search Tool.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database initialization and schema creation."""
    
    def __init__(self, db_path: str = "data/search_results.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def initialize_database(self) -> None:
        """Initialize database and create all required tables."""
        try:
            with self.get_connection() as conn:
                self._create_tables(conn)
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling and optimization."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Performance optimizations
            conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety and speed
            conn.execute("PRAGMA cache_size=10000")  # Increase cache size
            conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory mapping
            
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create all required database tables."""
        
        # Search history table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                search_type TEXT NOT NULL CHECK(search_type IN ('general', 'component')),
                manufacturer TEXT,
                part_number TEXT,
                results_count INTEGER DEFAULT 0,
                search_time REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Search results table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                description TEXT,
                rank_position INTEGER,
                is_official_source BOOLEAN DEFAULT FALSE,
                confidence_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (search_id) REFERENCES search_history (id) ON DELETE CASCADE
            )
        """)
        
        # Content analysis table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS content_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER,
                url TEXT NOT NULL,
                content_type TEXT CHECK(content_type IN ('general', 'specification', 'datasheet')),
                summary TEXT,
                key_points TEXT,
                technical_specs TEXT,
                extraction_time REAL DEFAULT 0.0,
                content_size INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (result_id) REFERENCES search_results (id) ON DELETE CASCADE
            )
        """)
        
        # User evaluations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER NOT NULL,
                usefulness_rating INTEGER CHECK(usefulness_rating BETWEEN 1 AND 5),
                accuracy_rating INTEGER CHECK(accuracy_rating BETWEEN 1 AND 5),
                feedback TEXT,
                time_saved_minutes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES content_analysis (id) ON DELETE CASCADE
            )
        """)
        
        # Application settings table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        self._create_indexes(conn)
        
        conn.commit()
        logger.info("All database tables created successfully")
    
    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create database indexes for better query performance."""
        
        indexes = [
            # Search history indexes
            "CREATE INDEX IF NOT EXISTS idx_search_history_type ON search_history(search_type)",
            "CREATE INDEX IF NOT EXISTS idx_search_history_created ON search_history(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query)",
            "CREATE INDEX IF NOT EXISTS idx_search_history_manufacturer ON search_history(manufacturer)",
            "CREATE INDEX IF NOT EXISTS idx_search_history_part_number ON search_history(part_number)",
            
            # Search results indexes
            "CREATE INDEX IF NOT EXISTS idx_search_results_search_id ON search_results(search_id)",
            "CREATE INDEX IF NOT EXISTS idx_search_results_url ON search_results(url)",
            "CREATE INDEX IF NOT EXISTS idx_search_results_rank ON search_results(rank_position)",
            "CREATE INDEX IF NOT EXISTS idx_search_results_official ON search_results(is_official_source)",
            "CREATE INDEX IF NOT EXISTS idx_search_results_confidence ON search_results(confidence_score)",
            
            # Content analysis indexes
            "CREATE INDEX IF NOT EXISTS idx_content_analysis_result_id ON content_analysis(result_id)",
            "CREATE INDEX IF NOT EXISTS idx_content_analysis_url ON content_analysis(url)",
            "CREATE INDEX IF NOT EXISTS idx_content_analysis_type ON content_analysis(content_type)",
            "CREATE INDEX IF NOT EXISTS idx_content_analysis_created ON content_analysis(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_content_analysis_size ON content_analysis(content_size)",
            
            # User evaluations indexes
            "CREATE INDEX IF NOT EXISTS idx_user_evaluations_content_id ON user_evaluations(content_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_evaluations_rating ON user_evaluations(usefulness_rating)",
            "CREATE INDEX IF NOT EXISTS idx_user_evaluations_created ON user_evaluations(created_at)",
            
            # Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_search_history_type_created ON search_history(search_type, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_search_results_search_rank ON search_results(search_id, rank_position)",
            "CREATE INDEX IF NOT EXISTS idx_content_analysis_url_created ON content_analysis(url, created_at)",
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        # Analyze tables for query optimization
        conn.execute("ANALYZE")
        
        logger.info("Database indexes and statistics updated successfully")
    
    def check_database_health(self) -> bool:
        """Check if database is accessible and has correct schema."""
        try:
            with self.get_connection() as conn:
                # Check if all required tables exist
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN (
                        'search_history', 'search_results', 'content_analysis',
                        'user_evaluations', 'app_settings'
                    )
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                expected_tables = {
                    'search_history', 'search_results', 'content_analysis',
                    'user_evaluations', 'app_settings'
                }
                
                if set(tables) == expected_tables:
                    logger.info("Database health check passed")
                    return True
                else:
                    missing_tables = expected_tables - set(tables)
                    logger.error(f"Database health check failed. Missing tables: {missing_tables}")
                    return False
                    
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def reset_database(self) -> None:
        """Reset database by dropping and recreating all tables."""
        try:
            with self.get_connection() as conn:
                # Drop all tables
                tables = ['user_evaluations', 'content_analysis', 'search_results', 
                         'search_history', 'app_settings']
                
                for table in tables:
                    conn.execute(f"DROP TABLE IF EXISTS {table}")
                
                # Recreate tables
                self._create_tables(conn)
                logger.info("Database reset successfully")
                
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            raise
    
    def optimize_database(self) -> Dict[str, Any]:
        """
        Optimize database performance.
        
        Returns:
            Dictionary with optimization results
        """
        try:
            with self.get_connection() as conn:
                # Get initial stats
                initial_stats = self._get_database_stats(conn)
                
                # Run VACUUM to reclaim space and defragment
                logger.info("Running VACUUM to optimize database...")
                conn.execute("VACUUM")
                
                # Update table statistics
                logger.info("Updating table statistics...")
                conn.execute("ANALYZE")
                
                # Rebuild indexes if needed
                logger.info("Checking index integrity...")
                cursor = conn.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                if integrity_result != "ok":
                    logger.warning(f"Database integrity issue: {integrity_result}")
                    # Rebuild indexes
                    self._rebuild_indexes(conn)
                
                # Get final stats
                final_stats = self._get_database_stats(conn)
                
                optimization_result = {
                    'initial_size_mb': initial_stats['size_mb'],
                    'final_size_mb': final_stats['size_mb'],
                    'space_saved_mb': initial_stats['size_mb'] - final_stats['size_mb'],
                    'integrity_check': integrity_result,
                    'page_count': final_stats['page_count'],
                    'page_size': final_stats['page_size']
                }
                
                logger.info(f"Database optimization completed: {optimization_result}")
                return optimization_result
                
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            return {'error': str(e)}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get database performance statistics.
        
        Returns:
            Dictionary with performance statistics
        """
        try:
            with self.get_connection() as conn:
                stats = self._get_database_stats(conn)
                
                # Add query performance info
                cursor = conn.execute("PRAGMA compile_options")
                compile_options = [row[0] for row in cursor.fetchall()]
                
                cursor = conn.execute("PRAGMA cache_size")
                cache_size = cursor.fetchone()[0]
                
                cursor = conn.execute("PRAGMA journal_mode")
                journal_mode = cursor.fetchone()[0]
                
                cursor = conn.execute("PRAGMA synchronous")
                synchronous = cursor.fetchone()[0]
                
                stats.update({
                    'cache_size': cache_size,
                    'journal_mode': journal_mode,
                    'synchronous': synchronous,
                    'compile_options': compile_options,
                    'wal_enabled': journal_mode.upper() == 'WAL'
                })
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {'error': str(e)}
    
    def _get_database_stats(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get basic database statistics."""
        cursor = conn.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        
        cursor = conn.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        size_bytes = page_count * page_size
        size_mb = round(size_bytes / (1024 * 1024), 2)
        
        # Get table counts
        table_stats = {}
        tables = ['search_history', 'search_results', 'content_analysis', 
                 'user_evaluations', 'app_settings']
        
        for table in tables:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            table_stats[f'{table}_count'] = cursor.fetchone()[0]
        
        return {
            'page_count': page_count,
            'page_size': page_size,
            'size_bytes': size_bytes,
            'size_mb': size_mb,
            **table_stats
        }
    
    def _rebuild_indexes(self, conn: sqlite3.Connection) -> None:
        """Rebuild all database indexes."""
        logger.info("Rebuilding database indexes...")
        
        # Drop existing indexes (except primary keys)
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        
        indexes = [row[0] for row in cursor.fetchall()]
        
        for index_name in indexes:
            conn.execute(f"DROP INDEX IF EXISTS {index_name}")
        
        # Recreate indexes
        self._create_indexes(conn)
        
        logger.info("Database indexes rebuilt successfully")
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Clean up old data beyond retention period.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            with self.get_connection() as conn:
                # Count records to be deleted
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM search_history 
                    WHERE created_at < ?
                """, (cutoff_date,))
                
                old_searches = cursor.fetchone()[0]
                
                # Delete old records (cascading deletes will handle related records)
                cursor = conn.execute("""
                    DELETE FROM search_history 
                    WHERE created_at < ?
                """, (cutoff_date,))
                
                deleted_searches = cursor.rowcount
                conn.commit()
                
                # Run VACUUM to reclaim space
                if deleted_searches > 0:
                    conn.execute("VACUUM")
                
                logger.info(f"Cleaned up {deleted_searches} old search records")
                
                return {
                    'deleted_searches': deleted_searches,
                    'cutoff_date': cutoff_date,
                    'days_kept': days_to_keep
                }
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {'error': str(e)}


def get_database_manager(db_path: Optional[str] = None) -> DatabaseManager:
    """
    Factory function to get DatabaseManager instance.
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        DatabaseManager instance
    """
    if db_path is None:
        db_path = "data/search_results.db"
    
    return DatabaseManager(db_path)


if __name__ == "__main__":
    # Initialize database when run directly
    logging.basicConfig(level=logging.INFO)
    
    db_manager = get_database_manager()
    db_manager.initialize_database()
    
    if db_manager.check_database_health():
        print("Database initialization completed successfully!")
    else:
        print("Database initialization failed!")