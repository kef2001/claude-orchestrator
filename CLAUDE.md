# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Orchestrator system that uses Claude Opus as a manager and multiple Claude Sonnet instances as workers for parallel task processing. It integrates with Task Master AI for comprehensive task management.

## Essential Commands

### Orchestrator Commands

```bash
# Check Claude CLI setup
python claude_orchestrator.py check

# Run the orchestrator (processes all pending tasks)
python claude_orchestrator.py run

# Add a new task via Opus manager
python claude_orchestrator.py add "task description"

# Parse a PRD file to create tasks
python claude_orchestrator.py parse path/to/prd.txt

# Check session usage status
python claude_orchestrator.py status
```

### Task Master Commands (if installed)

```bash
# View all tasks
task-master list

# Get next available task
task-master next

# Show task details
task-master show <id>

# Mark task complete
task-master set-status --id=<id> --status=done

# Expand task into subtasks
task-master expand --id=<id> --research
```

## Architecture

### Core Components

1. **claude_orchestrator.py** - Main orchestration engine
   - Manages Opus (planner) and Sonnet (worker) instances
   - Handles parallel task execution with ThreadPoolExecutor
   - Monitors session usage and provides warnings
   - Integrates with Task Master for task status updates

2. **orchestrator_config.json** - Configuration file
   - Models: manager (Opus) and worker (Sonnet) settings
   - Execution parameters: timeouts, max workers, retry settings
   - Monitoring: usage thresholds and warnings
   - Notification: Slack webhook configuration

3. **Task Master Integration** (.taskmaster/)
   - tasks.json: Main task database
   - config.json: AI model configurations
   - PRD parsing and task generation capabilities

### Workflow

1. Opus manager analyzes and plans tasks from Task Master
2. Tasks are distributed to Sonnet workers based on dependencies
3. Workers execute tasks in parallel using Claude CLI
4. Real-time progress tracking with visual indicators
5. Automatic task status updates in Task Master

## Development Guidelines

### Running Tests
Currently no test framework is configured. When implementing tests:
- Check for test commands in package.json or setup.py
- Follow existing patterns if tests are added

### Configuration

Required environment variables in .env:
```bash
ANTHROPIC_API_KEY=your_key_here
# Optional but recommended:
PERPLEXITY_API_KEY=your_key_here
```

### Key Configuration Options

In orchestrator_config.json:
- `max_workers`: Number of parallel Sonnet workers (default: 3)
- `timeout_minutes`: Task timeout (default: 30)
- `usage_warning_threshold`: Session usage warning level (default: 0.8)
- `slack_webhook_url`: Optional Slack notifications

### Error Handling

The orchestrator includes comprehensive error handling:
- **HTTP Error Recognition**: Handles all standard API error codes (400, 401, 403, 404, 413, 429, 500, 529)
- **Automatic Retries**: Intelligent retry logic for transient errors (429 rate limit, 529 overloaded, 500 server errors)
  - Exponential backoff with jitter
  - Configurable max retries (default: 3)
  - Respects server-provided retry-after headers
- **Request ID Tracking**: Logs request IDs for debugging with Anthropic support
- **Streaming Error Support**: Handles errors that occur during SSE streaming
- **Session Usage Monitoring**: Prevents limit exceeded errors
- **Detailed Error Logging**: Clear error messages with context
- **Graceful Shutdown**: Clean handling of interruptions

#### Retry Configuration

In orchestrator_config.json:
```json
"execution": {
  "max_retries": 3,
  "retry_base_delay": 1.0,
  "retry_max_delay": 60.0
}
```

## Important Notes

1. **Session Management**: Monitor usage warnings - the orchestrator will pause when approaching limits
2. **Task Dependencies**: Respect task dependencies defined in Task Master
3. **Parallel Execution**: Tasks without dependencies run in parallel automatically
4. **Progress Tracking**: Use the visual progress bars to monitor execution
5. **Task Status**: Always update task status in Task Master after completion

## Common Workflows

### Processing All Pending Tasks
```bash
python claude_orchestrator.py run
```

### Adding and Processing New Task
```bash
python claude_orchestrator.py add "Implement new feature X"
python claude_orchestrator.py run
```

### Monitoring Progress
- Watch the real-time progress bars during execution
- Check `python claude_orchestrator.py status` for usage
- Review Task Master with `task-master list` for task states