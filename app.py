import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent import ArchitectureAgent
from utils import FileHandler
import json
from datetime import datetime

st.set_page_config(
    page_title="Architecture Reviewer & Recommender",
    page_icon="🏗️",
    layout="wide"
)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = None
    st.session_state.review_result = None
    st.session_state.chat_history = []

# Sidebar
with st.sidebar:
    st.title("Configuration")

    use_mcp = st.checkbox("Enable MCP Servers", value=True,
                          help="Use MCP servers for security and cost analysis")

    verbose = st.checkbox("Verbose Mode", value=False,
                         help="Show detailed reasoning steps")

    max_iterations = st.slider("Max Iterations", 3, 15, 10,
                               help="Maximum reasoning cycles")

    if st.button("Initialize Agent"):
        try:
            if use_mcp:
                st.session_state.agent = ArchitectureAgent(verbose=verbose, use_mcp=True)
                st.session_state.agent.__enter__()
            else:
                st.session_state.agent = ArchitectureAgent(verbose=verbose, use_mcp=False)
            st.success("Agent initialized successfully")
        except Exception as e:
            st.error(f"Error initializing agent: {str(e)}")

    st.divider()

    st.subheader("About")
    st.markdown("""
    **AI Architecture Reviewer**

    Features:
    - RAG-based knowledge retrieval
    - ReAct reasoning loop
    - Multi-agent coordination (MCP)
    - Graph dependency analysis
    - Self-reflection capability

    Built with: Claude, Pinecone, Anthropic MCP
    """)

# Main content
st.title("Architecture Reviewer & Recommender Agent")
st.markdown("---")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Review", "Chat", "Compare", "History"])

with tab1:
    st.header("Architecture Review")

    col1, col2 = st.columns([2, 1])

    with col1:
        input_method = st.radio("Input Method", ["Paste Text", "Upload File"])

        if input_method == "Paste Text":
            architecture = st.text_area(
                "Architecture Description",
                height=300,
                placeholder="Paste your architecture description here...\n\nExample:\nE-commerce platform:\n- Frontend: React on S3\n- Backend: Node.js on ECS\n- Database: PostgreSQL RDS\n..."
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

        use_reflection = st.checkbox("Enable Self-Reflection", value=False,
                                     help="Agent will critique and improve its own analysis")

    with col2:
        st.subheader("Review Options")

        if st.button("Start Review", type="primary", disabled=not st.session_state.agent):
            if not architecture:
                st.error("Please provide architecture description")
            else:
                with st.spinner("Reviewing architecture..."):
                    try:
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
                        st.success("Review complete!")
                    except Exception as e:
                        st.error(f"Error during review: {str(e)}")

        if st.session_state.review_result:
            st.metric("Status", st.session_state.review_result["status"])
            st.metric("Iterations", len(st.session_state.review_result["trace"]["thoughts"]))

    # Display results
    if st.session_state.review_result:
        st.markdown("---")
        st.subheader("Review Results")

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Thoughts", len(st.session_state.review_result["trace"]["thoughts"]))
        with col2:
            st.metric("Actions", len(st.session_state.review_result["trace"]["actions"]))
        with col3:
            st.metric("Observations", len(st.session_state.review_result["trace"]["observations"]))
        with col4:
            st.metric("Status", st.session_state.review_result["status"])

        # Final answer
        st.markdown("### Final Review")
        st.markdown(st.session_state.review_result["final_answer"])

        # Reasoning trace (expandable)
        with st.expander("View Reasoning Trace"):
            st.subheader("Thoughts")
            for i, thought in enumerate(st.session_state.review_result["trace"]["thoughts"], 1):
                st.text(f"{i}. {thought}")

            st.subheader("Actions Executed")
            for i, action in enumerate(st.session_state.review_result["trace"]["actions"], 1):
                st.text(f"{i}. {action}")

        # Download results
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download Review (TXT)",
                data=st.session_state.review_result["final_answer"],
                file_name=f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
        with col2:
            st.download_button(
                "Download Trace (JSON)",
                data=json.dumps(st.session_state.review_result, indent=2),
                file_name=f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

with tab2:
    st.header("Chat with Agent")

    if not st.session_state.agent or not st.session_state.agent.memory.has_architecture():
        st.warning("Please complete an architecture review first")
    else:
        # Display chat history
        for chat in st.session_state.chat_history:
            with st.chat_message(chat["role"]):
                st.write(chat["content"])

        # Chat input
        if prompt := st.chat_input("Ask about the architecture..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = st.session_state.agent.chat(prompt)
                        st.write(response)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

with tab3:
    st.header("Compare Architectures")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Architecture 1")
        arch1_input = st.radio("Input Method", ["Paste", "Upload"], key="arch1_method")

        if arch1_input == "Paste":
            arch1 = st.text_area("Architecture 1", height=200, key="arch1_text")
        else:
            file1 = st.file_uploader("Upload Architecture 1", type=["txt", "md"], key="file1")
            arch1 = file1.read().decode() if file1 else None

    with col2:
        st.subheader("Architecture 2")
        arch2_input = st.radio("Input Method", ["Paste", "Upload"], key="arch2_method")

        if arch2_input == "Paste":
            arch2 = st.text_area("Architecture 2", height=200, key="arch2_text")
        else:
            file2 = st.file_uploader("Upload Architecture 2", type=["txt", "md"], key="file2")
            arch2 = file2.read().decode() if file2 else None

    if st.button("Compare Architectures", disabled=not st.session_state.agent):
        if not arch1 or not arch2:
            st.error("Please provide both architectures")
        else:
            with st.spinner("Comparing..."):
                try:
                    comparison = st.session_state.agent.compare(arch1, arch2)
                    st.markdown("### Comparison Results")
                    st.markdown(comparison)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with tab4:
    st.header("Session History")

    if st.session_state.agent and st.session_state.agent.memory:
        summary = st.session_state.agent.memory.get_summary()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Entries", summary["total_entries"])
        with col2:
            st.metric("Thoughts", summary["thoughts"])
        with col3:
            st.metric("Actions", summary["actions"])

        st.markdown("---")

        if summary["has_architecture"]:
            st.subheader("Current Architecture")
            arch = st.session_state.agent.memory.get_architecture()
            st.text_area("Architecture", arch, height=150, disabled=True)

        st.markdown("---")

        st.subheader("Recent History")
        for entry in st.session_state.agent.memory.history[-10:]:
            with st.expander(f"[{entry['role']}] {entry['timestamp']}"):
                st.text(entry['content'][:500])

        if st.button("Clear Memory"):
            st.session_state.agent.memory.clear()
            st.session_state.chat_history = []
            st.success("Memory cleared")
            st.rerun()

