#!/usr/bin/env python3
"""
Claude Orchestrator - Opus Manager with Sonnet Workers
Uses Task Master for task management and parallel processing
"""

import asyncio
import subprocess
import json
import os
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import shlex
from pathlib import Path
import re
import time
from datetime import timedelta

# Import the new configuration management system
try:
    from config_manager import ConfigurationManager, EnhancedConfig, ConfigValidationResult
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False
    print("⚠️ Enhanced configuration manager not available. Install requirements: pip install -r requirements.txt")

# Import error handling
try:
    from claude_error_handler import ClaudeErrorHandler, ClaudeError
    ERROR_HANDLER_AVAILABLE = True
except ImportError:
    ERROR_HANDLER_AVAILABLE = False
    logger.warning("Claude error handler not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProgressDisplay:
    """Handles real-time progress display with carriage return"""
    
    def __init__(self, total_tasks: int = 0):
        self.total_tasks = total_tasks
        self.completed = 0
        self.active = 0
        self.failed = 0
        self.start_time = time.time()
        self.current_status = ""
        self.last_update = 0
        self.update_interval = 0.1  # Update display every 100ms
        self.is_verbose = False
        self.last_line_length = 0
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        # Check if we're in a TTY (terminal) that supports carriage returns
        self.is_tty = sys.stdout.isatty() and os.environ.get('TERM', '') != 'dumb'
        
    def _clear_line(self):
        """Clear the current line"""
        if self.is_tty:
            # Use simple approach for better compatibility
            sys.stdout.write('\r' + ' ' * self.last_line_length + '\r')
        sys.stdout.flush()
        
    def _format_time(self, seconds: float) -> str:
        """Format elapsed time"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds//60:.0f}m {seconds%60:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"
    
    def _get_progress_bar(self, width: int = 20) -> str:
        """Generate a progress bar"""
        if self.total_tasks == 0:
            return "[" + "?" * width + "]"
        
        progress = (self.completed + self.failed) / self.total_tasks
        filled = int(width * progress)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
    
    def update(self, status: str = "", force: bool = False):
        """Update the progress display"""
        current_time = time.time()
        
        # Only update if enough time has passed or forced
        if not force and current_time - self.last_update < self.update_interval:
            return
            
        self.last_update = current_time
        elapsed = current_time - self.start_time
        
        # Update spinner
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
        spinner = self.spinner_frames[self.spinner_index]
        
        # Build status line
        progress_bar = self._get_progress_bar()
        percentage = ((self.completed + self.failed) / self.total_tasks * 100) if self.total_tasks > 0 else 0
        
        # Add spinner when tasks are active
        activity_indicator = spinner if self.active > 0 else "✨"
        
        if self.is_tty:
            # For TTY, use carriage return to overwrite line
            status_content = (
                f"{progress_bar} {percentage:3.0f}% | "
                f"✓ {self.completed} 📝 {self.active} ✗ {self.failed} / {self.total_tasks} | "
                f"⏱️  {self._format_time(elapsed)} | "
                f"{activity_indicator} {status[:50]}"
            )
            
            # Clear line first by overwriting with spaces
            if self.last_line_length > 0:
                sys.stdout.write('\r' + ' ' * self.last_line_length)
            
            # Write new status
            sys.stdout.write('\r' + status_content)
            sys.stdout.flush()
            self.last_line_length = len(status_content)
        else:
            # For non-TTY (pipe, redirect), print each update on a new line
            status_line = (
                f"{progress_bar} {percentage:3.0f}% | "
                f"✓ {self.completed} 📝 {self.active} ✗ {self.failed} / {self.total_tasks} | "
                f"⏱️  {self._format_time(elapsed)} | "
                f"{activity_indicator} {status[:50]}"
            )
            print(status_line)
        
    def log_message(self, message: str, level: str = "INFO"):
        """Log a message while preserving the progress display"""
        # Clear current line
        self._clear_line()
        
        # Print the message
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "ERROR":
            print(f"[{timestamp}] ❌ {message}")
        elif level == "SUCCESS":
            print(f"[{timestamp}] ✅ {message}")
        elif level == "WARNING":
            print(f"[{timestamp}] ⚠️  {message}")
        else:
            print(f"[{timestamp}] ℹ️  {message}")
        
        # Restore progress display
        self.update(force=True)
        
    def finish(self):
        """Complete the progress display"""
        self.update(force=True)
        if self.is_tty:
            print()  # New line after progress only for TTY
        
        # Print summary
        elapsed = time.time() - self.start_time
        print(f"\n📊 Summary:")
        print(f"   Total tasks: {self.total_tasks}")
        print(f"   Completed: {self.completed} ✅")
        print(f"   Failed: {self.failed} ❌")
        print(f"   Time elapsed: {self._format_time(elapsed)}")
        
        if self.completed > 0:
            avg_time = elapsed / self.completed
            print(f"   Average time per task: {self._format_time(avg_time)}")


def create_config(config_path: Optional[str] = None) -> Any:
    """Create configuration instance using enhanced or legacy system"""
    if CONFIG_MANAGER_AVAILABLE:
        # Use enhanced configuration management system
        config_paths = [config_path] if config_path else None
        config_manager = ConfigurationManager(config_paths)
        config_manager.load_configuration()
        
        # Validate configuration and show any issues
        validation_result = config_manager.get_validation_result()
        if not validation_result.is_valid:
            logger.error("Configuration validation failed:")
            for error in validation_result.errors:
                logger.error(f"  - {error}")
        
        if validation_result.warnings:
            logger.warning("Configuration warnings:")
            for warning in validation_result.warnings:
                logger.warning(f"  - {warning}")
        
        return EnhancedConfig(config_manager)
    else:
        # Fall back to legacy configuration system
        return LegacyConfig(config_path)


class LegacyConfig:
    """Legacy configuration manager for Claude Orchestrator (fallback)"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "orchestrator_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "models": {
                "manager": {
                    "model": "opus",
                    "description": "Opus model for planning and task management"
                },
                "worker": {
                    "model": "sonnet",
                    "description": "Sonnet model for code implementation"
                }
            },
            "execution": {
                "max_workers": 3,
                "worker_timeout": 300,
                "manager_timeout": 180,
                "task_queue_timeout": 1.0
            },
            "monitoring": {
                "progress_interval": 10,
                "verbose_logging": False
            },
            "claude_cli": {
                "command": "claude",
                "flags": {
                    "verbose": False,
                    "dangerously_skip_permissions": False
                }
            },
            "git": {
                "auto_commit": False,
                "commit_message_prefix": "🤖 Auto-commit by Claude Orchestrator"
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                return self._merge_configs(default_config, loaded_config)
            else:
                logger.info(f"Config file not found at {self.config_path}, using defaults")
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            return default_config
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults"""
        merged = default.copy()
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged
    
    @property
    def manager_model(self) -> str:
        return self.config["models"]["manager"]["model"]
    
    @property
    def worker_model(self) -> str:
        return self.config["models"]["worker"]["model"]
    
    @property
    def max_workers(self) -> int:
        return self.config["execution"]["max_workers"]
    
    @property
    def worker_timeout(self) -> int:
        return self.config["execution"]["worker_timeout"]
    
    @property
    def manager_timeout(self) -> int:
        return self.config["execution"]["manager_timeout"]
    
    @property
    def task_queue_timeout(self) -> float:
        return self.config["execution"]["task_queue_timeout"]
    
    @property
    def progress_interval(self) -> int:
        return self.config["monitoring"]["progress_interval"]
    
    @property
    def verbose_logging(self) -> bool:
        return self.config["monitoring"]["verbose_logging"]
    
    @property
    def enable_opus_review(self) -> bool:
        return self.config["monitoring"].get("enable_opus_review", True)
    
    @property
    def claude_command(self) -> str:
        return self.config["claude_cli"]["command"]
    
    @property
    def claude_flags(self) -> Dict[str, Any]:
        return self.config["claude_cli"]["flags"]
    
    @property
    def claude_settings(self) -> Dict[str, Any]:
        return self.config["claude_cli"].get("settings", {})
    
    @property
    def claude_environment(self) -> Dict[str, Any]:
        return self.config["claude_cli"].get("environment", {})
    
    @property
    def slack_webhook_url(self) -> Optional[str]:
        return self.config.get("notifications", {}).get("slack_webhook_url")
    
    @property
    def notify_on_task_complete(self) -> bool:
        return self.config.get("notifications", {}).get("notify_on_task_complete", True)
    
    @property
    def notify_on_task_failed(self) -> bool:
        return self.config.get("notifications", {}).get("notify_on_task_failed", True)
    
    @property
    def notify_on_all_complete(self) -> bool:
        return self.config.get("notifications", {}).get("notify_on_all_complete", True)
    
    @property
    def max_turns(self) -> Optional[int]:
        return self.config["execution"].get("max_turns")
    
    @property
    def default_working_dir(self) -> str:
        return self.config["execution"].get("default_working_dir", os.getcwd())
    
    @property
    def bash_default_timeout_ms(self) -> int:
        return self.config["execution"].get("bash_default_timeout_ms", 120000)
    
    @property
    def bash_max_timeout_ms(self) -> int:
        return self.config["execution"].get("bash_max_timeout_ms", 600000)
    
    @property
    def bash_max_output_length(self) -> int:
        return self.config["execution"].get("bash_max_output_length", 30000)
    
    @property
    def show_progress_bar(self) -> bool:
        return self.config["monitoring"].get("show_progress_bar", True)
    
    @property
    def git_auto_commit(self) -> bool:
        return self.config.get("git", {}).get("auto_commit", False)
    
    @property
    def git_commit_prefix(self) -> str:
        return self.config.get("git", {}).get("commit_message_prefix", "🤖 Auto-commit by Claude Orchestrator")


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "done"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class WorkerTask:
    """Task to be processed by a Sonnet worker"""
    task_id: str
    title: str
    description: str
    details: Optional[str] = None
    dependencies: List[str] = None
    status: TaskStatus = TaskStatus.PENDING
    assigned_worker: Optional[int] = None
    result: Optional[str] = None
    error: Optional[str] = None
    status_message: Optional[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class SlackNotificationManager:
    """Manages Slack webhook notifications"""
    
    def __init__(self, webhook_url: Optional[str]):
        self.webhook_url = webhook_url
        
    def send_notification(self, message: str, emoji: str = ":robot_face:", blocks: List[Dict] = None) -> bool:
        """Send a notification to Slack via webhook"""
        if not self.webhook_url:
            return False
            
        try:
            # Prepare the payload
            payload = {
                "text": f"{emoji} {message}"
            }
            
            # Add blocks if provided
            if blocks:
                payload["blocks"] = blocks
            
            # Use curl to send the notification
            cmd = [
                "curl",
                "-X", "POST",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payload),
                self.webhook_url,
                "-s"  # Silent mode
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.debug("Slack notification sent successfully")
                return True
            else:
                logger.error(f"Failed to send Slack notification: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    def send_task_complete(self, task_id: str, task_title: str) -> bool:
        """Send notification for completed task"""
        message = f"Task completed: [{task_id}] {task_title}"
        return self.send_notification(message, ":white_check_mark:")
    
    def send_task_failed(self, task_id: str, task_title: str, error: str = "") -> bool:
        """Send notification for failed task"""
        message = f"Task failed: [{task_id}] {task_title}"
        if error:
            message += f"\nError: {error}"
        return self.send_notification(message, ":x:")
    
    def send_all_complete(self, total_tasks: int, completed: int, failed: int, elapsed_time: str) -> bool:
        """Send notification when all tasks are complete"""
        message = (f"All tasks complete!\n"
                  f"Total: {total_tasks} | Completed: {completed} | Failed: {failed}\n"
                  f"Time: {elapsed_time}")
        emoji = ":tada:" if failed == 0 else ":warning:"
        return self.send_notification(message, emoji)
    
    def send_opus_review(self, review_summary: str, task_results: List[Dict[str, Any]], elapsed_time: str, follow_up_count: int = 0) -> bool:
        """Send Opus review notification with structured blocks"""
        if not self.webhook_url:
            return False
        
        # Build blocks for the notification
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎭 Opus Review Complete",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{review_summary[:500]}..."
                }
            },
            {
                "type": "divider"
            }
        ]
        
        # Add task results
        for result in task_results[:10]:  # Limit to 10 tasks to avoid message being too long
            status_emoji = "✅" if result.get("status") == "completed" else "❌"
            task_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{status_emoji} *{result.get('title', 'Unknown Task')}*\n_{result.get('summary', 'No summary available')}_"
                }
            }
            blocks.append(task_block)
        
        if len(task_results) > 10:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"_... and {len(task_results) - 10} more tasks_"
                }
            })
        
        # Add follow-up tasks info if any
        if follow_up_count > 0:
            blocks.extend([
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🔧 *Follow-up Tasks Created:* {follow_up_count}\n_Run orchestrator again to process improvements_"
                    }
                }
            ])
        
        # Add footer with stats
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏱️ Total time: {elapsed_time} | 📊 Tasks: {len(task_results)} | 🤖 Orchestrator: Claude"
                    }
                ]
            }
        ])
        
        return self.send_notification("Opus Review Complete", ":robot_face:", blocks)


class TaskMasterInterface:
    """Interface to interact with Task Master CLI"""
    
    def __init__(self):
        self.taskmaster_cmd = "task-master"
    
    def _run_command(self, args: List[str]) -> tuple[bool, str]:
        """Run a task-master command and return success status and output"""
        try:
            cmd = [self.taskmaster_cmd] + args
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            if not success:
                logger.error(f"Command failed: {output}")
            
            return success, output.strip()
        except Exception as e:
            logger.error(f"Error running task-master command: {e}")
            return False, str(e)
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the next available task"""
        success, output = self._run_command(["next"])
        if success and output and "No pending tasks available" not in output:
            # Try to get the task ID from the output and fetch details
            lines = output.strip().split('\n')
            for line in lines:
                if 'Next task:' in line:
                    # Extract task ID
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'task:' and i + 1 < len(parts):
                            task_id = parts[i + 1].strip(':')
                            # Get full task details
                            task_details = self.get_task(task_id)
                            if task_details:
                                return task_details
                            else:
                                return {'id': task_id, 'title': 'Unknown'}
            # If we can't parse, return a simple dict
            return {'id': 'unknown', 'title': output}
        return None
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific task"""
        success, output = self._run_command(["show", task_id])
        if success and output:
            # Parse the text output to extract task details
            task_data = self._parse_task_output(output, task_id)
            return task_data
        return None
    
    def _parse_task_output(self, output: str, task_id: str) -> Dict[str, Any]:
        """Parse task output text to extract task details"""
        # Simple parsing - extract key information
        lines = output.strip().split('\n')
        task = {
            'id': task_id,
            'title': '',
            'description': '',
            'status': 'pending',
            'priority': 'medium',
            'dependencies': []
        }
        
        for line in lines:
            if 'Title:' in line:
                task['title'] = line.split('Title:', 1)[1].strip()
            elif 'Description:' in line:
                task['description'] = line.split('Description:', 1)[1].strip()
            elif 'Status:' in line:
                task['status'] = line.split('Status:', 1)[1].strip()
            elif 'Priority:' in line:
                task['priority'] = line.split('Priority:', 1)[1].strip()
        
        return task
    
    def set_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        success, _ = self._run_command([
            "set-status",
            f"--id={task_id}",
            f"--status={status}"
        ])
        return success
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks"""
        success, output = self._run_command(["list"])
        if success and output:
            # Parse the text output to extract task list
            return self._parse_task_list(output)
        return []
    
    def _parse_task_list(self, output: str) -> List[Dict[str, Any]]:
        """Parse task list output"""
        tasks = []
        lines = output.strip().split('\n')
        
        in_table = False
        for line in lines:
            # Look for table rows with task data
            if '│' in line and not ('─' in line or '┌' in line or '└' in line or '├' in line or '┤' in line):
                # Check if this is the header row
                if 'ID' in line and 'Title' in line and 'Status' in line:
                    in_table = True
                    continue
                
                if in_table:
                    # Parse table row
                    parts = [p.strip() for p in line.split('│') if p.strip()]
                    if len(parts) >= 2:
                        task_id = parts[0].strip()
                        # Check if it's a valid task ID (numeric or numeric with dots)
                        if task_id and (task_id.isdigit() or all(p.isdigit() for p in task_id.split('.'))):
                            title = parts[1].strip() if len(parts) > 1 else ''
                            # Remove ellipsis from truncated titles
                            if title.endswith('...'):
                                # Try to get full title from task details
                                full_task = self.get_task(task_id)
                                if full_task and full_task.get('title'):
                                    title = full_task['title']
                                else:
                                    title = title[:-3].strip()
                            
                            # Extract status (might be in format "○ pending" or just "pending")
                            status = 'pending'
                            if len(parts) > 2:
                                status_part = parts[2].strip()
                                if 'pending' in status_part:
                                    status = 'pending'
                                elif 'in-progress' in status_part:
                                    status = 'in-progress'
                                elif 'done' in status_part:
                                    status = 'done'
                            
                            # Extract priority
                            priority = 'medium'
                            if len(parts) > 3:
                                priority = parts[3].strip() or 'medium'
                            
                            tasks.append({
                                'id': task_id,
                                'title': title,
                                'status': status,
                                'description': '',
                                'priority': priority,
                                'dependencies': []
                            })
        
        # Also look for subtasks in the recommended section
        in_subtasks = False
        for line in lines:
            if 'Subtasks:' in line:
                in_subtasks = True
                continue
            
            if in_subtasks and line.strip():
                # Parse lines like "1.1 [pending] Verify Python installation"
                match = re.match(r'(\d+\.\d+)\s*\[(\w+)\]\s*(.+)', line.strip())
                if match:
                    task_id = match.group(1)
                    status = match.group(2)
                    title = match.group(3)
                    
                    # Check if we already have this task
                    if not any(t['id'] == task_id for t in tasks):
                        tasks.append({
                            'id': task_id,
                            'title': title,
                            'status': status,
                            'description': '',
                            'priority': 'medium',
                            'dependencies': []
                        })
        
        return tasks
    
    def update_subtask(self, task_id: str, notes: str) -> bool:
        """Update subtask with implementation notes"""
        success, _ = self._run_command([
            "update-subtask",
            f"--id={task_id}",
            f"--prompt={notes}"
        ])
        return success


class OpusManager:
    """Opus model acting as the manager/orchestrator"""
    
    def __init__(self, config):
        self.config = config
        self.max_workers = config.max_workers
        self.task_master = TaskMasterInterface()
        self.task_queue: queue.Queue[WorkerTask] = queue.Queue()
        self.completed_tasks: Dict[str, WorkerTask] = {}
        self.failed_tasks: Dict[str, WorkerTask] = {}
        self.active_tasks: Dict[str, WorkerTask] = {}
        
    def analyze_and_plan(self) -> List[WorkerTask]:
        """Use Opus to analyze tasks and create execution plan"""
        logger.info("Opus Manager: Analyzing project tasks...")
        
        # Show loading indicator
        sys.stdout.write("⏳ Fetching tasks from Task Master...")
        sys.stdout.flush()
        
        # Get all tasks from Task Master
        all_tasks = self.task_master.list_tasks()
        
        sys.stdout.write("\r✅ Fetched tasks from Task Master" + " " * 20 + "\n")
        sys.stdout.flush()
        
        if not all_tasks:
            logger.warning("No tasks found in Task Master")
            return []
        
        # Convert Task Master tasks to WorkerTasks
        sys.stdout.write("🔍 Analyzing task dependencies and priorities...")
        sys.stdout.flush()
        
        worker_tasks = []
        for task in all_tasks:
            if task.get('status') in ['pending', 'in-progress']:
                worker_task = WorkerTask(
                    task_id=task.get('id', ''),
                    title=task.get('title', ''),
                    description=task.get('description', ''),
                    details=task.get('details'),
                    dependencies=task.get('dependencies', []),
                    status=TaskStatus.PENDING
                )
                worker_tasks.append(worker_task)
        
        sys.stdout.write(f"\r✅ Found {len(worker_tasks)} tasks to process" + " " * 30 + "\n")
        sys.stdout.flush()
        
        # Here you would normally call Opus API to analyze and prioritize tasks
        # For now, we'll use a simple dependency-based ordering
        return self._order_tasks_by_dependencies(worker_tasks)
    
    def _order_tasks_by_dependencies(self, tasks: List[WorkerTask]) -> List[WorkerTask]:
        """Order tasks based on dependencies"""
        ordered = []
        remaining = tasks.copy()
        completed_ids = set()
        
        while remaining:
            # Find tasks with no pending dependencies
            ready_tasks = [
                task for task in remaining
                if all(dep in completed_ids for dep in task.dependencies)
            ]
            
            if not ready_tasks:
                # If no tasks are ready, there might be circular dependencies
                logger.warning("Possible circular dependencies detected")
                ordered.extend(remaining)
                break
            
            # Add ready tasks to ordered list
            for task in ready_tasks:
                ordered.append(task)
                completed_ids.add(task.task_id)
                remaining.remove(task)
        
        return ordered
    
    def delegate_task(self, task: WorkerTask) -> None:
        """Add task to the queue for workers to process"""
        logger.info(f"Delegating task {task.task_id}: {task.title}")
        self.task_queue.put(task)
    
    def monitor_progress(self) -> None:
        """Monitor task progress and log status"""
        total_tasks = len(self.active_tasks) + len(self.completed_tasks) + len(self.failed_tasks)
        
        logger.info(f"\n=== Task Progress ===")
        logger.info(f"Active: {len(self.active_tasks)}")
        logger.info(f"Completed: {len(self.completed_tasks)}")
        logger.info(f"Failed: {len(self.failed_tasks)}")
        logger.info(f"Queued: {self.task_queue.qsize()}")
        logger.info(f"Total: {total_tasks}")
        
        if self.active_tasks:
            logger.info("\nActive tasks:")
            for task_id, task in self.active_tasks.items():
                logger.info(f"  - {task_id}: {task.title} (Worker {task.assigned_worker})")


class SonnetWorker:
    """Sonnet model acting as a worker"""
    
    def __init__(self, worker_id: int, working_dir: str, config):
        self.worker_id = worker_id
        self.working_dir = working_dir
        self.config = config
        self.task_master = TaskMasterInterface()
        self.session_tokens_used = 0
        self.session_start_time = time.time()
        self.tasks_completed = 0
        
        # Initialize error handler
        self.error_handler = None
        if ERROR_HANDLER_AVAILABLE:
            self.error_handler = ClaudeErrorHandler(
                max_retries=getattr(config, 'max_retries', 3),
                base_delay=getattr(config, 'retry_base_delay', 1.0),
                max_delay=getattr(config, 'retry_max_delay', 60.0)
            )
        
        logger.info(f"Worker {worker_id} initialized in {working_dir}")
    
    def process_task(self, task: WorkerTask) -> WorkerTask:
        """Process a single task using Claude CLI"""
        logger.info(f"Worker {self.worker_id}: Starting task {task.task_id} - {task.title}")
        
        try:
            # Update task status in Task Master
            self.task_master.set_task_status(task.task_id, "in-progress")
            task.status_message = "Updating task status..."
            
            # Create a prompt for Claude
            prompt = self._create_claude_prompt(task)
            
            # Execute Claude command (will use retry logic if error handler is available)
            result = self._execute_claude_command(prompt)
            
            if result['success']:
                task.status = TaskStatus.COMPLETED
                task.result = result['output']
                self.task_master.set_task_status(task.task_id, "done")
                
                # Track usage
                if 'usage' in result:
                    usage = result['usage']
                    self.session_tokens_used += usage.get('tokens_used', 0)
                    self.tasks_completed += 1
                    
                    # Log usage warning if present
                    if usage.get('warning'):
                        logger.warning(f"Worker {self.worker_id} - Usage Warning: {usage['warning']}")
                        logger.warning(f"Total tokens used this session: {self.session_tokens_used}")
                
                # Update subtask with completion notes
                completion_notes = f"Completed by Worker {self.worker_id}. Output: {result['output'][:200]}..."
                self.task_master.update_subtask(task.task_id, completion_notes)
                
                logger.info(f"Worker {self.worker_id}: Completed task {task.task_id}")
            else:
                task.status = TaskStatus.FAILED
                task.error = result['error']
                
                # Check if it's a usage limit error
                if "USAGE LIMIT" in result['error']:
                    logger.error(f"Worker {self.worker_id}: USAGE LIMIT REACHED - Cannot continue processing")
                    # Set a flag to stop this worker
                    task.error = "USAGE_LIMIT_REACHED"
                else:
                    logger.error(f"Worker {self.worker_id}: Failed task {task.task_id} - {result['error']}")
                
                # Log request ID if available
                if 'request_id' in result and result['request_id']:
                    logger.error(f"Request ID for debugging: {result['request_id']}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Worker {self.worker_id}: Exception processing task {task.task_id} - {e}")
        
        return task
    
    def _create_claude_prompt(self, task: WorkerTask) -> str:
        """Create a prompt for Claude based on the task"""
        prompt_parts = [
            f"Task ID: {task.task_id}",
            f"Title: {task.title}",
            f"Description: {task.description}"
        ]
        
        if task.details:
            prompt_parts.append(f"Details: {task.details}")
        
        prompt_parts.append("\nPlease complete this task. Start by analyzing what needs to be done, then implement the solution.")
        prompt_parts.append("\nIMPORTANT: If this task requires creating files, make sure to actually create them using the Write or Edit tools.")
        
        return "\n".join(prompt_parts)
    
    def _execute_claude_command(self, prompt: str) -> Dict[str, Any]:
        """Wrapper for executing Claude command - uses error handler if available"""
        if self.error_handler:
            return self.error_handler.execute_with_retry(
                self._execute_claude_command_internal, prompt
            )
        else:
            return self._execute_claude_command_internal(prompt)
    
    def _execute_claude_command_internal(self, prompt: str) -> Dict[str, Any]:
        """Execute Claude CLI command with the given prompt"""
        try:
            # First check if Claude CLI is available and authenticated
            test_cmd = [self.config.claude_command, "--version"]
            test_result = subprocess.run(test_cmd, capture_output=True, text=True)
            if test_result.returncode != 0:
                return {
                    'success': False,
                    'error': f"Claude CLI not available or not authenticated: {test_result.stderr}"
                }
            
            # Save prompt to temporary file to avoid shell escaping issues
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name
            
            # Construct Claude command
            cmd = [
                self.config.claude_command,
                "-p", f"@{prompt_file}",
                "--model", self.config.worker_model
            ]
            
            # Add additional flags from config
            if self.config.claude_flags.get("verbose"):
                cmd.append("--verbose")
            if self.config.claude_flags.get("dangerously_skip_permissions"):
                cmd.append("--dangerously-skip-permissions")
            
            # Add other CLI flags
            if self.config.claude_flags.get("add_dir"):
                for dir_path in self.config.claude_flags["add_dir"]:
                    cmd.extend(["--add-dir", dir_path])
            
            if self.config.claude_flags.get("allowed_tools"):
                for tool in self.config.claude_flags["allowed_tools"]:
                    cmd.extend(["--allowedTools", tool])
            
            if self.config.claude_flags.get("disallowed_tools"):
                for tool in self.config.claude_flags["disallowed_tools"]:
                    cmd.extend(["--disallowedTools", tool])
            
            if self.config.claude_flags.get("output_format") and self.config.claude_flags["output_format"] != "text":
                cmd.extend(["--output-format", self.config.claude_flags["output_format"]])
            
            if self.config.claude_flags.get("input_format") and self.config.claude_flags["input_format"] != "text":
                cmd.extend(["--input-format", self.config.claude_flags["input_format"]])
            
            if self.config.max_turns:
                cmd.extend(["--max-turns", str(self.config.max_turns)])
            
            if self.config.claude_flags.get("permission_mode"):
                cmd.extend(["--permission-mode", self.config.claude_flags["permission_mode"]])
            
            if self.config.claude_flags.get("permission_prompt_tool"):
                cmd.extend(["--permission-prompt-tool", self.config.claude_flags["permission_prompt_tool"]])
            
            logger.debug(f"Worker {self.worker_id}: Executing command: {' '.join(cmd)}")
            
            # Set up environment variables
            env = os.environ.copy()
            
            # First check if ANTHROPIC_API_KEY is already in environment
            if "ANTHROPIC_API_KEY" not in env:
                # Try to get it from .env file
                if os.path.exists(".env"):
                    with open(".env", "r") as f:
                        for line in f:
                            if line.startswith("ANTHROPIC_API_KEY="):
                                api_key = line.strip().split("=", 1)[1]
                                env["ANTHROPIC_API_KEY"] = api_key
                                logger.debug("Loaded ANTHROPIC_API_KEY from .env file")
                                break
            
            # Apply config environment variables (can override)
            for key, value in self.config.claude_environment.items():
                if value is not None:
                    env[key] = str(value)
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.working_dir,
                timeout=self.config.worker_timeout,
                env=env
            )
            
            # Clean up temp file
            os.unlink(prompt_file)
            
            if result.returncode == 0:
                # Try to extract usage information from output
                usage_info = self._extract_usage_info(result.stdout)
                return {
                    'success': True,
                    'output': result.stdout,
                    'usage': usage_info
                }
            else:
                error_msg = f"Command failed with code {result.returncode}\n"
                if result.stderr:
                    error_msg += f"STDERR: {result.stderr}\n"
                if result.stdout:
                    error_msg += f"STDOUT: {result.stdout}\n"
                    
                # Check for rate limit or usage errors
                if "rate limit" in error_msg.lower() or "usage limit" in error_msg.lower():
                    error_msg = f"⚠️ USAGE LIMIT REACHED: {error_msg}"
                    
                return {
                    'success': False,
                    'error': error_msg,
                    'return_code': result.returncode
                }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f"Command timed out after {self.config.worker_timeout} seconds",
                'return_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'return_code': -1
            }
    
    def _extract_usage_info(self, output: str) -> Dict[str, Any]:
        """Extract usage information from Claude CLI output"""
        usage_info = {
            'tokens_used': 0,
            'cost_estimate': 0.0,
            'warning': None
        }
        
        # Look for token usage patterns in output
        # Common patterns: "Tokens used: X", "Usage: X tokens", etc.
        token_patterns = [
            r'tokens?\s*used[:\s]+(\d+)',
            r'usage[:\s]+(\d+)\s*tokens?',
            r'consumed[:\s]+(\d+)\s*tokens?',
            r'(\d+)\s*tokens?\s*consumed'
        ]
        
        for pattern in token_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                usage_info['tokens_used'] = int(match.group(1))
                break
        
        # Look for cost information
        cost_patterns = [
            r'\$(\d+\.\d+)',
            r'cost[:\s]+\$?(\d+\.\d+)',
            r'estimated\s+cost[:\s]+\$?(\d+\.\d+)'
        ]
        
        for pattern in cost_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                usage_info['cost_estimate'] = float(match.group(1))
                break
        
        # Look for usage warnings
        if "approaching limit" in output.lower() or "near limit" in output.lower():
            usage_info['warning'] = "Approaching usage limit"
        elif "80%" in output or "90%" in output:
            usage_info['warning'] = "High usage percentage detected"
            
        return usage_info


