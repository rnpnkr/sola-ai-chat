import asyncio
import logging
from typing import Dict
from datetime import datetime
from .memory_coordinator import get_memory_coordinator

logger = logging.getLogger(__name__)

class MemoryHealthMonitor:
    """Monitor memory system health and performance"""
    def __init__(self):
        self.coordinator = get_memory_coordinator()
        self.monitoring_active = False
    async def start_monitoring(self):
        """Start health monitoring loop"""
        self.monitoring_active = True
        asyncio.create_task(self._monitoring_loop())
        logger.info("Memory health monitoring started")
    async def _monitoring_loop(self):
        """Monitor memory system health every 30 seconds"""
        while self.monitoring_active:
            try:
                stats = self.coordinator.get_stats()
                # Check for concerning patterns
                if len(stats["pending_operations"]) > 50:
                    logger.warning(f"High pending operations: {stats}")
                if stats["deduplication_cache_size"] > 1000:
                    logger.warning(f"Large deduplication cache: {stats['deduplication_cache_size']}")
                # Log healthy stats periodically
                if datetime.now().minute % 5 == 0:  # Every 5 minutes
                    logger.info(f"Memory system health: {stats}")
                await asyncio.sleep(30)  # 30-second monitoring interval
            except Exception as e:
                logger.error(f"Error in memory health monitoring: {e}")
                await asyncio.sleep(60)  # Longer wait on error
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        logger.info("Memory health monitoring stopped")
    async def get_health_report(self) -> Dict:
        """Get comprehensive health report"""
        try:
            stats = self.coordinator.get_stats()
            health_report = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "coordinator_stats": stats,
                "recommendations": []
            }
            # Health analysis
            if len(stats["pending_operations"]) > 100:
                health_report["status"] = "degraded"
                health_report["recommendations"].append("High memory operation backlog detected")
            if stats["deduplication_cache_size"] > 2000:
                health_report["status"] = "warning"
                health_report["recommendations"].append("Consider cache cleanup")
            return health_report
        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return {"status": "error", "error": str(e)}

# Global instance
memory_health_monitor = MemoryHealthMonitor() 