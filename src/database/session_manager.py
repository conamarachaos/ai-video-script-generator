"""Session management for video script projects."""

import json
from typing import Optional, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from .models import DatabaseManager, Project
from ..models.config import VideoScriptState, ScriptComponent as StateComponent

console = Console()


class SessionManager:
    """Manages project sessions and state persistence."""
    
    def __init__(self, db_path: str = "video_scripts.db"):
        """Initialize session manager."""
        self.db = DatabaseManager(db_path)
        self.current_project_id: Optional[int] = None
        self.auto_save_enabled = True
    
    def show_projects_menu(self) -> Optional[int]:
        """Show interactive projects menu and return selected project ID."""
        projects = self.db.list_projects(status='in_progress')
        
        # Always show the welcome menu first
        console.print("\n[bold cyan]Welcome! What would you like to do?[/bold cyan]\n")
        
        if not projects:
            console.print("📝 [bold]1.[/bold] Create a new video script")
            console.print("📚 [bold]2.[/bold] View saved projects (none found)")
            console.print("\n[dim]No existing projects found. Let's create your first one![/dim]")
            
            choice = Prompt.ask("\n[bold]Your choice[/bold]", choices=["1", "new"], default="1")
            return None
        
        # Show menu options first
        console.print("📝 [bold]new[/bold] - Create a new video script")
        console.print("📚 [bold]1-{}[/bold] - Continue an existing project".format(len(projects)))
        console.print("🔍 [bold]search[/bold] - Search your projects")
        console.print("🗑️  [bold]delete[/bold] - Remove a project")
        console.print("\n[dim]All projects auto-save after every interaction[/dim]\n")
        
        # Then show the project table
        table = Table(title="📚 Your Saved Video Scripts", show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Title", style="white", width=40)
        table.add_column("Platform", style="green", width=10)
        table.add_column("Status", style="yellow", width=12)
        table.add_column("Last Modified", style="blue", width=20)
        
        for idx, project in enumerate(projects, 1):
            status_emoji = "🚧" if project.status == "in_progress" else "✅"
            table.add_row(
                str(idx),
                project.title[:40],
                project.platform,
                f"{status_emoji} {project.status}",
                project.updated_at.strftime("%Y-%m-%d %H:%M") if project.updated_at else "N/A"
            )
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask("[bold]Your choice[/bold]", default="new")
        
        if choice.lower() == 'new':
            return None
        elif choice.lower() == 'search':
            return self._search_projects()
        elif choice.lower() == 'delete':
            return self._delete_project_menu(projects)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                return projects[idx].id
        elif choice == "":
            return -1  # Special flag for no database
        
        return None
    
    def _search_projects(self) -> Optional[int]:
        """Search for projects."""
        query = Prompt.ask("[bold]Search for[/bold]")
        results = self.db.search_projects(query)
        
        if not results:
            console.print(f"\n[yellow]No projects found matching '{query}'[/yellow]")
            return None
        
        console.print(f"\n[green]Found {len(results)} matching projects:[/green]")
        for idx, project in enumerate(results, 1):
            console.print(f"  {idx}. {project.title} ({project.platform})")
        
        choice = Prompt.ask("\n[bold]Select project number[/bold]", default="cancel")
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                return results[idx].id
        
        return None
    
    def _delete_project_menu(self, projects: list) -> Optional[int]:
        """Delete project menu."""
        console.print("\n[red]Select project to delete:[/red]")
        for idx, project in enumerate(projects, 1):
            console.print(f"  {idx}. {project.title}")
        
        choice = Prompt.ask("\n[bold]Project number to delete[/bold]", default="cancel")
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                project = projects[idx]
                if Confirm.ask(f"[red]Delete '{project.title}'? This cannot be undone[/red]"):
                    self.db.delete_project(project.id)
                    console.print("[green]Project deleted successfully[/green]")
        
        return None
    
    def create_new_project(self, topic: str, platform: str, target_audience: str = None,
                          video_duration: str = None) -> int:
        """Create a new project and return its ID."""
        # Auto-generate a title (user can rename later if needed)
        from datetime import datetime
        timestamp = datetime.now().strftime("%m/%d %H:%M")
        default_title = f"{topic[:30]} - {platform.title()} ({timestamp})"
        
        # Optional: Ask for custom title or use auto-generated
        console.print(f"\n[dim]Project will be saved as: {default_title}[/dim]")
        custom_title = Prompt.ask("[bold]Custom project name (or Enter to use default)[/bold]", default="")
        
        title = custom_title if custom_title else default_title
        
        project = self.db.create_project(
            topic=topic,
            platform=platform,
            target_audience=target_audience,
            video_duration=video_duration,
            title=title
        )
        
        self.current_project_id = project.id
        console.print(f"\n[green]✅ Project '{title}' created and will auto-save after every interaction[/green]")
        return project.id
    
    def load_project_state(self, project_id: int) -> VideoScriptState:
        """Load a project and restore its state."""
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Create state from project
        state = VideoScriptState(
            topic=project.topic,
            platform=project.platform,
            target_audience=project.target_audience,
            video_duration=project.video_duration
        )
        
        # Load components
        components = self.db.get_components(project_id)
        
        for comp_type, comp in components.items():
            if comp_type == 'hook' and comp.content:
                state.hook = StateComponent(
                    type="hook",
                    content=comp.content,
                    finalized=comp.finalized,
                    iterations=comp.iterations,
                    metadata=comp.metadata_json or {},
                    all_options=comp.options_json or []
                )
                if comp.feedback_history:
                    state.hook.feedback_history = comp.feedback_history
                    
            elif comp_type == 'story' and comp.content:
                state.story = StateComponent(
                    type="story",
                    content=comp.content,
                    finalized=comp.finalized,
                    iterations=comp.iterations,
                    metadata=comp.metadata_json or {},
                    all_options=comp.options_json or []
                )
                if comp.feedback_history:
                    state.story.feedback_history = comp.feedback_history
                    
            elif comp_type == 'cta' and comp.content:
                state.cta = StateComponent(
                    type="cta",
                    content=comp.content,
                    finalized=comp.finalized,
                    iterations=comp.iterations,
                    metadata=comp.metadata_json or {},
                    all_options=comp.options_json or []
                )
                if comp.feedback_history:
                    state.cta.feedback_history = comp.feedback_history
        
        # Load session data
        session = self.db.get_latest_session(project_id)
        if session and session.session_data:
            state.conversation_history = session.session_data.get('conversation_history', [])
            state.active_module = session.active_module or 'idle'
            
            # Restore workflow state
            if session.workflow_state:
                if state.story:
                    state.story.metadata.update(session.workflow_state)
        
        self.current_project_id = project_id
        return state
    
    def save_state(self, state: VideoScriptState, project_id: int = None):
        """Save the current state to database."""
        if project_id == -1:  # No database flag
            return
            
        project_id = project_id or self.current_project_id
        if not project_id:
            return
        
        # Save components
        if state.hook:
            self.db.save_component(
                project_id=project_id,
                component_type='hook',
                content=state.hook.content,
                metadata=state.hook.metadata,
                options=state.hook.all_options,
                finalized=state.hook.finalized
            )
        
        if state.story:
            self.db.save_component(
                project_id=project_id,
                component_type='story',
                content=state.story.content,
                metadata=state.story.metadata,
                options=state.story.all_options,
                finalized=state.story.finalized
            )
        
        if state.cta:
            self.db.save_component(
                project_id=project_id,
                component_type='cta',
                content=state.cta.content,
                metadata=state.cta.metadata,
                options=state.cta.all_options,
                finalized=state.cta.finalized
            )
        
        # Save session data
        session_data = {
            'conversation_history': state.conversation_history[-50:]  # Keep last 50 items
        }
        
        workflow_state = {}
        if state.story and state.story.metadata:
            workflow_state = {
                'workflow_mode': state.story.metadata.get('workflow_mode'),
                'current_act': state.story.metadata.get('current_act'),
                'acts_content': state.story.metadata.get('acts_content'),
                'video_duration': state.story.metadata.get('video_duration'),
                'enhanced_draft': state.story.metadata.get('enhanced_draft'),
                'awaiting_timing': state.story.metadata.get('awaiting_timing'),
                'mood_handled': state.story.metadata.get('mood_handled')
            }
        
        self.db.save_session(
            project_id=project_id,
            session_data=session_data,
            active_module=state.active_module,
            workflow_state=workflow_state
        )
    
    def show_project_summary(self, project_id: int):
        """Show a summary of the loaded project."""
        project = self.db.get_project(project_id)
        if not project:
            return
        
        components = self.db.get_components(project_id)
        
        # Create summary panel
        summary_lines = [
            f"[bold]Title:[/bold] {project.title}",
            f"[bold]Topic:[/bold] {project.topic}",
            f"[bold]Platform:[/bold] {project.platform}",
            f"[bold]Audience:[/bold] {project.target_audience or 'General'}",
            f"[bold]Duration:[/bold] {project.video_duration or 'Not set'}",
            f"[bold]Created:[/bold] {project.created_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "[bold]Progress:[/bold]"
        ]
        
        # Add component status
        for comp_type in ['hook', 'story', 'cta']:
            comp = components.get(comp_type)
            if comp and comp.content:
                status = "✅ Complete" if comp.finalized else "🚧 In Progress"
                preview = comp.content[:50] + "..." if len(comp.content) > 50 else comp.content
                summary_lines.append(f"  • {comp_type.title()}: {status}")
                summary_lines.append(f"    [dim]{preview}[/dim]")
            else:
                summary_lines.append(f"  • {comp_type.title()}: ⏳ Not started")
        
        panel = Panel(
            "\n".join(summary_lines),
            title="📝 Project Loaded",
            border_style="green"
        )
        console.print("\n")
        console.print(panel)
        console.print("\n[green]Ready to continue where you left off![/green]\n")
    
    def export_to_file(self, project_id: int, filepath: str = None):
        """Export project to a JSON file."""
        data = self.db.export_project(project_id)
        if not data:
            console.print("[red]Project not found[/red]")
            return
        
        if not filepath:
            project = data['project']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"script_export_{project['id']}_{timestamp}.json"
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        console.print(f"[green]Project exported to {filepath}[/green]")
    
    def get_script_text(self, project_id: int) -> str:
        """Get the complete script as formatted text."""
        components = self.db.get_components(project_id)
        project = self.db.get_project(project_id)
        
        script_parts = [
            f"# {project.title}",
            f"Platform: {project.platform}",
            f"Audience: {project.target_audience or 'General'}",
            f"Duration: {project.video_duration or 'Not specified'}",
            "\n---\n"
        ]
        
        # Add hook
        if 'hook' in components and components['hook'].content:
            script_parts.append("## HOOK\n")
            script_parts.append(components['hook'].content)
            script_parts.append("\n")
        
        # Add story with acts if available
        if 'story' in components:
            story = components['story']
            if story.metadata_json and 'acts_content' in story.metadata_json:
                acts = story.metadata_json['acts_content']
                script_parts.append("## STORY\n")
                for i in range(1, 4):
                    act_key = f'act_{i}'
                    if act_key in acts and acts[act_key]:
                        script_parts.append(f"### Act {i}\n")
                        script_parts.append(acts[act_key])
                        script_parts.append("\n")
            elif story.content:
                script_parts.append("## STORY\n")
                script_parts.append(story.content)
                script_parts.append("\n")
        
        # Add CTA
        if 'cta' in components and components['cta'].content:
            script_parts.append("## CALL TO ACTION\n")
            script_parts.append(components['cta'].content)
            script_parts.append("\n")
        
        return "\n".join(script_parts)
    
    def close(self):
        """Close database connection."""
        self.db.close()