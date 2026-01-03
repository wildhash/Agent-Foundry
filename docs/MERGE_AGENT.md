# MergeAgent - Automated PR Management and Branch Cleanup

## Overview

The MergeAgent is a specialized agent that automates pull request management and branch cleanup in GitHub repositories. It follows the Agent Foundry's BaseAgent pattern and includes reflexion loops for continuous improvement.

## Features

- ✅ **Automatic PR Merging**: Evaluates and merges eligible pull requests based on configurable criteria
- ✅ **CI/CD Integration**: Checks GitHub Actions and status checks before merging
- ✅ **Review Validation**: Ensures required approvals and no requested changes
- ✅ **Conflict Detection**: Skips PRs with merge conflicts
- ✅ **Branch Cleanup**: Removes stale branches to keep repository clean
- ✅ **Dry Run Mode**: Preview actions before making changes
- ✅ **Flexible Filtering**: Target specific PRs by label, author, or other criteria
- ✅ **Performance Tracking**: Built-in reflexion loops for self-improvement
- ✅ **Safe Defaults**: Conservative settings to prevent accidental merges

## Installation

### Prerequisites

- Python 3.9+
- PyGithub library
- GitHub Personal Access Token with repo permissions

### Install Dependencies

```bash
pip install -r requirements.txt
```

The MergeAgent requires PyGithub 2.1.1 or higher, which is included in the requirements.txt.

## Quick Start

### Basic Usage

```python
import asyncio
from agents.merge_agent import MergeAgent

async def main():
    # Initialize the agent
    agent = MergeAgent(
        agent_id="merger_1",
        github_token="ghp_your_token_here",
        repo_name="owner/repository"
    )
    
    # Configure merge criteria
    agent.configure(
        merge_strategy="squash",
        min_approvals=1,
        require_ci_pass=True
    )
    
    # Execute in dry run mode
    result = await agent.execute({
        "action": "both",  # merge_prs and cleanup_branches
        "dry_run": True
    })
    
    print(f"Would merge {len(result['merged_prs'])} PRs")
    print(f"Would clean {len(result['cleaned_branches'])} branches")

asyncio.run(main())
```

### Environment Variables

For production use, store credentials in environment variables:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_REPO="owner/repository"
```

Then initialize without explicit credentials:

```python
agent = MergeAgent(
    agent_id="merger_1",
    github_token=os.getenv("GITHUB_TOKEN"),
    repo_name=os.getenv("GITHUB_REPO")
)
```

## Configuration Options

### Merge Strategy

```python
agent.configure(merge_strategy="squash")  # Options: merge, squash, rebase
```

- **merge**: Creates a merge commit (default)
- **squash**: Squashes all commits into one
- **rebase**: Rebases and merges

### Approval Requirements

```python
agent.configure(min_approvals=2)  # Require 2 approvals before merging
```

### CI Requirements

```python
agent.configure(require_ci_pass=True)  # Require all CI checks to pass
```

### Stale Branch Settings

```python
agent.configure(stale_branch_days=90)  # Delete branches older than 90 days
```

## Usage Examples

### 1. Merge Dependabot PRs

```python
task = {
    "action": "merge_prs",
    "dry_run": False,
    "pr_filters": {
        "author": "dependabot[bot]"
    }
}

result = await agent.execute(task)
```

### 2. Merge PRs with Specific Labels

```python
task = {
    "action": "merge_prs",
    "dry_run": True,
    "pr_filters": {
        "labels": ["approved", "ready-to-merge"]
    }
}

result = await agent.execute(task)
```

### 3. Clean Up Stale Branches Only

```python
task = {
    "action": "cleanup_branches",
    "dry_run": True
}

result = await agent.execute(task)
```

### 4. Use Reflexion Loop for Improvement

```python
# Agent will iterate and improve its strategy
result = await agent.reflexion_loop(task, max_loops=5)

print(f"Best score: {result['score']}")
print(f"Iterations: {result['loops_executed']}")
```

## Mergeability Criteria

The agent checks multiple criteria before merging a PR:

1. ✅ **No Merge Conflicts**: PR must be mergeable
2. ✅ **Sufficient Approvals**: Must meet minimum approval count
3. ✅ **No Change Requests**: No reviewers requesting changes
4. ✅ **CI Passing**: All status checks and GitHub Actions must pass (if required)
5. ✅ **Not a Draft**: PR must not be in draft mode
6. ✅ **Mergeable State**: GitHub must report PR as ready to merge

If any criterion fails, the PR is skipped with a clear reason.

## Branch Cleanup

The agent identifies stale branches using these rules:

- ❌ **Protected branches** are never deleted (main, master, develop, etc.)
- ❌ **Branches with open PRs** are never deleted
- ✅ **Old branches** without activity are candidates for deletion
- ⚙️ **Configurable threshold** (default: 90 days)

## Result Structure

```python
{
    "success": True,
    "dry_run": False,
    "merged_prs": [
        {
            "number": 123,
            "title": "Update dependency",
            "author": "dependabot[bot]",
            "action": "merged"
        }
    ],
    "skipped_prs": [
        {
            "number": 124,
            "title": "Feature branch",
            "reason": "insufficient_approvals (0/1)"
        }
    ],
    "cleaned_branches": [
        {
            "name": "old-feature",
            "last_commit_date": "2024-01-01T00:00:00",
            "days_old": 100,
            "action": "deleted"
        }
    ],
    "errors": []
}
```

## Integration with Orchestrator

The MergeAgent can be integrated into the Agent Foundry orchestrator:

```python
from agents.orchestrator import AgentOrchestrator
from agents.merge_agent import MergeAgent

