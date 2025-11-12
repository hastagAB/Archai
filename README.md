# Archai - AI Architecture Reviewer & Recommender

> An autonomous architecture reasoning agent that reviews system designs, validates decisions against best practices, and provides actionable recommendations using advanced AI techniques.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Overview

Archai combines multiple AI capabilities to deliver comprehensive architecture reviews:

- **🔍 RAG (Retrieval Augmented Generation)**: Searches through 90+ architecture documents, ADRs, and patterns to find relevant best practices
- **🧠 ReAct Reasoning**: Structured thought-action-observation loops for systematic analysis
- **🤝 Multi-Agent Coordination**: Specialized agents for security, cost, and performance analysis
- **📊 Graph Analysis**: Identifies dependencies, single points of failure, and critical paths
- **✨ Self-Reflection**: Optional self-critique mechanism for improved review quality

## ✨ Key Features

### Core Capabilities

- **Structured Tool Calling**: Uses Claude's native tool calling for reliable execution
- **Streaming Output**: Real-time streaming for immediate feedback
- **MCP Integration**: Model Context Protocol servers for isolated security and cost analysis
- **Enhanced Graph Analysis**: LLM-powered component extraction with dependency analysis
- **File Upload**: Support for PDF, Markdown, and TXT files
- **Interactive Chat**: Context-aware Q&A about reviewed architectures
- **Architecture Comparison**: Side-by-side comparison of two designs
- **File Persistence**: Automatic saving of reviews, traces, and memory

### Technical Highlights

- **Production-Ready**: Error handling, logging, and graceful fallbacks
- **Modular Design**: Clean separation of concerns with focused modules
- **Extensible**: Easy to add new tools, agents, or analysis capabilities
- **Well-Tested**: Comprehensive test suite for reliability

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Archai

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### Run Your First Review

```bash
# Demo mode - see it in action
python run.py --demo

# Interactive mode - full control
python run.py --interactive
```

## 📖 Usage Guide

### Command Line Interface

#### Interactive Mode

Launch the interactive CLI:

```bash
python run.py --interactive
```

**Available Commands:**

| Command | Description |
|---------|-------------|
| `review [--stream] [--reflect]` | Review architecture with optional streaming and self-reflection |
| `upload <filepath>` | Upload and review architecture file (PDF, MD, TXT) |
| `chat <message>` | Ask follow-up questions about the reviewed architecture |
| `compare <file1> <file2>` | Compare two architecture designs side-by-side |
| `memory` | Display memory summary and session statistics |
| `save` | Manually save session to files |
| `clear` | Clear current memory and session |
| `exit` | Exit the application |

**Example Session:**

```bash
> review
Paste architecture (type END to finish):
E-commerce platform with React frontend, Node.js backend, PostgreSQL database
END

> chat What are the security risks?
[Agent provides detailed security analysis]

> compare arch1.md arch2.md
[Agent compares both architectures]
```

### Demo Mode

Run a pre-configured demo:

```bash
python run.py --demo
```

## 🏗️ How It Works

### ReAct Reasoning Loop

The agent follows a structured reasoning process:

```
┌─────────┐
│ Thought │  → Analyze what's needed for the review
└────┬────┘
     │
     ▼
┌─────────┐
│ Action  │  → Execute tools or sub-agents (RAG, security, etc.)
└────┬────┘
     │
     ▼
┌─────────────┐
│ Observation │  → Process results from tools
└────┬────────┘
     │
     ▼
┌────────────┐
│ Reflection │  → Validate completeness of analysis
└────┬───────┘
     │
     ▼
┌─────────┐
│ Answer  │  → Synthesize findings into recommendations
└─────────┘
```

### Multi-Agent Architecture

The system uses a coordinated approach with specialized agents:

- **Main Agent**: Orchestrates the review process using ReAct reasoning
- **Security Agent**: Analyzes authentication, authorization, encryption, OWASP compliance
- **Cost Agent**: Estimates infrastructure costs and identifies optimization opportunities
- **Performance Agent**: Evaluates bottlenecks, caching strategies, and scalability concerns
- **Graph Tool**: Extracts components and dependencies, identifies SPOFs

