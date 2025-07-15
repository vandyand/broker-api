import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import Issue, IssueType, IssuePriority, IssueStatus

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_issues.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_issue():
    """Test creating a new issue"""
    issue_data = {
        "title": "Test Bug Report",
        "description": "This is a test bug description",
        "issue_type": "bug",
        "priority": "medium",
        "reporter_name": "Test User",
        "reporter_email": "test@example.com",
        "component": "api"
    }
    
    response = client.post("/issues/", json=issue_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "Test Bug Report"
    assert data["description"] == "This is a test bug description"
    assert data["issue_type"] == "bug"
    assert data["priority"] == "medium"
    assert data["status"] == "open"
    assert data["reporter_name"] == "Test User"
    assert data["reporter_email"] == "test@example.com"
    assert data["component"] == "api"
    assert "id" in data
    assert "created_at" in data

def test_create_feature_request():
    """Test creating a feature request"""
    issue_data = {
        "title": "Add New Trading Feature",
        "description": "Please add support for options trading",
        "issue_type": "feature_request",
        "priority": "high",
        "reporter_name": "Trader User",
        "component": "trading"
    }
    
    response = client.post("/issues/", json=issue_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["issue_type"] == "feature_request"
    assert data["priority"] == "high"
    assert data["status"] == "open"

def test_list_issues():
    """Test listing issues with pagination"""
    # Create multiple issues
    issues = [
        {"title": "Bug 1", "description": "First bug", "issue_type": "bug"},
        {"title": "Feature 1", "description": "First feature", "issue_type": "feature_request"},
        {"title": "Enhancement 1", "description": "First enhancement", "issue_type": "enhancement"}
    ]
    
    for issue in issues:
        client.post("/issues/", json=issue)
    
    response = client.get("/issues/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["size"] == 100

def test_filter_issues_by_type():
    """Test filtering issues by type"""
    # Create issues of different types
    issues = [
        {"title": "Bug 1", "description": "First bug", "issue_type": "bug"},
        {"title": "Feature 1", "description": "First feature", "issue_type": "feature_request"},
        {"title": "Bug 2", "description": "Second bug", "issue_type": "bug"}
    ]
    
    for issue in issues:
        client.post("/issues/", json=issue)
    
    # Filter by bug type
    response = client.get("/issues/?issue_type=bug")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 2
    assert all(item["issue_type"] == "bug" for item in data["items"])

def test_filter_issues_by_priority():
    """Test filtering issues by priority"""
    issues = [
        {"title": "Low Priority", "description": "Low", "priority": "low"},
        {"title": "High Priority", "description": "High", "priority": "high"},
        {"title": "Medium Priority", "description": "Medium", "priority": "medium"}
    ]
    
    for issue in issues:
        client.post("/issues/", json=issue)
    
    response = client.get("/issues/?priority=high")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["priority"] == "high"

def test_search_issues():
    """Test searching issues by title and description"""
    issues = [
        {"title": "API Error", "description": "Error in API endpoint"},
        {"title": "Database Issue", "description": "Database connection problem"},
        {"title": "UI Bug", "description": "User interface issue"}
    ]
    
    for issue in issues:
        client.post("/issues/", json=issue)
    
    # Search for "API"
    response = client.get("/issues/?search=API")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 1
    assert "API" in data["items"][0]["title"]

def test_get_issue_by_id():
    """Test getting a specific issue by ID"""
    issue_data = {
        "title": "Specific Issue",
        "description": "This is a specific issue",
        "issue_type": "bug"
    }
    
    create_response = client.post("/issues/", json=issue_data)
    issue_id = create_response.json()["id"]
    
    response = client.get(f"/issues/{issue_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == issue_id
    assert data["title"] == "Specific Issue"

def test_update_issue():
    """Test updating an issue"""
    issue_data = {
        "title": "Original Title",
        "description": "Original description",
        "issue_type": "bug"
    }
    
    create_response = client.post("/issues/", json=issue_data)
    issue_id = create_response.json()["id"]
    
    update_data = {
        "title": "Updated Title",
        "priority": "high",
        "status": "in_progress"
    }
    
    response = client.put(f"/issues/{issue_id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["priority"] == "high"
    assert data["status"] == "in_progress"

def test_assign_issue():
    """Test assigning an issue to someone"""
    issue_data = {
        "title": "Assignable Issue",
        "description": "This issue can be assigned",
        "issue_type": "bug"
    }
    
    create_response = client.post("/issues/", json=issue_data)
    issue_id = create_response.json()["id"]
    
    response = client.post(f"/issues/{issue_id}/assign?assigned_to=John Doe")
    assert response.status_code == 200
    
    data = response.json()
    assert data["assigned_to"] == "John Doe"
    assert data["status"] == "in_progress"

def test_resolve_issue():
    """Test resolving an issue"""
    issue_data = {
        "title": "Resolvable Issue",
        "description": "This issue can be resolved",
        "issue_type": "bug"
    }
    
    create_response = client.post("/issues/", json=issue_data)
    issue_id = create_response.json()["id"]
    
    response = client.post(f"/issues/{issue_id}/resolve?resolution_notes=Fixed the bug")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None
    assert "Fixed the bug" in data["additional_notes"]

def test_delete_issue():
    """Test deleting (closing) an issue"""
    issue_data = {
        "title": "Deletable Issue",
        "description": "This issue can be deleted",
        "issue_type": "bug"
    }
    
    create_response = client.post("/issues/", json=issue_data)
    issue_id = create_response.json()["id"]
    
    response = client.delete(f"/issues/{issue_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "closed" in data["message"]

def test_get_issue_stats():
    """Test getting issue statistics"""
    # Create issues with different types and priorities
    issues = [
        {"title": "Bug 1", "description": "Bug", "issue_type": "bug", "priority": "high"},
        {"title": "Feature 1", "description": "Feature", "issue_type": "feature_request", "priority": "medium"},
        {"title": "Enhancement 1", "description": "Enhancement", "issue_type": "enhancement", "priority": "low"}
    ]
    
    for issue in issues:
        client.post("/issues/", json=issue)
    
    response = client.get("/issues/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_issues"] == 3
    assert data["open_issues"] == 3
    assert data["bugs"] == 1
    assert data["feature_requests"] == 1
    assert data["enhancements"] == 1
    assert data["high_priority"] == 1
    assert data["medium_priority"] == 1
    assert data["low_priority"] == 1

def test_get_issue_summary():
    """Test getting issue summary"""
    issues = [
        {"title": "Issue 1", "description": "First issue", "issue_type": "bug"},
        {"title": "Issue 2", "description": "Second issue", "issue_type": "feature_request"}
    ]
    
    for issue in issues:
        client.post("/issues/", json=issue)
    
    response = client.get("/issues/summary")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    assert all("id" in item for item in data)
    assert all("title" in item for item in data)
    assert all("issue_type" in item for item in data)
    assert all("priority" in item for item in data)
    assert all("status" in item for item in data)

def test_list_components():
    """Test listing all components"""
    issues = [
        {"title": "API Issue", "description": "API problem", "component": "api"},
        {"title": "DB Issue", "description": "Database problem", "component": "database"},
        {"title": "UI Issue", "description": "UI problem", "component": "frontend"}
    ]
    
    for issue in issues:
        client.post("/issues/", json=issue)
    
    response = client.get("/issues/components/list")
    assert response.status_code == 200
    
    data = response.json()
    assert "api" in data
    assert "database" in data
    assert "frontend" in data
    assert len(data) == 3

def test_list_labels():
    """Test listing all labels"""
    issues = [
        {"title": "Issue 1", "description": "First issue", "labels": "bug,api,urgent"},
        {"title": "Issue 2", "description": "Second issue", "labels": "feature,ui,enhancement"},
        {"title": "Issue 3", "description": "Third issue", "labels": "bug,database"}
    ]
    
    for issue in issues:
        client.post("/issues/", json=issue)
    
    response = client.get("/issues/labels/list")
    assert response.status_code == 200
    
    data = response.json()
    assert "bug" in data
    assert "api" in data
    assert "urgent" in data
    assert "feature" in data
    assert "ui" in data
    assert "enhancement" in data
    assert "database" in data

def test_issue_not_found():
    """Test getting a non-existent issue"""
    response = client.get("/issues/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Issue not found"

def test_update_nonexistent_issue():
    """Test updating a non-existent issue"""
    update_data = {"title": "Updated Title"}
    response = client.put("/issues/999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Issue not found" 