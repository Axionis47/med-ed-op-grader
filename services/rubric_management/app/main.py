"""Rubric Management Service - Main FastAPI application."""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import jsonpatch
from pathlib import Path
import sys

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import Rubric
from services.rubric_management.app.storage import RubricStorage

app = FastAPI(
    title="Rubric Management Service",
    description="CRUD operations, versioning, and storage for grading rubrics",
    version="1.0.0"
)

# Initialize storage
storage = RubricStorage()


# Request/Response Models
class CreateRubricRequest(BaseModel):
    """Request to create a new rubric."""
    rubric: Rubric


class UpdateRubricRequest(BaseModel):
    """Request to update a rubric (creates new version)."""
    rubric: Rubric


class PatchRubricRequest(BaseModel):
    """Request to apply JSON Patch operations."""
    operations: list[dict] = Field(..., description="JSON Patch operations (RFC 6902)")


class ApproveRubricResponse(BaseModel):
    """Response from rubric approval."""
    rubric_id: str
    version: str
    status: str
    approved_at: datetime


# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rubric_management"}


@app.post("/rubrics", status_code=status.HTTP_201_CREATED)
async def create_rubric(request: CreateRubricRequest):
    """
    Create a new rubric.
    
    The rubric will be saved with status 'draft' initially.
    """
    rubric = request.rubric
    
    # Check if rubric already exists
    existing = storage.load(rubric.rubric_id, rubric.version)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Rubric {rubric.rubric_id} version {rubric.version} already exists"
        )
    
    # Validate unique anchors
    if not rubric.validate_unique_anchors():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rubric contains duplicate anchors"
        )
    
    # Save rubric
    storage.save(rubric)
    
    return {
        "rubric_id": rubric.rubric_id,
        "version": rubric.version,
        "status": rubric.status,
        "created_at": rubric.created_at
    }


@app.get("/rubrics/{rubric_id}")
async def get_rubric(rubric_id: str, version: Optional[str] = None):
    """
    Retrieve a rubric.
    
    If version is not specified, returns the latest approved version.
    """
    rubric = storage.load(rubric_id, version)
    
    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rubric {rubric_id}" + (f" version {version}" if version else "") + " not found"
        )
    
    return rubric


@app.get("/rubrics/{rubric_id}/versions")
async def list_rubric_versions(rubric_id: str):
    """
    List all versions of a rubric.
    """
    versions = storage.list_versions(rubric_id)
    
    if not versions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No versions found for rubric {rubric_id}"
        )
    
    return {
        "rubric_id": rubric_id,
        "versions": versions
    }


@app.put("/rubrics/{rubric_id}")
async def update_rubric(rubric_id: str, request: UpdateRubricRequest):
    """
    Update a rubric by creating a new version.
    
    This increments the patch version number and saves as a new draft.
    """
    new_rubric = request.rubric
    
    # Verify rubric_id matches
    if new_rubric.rubric_id != rubric_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rubric ID in URL does not match rubric ID in body"
        )
    
    # Load current latest version
    current = storage.load(rubric_id)
    if not current:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rubric {rubric_id} not found"
        )
    
    # Create new version
    new_version = storage.create_new_version(current)
    new_rubric.version = new_version
    new_rubric.status = "draft"
    new_rubric.created_at = datetime.utcnow()
    new_rubric.updated_at = datetime.utcnow()
    
    # Validate unique anchors
    if not new_rubric.validate_unique_anchors():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rubric contains duplicate anchors"
        )
    
    # Save new version
    storage.save(new_rubric)
    
    return {
        "rubric_id": new_rubric.rubric_id,
        "version": new_rubric.version,
        "status": new_rubric.status,
        "updated_at": new_rubric.updated_at
    }


@app.patch("/rubrics/{rubric_id}")
async def patch_rubric(rubric_id: str, request: PatchRubricRequest):
    """
    Apply JSON Patch operations to a rubric (RFC 6902).
    
    Creates a new version with the patches applied.
    """
    # Load current latest version
    current = storage.load(rubric_id)
    if not current:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rubric {rubric_id} not found"
        )
    
    # Convert to dict for patching
    current_dict = current.model_dump(mode='json')
    
    # Apply patches
    try:
        patch = jsonpatch.JsonPatch(request.operations)
        patched_dict = patch.apply(current_dict)
    except jsonpatch.JsonPatchException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON Patch: {str(e)}"
        )
    
    # Create new rubric from patched data
    try:
        new_rubric = Rubric(**patched_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patched rubric is invalid: {str(e)}"
        )
    
    # Create new version
    new_version = storage.create_new_version(current)
    new_rubric.version = new_version
    new_rubric.status = "draft"
    new_rubric.updated_at = datetime.utcnow()
    
    # Validate unique anchors
    if not new_rubric.validate_unique_anchors():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patched rubric contains duplicate anchors"
        )
    
    # Save new version
    storage.save(new_rubric)
    
    return {
        "rubric_id": new_rubric.rubric_id,
        "version": new_rubric.version,
        "status": new_rubric.status,
        "updated_at": new_rubric.updated_at
    }


@app.post("/rubrics/{rubric_id}/approve")
async def approve_rubric(rubric_id: str, version: Optional[str] = None):
    """
    Approve a rubric version.
    
    If version is not specified, approves the latest draft version.
    This will run QA validation before approval (to be implemented).
    """
    # Load rubric
    if version:
        rubric = storage.load(rubric_id, version)
    else:
        # Find latest draft
        versions = storage.list_versions(rubric_id)
        draft_versions = [v for v in versions if v['status'] == 'draft']
        if not draft_versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No draft versions found for rubric {rubric_id}"
            )
        version = draft_versions[0]['version']
        rubric = storage.load(rubric_id, version)
    
    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rubric {rubric_id} version {version} not found"
        )
    
    if rubric.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rubric {rubric_id} version {version} is already approved"
        )
    
    # TODO: Call QA Validation Service
    # For now, we'll do basic validation
    if not rubric.validate_unique_anchors():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rubric contains duplicate anchors"
        )
    
    # Approve rubric
    rubric.status = "approved"
    rubric.updated_at = datetime.utcnow()
    storage.save(rubric)
    
    return ApproveRubricResponse(
        rubric_id=rubric.rubric_id,
        version=rubric.version,
        status=rubric.status,
        approved_at=rubric.updated_at
    )


@app.delete("/rubrics/{rubric_id}")
async def delete_rubric(rubric_id: str, version: str):
    """
    Delete a specific rubric version.
    
    Approved rubrics cannot be deleted, only archived.
    """
    # Load rubric to check status
    rubric = storage.load(rubric_id, version)
    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rubric {rubric_id} version {version} not found"
        )
    
    if rubric.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete approved rubric. Archive it instead."
        )
    
    # Delete rubric
    success = storage.delete(rubric_id, version)
    
    if success:
        return {"message": f"Rubric {rubric_id} version {version} deleted"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete rubric"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

