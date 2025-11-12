import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent import ArchitectureAgent
from utils import FileHandler
import json
from datetime import datetime
import io

st.set_page_config(
    page_title="Archai - AI Architecture Reviewer",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stAlert {margin-top: 1rem;}
    .reasoning-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .tool-execution {
        background-color: #e8f4f8;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = None
    st.session_state.review_result = None
    st.session_state.chat_history = []
    st.session_state.reasoning_log = []
    st.session_state.initialized = False

# Sidebar configuration
with st.sidebar:
    st.title("Configuration")

    st.markdown("""
    **Archai** - AI Architecture Reviewer

    Autonomous agent for architecture review using RAG, ReAct reasoning, and multi-agent coordination.
    """)

    st.divider()

    st.subheader("Agent Settings")

    use_mcp = st.checkbox(
        "Enable MCP Servers",
        value=True,
        help="Use Model Context Protocol servers for security and cost analysis"
    )

    verbose = st.checkbox(
        "Verbose Mode",
        value=True,
        help="Show detailed reasoning steps and tool executions"
    )

    max_iterations = st.slider(
        "Max Iterations",
        min_value=3,
        max_value=15,
        value=10,
        help="Maximum reasoning cycles"
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Initialize", type="primary", use_container_width=True):
            st.session_state.reasoning_log = []
            try:
                if use_mcp:
                    agent = ArchitectureAgent(verbose=verbose, use_mcp=True)
                    agent.__enter__()
                    st.session_state.agent = agent
                else:
                    st.session_state.agent = ArchitectureAgent(verbose=verbose, use_mcp=False)

                st.session_state.initialized = True
                st.success("Agent initialized")
            except Exception as e:
                st.error(f"Initialization error: {str(e)}")

    with col2:
        if st.button("Reset", use_container_width=True):
            if st.session_state.agent:
                try:
                    if hasattr(st.session_state.agent, '__exit__'):
                        st.session_state.agent.__exit__(None, None, None)
                except:
                    pass

            st.session_state.agent = None
            st.session_state.review_result = None
            st.session_state.chat_history = []
            st.session_state.reasoning_log = []
            st.session_state.initialized = False
            st.success("Reset complete")
            st.rerun()

    if st.session_state.initialized:
        st.divider()
        st.subheader("Session Stats")
        if st.session_state.agent and st.session_state.agent.memory:
            summary = st.session_state.agent.memory.get_summary()
            st.metric("Total Entries", summary["total_entries"])
            st.metric("Reasoning Steps", summary["thoughts"])
            st.metric("Tool Executions", summary["actions"])

    st.divider()

    st.markdown("""
    **Capabilities**

    - RAG: Knowledge retrieval from architecture patterns
    - ReAct: Structured reasoning (Thought → Action → Observation)
    - MCP: Multi-agent coordination for specialized analysis
    - Graph Analysis: Dependency and failure point detection
    """)

# Main header
st.title("Archai - AI Architecture Reviewer")
st.markdown("Autonomous architecture reasoning agent for reviewing decisions and recommending improvements.")

if not st.session_state.initialized:
    st.warning("Please initialize the agent from the sidebar to begin")
    st.stop()

st.markdown("---")

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Review",
    "Chat",
    "Compare",
    "Reasoning Trace",
    "History"
])

# Tab 1: Architecture Review
with tab1:
    st.header("Architecture Review")

    col1, col2 = st.columns([2, 1])

    with col1:
        input_method = st.radio("Input Method", ["Paste Text", "Upload File"])

        if input_method == "Paste Text":
            architecture = st.text_area(
                "Architecture Description",
                height=300,
                placeholder="""E-commerce Platform Architecture:

Infrastructure:
- Frontend: React SPA on S3 + CloudFront
- API Gateway: AWS API Gateway with Lambda authorizers
- Services: 5 microservices on ECS Fargate
- Database: RDS PostgreSQL (db.t3.large)
- Cache: None
- Authentication: JWT in localStorage

Requirements:
- Load: 10,000 requests/minute peak
- Availability: 99.9% uptime
- Budget: $5000/month
- Compliance: PCI DSS
"""
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload Architecture Document",
                type=["txt", "md", "pdf"]
            )
            architecture = None
            if uploaded_file:
                try:
                    if uploaded_file.type == "application/pdf":
                        import PyPDF2
                        from io import BytesIO
                        pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))
                        architecture = ""
                        for page in pdf_reader.pages:
                            architecture += page.extract_text() + "\n\n"
                    else:
                        architecture = uploaded_file.read().decode()
                    st.success(f"Loaded {len(architecture)} characters")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")

    with col2:
        st.subheader("Options")

        use_reflection = st.checkbox(
            "Self-Reflection",
            value=False,
            help="Agent critiques and improves its analysis"
        )

        show_reasoning = st.checkbox(
            "Show Reasoning",
            value=verbose,
            help="Display reasoning steps in real-time"
        )

        st.markdown("---")

        if st.button("Start Review", type="primary", use_container_width=True):
            if not architecture:
                st.error("Please provide architecture description")
            else:
                st.session_state.reasoning_log = []

                status_container = st.empty()
                reasoning_container = st.container()

                status_container.info("Analyzing architecture...")

                class StreamCapture:
                    def __init__(self):
                        self.logs = []

                    def write(self, text):
                        if text.strip():
                            self.logs.append(text)
                            st.session_state.reasoning_log.append(text)

                    def flush(self):
                        pass

                if show_reasoning:
                    old_stdout = sys.stdout
                    sys.stdout = StreamCapture()

                try:
                    with reasoning_container:
                        if use_reflection:
                            result = st.session_state.agent.review_with_reflection(
                                architecture,
                                max_iterations=max_iterations
                            )
                        else:
                            result = st.session_state.agent.review(
                                architecture,
                                max_iterations=max_iterations
                            )

                    st.session_state.review_result = result

                    if show_reasoning:
                        sys.stdout = old_stdout

                    status_container.success("Review complete")

                except Exception as e:
                    if show_reasoning:
                        sys.stdout = old_stdout
                    status_container.error(f"Error: {str(e)}")
                    st.exception(e)

    # Display reasoning log
    if st.session_state.reasoning_log and show_reasoning:
        st.markdown("---")
        with st.expander("Reasoning Process", expanded=True):
            for log in st.session_state.reasoning_log:
                if "ITERATION" in log:
                    st.markdown(f"**{log.strip()}**")
                elif "THOUGHT:" in log:
                    st.markdown(f'<div class="reasoning-box">{log.strip()}</div>', unsafe_allow_html=True)
                elif "EXECUTING TOOL:" in log or "EXECUTING:" in log:
                    st.markdown(f'<div class="tool-execution">{log.strip()}</div>', unsafe_allow_html=True)
                elif "OBSERVATION" in log:
                    st.markdown(f"**{log.strip()}**")
                else:
                    st.text(log.strip())

    # Display results
    if st.session_state.review_result:
        st.markdown("---")
        st.subheader("Review Results")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Thoughts", len(st.session_state.review_result["trace"]["thoughts"]))
        with col2:
            st.metric("Actions", len(st.session_state.review_result["trace"]["actions"]))
        with col3:
            st.metric("Observations", len(st.session_state.review_result["trace"]["observations"]))
        with col4:
            status = st.session_state.review_result["status"]
            st.metric("Status", status.upper())

        st.markdown("---")

        st.markdown("### Final Review")
        st.markdown(st.session_state.review_result["final_answer"])

        if "reflection" in st.session_state.review_result:
            with st.expander("Self-Reflection"):
                st.markdown(st.session_state.review_result["reflection"])

        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                "Download Review (TXT)",
                data=st.session_state.review_result["final_answer"],
                file_name=f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        with col2:
            st.download_button(
                "Download Trace (JSON)",
                data=json.dumps(st.session_state.review_result, indent=2),
                file_name=f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

        with col3:
            full_report = f"""Architecture Review Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*70}
SUMMARY
{'='*70}

Status: {st.session_state.review_result['status']}
Reasoning Steps: {len(st.session_state.review_result['trace']['thoughts'])}
Tools Used: {len(st.session_state.review_result['trace']['actions'])}

{'='*70}
FINAL REVIEW
{'='*70}

{st.session_state.review_result['final_answer']}

{'='*70}
REASONING TRACE
{'='*70}

Thoughts:

{chr(10).join([f"{i}. {t}" for i, t in enumerate(st.session_state.review_result['trace']['thoughts'], 1)])}

Actions Executed:

{chr(10).join([f"{i}. {a}" for i, a in enumerate(st.session_state.review_result['trace']['actions'], 1)])}
"""

            st.download_button(
                "Download Full Report",
                data=full_report,
                file_name=f"full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

# Tab 2: Chat
with tab2:
    st.header("Chat & Q&A")

    if not st.session_state.agent or not st.session_state.agent.memory.has_architecture():
        st.warning("Please complete an architecture review first")
    else:
        st.markdown("**Quick Questions:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Top 3 Security Risks", use_container_width=True):
                prompt = "What are the top 3 security risks in this architecture?"
                st.session_state.chat_history.append({"role": "user", "content": prompt})

        with col2:
            if st.button("Performance Improvements", use_container_width=True):
                prompt = "What are the main performance bottlenecks and how can we improve them?"
                st.session_state.chat_history.append({"role": "user", "content": prompt})

        with col3:
            if st.button("Cost Estimate", use_container_width=True):
                prompt = "Provide a detailed breakdown of estimated monthly costs"
                st.session_state.chat_history.append({"role": "user", "content": prompt})

        st.markdown("---")

        for chat in st.session_state.chat_history:
            with st.chat_message(chat["role"]):
                st.markdown(chat["content"])

        if prompt := st.chat_input("Ask about the architecture..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = st.session_state.agent.chat(prompt)
                        st.markdown(response)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        if st.session_state.chat_history:
            if st.button("Clear Chat History"):
                st.session_state.chat_history = []
                st.rerun()

# Tab 3: Compare
with tab3:
    st.header("Compare Architectures")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Architecture 1")
        arch1_method = st.radio("Input Method", ["Paste", "Upload"], key="arch1_method")

        if arch1_method == "Paste":
            arch1 = st.text_area("Architecture 1", height=250, key="arch1_text")
        else:
            file1 = st.file_uploader("Upload Architecture 1", type=["txt", "md"], key="file1")
            arch1 = file1.read().decode() if file1 else None

    with col2:
        st.subheader("Architecture 2")
        arch2_method = st.radio("Input Method", ["Paste", "Upload"], key="arch2_method")

        if arch2_method == "Paste":
            arch2 = st.text_area("Architecture 2", height=250, key="arch2_text")
        else:
            file2 = st.file_uploader("Upload Architecture 2", type=["txt", "md"], key="file2")
            arch2 = file2.read().decode() if file2 else None

    if st.button("Compare Architectures", type="primary", use_container_width=True):
        if not arch1 or not arch2:
            st.error("Please provide both architectures")
        else:
            with st.spinner("Comparing..."):
                try:
                    comparison = st.session_state.agent.compare(arch1, arch2)
                    st.markdown("---")
                    st.subheader("Comparison Results")
                    st.markdown(comparison)
                    st.download_button(
                        "Download Comparison",
                        data=comparison,
                        file_name=f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Tab 4: Reasoning Trace
with tab4:
    st.header("Reasoning Trace")

    if st.session_state.review_result:
        trace = st.session_state.review_result["trace"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Thoughts", len(trace["thoughts"]))
        with col2:
            st.metric("Tool Executions", len(trace["actions"]))
        with col3:
            st.metric("Observations", len(trace["observations"]))

        st.markdown("---")

        with st.expander("Reasoning Thoughts", expanded=True):
            for i, thought in enumerate(trace["thoughts"], 1):
                st.markdown(f"**Step {i}:**")
                st.info(thought)

        with st.expander("Actions Executed"):
            for i, action in enumerate(trace["actions"], 1):
                st.markdown(f"{i}. `{action}`")

        with st.expander("Observations"):
            for i, obs in enumerate(trace["observations"], 1):
                st.markdown(f"**Observation {i}:**")
                st.text_area(f"obs_{i}", obs[:500], height=100, disabled=True, label_visibility="collapsed")
    else:
        st.info("Complete an architecture review to see the reasoning trace")

# Tab 5: History
with tab5:
    st.header("Session History")

    if st.session_state.agent and st.session_state.agent.memory:
        summary = st.session_state.agent.memory.get_summary()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Session ID", summary["session_id"][:8])
        with col2:
            st.metric("Total Entries", summary["total_entries"])
        with col3:
            st.metric("Reasoning Steps", summary["thoughts"])
        with col4:
            st.metric("Tool Executions", summary["actions"])

        st.markdown("---")

        if summary["has_architecture"]:
            st.subheader("Current Architecture")
            arch = st.session_state.agent.memory.get_architecture()
            st.text_area("Architecture", arch[:1000], height=150, disabled=True)

        st.markdown("---")

        st.subheader("Recent Activity")
        history_limit = st.slider("Entries to show", 5, 50, 20)

        for entry in st.session_state.agent.memory.history[-history_limit:]:
            role = entry['role']
            timestamp = entry['timestamp'].split('T')[1].split('.')[0]

            if role == "thought":
                st.markdown(f"**[{timestamp}] Thought:**")
                st.info(entry['content'][:300])
            elif role == "action":
                st.markdown(f"**[{timestamp}] Action:**")
                st.success(entry['content'])
            elif role == "observation":
                st.markdown(f"**[{timestamp}] Observation:**")
                with st.expander("View details"):
                    st.text(entry['content'])
            else:
                st.markdown(f"**[{timestamp}] {role}:**")
                st.text(entry['content'][:200])

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Memory", type="secondary", use_container_width=True):
                st.session_state.agent.memory.clear()
                st.session_state.chat_history = []
                st.session_state.review_result = None
                st.session_state.reasoning_log = []
                st.success("Memory cleared")
                st.rerun()

        with col2:
            if st.button("Export Session", use_container_width=True):
                try:
                    saved = st.session_state.agent.memory.save_to_file(st.session_state.review_result)
                    st.success("Session exported")
                    st.json(saved)
                except Exception as e:
                    st.error(f"Export error: {str(e)}")
    else:
        st.info("Initialize the agent to start tracking session history")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Archai - AI Architecture Reviewer</strong></p>
    <p>Built with ❤️ by <a href="https://github.com/hastagAB" target="_blank">Ayush Bhardwaj</a></p>
    <p><a href="https://github.com/hastagAB/Archai" target="_blank">View on GitHub</a></p>
</div>
""", unsafe_allow_html=True)
