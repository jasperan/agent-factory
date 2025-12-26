"""Work order management endpoints.

Handles:
- Work order creation from voice/text
- Work order queries
- Work order updates
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Literal, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class WorkOrderCreate(BaseModel):
    """Request to create a work order."""
    title: str
    description: Optional[str] = None
    asset_id: str
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    created_by: str  # User ID (Telegram or internal)
    source: Literal["telegram_voice", "telegram_text", "web", "api"] = "api"
    
    # Optional: from intent parsing
    equipment_type: Optional[str] = None
    fault_codes: Optional[List[str]] = None


class WorkOrderResponse(BaseModel):
    """Work order details response."""
    id: str
    title: str
    description: Optional[str] = None
    status: Literal["OPEN", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"]
    priority: str
    asset_id: str
    asset_name: Optional[str] = None
    created_by: str
    created_at: str
    updated_at: Optional[str] = None


class WorkOrderUpdate(BaseModel):
    """Request to update a work order."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["OPEN", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"]] = None
    priority: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None
    notes: Optional[str] = None


class WorkOrderListResponse(BaseModel):
    """List of work orders."""
    work_orders: List[WorkOrderResponse]
    total: int
    page: int
    per_page: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/work-orders", response_model=WorkOrderResponse)
async def create_work_order(request: WorkOrderCreate):
    """
    Create a new work order.
    
    This is the core endpoint called by:
    - Telegram voice handler (after transcription + intent parsing)
    - Telegram text handler
    - Web interface
    - Direct API calls
    
    The work order is created in Atlas CMMS.
    """
    logger.info(f"Creating work order: {request.title} for asset {request.asset_id}")
    
    # ==========================================================================
    # TODO: Create in Atlas CMMS (WS-1 provides AtlasClient)
    # ==========================================================================
    # from agent_factory.integrations.atlas import AtlasClient
    # atlas = AtlasClient()
    # 
    # work_order = await atlas.create_work_order({
    #     "title": request.title,
    #     "description": request.description,
    #     "asset": {"id": request.asset_id},
    #     "priority": request.priority,
    #     "category": {"name": "Corrective"},
    #     "metadata": {
    #         "source": request.source,
    #         "created_by": request.created_by,
    #         "fault_codes": request.fault_codes
    #     }
    # })
    
    # Placeholder response
    work_order_id = f"WO-{int(datetime.now().timestamp())}"
    
    # ==========================================================================
    # TODO: Log to LangSmith for observability
    # ==========================================================================
    # from agent_factory.observability import log_work_order_created
    # log_work_order_created(work_order_id, request.source, request.created_by)
    
    return WorkOrderResponse(
        id=work_order_id,
        title=request.title,
        description=request.description,
        status="OPEN",
        priority=request.priority,
        asset_id=request.asset_id,
        asset_name=None,  # Would come from Atlas
        created_by=request.created_by,
        created_at=datetime.now().isoformat()
    )


@router.get("/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(work_order_id: str):
    """
    Get a work order by ID.
    """
    # ==========================================================================
    # TODO: Fetch from Atlas CMMS
    # ==========================================================================
    raise HTTPException(501, "Not implemented yet")


@router.put("/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def update_work_order(work_order_id: str, request: WorkOrderUpdate):
    """
    Update a work order.
    
    Can update status, priority, description, or add notes.
    """
    logger.info(f"Updating work order {work_order_id}")
    
    # ==========================================================================
    # TODO: Update in Atlas CMMS
    # ==========================================================================
    raise HTTPException(501, "Not implemented yet")


@router.get("/work-orders", response_model=WorkOrderListResponse)
async def list_work_orders(
    user_id: Optional[str] = Query(None, description="Filter by user"),
    asset_id: Optional[str] = Query(None, description="Filter by asset"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    List work orders with optional filters.
    
    Used by:
    - Telegram bot to show user's work orders
    - Web dashboard
    """
    # ==========================================================================
    # TODO: Query Atlas CMMS with filters
    # ==========================================================================
    return WorkOrderListResponse(
        work_orders=[],
        total=0,
        page=page,
        per_page=per_page
    )


@router.post("/work-orders/{work_order_id}/complete")
async def complete_work_order(work_order_id: str, notes: Optional[str] = None):
    """
    Mark a work order as completed.
    
    Convenience endpoint for the Telegram bot.
    """
    logger.info(f"Completing work order {work_order_id}")
    
    # ==========================================================================
    # TODO: Update in Atlas CMMS
    # ==========================================================================
    return {"status": "completed", "work_order_id": work_order_id}


# =============================================================================
# ASSET ENDPOINTS (Could be separate router)
# =============================================================================

class AssetSummary(BaseModel):
    """Brief asset info for search results."""
    id: str
    name: str
    location: Optional[str] = None
    type: Optional[str] = None


@router.get("/assets", response_model=List[AssetSummary])
async def search_assets(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search assets by name, location, or ID.
    
    Used by intent clarification when user says "the pump" and we need
    to ask which one.
    """
    logger.info(f"Searching assets: {q}")
    
    # ==========================================================================
    # TODO: Query Atlas CMMS
    # ==========================================================================
    # from agent_factory.integrations.atlas import AtlasClient
    # atlas = AtlasClient()
    # assets = await atlas.search_assets(query=q, limit=limit)
    
    # Placeholder - return empty for now
    return []


@router.get("/assets/{asset_id}")
async def get_asset(asset_id: str):
    """
    Get asset details by ID.
    """
    # ==========================================================================
    # TODO: Fetch from Atlas CMMS
    # ==========================================================================
    raise HTTPException(501, "Not implemented yet")
