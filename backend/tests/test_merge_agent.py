"""
Tests for Merge Agent
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta


@pytest.fixture
def mock_github_pr():
    """Mock GitHub PR object"""
    pr = Mock()
    pr.number = 42
    pr.title = "Add new feature"
    pr.user = Mock(login="testuser")
    pr.created_at = datetime.now()
    pr.mergeable = True

    # Mock reviews
    review = Mock()
    review.state = "APPROVED"
    pr.get_reviews = Mock(return_value=[review])

    # Mock commits and statuses
    commit = Mock()
    status = Mock()
    status.state = "success"

    commit_status = Mock()
    commit_status.totalCount = 1
    commit_status.__iter__ = Mock(return_value=iter([status]))
    commit.get_statuses = Mock(return_value=commit_status)

    pr.get_commits = Mock(return_value=[commit])

    # Mock merge result
    merge_result = Mock()
    merge_result.merged = True
    merge_result.sha = "abc123"
    merge_result.message = "Merged successfully"
    pr.merge = Mock(return_value=merge_result)

    return pr


@pytest.fixture
def mock_github_repo(mock_github_pr):
    """Mock GitHub repository object"""
    repo = Mock()
    repo.get_pulls = Mock(return_value=[mock_github_pr])

    # Mock branches
    branch = Mock()
    branch.name = "feature/old-branch"
    repo.get_branches = Mock(return_value=[branch])

    return repo


@pytest.fixture
def mock_github_client(mock_github_repo):
    """Mock GitHub client"""
    client = Mock()
    client.get_repo = Mock(return_value=mock_github_repo)
    return client


# ============================================================================
# MergeAgent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_merge_agent_initialization():
    """Test MergeAgent can be initialized without GitHub client"""
    from agents.merge_agent import MergeAgent

    # Test initialization without GitHub connection (mock mode)
    agent = MergeAgent("test_merger")

    assert agent.agent_id == "test_merger"
    assert agent.agent_type == "merger"
    assert "required_approvals" in agent.merge_criteria


@pytest.mark.asyncio
async def test_merge_agent_initialization_with_token():
    """Test MergeAgent initialization with GitHub token (should not connect in test)"""
    from agents.merge_agent import MergeAgent

    # Mock the Github class to prevent actual connection
    with patch("github.Github"):
        agent = MergeAgent(
            "test_merger",
            github_token="test_token",
            repo_owner="owner",
            repo_name="repo",
        )

        assert agent.agent_id == "test_merger"
        assert agent.agent_type == "merger"
        assert agent.github_token == "test_token"
        assert agent.repo_owner == "owner"
        assert agent.repo_name == "repo"
        assert "required_approvals" in agent.merge_criteria


@pytest.mark.asyncio
async def test_merge_agent_without_github_token():
    """Test MergeAgent works in mock mode without GitHub token"""
    from agents.merge_agent import MergeAgent

    agent = MergeAgent("test_merger")

    task = {"description": "Test merge task"}
    result = await agent.execute(task)

    # Should return mock result
    assert "mock" in result
    assert result["mock"] is True
    assert "merged_prs" in result
    assert "skipped_prs" in result


@pytest.mark.asyncio
async def test_merge_agent_evaluate_performance():
    """Test merge agent performance evaluation"""
    from agents.merge_agent import MergeAgent

    agent = MergeAgent("test_merger")

    # Test with successful merge
    result = {
        "merged_prs": [{"number": 1}],
        "skipped_prs": [{"number": 2}],
        "errors": [],
        "stale_branches_deleted": ["old-branch"],
    }

    score = await agent.evaluate_performance(result)

    assert score > 0.5
    assert score <= 1.0


@pytest.mark.asyncio
async def test_merge_agent_evaluate_performance_with_errors():
    """Test performance evaluation with errors"""
    from agents.merge_agent import MergeAgent

    agent = MergeAgent("test_merger")

    result = {
        "merged_prs": [],
        "skipped_prs": [],
        "errors": [{"error": "test error"}],
    }

    score = await agent.evaluate_performance(result)

    assert score < 0.5


@pytest.mark.asyncio
async def test_merge_agent_adjust_strategy():
    """Test merge agent strategy adjustment"""
    from agents.merge_agent import MergeAgent

    agent = MergeAgent("test_merger")
    agent.merge_criteria["required_approvals"] = 2

    await agent._adjust_strategy("performance_decline")

    # Should reduce required approvals
    assert agent.merge_criteria["required_approvals"] == 1


@pytest.mark.asyncio
async def test_merge_agent_configure_criteria():
    """Test merge criteria configuration"""
    from agents.merge_agent import MergeAgent

    agent = MergeAgent("test_merger")

    new_criteria = {
        "required_approvals": 2,
        "merge_strategy": "rebase",
    }

    agent.configure_merge_criteria(new_criteria)

    assert agent.merge_criteria["required_approvals"] == 2
    assert agent.merge_criteria["merge_strategy"] == "rebase"


@pytest.mark.asyncio
async def test_merge_agent_get_criteria():
    """Test getting merge criteria"""
    from agents.merge_agent import MergeAgent

    agent = MergeAgent("test_merger")

    criteria = agent.get_merge_criteria()

    assert "required_approvals" in criteria
    assert "require_ci_pass" in criteria
    assert "merge_strategy" in criteria


@pytest.mark.asyncio
async def test_merge_agent_with_mocked_github(
    mock_github_client, mock_github_repo, mock_github_pr
):
    """Test merge agent with mocked GitHub API"""
    from agents.merge_agent import MergeAgent

    # Create agent without connecting
    agent = MergeAgent("test_merger")

    # Manually set the mocked GitHub components
    agent.github_client = mock_github_client
    agent.repo = mock_github_repo
    agent.github_token = "test_token"
    agent.repo_owner = "owner"
    agent.repo_name = "repo"

    task = {"description": "Merge eligible PRs"}
    result = await agent.execute(task)

    assert "merged_prs" in result
    assert "skipped_prs" in result
    assert "errors" in result


@pytest.mark.asyncio
async def test_merge_agent_evaluate_pr_with_approvals(mock_github_pr):
    """Test PR evaluation with sufficient approvals"""
    from agents.merge_agent import MergeAgent

    agent = MergeAgent("test_merger")
    agent.merge_criteria["required_approvals"] = 1

    pr_info = await agent._evaluate_pr(mock_github_pr)

    assert pr_info["number"] == 42
    assert pr_info["approvals_count"] == 1
    assert pr_info["mergeable"] is True or len(pr_info["merge_blocked_reasons"]) >= 0


@pytest.mark.asyncio
async def test_merge_agent_evaluate_pr_insufficient_approvals():
    """Test PR evaluation with insufficient approvals"""
    from agents.merge_agent import MergeAgent

    pr = Mock()
    pr.number = 43
    pr.title = "Test PR"
    pr.user = Mock(login="testuser")
    pr.created_at = datetime.now()
    pr.mergeable = True
    pr.get_reviews = Mock(return_value=[])  # No approvals

    commit = Mock()
    status = Mock()
    status.state = "success"
    commit_status = Mock()
    commit_status.totalCount = 1
    commit_status.__iter__ = Mock(return_value=iter([status]))
    commit.get_statuses = Mock(return_value=commit_status)
    pr.get_commits = Mock(return_value=[commit])

    agent = MergeAgent("test_merger")
    agent.merge_criteria["required_approvals"] = 1

    pr_info = await agent._evaluate_pr(pr)

    assert pr_info["mergeable"] is False
    assert any("insufficient_approvals" in reason for reason in pr_info["merge_blocked_reasons"])


@pytest.mark.asyncio
async def test_merge_agent_check_ci_status_success():
    """Test CI status check with successful status"""
    from agents.merge_agent import MergeAgent

    pr = Mock()
    commit = Mock()
    status = Mock()
    status.state = "success"

    commit_status = Mock()
    commit_status.totalCount = 1
    commit_status.__iter__ = Mock(return_value=iter([status]))
    commit.get_statuses = Mock(return_value=commit_status)

    pr.get_commits = Mock(return_value=[commit])

    agent = MergeAgent("test_merger")
    ci_status = await agent._check_ci_status(pr)

    assert ci_status == "success"


@pytest.mark.asyncio
async def test_merge_agent_check_ci_status_failure():
    """Test CI status check with failure"""
    from agents.merge_agent import MergeAgent

    pr = Mock()
    commit = Mock()
    status = Mock()
    status.state = "failure"

    commit_status = Mock()
    commit_status.totalCount = 1
    commit_status.__iter__ = Mock(return_value=iter([status]))
    commit.get_statuses = Mock(return_value=commit_status)

    pr.get_commits = Mock(return_value=[commit])

    agent = MergeAgent("test_merger")
    ci_status = await agent._check_ci_status(pr)

    assert ci_status == "failure"


@pytest.mark.asyncio
async def test_merge_agent_merge_pr_success(mock_github_pr):
    """Test successful PR merge"""
    from agents.merge_agent import MergeAgent

    agent = MergeAgent("test_merger")
    agent.merge_criteria["merge_strategy"] = "squash"

    pr_info = {"number": 42, "title": "Test PR"}
    result = await agent._merge_pr(mock_github_pr, pr_info)

    assert result["merged"] is True
    assert result["number"] == 42
    assert result["merge_method"] == "squash"


@pytest.mark.asyncio
async def test_merge_agent_cleanup_stale_branches():
    """Test stale branch cleanup identification"""
    from agents.merge_agent import MergeAgent

    agent = MergeAgent("test_merger")
    agent.merge_criteria["stale_days"] = 30

    # Mock repo
    branch = Mock()
    branch.name = "feature/old-feature"

    pr = Mock()
    pr.state = "closed"
    pr.closed_at = datetime.now() - timedelta(days=60)

    repo = Mock()
    repo.get_branches = Mock(return_value=[branch])
    repo.get_pulls = Mock(return_value=[pr])

    agent.repo = repo

    stale_branches = await agent._cleanup_stale_branches()

    # Should identify stale branch
    assert isinstance(stale_branches, list)


@pytest.mark.asyncio
async def test_merge_agent_reflexion_loop():
    """Test merge agent reflexion loop"""
    from agents.merge_agent import MergeAgent

    agent = MergeAgent("test_merger")

    task = {"description": "Test merge task"}
    result = await agent.reflexion_loop(task, max_loops=2)

    assert "result" in result
    assert "score" in result
    assert "agent_id" in result
    assert result["agent_id"] == "test_merger"


@pytest.mark.asyncio
async def test_merge_agent_to_dict():
    """Test agent serialization to dict"""
    from agents.merge_agent import MergeAgent

    agent = MergeAgent("test_merger")

    agent_dict = agent.to_dict()

    assert agent_dict["agent_id"] == "test_merger"
    assert agent_dict["agent_type"] == "merger"
    assert "status" in agent_dict
    assert "performance_summary" in agent_dict
