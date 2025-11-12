#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent import ArchitectureAgent
from utils import FileHandler


def interactive():
    print("="*70)
    print("Architecture Reviewer - Interactive Mode (with MCP)")
    print("="*70)
    print("\nCommands:")
    print("  review              - Review architecture")
    print("  review --reflect    - Review with self-reflection")
    print("  review --stream     - Review with streaming output")
    print("  chat <message>      - Chat about architecture")
    print("  compare <file1> <file2> - Compare two architectures")
    print("  upload <filepath>   - Upload and review file")
    print("  memory              - Show memory summary")
    print("  save                - Save session to file")
    print("  clear               - Clear memory")
    print("  exit                - Exit interactive mode")
    print("="*70)

    with ArchitectureAgent(verbose=True, use_mcp=True) as agent:
        while True:
            try:
                cmd = input("\n> ").strip()

                if cmd == "exit":
                    break

                elif cmd == "memory":
                    summary = agent.memory.get_summary()
                    print(f"\n{'='*70}")
                    print("MEMORY SUMMARY")
                    print(f"{'='*70}")
                    print(f"Session ID: {summary['session_id']}")
                    print(f"Total Entries: {summary['total_entries']}")
                    print(f"Has Architecture: {summary['has_architecture']}")
                    print(f"Thoughts: {summary['thoughts']}")
                    print(f"Actions: {summary['actions']}")
                    print(f"Observations: {summary['observations']}")

                    if summary['has_architecture']:
                        arch = agent.memory.get_architecture()
                        print(f"\nArchitecture Preview:")
                        print(arch[:200] + "..." if len(arch) > 200 else arch)

                    # Show recent history
                    print(f"\n{'='*70}")
                    print("RECENT HISTORY (last 5 entries)")
                    print(f"{'='*70}")
                    for entry in agent.memory.history[-5:]:
                        role = entry['role']
                        content = entry['content'][:100]
                        timestamp = entry['timestamp']
                        print(f"[{timestamp}] {role}: {content}...")

                elif cmd == "save":
                    saved = agent.memory.save_to_file()
                    print(f"\nSession saved:")
                    for file_type, filepath in saved.items():
                        if filepath:
                            print(f"  {file_type}: {filepath}")

                elif cmd == "clear":
                    agent.memory.clear()
                    print("Memory cleared")

                elif cmd.startswith("review"):
                    parts = cmd.split()
                    use_reflection = "--reflect" in parts
                    use_streaming = "--stream" in parts

                    # Remove flags from parts for processing
                    parts = [p for p in parts if p not in ["--reflect", "--stream"]]

                    if len(parts) == 1:
                        print("\nPaste architecture (type END to finish):")
                        lines = []
                        while True:
                            line = input()
                            if line == "END":
                                break
                            lines.append(line)
                        arch = "\n".join(lines)
                    else:
                        filepath = parts[1]
                        if Path(filepath).exists():
                            arch = FileHandler.read_file(filepath)
                        else:
                            arch = parts[1]

                    print(f"\nStarting review (with reflection: {use_reflection})...")
                    
                    if use_streaming:
                        result = agent.review_streaming(arch)
                    elif use_reflection:
                        result = agent.review_with_reflection(arch)
                    else:
                        result = agent.review(arch)
                    
                    print(f"\n{'='*70}")
                    print("REVIEW COMPLETE")
                    print(f"{'='*70}")
                    print(result["final_answer"])
                    
                    if "reflection" in result:
                        print(f"\n{'='*70}")
                        print("SELF-CRITIQUE")
                        print(f"{'='*70}")
                        print(result["reflection"])

                    # Show saved files
                    if "saved_files" in result:
                        print(f"\n{'='*70}")
                        print("FILES SAVED")
                        print(f"{'='*70}")
                        for file_type, filepath in result["saved_files"].items():
                            if filepath:
                                print(f"{file_type}: {filepath}")

                elif cmd.startswith("chat"):
                    message = cmd.split(maxsplit=1)[1] if len(cmd.split()) > 1 else ""
                    if not message:
                        print("Usage: chat <message>")
                        continue
                    response = agent.chat(message)
                    print(f"\nAssistant: {response}")

                elif cmd.startswith("upload"):
                    filepath = cmd.split(maxsplit=1)[1] if len(cmd.split()) > 1 else ""
                    if not filepath:
                        print("Usage: upload <filepath>")
                        continue
                    arch = FileHandler.read_file(filepath)
                    result = agent.review(arch)
                    print(f"\n{'='*70}")
                    print("REVIEW COMPLETE")
                    print(f"{'='*70}")
                    print(result["final_answer"])

                    # Show saved files
                    if "saved_files" in result:
                        print(f"\n{'='*70}")
                        print("FILES SAVED")
                        print(f"{'='*70}")
                        for file_type, filepath in result["saved_files"].items():
                            if filepath:
                                print(f"{file_type}: {filepath}")

                elif cmd.startswith("compare"):
                    parts = cmd.split()

                    if len(parts) < 3:
                        print("Usage: compare <file1> <file2>")
                        continue
                    arch1 = FileHandler.read_file(parts[1])
                    arch2 = FileHandler.read_file(parts[2])
                    result = agent.compare(arch1, arch2)
                    print(f"\n{'='*70}")
                    print("COMPARISON")
                    print(f"{'='*70}")
                    print(result)

                else:
                    print("Unknown command")

            except Exception as e:
                print(f"Error: {e}")


def demo():
    print("="*70)
    print("Architecture Reviewer - Demo Mode (with MCP)")
    print("="*70)

    architecture = """
    E-commerce platform:
    - Frontend: React on S3 + CloudFront
    - API Gateway: AWS API Gateway
    - Services: 5 microservices on ECS
    - Database: Single RDS PostgreSQL
    - Cache: None
    - Auth: JWT in localStorage
    - Load: 10k requests/min
    - Budget: $5000/month
    """

    with ArchitectureAgent(verbose=True, use_mcp=True) as agent:
        result = agent.review(architecture)

        print(f"\n{'='*70}")
        print("FINAL REVIEW")
        print(f"{'='*70}")
        print(result["final_answer"])


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run.py --demo")
        print("  python run.py --interactive")
        return

    if sys.argv[1] == "--demo":
        demo()
    elif sys.argv[1] == "--interactive":
        interactive()


if __name__ == "__main__":
    main()