class ClaudeOrchestrator:
    """Main orchestrator coordinating Opus manager and Sonnet workers"""
    
    def __init__(self, config, working_dir: Optional[str] = None):
        self.config = config
        self.working_dir = os.path.abspath(working_dir) if working_dir else os.getcwd()
        self.manager = OpusManager(config)
        self.workers: List[SonnetWorker] = []
        self.max_workers = config.max_workers
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self.running = False
        self.progress = None
        # Use progress display if enabled and not in verbose mode
        self.use_progress_display = (
            config.show_progress_bar and 
            not config.verbose_logging
        )
        self.usage_warnings = []
        self.workers_at_limit = set()
        
        # Initialize Opus review system
        self.review_executor = ThreadPoolExecutor(max_workers=max(2, config.max_workers // 2))
        self.review_queue = queue.Queue()
        self.pending_reviews = {}  # task_id -> Future
        
        # Initialize Slack notification manager
        self.slack_notifier = SlackNotificationManager(config.slack_webhook_url)
        
        # Verify working directory exists
        if not os.path.exists(self.working_dir):
            raise ValueError(f"Working directory does not exist: {self.working_dir}")
        
        logger.info(f"Orchestrator initialized with working directory: {self.working_dir}")
        
    def initialize(self, task_count: int = None):
        """Initialize the orchestrator with dynamic worker count"""
        logger.info("Initializing Claude Orchestrator...")
        
        # Determine optimal worker count based on tasks
        if task_count:
            # Create workers based on task count, but respect max_workers limit
            optimal_workers = min(task_count, self.max_workers)
            # At least 1 worker, but no more than configured maximum
            worker_count = max(1, optimal_workers)
        else:
            worker_count = self.max_workers
        
        # Update thread pool size
        self.executor = ThreadPoolExecutor(max_workers=worker_count)
        
        # Create workers
        for i in range(worker_count):
            worker = SonnetWorker(i, self.working_dir, self.config)
            self.workers.append(worker)
        
        logger.info(f"Created {worker_count} Sonnet workers for {task_count or 'unknown'} tasks")
    
    def review_loop(self):
        """Loop that processes Opus reviews in parallel"""
        while self.running or not self.review_queue.empty():
            try:
                # Get task from review queue with timeout
                task = self.review_queue.get(timeout=1.0)
                
                if self.use_progress_display and self.progress:
                    self.progress.log_message(f"🔍 Opus reviewing task {task.task_id}: {task.title}", "INFO")
                else:
                    logger.info(f"🔍 Opus reviewing task {task.task_id}: {task.title}")
                
                # Perform the review
                review_result = self._opus_review_single_task(task)
                
                if review_result['success']:
                    if review_result['needs_improvement']:
                        # Task needs improvement
                        if self.use_progress_display and self.progress:
                            self.progress.log_message(
                                f"📝 Task {task.task_id} needs improvements ({review_result['follow_up_count']} follow-up tasks created)",
                                "WARNING"
                            )
                        else:
                            logger.warning(f"Task {task.task_id} needs improvements ({review_result['follow_up_count']} follow-up tasks created)")
                        
                        # Update task status to indicate review found issues
                        task.status_message = f"Review complete - {review_result['follow_up_count']} improvements needed"
                    else:
                        # Task passed review
                        if self.use_progress_display and self.progress:
                            self.progress.log_message(f"✅ Task {task.task_id} passed Opus review", "SUCCESS")
                        else:
                            logger.info(f"✅ Task {task.task_id} passed Opus review")
                        
                        task.status_message = "Review complete - No issues found"
                    
                    # Log the review summary
                    logger.debug(f"Opus review for task {task.task_id}:\n{review_result['review']}")
                else:
                    logger.error(f"Opus review failed for task {task.task_id}: {review_result.get('error', 'Unknown error')}")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in review loop: {e}")
        
        logger.info("Review loop stopped")
    
    def worker_loop(self, worker: SonnetWorker):
        """Worker loop that processes tasks from the queue"""
        if self.use_progress_display and self.progress:
            self.progress.log_message(f"Worker {worker.worker_id} started", "INFO")
        else:
            logger.info(f"Worker {worker.worker_id} started")
            
        while self.running:
            try:
                # Get task from queue with timeout
                task = self.manager.task_queue.get(timeout=self.config.task_queue_timeout)
                
                # Mark task as active
                task.assigned_worker = worker.worker_id
                self.manager.active_tasks[task.task_id] = task
                
                # Update progress display
                if self.use_progress_display and self.progress:
                    self.progress.active = len(self.manager.active_tasks)
                    self.progress.update(f"Worker {worker.worker_id}: {task.title[:40]}...")
                
                # Process task
                completed_task = worker.process_task(task)
                
                # Move task to appropriate collection
                del self.manager.active_tasks[task.task_id]
                
                if completed_task.status == TaskStatus.COMPLETED:
                    # First mark as completed
                    self.manager.completed_tasks[task.task_id] = completed_task
                    if self.use_progress_display and self.progress:
                        self.progress.completed += 1
                        self.progress.active = len(self.manager.active_tasks)
                        self.progress.log_message(f"✅ Task {task.task_id} completed: {task.title[:40]}...", "SUCCESS")
                    
                    # Submit task for Opus review
                    self.review_queue.put(completed_task)
                    if self.use_progress_display and self.progress:
                        self.progress.log_message(f"📋 Task {task.task_id} submitted for Opus review", "INFO")
                    
                    # Send Slack notification for completed task
                    if self.config.notify_on_task_complete:
                        self.slack_notifier.send_task_complete(task.task_id, task.title)
                else:
                    self.manager.failed_tasks[task.task_id] = completed_task
                    if self.use_progress_display and self.progress:
                        self.progress.failed += 1
                        self.progress.active = len(self.manager.active_tasks)
                        self.progress.log_message(f"❌ Task {task.task_id} failed: {task.title[:40]}...", "ERROR")
                    
                    # Send Slack notification for failed task
                    if self.config.notify_on_task_failed:
                        error_msg = completed_task.error or "Unknown error"
                        self.slack_notifier.send_task_failed(task.task_id, task.title, error_msg)
                    
                    # Check if worker hit usage limit
                    if completed_task.error == "USAGE_LIMIT_REACHED":
                        self.workers_at_limit.add(worker.worker_id)
                        if self.use_progress_display and self.progress:
                            self.progress.log_message(
                                f"⚠️ Worker {worker.worker_id} reached usage limit and will stop", 
                                "WARNING"
                            )
                        # Stop this worker
                        break
                
                # Mark queue task as done
                self.manager.task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                if self.use_progress_display and self.progress:
                    self.progress.log_message(f"Worker {worker.worker_id} error: {e}", "ERROR")
                else:
                    logger.error(f"Worker {worker.worker_id} error: {e}")
    
    def _format_elapsed_time(self, seconds: float) -> str:
        """Format elapsed time in human-readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds//60:.0f}m {seconds%60:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"
    
    def run(self):
        """Main orchestration loop"""
        logger.info("Starting Claude Orchestrator...")
        self.start_time = time.time()
        
        # Check usage before starting if configured
        if self.config.check_usage_before_start:
            print("\n📊 Checking Claude session status before starting...")
            if not check_claude_session_status():
                logger.error("Failed to check session status. Consider checking manually with 'python claude_orchestrator.py status'")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    logger.info("Aborting due to session status check failure")
                    return
        
        try:
            # First check if there are any tasks available
            logger.info("Checking for available tasks...")
            task_master = TaskMasterInterface()
            next_task = task_master.get_next_task()
            
            if not next_task:
                logger.info("No pending tasks found in Task Master. Nothing to process.")
                logger.info("Use 'python claude_orchestrator.py add \"task description\"' to add tasks")
                logger.info("Or 'python claude_orchestrator.py parse <file>' to parse a PRD")
                return
            
            logger.info(f"Found available task: {next_task.get('id', 'Unknown')} - {next_task.get('title', 'Unknown')}")
            
            # Get initial task plan from Opus to know how many tasks we'll have
            if self.use_progress_display:
                print("🔍 Opus Manager analyzing all tasks...")
            else:
                logger.info("Opus Manager analyzing all tasks...")
                
            tasks = self.manager.analyze_and_plan()
            
            if not tasks:
                logger.warning("No tasks to process after analysis")
                return
            
            # Initialize workers based on task count
            self.initialize(task_count=len(tasks))
            self.running = True
            
            # Initialize progress display
            if self.use_progress_display:
                self.progress = ProgressDisplay(total_tasks=len(tasks))
                self.progress.log_message(f"Opus Manager prepared {len(tasks)} tasks for processing", "INFO")
            else:
                logger.info(f"Opus Manager prepared {len(tasks)} tasks for processing")
            
            # Start worker threads
            worker_futures = []
            for worker in self.workers:
                future = self.executor.submit(self.worker_loop, worker)
                worker_futures.append(future)
            
            # Start review threads
            review_futures = []
            num_reviewers = max(2, len(self.workers) // 2)  # Half the workers, minimum 2
            for i in range(num_reviewers):
                future = self.review_executor.submit(self.review_loop)
                review_futures.append(future)
                if self.use_progress_display:
                    self.progress.log_message(f"Started Opus reviewer thread {i+1}", "INFO")
                else:
                    logger.info(f"Started Opus reviewer thread {i+1}")
            
            # Delegate tasks
            for task in tasks:
                # Check dependencies
                deps_completed = all(
                    dep in self.manager.completed_tasks 
                    for dep in task.dependencies
                )
                
                if deps_completed:
                    self.manager.delegate_task(task)
                else:
                    logger.info(f"Task {task.task_id} waiting for dependencies: {task.dependencies}")
            
            # Monitor progress
            monitor_interval = self.config.progress_interval
            last_monitor = datetime.now()
            last_progress_update = time.time()
            
            while True:
                # Update progress display
                if self.use_progress_display and self.progress:
                    current_time = time.time()
                    if current_time - last_progress_update > 0.1:  # Update every 100ms
                        active_count = len(self.manager.active_tasks)
                        if active_count > 0:
                            # Show current active tasks
                            active_titles = [f"W{task.assigned_worker}: {task.title[:20]}" 
                                           for task in self.manager.active_tasks.values()]
                            status = " | ".join(active_titles[:2])  # Show up to 2 active tasks
                            if active_count > 2:
                                status += f" +{active_count - 2} more"
                        else:
                            status = "Waiting for tasks..."
                        self.progress.update(status)
                        last_progress_update = current_time
                
                # Check if all tasks are done
                all_done = (
                    self.manager.task_queue.empty() and
                    len(self.manager.active_tasks) == 0 and
                    len(tasks) == len(self.manager.completed_tasks) + len(self.manager.failed_tasks)
                )
                
                if all_done:
                    if self.use_progress_display and self.progress:
                        self.progress.finish()
                    else:
                        logger.info("All tasks completed!")
                    break
                
                # Periodic monitoring
                if (datetime.now() - last_monitor).seconds >= monitor_interval:
                    if not self.use_progress_display:
                        self.manager.monitor_progress()
                    last_monitor = datetime.now()
                    
                    # Check for newly available tasks (dependencies satisfied)
                    for task in tasks:
                        if (task.task_id not in self.manager.completed_tasks and
                            task.task_id not in self.manager.failed_tasks and
                            task.task_id not in self.manager.active_tasks and
                            task.task_id not in [t.task_id for t in list(self.manager.task_queue.queue)]):
                            
                            deps_completed = all(
                                dep in self.manager.completed_tasks 
                                for dep in task.dependencies
                            )
                            
                            if deps_completed:
                                logger.info(f"Dependencies satisfied for task {task.task_id}, delegating...")
                                self.manager.delegate_task(task)
                
                # Small sleep to prevent busy waiting
                time.sleep(0.1)
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        finally:
            # Shutdown
            self.running = False
            
            # Wait for all reviews to complete
            if self.use_progress_display and self.progress:
                self.progress.log_message("Waiting for reviews to complete...", "INFO")
            else:
                logger.info("Waiting for reviews to complete...")
            
            # Shutdown executors
            self.executor.shutdown(wait=True)
            self.review_executor.shutdown(wait=True)
            
            # Final report
            self._generate_final_report()
    
    def _generate_final_report(self):
        """Generate final execution report"""
        logger.info("\n" + "="*50)
        logger.info("FINAL EXECUTION REPORT")
        logger.info("="*50)
        
        total_tasks = (
            len(self.manager.completed_tasks) + 
            len(self.manager.failed_tasks)
        )
        
        logger.info(f"Total tasks processed: {total_tasks}")
        logger.info(f"Successful: {len(self.manager.completed_tasks)}")
        logger.info(f"Failed: {len(self.manager.failed_tasks)}")
        
        # Calculate elapsed time
        if hasattr(self, 'start_time'):
            elapsed = time.time() - self.start_time
            elapsed_str = self._format_elapsed_time(elapsed)
        else:
            elapsed_str = "Unknown"
        
        # Send Slack notification for all tasks complete
        if self.config.notify_on_all_complete and total_tasks > 0:
            self.slack_notifier.send_all_complete(
                total_tasks,
                len(self.manager.completed_tasks),
                len(self.manager.failed_tasks),
                elapsed_str
            )
        
        # Report usage statistics
        if self.workers:
            logger.info("\nWorker Usage Statistics:")
            total_tokens = 0
            for worker in self.workers:
                logger.info(f"  Worker {worker.worker_id}:")
                logger.info(f"    Tasks completed: {worker.tasks_completed}")
                logger.info(f"    Tokens used: {worker.session_tokens_used:,}")
                total_tokens += worker.session_tokens_used
                
                if worker.worker_id in self.workers_at_limit:
                    logger.info(f"    ⚠️ Reached usage limit")
                    
            if total_tokens > 0:
                logger.info(f"\nTotal tokens used across all workers: {total_tokens:,}")
        
        if self.manager.completed_tasks:
            logger.info("\nCompleted tasks:")
            for task_id, task in self.manager.completed_tasks.items():
                logger.info(f"  ✓ {task_id}: {task.title}")
        
        if self.manager.failed_tasks:
            logger.info("\nFailed tasks:")
            for task_id, task in self.manager.failed_tasks.items():
                logger.info(f"  ✗ {task_id}: {task.title}")
                if task.error:
                    logger.info(f"    Error: {task.error}")
        
        # Summary of Opus reviews
        if self.config.enable_opus_review:
            logger.info("\n" + "="*50)
            logger.info("OPUS REVIEW SUMMARY")
            logger.info("="*50)
            
            # Count tasks by review status
            tasks_passed_review = 0
            tasks_need_improvement = 0
            total_follow_ups = 0
            
            for task_id, task in self.manager.completed_tasks.items():
                if hasattr(task, 'status_message'):
                    if "No issues found" in task.status_message:
                        tasks_passed_review += 1
                    elif "improvements needed" in task.status_message:
                        tasks_need_improvement += 1
                        # Extract follow-up count from message
                        import re
                        match = re.search(r'(\d+) improvements needed', task.status_message)
                        if match:
                            total_follow_ups += int(match.group(1))
            
            logger.info(f"Tasks passed review: {tasks_passed_review}")
            logger.info(f"Tasks needing improvement: {tasks_need_improvement}")
            
            if total_follow_ups > 0:
                logger.info(f"\n🔧 Total Follow-up Tasks Created: {total_follow_ups}")
                logger.info("Run 'python claude_orchestrator.py run' again to process the improvements")
            
            # Send summary to Slack if configured
            if self.slack_notifier.webhook_url and self.manager.completed_tasks:
                summary = f"Completed {len(self.manager.completed_tasks)} tasks. "
                summary += f"{tasks_passed_review} passed review, {tasks_need_improvement} need improvements."
                
                task_results = []
                for task_id, task in self.manager.completed_tasks.items():
                    task_results.append({
                        'status': 'completed',
                        'title': task.title,
                        'summary': task.status_message or "No review status"
                    })
                
                elapsed_time = elapsed_str if 'elapsed_str' in locals() else "Unknown"
                self.slack_notifier.send_opus_review(summary, task_results, elapsed_time, total_follow_ups)
        
        # Auto-commit changes if configured and git is available
        if self.config.git_auto_commit:
            self._auto_commit_changes()
    
    def _auto_commit_changes(self):
        """Auto-commit changes to git if repository exists"""
        try:
            # Check if we're in a git repository
            git_check = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True
            )
            
            if git_check.returncode != 0:
                logger.info("Not in a git repository, skipping auto-commit")
                return
            
            # Check if there are changes to commit
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True
            )
            
            if not status_result.stdout.strip():
                logger.info("No changes to commit")
                return
            
            logger.info("\n" + "="*50)
            logger.info("AUTO-COMMITTING CHANGES")
            logger.info("="*50)
            
            # Add all changes
            add_result = subprocess.run(
                ["git", "add", "-A"],
                capture_output=True,
                text=True
            )
            
            if add_result.returncode != 0:
                logger.error(f"Failed to stage changes: {add_result.stderr}")
                return
            
            # Generate commit message
            completed_count = len(self.manager.completed_tasks)
            failed_count = len(self.manager.failed_tasks)
            
            commit_message = f"{self.config.git_commit_prefix}\n\n"
            commit_message += f"Completed {completed_count} tasks, {failed_count} failed\n\n"
            
            if self.manager.completed_tasks:
                commit_message += "Completed tasks:\n"
                for task_id, task in self.manager.completed_tasks.items():
                    commit_message += f"- ✅ {task.title}\n"
            
            if self.manager.failed_tasks:
                commit_message += "\nFailed tasks:\n"
                for task_id, task in self.manager.failed_tasks.items():
                    commit_message += f"- ❌ {task.title}\n"
            
            # Commit changes
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True,
                text=True
            )
            
            if commit_result.returncode == 0:
                # Get commit hash
                hash_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True
                )
                commit_hash = hash_result.stdout.strip()[:7] if hash_result.returncode == 0 else "unknown"
                
                logger.info(f"✅ Successfully committed changes: {commit_hash}")
                logger.info(f"   Message: {self.config.git_commit_prefix}")
                
                # Also send to Slack if configured
                if self.slack_notifier.webhook_url:
                    self.slack_notifier.send_notification(
                        f"Auto-committed changes: {commit_hash}\n{completed_count} completed, {failed_count} failed",
                        ":white_check_mark:"
                    )
            else:
                logger.error(f"Failed to commit: {commit_result.stderr}")
                
        except Exception as e:
            logger.error(f"Error during auto-commit: {e}")
    
    def _opus_review_work(self) -> Optional[str]:
        """Use Opus to review all completed work"""
        try:
            # Prepare review data
            completed_tasks = []
            for task_id, task in self.manager.completed_tasks.items():
                completed_tasks.append({
                    'id': task_id,
                    'title': task.title,
                    'description': task.description,
                    'result': task.result[:500] if task.result else "No output"  # Limit output length
                })
            
            # Create review prompt
            prompt = f"""You are the Opus Manager reviewing the work completed by Sonnet workers.

Please review the following completed tasks and provide:
1. Overall quality assessment
2. Any potential issues or concerns
3. Suggestions for improvements
4. Confirmation that all tasks meet the requirements

Completed Tasks:
{json.dumps(completed_tasks, indent=2)}

Additionally, review the current state of the codebase:
- Check for consistency across changes
- Verify that all changes follow best practices
- Ensure no breaking changes were introduced
- Confirm that the implementation matches the original requirements

IMPORTANT: Based on your review, if there are any improvements needed or follow-up work required:
1. Use the task-master CLI to create new tasks for these improvements
2. Be specific about what needs to be done
3. Set appropriate priorities based on importance
4. Add helpful context in the task descriptions

Example commands you can use:
- task-master add-task --prompt="Add unit tests for the new authentication module" --priority=high
- task-master add-task --prompt="Refactor error handling to use consistent patterns" --priority=medium
- task-master add-task --prompt="Add documentation for the API endpoints" --priority=low

First provide your review summary, then create any necessary follow-up tasks."""

            # Execute Opus review
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name
            
            cmd = [
                self.config.claude_command,
                "-p", f"@{prompt_file}",
                "--model", self.config.manager_model
            ]
            
            # Add flags
            if self.config.claude_flags.get("verbose"):
                cmd.append("--verbose")
            if self.config.claude_flags.get("dangerously_skip_permissions"):
                cmd.append("--dangerously-skip-permissions")
            
            # Set up environment
            env = os.environ.copy()
            for key, value in self.config.claude_environment.items():
                if value is not None:
                    env[key] = str(value)
            
            logger.info("Opus is reviewing completed work...")
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd(),
                env=env
            )
            
            # Show loading indicator while waiting
            spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            spinner_index = 0
            start_time = time.time()
            
            while process.poll() is None:
                elapsed = time.time() - start_time
                spinner = spinner_frames[spinner_index % len(spinner_frames)]
                sys.stdout.write(f"\r{spinner} Opus is analyzing the completed work... ({elapsed:.0f}s)")
                sys.stdout.flush()
                spinner_index += 1
                
                # Check timeout
                if elapsed > self.config.manager_timeout:
                    process.terminate()
                    sys.stdout.write("\r❌ Opus review timed out" + " " * 30 + "\n")
                    sys.stdout.flush()
                    logger.error("Opus review timed out")
                    return None
                
                time.sleep(0.1)
            
            # Clear the loading indicator
            sys.stdout.write("\r" + " " * 60 + "\r")
            sys.stdout.flush()
            
            # Get the results
            stdout, stderr = process.communicate()
            result_code = process.returncode
            
            # Clean up
            os.unlink(prompt_file)
            
            if result_code == 0:
                logger.info("✅ Opus review completed successfully")
                
                # Parse the output to count any follow-up tasks created
                follow_up_count = self._count_follow_up_tasks(stdout)
                if follow_up_count > 0:
                    logger.info(f"📝 Created {follow_up_count} follow-up tasks for improvements")
                
                return stdout.strip()
            else:
                logger.error(f"Opus review failed: {stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error during Opus review: {e}")
            return None
    
    def _opus_review_single_task(self, task: WorkerTask) -> Dict[str, Any]:
        """Use Opus to review a single completed task"""
        try:
            # Create review prompt for single task
            prompt = f"""You are the Opus Manager reviewing a single task completed by a Sonnet worker.

Task Information:
- ID: {task.task_id}
- Title: {task.title}
- Description: {task.description}
- Status: {task.status.value}
- Result: {task.result[:1000] if task.result else "No output"}

Please review this task and:
1. Verify the implementation meets requirements
2. Check code quality and best practices
3. Identify any issues or improvements needed

If improvements are needed:
- Use task-master CLI to create specific follow-up tasks
- Set appropriate priorities
- Be clear about what needs to be fixed

Example commands:
- task-master add-task --prompt="Fix error handling in {task.title}" --priority=high
- task-master add-task --prompt="Add tests for {task.title}" --priority=medium

Provide a brief review summary and create any necessary follow-up tasks."""

            # Execute Opus review
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name
            
            cmd = [
                self.config.claude_command,
                "-p", f"@{prompt_file}",
                "--model", self.config.manager_model
            ]
            
            # Add flags
            if self.config.claude_flags.get("verbose"):
                cmd.append("--verbose")
            if self.config.claude_flags.get("dangerously_skip_permissions"):
                cmd.append("--dangerously-skip-permissions")
            
            # Set up environment
            env = os.environ.copy()
            for key, value in self.config.claude_environment.items():
                if value is not None:
                    env[key] = str(value)
            
            # Execute review
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.working_dir,
                timeout=60,  # Shorter timeout for single task review
                env=env
            )
            
            # Clean up
            os.unlink(prompt_file)
            
            if result.returncode == 0:
                review_output = result.stdout.strip()
                follow_up_count = self._count_follow_up_tasks(review_output)
                
                return {
                    'success': True,
                    'review': review_output,
                    'follow_up_count': follow_up_count,
                    'needs_improvement': follow_up_count > 0
                }
            else:
                logger.error(f"Opus review failed for task {task.task_id}: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr,
                    'needs_improvement': False
                }
                
        except Exception as e:
            logger.error(f"Error during Opus review of task {task.task_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'needs_improvement': False
            }
    
    def _count_follow_up_tasks(self, opus_output: str) -> int:
        """Count how many follow-up tasks were created from the Opus output"""
        count = 0
        
        # Look for patterns that indicate task creation
        patterns = [
            r"Created task \d+",
            r"Task created with ID: \d+",
            r"Added task:",
            r"✅ Task added successfully",
            r"Successfully created task"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, opus_output, re.IGNORECASE)
            count += len(matches)
        
        # Also check for task-master command executions
        task_master_commands = re.findall(r"task-master add-task", opus_output)
        if task_master_commands:
            # Estimate based on commands (may not all succeed)
            count = max(count, len(task_master_commands))
        
        return count


def opus_add_task(description: str, config) -> bool:
    """Use Opus to intelligently add a task to Task Master"""
    logger.info(f"Using Opus to add task: {description}")
    
    # Create progress display
    progress = ProgressDisplay(total_tasks=1)
    progress.update("🤖 Starting Opus to analyze and add task...")
    
    try:
        # Escape the description to handle newlines and quotes properly
        escaped_description = description.replace('\n', '\\n').replace('"', '\\"')
        
        # Create prompt for Opus to analyze and create task
        prompt = f"""You are a project manager using Task Master. 
A user wants to add this task: "{description}"

CRITICAL ANALYSIS REQUIRED:
1. Analyze the task to identify INDEPENDENT components that can be worked on in PARALLEL
2. Consider the scope and impact area of each component
3. Create SEPARATE tasks for work that affects different files, modules, or features

GUIDELINES FOR TASK SEPARATION:
- If the task involves multiple features → Create separate tasks for each feature
- If the task affects different files/modules → Create separate tasks for each module
- If parts can be developed independently → Create separate parallel tasks
- Only create dependencies when one task MUST complete before another can start

EXAMPLE:
Instead of: "Implement authentication system"
Create multiple tasks:
- "Create user model and database schema"
- "Implement JWT token generation"
- "Create login API endpoint"
- "Create registration API endpoint"
- "Add authentication middleware"
- "Create user profile endpoints"

These can mostly run in parallel, maximizing efficiency!

Use these commands:
- task-master add-task --prompt="[specific component]" --priority=[high/medium/low]
- For truly complex tasks: task-master expand --id=<id> --research

IMPORTANT: 
- Escape newlines in prompts with \\n
- Create multiple focused tasks rather than one large task
- Think about what can be done simultaneously by different workers"""

        # Execute Opus command
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name
        
        cmd = [
            config.claude_command,
            "-p", f"@{prompt_file}",
            "--model", config.manager_model
        ]
        
        # Add additional flags from config
        if config.claude_flags.get("verbose"):
            cmd.append("--verbose")
        if config.claude_flags.get("dangerously_skip_permissions"):
            cmd.append("--dangerously-skip-permissions")
        
        # Set up environment variables
        env = os.environ.copy()
        for key, value in config.claude_environment.items():
            if value is not None:
                env[key] = str(value)
        
        progress.update("🔄 Opus is analyzing the task request...")
        logger.info("Executing Opus to add task...")
        
        # Run subprocess with real-time progress updates
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=config.default_working_dir,
            env=env
        )
        
        # Show progress while waiting
        start_time = time.time()
        while process.poll() is None:
            elapsed = time.time() - start_time
            progress.update(f"⏳ Opus is working... ({elapsed:.0f}s)", force=True)
            time.sleep(0.5)
            
            # Check timeout
            if elapsed > config.manager_timeout:
                process.terminate()
                progress.update("❌ Opus task creation timed out", force=True)
                logger.error("Opus task creation timed out")
                return False
        
        stdout, stderr = process.communicate()
        result_code = process.returncode
        
        # Clean up temp file
        os.unlink(prompt_file)
        
        if result_code == 0:
            progress.completed = 1
            progress.update("✅ Task successfully added to Task Master!", force=True)
            logger.info("Opus successfully added task to Task Master")
            logger.debug(f"Opus output: {stdout}")
            print("")  # New line after progress
            return True
        else:
            progress.failed = 1
            progress.update("❌ Failed to add task", force=True)
            logger.error(f"Opus failed to add task: {stderr}")
            print("")  # New line after progress
            return False
            
    except Exception as e:
        progress.failed = 1
        progress.update(f"❌ Error: {str(e)}", force=True)
        logger.error(f"Error using Opus to add task: {e}")
        print("")  # New line after progress
        return False


def opus_parse_file(file_path: str, config) -> bool:
    """Use Opus to parse a PRD or prompt file and add tasks to Task Master"""
    logger.info(f"Using Opus to parse file: {file_path}")
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        # Read file contents
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.read()
        
        # Create prompt for Opus
        prompt = f"""You are a project manager using Task Master.
I have a document that needs to be parsed and converted into tasks.

File: {file_path}
Contents:
---
{file_contents}
---

CRITICAL: MAXIMIZE PARALLEL EXECUTION
When analyzing this document:
1. Identify all INDEPENDENT work items that can be done in PARALLEL
2. Create SEPARATE tasks for each component that can be worked on simultaneously
3. Only add dependencies when absolutely necessary (one task MUST complete before another)

TASK SEPARATION STRATEGY:
- Different features/modules → Separate tasks
- Different files affected → Separate tasks  
- Frontend vs Backend → Separate tasks
- Database vs API → Separate tasks
- Documentation vs Code → Separate tasks

EXAMPLE BREAKDOWN:
"Build a user management system" should become:
- "Design and create user database schema"
- "Implement user model and ORM mappings"
- "Create user registration API endpoint"
- "Create user login API endpoint"
- "Create user profile API endpoints"
- "Build frontend registration form"
- "Build frontend login form"
- "Add user authentication middleware"
- "Write API documentation"
- "Create unit tests for user endpoints"

Most of these can run in parallel!

COMMANDS TO USE:
1. If it's a PRD format: task-master parse-prd "{file_path}"
2. For individual tasks: task-master add-task --prompt="[specific component]" --priority=[high/medium/low]
3. Only use expand for truly complex single components

Remember: More parallel tasks = faster completion!"""

        # Execute Opus command
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name
        
        cmd = [
            config.claude_command,
            "-p", f"@{prompt_file}",
            "--model", config.manager_model
        ]
        
        # Add additional flags from config
        if config.claude_flags.get("verbose"):
            cmd.append("--verbose")
        if config.claude_flags.get("dangerously_skip_permissions"):
            cmd.append("--dangerously-skip-permissions")
        
        # Set up environment variables
        env = os.environ.copy()
        for key, value in config.claude_environment.items():
            if value is not None:
                env[key] = str(value)
        
        logger.info("Executing Opus to parse file and create tasks...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            timeout=config.manager_timeout,
            env=env
        )
        
        # Clean up temp file
        os.unlink(prompt_file)
        
        if result.returncode == 0:
            logger.info("Opus successfully parsed file and added tasks")
            logger.debug(f"Opus output: {result.stdout}")
            return True
        else:
            logger.error(f"Opus failed to parse file: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error using Opus to parse file: {e}")
        return False


def check_claude_session_status():
    """Check Claude session status and usage"""
    print("\n🔍 Checking Claude session status...")
    
    try:
        # Try to get session info with a minimal prompt
        result = subprocess.run(
            ["claude", "-p", "Return only: OK"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Look for usage information in output
            output = result.stdout + (result.stderr or "")
            
            # Check for common usage indicators
            if "limit" in output.lower() or "usage" in output.lower():
                print(f"⚠️ Usage information detected: {output}")
                
            # Try to extract percentage if available
            percent_match = re.search(r'(\d+)%', output)
            if percent_match:
                usage_percent = int(percent_match.group(1))
                if usage_percent >= 90:
                    print(f"⚠️ HIGH USAGE: {usage_percent}% of session limit used")
                elif usage_percent >= 80:
                    print(f"⚠️ Warning: {usage_percent}% of session limit used")
                else:
                    print(f"✓ Session usage: {usage_percent}%")
            else:
                print("✓ Session appears to be active (no usage data available)")
                
            return True
        else:
            print(f"✗ Session check failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error checking session: {e}")
        return False


def check_claude_setup():
    """Check if Claude CLI is properly set up"""
    print("Checking Claude CLI setup...")
    
    # Check if claude command exists
    try:
        result = subprocess.run(["which", "claude"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Claude CLI found at: {result.stdout.strip()}")
        else:
            print("✗ Claude CLI not found in PATH")
            return False
    except Exception as e:
        print(f"✗ Error checking Claude CLI: {e}")
        return False
    
    # Check Claude version
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Claude CLI version: {result.stdout.strip()}")
        else:
            print(f"✗ Claude CLI error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error running Claude CLI: {e}")
        return False
    
    # Check API key
    api_key_env = os.environ.get("ANTHROPIC_API_KEY")
    api_key_file = os.path.expanduser("~/.anthropic/claude.ai/api_key")
    
    if api_key_env:
        print(f"✓ ANTHROPIC_API_KEY found in environment (starts with: {api_key_env[:10]}...)")
    elif os.path.exists(api_key_file):
        print(f"✓ API key file found at: {api_key_file}")
    else:
        print("✗ No API key found. Please set ANTHROPIC_API_KEY or run 'claude login'")
        return False
    
    # Test Claude with simple prompt
    print("\nTesting Claude CLI with simple prompt...")
    try:
        result = subprocess.run(
            ["claude", "-p", "Say 'Hello' and nothing else"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✓ Claude responded: {result.stdout.strip()}")
            
            # Also check session status
            check_claude_session_status()
            
            return True
        else:
            print(f"✗ Claude test failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Claude test timed out")
        return False
    except Exception as e:
        print(f"✗ Error testing Claude: {e}")
        return False


def init_orchestrator(config) -> bool:
    """Initialize orchestrator by setting up configuration and dependencies"""
    print("🚀 Initializing Claude Orchestrator...\n")
    
    # Define required dependencies
    REQUIRED_DEPENDENCIES = [
        "jsonschema>=4.0.0",  # For configuration validation
        "PyYAML>=6.0",  # For YAML support
        "rich>=10.0.0",  # Enhanced terminal output (optional)
        "pydantic>=2.0.0",  # Enhanced config management (optional)
    ]
    
    # Check if config file exists
    config_file = "orchestrator_config.json"
    if not os.path.exists(config_file):
        print(f"📝 Creating default configuration file: {config_file}")
        default_config = {
            "models": {
                "manager": {
                    "model": "opus",
                    "description": "Opus model for planning and task management"
                },
                "worker": {
                    "model": "sonnet",
                    "description": "Sonnet model for code implementation"
                }
            },
            "execution": {
                "max_workers": 3,
                "worker_timeout": 300,
                "manager_timeout": 180,
                "task_queue_timeout": 1.0,
                "max_turns": 10,
                "default_working_dir": os.getcwd(),
                "bash_default_timeout_ms": 120000,
                "bash_max_timeout_ms": 600000,
                "bash_max_output_length": 30000
            },
            "monitoring": {
                "progress_interval": 10,
                "verbose_logging": False,
                "show_progress_bar": True,
                "enable_opus_review": True
            },
            "claude_cli": {
                "command": "claude",
                "flags": {
                    "verbose": False,
                    "dangerously_skip_permissions": False
                },
                "settings": {},
                "environment": {}
            },
            "notifications": {
                "slack_webhook_url": "",
                "notify_on_task_complete": True,
                "notify_on_task_failed": True,
                "notify_on_all_complete": True
            },
            "git": {
                "auto_commit": False,
                "commit_message_prefix": "🤖 Auto-commit by Claude Orchestrator"
            }
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"✅ Created {config_file}")
        except Exception as e:
            print(f"❌ Failed to create config file: {e}")
            return False
    else:
        print(f"✅ Configuration file exists: {config_file}")
    
    # Check Claude CLI setup
    print("\n🔍 Checking Claude CLI setup...")
    claude_setup_ok = check_claude_setup()
    if not claude_setup_ok:
        print("\n⚠️  Claude CLI needs configuration. Please set ANTHROPIC_API_KEY or run 'claude login'")
        print("   Continuing with dependency installation...")
    
    # Check and install Python dependencies
    print("\n📦 Checking and installing dependencies...")
    
    # Check which dependencies are missing
    missing_deps = []
    installed_deps = []
    
    # Check each dependency
    dependency_checks = {
        "jsonschema": ("jsonschema", "JSON Schema"),
        "PyYAML": ("yaml", "PyYAML"),
        "rich": ("rich", "Rich (optional)"),
        "pydantic": ("pydantic", "Pydantic (optional)")
    }
    
    for package, (import_name, display_name) in dependency_checks.items():
        try:
            __import__(import_name)
            installed_deps.append(display_name)
        except ImportError:
            missing_deps.append(package)
    
    if installed_deps:
        print(f"✅ Already installed: {', '.join(installed_deps)}")
    
    # Install missing dependencies
    if missing_deps:
        print(f"📦 Installing missing dependencies: {', '.join(missing_deps)}")
        for dep in missing_deps:
            print(f"   Installing {dep}...")
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", dep],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"   ✅ {dep} installed successfully")
                else:
                    print(f"   ❌ Failed to install {dep}: {result.stderr.strip()}")
            except Exception as e:
                print(f"   ❌ Error installing {dep}: {e}")
    else:
        print("✅ All dependencies are already installed")
    
    # Create requirements.txt for reference
    print("\n📝 Creating requirements.txt for reference...")
    try:
        with open("requirements.txt", 'w') as f:
            f.write("# Claude Orchestrator Dependencies\n")
            f.write("# Generated by 'claude_orchestrator.py init'\n\n")
            for dep in REQUIRED_DEPENDENCIES:
                f.write(f"{dep}\n")
        print("✅ Created requirements.txt")
    except Exception as e:
        print(f"⚠️  Could not create requirements.txt: {e}")
    
    # Check and install Task Master AI (npm package)
    print("\n🔧 Checking Task Master AI...")
    
    # First check if npm is installed
    try:
        npm_check = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if npm_check.returncode != 0:
            print("❌ npm not found. Please install Node.js and npm first")
            print("   Visit: https://nodejs.org/")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ npm not found. Please install Node.js and npm first")
        print("   Visit: https://nodejs.org/")
        return False
    
    # Check if Task Master is installed
    try:
        result = subprocess.run(
            ["task-master", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Task Master AI already installed: {result.stdout.strip()}")
        else:
            raise FileNotFoundError("Task Master not found")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Task Master AI not installed")
        print("📦 Installing Task Master AI globally...")
        try:
            # Install task-master-ai globally
            install_result = subprocess.run(
                ["npm", "install", "-g", "task-master-ai"],
                capture_output=True,
                text=True
            )
            if install_result.returncode == 0:
                print("✅ Task Master AI installed successfully")
                # Verify installation
                verify_result = subprocess.run(
                    ["task-master", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if verify_result.returncode == 0:
                    print(f"   Version: {verify_result.stdout.strip()}")
                else:
                    print("⚠️  Task Master installed but command not found in PATH")
                    print("   You may need to restart your terminal")
            else:
                print(f"❌ Failed to install Task Master AI: {install_result.stderr}")
                print("   Please run manually: npm install -g task-master-ai")
                return False
        except Exception as e:
            print(f"❌ Error installing Task Master AI: {e}")
            print("   Please run manually: npm install -g task-master-ai")
            return False
    
    # Create example files if they don't exist
    if not os.path.exists(".env.example"):
        print("\n📝 Creating .env.example...")
        with open(".env.example", 'w') as f:
            f.write("# Claude Orchestrator Environment Variables\n")
            f.write("ANTHROPIC_API_KEY=your_anthropic_api_key_here\n")
            f.write("PERPLEXITY_API_KEY=your_perplexity_api_key_here  # Optional\n")
            f.write("SLACK_WEBHOOK_URL=your_slack_webhook_url_here   # Optional\n")
        print("✅ Created .env.example")
    
    # Create co shortcut if it doesn't exist
    if not os.path.exists("co"):
        print("\n🔧 Creating 'co' shortcut...")
        co_content = '''#!/usr/bin/env python3
"""
Claude Orchestrator shortcut command
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claude_orchestrator import main

if __name__ == "__main__":
    main()'''
        
        with open("co", 'w') as f:
            f.write(co_content)
        
        # Make it executable
        import stat
        st = os.stat('co')
        os.chmod('co', st.st_mode | stat.S_IEXEC)
        
        print("✅ Created 'co' shortcut command")
        print("   You can now use './co' instead of 'python claude_orchestrator.py'")
    
    print("\n✅ Orchestrator initialization complete!")
    print("\nNext steps:")
    print("1. Review and customize orchestrator_config.json")
    if not claude_setup_ok:
        print("2. Set up your .env file with API keys or run 'claude login'")
    print("3. Run: python claude_orchestrator.py add \"your first task\"")
    print("4. Run: python claude_orchestrator.py run")
    
    return True


def main():
    """Main entry point"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(
        description="Claude Orchestrator - Opus Manager with Sonnet Workers\n\n"
                    "An intelligent task orchestration system that uses Claude Opus as a manager "
                    "to analyze and delegate tasks to multiple Claude Sonnet workers for parallel execution.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a single task
  python claude_orchestrator.py add "Implement user authentication"
  
  # Add task with verbose output
  python claude_orchestrator.py --verbose add "Debug eslint issues" -d ./project
  
  # Parse a PRD file
  python claude_orchestrator.py parse .taskmaster/docs/prd.txt
  
  # Run orchestrator with 5 workers
  python claude_orchestrator.py run --workers 5
  
  # Check session status
  python claude_orchestrator.py status
  
  # Enable debug logging
  python claude_orchestrator.py --debug run

For more information, see README_orchestrator.md
        """
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(
        dest='command', 
        help='Available commands',
        description='Use "python claude_orchestrator.py <command> --help" for command-specific help'
    )
    
    # Add task command
    add_parser = subparsers.add_parser(
        'add', 
        help='Add a new task using Opus AI analysis',
        description='Uses Claude Opus to intelligently analyze a task description and add it to Task Master. '
                    'Complex tasks will be automatically broken down into subtasks.'
    )
    add_parser.add_argument(
        'description', 
        help='Task description (e.g., "Implement OAuth2 authentication")'
    )
    add_parser.add_argument(
        "--working-dir", "-d",
        type=str,
        help="Working directory for the project (default: current directory)"
    )
    
    # Parse file command
    parse_parser = subparsers.add_parser(
        'parse', 
        help='Parse PRD or prompt file using Opus AI',
        description='Uses Claude Opus to parse a Product Requirements Document (PRD) or any text file '
                    'containing project requirements. Automatically creates appropriate tasks in Task Master.'
    )
    parse_parser.add_argument(
        'file_path', 
        help='Path to PRD or requirements file (supports .txt, .md files)'
    )
    parse_parser.add_argument(
        "--working-dir", "-d",
        type=str,
        help="Working directory for the project (default: current directory)"
    )
    
    # Run command (default)
    run_parser = subparsers.add_parser(
        'run', 
        help='Run the orchestrator to process tasks',
        description='Starts the orchestration system with Opus as manager and multiple Sonnet workers. '
                    'Tasks are fetched from Task Master, analyzed for dependencies, and processed in parallel.'
    )
    run_parser.add_argument(
        "--workers", 
        type=int, 
        default=3, 
        help="Number of parallel Sonnet workers (default: 3, recommended: 2-5)"
    )
    run_parser.add_argument(
        "--working-dir", "-d",
        type=str,
        help="Working directory for the project (default: current directory)"
    )
    
    # Check command
    check_parser = subparsers.add_parser(
        'check',
        help='Check Claude CLI setup and authentication',
        description='Verifies that Claude CLI is properly installed, authenticated, and configured. '
                    'Runs diagnostic tests to identify common setup issues.'
    )
    
    # Session status command
    status_parser = subparsers.add_parser(
        'status',
        help='Check Claude session usage status',
        description='Checks the current Claude session usage and warns if approaching limits.'
    )
    
    # Init command
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize orchestrator with configuration and dependencies',
        description='Sets up the orchestrator environment by creating configuration files, '
                    'installing dependencies, and verifying Claude CLI setup.'
    )
    
    # Global arguments
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging for detailed execution information"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true", 
        help="Enable verbose output (disables progress bar)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    # Add config file argument
    parser.add_argument(
        "--config",
        type=str,
        default="orchestrator_config.json",
        help="Path to configuration file (default: orchestrator_config.json)"
    )
    
    args = parser.parse_args()
    
    # Load configuration using the new system
    config = create_config(args.config)
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle verbose flag - override config setting
    if args.verbose:
        if hasattr(config, 'config_manager'):
            # Enhanced config system
            config.config_manager.config["monitoring"]["verbose_logging"] = True
            config.config_manager.config["monitoring"]["show_progress_bar"] = False
        else:
            # Legacy config system
            config.config["monitoring"]["verbose_logging"] = True
            config.config["monitoring"]["show_progress_bar"] = False
    
    # Handle commands
    if args.command == 'add':
        # Change to working directory if specified
        working_dir = getattr(args, 'working_dir', None)
        if working_dir:
            original_dir = os.getcwd()
            os.chdir(working_dir)
            logger.info(f"Changed to working directory: {working_dir}")
        
        try:
            # Use Opus to add task
            success = opus_add_task(args.description, config)
            sys.exit(0 if success else 1)
        finally:
            if working_dir:
                os.chdir(original_dir)
                
    elif args.command == 'parse':
        # Change to working directory if specified
        working_dir = getattr(args, 'working_dir', None)
        if working_dir:
            original_dir = os.getcwd()
            os.chdir(working_dir)
            logger.info(f"Changed to working directory: {working_dir}")
        
        try:
            # Use Opus to parse file
            success = opus_parse_file(args.file_path, config)
            sys.exit(0 if success else 1)
        finally:
            if working_dir:
                os.chdir(original_dir)
                
    elif args.command == 'check':
        # Check Claude CLI setup
        success = check_claude_setup()
        sys.exit(0 if success else 1)
    elif args.command == 'status':
        # Check session status only
        success = check_claude_session_status()
        sys.exit(0 if success else 1)
    elif args.command == 'init':
        # Initialize orchestrator
        success = init_orchestrator(config)
        sys.exit(0 if success else 1)
    elif args.command == 'run' or args.command is None:
        # Default behavior - run orchestrator
        # Override config with command line args if provided
        if hasattr(args, 'workers') and args.workers:
            if hasattr(config, 'config_manager'):
                # Enhanced config system
                config.config_manager.config["execution"]["max_workers"] = args.workers
            else:
                # Legacy config system
                config.config["execution"]["max_workers"] = args.workers
        
        # Get working directory from args or config
        working_dir = getattr(args, 'working_dir', None)
        if not working_dir:
            working_dir = config.default_working_dir
            if working_dir and working_dir != os.getcwd():
                logger.info(f"Using default working directory from config: {working_dir}")
        
        # Change to working directory to ensure Task Master operates there
        if working_dir:
            original_dir = os.getcwd()
            os.chdir(working_dir)
            logger.info(f"Changed to working directory: {working_dir}")
        
        try:
            orchestrator = ClaudeOrchestrator(config, working_dir)
            orchestrator.run()
        finally:
            # Restore original directory if changed
            if working_dir:
                os.chdir(original_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()