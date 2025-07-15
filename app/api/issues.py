from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Issue, IssueType, IssuePriority, IssueStatus
from app.schemas import (
    IssueCreate, IssueUpdate, Issue as IssueSchema, 
    IssueSummary, IssueStats, PaginatedResponse, StandardResponse
)

router = APIRouter(prefix="/issues", tags=["issues"])


@router.post("/", response_model=IssueSchema)
async def create_issue(issue: IssueCreate, db: Session = Depends(get_db)):
    """Create a new issue or feature request"""
    db_issue = Issue(**issue.model_dump())
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    return db_issue


@router.get("/", response_model=PaginatedResponse)
async def list_issues(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    issue_type: Optional[IssueType] = Query(None, description="Filter by issue type"),
    priority: Optional[IssuePriority] = Query(None, description="Filter by priority"),
    status: Optional[IssueStatus] = Query(None, description="Filter by status"),
    component: Optional[str] = Query(None, description="Filter by component"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned person"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    db: Session = Depends(get_db)
):
    """List issues with filtering and pagination"""
    query = db.query(Issue)
    
    # Apply filters
    if issue_type:
        query = query.filter(Issue.issue_type == issue_type)
    if priority:
        query = query.filter(Issue.priority == priority)
    if status:
        query = query.filter(Issue.status == status)
    if component:
        query = query.filter(Issue.component == component)
    if assigned_to:
        query = query.filter(Issue.assigned_to == assigned_to)
    if search:
        search_filter = or_(
            Issue.title.ilike(f"%{search}%"),
            Issue.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    issues = query.order_by(Issue.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert to schema
    items = [IssueSchema.from_orm(issue) for issue in issues]
    
    # Calculate pagination info
    pages = (total + limit - 1) // limit
    page = (skip // limit) + 1
    
    return PaginatedResponse(
        items=[item.model_dump() for item in items],
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get("/summary", response_model=List[IssueSummary])
async def list_issues_summary(
    limit: int = Query(50, ge=1, le=500, description="Number of records to return"),
    status: Optional[IssueStatus] = Query(None, description="Filter by status"),
    priority: Optional[IssuePriority] = Query(None, description="Filter by priority"),
    db: Session = Depends(get_db)
):
    """Get a summary list of issues for quick overview"""
    query = db.query(Issue)
    
    if status:
        query = query.filter(Issue.status == status)
    if priority:
        query = query.filter(Issue.priority == priority)
    
    issues = query.order_by(Issue.created_at.desc()).limit(limit).all()
    return [IssueSummary.from_orm(issue) for issue in issues]


@router.get("/stats", response_model=IssueStats)
async def get_issue_stats(db: Session = Depends(get_db)):
    """Get issue statistics"""
    # Total counts by status
    total_issues = db.query(func.count(Issue.id)).scalar()
    open_issues = db.query(func.count(Issue.id)).filter(Issue.status == IssueStatus.OPEN).scalar()
    in_progress_issues = db.query(func.count(Issue.id)).filter(Issue.status == IssueStatus.IN_PROGRESS).scalar()
    resolved_issues = db.query(func.count(Issue.id)).filter(Issue.status == IssueStatus.RESOLVED).scalar()
    closed_issues = db.query(func.count(Issue.id)).filter(Issue.status == IssueStatus.CLOSED).scalar()
    
    # Counts by type
    bugs = db.query(func.count(Issue.id)).filter(Issue.issue_type == IssueType.BUG).scalar()
    feature_requests = db.query(func.count(Issue.id)).filter(Issue.issue_type == IssueType.FEATURE_REQUEST).scalar()
    enhancements = db.query(func.count(Issue.id)).filter(Issue.issue_type == IssueType.ENHANCEMENT).scalar()
    
    # Counts by priority
    critical_priority = db.query(func.count(Issue.id)).filter(Issue.priority == IssuePriority.CRITICAL).scalar()
    high_priority = db.query(func.count(Issue.id)).filter(Issue.priority == IssuePriority.HIGH).scalar()
    medium_priority = db.query(func.count(Issue.id)).filter(Issue.priority == IssuePriority.MEDIUM).scalar()
    low_priority = db.query(func.count(Issue.id)).filter(Issue.priority == IssuePriority.LOW).scalar()
    
    return IssueStats(
        total_issues=total_issues,
        open_issues=open_issues,
        in_progress_issues=in_progress_issues,
        resolved_issues=resolved_issues,
        closed_issues=closed_issues,
        bugs=bugs,
        feature_requests=feature_requests,
        enhancements=enhancements,
        critical_priority=critical_priority,
        high_priority=high_priority,
        medium_priority=medium_priority,
        low_priority=low_priority
    )


@router.get("/{issue_id}", response_model=IssueSchema)
async def get_issue(issue_id: int, db: Session = Depends(get_db)):
    """Get a specific issue by ID"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.put("/{issue_id}", response_model=IssueSchema)
async def update_issue(issue_id: int, issue_update: IssueUpdate, db: Session = Depends(get_db)):
    """Update an issue"""
    db_issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Update fields
    update_data = issue_update.model_dump(exclude_unset=True)
    
    # Handle status changes
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status in [IssueStatus.RESOLVED, IssueStatus.CLOSED] and not db_issue.resolved_at:
            update_data["resolved_at"] = datetime.utcnow()
        elif new_status not in [IssueStatus.RESOLVED, IssueStatus.CLOSED]:
            update_data["resolved_at"] = None
    
    for field, value in update_data.items():
        setattr(db_issue, field, value)
    
    db.commit()
    db.refresh(db_issue)
    return db_issue


@router.delete("/{issue_id}", response_model=StandardResponse)
async def delete_issue(issue_id: int, db: Session = Depends(get_db)):
    """Delete an issue (soft delete by marking as closed)"""
    db_issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Soft delete by marking as closed
    db_issue.status = IssueStatus.CLOSED
    db_issue.resolved_at = datetime.utcnow()
    db.commit()
    
    return StandardResponse(
        success=True,
        message=f"Issue {issue_id} has been closed"
    )


@router.post("/{issue_id}/assign", response_model=IssueSchema)
async def assign_issue(
    issue_id: int, 
    assigned_to: str = Query(..., description="Person to assign the issue to"),
    db: Session = Depends(get_db)
):
    """Assign an issue to someone"""
    db_issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    db_issue.assigned_to = assigned_to
    if db_issue.status == IssueStatus.OPEN:
        db_issue.status = IssueStatus.IN_PROGRESS
    
    db.commit()
    db.refresh(db_issue)
    return db_issue


@router.post("/{issue_id}/resolve", response_model=IssueSchema)
async def resolve_issue(
    issue_id: int,
    resolution_notes: Optional[str] = Query(None, description="Notes about the resolution"),
    db: Session = Depends(get_db)
):
    """Mark an issue as resolved"""
    db_issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    db_issue.status = IssueStatus.RESOLVED
    db_issue.resolved_at = datetime.utcnow()
    if resolution_notes:
        db_issue.additional_notes = (db_issue.additional_notes or "") + f"\n\nResolution: {resolution_notes}"
    
    db.commit()
    db.refresh(db_issue)
    return db_issue


@router.get("/components/list")
async def list_components(db: Session = Depends(get_db)):
    """Get list of all components that have issues"""
    components = db.query(Issue.component).filter(
        Issue.component.isnot(None)
    ).distinct().all()
    return [comp[0] for comp in components if comp[0]]


@router.get("/labels/list")
async def list_labels(db: Session = Depends(get_db)):
    """Get list of all labels used in issues"""
    labels_query = db.query(Issue.labels).filter(
        Issue.labels.isnot(None)
    ).distinct().all()
    
    all_labels = set()
    for label_set in labels_query:
        if label_set[0]:
            labels = [label.strip() for label in label_set[0].split(",")]
            all_labels.update(labels)
    
    return sorted(list(all_labels)) 