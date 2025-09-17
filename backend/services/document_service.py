from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import base64
import io
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, UploadFile
import logging

logger = logging.getLogger(__name__)

class DocumentService:
    """Document management service for PM Connect 3.0"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.document_categories = {
            "agenda": {
                "title": "Event Agenda",
                "description": "Complete agenda for PM Connect events",
                "file_types": [".pdf", ".docx"],
                "max_size_mb": 10
            },
            "safety_booklet": {
                "title": "Safety Guidelines",
                "description": "Comprehensive safety guidelines and protocols",
                "file_types": [".pdf", ".docx"],
                "max_size_mb": 15
            },
            "quality_booklet": {
                "title": "Quality Standards",
                "description": "Quality management standards and procedures",
                "file_types": [".pdf", ".docx"],
                "max_size_mb": 15
            },
            "travel_info": {
                "title": "Travel Information",
                "description": "Travel guidelines and accommodation details",
                "file_types": [".pdf", ".docx"],
                "max_size_mb": 8
            },
            "event_presentation": {
                "title": "Event Presentations",
                "description": "Presentations and materials from the event",
                "file_types": [".pdf", ".pptx", ".docx"],
                "max_size_mb": 25
            },
            "certificates": {
                "title": "Certificates",
                "description": "Participation and achievement certificates",
                "file_types": [".pdf"],
                "max_size_mb": 5
            }
        }
    
    async def upload_document(self, 
                            file: UploadFile, 
                            category: str, 
                            event_version: str,
                            uploaded_by: str,
                            title: Optional[str] = None,
                            description: Optional[str] = None,
                            is_public: bool = True) -> Dict[str, Any]:
        """Upload a document to the system"""
        try:
            # Validate category
            if category not in self.document_categories:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid category. Must be one of: {list(self.document_categories.keys())}"
                )
            
            category_config = self.document_categories[category]
            
            # Validate file type
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in category_config["file_types"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type for {category}. Allowed: {category_config['file_types']}"
                )
            
            # Read and validate file size
            contents = await file.read()
            file_size_mb = len(contents) / (1024 * 1024)
            
            if file_size_mb > category_config["max_size_mb"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size for {category}: {category_config['max_size_mb']}MB"
                )
            
            # Encode file content
            file_base64 = base64.b64encode(contents).decode('utf-8')
            
            # Create document record
            document = {
                "documentId": str(uuid.uuid4()),
                "filename": file.filename,
                "originalName": file.filename,
                "title": title or category_config["title"],
                "description": description or category_config["description"],
                "category": category,
                "fileType": file_extension,
                "fileSizeMB": round(file_size_mb, 2),
                "eventVersion": event_version,
                "documentData": file_base64,
                "uploadedBy": uploaded_by,
                "uploadedAt": datetime.utcnow(),
                "isPublic": is_public,
                "downloadCount": 0,
                "isActive": True,
                "tags": [category, event_version],
                "version": 1,
                "checksum": self._generate_checksum(contents)
            }
            
            # Check if document with same category and event version exists
            existing = await self.db.documents.find_one({
                "category": category,
                "eventVersion": event_version,
                "isActive": True
            })
            
            if existing:
                # Archive existing document
                await self.db.documents.update_one(
                    {"documentId": existing["documentId"]},
                    {"$set": {"isActive": False, "archivedAt": datetime.utcnow()}}
                )
            
            # Insert new document
            result = await self.db.documents.insert_one(document)
            
            return {
                "documentId": document["documentId"],
                "filename": document["filename"],
                "title": document["title"],
                "category": document["category"],
                "eventVersion": document["eventVersion"],
                "fileSizeMB": document["fileSizeMB"],
                "uploadedAt": document["uploadedAt"],
                "message": "Document uploaded successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Document upload failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")
    
    async def get_document_by_id(self, document_id: str, track_download: bool = True) -> Dict[str, Any]:
        """Get document by ID and optionally track download"""
        try:
            document = await self.db.documents.find_one({
                "documentId": document_id,
                "isActive": True
            })
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Track download
            if track_download:
                await self.db.documents.update_one(
                    {"documentId": document_id},
                    {
                        "$inc": {"downloadCount": 1},
                        "$set": {"lastDownloadedAt": datetime.utcnow()}
                    }
                )
                
                # Log download
                download_log = {
                    "downloadId": str(uuid.uuid4()),
                    "documentId": document_id,
                    "filename": document["filename"],
                    "category": document["category"],
                    "downloadedAt": datetime.utcnow(),
                    "userAgent": None,  # Could be passed from request
                    "ipAddress": None   # Could be passed from request
                }
                await self.db.download_logs.insert_one(download_log)
            
            # Remove _id for JSON serialization
            document.pop('_id', None)
            
            return document
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Document retrieval failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Document retrieval failed: {str(e)}")
    
    async def get_documents_by_category(self, 
                                      category: str, 
                                      event_version: Optional[str] = None,
                                      is_public: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get all documents in a specific category"""
        try:
            # Build query
            query = {"category": category, "isActive": True}
            
            if event_version:
                query["eventVersion"] = event_version
            
            if is_public is not None:
                query["isPublic"] = is_public
            
            documents = await self.db.documents.find(query)\
                .sort("uploadedAt", -1)\
                .to_list(50)
            
            # Remove sensitive data and _id
            for doc in documents:
                doc.pop('_id', None)
                doc.pop('documentData', None)  # Don't include base64 data in list
            
            return documents
            
        except Exception as e:
            logger.error(f"Documents by category retrieval failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Documents retrieval failed: {str(e)}")
    
    async def get_public_documents(self, event_version: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get all public documents organized by category"""
        try:
            query = {"isPublic": True, "isActive": True}
            
            if event_version:
                query["eventVersion"] = event_version
            
            documents = await self.db.documents.find(query)\
                .sort("uploadedAt", -1)\
                .to_list(100)
            
            # Organize by category
            documents_by_category = {}
            for doc in documents:
                category = doc["category"]
                if category not in documents_by_category:
                    documents_by_category[category] = []
                
                # Remove sensitive data
                doc.pop('_id', None)
                doc.pop('documentData', None)
                
                documents_by_category[category].append(doc)
            
            return documents_by_category
            
        except Exception as e:
            logger.error(f"Public documents retrieval failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Public documents retrieval failed: {str(e)}")
    
    async def search_documents(self, 
                             search_term: str, 
                             category: Optional[str] = None,
                             event_version: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search documents by title, description, or filename"""
        try:
            # Build search query
            search_query = {
                "$text": {"$search": search_term}
            } if search_term else {}
            
            # Add filters
            filter_query = {"isActive": True, "isPublic": True}
            
            if category:
                filter_query["category"] = category
            
            if event_version:
                filter_query["eventVersion"] = event_version
            
            # Combine queries
            if search_query:
                query = {"$and": [search_query, filter_query]}
            else:
                query = filter_query
            
            documents = await self.db.documents.find(query)\
                .sort("uploadedAt", -1)\
                .to_list(50)
            
            # Remove sensitive data
            for doc in documents:
                doc.pop('_id', None)
                doc.pop('documentData', None)
            
            return documents
            
        except Exception as e:
            logger.error(f"Document search failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Document search failed: {str(e)}")
    
    async def delete_document(self, document_id: str, deleted_by: str) -> Dict[str, Any]:
        """Soft delete document"""
        try:
            result = await self.db.documents.update_one(
                {"documentId": document_id, "isActive": True},
                {
                    "$set": {
                        "isActive": False,
                        "deletedBy": deleted_by,
                        "deletedAt": datetime.utcnow()
                    }
                }
            )
            
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Document not found")
            
            return {
                "message": "Document deleted successfully",
                "documentId": document_id,
                "deletedAt": datetime.utcnow()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Document deletion failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Document deletion failed: {str(e)}")
    
    async def get_document_analytics(self) -> Dict[str, Any]:
        """Get document analytics"""
        try:
            # Aggregate document statistics
            pipeline = [
                {"$match": {"isActive": True}},
                {
                    "$facet": {
                        "category_distribution": [
                            {"$group": {"_id": "$category", "count": {"$sum": 1}, "totalDownloads": {"$sum": "$downloadCount"}}}
                        ],
                        "event_version_distribution": [
                            {"$group": {"_id": "$eventVersion", "count": {"$sum": 1}}}
                        ],
                        "file_type_distribution": [
                            {"$group": {"_id": "$fileType", "count": {"$sum": 1}}}
                        ],
                        "upload_trends": [
                            {
                                "$group": {
                                    "_id": {
                                        "year": {"$year": "$uploadedAt"},
                                        "month": {"$month": "$uploadedAt"}
                                    },
                                    "count": {"$sum": 1}
                                }
                            },
                            {"$sort": {"_id.year": -1, "_id.month": -1}},
                            {"$limit": 12}
                        ]
                    }
                }
            ]
            
            results = await self.db.documents.aggregate(pipeline).to_list(1)
            
            if not results:
                return {"message": "No document data available"}
            
            analytics = results[0]
            
            # Calculate totals
            total_documents = await self.db.documents.count_documents({"isActive": True})
            total_downloads = await self.db.documents.aggregate([
                {"$match": {"isActive": True}},
                {"$group": {"_id": None, "total": {"$sum": "$downloadCount"}}}
            ]).to_list(1)
            
            total_download_count = total_downloads[0]["total"] if total_downloads else 0
            
            return {
                "overview": {
                    "total_documents": total_documents,
                    "total_downloads": total_download_count,
                    "categories_count": len(analytics["category_distribution"])
                },
                "distributions": {
                    "categories": {
                        item["_id"]: {
                            "count": item["count"],
                            "downloads": item["totalDownloads"]
                        } for item in analytics["category_distribution"]
                    },
                    "event_versions": {item["_id"]: item["count"] for item in analytics["event_version_distribution"]},
                    "file_types": {item["_id"]: item["count"] for item in analytics["file_type_distribution"]}
                },
                "trends": {
                    "monthly_uploads": [
                        {
                            "period": f"{item['_id']['year']}-{item['_id']['month']:02d}",
                            "count": item["count"]
                        } for item in analytics["upload_trends"]
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Document analytics failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Document analytics failed: {str(e)}")
    
    async def get_download_logs(self, 
                              page: int = 1, 
                              limit: int = 50,
                              document_id: Optional[str] = None) -> Dict[str, Any]:
        """Get document download logs"""
        try:
            skip = (page - 1) * limit
            query = {}
            
            if document_id:
                query["documentId"] = document_id
            
            logs = await self.db.download_logs.find(query)\
                .sort("downloadedAt", -1)\
                .skip(skip)\
                .limit(limit)\
                .to_list(limit)
            
            total_count = await self.db.download_logs.count_documents(query)
            total_pages = (total_count + limit - 1) // limit
            
            # Clean up logs
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
            logger.error(f"Download logs retrieval failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Download logs retrieval failed: {str(e)}")
    
    def get_supported_categories(self) -> Dict[str, Any]:
        """Get all supported document categories"""
        return {
            "categories": self.document_categories
        }
    
    def _generate_checksum(self, content: bytes) -> str:
        """Generate MD5 checksum for file content"""
        import hashlib
        return hashlib.md5(content).hexdigest()
    
    async def create_database_indexes(self):
        """Create database indexes for documents collection"""
        try:
            # Create indexes for better query performance
            await self.db.documents.create_index("documentId", unique=True)
            await self.db.documents.create_index("category")
            await self.db.documents.create_index("eventVersion")
            await self.db.documents.create_index("isActive")
            await self.db.documents.create_index("isPublic")
            await self.db.documents.create_index("uploadedAt")
            
            # Text index for search
            await self.db.documents.create_index([
                ("title", "text"),
                ("description", "text"),
                ("filename", "text")
            ])
            
            # Download logs indexes
            await self.db.download_logs.create_index("documentId")
            await self.db.download_logs.create_index("downloadedAt")
            
            return {"success": True, "message": "Document indexes created successfully"}
            
        except Exception as e:
            logger.error(f"Document index creation failed: {str(e)}")
            return {"success": False, "error": str(e)}