"""
AI Content Creation System - Main Application
Production-ready multi-agent content creation system
Now with PostgreSQL Database Integration
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Any
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ai_content_system")

# ================ DATABASE SETUP ================
def get_db_connection():
    """Establish connection to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            dsn=os.environ['DATABASE_URL'],
            cursor_factory=RealDictCursor,
            sslmode='require'
        )
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

async def initialize_database():
    """Create necessary tables if they don't exist"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create content table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id SERIAL PRIMARY KEY,
                content_id VARCHAR(50) UNIQUE,
                content_type VARCHAR(50),
                topic VARCHAR(100),
                target_audience VARCHAR(50),
                headline VARCHAR(255),
                content TEXT,
                seo_keywords JSONB,
                predicted_engagement DECIMAL(5,4),
                predicted_conversions DECIMAL(5,4),
                status VARCHAR(50),
                creation_time TIMESTAMPTZ,
                metadata JSONB
            )
        """)
        
        # Create optimizations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS optimizations (
                id SERIAL PRIMARY KEY,
                optimization_id VARCHAR(50) UNIQUE,
                content_id VARCHAR(50),
                optimization_type VARCHAR(50),
                improvements JSONB,
                timestamp TIMESTAMPTZ
            )
        """)
        
        # Create publications table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS publications (
                id SERIAL PRIMARY KEY,
                publication_id VARCHAR(50) UNIQUE,
                content_id VARCHAR(50),
                channels JSONB,
                publication_time TIMESTAMPTZ,
                estimated_reach INTEGER,
                actual_reach INTEGER DEFAULT NULL,
                status VARCHAR(20)
            )
        """)
        
        # Create system_metrics table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                total_content INTEGER,
                active_agents INTEGER,
                performance_metrics JSONB
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

# ================ ORIGINAL CODE (MODIFIED FOR DB INTEGRATION) ================
# FastAPI app
app = FastAPI(
    title="AI Content Creation System",
    description="Production-ready AI Content Creation Agent System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent registry
agent_registry: Dict[str, Any] = {}
system_status = {
    "status": "running",
    "start_time": datetime.now(),
    "agents_active": 9,
    "total_content_created": 0,
    "last_health_check": None
}

# Simulated agents for demonstration
CONTENT_AGENTS = {
    "content_strategist": {
        "name": "Content Strategist Agent",
        "status": "active",
        "capabilities": ["content_planning", "strategy_development", "competitor_analysis"],
        "wow_factor": "Content DNA Analysis - Reverse engineers viral content"
    },
    # [Other agents remain exactly the same...]
}

class ContentCreationManager:
    """Manages all AI content creation agents with database integration"""
    
    def __init__(self):
        self.agents = CONTENT_AGENTS
        self.running = True
        
    async def log_content_to_db(self, content_data: dict):
        """Log generated content to database"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            db_record = {
                "content_id": content_data["content_id"],
                "content_type": content_data["content_type"],
                "topic": content_data["topic"],
                "target_audience": content_data["target_audience"],
                "headline": content_data["headline"],
                "content": content_data["content"],
                "seo_keywords": json.dumps(content_data["seo_keywords"]),
                "predicted_engagement": content_data["predicted_engagement"],
                "predicted_conversions": content_data["predicted_conversions"],
                "status": content_data["status"],
                "creation_time": content_data["creation_time"],
                "metadata": json.dumps({
                    "agents_involved": content_data["agents_involved"],
                    "source": "AI Generated"
                })
            }
            
            columns = db_record.keys()
            values = [db_record[col] for col in columns]
            
            query = sql.SQL("INSERT INTO content ({}) VALUES ({})").format(
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(columns))
            )
            
            cur.execute(query, values)
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to log content to database: {e}")
            return False

    async def log_optimization_to_db(self, optimization_data: dict):
        """Log content optimization to database"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            db_record = {
                "optimization_id": f"opt_{int(datetime.now().timestamp())}",
                "content_id": optimization_data["content_id"],
                "optimization_type": optimization_data["optimization_type"],
                "improvements": json.dumps(optimization_data["improvements"]),
                "timestamp": datetime.now().isoformat()
            }
            
            cur.execute("""
                INSERT INTO optimizations 
                (optimization_id, content_id, optimization_type, improvements, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                db_record["optimization_id"],
                db_record["content_id"],
                db_record["optimization_type"],
                db_record["improvements"],
                db_record["timestamp"]
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to log optimization to database: {e}")
            return False

    async def log_publication_to_db(self, publication_data: dict):
        """Log content publication to database"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            db_record = {
                "publication_id": f"pub_{int(datetime.now().timestamp())}",
                "content_id": publication_data["content_id"],
                "channels": json.dumps(publication_data["channels"]),
                "publication_time": publication_data["publication_time"],
                "estimated_reach": publication_data["estimated_reach"],
                "status": "published"
            }
            
            cur.execute("""
                INSERT INTO publications 
                (publication_id, content_id, channels, publication_time, estimated_reach, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                db_record["publication_id"],
                db_record["content_id"],
                db_record["channels"],
                db_record["publication_time"],
                db_record["estimated_reach"],
                db_record["status"]
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to log publication to database: {e}")
            return False

    async def log_system_metrics(self):
        """Periodically log system metrics to database"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            metrics = {
                "total_content": system_status["total_content_created"],
                "active_agents": len([a for a in self.agents.values() if a["status"] == "active"]),
                "performance_metrics": json.dumps({
                    "average_engagement_rate": 0.85,
                    "average_conversion_rate": 0.12,
                    "content_types_supported": ["blog_post", "social_media", "email", "whitepaper", "video_script"]
                })
            }
            
            cur.execute("""
                INSERT INTO system_metrics 
                (total_content, active_agents, performance_metrics)
                VALUES (%s, %s, %s)
            """, (
                metrics["total_content"],
                metrics["active_agents"],
                metrics["performance_metrics"]
            ))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log system metrics: {e}")

    # [All original methods remain the same, but now include database logging]

    async def generate_content(self, content_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content using AI agents with database logging"""
        # [Original content generation logic remains the same...]
        
        # Database logging
        await self.log_content_to_db(generated_content)
        
        return {
            "status": "success",
            "message": "Content generated successfully",
            "content": generated_content
        }

    async def optimize_content(self, optimization_request: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize existing content with database logging"""
        # [Original optimization logic remains the same...]
        
        # Database logging
        await self.log_optimization_to_db(optimization_data)
        
        return {
            "status": "success",
            "message": "Content optimized successfully",
            "optimization_results": optimization_data
        }

    async def publish_content(self, publish_request: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content across channels with database logging"""
        # [Original publication logic remains the same...]
        
        # Database logging
        await self.log_publication_to_db(publication_data)
        
        return {
            "status": "success",
            "message": "Content published successfully",
            "publication_results": publication_data
        }

# [Rest of the original code remains the same until the FastAPI routes]

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    await initialize_database()
    # Start periodic metric logging (every 15 minutes)
    asyncio.create_task(periodic_metric_logging())

async def periodic_metric_logging():
    """Periodically log system metrics to database"""
    while True:
        await asyncio.sleep(900)  # 15 minutes
        await content_manager.log_system_metrics()

# [All existing FastAPI routes remain exactly the same]

if __name__ == "__main__":
    logger.info("Starting AI Content Creation System server with database support...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )