# Claude Orchestrator 🤖

An intelligent task orchestration system that uses Claude Opus as a manager and multiple Claude Sonnet instances as workers for parallel task processing with real-time per-task reviews.

## 🌟 Key Features

- **Intelligent Task Management**: Opus analyzes and plans tasks from Task Master AI
- **Parallel Task Creation**: Opus breaks down complex tasks into parallel components for maximum efficiency
- **Parallel Processing**: Multiple Sonnet workers execute tasks concurrently
- **Real-time Per-Task Reviews**: Each completed task is immediately reviewed by Opus in parallel
- **Auto-improvement**: Opus automatically creates follow-up tasks for any issues found
- **Dynamic Scaling**: Worker count adjusts based on task volume
- **Progress Tracking**: Beautiful real-time progress display with task status
- **Slack Integration**: Rich notifications with structured blocks for task updates
- **Git Integration**: Automatic commits after task completion (optional)
- **Session Management**: Monitors API usage to prevent limit errors
- **Auto Setup**: Init command installs all dependencies and creates shortcuts

## 📋 Prerequisites

- Python 3.8+
- Node.js and npm (for Task Master AI)
- Claude CLI (via Claude Code)
- Git (optional, for auto-commit feature)

## 🚀 Quick Start

### 1. Initialize the Orchestrator

```bash
# Run the interactive setup
python claude_orchestrator.py init

# Or use the shortcut
./co init
```

This will:
- Create configuration files
- Install Python dependencies
- Install Task Master AI via npm
- Set up example files
- Create `co` shortcut command for easier usage

### 2. Configure API Keys

Create a `.env` file based on `.env.example`:

```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here  # Optional
```

Or use Claude CLI login:
```bash
claude login
```

### 3. Add Tasks

Add a single task:
```bash
./co add "Implement user authentication system"
```

Parse a requirements document:
```bash
./co parse requirements.txt
```

### 4. Run the Orchestrator

```bash
./co run
```

## 🎯 How It Works

1. **Task Analysis & Creation**: 
   - Opus Manager analyzes requests and breaks them into parallel tasks
   - Identifies independent components that can be worked on simultaneously
   - Creates focused, granular tasks for maximum parallelism

2. **Parallel Execution**: 
   - Tasks are distributed to Sonnet workers based on dependencies
   - Multiple workers process different tasks concurrently
   - Dynamic worker scaling based on task volume

3. **Real-time Per-Task Review**: 
   - As each task completes, it's immediately sent to Opus for review
   - Multiple Opus reviewers work in parallel
   - Workers continue processing while reviews happen

4. **Continuous Improvement**: 
   - If issues are found, Opus creates follow-up tasks automatically
   - Follow-up tasks are added to the queue for immediate processing
   - Ensures quality without manual intervention

5. **Progress Tracking**: 
   - Visual progress bars show real-time status
   - Track active tasks, reviews in progress, and completions
   - Session usage monitoring to prevent API limits

## 📁 Configuration

Edit `orchestrator_config.json` to customize:

```json
{
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
    "manager_timeout": 180
  },
  "notifications": {
    "slack_webhook_url": "your_webhook_url",
    "notify_on_task_complete": true
  },
  "git": {
    "auto_commit": false,
    "commit_message_prefix": "🤖 Auto-commit by Claude Orchestrator"
  }
}
```

## 🛠️ Commands

The `co` shortcut is automatically created during initialization. You can use either:
- `./co <command>` (shortcut)
- `python claude_orchestrator.py <command>` (full command)

```bash
# Initialize orchestrator (creates co shortcut)
python claude_orchestrator.py init

# After init, you can use the shortcut:
./co check              # Check Claude CLI setup
./co status             # Check session usage
./co add "task"         # Add a task
./co parse file.txt     # Parse a requirements file
./co run                # Run orchestrator
./co run --workers 5    # Run with custom workers
./co run --verbose      # Run with verbose output
```

## 📊 Features in Detail

### Parallel Task Creation & Execution
- Opus analyzes tasks and breaks them into independent components
- Creates multiple parallel tasks instead of monolithic ones
- Maximizes worker efficiency by identifying work that can be done simultaneously
- Examples: Frontend/Backend, Different modules, Tests/Documentation

### Real-time Per-Task Reviews
- Each completed task is immediately reviewed by Opus
- Multiple Opus reviewers run in parallel (configurable)
- Reviews don't block workers - they continue processing while reviews happen
- Automatic creation of improvement tasks based on review findings
- Real-time feedback on code quality and implementation

### Dynamic Worker Scaling
- Workers are created based on task count
- Minimum 1 worker, maximum configurable
- Efficient resource utilization

### Slack Notifications
- Beautiful block-formatted messages
- Task completion updates
- Opus review summaries
- Follow-up task notifications

### Git Integration
- Automatic commits after all tasks complete
- Detailed commit messages with task summaries
- Configurable commit prefix

### Progress Display
- Real-time progress bars
- Active task tracking
- Worker status monitoring
- Time elapsed tracking

## 🔧 Advanced Usage

### Custom Working Directory
```bash
./co run --working-dir /path/to/project
```

### Debug Mode
```bash
./co --debug run
```

### Disable Progress Bar
```bash
./co --verbose run
```

## 📝 Task Master Integration

The orchestrator integrates seamlessly with Task Master AI:

```bash
# View all tasks
task-master list

# Get next task
task-master next

# Mark task complete
task-master set-status --id=1 --status=done
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with [Claude Code](https://claude.ai/code)
- Task management by [Task Master AI](https://github.com/cline/task-master-ai)
- Powered by Anthropic's Claude models