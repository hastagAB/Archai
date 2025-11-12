# Archai - AI Architecture Reviewer & Recommender Agent

An autonomous architecture reasoning agent using RAG, ReAct reasoning, and multi-agent coordination to review and improve system architectures.

## Features

- **RAG Integration**: Retrieves relevant patterns from vector store
- **ReAct Reasoning**: Structured thought-action-observation loops
- **MCP Integration**: Model Context Protocol servers for security and cost analysis
- **Multi-Agent Coordination**: Security, Cost, Performance specialists
- **Graph Analysis**: Dependency and bottleneck detection
- **File Upload**: Support for PDF, Markdown, and TXT files
- **Interactive Chat**: Ask follow-up questions about architectures
- **Architecture Comparison**: Side-by-side comparison of two architectures
- **Verbose Output**: Detailed reasoning trace with thoughts, actions, and observations

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create `.env` file:
```
OPENAI_API_KEY=your_key
PINECONE_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

## Usage

### Demo Mode
```bash
python run.py --demo
```

### Interactive Mode
```bash
python run.py --interactive
```

Available commands:
- `review` - Review architecture (paste text or provide filepath)
- `upload <filepath>` - Upload and review architecture file
- `chat <message>` - Chat about current architecture
- `compare <file1> <file2>` - Compare two architectures
- `memory` - Show memory summary
- `clear` - Clear memory
- `exit` - Exit program

## Testing

```bash
# Run all tests
python -m pytest tests/test_all.py -v
```

## Project Structure

```
Archai/
├── src/
│   ├── agent.py       # Main ReAct agent (core logic)
│   ├── mcp_client.py  # MCP client for server communication
│   ├── tools.py       # All tools (RAG, Graph)
│   ├── sub_agents.py  # Specialist agents
│   ├── memory.py      # Conversation memory
│   └── utils.py       # Helpers (Logger, FileHandler)
├── mcp_servers/       # MCP servers (isolated processes)
│   ├── security_server.py
│   └── cost_server.py
├── tests/
│   └── test_all.py   # Simple tests
├── data/
│   ├── md/           # Markdown documents
│   ├── pdf/          # PDF documents
│   └── scripts/
│       └── create_rag.py
└── run.py            # Main runner
```

## Architecture

The system uses a ReAct loop:
1. **Thought**: Analyze what's needed
2. **Action**: Execute tools/sub-agents
3. **Observation**: Process results
4. **Reflection**: Validate completeness
5. **Answer**: Final recommendations
