#!/usr/bin/env python3
"""
Performance profiling tools for AllSeeingEye
"""

import time
import cProfile
import pstats
import io
import logging
import functools
import threading
import psutil
import os
from typing import Any, Callable, Dict, Optional, List, Tuple

# Configure logging
logger = logging.getLogger("Profiler")


class PerformanceStats:
    """Class for tracking performance statistics"""
    
    def __init__(self):
        """Initialize performance statistics"""
        self.start_time = time.time()
        self.end_time = None
        self.duration = 0
        self.memory_start = self._get_memory_usage()
        self.memory_end = None
        self.memory_diff = 0
        self.cpu_percent = 0
        self.call_count = 0
        self.file_count = 0
        self.total_size = 0
        self.events = []
    
    def stop(self):
        """Stop tracking and calculate final statistics"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.memory_end = self._get_memory_usage()
        self.memory_diff = self.memory_end - self.memory_start
        
        # Try to get CPU percentage for the current process
        try:
            process = psutil.Process(os.getpid())
            self.cpu_percent = process.cpu_percent(interval=0.1)
        except Exception as e:
            logger.warning(f"Error getting CPU stats: {e}")
    
    def add_event(self, name: str, data: Dict[str, Any] = None):
        """
        Add a performance event with timestamp.
        
        Args:
            name: Name of the event
            data: Additional data for the event
        """
        event = {
            "name": name,
            "timestamp": time.time(),
            "relative_time": time.time() - self.start_time,
            "data": data or {}
        }
        self.events.append(event)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert performance stats to a dictionary.
        
        Returns:
            Dictionary of performance statistics
        """
        return {
            "duration": self.duration,
            "memory_start_mb": self.memory_start / (1024 * 1024),
            "memory_end_mb": self.memory_end / (1024 * 1024) if self.memory_end else None,
            "memory_diff_mb": self.memory_diff / (1024 * 1024),
            "cpu_percent": self.cpu_percent,
            "call_count": self.call_count,
            "file_count": self.file_count,
            "total_size_mb": self.total_size / (1024 * 1024) if self.total_size else 0,
            "events": self.events
        }
    
    def _get_memory_usage(self) -> int:
        """
        Get current memory usage.
        
        Returns:
            Memory usage in bytes
        """
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except Exception as e:
            logger.warning(f"Error getting memory usage: {e}")
            return 0


class Profiler:
    """Performance profiler for AllSeeingEye"""
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the profiler.
        
        Args:
            enabled: Whether profiling is enabled
        """
        self.enabled = enabled
        self.stats = PerformanceStats()
        self._profiler = None
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
    
    def start(self):
        """Start performance profiling"""
        if not self.enabled:
            return
        
        # Reset stats
        self.stats = PerformanceStats()
        
        # Start cProfile if available
        try:
            self._profiler = cProfile.Profile()
            self._profiler.enable()
        except Exception as e:
            logger.warning(f"Error starting cProfile: {e}")
        
        # Start monitoring thread for continuous stats
        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(target=self._monitor_resources)
        self._monitoring_thread.daemon = True
        self._monitoring_thread.start()
        
        logger.debug("Profiler started")
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop performance profiling and return statistics.
        
        Returns:
            Dictionary of performance statistics
        """
        if not self.enabled:
            return {}
        
        # Stop cProfile
        if self._profiler:
            self._profiler.disable()
        
        # Stop monitoring thread
        if self._monitoring_thread:
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=1.0)
        
        # Finalize stats
        self.stats.stop()
        
        logger.debug(f"Profiler stopped. Duration: {self.stats.duration:.2f}s")
        
        return self.stats.to_dict()
    
    def add_event(self, name: str, data: Dict[str, Any] = None):
        """
        Add a performance event.
        
        Args:
            name: Name of the event
            data: Additional data for the event
        """
        if self.enabled:
            self.stats.add_event(name, data)
    
    def get_profile_stats(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Get detailed profile statistics.
        
        Args:
            top_n: Number of top functions to include
            
        Returns:
            List of function statistics
        """
        if not self.enabled or not self._profiler:
            return []
        
        # Capture stats in a string stream
        s = io.StringIO()
        ps = pstats.Stats(self._profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(top_n)
        
        # Parse the stats
        stats_text = s.getvalue()
        stats_lines = stats_text.split('\n')
        
        # Extract function data (skip header lines)
        result = []
        
        for line in stats_lines[5:]:
            if not line.strip():
                continue
            
            parts = line.strip().split()
            if len(parts) < 6:
                continue
            
            try:
                # Parse the stats line
                # Format is usually: ncalls tottime percall cumtime percall filename:lineno(function)
                ncalls = parts[0]
                tottime = float(parts[1])
                percall1 = float(parts[2])
                cumtime = float(parts[3])
                percall2 = float(parts[4])
                
                # Join the rest for the function name/location
                func_loc = ' '.join(parts[5:])
                
                result.append({
                    "ncalls": ncalls,
                    "tottime": tottime,
                    "percall_tottime": percall1,
                    "cumtime": cumtime,
                    "percall_cumtime": percall2,
                    "function": func_loc
                })
            except Exception:
                # Skip lines that don't parse properly
                continue
            
            if len(result) >= top_n:
                break
        
        return result
    
    def _monitor_resources(self):
        """Background thread to monitor system resources"""
        interval = 1.0  # Check every second
        
        while not self._stop_monitoring.is_set():
            try:
                # Get current process
                process = psutil.Process(os.getpid())
                
                # Get CPU and memory usage
                cpu_percent = process.cpu_percent(interval=0.1)
                memory_info = process.memory_info()
                
                # Record the data
                self.add_event("resource_check", {
                    "cpu_percent": cpu_percent,
                    "memory_rss_mb": memory_info.rss / (1024 * 1024),
                    "memory_vms_mb": memory_info.vms / (1024 * 1024)
                })
                
            except Exception as e:
                logger.debug(f"Error in resource monitoring: {e}")
            
            # Sleep for the interval, but be responsive to stop signals
            self._stop_monitoring.wait(interval)


def profile(func=None, *, enabled=True):
    """
    Decorator for profiling functions.
    
    Args:
        func: Function to profile
        enabled: Whether profiling is enabled
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if not enabled:
                return f(*args, **kwargs)
            
            profiler = Profiler(enabled=True)
            profiler.start()
            
            try:
                result = f(*args, **kwargs)
                return result
            finally:
                stats = profiler.stop()
                logger.debug(f"Function {f.__name__} profile: {stats}")
        
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)
