#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent import ArchitectureAgent
from utils import FileHandler


def interactive():
    agent = ArchitectureAgent(verbose=True)

    print("="*70)
    print("Architecture Reviewer - Interactive Mode")
    print("="*70)
    print("\nCommands: review | chat | compare | upload | memory | clear | exit")
    print("="*70)

    while True:
        try:
            cmd = input("\n> ").strip()

            if cmd == "exit":
                break

            elif cmd == "memory":
                summary = agent.memory.get_summary()
                print(f"\nMemory: {summary}")

            elif cmd == "clear":
                agent.memory.clear()
                print("Memory cleared")

            elif cmd.startswith("review"):
                parts = cmd.split(maxsplit=1)
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

                result = agent.review(arch)
                print(f"\n{'='*70}")
                print("REVIEW COMPLETE")
                print(f"{'='*70}")
                print(result["final_answer"])

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
    print("Architecture Reviewer - Demo Mode")
    print("="*70)

    agent = ArchitectureAgent(verbose=True)

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
