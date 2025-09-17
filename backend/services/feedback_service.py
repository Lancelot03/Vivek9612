from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class FeedbackService:
    """Feedback management service for PM Connect 3.0"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def submit_feedback(self, feedback_data: Dict[str, Any], employee_id: str = None) -> Dict[str, Any]:
        """Submit feedback from user"""
        try:
            feedback = {
                "feedbackId": str(uuid.uuid4()),
                "employeeId": employee_id,
                "rating": feedback_data.get("rating"),  # 1-5 scale
                "category": feedback_data.get("category"),  # "event", "logistics", "food", "accommodation", "overall", "suggestion"
                "subject": feedback_data.get("subject", "").strip(),
                "message": feedback_data.get("message", "").strip(),
                "anonymous": feedback_data.get("anonymous", False),
                "submissionTimestamp": datetime.utcnow(),
                "status": "submitted",  # submitted, reviewed, responded, closed
                "adminResponse": None,
                "adminRespondedBy": None,
                "adminResponseTimestamp": None,
                "tags": feedback_data.get("tags", []),  # For categorization
                "priority": feedback_data.get("priority", "medium"),  # low, medium, high, urgent
                "attachments": feedback_data.get("attachments", []),  # For future file attachments
                "isPublic": feedback_data.get("isPublic", False),  # For public testimonials
                "sentiment": self._analyze_sentiment(feedback_data.get("message", "")),
                "ipAddress": feedback_data.get("ipAddress"),
                "userAgent": feedback_data.get("userAgent")
            }
            
            # Insert feedback
            result = await self.db.feedback.insert_one(feedback)
            
            # Update user's feedback count
            if employee_id:
                await self.db.users.update_one(
                    {"employeeId": employee_id},
                    {"$inc": {"feedbackCount": 1}, "$set": {"lastFeedbackDate": datetime.utcnow()}}
                )
            
            return {
                "feedbackId": feedback["feedbackId"],
                "message": "Feedback submitted successfully",
                "submissionTimestamp": feedback["submissionTimestamp"],
                "tracking": {
                    "feedbackId": feedback["feedbackId"],
                    "status": feedback["status"],
                    "category": feedback["category"]
                }
            }
            
        except Exception as e:
            logger.error(f"Feedback submission failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")
    
    async def get_feedback_by_id(self, feedback_id: str) -> Dict[str, Any]:
        """Get specific feedback by ID"""
        try:
            feedback = await self.db.feedback.find_one({"feedbackId": feedback_id})
            if not feedback:
                raise HTTPException(status_code=404, detail="Feedback not found")
            
            # Remove internal fields for user response
            feedback.pop('_id', None)
            feedback.pop('ipAddress', None)
            feedback.pop('userAgent', None)
            
            return feedback
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Feedback retrieval failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Feedback retrieval failed: {str(e)}")
    
    async def get_user_feedback(self, employee_id: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get all feedback submitted by a specific user"""
        try:
            skip = (page - 1) * limit
            
            # Get user's feedback
            feedback_list = await self.db.feedback.find(
                {"employeeId": employee_id}
            ).sort("submissionTimestamp", -1).skip(skip).limit(limit).to_list(limit)
            
            total_count = await self.db.feedback.count_documents({"employeeId": employee_id})
            total_pages = (total_count + limit - 1) // limit
            
            # Clean up internal fields
            for feedback in feedback_list:
                feedback.pop('_id', None)
                feedback.pop('ipAddress', None)
                feedback.pop('userAgent', None)
            
            return {
                "feedback": feedback_list,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_count,
                    "limit": limit,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"User feedback retrieval failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"User feedback retrieval failed: {str(e)}")
    
    async def get_all_feedback_admin(self, 
                                   page: int = 1, 
                                   limit: int = 20,
                                   category: Optional[str] = None,
                                   status: Optional[str] = None,
                                   priority: Optional[str] = None,
                                   rating: Optional[int] = None) -> Dict[str, Any]:
        """Get all feedback for admin review with filters"""
        try:
            skip = (page - 1) * limit
            
            # Build filter query
            query = {}
            if category:
                query["category"] = category
            if status:
                query["status"] = status
            if priority:
                query["priority"] = priority
            if rating:
                query["rating"] = rating
            
            # Get feedback with user details
            pipeline = [
                {"$match": query},
                {"$sort": {"submissionTimestamp": -1}},
                {"$skip": skip},
                {"$limit": limit},
                {
                    "$lookup": {
                        "from": "invitees",
                        "localField": "employeeId",
                        "foreignField": "employeeId",
                        "as": "user_details"
                    }
                },
                {
                    "$unwind": {
                        "path": "$user_details",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "feedbackId": 1,
                        "employeeId": 1,
                        "rating": 1,
                        "category": 1,
                        "subject": 1,
                        "message": 1,
                        "anonymous": 1,
                        "submissionTimestamp": 1,
                        "status": 1,
                        "adminResponse": 1,
                        "adminRespondedBy": 1,
                        "adminResponseTimestamp": 1,
                        "tags": 1,
                        "priority": 1,
                        "isPublic": 1,
                        "sentiment": 1,
                        "employeeName": "$user_details.employeeName",
                        "cadre": "$user_details.cadre",
                        "projectName": "$user_details.projectName"
                    }
                }
            ]
            
            feedback_list = await self.db.feedback.aggregate(pipeline).to_list(limit)
            total_count = await self.db.feedback.count_documents(query)
            total_pages = (total_count + limit - 1) // limit
            
            return {
                "feedback": feedback_list,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_count,
                    "limit": limit,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                },
                "filters_applied": {
                    "category": category,
                    "status": status,
                    "priority": priority,
                    "rating": rating
                }
            }
            
        except Exception as e:
            logger.error(f"Admin feedback retrieval failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Admin feedback retrieval failed: {str(e)}")
    
    async def respond_to_feedback(self, 
                                feedback_id: str, 
                                admin_response: str, 
                                admin_employee_id: str,
                                new_status: str = "responded") -> Dict[str, Any]:
        """Admin response to feedback"""
        try:
            update_data = {
                "adminResponse": admin_response.strip(),
                "adminRespondedBy": admin_employee_id,
                "adminResponseTimestamp": datetime.utcnow(),
                "status": new_status
            }
            
            result = await self.db.feedback.update_one(
                {"feedbackId": feedback_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Feedback not found")
            
            if result.modified_count == 0:
                raise HTTPException(status_code=400, detail="Feedback not updated")
            
            return {
                "message": "Admin response added successfully",
                "feedbackId": feedback_id,
                "status": new_status,
                "responseTimestamp": update_data["adminResponseTimestamp"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Admin response failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Admin response failed: {str(e)}")
    
    async def get_feedback_analytics(self) -> Dict[str, Any]:
        """Get feedback analytics for admin dashboard"""
        try:
            # Aggregate feedback statistics
            pipeline = [
                {
                    "$facet": {
                        "rating_distribution": [
                            {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
                            {"$sort": {"_id": 1}}
                        ],
                        "category_distribution": [
                            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
                        ],
                        "status_distribution": [
                            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                        ],
                        "priority_distribution": [
                            {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
                        ],
                        "sentiment_distribution": [
                            {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
                        ],
                        "monthly_trends": [
                            {
                                "$group": {
                                    "_id": {
                                        "year": {"$year": "$submissionTimestamp"},
                                        "month": {"$month": "$submissionTimestamp"}
                                    },
                                    "count": {"$sum": 1},
                                    "avg_rating": {"$avg": "$rating"}
                                }
                            },
                            {"$sort": {"_id.year": -1, "_id.month": -1}},
                            {"$limit": 12}
                        ]
                    }
                }
            ]
            
            results = await self.db.feedback.aggregate(pipeline).to_list(1)
            
            if not results:
                return {"message": "No feedback data available"}
            
            analytics = results[0]
            
            # Calculate overall statistics
            total_feedback = await self.db.feedback.count_documents({})
            avg_rating = await self.db.feedback.aggregate([
                {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
            ]).to_list(1)
            
            overall_avg_rating = avg_rating[0]["avg_rating"] if avg_rating else 0
            
            # Recent feedback (last 7 days)
            recent_feedback_count = await self.db.feedback.count_documents({
                "submissionTimestamp": {"$gte": datetime.utcnow() - timedelta(days=7)}
            })
            
            return {
                "overview": {
                    "total_feedback": total_feedback,
                    "average_rating": round(overall_avg_rating, 2),
                    "recent_feedback_7_days": recent_feedback_count
                },
                "distributions": {
                    "ratings": {item["_id"]: item["count"] for item in analytics["rating_distribution"]},
                    "categories": {item["_id"]: item["count"] for item in analytics["category_distribution"]},
                    "statuses": {item["_id"]: item["count"] for item in analytics["status_distribution"]},
                    "priorities": {item["_id"]: item["count"] for item in analytics["priority_distribution"]},
                    "sentiments": {item["_id"]: item["count"] for item in analytics["sentiment_distribution"]}
                },
                "trends": {
                    "monthly": [
                        {
                            "period": f"{item['_id']['year']}-{item['_id']['month']:02d}",
                            "count": item["count"],
                            "avg_rating": round(item["avg_rating"], 2)
                        } for item in analytics["monthly_trends"]
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Feedback analytics failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Feedback analytics failed: {str(e)}")
    
    async def update_feedback_status(self, feedback_id: str, new_status: str, admin_employee_id: str) -> Dict[str, Any]:
        """Update feedback status"""
        try:
            valid_statuses = ["submitted", "reviewed", "responded", "closed", "escalated"]
            if new_status not in valid_statuses:
                raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
            
            update_data = {
                "status": new_status,
                "lastUpdatedBy": admin_employee_id,
                "lastUpdatedTimestamp": datetime.utcnow()
            }
            
            result = await self.db.feedback.update_one(
                {"feedbackId": feedback_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Feedback not found")
            
            return {
                "message": f"Feedback status updated to {new_status}",
                "feedbackId": feedback_id,
                "new_status": new_status,
                "updatedTimestamp": update_data["lastUpdatedTimestamp"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Status update failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Status update failed: {str(e)}")
    
    def _analyze_sentiment(self, message: str) -> str:
        """Simple sentiment analysis (can be enhanced with ML models)"""
        if not message:
            return "neutral"
        
        message_lower = message.lower()
        
        # Positive keywords
        positive_words = [
            "excellent", "amazing", "great", "fantastic", "wonderful", "awesome", 
            "good", "nice", "happy", "satisfied", "pleased", "love", "perfect",
            "outstanding", "brilliant", "superb", "marvelous", "impressive"
        ]
        
        # Negative keywords
        negative_words = [
            "terrible", "awful", "bad", "horrible", "worst", "hate", "disappointed",
            "frustrated", "angry", "poor", "disgusting", "unacceptable", "pathetic",
            "useless", "annoying", "irritating", "ridiculous", "inadequate"
        ]
        
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    async def get_public_testimonials(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get public testimonials for display"""
        try:
            testimonials = await self.db.feedback.find({
                "isPublic": True,
                "rating": {"$gte": 4},  # Only positive testimonials
                "status": {"$in": ["reviewed", "responded"]}
            }).sort("submissionTimestamp", -1).limit(limit).to_list(limit)
            
            # Clean up for public display
            public_testimonials = []
            for testimonial in testimonials:
                if testimonial.get("anonymous", False):
                    name = "Anonymous Participant"
                else:
                    # Get employee name
                    invitee = await self.db.invitees.find_one({"employeeId": testimonial.get("employeeId")})
                    name = invitee.get("employeeName", "Anonymous") if invitee else "Anonymous"
                
                public_testimonials.append({
                    "rating": testimonial.get("rating"),
                    "message": testimonial.get("message", ""),
                    "category": testimonial.get("category", ""),
                    "author": name,
                    "date": testimonial.get("submissionTimestamp"),
                    "sentiment": testimonial.get("sentiment", "neutral")
                })
            
            return public_testimonials
            
        except Exception as e:
            logger.error(f"Public testimonials retrieval failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Public testimonials retrieval failed: {str(e)}")