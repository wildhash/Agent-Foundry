# Merge Agent Documentation

## Overview

The Merge Agent is an automated agent that manages pull requests and branch cleanup in GitHub repositories. It follows the Agent Foundry's BaseAgent pattern with reflexion loops and performance tracking.

## Features

- **Automated PR Merging**: Evaluates and merges pull requests based on configurable criteria
- **CI/CD Integration**: Checks CI status before merging
- **Approval Tracking**: Requires minimum number of approvals
- **Merge Conflict Detection**: Prevents merging PRs with conflicts
- **Stale Branch Cleanup**: Identifies stale branches for cleanup
- **Reflexion Loops**: Self-improves based on performance
- **Multiple Merge Strategies**: Supports squash, merge, and rebase

## Configuration

### Environment Variables

Add the following to your `.env` file or environment:

```bash
# Required for Merge Agent
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO_OWNER=your_github_username_or_org
GITHUB_REPO_NAME=your_repository_name

# Required (existing)
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### GitHub Token Permissions

Your GitHub personal access token needs the following permissions:
- `repo` (Full control of private repositories)
- `read:org` (Read organization membership)

### Default Merge Criteria

```python
{
    "required_approvals": 1,        # Minimum number of approvals
    "require_ci_pass": True,        # Require CI checks to pass
    "allow_merge_conflicts": False, # Don't merge if conflicts exist
    "merge_strategy": "squash",     # squash, merge, or rebase
    "stale_days": 30                # Days before branch considered stale
}
```

## API Endpoints

### Execute Merge Agent

**POST** `/merge/execute`

Trigger the merge agent to evaluate and merge eligible PRs.

**Request Body:**
```json
{
    "description": "Merge eligible PRs",
    "cleanup_stale_branches": false,
    "merge_criteria": {
        "required_approvals": 2,
        "require_ci_pass": true
    }
}
```

**Response:**
```json
{
    "status": "completed",
    "message": "Merge agent completed. Merged 3 PRs.",
    "result": {
        "result": {
            "merged_prs": [
                {
                    "number": 42,
                    "title": "Add new feature",
                    "merged": true,
                    "merge_method": "squash"
                }
            ],
            "skipped_prs": [],
            "errors": [],
            "stale_branches_deleted": []
        },
        "score": 0.85,
        "loops_executed": 2,
        "agent_id": "merge_agent_primary"
    }
}
```

### Get Merge Agent Status

**GET** `/merge/status`

Get current merge agent status and performance.

**Response:**
```json
{
    "initialized": true,
    "agent": {
        "agent_id": "merge_agent_primary",
        "agent_type": "merger",
        "status": "completed",
        "generation": 0
    },
    "performance": {
        "average_score": 0.82,
        "best_score": 0.95,
        "worst_score": 0.65,
        "total_executions": 5
    },
    "merge_criteria": {
        "required_approvals": 1,
        "require_ci_pass": true,
        "allow_merge_conflicts": false,
        "merge_strategy": "squash",
        "stale_days": 30
    }
}
```

### Get Merge Criteria

**GET** `/merge/criteria`

Get current merge criteria configuration.

**Response:**
```json
{
    "merge_criteria": {
        "required_approvals": 1,
        "require_ci_pass": true,
        "allow_merge_conflicts": false,
        "merge_strategy": "squash",
        "stale_days": 30
    }
}
```

### Update Merge Criteria

**PUT** `/merge/criteria`

Update merge criteria configuration.

**Request Body:**
```json
{
    "required_approvals": 2,
    "require_ci_pass": true,
    "merge_strategy": "rebase"
}
```

**Response:**
```json
{
    "status": "updated",
    "merge_criteria": {
        "required_approvals": 2,
        "require_ci_pass": true,
        "allow_merge_conflicts": false,
        "merge_strategy": "rebase",
        "stale_days": 30
    }
}
```

### Get Merge History

**GET** `/merge/history`

Get merge agent execution history.

**Response:**
```json
{
    "history": [
        {
            "task": "{'description': 'Merge eligible PRs'}",
            "performance_score": 0.85,
            "timestamp": "2026-01-03T23:00:00",
            "merged_prs": 3,
            "skipped_prs": 1
        }
    ],
    "total_executions": 1
}
```

## Usage Examples

### Using cURL

```bash
# Execute merge agent
curl -X POST http://localhost:8000/merge/execute \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Merge eligible PRs",
    "cleanup_stale_branches": false
  }'

