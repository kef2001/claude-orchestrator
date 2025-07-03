# Claude Code overview

> Learn about Claude Code, the agentic coding tool that lives in your terminal, understands your codebase, and helps you code faster through natural language commands.

By integrating directly with your development environment, Claude Code streamlines your workflow without requiring additional servers or complex setup.

## Basic usage

To install Claude Code, use NPM:

```bash
npm install -g @anthropic-ai/claude-code
```

For more detailed installation instructions, see [Set up Claude Code](/en/docs/claude-code/setup).

To run Claude Code, simply call the `claude` CLI:

```bash
claude
```

You can then prompt Claude directly from the interactive Claude Code REPL session.

For more usage instructions, see [Quickstart](/en/docs/claude-code/quickstart).

## Why Claude Code?

### Accelerate development

Use Claude Code to accelerate development with the following key capabilities:

* Editing files and fixing bugs across your codebase
* Answering questions about your code's architecture and logic
* Executing and fixing tests, linting, and other commands
* Searching through git history, resolving merge conflicts, and creating commits and PRs
* Browsing documentation and resources from the internet using web search

### Security and privacy by design

Your code's security is paramount. Claude Code's architecture ensures:

* **Direct API connection**: Your queries go straight to Anthropic's API without intermediate servers
* **Works where you work**: Operates directly in your terminal
* **Understands context**: Maintains awareness of your entire project structure
* **Takes action**: Performs real operations like editing files and creating commits

### Enterprise integration

Claude Code seamlessly integrates with enterprise AI platforms. You can connect to [Amazon Bedrock or Google Vertex AI](/en/docs/claude-code/third-party-integrations) for secure, compliant deployments that meet your organization's requirements.

## Next steps

<CardGroup>
  <Card title="Setup" icon="download" href="/en/docs/claude-code/setup">
    Install and authenticate Claude Code
  </Card>

  <Card title="Quickstart" icon="rocket" href="/en/docs/claude-code/quickstart">
    See Claude Code in action with practical examples
  </Card>

  <Card title="Commands" icon="terminal" href="/en/docs/claude-code/cli-reference">
    Learn about CLI commands and controls
  </Card>

  <Card title="Configuration" icon="gear" href="/en/docs/claude-code/settings">
    Customize Claude Code for your workflow
  </Card>
</CardGroup>

## Additional resources

<CardGroup>
  <Card title="Common workflows" icon="graduation-cap" href="/en/docs/claude-code/common-workflows">
    Step-by-step guides for common workflows
  </Card>

  <Card title="Troubleshooting" icon="wrench" href="/en/docs/claude-code/troubleshooting">
    Solutions for common issues with Claude Code
  </Card>

  <Card title="Bedrock & Vertex integrations" icon="cloud" href="/en/docs/claude-code/bedrock-vertex-proxies">
    Configure Claude Code with Amazon Bedrock or Google Vertex AI
  </Card>

  <Card title="Reference implementation" icon="code" href="https://github.com/anthropics/claude-code/tree/main/.devcontainer">
    Clone our development container reference implementation.
  </Card>
</CardGroup>


# Set up Claude Code

> Install, authenticate, and start using Claude Code on your development machine.

## System requirements