orchestrator = AgentOrchestrator()

# Add merge agent to pipeline
merge_agent = MergeAgent(
    agent_id="pipeline_merger",
    github_token=github_token,
    repo_name=repo_name
)

orchestrator.agents[merge_agent.agent_id] = merge_agent
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Auto-merge PRs

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
  workflow_dispatch:  # Manual trigger

jobs:
  auto-merge:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run MergeAgent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
        run: |
          python -c "
          import asyncio
          from agents.merge_agent import MergeAgent
          
          async def main():
              agent = MergeAgent(
                  agent_id='ci_merger',
                  github_token='${{ secrets.GITHUB_TOKEN }}',
                  repo_name='${{ github.repository }}'
              )
              agent.configure(merge_strategy='squash', min_approvals=1)
              result = await agent.execute({'action': 'both', 'dry_run': False})
              print(f\"Merged {len(result['merged_prs'])} PRs\")
          
          asyncio.run(main())
          "
```

## Performance Metrics

The agent tracks its own performance:

```python
# Get performance summary
summary = agent.get_performance_summary()

print(f"Average score: {summary['average_score']}")
print(f"Best score: {summary['best_score']}")
print(f"Total executions: {summary['total_executions']}")
```

Performance scoring:
- **Base score (0.3)**: Successful execution
- **Merge bonus (up to 0.3)**: For each PR merged
- **Cleanup bonus (up to 0.2)**: For each branch cleaned
- **Safety bonus (0.1)**: For properly skipping risky PRs
- **Error penalty (up to -0.3)**: For each error encountered

## Security Considerations

1. **Token Security**: Never hardcode GitHub tokens. Use environment variables or secrets management.

2. **Branch Protection**: The agent respects GitHub branch protection rules.

3. **Dry Run First**: Always test with `dry_run: True` before actual execution.

4. **Minimum Approvals**: Set appropriate approval requirements for your organization.

5. **CI Requirements**: Enable `require_ci_pass` to ensure quality gates.

## Troubleshooting

### Agent Not Merging PRs

Check the `skipped_prs` in the result for reasons:
- `insufficient_approvals`: Increase approvals or decrease `min_approvals`
- `ci_failed`: Fix failing tests
- `has_merge_conflicts`: Resolve conflicts manually
- `changes_requested`: Address reviewer feedback

### GitHub API Rate Limits

The PyGithub library respects rate limits. For high-volume usage:
- Use a GitHub App instead of personal token
- Implement caching for frequently accessed data
- Run agent less frequently

### Branch Deletion Failures

- Check if branch is protected
- Ensure token has sufficient permissions
- Verify branch doesn't have open PRs

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_merge_agent.py -v
```

Run with coverage:

```bash
pytest tests/test_merge_agent.py --cov=agents.merge_agent --cov-report=html
```

## Demo Script

A comprehensive demo is available:

```bash
cd backend
export GITHUB_TOKEN="your_token"
export GITHUB_REPO="owner/repo"
python demos/merge_agent_demo.py
```

The demo includes:
1. Dry run mode demonstration
2. Reflexion loop example
3. Dependabot PR merging
4. Branch cleanup only

## Contributing

Follow the guidelines in [CONTRIBUTING.md](../../CONTRIBUTING.md):

1. Write tests for new features
2. Run linters: `black .` and `flake8 .`
3. Ensure all tests pass: `pytest`
4. Create a descriptive PR

## License

This project is licensed under the MIT License - see [LICENSE](../../LICENSE) for details.

## Acknowledgments

- Built on the Agent Foundry framework
- Follows the BaseAgent pattern with reflexion loops
- Uses PyGithub for GitHub API integration

## Support

For issues or questions:
1. Check existing issues on GitHub
2. Review the troubleshooting section
3. Create a new issue with detailed information

---

**Note**: This agent is designed to be conservative and safe by default. Always test with `dry_run: True` before enabling automatic merging in production.