# Get status
curl http://localhost:8000/merge/status

# Update criteria
curl -X PUT http://localhost:8000/merge/criteria \
  -H "Content-Type: application/json" \
  -d '{
    "required_approvals": 2,
    "merge_strategy": "rebase"
  }'
```

### Using Python

```python
import requests

# Execute merge agent
response = requests.post(
    "http://localhost:8000/merge/execute",
    json={
        "description": "Merge eligible PRs",
        "cleanup_stale_branches": False
    }
)
result = response.json()
print(f"Merged {len(result['result']['result']['merged_prs'])} PRs")

# Get status
status = requests.get("http://localhost:8000/merge/status").json()
print(f"Average performance: {status['performance']['average_score']}")
```

## Merge Criteria

### Required Approvals

Number of required approving reviews before a PR can be merged.

- **Default**: 1
- **Recommended**: 2 for production repositories
- **Minimum**: 0 (not recommended)

### Require CI Pass

Whether to require all CI checks to pass before merging.

- **Default**: True
- **Recommended**: Always True for production

### Allow Merge Conflicts

Whether to allow merging PRs with merge conflicts.

- **Default**: False
- **Recommended**: Always False

### Merge Strategy

How to merge the pull request.

- **squash**: Combine all commits into one (default, recommended for clean history)
- **merge**: Create a merge commit (preserves all commits)
- **rebase**: Rebase and merge (linear history)

### Stale Days

Number of days before a branch is considered stale.

- **Default**: 30
- **Recommended**: 14-30 for active repositories

## Reflexion and Performance

The Merge Agent uses reflexion loops to self-improve:

1. **Execute**: Merge eligible PRs
2. **Evaluate**: Score performance (0.0 - 1.0)
3. **Reflect**: Analyze results and trends
4. **Adjust**: Modify strategy if needed

### Performance Scoring

- **0.3**: Successful execution without errors
- **0.3**: Processing PRs
- **0.3**: Successful merges
- **0.1**: High merge rate bonus
- **0.1**: Branch cleanup bonus

### Strategy Adjustments

- **Performance Decline**: Reduces required approvals
- **Low Merge Rate**: Relaxes CI requirements (cautiously)

## Best Practices

1. **Start Conservative**: Begin with strict criteria (2+ approvals, CI required)
2. **Monitor Performance**: Check `/merge/status` regularly
3. **Review History**: Examine `/merge/history` for patterns
4. **Gradual Relaxation**: Only relax criteria if merge rate is too low
5. **Branch Protection**: Use GitHub branch protection rules as backup
6. **Manual Override**: Keep ability to manually merge critical PRs

## Security Considerations

1. **Token Security**: Store GitHub token in secure environment variables
2. **Minimum Permissions**: Use least privilege for GitHub token
3. **Audit Logging**: Review merge history regularly
4. **Branch Protection**: Enable GitHub branch protection rules
5. **CI Requirements**: Always require CI to pass
6. **Approval Requirements**: Require at least 1 approval

## Troubleshooting

### Merge Agent Not Initialized

**Error**: `Merge agent not initialized`

**Solution**: Ensure `GITHUB_TOKEN`, `GITHUB_REPO_OWNER`, and `GITHUB_REPO_NAME` are set in environment.

### GitHub API Rate Limits

**Issue**: Too many API calls

**Solution**: 
- Reduce execution frequency
- Use GitHub Apps for higher rate limits
- Monitor `/merge/history` for execution count

### PRs Not Merging

**Issue**: PRs meeting criteria but not merging

**Solution**:
1. Check CI status manually
2. Verify approvals are from authorized reviewers
3. Check for merge conflicts
4. Review error messages in response

### Low Performance Score

**Issue**: Performance score consistently low

**Solution**:
1. Review merge criteria (may be too strict)
2. Check for CI failures in repository
3. Ensure PRs have necessary approvals
4. Monitor `/merge/history` for patterns

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Auto-merge PRs

on:
  schedule:
    # Run every hour
    - cron: '0 * * * *'
  workflow_dispatch:

jobs:
  merge:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Merge Agent
        run: |
          curl -X POST ${{ secrets.AGENT_FOUNDRY_URL }}/merge/execute \
            -H "Content-Type: application/json" \
            -d '{
              "description": "Scheduled PR merge",
              "cleanup_stale_branches": false
            }'
```

## Support

For issues or questions:
- Open an issue on GitHub
- Check the main README.md
- Review the CONTRIBUTING.md guidelines