### Knowledge Base

The system uses RAG to retrieve relevant information from:

- Architecture Decision Records (ADRs)
- Design patterns and best practices
- Technology-specific guidance
- Security and compliance standards
- Cost optimization strategies

## 📁 Project Structure

```
Archai/
├── src/
│   ├── agent.py          # Main ReAct agent (core orchestration)
│   ├── mcp_client.py     # MCP client for server communication
│   ├── tools.py          # Tools (RAG, Graph analysis)
│   ├── sub_agents.py     # Specialist agents (Security, Cost, Performance)
│   ├── memory.py         # Conversation memory and persistence
│   └── utils.py          # Utilities (Logger, FileHandler)
├── mcp_servers/          # MCP servers (isolated processes)
│   ├── security_server.py
│   └── cost_server.py
├── tests/
│   └── test_all.py      # Test suite
├── data/
│   ├── md/              # Markdown documents for RAG
│   ├── pdf/             # PDF documents
│   └── scripts/
│       └── create_rag.py # RAG knowledge base creation
├── outputs/             # Generated reviews and traces
├── run.py              # CLI entry point
└── requirements.txt    # Python dependencies
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/test_all.py -v

# Run specific test
python -m pytest tests/test_all.py::TestSystem::test_graph -v
```

## 💡 Example Output

After reviewing an architecture, you receive:

- **Comprehensive Analysis**: Security, cost, performance, and scalability assessment
- **Specific Recommendations**: Actionable improvements with rationale
- **Risk Identification**: Single points of failure, bottlenecks, and vulnerabilities
- **Reasoning Trace**: Complete thought process showing how conclusions were reached
- **Exportable Reports**: Download reviews, traces, and full reports

**Sample Review Output:**

```
FINAL REVIEW:

Security Analysis:
- Critical: JWT tokens in localStorage vulnerable to XSS
- High: Single database instance creates SPOF
- Medium: Missing rate limiting on API Gateway

Cost Analysis:
- Estimated monthly cost: $4,200
- Optimization opportunity: Use reserved instances (save 30%)
- Idle resources: Lambda functions not optimized

Performance Analysis:
- Bottleneck: Single database instance
- Missing: No caching layer for read-heavy operations
- Recommendation: Add Redis cache, implement read replicas
```

## 🛠️ Technology Stack

- **LLM**: Claude Sonnet 4.5 (Anthropic)
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector Store**: Pinecone
- **Protocol**: Model Context Protocol (MCP)
- **Language**: Python 3.9+

## 🎓 Architecture Decision Process

The agent helps you:

1. **Validate Designs**: Check against established patterns and best practices
2. **Identify Risks**: Find security vulnerabilities, cost overruns, and performance issues
3. **Optimize Decisions**: Get recommendations for improvement
4. **Compare Alternatives**: Evaluate different architectural approaches
5. **Document Rationale**: Understand why certain decisions are recommended

## 🔧 Advanced Features

### Streaming Output

Enable real-time feedback during review:

```bash
> review --stream
```

Watch the agent think and execute tools in real-time.

### Self-Reflection

Enable self-critique for improved quality:

```bash
> review --reflect
```

The agent critiques its own analysis and provides improved recommendations.

### Memory Management

View and manage session memory:

```bash
> memory
Session ID: 20241113_120000
Total Entries: 45
Thoughts: 12
Actions: 8
Observations: 8

> save
Session saved to: outputs/memory_20241113_120000.json
```

## 📚 Use Cases

- **Architecture Reviews**: Comprehensive analysis of system designs
- **Design Validation**: Check decisions against best practices
- **Cost Optimization**: Identify and reduce infrastructure costs
- **Security Audits**: Find vulnerabilities and compliance issues
- **Performance Tuning**: Identify bottlenecks and optimization opportunities
- **Technology Selection**: Compare different architectural approaches

## 🤝 Contributing

This is a production-ready system demonstrating:

- Advanced AI agent architecture
- Multi-agent coordination patterns
- RAG implementation
- ReAct reasoning loops
- MCP protocol integration
- Production-grade error handling

## 📄 License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) file for details.
