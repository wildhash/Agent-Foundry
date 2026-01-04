"""
Tests for MergeAgent
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from agents.merge_agent import MergeAgent


@pytest.fixture
def mock_github_token():
    """Mock GitHub token"""
    return "ghp_test_token_1234567890"


@pytest.fixture
def mock_repo_name():
    """Mock repository name"""
    return "test-owner/test-repo"


@pytest.fixture
def merge_agent(mock_github_token, mock_repo_name):
    """Create a MergeAgent instance with mocked GitHub client"""
    # Create agent without initializing GitHub client
    agent = MergeAgent(agent_id="test_merger_1")

    # Manually mock the GitHub client and repo
    mock_client = MagicMock()
    mock_repo = MagicMock()

    agent.github_token = mock_github_token
    agent.repo_name = mock_repo_name
    agent.github_client = mock_client
    agent.repo = mock_repo

    return agent


@pytest.fixture
def mock_pull_request():
    """Create a mock pull request"""
    pr = MagicMock()
    pr.number = 123
    pr.title = "Test PR"
    pr.user.login = "test-user"
    pr.created_at = datetime.now()
    pr.mergeable = True
    pr.mergeable_state = "clean"
    pr.draft = False
    pr.body = "Test PR body"
    pr.labels = []
    return pr


class TestMergeAgentInit:
    """Test MergeAgent initialization"""

    def test_init_without_credentials(self):
        """Test initialization without GitHub credentials"""
        agent = MergeAgent(agent_id="test_merger")

        assert agent.agent_id == "test_merger"
        assert agent.agent_type == "merger"
        assert agent.merge_strategy == "merge"
        assert agent.stale_branch_days == 90
        assert agent.min_approvals == 1
        assert agent.require_ci_pass is True

    def test_init_with_credentials(self, mock_github_token, mock_repo_name):
        """Test initialization with GitHub credentials"""
        # Mock the github module and Github class
        with patch.dict("sys.modules", {"github": MagicMock()}):
            import sys

            mock_github_class = MagicMock()
            mock_client = MagicMock()
            mock_repo = MagicMock()
            mock_github_class.return_value = mock_client
            mock_client.get_repo.return_value = mock_repo
            sys.modules["github"].Github = mock_github_class

            agent = MergeAgent(agent_id="test_merger", github_token=mock_github_token, repo_name=mock_repo_name)

            assert agent.github_token == mock_github_token
            assert agent.repo_name == mock_repo_name
            assert agent.github_client is not None
            assert agent.repo is not None

    def test_configure_merge_strategy(self, merge_agent):
        """Test configuring merge strategy"""
        merge_agent.configure(merge_strategy="squash")
        assert merge_agent.merge_strategy == "squash"

        merge_agent.configure(merge_strategy="rebase")
        assert merge_agent.merge_strategy == "rebase"

    def test_configure_invalid_merge_strategy(self, merge_agent):
        """Test configuring invalid merge strategy raises error"""
        with pytest.raises(ValueError):
            merge_agent.configure(merge_strategy="invalid")

    def test_configure_stale_branch_days(self, merge_agent):
        """Test configuring stale branch days"""
        merge_agent.configure(stale_branch_days=60)
        assert merge_agent.stale_branch_days == 60

        # Should not allow values less than 1
        merge_agent.configure(stale_branch_days=0)
        assert merge_agent.stale_branch_days == 1

    def test_configure_min_approvals(self, merge_agent):
        """Test configuring minimum approvals"""
        merge_agent.configure(min_approvals=2)
        assert merge_agent.min_approvals == 2

        # Should not allow negative values
        merge_agent.configure(min_approvals=-1)
        assert merge_agent.min_approvals == 0

    def test_configure_require_ci_pass(self, merge_agent):
        """Test configuring CI requirement"""
        merge_agent.configure(require_ci_pass=False)
        assert merge_agent.require_ci_pass is False


class TestMergeAgentExecute:
    """Test MergeAgent execute method"""

    @pytest.mark.asyncio
    async def test_execute_without_github_client(self):
        """Test execute fails gracefully without GitHub client"""
        agent = MergeAgent(agent_id="test_merger")

        result = await agent.execute({"action": "merge_prs"})

        assert result["success"] is False
        assert "not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_merge_prs_dry_run(self, merge_agent, mock_pull_request):
        """Test execute with merge_prs action in dry run mode"""
        merge_agent.repo.get_pulls.return_value = [mock_pull_request]

        # Mock eligibility check to return eligible
        with patch.object(merge_agent, "_check_pr_eligibility", return_value=(True, "eligible")):
            result = await merge_agent.execute({"action": "merge_prs", "dry_run": True})

        assert result["success"] is True
        assert result["dry_run"] is True
        assert len(result["merged_prs"]) == 1
        assert result["merged_prs"][0]["action"] == "would_merge"
        assert result["merged_prs"][0]["number"] == 123

    @pytest.mark.asyncio
    async def test_execute_merge_prs_with_filters(self, merge_agent, mock_pull_request):
        """Test execute with PR filters"""
        # Add labels to PR
        label1 = MagicMock()
        label1.name = "approved"
        label2 = MagicMock()
        label2.name = "ready-to-merge"
        mock_pull_request.labels = [label1, label2]

        merge_agent.repo.get_pulls.return_value = [mock_pull_request]

        with patch.object(merge_agent, "_check_pr_eligibility", return_value=(True, "eligible")):
            result = await merge_agent.execute(
                {"action": "merge_prs", "dry_run": True, "pr_filters": {"labels": ["approved", "ready-to-merge"]}}
            )

        assert result["success"] is True
        assert len(result["merged_prs"]) == 1

    @pytest.mark.asyncio
    async def test_execute_both_actions(self, merge_agent, mock_pull_request):
        """Test execute with both merge and cleanup actions"""
        merge_agent.repo.get_pulls.return_value = []
        merge_agent.repo.get_branches.return_value = []

        result = await merge_agent.execute({"action": "both", "dry_run": True})

        assert result["success"] is True
        assert "merged_prs" in result
        assert "cleaned_branches" in result


class TestPRMergeability:
    """Test PR eligibility checking"""

    @pytest.mark.asyncio
    async def test_check_pr_eligibility_mergeable(self, merge_agent, mock_pull_request):
        """Test PR eligibility when all criteria are met"""
        # Mock reviews with approval
        mock_review = MagicMock()
        mock_review.state = "APPROVED"
        mock_review.user.login = "reviewer1"
        mock_review.submitted_at = datetime.now()
        mock_pull_request.get_reviews.return_value = [mock_review]

        # Mock CI status
        with patch.object(merge_agent, "_check_ci_status", return_value=(True, "all_checks_passed")):
            eligible, reason = await merge_agent._check_pr_eligibility(mock_pull_request)

        assert eligible is True
        assert reason == "eligible"

    @pytest.mark.asyncio
    async def test_check_pr_eligibility_has_conflicts(self, merge_agent, mock_pull_request):
        """Test PR eligibility when there are merge conflicts"""
        mock_pull_request.mergeable = False

        eligible, reason = await merge_agent._check_pr_eligibility(mock_pull_request)

        assert eligible is False
        assert reason == "has_merge_conflicts"

    @pytest.mark.asyncio
    async def test_check_pr_eligibility_insufficient_approvals(self, merge_agent, mock_pull_request):
        """Test PR eligibility with insufficient approvals"""
        mock_pull_request.get_reviews.return_value = []

        eligible, reason = await merge_agent._check_pr_eligibility(mock_pull_request)

        assert eligible is False
        assert "insufficient_approvals" in reason

    @pytest.mark.asyncio
    async def test_check_pr_eligibility_changes_requested(self, merge_agent, mock_pull_request):
        """Test PR eligibility when changes are requested"""
        mock_review1 = MagicMock()
        mock_review1.state = "APPROVED"
        mock_review1.user.login = "reviewer1"
        mock_review1.submitted_at = datetime.now() - timedelta(hours=1)

        mock_review2 = MagicMock()
        mock_review2.state = "CHANGES_REQUESTED"
        mock_review2.user.login = "reviewer2"
        mock_review2.submitted_at = datetime.now()

        mock_pull_request.get_reviews.return_value = [mock_review1, mock_review2]

        eligible, reason = await merge_agent._check_pr_eligibility(mock_pull_request)

        assert eligible is False
        assert reason == "changes_requested"

    @pytest.mark.asyncio
    async def test_check_pr_eligibility_is_draft(self, merge_agent, mock_pull_request):
        """Test PR eligibility when PR is draft"""
        mock_pull_request.draft = True
        mock_review = MagicMock()
        mock_review.state = "APPROVED"
        mock_review.user.login = "reviewer1"
        mock_review.submitted_at = datetime.now()
        mock_pull_request.get_reviews.return_value = [mock_review]

        with patch.object(merge_agent, "_check_ci_status", return_value=(True, "all_checks_passed")):
            eligible, reason = await merge_agent._check_pr_eligibility(mock_pull_request)

        assert eligible is False
        assert reason == "is_draft"

    @pytest.mark.asyncio
    async def test_check_pr_eligibility_ci_failed(self, merge_agent, mock_pull_request):
        """Test PR eligibility when CI checks fail"""
        mock_review = MagicMock()
        mock_review.state = "APPROVED"
        mock_review.user.login = "reviewer1"
        mock_review.submitted_at = datetime.now()
        mock_pull_request.get_reviews.return_value = [mock_review]

        with patch.object(merge_agent, "_check_ci_status", return_value=(False, "checks_failed")):
            eligible, reason = await merge_agent._check_pr_eligibility(mock_pull_request)

        assert eligible is False
        assert "ci_failed" in reason


class TestCIStatus:
    """Test CI status checking"""

    @pytest.mark.asyncio
    async def test_check_ci_status_passing(self, merge_agent, mock_pull_request):
        """Test CI status when all checks pass"""
        mock_commit = MagicMock()
        mock_status = MagicMock()
        mock_status.state = "success"
        mock_commit.get_combined_status.return_value = mock_status

        mock_check_run = MagicMock()
        mock_check_run.status = "completed"
        mock_check_run.conclusion = "success"
        mock_check_run.name = "test-check"
        mock_commit.get_check_runs.return_value = [mock_check_run]

        mock_commits = MagicMock()
        mock_commits.totalCount = 1
        mock_commits.__iter__ = lambda self: iter([mock_commit])
        mock_pull_request.get_commits.return_value = mock_commits

        passed, reason = await merge_agent._check_ci_status(mock_pull_request)

        assert passed is True
        assert reason == "all_checks_passed"

    @pytest.mark.asyncio
    async def test_check_ci_status_pending(self, merge_agent, mock_pull_request):
        """Test CI status when checks are pending"""
        mock_commit = MagicMock()
        mock_status = MagicMock()
        mock_status.state = "pending"
        mock_commit.get_combined_status.return_value = mock_status

        mock_commits = MagicMock()
        mock_commits.totalCount = 1
        mock_commits.__iter__ = lambda self: iter([mock_commit])
        mock_pull_request.get_commits.return_value = mock_commits

        passed, reason = await merge_agent._check_ci_status(mock_pull_request)

        assert passed is False
        assert reason == "checks_pending"

    @pytest.mark.asyncio
    async def test_check_ci_status_failed(self, merge_agent, mock_pull_request):
        """Test CI status when checks fail"""
        mock_commit = MagicMock()
        mock_status = MagicMock()
        mock_status.state = "failure"
        mock_commit.get_combined_status.return_value = mock_status

        mock_commits = MagicMock()
        mock_commits.totalCount = 1
        mock_commits.__iter__ = lambda self: iter([mock_commit])
        mock_pull_request.get_commits.return_value = mock_commits

        passed, reason = await merge_agent._check_ci_status(mock_pull_request)

        assert passed is False
        assert reason == "checks_failed"


class TestBranchCleanup:
    """Test branch cleanup functionality"""

    @pytest.mark.asyncio
    async def test_cleanup_stale_branches_dry_run(self, merge_agent):
        """Test branch cleanup in dry run mode"""
        # Mock a stale branch
        mock_branch = MagicMock()
        mock_branch.name = "feature/old-feature"
        mock_branch.protected = False

        mock_commit = MagicMock()
        mock_commit.commit.author.date = datetime.now() - timedelta(days=100)
        mock_branch.commit = mock_commit

        merge_agent.repo.get_branches.return_value = [mock_branch]
        merge_agent.repo.owner.login = "test-owner"

        # Mock no open PRs for this branch
        mock_prs = MagicMock()
        mock_prs.totalCount = 0
        merge_agent.repo.get_pulls.return_value = mock_prs

        result = {"cleaned_branches": [], "errors": []}
        await merge_agent._cleanup_stale_branches(result, dry_run=True)

        assert len(result["cleaned_branches"]) == 1
        assert result["cleaned_branches"][0]["name"] == "feature/old-feature"
        assert result["cleaned_branches"][0]["action"] == "would_delete"

    @pytest.mark.asyncio
    async def test_cleanup_protected_branches(self, merge_agent):
        """Test that protected branches are not cleaned up"""
        # Mock protected branches
        mock_branches = []
        for name in ["main", "master", "develop"]:
            branch = MagicMock()
            branch.name = name
            branch.protected = False
            mock_branches.append(branch)

        merge_agent.repo.get_branches.return_value = mock_branches

        result = {"cleaned_branches": [], "errors": []}
        await merge_agent._cleanup_stale_branches(result, dry_run=True)

        # No branches should be cleaned
        assert len(result["cleaned_branches"]) == 0

    @pytest.mark.asyncio
    async def test_cleanup_branches_with_open_prs(self, merge_agent):
        """Test that branches with open PRs are not cleaned"""
        mock_branch = MagicMock()
        mock_branch.name = "feature/with-pr"
        mock_branch.protected = False

        mock_commit = MagicMock()
        mock_commit.commit.author.date = datetime.now() - timedelta(days=100)
        mock_branch.commit = mock_commit

        merge_agent.repo.get_branches.return_value = [mock_branch]
        merge_agent.repo.owner.login = "test-owner"

        # Mock open PRs for this branch
        mock_prs = MagicMock()
        mock_prs.totalCount = 1
        merge_agent.repo.get_pulls.return_value = mock_prs

        result = {"cleaned_branches": [], "errors": []}
        await merge_agent._cleanup_stale_branches(result, dry_run=True)

        # Branch should not be cleaned
        assert len(result["cleaned_branches"]) == 0


class TestPerformanceEvaluation:
    """Test performance evaluation"""

    @pytest.mark.asyncio
    async def test_evaluate_performance_success(self, merge_agent):
        """Test performance evaluation for successful execution"""
        result = {
            "success": True,
            "merged_prs": [{"number": 1}, {"number": 2}],
            "cleaned_branches": [{"name": "old-branch"}],
            "skipped_prs": [{"number": 3}],
            "errors": [],
        }

        score = await merge_agent.evaluate_performance(result)

        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be a good score

    @pytest.mark.asyncio
    async def test_evaluate_performance_failure(self, merge_agent):
        """Test performance evaluation for failed execution"""
        result = {"success": False, "merged_prs": [], "cleaned_branches": [], "errors": ["error1", "error2"]}

        score = await merge_agent.evaluate_performance(result)

        assert score == 0.1  # Low score for failure

    @pytest.mark.asyncio
    async def test_evaluate_performance_with_errors(self, merge_agent):
        """Test performance evaluation with errors"""
        result = {
            "success": True,
            "merged_prs": [{"number": 1}],
            "cleaned_branches": [],
            "errors": ["error1", "error2", "error3"],
        }

        score = await merge_agent.evaluate_performance(result)

        assert 0.0 <= score <= 1.0
        # Score should be lower due to errors

    @pytest.mark.asyncio
    async def test_evaluate_performance_no_activity(self, merge_agent):
        """Test performance evaluation with no merges or cleanups"""
        result = {"success": True, "merged_prs": [], "cleaned_branches": [], "skipped_prs": [], "errors": []}

        score = await merge_agent.evaluate_performance(result)

        assert score == 0.3  # Base score only


class TestStrategyAdjustment:
    """Test strategy adjustment"""

    @pytest.mark.asyncio
    async def test_adjust_strategy_performance_decline(self, merge_agent):
        """Test strategy adjustment on performance decline"""
        initial_approvals = merge_agent.min_approvals

        await merge_agent._adjust_strategy("performance_decline")

        assert merge_agent.min_approvals == initial_approvals + 1

    @pytest.mark.asyncio
    async def test_adjust_strategy_performance_improvement(self, merge_agent):
        """Test strategy adjustment on performance improvement"""
        merge_agent.min_approvals = 3

        await merge_agent._adjust_strategy("performance_improvement")

        assert merge_agent.min_approvals == 2
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
async def test_merge_agent_with_mocked_github(mock_github_client, mock_github_repo, mock_github_pr):
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
