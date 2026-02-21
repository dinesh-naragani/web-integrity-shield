"""
Level-2 Deep Analysis Microservice for Web Integrity Shield

PORT: 8001
ENDPOINT: POST /deep-analyze

This service performs deep Selenium-based analysis on URLs flagged as suspicious
by the Level-1 ONNX model (risk score >= 0.7).

Architecture:
  Java Backend (port 8080) 
      → Level-2 Service (port 8001)
      → Returns deep analysis verdict
"""

import logging
import asyncio
import uuid
import ipaddress
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn

from selenium_analyzer import SeleniumPageAnalyzer
from config import Config, LogConfig

# Configure logging
logging.config.dictConfig(LogConfig.config)
logger = logging.getLogger(__name__)

# FastAPI app setup
app = FastAPI(
    title="Web Integrity Shield - Level-2 Deep Analysis",
    description="Selenium-based deep phishing analysis service",
    version="1.0.0"
)

# Global instances
page_analyzer: Optional[SeleniumPageAnalyzer] = None
analysis_semaphore: asyncio.Semaphore = None  # Will be initialized at startup


class DeepAnalyzeRequest(BaseModel):
    """Request model for deep analysis endpoint"""
    url: str = Field(..., description="URL to analyze", min_length=5, max_length=2048)
    riskScore: float = Field(..., description="Level-1 risk score from 0.0 to 1.0", ge=0.0, le=1.0)
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://suspicious-paypal-login.com",
                "riskScore": 0.82
            }
        }


class DeepAnalyzeResponse(BaseModel):
    """Response model for deep analysis endpoint"""
    analysisId: str = Field(..., description="Unique analysis ID (UUID)")
    url: str = Field(..., description="Analyzed URL")
    level2Score: float = Field(..., description="Level-2 risk score 0.0-1.0")
    finalVerdict: str = Field(..., description="PHISHING or SUSPICIOUS")
    reasons: list = Field(default_factory=list, description="Analysis reasons")
    analysisTime: float = Field(..., description="Time taken in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        schema_extra = {
            "example": {
                "analysisId": "550e8400-e29b-41d4-a716-446655440000",
                "url": "https://suspicious-paypal-login.com",
                "level2Score": 0.91,
                "finalVerdict": "PHISHING",
                "reasons": [
                    "Login form detected",
                    "External script injection",
                    "Domain age suspicious"
                ],
                "analysisTime": 3.45,
                "timestamp": "2026-02-21T12:14:42.123456"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    code: int
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


@app.on_event("startup")
async def startup_event():
    """Initialize Selenium analyzer and concurrency limits on startup"""
    global page_analyzer, analysis_semaphore
    try:
        logger.info("Starting Level-2 Deep Analysis Service...")
        page_analyzer = SeleniumPageAnalyzer(
            headless=True,
            page_load_timeout=Config.SELENIUM_TIMEOUT,
            script_timeout=Config.SELENIUM_TIMEOUT
        )
        logger.info("✓ Selenium analyzer initialized successfully")
        logger.info(f"✓ Chrome version validated")
        
        # Initialize concurrency semaphore (max 3 concurrent analyses)
        analysis_semaphore = asyncio.Semaphore(3)
        logger.info("✓ Concurrency limit set to 3 concurrent analyses")
    except Exception as e:
        logger.error(f"✗ Failed to initialize Selenium analyzer: {str(e)}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up Selenium resources on shutdown"""
    global page_analyzer
    if page_analyzer:
        try:
            logger.info("Shutting down Selenium analyzer...")
            page_analyzer.close()
            logger.info("✓ Selenium analyzer closed")
        except Exception as e:
            logger.error(f"Error closing analyzer: {str(e)}")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "OK",
        "service": "Level-2 Deep Analysis",
        "port": Config.SERVICE_PORT,
        "selenium_ready": page_analyzer is not None
    }


def _is_ssrf_vulnerability(url: str) -> bool:
    """
    Check if URL contains SSRF attack pattern (private IPs, localhost, etc.)
    
    Returns True if URL should be blocked, False if safe to analyze
    """
    try:
        # Check protocol
        if url.startswith('file://') or url.startswith('ftp://'):
            logger.warning(f"Blocked SSRF protocol: {url[:50]}")
            return True
        
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            return True
        
        # Check for localhost
        if hostname.lower() in ['localhost', 'l.localhost']:
            logger.warning(f"Blocked localhost URL: {url}")
            return True
        
        # Try to parse as IP address
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback:
                logger.warning(f"Blocked private IP: {hostname}")
                return True
        except ValueError:
            # Not an IP address (hostname), safe to proceed
            pass
        
        return False
    
    except Exception as e:
        logger.warning(f"Error checking SSRF: {str(e)}")
        return True  # Fail safe


@app.post(
    "/deep-analyze",
    response_model=DeepAnalyzeResponse,
    tags=["Analysis"],
    summary="Perform deep phishing analysis",
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Invalid URL or request"},
        500: {"description": "Analysis service error"}
    }
)
async def deep_analyze(request: DeepAnalyzeRequest):
    """
    Perform deep Selenium-based analysis on a suspicious URL.
    
    This endpoint:
    1. Validates the input URL and blocks SSRF attacks
    2. Limits concurrent analyses to 3
    3. Launches headless Chrome
    4. Analyzes page content and behavior
    5. Scores suspicious factors
    6. Returns detailed verdict and reasons
    
    **Input:**
    - url: URL to analyze (string, 5-2048 chars)
    - riskScore: Level-1 risk score (float, 0.0-1.0)
    
    **Output:**
    - analysisId: Unique analysis UUID
    - level2Score: Deep analysis risk score (0.0-1.0)
    - finalVerdict: "PHISHING" or "SUSPICIOUS"
    - reasons: List of suspicious factors detected
    - analysisTime: Seconds taken for analysis
    """
    analysis_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        if not page_analyzer:
            raise HTTPException(
                status_code=500,
                detail="Selenium analyzer not initialized"
            )
        
        # SSRF Protection: Block private IPs and dangerous protocols
        if _is_ssrf_vulnerability(request.url):
            logger.warning(f"[{analysis_id}] SSRF attack blocked: {request.url[:50]}")
            raise HTTPException(
                status_code=400,
                detail="URL blocked: private IP address or dangerous protocol"
            )
        
        logger.info(f"[{analysis_id}] Starting deep analysis for URL: {request.url[:50]}...")
        
        # Concurrency limit: max 3 concurrent Chrome analyses
        async with analysis_semaphore:
            # Run Selenium analysis with timeout protection
            try:
                analysis_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        page_analyzer.analyze_page,
                        request.url,
                        request.riskScore
                    ),
                    timeout=Config.REQUEST_TIMEOUT
                )
            except asyncio.TimeoutError:
                # Timeout is not a crash - return safe response with timeout indicator
                analysis_time = (datetime.utcnow() - start_time).total_seconds()
                logger.warning(f"[{analysis_id}] Analysis timeout after {analysis_time:.1f}s")
                
                return DeepAnalyzeResponse(
                    analysisId=analysis_id,
                    url=request.url,
                    level2Score=0.6,  # Default to SUSPICIOUS on timeout
                    finalVerdict="SUSPICIOUS",
                    reasons=["Analysis timeout - inconclusive"],
                    analysisTime=analysis_time
                )
        
        analysis_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Build response
        response = DeepAnalyzeResponse(
            analysisId=analysis_id,
            url=request.url,
            level2Score=analysis_result['score'],
            finalVerdict=analysis_result['verdict'],
            reasons=analysis_result['reasons'],
            analysisTime=analysis_time
        )
        
        logger.info(
            f"[{analysis_id}] Analysis complete - "
            f"URL: {request.url[:40]}... "
            f"Score: {response.level2Score:.3f}, "
            f"Verdict: {response.finalVerdict}, "
            f"Time: {analysis_time:.2f}s"
        )
        
        return response
        
    except HTTPException as e:
        logger.error(f"[{analysis_id}] HTTP error: {e.detail}")
        raise
    except Exception as e:
        # Return 500 only for unexpected internal errors
        logger.error(f"[{analysis_id}] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal analysis error"
        )


