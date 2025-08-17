"""Database models for video script projects."""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import json
from typing import Optional, Dict, Any

Base = declarative_base()


class Project(Base):
    """Main project/session model."""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    topic = Column(String(500), nullable=False)
    platform = Column(String(50), nullable=False)
    target_audience = Column(String(200))
    video_duration = Column(String(50))
    status = Column(String(50), default='in_progress')  # in_progress, completed, archived
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_accessed = Column(DateTime, default=func.now())
    
    # Relationships
    components = relationship("ScriptComponent", back_populates="project", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="project", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'topic': self.topic,
            'platform': self.platform,
            'target_audience': self.target_audience,
            'video_duration': self.video_duration,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }


class ScriptComponent(Base):
    """Individual script components (hook, story, cta)."""
    __tablename__ = 'script_components'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    component_type = Column(String(50), nullable=False)  # hook, story, cta
    content = Column(Text)
    finalized = Column(Boolean, default=False)
    iterations = Column(Integer, default=0)
    
    # Metadata storage
    metadata_json = Column(JSON)  # Store acts, enhanced drafts, etc.
    options_json = Column(JSON)  # Store generated options
    feedback_history = Column(JSON)  # Store feedback history
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship
    project = relationship("Project", back_populates="components")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary."""
        return {
            'id': self.id,
            'type': self.component_type,
            'content': self.content,
            'finalized': self.finalized,
            'iterations': self.iterations,
            'metadata': self.metadata_json or {},
            'options': self.options_json or [],
            'feedback_history': self.feedback_history or [],
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Session(Base):
    """Session tracking for conversation history."""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    session_data = Column(JSON)  # Store conversation history and state
    active_module = Column(String(50))  # Current active module
    workflow_state = Column(JSON)  # Store workflow-specific state (act number, etc.)
    
    # Timestamps
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime)
    
    # Relationship
    project = relationship("Project", back_populates="sessions")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'session_data': self.session_data or {},
            'active_module': self.active_module,
            'workflow_state': self.workflow_state or {},
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }


class DatabaseManager:
    """Manager class for database operations."""
    
    def __init__(self, db_path: str = "video_scripts.db"):
        """Initialize database connection."""
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def create_project(self, topic: str, platform: str, target_audience: str = None, 
                      video_duration: str = None, title: str = None) -> Project:
        """Create a new project."""
        project = Project(
            title=title or f"{topic[:50]} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            topic=topic,
            platform=platform,
            target_audience=target_audience,
            video_duration=video_duration
        )
        self.session.add(project)
        self.session.commit()
        return project
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """Get a project by ID."""
        project = self.session.query(Project).filter_by(id=project_id).first()
        if project:
            # Update last accessed time
            project.last_accessed = datetime.now()
            self.session.commit()
        return project
    
    def list_projects(self, status: str = None, limit: int = 20) -> list:
        """List all projects, optionally filtered by status."""
        query = self.session.query(Project)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Project.last_accessed.desc()).limit(limit).all()
    
    def save_component(self, project_id: int, component_type: str, content: str, 
                      metadata: dict = None, options: list = None, finalized: bool = False) -> ScriptComponent:
        """Save or update a script component."""
        component = self.session.query(ScriptComponent).filter_by(
            project_id=project_id,
            component_type=component_type
        ).first()
        
        if component:
            # Update existing
            component.content = content
            component.metadata_json = metadata
            component.options_json = options
            component.finalized = finalized
            component.iterations += 1
        else:
            # Create new
            component = ScriptComponent(
                project_id=project_id,
                component_type=component_type,
                content=content,
                metadata_json=metadata,
                options_json=options,
                finalized=finalized
            )
            self.session.add(component)
        
        self.session.commit()
        return component
    
    def get_components(self, project_id: int) -> Dict[str, ScriptComponent]:
        """Get all components for a project."""
        components = self.session.query(ScriptComponent).filter_by(project_id=project_id).all()
        return {comp.component_type: comp for comp in components}
    
    def save_session(self, project_id: int, session_data: dict, active_module: str = None,
                    workflow_state: dict = None) -> Session:
        """Save session data."""
        # End any previous active sessions
        self.session.query(Session).filter_by(
            project_id=project_id,
            ended_at=None
        ).update({'ended_at': datetime.now()})
        
        # Create new session
        new_session = Session(
            project_id=project_id,
            session_data=session_data,
            active_module=active_module,
            workflow_state=workflow_state
        )
        self.session.add(new_session)
        self.session.commit()
        return new_session
    
    def get_latest_session(self, project_id: int) -> Optional[Session]:
        """Get the latest session for a project."""
        return self.session.query(Session).filter_by(
            project_id=project_id
        ).order_by(Session.started_at.desc()).first()
    
    def delete_project(self, project_id: int) -> bool:
        """Delete a project and all its components."""
        project = self.get_project(project_id)
        if project:
            self.session.delete(project)
            self.session.commit()
            return True
        return False
    
    def archive_project(self, project_id: int) -> bool:
        """Archive a project."""
        project = self.get_project(project_id)
        if project:
            project.status = 'archived'
            self.session.commit()
            return True
        return False
    
    def search_projects(self, query: str) -> list:
        """Search projects by topic or title."""
        return self.session.query(Project).filter(
            (Project.topic.contains(query)) | 
            (Project.title.contains(query))
        ).order_by(Project.last_accessed.desc()).all()
    
    def export_project(self, project_id: int) -> Dict[str, Any]:
        """Export a project as a dictionary for backup/sharing."""
        project = self.get_project(project_id)
        if not project:
            return None
        
        components = self.get_components(project_id)
        
        return {
            'project': project.to_dict(),
            'components': {
                comp_type: comp.to_dict() 
                for comp_type, comp in components.items()
            }
        }
    
    def close(self):
        """Close database connection."""
        self.session.close()