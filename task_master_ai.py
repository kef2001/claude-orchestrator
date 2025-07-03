"""
Task Master AI Features - Task expansion, research, and analysis
"""

import json
import logging
import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

from task_master import TaskManager, Task, Subtask

logger = logging.getLogger(__name__)


class TaskMasterAI:
    """AI-powered features for Task Master"""
    
    def __init__(self, task_manager: TaskManager, claude_command: str = "claude"):
        self.task_manager = task_manager
        self.claude_command = claude_command
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        
    def _create_ai_prompt(self, template: str, **kwargs) -> str:
        """Create a prompt from template with variables"""
        return template.format(**kwargs)
    
    def _execute_claude(self, prompt: str, model: str = "claude-3-5-sonnet-20241022") -> Dict[str, Any]:
        """Execute Claude CLI with the given prompt"""
        try:
            # Save prompt to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name
            
            # Construct command
            cmd = [
                self.claude_command,
                "-p", f"@{prompt_file}",
                "--model", model,
                "--output-format", "json"
            ]
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.task_manager.project_root
            )
            
            # Clean up
            os.unlink(prompt_file)
            
            if result.returncode == 0:
                try:
                    # Parse JSON output
                    return {
                        'success': True,
                        'response': json.loads(result.stdout)
                    }
                except json.JSONDecodeError:
                    # Fallback to text response
                    return {
                        'success': True,
                        'response': result.stdout
                    }
            else:
                return {
                    'success': False,
                    'error': result.stderr or "Command failed"
                }
                
        except Exception as e:
            logger.error(f"Error executing Claude: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def expand_task(self, task_id: str, num_subtasks: int = 5, use_research: bool = False) -> List[Subtask]:
        """Expand a task into subtasks using AI"""
        task = self.task_manager.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return []
        
        # Create expansion prompt
        prompt = f"""You are an expert project manager. Break down the following task into {num_subtasks} detailed subtasks.

Task ID: {task.id}
Title: {task.title}
Description: {task.description}
Details: {task.details or 'None provided'}
Priority: {task.priority}

Please create {num_subtasks} subtasks that:
1. Are specific and actionable
2. Follow a logical sequence
3. Cover all aspects of the main task
4. Include clear success criteria

Return your response as a JSON array with this structure:
[
  {{
    "title": "Subtask title",
    "description": "Detailed description",
    "details": "Implementation details and notes",
    "dependencies": [list of subtask numbers that must be completed first, if any]
  }}
]

Focus on technical implementation details and ensure each subtask is well-defined."""

        # Add research context if requested
        if use_research:
            research_prompt = f"Research context for task: {task.title}"
            research_result = self.perform_research(research_prompt, task_ids=[task.id])
            if research_result['success']:
                prompt += f"\n\nResearch Context:\n{research_result['research'][:2000]}"
        
        # Execute AI request
        result = self._execute_claude(prompt)
        
        if not result['success']:
            logger.error(f"Failed to expand task: {result['error']}")
            return []
        
        # Parse response
        subtasks_created = []
        try:
            if isinstance(result['response'], dict) and 'response' in result['response']:
                subtasks_data = json.loads(result['response']['response'])
            elif isinstance(result['response'], str):
                # Extract JSON from response
                import re
                json_match = re.search(r'\[.*\]', result['response'], re.DOTALL)
                if json_match:
                    subtasks_data = json.loads(json_match.group())
                else:
                    logger.error("No JSON found in response")
                    return []
            else:
                subtasks_data = result['response']
            
            # Create subtasks
            for idx, st_data in enumerate(subtasks_data):
                subtask = self.task_manager.add_subtask(
                    parent_id=str(task.id),
                    title=st_data.get('title', f'Subtask {idx+1}'),
                    description=st_data.get('description', ''),
                    dependencies=st_data.get('dependencies', [])
                )
                if subtask:
                    subtasks_created.append(subtask)
                    
        except Exception as e:
            logger.error(f"Error parsing subtasks: {e}")
            
        return subtasks_created
    
    def analyze_complexity(self, threshold: int = 5) -> Dict[str, Any]:
        """Analyze task complexity and recommend expansions"""
        tasks = self.task_manager.get_all_tasks()
        
        analysis = {
            'recommendations': [],
            'statistics': {
                'total_tasks': len(tasks),
                'tasks_with_subtasks': 0,
                'tasks_without_subtasks': 0,
                'average_subtasks': 0,
                'complex_tasks': []
            }
        }
        
        # Analyze each task
        total_subtasks = 0
        for task in tasks:
            if task.status in ['done', 'cancelled']:
                continue
                
            subtask_count = len(task.subtasks)
            if subtask_count > 0:
                analysis['statistics']['tasks_with_subtasks'] += 1
                total_subtasks += subtask_count
            else:
                analysis['statistics']['tasks_without_subtasks'] += 1
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity(task)
            
            if complexity_score >= threshold and subtask_count == 0:
                analysis['recommendations'].append({
                    'task_id': task.id,
                    'title': task.title,
                    'complexity_score': complexity_score,
                    'reason': 'High complexity task without subtasks',
                    'suggested_subtasks': min(complexity_score, 8)
                })
                analysis['statistics']['complex_tasks'].append(task.id)
        
        # Calculate average
        if analysis['statistics']['tasks_with_subtasks'] > 0:
            analysis['statistics']['average_subtasks'] = (
                total_subtasks / analysis['statistics']['tasks_with_subtasks']
            )
        
        # Save report
        report_file = self.task_manager.complexity_report_file
        with open(report_file, 'w') as f:
            json.dump(analysis, f, indent=2)
            
        return analysis
    
    def _calculate_complexity(self, task: Task) -> int:
        """Calculate complexity score for a task"""
        score = 0
        
        # Length of description
        if len(task.description) > 100:
            score += 2
        elif len(task.description) > 50:
            score += 1
        
        # Details provided
        if task.details:
            if len(task.details) > 200:
                score += 3
            elif len(task.details) > 100:
                score += 2
            else:
                score += 1
        
        # Dependencies
        score += len(task.dependencies)
        
        # Keywords indicating complexity
        complex_keywords = [
            'implement', 'create', 'design', 'build', 'develop',
            'integrate', 'system', 'architecture', 'multiple',
            'various', 'complex', 'comprehensive'
        ]
        
        text = f"{task.title} {task.description} {task.details or ''}".lower()
        for keyword in complex_keywords:
            if keyword in text:
                score += 1
        
        return score
    
    def perform_research(self, query: str, task_ids: Optional[List[str]] = None,
                        file_paths: Optional[List[str]] = None,
                        additional_context: Optional[str] = None) -> Dict[str, Any]:
        """Perform AI-powered research with project context"""
        
        # Build context
        context_parts = [f"Research Query: {query}"]
        
        # Add task context
        if task_ids:
            context_parts.append("\nRelated Tasks:")
            for task_id in task_ids:
                task = self.task_manager.get_task(task_id)
                if task:
                    context_parts.append(f"- Task {task.id}: {task.title}")
                    context_parts.append(f"  Description: {task.description}")
                    if task.details:
                        context_parts.append(f"  Details: {task.details}")
        
        # Add file context
        if file_paths:
            context_parts.append("\nRelevant Files:")
            for file_path in file_paths:
                path = Path(file_path)
                if path.exists():
                    context_parts.append(f"- {file_path}")
                    try:
                        # Read first 500 lines of file
                        with open(path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()[:500]
                            context_parts.append(f"  Content preview:\n{''.join(lines[:50])}")
                    except Exception as e:
                        context_parts.append(f"  (Could not read file: {e})")
        
        # Add additional context
        if additional_context:
            context_parts.append(f"\nAdditional Context:\n{additional_context}")
        
        # Create research prompt
        prompt = f"""You are a technical research assistant. Please provide comprehensive research and analysis for the following query.

{chr(10).join(context_parts)}

Provide a detailed response that includes:
1. Direct answer to the query
2. Technical implementation details
3. Best practices and recommendations
4. Potential challenges and solutions
5. Code examples where relevant

Focus on practical, actionable information that can be used for implementation."""

        # Execute research
        result = self._execute_claude(prompt, model="claude-3-5-sonnet-20241022")
        
        if result['success']:
            return {
                'success': True,
                'research': result['response'].get('response', result['response']) if isinstance(result['response'], dict) else result['response'],
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': result['error']
            }
    
    def parse_prd(self, prd_content: str, auto_add: bool = True) -> List[Task]:
        """Parse PRD content and create tasks"""
        prompt = f"""You are an expert project manager. Parse the following PRD (Product Requirements Document) and create a comprehensive task list.

PRD Content:
{prd_content}

Create a structured task list with:
1. Clear task titles and descriptions
2. Logical dependencies between tasks
3. Appropriate priority levels (high/medium/low)
4. Implementation details where applicable
5. Test strategies for each task

Return your response as a JSON array with this structure:
[
  {{
    "title": "Task title",
    "description": "Task description",
    "priority": "high|medium|low",
    "dependencies": [list of task numbers this depends on],
    "details": "Implementation details",
    "testStrategy": "How to test this task"
  }}
]

Ensure tasks are ordered logically with foundational tasks first."""

        result = self._execute_claude(prompt)
        
        if not result['success']:
            logger.error(f"Failed to parse PRD: {result['error']}")
            return []
        
        tasks_created = []
        try:
            if isinstance(result['response'], dict) and 'response' in result['response']:
                tasks_data = json.loads(result['response']['response'])
            elif isinstance(result['response'], str):
                # Extract JSON from response
                import re
                json_match = re.search(r'\[.*\]', result['response'], re.DOTALL)
                if json_match:
                    tasks_data = json.loads(json_match.group())
                else:
                    logger.error("No JSON found in response")
                    return []
            else:
                tasks_data = result['response']
            
            # Create tasks if auto_add is True
            if auto_add:
                # Map old indices to new task IDs for dependencies
                id_mapping = {}
                
                for idx, task_data in enumerate(tasks_data):
                    # Map dependencies using the mapping
                    mapped_deps = []
                    for dep in task_data.get('dependencies', []):
                        if dep in id_mapping:
                            mapped_deps.append(id_mapping[dep])
                    
                    # Create task
                    task = self.task_manager.add_task(
                        title=task_data.get('title', f'Task {idx+1}'),
                        description=task_data.get('description', ''),
                        dependencies=mapped_deps,
                        priority=task_data.get('priority', 'medium'),
                        details=task_data.get('details'),
                        testStrategy=task_data.get('testStrategy')
                    )
                    
                    # Store mapping
                    id_mapping[idx + 1] = task.id
                    tasks_created.append(task)
            else:
                # Just return parsed tasks without adding
                for task_data in tasks_data:
                    task = Task(
                        id=0,  # Temporary ID
                        title=task_data.get('title', ''),
                        description=task_data.get('description', ''),
                        dependencies=task_data.get('dependencies', []),
                        priority=task_data.get('priority', 'medium'),
                        details=task_data.get('details'),
                        testStrategy=task_data.get('testStrategy')
                    )
                    tasks_created.append(task)
                    
        except Exception as e:
            logger.error(f"Error parsing tasks from PRD: {e}")
            
        return tasks_created