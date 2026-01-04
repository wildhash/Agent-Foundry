"""
Demo script for MergeAgent usage

This script demonstrates how to use the MergeAgent to automatically
manage pull requests and clean up stale branches.
"""

import asyncio
import os
from agents.merge_agent import MergeAgent


async def demo_merge_agent_dry_run():
    """Demonstrate MergeAgent in dry run mode"""
    print("=" * 70)
    print("MergeAgent Demo - Dry Run Mode")
    print("=" * 70)
    print()

    # Initialize the merge agent
    # In production, use environment variables or secure configuration
    github_token = os.getenv("GITHUB_TOKEN", "your-github-token")
    repo_name = os.getenv("GITHUB_REPO", "owner/repository")

    agent = MergeAgent(agent_id="demo_merger_1", github_token=github_token, repo_name=repo_name)

    # Configure the agent
    agent.configure(
        merge_strategy="squash",  # Options: merge, squash, rebase
        stale_branch_days=90,  # Days before considering a branch stale
        min_approvals=1,  # Minimum number of approvals required
        require_ci_pass=True,  # Require CI to pass before merging
    )

    print(f"Agent configured:")
    print(f"  - Merge strategy: {agent.merge_strategy}")
    print(f"  - Stale branch days: {agent.stale_branch_days}")
    print(f"  - Min approvals: {agent.min_approvals}")
    print(f"  - Require CI pass: {agent.require_ci_pass}")
    print()

    # Execute in dry run mode to see what would happen
    print("Executing merge agent in DRY RUN mode...")
    print("(No actual changes will be made)")
    print()

    task = {
        "action": "both",  # Options: merge_prs, cleanup_branches, both
        "dry_run": True,
        "pr_filters": {
            # Optional: Filter PRs by labels
            # "labels": ["approved", "ready-to-merge"],
            # Optional: Filter PRs by author
            # "author": "dependabot[bot]",
        },
    }

    result = await agent.execute(task)

    # Display results
    print("Execution Results:")
    print("-" * 70)
    print(f"Success: {result['success']}")
    print()

    if result.get("merged_prs"):
        print(f"Pull Requests that would be merged ({len(result['merged_prs'])}):")
        for pr in result["merged_prs"]:
            print(f"  - PR #{pr['number']}: {pr['title']}")
            print(f"    Author: {pr['author']}")
            print(f"    Action: {pr['action']}")
        print()

    if result.get("skipped_prs"):
        print(f"Pull Requests skipped ({len(result['skipped_prs'])}):")
        for pr in result["skipped_prs"]:
            print(f"  - PR #{pr['number']}: {pr['title']}")
            print(f"    Reason: {pr['reason']}")
        print()

    if result.get("cleaned_branches"):
        print(f"Branches that would be cleaned up ({len(result['cleaned_branches'])}):")
        for branch in result["cleaned_branches"]:
            print(f"  - {branch['name']}")
            print(f"    Last commit: {branch['last_commit_date']}")
            print(f"    Age: {branch['days_old']} days")
        print()

    if result.get("errors"):
        print(f"Errors encountered ({len(result['errors'])}):")
        for error in result["errors"]:
            print(f"  - {error}")
        print()

    # Evaluate performance
    score = await agent.evaluate_performance(result)
    print(f"Performance Score: {score:.2f}/1.00")
    print()


async def demo_merge_agent_with_reflexion():
    """Demonstrate MergeAgent with reflexion loop"""
    print("=" * 70)
    print("MergeAgent Demo - Reflexion Loop")
    print("=" * 70)
    print()

    github_token = os.getenv("GITHUB_TOKEN", "your-github-token")
    repo_name = os.getenv("GITHUB_REPO", "owner/repository")

    agent = MergeAgent(agent_id="demo_merger_2", github_token=github_token, repo_name=repo_name)

    # Configure for conservative merging
    agent.configure(merge_strategy="squash", min_approvals=2, require_ci_pass=True)

    print("Executing with reflexion loop (max 3 iterations)...")
    print("Agent will learn and adjust strategy based on performance")
    print()

    task = {
        "action": "merge_prs",
        "dry_run": True,
        "pr_filters": {
            "labels": ["approved"],
        },
    }

    # Use reflexion loop for iterative improvement
    result = await agent.reflexion_loop(task, max_loops=3)

    print("Reflexion Loop Results:")
    print("-" * 70)
    print(f"Best score: {result['score']:.2f}")
    print(f"Loops executed: {result['loops_executed']}")
    print(f"Agent generation: {agent.generation}")
    print()

    # Display performance summary
    perf_summary = agent.get_performance_summary()
    print("Performance Summary:")
    print(f"  - Average score: {perf_summary['average_score']:.2f}")
    print(f"  - Best score: {perf_summary['best_score']:.2f}")
    print(f"  - Total executions: {perf_summary['total_executions']}")
    print()