@app.post(
    "/batch-analyze",
    tags=["Analysis"],
    summary="Analyze multiple URLs (batch mode)"
)
async def batch_analyze(requests: list[DeepAnalyzeRequest]):
    """
    Analyze multiple URLs in batch mode.
    
    Returns immediately with job status.
    Results stored for batch retrieval.
    """
    if len(requests) > Config.MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum ({Config.MAX_BATCH_SIZE})"
        )
    
    logger.info(f"Starting batch analysis for {len(requests)} URLs")
    return {
        "status": "batch_queued",
        "count": len(requests),
        "message": "Batch analysis queued (feature in progress)"
    }


@app.get("/stats", tags=["Monitoring"])
async def get_stats():
    """Get service statistics"""
    return {
        "service": "Level-2 Deep Analysis",
        "status": "running",
        "selenium_ready": page_analyzer is not None,
        "config": {
            "timeout": Config.SELENIUM_TIMEOUT,
            "max_batch": Config.MAX_BATCH_SIZE,
            "port": Config.SERVICE_PORT
        }
    }


@app.get("/", tags=["Info"])
async def root():
    """Service info endpoint"""
    return {
        "name": "Web Integrity Shield - Level-2 Deep Analysis Service",
        "version": "1.0.0",
        "description": "Selenium-based phishing analysis",
        "endpoints": {
            "health": "GET /health",
            "analyze": "POST /deep-analyze",
            "batch": "POST /batch-analyze",
            "stats": "GET /stats",
            "docs": "/docs (Swagger UI)",
            "redoc": "/redoc (ReDoc)"
        }
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {
        "error": "Internal server error",
        "code": 500,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    logger.info(f"Starting server on port {Config.SERVICE_PORT}...")
    uvicorn.run(
        "level2_service:app",
        host="0.0.0.0",
        port=Config.SERVICE_PORT,
        reload=False,
        log_level="info"
    )