* **Operating Systems**: macOS 10.15+, Ubuntu 20.04+/Debian 10+, or Windows via WSL
* **Hardware**: 4GB RAM minimum
* **Software**:
  * Node.js 18+
  * [git](https://git-scm.com/downloads) 2.23+ (optional)
  * [GitHub](https://cli.github.com/) or [GitLab](https://gitlab.com/gitlab-org/cli) CLI for PR workflows (optional)
* **Network**: Internet connection required for authentication and AI processing
* **Location**: Available only in [supported countries](https://www.anthropic.com/supported-countries)

## Install and authenticate

<Steps>
  <Step title="Install Claude Code">
    Install [NodeJS 18+](https://nodejs.org/en/download), then run:

    ```sh
    npm install -g @anthropic-ai/claude-code
    ```

    <Warning>
      Do NOT use `sudo npm install -g` as this can lead to permission issues and
      security risks. If you encounter permission errors, see [configure Claude
      Code](/en/docs/claude-code/troubleshooting#linux-permission-issues) for recommended solutions.
    </Warning>
  </Step>

  <Step title="Navigate to your project">
    ```bash
    cd your-project-directory 
    ```
  </Step>

  <Step title="Start Claude Code">
    ```bash
    claude
    ```
  </Step>

  <Step title="Complete authentication">
    Claude Code offers multiple authentication options:

    1. **Anthropic Console**: The default option. Connect through the Anthropic Console and
       complete the OAuth process. Requires active billing at [console.anthropic.com](https://console.anthropic.com).
    2. **Claude App (with Pro or Max plan)**: Subscribe to Claude's [Pro or Max plan](https://www.anthropic.com/pricing) for a unified subscription that includes both Claude Code and the web interface. Get more value at the same price point while managing your account in one place. Log in with your Claude.ai account. During launch, choose the option that matches your subscription type.
    3. **Enterprise platforms**: Configure Claude Code to use
       [Amazon Bedrock or Google Vertex AI](/en/docs/claude-code/bedrock-vertex-proxies)
       for enterprise deployments with your existing cloud infrastructure.
  </Step>
</Steps>

## Initialize your project

For first-time users, we recommend:

<Steps>
  <Step title="Start Claude Code">
    ```bash
    claude
    ```
  </Step>

  <Step title="Run a simple command">
    ```
    > summarize this project
    ```
  </Step>

  <Step title="Generate a CLAUDE.md project guide">
    ```
    /init 
    ```
  </Step>

  <Step title="Commit the generated CLAUDE.md file">
    Ask Claude to commit the generated CLAUDE.md file to your repository.
  </Step>
</Steps>

## Troubleshooting

### Troubleshooting WSL installation

Currently, Claude Code does not run directly in Windows, and instead requires WSL.

You might encounter the following issues in WSL:

**OS/platform detection issues**: If you receive an error during installation, WSL may be using Windows `npm`. Try:

* Run `npm config set os linux` before installation
* Install with `npm install -g @anthropic-ai/claude-code --force --no-os-check` (Do NOT use `sudo`)

**Node not found errors**: If you see `exec: node: not found` when running `claude`, your WSL environment may be using a Windows installation of Node.js. You can confirm this with `which npm` and `which node`, which should point to Linux paths starting with `/usr/` rather than `/mnt/c/`. To fix this, try installing Node via your Linux distribution's package manager or via [`nvm`](https://github.com/nvm-sh/nvm).

## Optimize your terminal setup

Claude Code works best when your terminal is properly configured. Follow these guidelines to optimize your experience.

**Supported shells**:

* Bash
* Zsh
* Fish

### Themes and appearance

Claude cannot control the theme of your terminal. That's handled by your terminal application. You can match Claude Code's theme to your terminal during onboarding or any time via the `/config` command

### Line breaks

You have several options for entering linebreaks into Claude Code:

* **Quick escape**: Type `\` followed by Enter to create a newline
* **Keyboard shortcut**: Press Option+Enter (Meta+Enter) with proper configuration

To set up Option+Enter in your terminal:

**For Mac Terminal.app:**

1. Open Settings → Profiles → Keyboard
2. Check "Use Option as Meta Key"

**For iTerm2 and VSCode terminal:**

1. Open Settings → Profiles → Keys
2. Under General, set Left/Right Option key to "Esc+"

**Tip for iTerm2 and VSCode users**: Run `/terminal-setup` within Claude Code to automatically configure Shift+Enter as a more intuitive alternative.

### Notification setup

Never miss when Claude completes a task with proper notification configuration:

#### Terminal bell notifications

Enable sound alerts when tasks complete:

```sh
claude config set --global preferredNotifChannel terminal_bell
```

**For macOS users**: Don't forget to enable notification permissions in System Settings → Notifications → \[Your Terminal App].

#### iTerm 2 system notifications

For iTerm 2 alerts when tasks complete:

1. Open iTerm 2 Preferences
2. Navigate to Profiles → Terminal
3. Enable "Silence bell" and Filter Alerts → "Send escape sequence-generated alerts"
4. Set your preferred notification delay

Note that these notifications are specific to iTerm 2 and not available in the default macOS Terminal.

### Handling large inputs

When working with extensive code or long instructions:

* **Avoid direct pasting**: Claude Code may struggle with very long pasted content
* **Use file-based workflows**: Write content to a file and ask Claude to read it
* **Be aware of VS Code limitations**: The VS Code terminal is particularly prone to truncating long pastes

### Vim Mode

Claude Code supports a subset of Vim keybindings that can be enabled with `/vim` or configured via `/config`.

The supported subset includes:

* Mode switching: `Esc` (to NORMAL), `i`/`I`, `a`/`A`, `o`/`O` (to INSERT)
* Navigation: `h`/`j`/`k`/`l`, `w`/`e`/`b`, `0`/`$`/`^`, `gg`/`G`
* Editing: `x`, `dw`/`de`/`db`/`dd`/`D`, `cw`/`ce`/`cb`/`cc`/`C`, `.` (repeat)


# Quickstart

> Welcome to Claude Code!

This quickstart guide will have you using AI-powered coding assistance in just a few minutes. By the end, you'll understand how to use Claude Code for common development tasks.

## Before you begin

Make sure you have:

* [Installed Claude Code](/en/docs/claude-code/setup)
* A terminal or command prompt open
* A code project to work with (or use our [sample project](https://github.com/anthropics/claude-code-quickstart))

## Step 1: Start your first session

Open your terminal in any project directory and start Claude Code:

```bash
cd /path/to/your/project
claude
```

You'll see the Claude Code prompt inside a new interactive session:

```
✻ Welcome to Claude Code!

...

> Try "create a util logging.py that..." 
```

## Step 2: Ask your first question

Let's start with understanding your codebase. Try one of these commands:

```
> what does this project do?
```

Claude will analyze your files and provide a summary. You can also ask more specific questions:

```
> what technologies does this project use?
```

```
> where is the main entry point?
```

```
> explain the folder structure
```

<Note>
  Claude Code reads your files as needed - you don't have to manually add context.
</Note>

## Step 3: Make your first code change

Now let's make Claude Code do some actual coding. Try a simple task:

```
> add a hello world function to the main file
```

Claude Code will:

1. Find the appropriate file
2. Show you the proposed changes
3. Ask for your approval
4. Make the edit

<Note>
  Claude Code always asks for permission before modifying files. You can approve individual changes or enable "Accept all" mode for a session.
</Note>

## Step 4: Use Git with Claude Code

Claude Code makes Git operations conversational:

```
> what files have I changed?
```

```
> commit my changes with a descriptive message
```

You can also prompt for more complex Git operations:

```
> create a new branch called feature/quickstart
```

```
> show me the last 5 commits
```

```
> help me resolve merge conflicts
```

## Step 5: Fix a bug or add a feature

Claude is proficient at debugging and feature implementation.

Describe what you want in natural language:

```
> add input validation to the user registration form
```

Or fix existing issues:

```
> there's a bug where users can submit empty forms - fix it
```

Claude Code will:

* Locate the relevant code
* Understand the context
* Implement a solution
* Run tests if available

## Step 6: Test out other common workflows

There are a number of ways to work with Claude:

**Refactor code**

```
> refactor the authentication module to use async/await instead of callbacks
```

**Write tests**

```
> write unit tests for the calculator functions
```

**Update documentation**

```
> update the README with installation instructions
```

**Code review**

```
> review my changes and suggest improvements
```

<Tip>
  **Remember**: Claude Code is your AI pair programmer. Talk to it like you would a helpful colleague - describe what you want to achieve, and it will help you get there.
</Tip>

## Essential commands

Here are the most important commands for daily use:

| Command             | What it does                      | Example                             |
| ------------------- | --------------------------------- | ----------------------------------- |
| `claude`            | Start interactive mode            | `claude`                            |
| `claude "task"`     | Run a one-time task               | `claude "fix the build error"`      |
| `claude -p "query"` | Run one-off query, then exit      | `claude -p "explain this function"` |
| `claude -c`         | Continue most recent conversation | `claude -c`                         |
| `claude -r`         | Resume a previous conversation    | `claude -r`                         |
| `claude commit`     | Create a Git commit               | `claude commit`                     |
| `/clear`            | Clear conversation history        | `> /clear`                          |
| `/help`             | Show available commands           | `> /help`                           |
| `exit` or Ctrl+C    | Exit Claude Code                  | `> exit`                            |

## Pro tips for beginners

<AccordionGroup>
  <Accordion title="Be specific with your requests">
    Instead of: "fix the bug"

    Try: "fix the login bug where users see a blank screen after entering wrong credentials"
  </Accordion>

  <Accordion title="Use step-by-step instructions">
    Break complex tasks into steps:

    ```
    > 1. create a new API endpoint for user profiles
    ```

    ```
    > 2. add validation for required fields
    ```

    ```
    > 3. write tests for the endpoint
    ```
  </Accordion>

  <Accordion title="Let Claude explore first">
    Before making changes, let Claude understand your code:

    ```
    > analyze the database schema
    ```

    ```
    > how does error handling work in this app?
    ```
  </Accordion>

  <Accordion title="Save time with shortcuts">
    * Use Tab for command completion
    * Press ↑ for command history
    * Type `/` to see all slash commands
  </Accordion>
</AccordionGroup>

## What's next?

Now that you've learned the basics, explore more advanced features:

<CardGroup cols={3}>
  <Card title="CLI reference" icon="terminal" href="/en/docs/claude-code/cli-reference">
    Master all commands and options
  </Card>

  <Card title="Configuration" icon="gear" href="/en/docs/claude-code/settings">
    Customize Claude Code for your workflow
  </Card>

  <Card title="Common workflows" icon="graduation-cap" href="/en/docs/claude-code/common-workflows">
    Learn advanced techniques
  </Card>
</CardGroup>

## Getting help

* **In Claude Code**: Type `/help` or ask "how do I..."
* **Documentation**: You're here! Browse other guides
* **Community**: Join our [Discord](https://discord.gg/anthropic) for tips and support




# CLI reference

> Complete reference for Claude Code command-line interface, including commands and flags.

## CLI commands

| Command                            | Description                                    | Example                                                            |
| :--------------------------------- | :--------------------------------------------- | :----------------------------------------------------------------- |
| `claude`                           | Start interactive REPL                         | `claude`                                                           |
| `claude "query"`                   | Start REPL with initial prompt                 | `claude "explain this project"`                                    |
| `claude -p "query"`                | Query via SDK, then exit                       | `claude -p "explain this function"`                                |
| `cat file \| claude -p "query"`    | Process piped content                          | `cat logs.txt \| claude -p "explain"`                              |
| `claude -c`                        | Continue most recent conversation              | `claude -c`                                                        |
| `claude -c -p "query"`             | Continue via SDK                               | `claude -c -p "Check for type errors"`                             |
| `claude -r "<session-id>" "query"` | Resume session by ID                           | `claude -r "abc123" "Finish this PR"`                              |
| `claude update`                    | Update to latest version                       | `claude update`                                                    |
| `claude mcp`                       | Configure Model Context Protocol (MCP) servers | See the [Claude Code MCP documentation](/en/docs/claude-code/mcp). |

## CLI flags

Customize Claude Code's behavior with these command-line flags:

| Flag                             | Description                                                                                                                                              | Example                                                     |
| :------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------- |
| `--add-dir`                      | Add additional working directories for Claude to access (validates each path exists as a directory)                                                      | `claude --add-dir ../apps ../lib`                           |
| `--allowedTools`                 | A list of tools that should be allowed without prompting the user for permission, in addition to [settings.json files](/en/docs/claude-code/settings)    | `"Bash(git log:*)" "Bash(git diff:*)" "Read"`               |
| `--disallowedTools`              | A list of tools that should be disallowed without prompting the user for permission, in addition to [settings.json files](/en/docs/claude-code/settings) | `"Bash(git log:*)" "Bash(git diff:*)" "Edit"`               |
| `--print`, `-p`                  | Print response without interactive mode (see [SDK documentation](/en/docs/claude-code/sdk) for programmatic usage details)                               | `claude -p "query"`                                         |
| `--output-format`                | Specify output format for print mode (options: `text`, `json`, `stream-json`)                                                                            | `claude -p "query" --output-format json`                    |
| `--input-format`                 | Specify input format for print mode (options: `text`, `stream-json`)                                                                                     | `claude -p --output-format json --input-format stream-json` |
| `--verbose`                      | Enable verbose logging, shows full turn-by-turn output (helpful for debugging in both print and interactive modes)                                       | `claude --verbose`                                          |
| `--max-turns`                    | Limit the number of agentic turns in non-interactive mode                                                                                                | `claude -p --max-turns 3 "query"`                           |
| `--model`                        | Sets the model for the current session with an alias for the latest model (`sonnet` or `opus`) or a model's full name                                    | `claude --model claude-sonnet-4-20250514`                   |
| `--permission-mode`              | Begin in a specified [permission mode](iam#permission-modes)                                                                                             | `claude --permission-mode plan`                             |
| `--permission-prompt-tool`       | Specify an MCP tool to handle permission prompts in non-interactive mode                                                                                 | `claude -p --permission-prompt-tool mcp_auth_tool "query"`  |
| `--resume`                       | Resume a specific session by ID, or by choosing in interactive mode                                                                                      | `claude --resume abc123 "query"`                            |
| `--continue`                     | Load the most recent conversation in the current directory                                                                                               | `claude --continue`                                         |
| `--dangerously-skip-permissions` | Skip permission prompts (use with caution)                                                                                                               | `claude --dangerously-skip-permissions`                     |

<Tip>
  The `--output-format json` flag is particularly useful for scripting and
  automation, allowing you to parse Claude's responses programmatically.
</Tip>

For detailed information about print mode (`-p`) including output formats,
streaming, verbose logging, and programmatic usage, see the
[SDK documentation](/en/docs/claude-code/sdk).

## See also

* [Interactive mode](/en/docs/claude-code/interactive-mode) - Shortcuts, input modes, and interactive features
* [Slash commands](/en/docs/claude-code/slash-commands) - Interactive session commands
* [Quickstart guide](/en/docs/claude-code/quickstart) - Getting started with Claude Code
* [Common workflows](/en/docs/claude-code/common-workflows) - Advanced workflows and patterns
* [Settings](/en/docs/claude-code/settings) - Configuration options
* [SDK documentation](/en/docs/claude-code/sdk) - Programmatic usage and integrations


# Claude Code settings

> Configure Claude Code with global and project-level settings, and environment variables.

Claude Code offers a variety of settings to configure its behavior to meet your needs. You can configure Claude Code by running the `/config` command when using the interactive REPL.

## Settings files

The `settings.json` file is our official mechanism for configuring Claude
Code through hierarchical settings:

* **User settings** are defined in `~/.claude/settings.json` and apply to all
  projects.
* **Project settings** are saved in your project directory:
  * `.claude/settings.json` for settings that are checked into source control and shared with your team
  * `.claude/settings.local.json` for settings that are not checked in, useful for personal preferences and experimentation. Claude Code will configure git to ignore `.claude/settings.local.json` when it is created.
* For enterprise deployments of Claude Code, we also support **enterprise
  managed policy settings**. These take precedence over user and project
  settings. System administrators can deploy policies to
  `/Library/Application Support/ClaudeCode/managed-settings.json` on macOS and
  `/etc/claude-code/managed-settings.json` on Linux and Windows via WSL.

```JSON Example settings.json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test:*)",
      "Read(~/.zshrc)"
    ],
    "deny": [
      "Bash(curl:*)"
    ]
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp"
  }
}
```

### Available settings

`settings.json` supports a number of options:

| Key                   | Description                                                                                                                                                                                                    | Example                         |
| :-------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------ |
| `apiKeyHelper`        | Custom script, to be executed in `/bin/sh`, to generate an auth value. This value will generally be sent as `X-Api-Key`, `Authorization: Bearer`, and `Proxy-Authorization: Bearer` headers for model requests | `/bin/generate_temp_api_key.sh` |
| `cleanupPeriodDays`   | How long to locally retain chat transcripts (default: 30 days)                                                                                                                                                 | `20`                            |
| `env`                 | Environment variables that will be applied to every session                                                                                                                                                    | `{"FOO": "bar"}`                |
| `includeCoAuthoredBy` | Whether to include the `co-authored-by Claude` byline in git commits and pull requests (default: `true`)                                                                                                       | `false`                         |
| `permissions`         | See table below for structure of permissions.                                                                                                                                                                  |                                 |

### Permission settings

| Keys                           | Description                                                                                                                                        | Example                          |
| :----------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------- |
| `allow`                        | Array of [permission rules](/en/docs/claude-code/iam#configuring-permissions) to allow tool use                                                    | `[ "Bash(git diff:*)" ]`         |
| `deny`                         | Array of [permission rules](/en/docs/claude-code/iam#configuring-permissions) to deny tool use                                                     | `[ "WebFetch", "Bash(curl:*)" ]` |
| `additionalDirectories`        | Additional [working directories](iam#working-directories) that Claude has access to                                                                | `[ "../docs/" ]`                 |
| `defaultMode`                  | Default [permission mode](iam#permission-modes) when opening Claude Code                                                                           | `"allowEdits"`                   |
| `disableBypassPermissionsMode` | Set to `"disable"` to prevent `bypassPermissions` mode from being activated. See [managed policy settings](iam#enterprise-managed-policy-settings) | `"disable"`                      |
| `forceLoginMethod`             | Use `claudeai` to restrict login to subscription plans only, `console` to restrict login to Anthropic Console (API usage billing) accounts only    | `claudeai`                       |

### Settings precedence

Settings are applied in order of precedence:

1. Enterprise policies (see [IAM documentation](/en/docs/claude-code/iam#enterprise-managed-policy-settings))
2. Command line arguments
3. Local project settings
4. Shared project settings
5. User settings

## Environment variables

Claude Code supports the following environment variables to control its behavior:

<Note>
  All environment variables can also be configured in [`settings.json`](#available-settings). This is useful as a way to automatically set environment variables for each session, or to roll out a set of environment variables for your whole team or organization.
</Note>

| Variable                                   | Purpose                                                                                                                                |
| :----------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------- |
| `ANTHROPIC_API_KEY`                        | API key sent as `X-Api-Key` header, typically for the Claude SDK (for interactive usage, run `/login`)                                 |
| `ANTHROPIC_AUTH_TOKEN`                     | Custom value for the `Authorization` and `Proxy-Authorization` headers (the value you set here will be prefixed with `Bearer `)        |
| `ANTHROPIC_CUSTOM_HEADERS`                 | Custom headers you want to add to the request (in `Name: Value` format)                                                                |
| `ANTHROPIC_MODEL`                          | Name of custom model to use (see [Model Configuration](/en/docs/claude-code/bedrock-vertex-proxies#model-configuration))               |
| `ANTHROPIC_SMALL_FAST_MODEL`               | Name of [Haiku-class model for background tasks](/en/docs/claude-code/costs)                                                           |
| `BASH_DEFAULT_TIMEOUT_MS`                  | Default timeout for long-running bash commands                                                                                         |
| `BASH_MAX_TIMEOUT_MS`                      | Maximum timeout the model can set for long-running bash commands                                                                       |
| `BASH_MAX_OUTPUT_LENGTH`                   | Maximum number of characters in bash outputs before they are middle-truncated                                                          |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` | Return to the original working directory after each Bash command                                                                       |
| `CLAUDE_CODE_API_KEY_HELPER_TTL_MS`        | Interval in milliseconds at which credentials should be refreshed (when using `apiKeyHelper`)                                          |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS`            | Set the maximum number of output tokens for most requests                                                                              |
| `CLAUDE_CODE_USE_BEDROCK`                  | Use Bedrock (see [Bedrock & Vertex](/en/docs/claude-code/bedrock-vertex-proxies))                                                      |
| `CLAUDE_CODE_USE_VERTEX`                   | Use Vertex (see [Bedrock & Vertex](/en/docs/claude-code/bedrock-vertex-proxies))                                                       |
| `CLAUDE_CODE_SKIP_BEDROCK_AUTH`            | Skip AWS authentication for Bedrock (e.g. when using an LLM gateway)                                                                   |
| `CLAUDE_CODE_SKIP_VERTEX_AUTH`             | Skip Google authentication for Vertex (e.g. when using an LLM gateway)                                                                 |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Equivalent of setting `DISABLE_AUTOUPDATER`, `DISABLE_BUG_COMMAND`, `DISABLE_ERROR_REPORTING`, and `DISABLE_TELEMETRY`                 |
| `DISABLE_AUTOUPDATER`                      | Set to `1` to disable the automatic updater                                                                                            |
| `DISABLE_BUG_COMMAND`                      | Set to `1` to disable the `/bug` command                                                                                               |
| `DISABLE_COST_WARNINGS`                    | Set to `1` to disable cost warning messages                                                                                            |
| `DISABLE_ERROR_REPORTING`                  | Set to `1` to opt out of Sentry error reporting                                                                                        |
| `DISABLE_NON_ESSENTIAL_MODEL_CALLS`        | Set to `1` to disable model calls for non-critical paths like flavor text                                                              |
| `DISABLE_TELEMETRY`                        | Set to `1` to opt out of Statsig telemetry (note that Statsig events do not include user data like code, file paths, or bash commands) |
| `HTTP_PROXY`                               | Specify HTTP proxy server for network connections                                                                                      |
| `HTTPS_PROXY`                              | Specify HTTPS proxy server for network connections                                                                                     |
| `MAX_THINKING_TOKENS`                      | Force a thinking for the model budget                                                                                                  |
| `MCP_TIMEOUT`                              | Timeout in milliseconds for MCP server startup                                                                                         |
| `MCP_TOOL_TIMEOUT`                         | Timeout in milliseconds for MCP tool execution                                                                                         |
| `MAX_MCP_OUTPUT_TOKENS`                    | Maximum number of tokens allowed in MCP tool responses (default: 25000)                                                                |

## Configuration options

We are in the process of migrating global configuration to `settings.json`.

`claude config` will be deprecated in place of [settings.json](#settings-files)

To manage your configurations, use the following commands:

* List settings: `claude config list`
* See a setting: `claude config get <key>`
* Change a setting: `claude config set <key> <value>`
* Push to a setting (for lists): `claude config add <key> <value>`
* Remove from a setting (for lists): `claude config remove <key> <value>`

By default `config` changes your project configuration. To manage your global configuration, use the `--global` (or `-g`) flag.

### Global configuration

To set a global configuration, use `claude config set -g <key> <value>`:

| Key                     | Description                                                      | Example                                                                    |
| :---------------------- | :--------------------------------------------------------------- | :------------------------------------------------------------------------- |
| `autoUpdates`           | Whether to enable automatic updates (default: `true`)            | `false`                                                                    |
| `preferredNotifChannel` | Where you want to receive notifications (default: `iterm2`)      | `iterm2`, `iterm2_with_bell`, `terminal_bell`, or `notifications_disabled` |
| `theme`                 | Color theme                                                      | `dark`, `light`, `light-daltonized`, or `dark-daltonized`                  |
| `verbose`               | Whether to show full bash and command outputs (default: `false`) | `true`                                                                     |

## Tools available to Claude

Claude Code has access to a set of powerful tools that help it understand and modify your codebase:

| Tool             | Description                                          | Permission Required |
| :--------------- | :--------------------------------------------------- | :------------------ |
| **Agent**        | Runs a sub-agent to handle complex, multi-step tasks | No                  |
| **Bash**         | Executes shell commands in your environment          | Yes                 |
| **Edit**         | Makes targeted edits to specific files               | Yes                 |
| **Glob**         | Finds files based on pattern matching                | No                  |
| **Grep**         | Searches for patterns in file contents               | No                  |
| **LS**           | Lists files and directories                          | No                  |
| **MultiEdit**    | Performs multiple edits on a single file atomically  | Yes                 |
| **NotebookEdit** | Modifies Jupyter notebook cells                      | Yes                 |
| **NotebookRead** | Reads and displays Jupyter notebook contents         | No                  |
| **Read**         | Reads the contents of files                          | No                  |
| **TodoRead**     | Reads the current session's task list                | No                  |
| **TodoWrite**    | Creates and manages structured task lists            | No                  |
| **WebFetch**     | Fetches content from a specified URL                 | Yes                 |
| **WebSearch**    | Performs web searches with domain filtering          | Yes                 |
| **Write**        | Creates or overwrites files                          | Yes                 |

Permission rules can be configured using `/allowed-tools` or in [permission settings](/en/docs/claude-code/settings#available-settings).

## See also

* [Identity and Access Management](/en/docs/claude-code/iam#configuring-permissions) - Learn about Claude Code's permission system
* [IAM and access control](/en/docs/claude-code/iam#enterprise-managed-policy-settings) - Enterprise policy management
* [Troubleshooting](/en/docs/claude-code/troubleshooting#auto-updater-issues) - Solutions for common configuration issues


# Common workflows

> Learn about common workflows with Claude Code.

Each task in this document includes clear instructions, example commands, and best practices to help you get the most from Claude Code.

## Understand new codebases

### Get a quick codebase overview

Suppose you've just joined a new project and need to understand its structure quickly.

<Steps>
  <Step title="Navigate to the project root directory">
    ```bash
    cd /path/to/project 
    ```
  </Step>

  <Step title="Start Claude Code">
    ```bash
    claude 
    ```
  </Step>

  <Step title="Ask for a high-level overview">
    ```
    > give me an overview of this codebase 
    ```
  </Step>

  <Step title="Dive deeper into specific components">
    ```
    > explain the main architecture patterns used here 
    ```

    ```
    > what are the key data models?
    ```

    ```
    > how is authentication handled?
    ```
  </Step>
</Steps>

<Tip>
  Tips:

  * Start with broad questions, then narrow down to specific areas
  * Ask about coding conventions and patterns used in the project
  * Request a glossary of project-specific terms
</Tip>

### Find relevant code

Suppose you need to locate code related to a specific feature or functionality.

<Steps>
  <Step title="Ask Claude to find relevant files">
    ```
    > find the files that handle user authentication 
    ```
  </Step>

  <Step title="Get context on how components interact">
    ```
    > how do these authentication files work together? 
    ```
  </Step>

  <Step title="Understand the execution flow">
    ```
    > trace the login process from front-end to database 
    ```
  </Step>
</Steps>

<Tip>
  Tips:

  * Be specific about what you're looking for
  * Use domain language from the project
</Tip>

***

## Fix bugs efficiently

Suppose you've encountered an error message and need to find and fix its source.

<Steps>
  <Step title="Share the error with Claude">
    ```
    > I'm seeing an error when I run npm test 
    ```
  </Step>

  <Step title="Ask for fix recommendations">
    ```
    > suggest a few ways to fix the @ts-ignore in user.ts 
    ```
  </Step>

  <Step title="Apply the fix">
    ```
    > update user.ts to add the null check you suggested 
    ```
  </Step>
</Steps>

<Tip>
  Tips:

  * Tell Claude the command to reproduce the issue and get a stack trace
  * Mention any steps to reproduce the error
  * Let Claude know if the error is intermittent or consistent
</Tip>

***

## Refactor code

Suppose you need to update old code to use modern patterns and practices.

<Steps>
  <Step title="Identify legacy code for refactoring">
    ```
    > find deprecated API usage in our codebase 
    ```
  </Step>

  <Step title="Get refactoring recommendations">
    ```
    > suggest how to refactor utils.js to use modern JavaScript features 
    ```
  </Step>

  <Step title="Apply the changes safely">
    ```
    > refactor utils.js to use ES2024 features while maintaining the same behavior 
    ```
  </Step>

  <Step title="Verify the refactoring">
    ```
    > run tests for the refactored code 
    ```
  </Step>
</Steps>

<Tip>
  Tips:

  * Ask Claude to explain the benefits of the modern approach
  * Request that changes maintain backward compatibility when needed
  * Do refactoring in small, testable increments
</Tip>

***

## Work with tests

Suppose you need to add tests for uncovered code.

<Steps>
  <Step title="Identify untested code">
    ```
    > find functions in NotificationsService.swift that are not covered by tests 
    ```
  </Step>

  <Step title="Generate test scaffolding">
    ```
    > add tests for the notification service 
    ```
  </Step>

  <Step title="Add meaningful test cases">
    ```
    > add test cases for edge conditions in the notification service 
    ```
  </Step>

  <Step title="Run and verify tests">
    ```
    > run the new tests and fix any failures 
    ```
  </Step>
</Steps>

<Tip>
  Tips:

  * Ask for tests that cover edge cases and error conditions
  * Request both unit and integration tests when appropriate
  * Have Claude explain the testing strategy
</Tip>

***

## Create pull requests

Suppose you need to create a well-documented pull request for your changes.

<Steps>
  <Step title="Summarize your changes">
    ```
    > summarize the changes I've made to the authentication module 
    ```
  </Step>

  <Step title="Generate a PR with Claude">
    ```
    > create a pr 
    ```
  </Step>

  <Step title="Review and refine">
    ```
    > enhance the PR description with more context about the security improvements 
    ```
  </Step>

  <Step title="Add testing details">
    ```
    > add information about how these changes were tested 
    ```
  </Step>
</Steps>

<Tip>
  Tips:

  * Ask Claude directly to make a PR for you
  * Review Claude's generated PR before submitting
  * Ask Claude to highlight potential risks or considerations
</Tip>

## Handle documentation

Suppose you need to add or update documentation for your code.

<Steps>
  <Step title="Identify undocumented code">
    ```
    > find functions without proper JSDoc comments in the auth module 
    ```
  </Step>

  <Step title="Generate documentation">
    ```
    > add JSDoc comments to the undocumented functions in auth.js 
    ```
  </Step>

  <Step title="Review and enhance">
    ```
    > improve the generated documentation with more context and examples 
    ```
  </Step>

  <Step title="Verify documentation">
    ```
    > check if the documentation follows our project standards 
    ```
  </Step>
</Steps>

<Tip>
  Tips:

  * Specify the documentation style you want (JSDoc, docstrings, etc.)
  * Ask for examples in the documentation
  * Request documentation for public APIs, interfaces, and complex logic
</Tip>

***

## Work with images

Suppose you need to work with images in your codebase, and you want Claude's help analyzing image content.

<Steps>
  <Step title="Add an image to the conversation">
    You can use any of these methods:

    1. Drag and drop an image into the Claude Code window
    2. Copy an image and paste it into the CLI with ctrl+v (Do not use cmd+v)
    3. Provide an image path to Claude. E.g., "Analyze this image: /path/to/your/image.png"
  </Step>

  <Step title="Ask Claude to analyze the image">
    ```
    > What does this image show?
    ```

    ```
    > Describe the UI elements in this screenshot
    ```

    ```
    > Are there any problematic elements in this diagram?
    ```
  </Step>

  <Step title="Use images for context">
    ```
    > Here's a screenshot of the error. What's causing it?
    ```

    ```
    > This is our current database schema. How should we modify it for the new feature?
    ```
  </Step>

  <Step title="Get code suggestions from visual content">
    ```
    > Generate CSS to match this design mockup
    ```

    ```
    > What HTML structure would recreate this component?
    ```
  </Step>
</Steps>

<Tip>
  Tips:

  * Use images when text descriptions would be unclear or cumbersome
  * Include screenshots of errors, UI designs, or diagrams for better context
  * You can work with multiple images in a conversation
  * Image analysis works with diagrams, screenshots, mockups, and more
</Tip>

***

## Reference files and directories

Use @ to quickly include files or directories without waiting for Claude to read them.

<Steps>
  <Step title="Reference a single file">
    ```
    > Explain the logic in @src/utils/auth.js
    ```

    This includes the full content of the file in the conversation.
  </Step>

  <Step title="Reference a directory">
    ```
    > What's the structure of @src/components?
    ```

    This provides a directory listing with file information.
  </Step>

  <Step title="Reference MCP resources">
    ```
    > Show me the data from @github:repos/owner/repo/issues
    ```

    This fetches data from connected MCP servers using the format @server:resource. See [MCP resources](/en/docs/claude-code/mcp#use-mcp-resources) for details.
  </Step>
</Steps>

<Tip>
  Tips:

  * File paths can be relative or absolute
  * @ file references add CLAUDE.md in the file's directory and parent directories to context
  * Directory references show file listings, not contents
  * You can reference multiple files in a single message (e.g., "@file1.js and @file2.js")
</Tip>

***

## Use extended thinking

Suppose you're working on complex architectural decisions, challenging bugs, or planning multi-step implementations that require deep reasoning.

<Steps>
  <Step title="Provide context and ask Claude to think">
    ```
    > I need to implement a new authentication system using OAuth2 for our API. Think deeply about the best approach for implementing this in our codebase. 
    ```

    Claude will gather relevant information from your codebase and
    use extended thinking, which will be visible in the interface.
  </Step>

  <Step title="Refine the thinking with follow-up prompts">
    ```
    > think about potential security vulnerabilities in this approach 
    ```

    ```
    > think harder about edge cases we should handle 
    ```
  </Step>
</Steps>

<Tip>
  Tips to get the most value out of extended thinking:

  Extended thinking is most valuable for complex tasks such as:

  * Planning complex architectural changes
  * Debugging intricate issues
  * Creating implementation plans for new features
  * Understanding complex codebases
  * Evaluating tradeoffs between different approaches

  The way you prompt for thinking results in varying levels of thinking depth:

  * "think" triggers basic extended thinking
  * intensifying phrases such as "think more", "think a lot", "think harder", or "think longer" triggers deeper thinking

  For more extended thinking prompting tips, see [Extended thinking tips](/en/docs/build-with-claude/prompt-engineering/extended-thinking-tips).
</Tip>

<Note>
  Claude will display its thinking process as italic gray text above the
  response.
</Note>

***

## Resume previous conversations

Suppose you've been working on a task with Claude Code and need to continue where you left off in a later session.

Claude Code provides two options for resuming previous conversations:

* `--continue` to automatically continue the most recent conversation
* `--resume` to display a conversation picker

<Steps>
  <Step title="Continue the most recent conversation">
    ```bash
    claude --continue
    ```

    This immediately resumes your most recent conversation without any prompts.
  </Step>

  <Step title="Continue in non-interactive mode">
    ```bash
    claude --continue --print "Continue with my task"
    ```

    Use `--print` with `--continue` to resume the most recent conversation in non-interactive mode, perfect for scripts or automation.
  </Step>

  <Step title="Show conversation picker">
    ```bash
    claude --resume
    ```

    This displays an interactive conversation selector showing:

    * Conversation start time
    * Initial prompt or conversation summary
    * Message count

    Use arrow keys to navigate and press Enter to select a conversation.
  </Step>
</Steps>

<Tip>
  Tips:

  * Conversation history is stored locally on your machine
  * Use `--continue` for quick access to your most recent conversation
  * Use `--resume` when you need to select a specific past conversation
  * When resuming, you'll see the entire conversation history before continuing
  * The resumed conversation starts with the same model and configuration as the original

  How it works:

  1. **Conversation Storage**: All conversations are automatically saved locally with their full message history
  2. **Message Deserialization**: When resuming, the entire message history is restored to maintain context
  3. **Tool State**: Tool usage and results from the previous conversation are preserved
  4. **Context Restoration**: The conversation resumes with all previous context intact

  Examples:

  ```bash
  # Continue most recent conversation
  claude --continue

  # Continue most recent conversation with a specific prompt
  claude --continue --print "Show me our progress"

  # Show conversation picker
  claude --resume

  # Continue most recent conversation in non-interactive mode
  claude --continue --print "Run the tests again"
  ```
</Tip>

***

## Run parallel Claude Code sessions with Git worktrees

Suppose you need to work on multiple tasks simultaneously with complete code isolation between Claude Code instances.

<Steps>
  <Step title="Understand Git worktrees">
    Git worktrees allow you to check out multiple branches from the same
    repository into separate directories. Each worktree has its own working
    directory with isolated files, while sharing the same Git history. Learn
    more in the [official Git worktree
    documentation](https://git-scm.com/docs/git-worktree).
  </Step>

  <Step title="Create a new worktree">
    ```bash
    # Create a new worktree with a new branch 
    git worktree add ../project-feature-a -b feature-a

    # Or create a worktree with an existing branch
    git worktree add ../project-bugfix bugfix-123
    ```

    This creates a new directory with a separate working copy of your repository.
  </Step>

  <Step title="Run Claude Code in each worktree">
    ```bash
    # Navigate to your worktree 
    cd ../project-feature-a

    # Run Claude Code in this isolated environment
    claude
    ```
  </Step>

  <Step title="Run Claude in another worktree">
    ```bash
    cd ../project-bugfix
    claude
    ```
  </Step>

  <Step title="Manage your worktrees">
    ```bash
    # List all worktrees
    git worktree list

    # Remove a worktree when done
    git worktree remove ../project-feature-a
    ```
  </Step>
</Steps>

<Tip>
  Tips:

  * Each worktree has its own independent file state, making it perfect for parallel Claude Code sessions
  * Changes made in one worktree won't affect others, preventing Claude instances from interfering with each other
  * All worktrees share the same Git history and remote connections
  * For long-running tasks, you can have Claude working in one worktree while you continue development in another
  * Use descriptive directory names to easily identify which task each worktree is for
  * Remember to initialize your development environment in each new worktree according to your project's setup. Depending on your stack, this might include:
    * JavaScript projects: Running dependency installation (`npm install`, `yarn`)
    * Python projects: Setting up virtual environments or installing with package managers
    * Other languages: Following your project's standard setup process
</Tip>

***

## Use Claude as a unix-style utility

### Add Claude to your verification process

Suppose you want to use Claude Code as a linter or code reviewer.

**Add Claude to your build script:**

```json
// package.json
{
    ...
    "scripts": {
        ...
        "lint:claude": "claude -p 'you are a linter. please look at the changes vs. main and report any issues related to typos. report the filename and line number on one line, and a description of the issue on the second line. do not return any other text.'"
    }
}
```

<Tip>
  Tips:

  * Use Claude for automated code review in your CI/CD pipeline
  * Customize the prompt to check for specific issues relevant to your project
  * Consider creating multiple scripts for different types of verification
</Tip>

### Pipe in, pipe out

Suppose you want to pipe data into Claude, and get back data in a structured format.

**Pipe data through Claude:**

```bash
cat build-error.txt | claude -p 'concisely explain the root cause of this build error' > output.txt
```

<Tip>
  Tips:

  * Use pipes to integrate Claude into existing shell scripts
  * Combine with other Unix tools for powerful workflows
  * Consider using --output-format for structured output
</Tip>

### Control output format

Suppose you need Claude's output in a specific format, especially when integrating Claude Code into scripts or other tools.

<Steps>
  <Step title="Use text format (default)">
    ```bash
    cat data.txt | claude -p 'summarize this data' --output-format text > summary.txt
    ```

    This outputs just Claude's plain text response (default behavior).
  </Step>

  <Step title="Use JSON format">
    ```bash
    cat code.py | claude -p 'analyze this code for bugs' --output-format json > analysis.json
    ```

    This outputs a JSON array of messages with metadata including cost and duration.
  </Step>

  <Step title="Use streaming JSON format">
    ```bash
    cat log.txt | claude -p 'parse this log file for errors' --output-format stream-json
    ```

    This outputs a series of JSON objects in real-time as Claude processes the request. Each message is a valid JSON object, but the entire output is not valid JSON if concatenated.
  </Step>
</Steps>

<Tip>
  Tips:

  * Use `--output-format text` for simple integrations where you just need Claude's response
  * Use `--output-format json` when you need the full conversation log
  * Use `--output-format stream-json` for real-time output of each conversation turn
</Tip>

***

## Create custom slash commands

Claude Code supports custom slash commands that you can create to quickly execute specific prompts or tasks.

For more details, see the [Slash commands](/en/docs/claude-code/slash-commands) reference page.

### Create project-specific commands

Suppose you want to create reusable slash commands for your project that all team members can use.

<Steps>
  <Step title="Create a commands directory in your project">
    ```bash
    mkdir -p .claude/commands
    ```
  </Step>

  <Step title="Create a Markdown file for each command">
    ```bash
    echo "Analyze the performance of this code and suggest three specific optimizations:" > .claude/commands/optimize.md 
    ```
  </Step>

  <Step title="Use your custom command in Claude Code">
    ```
    > /project:optimize 
    ```
  </Step>
</Steps>

<Tip>
  Tips:

  * Command names are derived from the filename (e.g., `optimize.md` becomes `/project:optimize`)
  * You can organize commands in subdirectories (e.g., `.claude/commands/frontend/component.md` becomes `/project:frontend:component`)
  * Project commands are available to everyone who clones the repository
  * The Markdown file content becomes the prompt sent to Claude when the command is invoked
</Tip>

### Add command arguments with \$ARGUMENTS

Suppose you want to create flexible slash commands that can accept additional input from users.

<Steps>
  <Step title="Create a command file with the $ARGUMENTS placeholder">
    ```bash
    echo "Find and fix issue #$ARGUMENTS. Follow these steps: 1.
    Understand the issue described in the ticket 2. Locate the relevant code in
    our codebase 3. Implement a solution that addresses the root cause 4. Add
    appropriate tests 5. Prepare a concise PR description" >
    .claude/commands/fix-issue.md 
    ```
  </Step>

  <Step title="Use the command with an issue number">
    In your Claude session, use the command with arguments.

    ```
    > /project:fix-issue 123 
    ```

    This will replace \$ARGUMENTS with "123" in the prompt.
  </Step>
</Steps>

<Tip>
  Tips:

  * The \$ARGUMENTS placeholder is replaced with any text that follows the command
  * You can position \$ARGUMENTS anywhere in your command template
  * Other useful applications: generating test cases for specific functions, creating documentation for components, reviewing code in particular files, or translating content to specified languages
</Tip>

### Create personal slash commands

Suppose you want to create personal slash commands that work across all your projects.

<Steps>
  <Step title="Create a commands directory in your home folder">
    ```bash
    mkdir -p ~/.claude/commands 
    ```
  </Step>

  <Step title="Create a Markdown file for each command">
    ```bash
    echo "Review this code for security vulnerabilities, focusing on:" >
    ~/.claude/commands/security-review.md 
    ```
  </Step>

  <Step title="Use your personal custom command">
    ```
    > /user:security-review 
    ```
  </Step>
</Steps>

<Tip>
  Tips:

  * Personal commands are prefixed with `/user:` instead of `/project:`
  * Personal commands are only available to you and not shared with your team
  * Personal commands work across all your projects
  * You can use these for consistent workflows across different codebases
</Tip>

***

## Next steps

<Card title="Claude Code reference implementation" icon="code" href="https://github.com/anthropics/claude-code/tree/main/.devcontainer">
  Clone our development container reference implementation.
</Card>


# Troubleshooting

> Discover solutions to common issues with Claude Code installation and usage.

## Common installation issues

### Linux permission issues

When installing Claude Code with npm, you may encounter permission errors if your npm global prefix is not user writable (eg. `/usr`, or `/usr/local`).

#### Recommended solution: Create a user-writable npm prefix

The safest approach is to configure npm to use a directory within your home folder:

```bash
# First, save a list of your existing global packages for later migration
npm list -g --depth=0 > ~/npm-global-packages.txt

# Create a directory for your global packages
mkdir -p ~/.npm-global

# Configure npm to use the new directory path
npm config set prefix ~/.npm-global

# Note: Replace ~/.bashrc with ~/.zshrc, ~/.profile, or other appropriate file for your shell
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc

# Apply the new PATH setting
source ~/.bashrc

# Now reinstall Claude Code in the new location
npm install -g @anthropic-ai/claude-code

# Optional: Reinstall your previous global packages in the new location
# Look at ~/npm-global-packages.txt and install packages you want to keep
```

This solution is recommended because it:

* Avoids modifying system directory permissions
* Creates a clean, dedicated location for your global npm packages
* Follows security best practices

#### System Recovery: If you have run commands that change ownership and permissions of system files or similar

If you've already run a command that changed system directory permissions (such as `sudo chown -R $USER:$(id -gn) /usr && sudo chmod -R u+w /usr`) and your system is now broken (for example, if you see `sudo: /usr/bin/sudo must be owned by uid 0 and have the setuid bit set`), you'll need to perform recovery steps.

##### Ubuntu/Debian Recovery Method:

1. While rebooting, hold **SHIFT** to access the GRUB menu

2. Select "Advanced options for Ubuntu/Debian"

3. Choose the recovery mode option

4. Select "Drop to root shell prompt"

5. Remount the filesystem as writable:
   ```bash
   mount -o remount,rw /
   ```

6. Fix permissions:

   ```bash
   # Restore root ownership
   chown -R root:root /usr
   chmod -R 755 /usr

   # Ensure /usr/local is owned by your user for npm packages
   chown -R YOUR_USERNAME:YOUR_USERNAME /usr/local

   # Set setuid bit for critical binaries
   chmod u+s /usr/bin/sudo
   chmod 4755 /usr/bin/sudo
   chmod u+s /usr/bin/su
   chmod u+s /usr/bin/passwd
   chmod u+s /usr/bin/newgrp
   chmod u+s /usr/bin/gpasswd
   chmod u+s /usr/bin/chsh
   chmod u+s /usr/bin/chfn

   # Fix sudo configuration
   chown root:root /usr/libexec/sudo/sudoers.so
   chmod 4755 /usr/libexec/sudo/sudoers.so
   chown root:root /etc/sudo.conf
   chmod 644 /etc/sudo.conf
   ```

7. Reinstall affected packages (optional but recommended):

   ```bash
   # Save list of installed packages
   dpkg --get-selections > /tmp/installed_packages.txt

   # Reinstall them
   awk '{print $1}' /tmp/installed_packages.txt | xargs -r apt-get install --reinstall -y
   ```

8. Reboot:
   ```bash
   reboot
   ```

##### Alternative Live USB Recovery Method:

If the recovery mode doesn't work, you can use a live USB:

1. Boot from a live USB (Ubuntu, Debian, or any Linux distribution)

2. Find your system partition:
   ```bash
   lsblk
   ```

3. Mount your system partition:
   ```bash
   sudo mount /dev/sdXY /mnt  # replace sdXY with your actual system partition
   ```

4. If you have a separate boot partition, mount it too:
   ```bash
   sudo mount /dev/sdXZ /mnt/boot  # if needed
   ```

5. Chroot into your system:

   ```bash
   # For Ubuntu/Debian:
   sudo chroot /mnt

   # For Arch-based systems:
   sudo arch-chroot /mnt
   ```

6. Follow steps 6-8 from the Ubuntu/Debian recovery method above

After restoring your system, follow the recommended solution above to set up a user-writable npm prefix.

## Auto-updater issues

If Claude Code can't update automatically, it may be due to permission issues with your npm global prefix directory. Follow the [recommended solution](#recommended-solution-create-a-user-writable-npm-prefix) above to fix this.

If you prefer to disable the auto-updater instead, you can use:
If you prefer to disable the auto-updater instead , you can
set the `DISABLE_AUTOUPDATER` [environment variable](settings#environment-variables) to `1`

## Permissions and authentication

### Repeated permission prompts

If you find yourself repeatedly approving the same commands, you can allow specific tools
to run without approval using the `/permissions` command. See [Permissions docs](/en/docs/claude-code/iam#configuring-permissions).

### Authentication issues

If you're experiencing authentication problems:

1. Run `/logout` to sign out completely
2. Close Claude Code
3. Restart with `claude` and complete the authentication process again

If problems persist, try:

```bash
rm -rf ~/.config/claude-code/auth.json
claude
```

This removes your stored authentication information and forces a clean login.

## Performance and stability

### High CPU or memory usage

Claude Code is designed to work with most development environments, but may consume significant resources when processing large codebases. If you're experiencing performance issues:

1. Use `/compact` regularly to reduce context size
2. Close and restart Claude Code between major tasks
3. Consider adding large build directories to your `.gitignore` file

### Command hangs or freezes

If Claude Code seems unresponsive:

1. Press Ctrl+C to attempt to cancel the current operation
2. If unresponsive, you may need to close the terminal and restart

### ESC key not working in JetBrains (IntelliJ, PyCharm, etc.) terminals

If you're using Claude Code in JetBrains terminals and the ESC key doesn't interrupt the agent as expected, this is likely due to a keybinding clash with JetBrains' default shortcuts.

To fix this issue:

1. Go to Settings → Tools → Terminal
2. Click the "Configure terminal keybindings" hyperlink next to "Override IDE Shortcuts"
3. Within the terminal keybindings, scroll down to "Switch focus to Editor" and delete that shortcut

This will allow the ESC key to properly function for canceling Claude Code operations instead of being captured by PyCharm's "Switch focus to Editor" action.

## Getting more help

If you're experiencing issues not covered here:

1. Use the `/bug` command within Claude Code to report problems directly to Anthropic
2. Check the [GitHub repository](https://github.com/anthropics/claude-code) for known issues
3. Run `/doctor` to check the health of your Claude Code installation


