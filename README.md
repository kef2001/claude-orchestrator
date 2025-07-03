# Claude Orchestrator 🤖

An intelligent task orchestration system that uses Claude Opus as a manager and multiple Claude Sonnet instances as workers for parallel task processing with real-time per-task reviews.

## 🌟 Key Features

- **Intelligent Task Management**: Opus analyzes and plans tasks from Task Master AI
- **Parallel Processing**: Multiple Sonnet workers execute tasks concurrently
- **Real-time Reviews**: Each completed task is immediately reviewed by Opus in parallel
- **Auto-improvement**: Opus automatically creates follow-up tasks for any issues found
- **Dynamic Scaling**: Worker count adjusts based on task volume
- **Progress Tracking**: Beautiful real-time progress display with task status
- **Slack Integration**: Rich notifications with structured blocks for task updates
- **Git Integration**: Automatic commits after task completion (optional)
- **Session Management**: Monitors API usage to prevent limit errors

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

1. **Task Analysis**: Opus Manager fetches tasks from Task Master and analyzes dependencies
2. **Parallel Execution**: Tasks are distributed to Sonnet workers based on dependencies
3. **Real-time Review**: As each task completes, Opus reviews it immediately in parallel
4. **Continuous Improvement**: If issues are found, Opus creates follow-up tasks automatically
5. **Progress Tracking**: Visual progress bars show real-time status of all operations

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

```bash
# Initialize orchestrator
./co init

# Check Claude CLI setup
./co check

# Check session usage
./co status

# Add a task
./co add "task description"

# Parse a requirements file
./co parse file.txt

# Run orchestrator with custom workers
./co run --workers 5

# Run with verbose output
./co run --verbose
```

## 📊 Features in Detail

### Parallel Task Reviews
- Each completed task is immediately reviewed by Opus
- Reviews run in parallel without blocking workers
- Automatic creation of improvement tasks
- Real-time feedback on code quality

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