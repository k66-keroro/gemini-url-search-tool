"""
Performance monitoring utilities for the Gemini URL Search Tool.

Provides tools for monitoring and optimizing application performance.
"""

import time
import psutil
import threading
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from contextlib import contextmanager
import functools

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_threads: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class FunctionMetrics:
    """Function execution metrics."""
    function_name: str
    call_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    last_called: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class PerformanceMonitor:
    """
    System performance monitoring and optimization.
    
    Provides:
    - System resource monitoring
    - Function execution timing
    - Performance alerts
    - Optimization recommendations
    """
    
    def __init__(self, monitoring_interval: int = 60):
        """
        Initialize performance monitor.
        
        Args:
            monitoring_interval: Interval in seconds for system monitoring
        """
        self.monitoring_interval = monitoring_interval
        self.metrics_history: List[PerformanceMetrics] = []
        self.function_metrics: Dict[str, FunctionMetrics] = {}
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Performance thresholds
        self.cpu_threshold = 80.0  # CPU usage percentage
        self.memory_threshold = 80.0  # Memory usage percentage
        self.response_time_threshold = 5.0  # Response time in seconds
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
    
    def start_monitoring(self) -> None:
        """Start system performance monitoring."""
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop system performance monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Add callback for performance alerts.
        
        Args:
            callback: Function to call when alert is triggered
        """
        self.alert_callbacks.append(callback)
    
    @contextmanager
    def measure_execution(self, operation_name: str):
        """
        Context manager for measuring execution time.
        
        Args:
            operation_name: Name of the operation being measured
        """
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.record_function_execution(operation_name, execution_time)
    
    def record_function_execution(self, function_name: str, execution_time: float) -> None:
        """
        Record function execution metrics.
        
        Args:
            function_name: Name of the function
            execution_time: Execution time in seconds
        """
        with self._lock:
            if function_name not in self.function_metrics:
                self.function_metrics[function_name] = FunctionMetrics(
                    function_name=function_name,
                    call_count=0,
                    total_time=0.0,
                    avg_time=0.0,
                    min_time=float('inf'),
                    max_time=0.0,
                    last_called=datetime.now()
                )
            
            metrics = self.function_metrics[function_name]
            metrics.call_count += 1
            metrics.total_time += execution_time
            metrics.avg_time = metrics.total_time / metrics.call_count
            metrics.min_time = min(metrics.min_time, execution_time)
            metrics.max_time = max(metrics.max_time, execution_time)
            metrics.last_called = datetime.now()
            
            # Check for performance alerts
            if execution_time > self.response_time_threshold:
                self._trigger_alert(
                    "slow_function",
                    {
                        "function_name": function_name,
                        "execution_time": execution_time,
                        "threshold": self.response_time_threshold
                    }
                )
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            memory_percent = memory.percent
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
            disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_sent_mb = network_io.bytes_sent / (1024 * 1024) if network_io else 0
            network_recv_mb = network_io.bytes_recv / (1024 * 1024) if network_io else 0
            
            # Thread count
            active_threads = threading.active_count()
            
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_threads=active_threads
            )
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                active_threads=0
            )
    
    def get_metrics_history(self, hours_back: int = 24) -> List[PerformanceMetrics]:
        """
        Get performance metrics history.
        
        Args:
            hours_back: Number of hours of history to return
            
        Returns:
            List of performance metrics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with self._lock:
            return [
                metrics for metrics in self.metrics_history
                if metrics.timestamp >= cutoff_time
            ]
    
    def get_function_metrics(self) -> Dict[str, FunctionMetrics]:
        """Get function execution metrics."""
        with self._lock:
            return dict(self.function_metrics)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with performance summary
        """
        current_metrics = self.get_current_metrics()
        function_metrics = self.get_function_metrics()
        
        # Calculate averages from recent history
        recent_metrics = self.get_metrics_history(hours_back=1)
        
        if recent_metrics:
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        else:
            avg_cpu = current_metrics.cpu_percent
            avg_memory = current_metrics.memory_percent
        
        # Find slowest functions
        slowest_functions = sorted(
            function_metrics.values(),
            key=lambda x: x.avg_time,
            reverse=True
        )[:5]
        
        # Find most called functions
        most_called_functions = sorted(
            function_metrics.values(),
            key=lambda x: x.call_count,
            reverse=True
        )[:5]
        
        return {
            'current_metrics': current_metrics.to_dict(),
            'averages': {
                'cpu_percent': round(avg_cpu, 2),
                'memory_percent': round(avg_memory, 2)
            },
            'slowest_functions': [f.to_dict() for f in slowest_functions],
            'most_called_functions': [f.to_dict() for f in most_called_functions],
            'total_functions_tracked': len(function_metrics),
            'metrics_history_count': len(self.metrics_history)
        }
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get performance optimization recommendations.
        
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        current_metrics = self.get_current_metrics()
        function_metrics = self.get_function_metrics()
        
        # High CPU usage
        if current_metrics.cpu_percent > self.cpu_threshold:
            recommendations.append({
                'type': 'high_cpu',
                'severity': 'warning',
                'message': f'High CPU usage: {current_metrics.cpu_percent:.1f}%',
                'suggestion': 'Consider optimizing CPU-intensive operations or adding caching'
            })
        
        # High memory usage
        if current_metrics.memory_percent > self.memory_threshold:
            recommendations.append({
                'type': 'high_memory',
                'severity': 'warning',
                'message': f'High memory usage: {current_metrics.memory_percent:.1f}%',
                'suggestion': 'Consider implementing memory optimization or garbage collection'
            })
        
        # Slow functions
        slow_functions = [
            f for f in function_metrics.values()
            if f.avg_time > self.response_time_threshold
        ]
        
        if slow_functions:
            for func in slow_functions[:3]:  # Top 3 slowest
                recommendations.append({
                    'type': 'slow_function',
                    'severity': 'info',
                    'message': f'Slow function: {func.function_name} ({func.avg_time:.2f}s avg)',
                    'suggestion': 'Consider optimizing this function or adding caching'
                })
        
        # High thread count
        if current_metrics.active_threads > 50:
            recommendations.append({
                'type': 'high_thread_count',
                'severity': 'info',
                'message': f'High thread count: {current_metrics.active_threads}',
                'suggestion': 'Consider using thread pools or async operations'
            })
        
        return recommendations
    
    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        with self._lock:
            self.metrics_history.clear()
            self.function_metrics.clear()
        logger.info("Performance metrics reset")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        logger.info("Performance monitoring loop started")
        
        while self.monitoring_active:
            try:
                # Collect current metrics
                metrics = self.get_current_metrics()
                
                with self._lock:
                    self.metrics_history.append(metrics)
                    
                    # Keep only recent history (last 24 hours)
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    self.metrics_history = [
                        m for m in self.metrics_history
                        if m.timestamp >= cutoff_time
                    ]
                
                # Check for alerts
                self._check_system_alerts(metrics)
                
                # Sleep until next monitoring interval
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
        
        logger.info("Performance monitoring loop stopped")
    
    def _check_system_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for system performance alerts."""
        # High CPU alert
        if metrics.cpu_percent > self.cpu_threshold:
            self._trigger_alert(
                "high_cpu",
                {
                    "cpu_percent": metrics.cpu_percent,
                    "threshold": self.cpu_threshold
                }
            )
        
        # High memory alert
        if metrics.memory_percent > self.memory_threshold:
            self._trigger_alert(
                "high_memory",
                {
                    "memory_percent": metrics.memory_percent,
                    "memory_mb": metrics.memory_mb,
                    "threshold": self.memory_threshold
                }
            )
    
    def _trigger_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Trigger performance alert."""
        logger.warning(f"Performance alert: {alert_type} - {data}")
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")


def performance_monitor(func_name: Optional[str] = None):
    """
    Decorator for monitoring function performance.
    
    Args:
        func_name: Optional custom name for the function
    """
    def decorator(func):
        name = func_name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.measure_execution(name):
                return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.measure_execution(name):
                return await func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    
    return decorator


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None
_monitor_lock = threading.Lock()


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get global performance monitor instance.
    
    Returns:
        PerformanceMonitor instance
    """
    global _performance_monitor
    
    if _performance_monitor is None:
        with _monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = PerformanceMonitor()
    
    return _performance_monitor


def start_performance_monitoring() -> None:
    """Start global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.start_monitoring()


def stop_performance_monitoring() -> None:
    """Stop global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.stop_monitoring()