async def demo_merge_specific_prs():
    """Demonstrate merging specific PRs with filters"""
    print("=" * 70)
    print("MergeAgent Demo - Merge Dependabot PRs")
    print("=" * 70)
    print()

    github_token = os.getenv("GITHUB_TOKEN", "your-github-token")
    repo_name = os.getenv("GITHUB_REPO", "owner/repository")

    agent = MergeAgent(agent_id="demo_merger_3", github_token=github_token, repo_name=repo_name)

    # Configure for automatic Dependabot PR merging
    agent.configure(
        merge_strategy="squash",
        min_approvals=0,  # Dependabot PRs may not need manual approval
        require_ci_pass=True,  # But CI must pass
    )

    print("Targeting Dependabot PRs for automatic merging...")
    print()

    task = {
        "action": "merge_prs",
        "dry_run": False,  # Actually merge PRs
        "pr_filters": {
            "author": "dependabot[bot]",  # Only Dependabot PRs
        },
    }

    result = await agent.execute(task)

    print("Results:")
    print(f"  - Merged: {len(result.get('merged_prs', []))} PRs")
    print(f"  - Skipped: {len(result.get('skipped_prs', []))} PRs")
    print()

    if result.get("merged_prs"):
        print("Successfully merged:")
        for pr in result["merged_prs"]:
            print(f"  - PR #{pr['number']}: {pr['title']}")


async def demo_branch_cleanup():
    """Demonstrate branch cleanup only"""
    print("=" * 70)
    print("MergeAgent Demo - Branch Cleanup")
    print("=" * 70)
    print()

    github_token = os.getenv("GITHUB_TOKEN", "your-github-token")
    repo_name = os.getenv("GITHUB_REPO", "owner/repository")

    agent = MergeAgent(agent_id="demo_merger_4", github_token=github_token, repo_name=repo_name)

    # Configure for aggressive cleanup
    agent.configure(stale_branch_days=60)  # Delete branches older than 60 days

    print(f"Cleaning up branches older than {agent.stale_branch_days} days...")
    print()

    task = {"action": "cleanup_branches", "dry_run": True}

    result = await agent.execute(task)

    if result.get("cleaned_branches"):
        print(f"Branches to be cleaned up ({len(result['cleaned_branches'])}):")
        for branch in result["cleaned_branches"]:
            print(f"  - {branch['name']} (age: {branch['days_old']} days)")
    else:
        print("No stale branches found.")
    print()


async def main():
    """Run all demos"""
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║           MergeAgent - Automated PR Management Demo               ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()

    # Check if credentials are configured
    if not os.getenv("GITHUB_TOKEN"):
        print("⚠️  WARNING: GITHUB_TOKEN environment variable not set")
        print("   Set it to enable actual GitHub API integration")
        print("   Example: export GITHUB_TOKEN='ghp_your_token_here'")
        print()

    if not os.getenv("GITHUB_REPO"):
        print("⚠️  WARNING: GITHUB_REPO environment variable not set")
        print("   Set it to enable actual GitHub API integration")
        print("   Example: export GITHUB_REPO='owner/repository'")
        print()

    print("Select a demo to run:")
    print("  1. Dry run mode (safe, no changes)")
    print("  2. Reflexion loop demonstration")
    print("  3. Merge Dependabot PRs")
    print("  4. Branch cleanup only")
    print("  5. Run all demos")
    print()

    choice = input("Enter choice (1-5): ").strip()

    if choice == "1":
        await demo_merge_agent_dry_run()
    elif choice == "2":
        await demo_merge_agent_with_reflexion()
    elif choice == "3":
        await demo_merge_specific_prs()
    elif choice == "4":
        await demo_branch_cleanup()
    elif choice == "5":
        await demo_merge_agent_dry_run()
        await demo_merge_agent_with_reflexion()
        await demo_branch_cleanup()
    else:
        print("Invalid choice. Running dry run demo...")
        await demo_merge_agent_dry_run()

    print()
    print("=" * 70)
    print("Demo completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
