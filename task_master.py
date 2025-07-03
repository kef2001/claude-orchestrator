"""
Task Master - Native Python implementation
Integrated task management system for Claude Orchestrator
"""

import json
import os
import re
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status options"""
    PENDING = "pending"
    DONE = "done"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"
    
    @classmethod
    def is_valid(cls, status: str) -> bool:
        """Check if a status is valid"""
        return status in [s.value for s in cls]


@dataclass
class Subtask:
    """Subtask data structure"""
    id: int
    title: str
    description: str
    status: str = "pending"
    dependencies: List[int] = field(default_factory=list)
    details: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class Task:
    """Task data structure"""
    id: int
    title: str
    description: str
    status: str = "pending"
    dependencies: List[int] = field(default_factory=list)
    priority: str = "medium"
    details: Optional[str] = None
    testStrategy: Optional[str] = None
    subtasks: List[Subtask] = field(default_factory=list)
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    complexity: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert subtasks
        if self.subtasks:
            data['subtasks'] = [st.to_dict() if isinstance(st, Subtask) else st for st in self.subtasks]
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """Create Task from dictionary"""
        subtasks_data = data.pop('subtasks', [])
        task = cls(**data)
        
        # Convert subtasks
        task.subtasks = []
        for st in subtasks_data:
            if isinstance(st, dict):
                task.subtasks.append(Subtask(**st))
            else:
                task.subtasks.append(st)
        
        return task


class TaskManager:
    """Native Python Task Manager implementation"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.taskmaster_dir = self.project_root / ".taskmaster"
        self.tasks_dir = self.taskmaster_dir / "tasks"
        self.tasks_file = self.tasks_dir / "tasks.json"
        self.complexity_report_file = self.taskmaster_dir / "task-complexity-report.json"
        
        # Ensure directories exist
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        
        # Load tasks
        self.tasks_data = self._load_tasks()
        
    def _load_tasks(self) -> Dict:
        """Load tasks from file"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert task dicts to Task objects
                    if 'tasks' in data:
                        data['tasks'] = [Task.from_dict(t) if isinstance(t, dict) else t for t in data['tasks']]
                    return data
            except Exception as e:
                logger.error(f"Error loading tasks: {e}")
                return self._create_empty_tasks_data()
        else:
            return self._create_empty_tasks_data()
    
    def _create_empty_tasks_data(self) -> Dict:
        """Create empty tasks data structure"""
        return {
            'meta': {
                'projectName': self.project_root.name,
                'projectVersion': '1.0.0',
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            },
            'tasks': []
        }
    
    def _save_tasks(self):
        """Save tasks to file"""
        try:
            # Update timestamp
            self.tasks_data['meta']['updatedAt'] = datetime.now().isoformat()
            
            # Convert Task objects to dicts
            data = self.tasks_data.copy()
            data['tasks'] = [t.to_dict() if isinstance(t, Task) else t for t in self.tasks_data['tasks']]
            
            # Save with pretty formatting
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(data['tasks'])} tasks to {self.tasks_file}")
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
            raise
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        return self.tasks_data.get('tasks', [])
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID"""
        # Handle subtask IDs (e.g., "1.2")
        if '.' in str(task_id):
            parent_id, subtask_id = str(task_id).split('.', 1)
            parent_task = self.get_task(parent_id)
            if parent_task and parent_task.subtasks:
                for subtask in parent_task.subtasks:
                    if str(subtask.id) == subtask_id:
                        return subtask
        else:
            # Regular task
            for task in self.get_all_tasks():
                if str(task.id) == str(task_id):
                    return task
        return None
    
    def add_task(self, title: str, description: str, 
                 dependencies: Optional[List[int]] = None,
                 priority: str = "medium",
                 details: Optional[str] = None,
                 testStrategy: Optional[str] = None) -> Task:
        """Add a new task"""
        # Find next available ID
        tasks = self.get_all_tasks()
        next_id = max([t.id for t in tasks], default=0) + 1
        
        # Create new task
        task = Task(
            id=next_id,
            title=title,
            description=description,
            status="pending",
            dependencies=dependencies or [],
            priority=priority,
            details=details,
            testStrategy=testStrategy,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
        
        # Add to tasks
        self.tasks_data['tasks'].append(task)
        self._save_tasks()
        
        logger.info(f"Added task {next_id}: {title}")
        return task
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        if not TaskStatus.is_valid(status):
            logger.error(f"Invalid status: {status}")
            return False
            
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        task.status = status
        task.updatedAt = datetime.now().isoformat()
        self._save_tasks()
        
        logger.info(f"Updated task {task_id} status to {status}")
        return True
    
    def add_subtask(self, parent_id: str, title: str, description: str,
                    dependencies: Optional[List[int]] = None) -> Optional[Subtask]:
        """Add a subtask to a parent task"""
        parent_task = self.get_task(parent_id)
        if not parent_task:
            logger.error(f"Parent task {parent_id} not found")
            return None
        
        # Find next subtask ID
        next_id = max([st.id for st in parent_task.subtasks], default=0) + 1
        
        # Create subtask
        subtask = Subtask(
            id=next_id,
            title=title,
            description=description,
            status="pending",
            dependencies=dependencies or [],
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
        
        parent_task.subtasks.append(subtask)
        self._save_tasks()
        
        logger.info(f"Added subtask {parent_id}.{next_id}: {title}")
        return subtask
    
    def get_next_task(self) -> Optional[Task]:
        """Get the next task to work on based on dependencies and priority"""
        tasks = self.get_all_tasks()
        
        # Filter for pending/in-progress tasks
        available_tasks = [t for t in tasks if t.status in ["pending", "in-progress"]]
        
        # Filter out tasks with unmet dependencies
        ready_tasks = []
        for task in available_tasks:
            deps_met = True
            for dep_id in task.dependencies:
                dep_task = self.get_task(str(dep_id))
                if dep_task and dep_task.status != "done":
                    deps_met = False
                    break
            if deps_met:
                ready_tasks.append(task)
        
        if not ready_tasks:
            return None
        
        # Sort by priority (high > medium > low) and ID
        priority_order = {"high": 3, "medium": 2, "low": 1}
        ready_tasks.sort(key=lambda t: (-priority_order.get(t.priority, 2), t.id))
        
        return ready_tasks[0]
    
    def get_task_subtask_progress(self, task_id: str) -> Tuple[int, int]:
        """Get subtask progress for a task (completed, total)"""
        task = self.get_task(task_id)
        if not task or not task.subtasks:
            return (0, 0)
        
        completed = sum(1 for st in task.subtasks if st.status == "done")
        total = len(task.subtasks)
        
        return (completed, total)
    
    def validate_dependencies(self) -> List[Dict[str, Any]]:
        """Validate all task dependencies"""
        issues = []
        tasks = self.get_all_tasks()
        task_ids = {t.id for t in tasks}
        
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    issues.append({
                        'task_id': task.id,
                        'task_title': task.title,
                        'invalid_dependency': dep_id,
                        'issue': f"Dependency {dep_id} does not exist"
                    })
                elif dep_id == task.id:
                    issues.append({
                        'task_id': task.id,
                        'task_title': task.title,
                        'invalid_dependency': dep_id,
                        'issue': "Task cannot depend on itself"
                    })
        
        return issues
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get all tasks with a specific status"""
        return [t for t in self.get_all_tasks() if t.status == status]
    
    def get_task_dependencies(self, task_id: str) -> List[Task]:
        """Get all tasks that depend on the given task"""
        dependent_tasks = []
        for task in self.get_all_tasks():
            if int(task_id) in task.dependencies:
                dependent_tasks.append(task)
        return dependent_tasks