# Cortex-R Agent Architecture

A reasoning-driven AI agent capable of using external tools and memory to solve complex tasks step-by-step. The agent follows a **Perception → Decision → Action** loop architecture with support for multiple MCP (Model Context Protocol) servers.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Module Descriptions](#module-descriptions)
- [Data Flow](#data-flow)
- [Configuration](#configuration)
- [Usage](#usage)
- [Examples](#example-queries-and-logs)

## Overview

Cortex-R is an autonomous agent that:
- **Perceives** user intent and selects relevant tools
- **Decides** on execution plans using LLM reasoning
- **Acts** by executing plans in a sandboxed Python environment
- **Remembers** past interactions and tool results
- **Adapts** using different planning strategies (conservative/exploratory)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         agent.py                                 │
│                    (Entry Point)                                 │
│  - Initializes MultiMCP with server configs                      │
│  - Creates AgentContext for each user query                     │
│  - Runs AgentLoop until completion                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    core/loop.py                                  │
│                    (AgentLoop)                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  For each step (max_steps):                              │   │
│  │    1. Perception → Select MCP servers & tools           │   │
│  │    2. Decision → Generate solve() plan                  │   │
│  │    3. Action → Execute plan in sandbox                  │   │
│  │    4. Memory → Store results                            │   │
│  │    5. Check for FINAL_ANSWER or continue                │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Perception   │ │  Decision    │ │   Action     │
│  Module      │ │   Module     │ │   Module     │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Detailed Module Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CORE MODULES                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐      ┌──────────────────┐                    │
│  │  context.py      │      │   session.py     │                    │
│  │                  │      │                  │                    │
│  │  AgentContext    │◄─────┤   MultiMCP       │                    │
│  │  - user_input    │      │   - tool_map     │                    │
│  │  - session_id    │      │   - server_tools │                    │
│  │  - memory        │      │   - call_tool()  │                    │
│  │  - dispatcher    │      │   - initialize() │                    │
│  │  - agent_profile │      │                  │                    │
│  └──────────────────┘      └──────────────────┘                    │
│           │                                                          │
│           │                                                          │
│  ┌────────▼──────────┐      ┌──────────────────┐                  │
│  │    loop.py        │      │   strategy.py    │                  │
│  │                   │      │                  │                  │
│  │  AgentLoop        │──────┤  select_prompt() │                  │
│  │  - run()          │      │  - conservative  │                  │
│  │  - step loop      │      │  - exploratory   │                  │
│  │  - lifelines      │      │                  │                  │
│  └───────────────────┘      └──────────────────┘                  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        FUNCTIONAL MODULES                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐      ┌──────────────────┐                    │
│  │  perception.py   │      │   decision.py    │                    │
│  │                  │      │                  │                    │
│  │  - extract_      │      │  - generate_plan │                    │
│  │    perception()  │      │  - validate      │                    │
│  │  - select        │      │    solve()       │                    │
│  │    servers       │      │                  │                    │
│  │  - intent        │      │                  │                    │
│  │  - entities      │      │                  │                    │
│  └──────────────────┘      └──────────────────┘                    │
│           │                                                          │
│           │                                                          │
│  ┌────────▼──────────┐      ┌──────────────────┐                  │
│  │    action.py      │      │    memory.py     │                  │
│  │                   │      │                  │                  │
│  │  - run_python_    │      │  MemoryManager   │                  │
│  │    sandbox()      │      │  - add()         │                  │
│  │  - SandboxMCP     │      │  - save()        │                  │
│  │  - tool calls     │      │  - load()        │                  │
│  └───────────────────┘      └──────────────────┘                  │
│                                                                       │
│  ┌──────────────────┐      ┌──────────────────┐                    │
│  │   tools.py       │      │ model_manager.py │                    │
│  │                  │      │                  │                    │
│  │  - summarize_    │      │  ModelManager    │                    │
│  │    tools()       │      │  - generate_text │                    │
│  │  - filter_tools  │      │  - Gemini        │                    │
│  │  - load_prompt   │      │  - Ollama        │                    │
│  └──────────────────┘      └──────────────────┘                  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Execution Flow Diagram

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  agent.py: main()                                            │
│  - Load config/profiles.yaml                                  │
│  - Initialize MultiMCP with MCP servers                      │
└───────────────┬───────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│  AgentContext Creation                                        │
│  - Generate session_id                                        │
│  - Initialize MemoryManager                                   │
│  - Load AgentProfile from config                              │
└───────────────┬───────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│  AgentLoop.run()                                             │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  FOR step in range(max_steps):                        │   │
│  │    FOR lifeline in range(max_lifelines_per_step):     │   │
│  │                                                        │   │
│  │      ┌──────────────────────────────────────────┐     │   │
│  │      │  1. PERCEPTION                            │     │   │
│  │      │  - run_perception()                       │     │   │
│  │      │  - Extract intent, entities               │     │   │
│  │      │  - Select relevant MCP servers            │     │   │
│  │      │  - Get tools from selected servers       │     │   │
│  │      └──────────────┬───────────────────────────┘     │   │
│  │                     │                                   │   │
│  │      ┌──────────────▼───────────────────────────┐     │   │
│  │      │  2. DECISION                              │     │   │
│  │      │  - generate_plan()                        │     │   │
│  │      │  - Select prompt based on strategy        │     │   │
│  │      │  - LLM generates solve() function         │     │   │
│  │      │  - Validate solve() format               │     │   │
│  │      └──────────────┬───────────────────────────┘     │   │
│  │                     │                                   │   │
│  │      ┌──────────────▼───────────────────────────┐     │   │
│  │      │  3. ACTION                                │     │   │
│  │      │  - run_python_sandbox(plan)               │     │   │
│  │      │  - Create sandboxed environment           │     │   │
│  │      │  - Inject SandboxMCP with dispatcher     │     │   │
│  │      │  - Execute solve() function              │     │   │
│  │      │  - Handle tool calls via MCP             │     │   │
│  │      └──────────────┬───────────────────────────┘     │   │
│  │                     │                                   │   │
│  │      ┌──────────────▼───────────────────────────┐     │   │
│  │      │  4. RESULT PROCESSING                     │     │   │
│  │      │  - Check for FINAL_ANSWER:                │     │   │
│  │      │    → Return result, exit loop            │     │   │
│  │      │  - Check for FURTHER_PROCESSING_REQUIRED:│     │   │
│  │      │    → Update user_input_override, continue│     │   │
│  │      │  - Store in memory                       │     │   │
│  │      └───────────────────────────────────────────┘     │   │
│  │                                                        │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                │
                ▼
         Final Answer
```

### MCP Server Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                    MultiMCP (session.py)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  tool_map: {tool_name → {config, tool}}                  │   │
│  │  server_tools: {server_id → [tools]}                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────┬───────────────────────────────────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ MCP     │ │ MCP     │ │ MCP     │
│ Server  │ │ Server  │ │ Server  │
│ #1      │ │ #2      │ │ #3      │
│         │ │         │ │         │
│ Math    │ │ Docs    │ │ Web     │
│ Tools   │ │ Tools   │ │ Tools   │
└─────────┘ └─────────┘ └─────────┘
```

## Module Descriptions

### Core Modules

#### `agent.py` - Entry Point
- **Purpose**: Main entry point for the agent
- **Responsibilities**:
  - Loads configuration from `config/profiles.yaml`
  - Initializes `MultiMCP` with MCP server configurations
  - Creates `AgentContext` for each user query
  - Instantiates and runs `AgentLoop`
  - Handles user input loop and session management
  - Processes final answers and further processing requirements

#### `core/loop.py` - Agent Loop Orchestrator
- **Purpose**: Orchestrates the Perception-Decision-Action cycle
- **Key Components**:
  - `AgentLoop.run()`: Main execution loop
  - Step management (max_steps)
  - Lifeline management (retries per step)
  - Coordinates perception, decision, and action modules
  - Handles result processing and loop termination

#### `core/context.py` - Context Management
- **Purpose**: Manages agent state and configuration
- **Key Components**:
  - `AgentContext`: Holds session state, user input, memory, dispatcher
  - `AgentProfile`: Loads agent configuration from YAML
  - `StrategyProfile`: Defines planning strategy parameters
  - Session ID generation and management
  - Task progress tracking

#### `core/session.py` - MCP Server Management
- **Purpose**: Manages multiple MCP servers and tool discovery
- **Key Components**:
  - `MultiMCP`: Discovers and manages tools from multiple MCP servers
  - Tool-to-server mapping
  - Tool invocation via `call_tool()`
  - Server initialization and tool discovery

#### `core/strategy.py` - Strategy Selection
- **Purpose**: Selects appropriate decision prompts based on strategy
- **Key Functions**:
  - `select_decision_prompt_path()`: Chooses prompt file based on planning mode
  - Supports conservative and exploratory planning modes
  - Handles parallel and sequential exploration modes

### Functional Modules

#### `modules/perception.py` - Intent Understanding
- **Purpose**: Analyzes user input and selects relevant tools
- **Key Functions**:
  - `extract_perception()`: Uses LLM to extract intent, entities, and tool hints
  - `run_perception()`: Wrapper for context-based perception
- **Output**: `PerceptionResult` with:
  - `intent`: User's intent
  - `entities`: Extracted entities
  - `tool_hint`: Suggested tool category
  - `selected_servers`: List of relevant MCP server IDs
  - `tags`: Classification tags

#### `modules/decision.py` - Plan Generation
- **Purpose**: Generates execution plans using LLM
- **Key Functions**:
  - `generate_plan()`: Creates a `solve()` function plan
  - Validates plan format (must contain `solve()` function)
  - Uses strategy-specific prompts
- **Output**: Python code string containing `solve()` function

#### `modules/action.py` - Plan Execution
- **Purpose**: Executes plans in a sandboxed Python environment
- **Key Components**:
  - `run_python_sandbox()`: Executes the generated plan
  - `SandboxMCP`: Wrapper that injects MCP dispatcher into sandbox
  - Tool call limit enforcement (MAX_TOOL_CALLS_PER_PLAN)
  - Error handling and result formatting

#### `modules/memory.py` - Memory Management
- **Purpose**: Manages session memory and tool call history
- **Key Components**:
  - `MemoryManager`: Handles memory persistence
  - `MemoryItem`: Represents individual memory entries
  - Date-based directory structure for storage
  - Methods: `add()`, `save()`, `load()`, `get_session_items()`
  - Success tracking for tool calls

#### `modules/tools.py` - Tool Utilities
- **Purpose**: Utility functions for tool management
- **Key Functions**:
  - `summarize_tools()`: Creates text summary of tools for prompts
  - `filter_tools_by_hint()`: Filters tools based on perception hints
  - `load_prompt()`: Loads prompt templates from files
  - `extract_json_block()`: Extracts JSON from LLM responses

#### `modules/model_manager.py` - LLM Integration
- **Purpose**: Manages LLM model interactions
- **Supported Models**:
  - Gemini (via Google GenAI SDK)
  - Ollama (local models)
- **Key Functions**:
  - `generate_text()`: Unified interface for text generation
  - Model configuration from `config/models.json`

### Configuration

#### `config/profiles.yaml`
Defines agent behavior:
- **agent**: Name, ID, description
- **strategy**: Planning mode (conservative/exploratory), exploration mode, memory fallback, max steps/lifelines
- **memory**: Storage configuration
- **llm**: Model selection (gemini, ollama, etc.)
- **persona**: Tone and behavior settings
- **mcp_servers**: List of MCP server configurations

#### `config/models.json`
Defines available LLM models:
- Model types (gemini, ollama, huggingface)
- API endpoints and configurations
- Embedding model settings

#### `prompts/`
Contains prompt templates:
- `perception_prompt.txt`: Template for intent extraction
- `decision_prompt_conservative.txt`: Conservative planning prompt
- `decision_prompt_exploratory_parallel.txt`: Parallel exploration prompt
- `decision_prompt_exploratory_sequential.txt`: Sequential exploration prompt

## Data Flow

### 1. Initialization Flow
```
agent.py
  → Load profiles.yaml
  → Initialize MultiMCP
  → Discover tools from all MCP servers
  → Create tool_map and server_tools
```

### 2. Query Processing Flow
```
User Input
  → AgentContext(user_input, session_id, dispatcher)
  → AgentLoop(context)
  → Loop.run()
    → Perception: user_input → PerceptionResult
    → Decision: PerceptionResult + tools → solve() plan
    → Action: plan → execute in sandbox → result
    → Memory: store result
    → Check: FINAL_ANSWER or continue
```

### 3. Tool Call Flow
```
solve() function in sandbox
  → sandbox.mcp.call_tool(tool_name, args)
  → SandboxMCP.call_tool()
  → dispatcher.call_tool() (MultiMCP)
  → Find tool in tool_map
  → Create MCP session for server
  → Execute tool via MCP protocol
  → Return result to sandbox
  → Continue solve() execution
```

### 4. Memory Flow
```
Tool execution
  → context.memory.add_tool_output()
  → MemoryManager.add()
  → MemoryItem created
  → Save to JSON file
  → Date-based directory structure
```

## Configuration

### Strategy Modes

#### Conservative Mode
- Plans one tool call at a time
- Uses filtered tools based on perception
- Lower risk, step-by-step approach
- Prompt: `decision_prompt_conservative.txt`

#### Exploratory Mode
- Can plan multiple tool calls
- Two sub-modes:
  - **Parallel**: Execute multiple tools simultaneously
  - **Sequential**: Execute tools one after another
- Memory fallback enabled
- Prompts: `decision_prompt_exploratory_*.txt`

### Memory Configuration
- **Storage**: Date-based directory structure (`memory/YYYY/MM/DD/`)
- **Format**: JSON files per session
- **Tracking**: Tool calls, outputs, success status, metadata

## Usage

### Basic Usage

```bash
python agent.py
```

### Interactive Mode
The agent runs in an interactive loop:
- Enter your query when prompted
- Type `exit` to quit
- Type `new` to start a new session

### Example Queries
- "Find the ASCII values of characters in INDIA and return sum of exponentials"
- "How much did Anmol Singh pay for his DLF apartment via Capbridge?"
- "What is the relationship between Gensol and Go-Auto?"

### Environment Setup
1. Create `.env` file with:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

2. Install dependencies (using `uv` or `pip`)

3. Configure MCP servers in `config/profiles.yaml`

### MCP Server Configuration
Each MCP server requires:
- `id`: Unique identifier
- `script`: Python script path
- `cwd`: Working directory
- `description`: Server capabilities description
- `capabilities`: List of available tools

## Architecture Principles

1. **Modularity**: Clear separation between core orchestration and functional modules
2. **Extensibility**: Easy to add new MCP servers and tools
3. **Strategy Pattern**: Pluggable planning strategies (conservative/exploratory)
4. **Memory Persistence**: Session-based memory with date-structured storage
5. **Sandboxed Execution**: Safe execution of generated plans
6. **Tool Abstraction**: Unified interface for multiple MCP servers

## File Structure

```
agents2-s9-policies-architecture/
├── agent.py                 # Entry point
├── core/
│   ├── context.py           # Context and profile management
│   ├── loop.py              # Main agent loop
│   ├── session.py           # MCP server management
│   └── strategy.py          # Strategy selection
├── modules/
│   ├── action.py            # Plan execution
│   ├── decision.py          # Plan generation
│   ├── memory.py            # Memory management
│   ├── model_manager.py     # LLM integration
│   ├── perception.py        # Intent understanding
│   ├── tools.py             # Tool utilities
│   └── mcp_server_memory.py # Memory MCP server
├── config/
│   ├── models.json          # LLM model configurations
│   └── profiles.yaml        # Agent configuration
├── prompts/                 # Prompt templates
├── memory/                  # Session memory storage
└── documents/               # Document storage for search
```

## Example Queries and logs
 ### Example 1 - what is the capital of North Carolina State (USA)?
 ````
 What do you want to solve today? → what is the capital of North Carolina State (USA)?
🔁 Step 1/3 starting...
[23:20:49] [perception] Raw output: ```json
{
  "intent": "Find the capital city of North Carolina.",
  "entities": ["North Carolina"],
  "tool_hint": "websearch",
  "selected_servers": ["websearch"]
}
```
result {'intent': 'Find the capital city of North Carolina.', 'entities': ['North Carolina'], 'tool_hint': 'websearch', 'selected_servers': ['websearch']}
[perception] intent='Find the capital city of North Carolina.' entities=['North Carolina'] tool_hint='websearch' tags=[] selected_servers=['websearch']
[23:20:50] [plan] LLM output: ```python
async def solve():
    """duckduckgo_search_results: Search DuckDuckGo. Usage: input={"input": {"query": "latest AI developments", "max_results": 5} } result = await mcp.call_tool('duckduckgo_search_results', input)"""
    input = {"input": {"query": "capital of North Carolina", "max_results": 1}}
    result = await mcp.call_tool('duckduckgo_search_results', input)
    parsed = json.loads(result.content[0].text)["result"]
    return f"FINAL_ANSWER: Raleigh"
```
[plan] async def solve():
    """duckduckgo_search_results: Search DuckDuckGo. Usage: input={"input": {"query": "latest AI developments", "max_results": 5} } result = await mcp.call_tool('duckduckgo_search_results', input)"""
    input = {"input": {"query": "capital of North Carolina", "max_results": 1}}
    result = await mcp.call_tool('duckduckgo_search_results', input)
    parsed = json.loads(result.content[0].text)["result"]
    return f"FINAL_ANSWER: Raleigh"
[loop] Detected solve() plan — running sandboxed...
[action] 🔍 Entered run_python_sandbox()
[01/07/26 23:20:51] INFO     Processing request of type               server.py:534
                             CallToolRequest                                       
[01/07/26 23:20:52] INFO     HTTP Request: POST                     _client.py:1740
                             https://html.duckduckgo.com/html                      
                             "HTTP/1.1 200 OK"                                     

💡 Final Answer: Raleigh
🧑 What do you want to solve today? → 
````
