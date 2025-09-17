import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import psutil
import os
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class PerformanceService:
    """Performance monitoring and optimization service for PM Connect 3.0"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.cache = {}
        self.cache_ttl = {}
        self.performance_metrics = {
            "api_calls": {},
            "response_times": {},
            "cache_hits": 0,
            "cache_misses": 0,
            "active_connections": 0
        }
    
    # ============ DATABASE OPTIMIZATION ============
    
    async def create_database_indexes(self):
        """Create optimized database indexes for better query performance"""
        try:
            index_results = []
            
            # Invitees collection indexes
            await self.db.invitees.create_index("employeeId", unique=True)
            await self.db.invitees.create_index("hasResponded")
            await self.db.invitees.create_index("cadre")
            await self.db.invitees.create_index("projectName")
            await self.db.invitees.create_index([("employeeName", 1)])
            index_results.append("invitees indexes created")
            
            # Responses collection indexes
            await self.db.responses.create_index("employeeId", unique=True)
            await self.db.responses.create_index("submissionTimestamp")
            await self.db.responses.create_index("requiresAccommodation")
            await self.db.responses.create_index("foodPreference")
            await self.db.responses.create_index("departureTimePreference")
            await self.db.responses.create_index("arrivalTimePreference")
            index_results.append("responses indexes created")
            
            # Users collection indexes
            await self.db.users.create_index("employeeId", unique=True)
            await self.db.users.create_index("role")
            await self.db.users.create_index("isActive")
            await self.db.users.create_index("lastLogin")
            index_results.append("users indexes created")
            
            # Gallery photos collection indexes
            await self.db.gallery_photos.create_index("employeeId")
            await self.db.gallery_photos.create_index("eventVersion")
            await self.db.gallery_photos.create_index("uploadTimestamp")
            index_results.append("gallery_photos indexes created")
            
            # Cab allocations collection indexes
            await self.db.cab_allocations.create_index("cabNumber")
            await self.db.cab_allocations.create_index("assignedMembers")
            index_results.append("cab_allocations indexes created")
            
            # Audit logs collection indexes (for performance monitoring)
            await self.db.audit_logs.create_index("employeeId")
            await self.db.audit_logs.create_index("action")
            await self.db.audit_logs.create_index("timestamp")
            index_results.append("audit_logs indexes created")
            
            # Export tasks collection indexes
            await self.db.export_tasks.create_index("taskId", unique=True)
            await self.db.export_tasks.create_index("status")
            await self.db.export_tasks.create_index("createdAt")
            index_results.append("export_tasks indexes created")
            
            return {
                "success": True,
                "indexes_created": index_results,
                "total_collections": len(index_results),
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Database index creation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Index creation failed: {str(e)}")
    
    # ============ CACHING SYSTEM ============
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache_ttl:
            return False
        return datetime.utcnow() < self.cache_ttl[key]
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve data from cache if valid"""
        if key in self.cache and self._is_cache_valid(key):
            self.performance_metrics["cache_hits"] += 1
            return self.cache[key]
        
        self.performance_metrics["cache_misses"] += 1
        return None
    
    def set_cached_data(self, key: str, data: Any, ttl_minutes: int = 5):
        """Store data in cache with TTL"""
        self.cache[key] = data
        self.cache_ttl[key] = datetime.utcnow() + timedelta(minutes=ttl_minutes)
    
    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries, optionally by pattern"""
        if pattern:
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
                del self.cache_ttl[key]
        else:
            self.cache.clear()
            self.cache_ttl.clear()
    
    # ============ OPTIMIZED QUERIES ============
    
    async def get_dashboard_stats_optimized(self) -> Dict[str, Any]:
        """Optimized dashboard statistics with caching"""
        cache_key = "dashboard_stats"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        start_time = time.time()
        
        # Use aggregation pipeline for better performance
        pipeline = [
            {
                "$facet": {
                    "invitee_stats": [
                        {"$group": {"_id": None, "total": {"$sum": 1}, "responded": {"$sum": {"$cond": ["$hasResponded", 1, 0]}}}}
                    ],
                    "accommodation_stats": [
                        {"$match": {"requiresAccommodation": True}},
                        {"$count": "accommodation_requests"}
                    ],
                    "food_preferences": [
                        {"$group": {"_id": "$foodPreference", "count": {"$sum": 1}}}
                    ]
                }
            }
        ]
        
        # Run parallel queries for better performance
        invitee_results = await self.db.invitees.aggregate([
            {"$group": {"_id": None, "total": {"$sum": 1}, "responded": {"$sum": {"$cond": ["$hasResponded", 1, 0]}}}}
        ]).to_list(1)
        
        accommodation_count = await self.db.responses.count_documents({"requiresAccommodation": True})
        
        food_prefs = await self.db.responses.aggregate([
            {"$group": {"_id": "$foodPreference", "count": {"$sum": 1}}}
        ]).to_list(10)
        
        # Compile results
        invitee_stats = invitee_results[0] if invitee_results else {"total": 0, "responded": 0}
        
        stats = {
            "totalInvitees": invitee_stats["total"],
            "rsvpYes": invitee_stats["responded"],
            "rsvpNo": invitee_stats["total"] - invitee_stats["responded"],
            "accommodationRequests": accommodation_count,
            "foodPreferences": {pref["_id"]: pref["count"] for pref in food_prefs},
            "cached": False,
            "query_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        # Cache for 2 minutes
        self.set_cached_data(cache_key, stats, ttl_minutes=2)
        
        return stats
    
    async def get_paginated_invitees(self, page: int = 1, limit: int = 50, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get paginated invitees with optimized queries"""
        
        # Build query with filters
        query = filters or {}
        skip = (page - 1) * limit
        
        # Use parallel queries for count and data
        count_task = self.db.invitees.count_documents(query)
        data_task = self.db.invitees.find(query).skip(skip).limit(limit).to_list(limit)
        
        total_count, invitees = await asyncio.gather(count_task, data_task)
        
        # Convert ObjectId to string for JSON serialization
        for invitee in invitees:
            if '_id' in invitee:
                invitee['_id'] = str(invitee['_id'])
        
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "items": invitees,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "limit": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    async def get_paginated_responses(self, page: int = 1, limit: int = 50, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get paginated responses with employee details"""
        
        query = filters or {}
        skip = (page - 1) * limit
        
        # Optimized aggregation with pagination
        pipeline = [
            {"$match": query},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "invitees",
                    "localField": "employeeId", 
                    "foreignField": "employeeId",
                    "as": "invitee_details"
                }
            },
            {
                "$unwind": {
                    "path": "$invitee_details",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "responseId": 1,
                    "employeeId": 1,
                    "mobileNumber": 1,
                    "requiresAccommodation": 1,
                    "arrivalDate": 1,
                    "departureDate": 1,
                    "foodPreference": 1,
                    "departureTimePreference": 1,
                    "arrivalTimePreference": 1,
                    "specialFlightRequirements": 1,
                    "submissionTimestamp": 1,
                    "employeeName": "$invitee_details.employeeName",
                    "cadre": "$invitee_details.cadre",
                    "projectName": "$invitee_details.projectName"
                }
            }
        ]
        
        # Parallel execution
        count_task = self.db.responses.count_documents(query)
        data_task = self.db.responses.aggregate(pipeline).to_list(limit)
        
        total_count, responses = await asyncio.gather(count_task, data_task)
        
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "items": responses,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "limit": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    # ============ PERFORMANCE MONITORING ============
    
    def record_api_call(self, endpoint: str, response_time: float, status_code: int):
        """Record API call metrics"""
        if endpoint not in self.performance_metrics["api_calls"]:
            self.performance_metrics["api_calls"][endpoint] = {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "errors": 0
            }
        
        metrics = self.performance_metrics["api_calls"][endpoint]
        metrics["count"] += 1
        metrics["total_time"] += response_time
        metrics["avg_time"] = metrics["total_time"] / metrics["count"]
        
        if status_code >= 400:
            metrics["errors"] += 1
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics"""
        
        # System resource metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database metrics
        db_stats = await self.db.command("dbStats")
        
        # Application metrics
        cache_hit_rate = 0
        total_cache_requests = self.performance_metrics["cache_hits"] + self.performance_metrics["cache_misses"]
        if total_cache_requests > 0:
            cache_hit_rate = (self.performance_metrics["cache_hits"] / total_cache_requests) * 100
        
        return {
            "timestamp": datetime.utcnow(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "database": {
                "collections": db_stats.get("collections", 0),
                "data_size_mb": round(db_stats.get("dataSize", 0) / (1024**2), 2),
                "storage_size_mb": round(db_stats.get("storageSize", 0) / (1024**2), 2),
                "indexes": db_stats.get("indexes", 0)
            },
            "application": {
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                "cache_entries": len(self.cache),
                "active_connections": self.performance_metrics["active_connections"],
                "api_endpoints_monitored": len(self.performance_metrics["api_calls"])
            },
            "api_performance": self.performance_metrics["api_calls"]
        }
    
    async def run_performance_test(self, concurrent_users: int = 10, duration_seconds: int = 30) -> Dict[str, Any]:
        """Run a performance test simulation"""
        
        start_time = time.time()
        results = {
            "test_config": {
                "concurrent_users": concurrent_users,
                "duration_seconds": duration_seconds,
                "start_time": start_time
            },
            "results": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_response_time": 0,
                "max_response_time": 0,
                "min_response_time": float('inf'),
                "requests_per_second": 0
            }
        }
        
        # Simulate concurrent API calls
        async def simulate_user():
            user_requests = 0
            user_total_time = 0
            
            while time.time() - start_time < duration_seconds:
                request_start = time.time()
                try:
                    # Simulate dashboard stats call (most common endpoint)
                    await self.get_dashboard_stats_optimized()
                    user_requests += 1
                    results["results"]["successful_requests"] += 1
                except Exception:
                    results["results"]["failed_requests"] += 1
                    
                request_time = time.time() - request_start
                user_total_time += request_time
                
                # Update response time metrics
                if request_time > results["results"]["max_response_time"]:
                    results["results"]["max_response_time"] = request_time
                if request_time < results["results"]["min_response_time"]:
                    results["results"]["min_response_time"] = request_time
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
            
            return user_requests, user_total_time
        
        # Run concurrent users
        user_tasks = [simulate_user() for _ in range(concurrent_users)]
        user_results = await asyncio.gather(*user_tasks)
        
        # Compile results
        total_requests = sum(requests for requests, _ in user_results)
        total_time = sum(total_time for _, total_time in user_results)
        
        results["results"]["total_requests"] = total_requests
        results["results"]["avg_response_time"] = total_time / total_requests if total_requests > 0 else 0
        results["results"]["requests_per_second"] = total_requests / duration_seconds
        results["results"]["test_duration"] = time.time() - start_time
        
        if results["results"]["min_response_time"] == float('inf'):
            results["results"]["min_response_time"] = 0
        
        return results
    
    # ============ OPTIMIZATION RECOMMENDATIONS ============
    
    async def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Generate performance optimization recommendations"""
        
        recommendations = []
        metrics = await self.get_system_metrics()
        
        # CPU recommendations
        if metrics["system"]["cpu_percent"] > 80:
            recommendations.append({
                "type": "high_cpu",
                "priority": "high",
                "message": "CPU usage is high. Consider implementing response caching and query optimization.",
                "actions": ["Enable response caching", "Optimize database queries", "Add API rate limiting"]
            })
        
        # Memory recommendations
        if metrics["system"]["memory_percent"] > 85:
            recommendations.append({
                "type": "high_memory",
                "priority": "high", 
                "message": "Memory usage is high. Consider implementing cache size limits.",
                "actions": ["Set cache TTL limits", "Implement cache eviction policy", "Monitor memory leaks"]
            })
        
        # Database recommendations
        if metrics["database"]["data_size_mb"] > 1000:
            recommendations.append({
                "type": "large_database",
                "priority": "medium",
                "message": "Database size is growing. Consider implementing data archiving.",
                "actions": ["Archive old responses", "Implement data retention policy", "Add data compression"]
            })
        
        # Cache recommendations
        if metrics["application"]["cache_hit_rate_percent"] < 70:
            recommendations.append({
                "type": "low_cache_hit_rate",
                "priority": "medium",
                "message": "Cache hit rate is low. Consider adjusting cache TTL and strategy.",
                "actions": ["Increase cache TTL", "Cache more static data", "Implement smarter cache keys"]
            })
        
        # API performance recommendations
        slow_endpoints = []
        for endpoint, stats in metrics["api_performance"].items():
            if stats["avg_time"] > 1.0:  # More than 1 second
                slow_endpoints.append(endpoint)
        
        if slow_endpoints:
            recommendations.append({
                "type": "slow_endpoints",
                "priority": "high",
                "message": f"Slow endpoints detected: {', '.join(slow_endpoints)}",
                "actions": ["Add response caching", "Optimize database queries", "Implement pagination"]
            })
        
        return {
            "timestamp": datetime.utcnow(),
            "recommendations": recommendations,
            "performance_score": self._calculate_performance_score(metrics),
            "metrics_summary": {
                "cpu_health": "good" if metrics["system"]["cpu_percent"] < 70 else "warning" if metrics["system"]["cpu_percent"] < 85 else "critical",
                "memory_health": "good" if metrics["system"]["memory_percent"] < 75 else "warning" if metrics["system"]["memory_percent"] < 90 else "critical",
                "cache_health": "good" if metrics["application"]["cache_hit_rate_percent"] > 80 else "warning"
            }
        }
    
    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> int:
        """Calculate overall performance score (0-100)"""
        score = 100
        
        # CPU penalty
        if metrics["system"]["cpu_percent"] > 70:
            score -= (metrics["system"]["cpu_percent"] - 70) * 0.5
        
        # Memory penalty
        if metrics["system"]["memory_percent"] > 75:
            score -= (metrics["system"]["memory_percent"] - 75) * 0.5
        
        # Cache bonus
        cache_hit_rate = metrics["application"]["cache_hit_rate_percent"]
        if cache_hit_rate > 80:
            score += (cache_hit_rate - 80) * 0.2
        else:
            score -= (80 - cache_hit_rate) * 0.3
        
        return max(0, min(100, int(score)))