from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import httpx
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class WhatsAppService:
    """WhatsApp messaging service for PM Connect 3.0"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.whatsapp_node_service_url = "http://localhost:3001"  # Node.js service URL
        self.message_templates = {
            "rsvp_reminder": {
                "template": "🎉 PM Connect 3.0 Reminder\n\nHi {name}!\n\nYou haven't submitted your RSVP yet. Please respond by {deadline}.\n\n✅ Click here to RSVP: {rsvp_link}\n\nFor any queries, contact the admin team.",
                "variables": ["name", "deadline", "rsvp_link"]
            },
            "event_update": {
                "template": "📢 PM Connect 3.0 Update\n\nHi {name}!\n\n{update_message}\n\nBest regards,\nPM Connect Team",
                "variables": ["name", "update_message"]
            },
            "accommodation_confirmation": {
                "template": "🏨 Accommodation Confirmed\n\nHi {name}!\n\nYour accommodation has been confirmed:\n📅 Arrival: {arrival_date}\n📅 Departure: {departure_date}\n🚗 Flight preferences noted: {flight_preferences}\n\nSee you at PM Connect 3.0!",
                "variables": ["name", "arrival_date", "departure_date", "flight_preferences"]
            },
            "cab_allocation": {
                "template": "🚕 Cab Allocation - PM Connect 3.0\n\nHi {name}!\n\nYour cab details:\n🚗 Cab Number: {cab_number}\n📍 Pickup Location: {pickup_location}\n🕐 Pickup Time: {pickup_time}\n👥 Co-passengers: {passengers}\n\nDriver details will be shared separately.",
                "variables": ["name", "cab_number", "pickup_location", "pickup_time", "passengers"]
            },
            "feedback_thank_you": {
                "template": "🙏 Thank You for Your Feedback!\n\nHi {name}!\n\nWe received your {rating}-star feedback about PM Connect 3.0. Your input helps us improve future events.\n\n{admin_response}\n\nBest regards,\nPM Connect Team",
                "variables": ["name", "rating", "admin_response"]
            }
        }
    
    async def check_whatsapp_status(self) -> Dict[str, Any]:
        """Check WhatsApp service connection status"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.whatsapp_node_service_url}/status")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"connected": False, "error": "Service unavailable"}
        except Exception as e:
            logger.error(f"WhatsApp status check failed: {str(e)}")
            return {"connected": False, "error": str(e)}
    
    async def get_qr_code(self) -> Optional[str]:
        """Get current QR code for WhatsApp authentication"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.whatsapp_node_service_url}/qr")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("qr")
                return None
        except Exception as e:
            logger.error(f"QR code fetch failed: {str(e)}")
            return None
    
    async def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send individual WhatsApp message"""
        try:
            # Log message attempt
            message_log = {
                "messageId": str(uuid.uuid4()),
                "phoneNumber": phone_number,
                "message": message,
                "sentAt": datetime.utcnow(),
                "status": "pending",
                "attempts": 1,
                "service": "whatsapp"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.whatsapp_node_service_url}/send",
                    json={
                        "phone_number": phone_number,
                        "message": message
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message_log["status"] = "sent" if result.get("success") else "failed"
                    message_log["response"] = result
                else:
                    message_log["status"] = "failed"
                    message_log["error"] = f"HTTP {response.status_code}"
            
            # Store message log
            await self.db.message_logs.insert_one(message_log)
            
            return {
                "success": message_log["status"] == "sent",
                "messageId": message_log["messageId"],
                "status": message_log["status"]
            }
            
        except Exception as e:
            logger.error(f"Message send failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_bulk_messages(self, recipients: List[Dict[str, str]], delay_seconds: int = 2) -> Dict[str, Any]:
        """Send bulk WhatsApp messages with delay between sends"""
        results = {
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "details": []
        }
        
        bulk_id = str(uuid.uuid4())
        
        for recipient in recipients:
            phone_number = recipient.get("phone_number")
            message = recipient.get("message")
            
            if not phone_number or not message:
                results["failed"] += 1
                results["details"].append({
                    "phone_number": phone_number,
                    "status": "failed",
                    "error": "Missing phone number or message"
                })
                continue
            
            # Send message
            result = await self.send_message(phone_number, message)
            
            if result["success"]:
                results["sent"] += 1
                results["details"].append({
                    "phone_number": phone_number,
                    "status": "sent",
                    "messageId": result["messageId"]
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "phone_number": phone_number,
                    "status": "failed",
                    "error": result.get("error", "Unknown error")
                })
            
            # Delay between messages to avoid rate limiting
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
        
        # Log bulk operation
        bulk_log = {
            "bulkId": bulk_id,
            "totalRecipients": results["total"],
            "sentCount": results["sent"],
            "failedCount": results["failed"],
            "createdAt": datetime.utcnow(),
            "service": "whatsapp"
        }
        await self.db.bulk_message_logs.insert_one(bulk_log)
        
        return results
    
    async def send_template_message(self, phone_number: str, template_name: str, variables: Dict[str, str]) -> Dict[str, Any]:
        """Send message using predefined template"""
        try:
            if template_name not in self.message_templates:
                raise ValueError(f"Template '{template_name}' not found")
            
            template = self.message_templates[template_name]
            message = template["template"]
            
            # Replace variables in template
            for var_name, var_value in variables.items():
                message = message.replace(f"{{{var_name}}}", str(var_value))
            
            # Check for unreplaced variables
            import re
            unreplaced = re.findall(r'\{([^}]+)\}', message)
            if unreplaced:
                logger.warning(f"Unreplaced variables in template {template_name}: {unreplaced}")
            
            return await self.send_message(phone_number, message)
            
        except Exception as e:
            logger.error(f"Template message send failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_rsvp_reminders(self, days_before_deadline: int = 3) -> Dict[str, Any]:
        """Send RSVP reminders to users who haven't responded"""
        try:
            # Get invitees who haven't responded
            unresponded_invitees = await self.db.invitees.find({
                "hasResponded": False
            }).to_list(1000)
            
            if not unresponded_invitees:
                return {"message": "No pending RSVPs", "sent": 0}
            
            recipients = []
            for invitee in unresponded_invitees:
                # Get phone number from responses or use a default
                phone_number = invitee.get("phone", "")  # Assume phone field exists
                if not phone_number:
                    continue
                
                variables = {
                    "name": invitee.get("employeeName", "Participant"),
                    "deadline": (datetime.utcnow() + timedelta(days=days_before_deadline)).strftime("%B %d, %Y"),
                    "rsvp_link": f"https://pmconnect.app/rsvp?id={invitee['employeeId']}"
                }
                
                template_result = self.message_templates["rsvp_reminder"]
                message = template_result["template"]
                for var_name, var_value in variables.items():
                    message = message.replace(f"{{{var_name}}}", str(var_value))
                
                recipients.append({
                    "phone_number": phone_number,
                    "message": message
                })
            
            if not recipients:
                return {"message": "No valid phone numbers found", "sent": 0}
            
            # Send bulk reminders
            results = await self.send_bulk_messages(recipients, delay_seconds=3)
            
            return {
                "message": f"RSVP reminders processed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"RSVP reminder sending failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"RSVP reminder failed: {str(e)}")
    
    async def send_event_updates(self, update_message: str, target_group: str = "all") -> Dict[str, Any]:
        """Send event updates to specified group"""
        try:
            # Build query based on target group
            query = {}
            if target_group == "responded":
                query["hasResponded"] = True
            elif target_group == "not_responded":
                query["hasResponded"] = False
            elif target_group == "accommodation":
                # Get employees who need accommodation
                accommodation_responses = await self.db.responses.find({
                    "requiresAccommodation": True
                }).to_list(1000)
                employee_ids = [r["employeeId"] for r in accommodation_responses]
                query["employeeId"] = {"$in": employee_ids}
            
            # Get target invitees
            invitees = await self.db.invitees.find(query).to_list(1000)
            
            if not invitees:
                return {"message": f"No invitees found for group: {target_group}", "sent": 0}
            
            recipients = []
            for invitee in invitees:
                phone_number = invitee.get("phone", "")
                if not phone_number:
                    continue
                
                variables = {
                    "name": invitee.get("employeeName", "Participant"),
                    "update_message": update_message
                }
                
                template_result = self.message_templates["event_update"]
                message = template_result["template"]
                for var_name, var_value in variables.items():
                    message = message.replace(f"{{{var_name}}}", str(var_value))
                
                recipients.append({
                    "phone_number": phone_number,
                    "message": message
                })
            
            # Send bulk updates
            results = await self.send_bulk_messages(recipients, delay_seconds=2)
            
            return {
                "message": f"Event updates sent to {target_group} group",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Event update sending failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Event update failed: {str(e)}")
    
    async def get_message_logs(self, page: int = 1, limit: int = 50, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """Get message delivery logs with pagination"""
        try:
            skip = (page - 1) * limit
            query = {"service": "whatsapp"}
            
            if phone_number:
                query["phoneNumber"] = phone_number
            
            # Get logs
            logs = await self.db.message_logs.find(query)\
                .sort("sentAt", -1)\
                .skip(skip)\
                .limit(limit)\
                .to_list(limit)
            
            total_count = await self.db.message_logs.count_documents(query)
            total_pages = (total_count + limit - 1) // limit
            
            # Clean up logs for response
            for log in logs:
                log.pop('_id', None)
            
            return {
                "logs": logs,
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
            logger.error(f"Message logs retrieval failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Message logs failed: {str(e)}")
    
    async def get_message_analytics(self) -> Dict[str, Any]:
        """Get WhatsApp messaging analytics"""
        try:
            # Aggregate message statistics
            pipeline = [
                {"$match": {"service": "whatsapp"}},
                {
                    "$facet": {
                        "status_distribution": [
                            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                        ],
                        "daily_volume": [
                            {
                                "$group": {
                                    "_id": {
                                        "year": {"$year": "$sentAt"},
                                        "month": {"$month": "$sentAt"},
                                        "day": {"$dayOfMonth": "$sentAt"}
                                    },
                                    "count": {"$sum": 1},
                                    "sent": {"$sum": {"$cond": [{"$eq": ["$status", "sent"]}, 1, 0]}},
                                    "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}
                                }
                            },
                            {"$sort": {"_id.year": -1, "_id.month": -1, "_id.day": -1}},
                            {"$limit": 30}
                        ]
                    }
                }
            ]
            
            results = await self.db.message_logs.aggregate(pipeline).to_list(1)
            
            if not results:
                return {"message": "No message data available"}
            
            analytics = results[0]
            
            # Calculate success rate
            total_messages = await self.db.message_logs.count_documents({"service": "whatsapp"})
            sent_messages = await self.db.message_logs.count_documents({"service": "whatsapp", "status": "sent"})
            success_rate = (sent_messages / total_messages * 100) if total_messages > 0 else 0
            
            return {
                "overview": {
                    "total_messages": total_messages,
                    "sent_messages": sent_messages,
                    "success_rate_percent": round(success_rate, 2)
                },
                "distributions": {
                    "status": {item["_id"]: item["count"] for item in analytics["status_distribution"]}
                },
                "trends": {
                    "daily": [
                        {
                            "date": f"{item['_id']['year']}-{item['_id']['month']:02d}-{item['_id']['day']:02d}",
                            "total": item["count"],
                            "sent": item["sent"],
                            "failed": item["failed"]
                        } for item in analytics["daily_volume"]
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Message analytics failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Message analytics failed: {str(e)}")
    
    def get_available_templates(self) -> Dict[str, Any]:
        """Get all available message templates"""
        return {
            "templates": {
                name: {
                    "template": template["template"],
                    "required_variables": template["variables"]
                }
                for name, template in self.message_templates.items()
            }
        }