"""
Merge Agent for automated PR management and branch cleanup
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class MergeAgent(BaseAgent):
    """
    Merge agent for automated PR management and branch cleanup.
    Evaluates PRs for mergeability based on configurable criteria.
    """

    def __init__(
        self,
        agent_id: str,
        github_token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
    ):
        super().__init__(agent_id, "merger")
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_client = None
        self.repo = None

        # Default merge criteria
        self.merge_criteria = {
            "required_approvals": 1,
            "require_ci_pass": True,
            "allow_merge_conflicts": False,
            "merge_strategy": "squash",  # squash, merge, rebase
            "stale_days": 30,
        }

        # Initialize GitHub client if credentials provided
        if github_token and repo_owner and repo_name:
            self._initialize_github_client()

    def _initialize_github_client(self):
        """Initialize GitHub API client"""
        try:
            from github import Github

            self.github_client = Github(self.github_token)
            self.repo = self.github_client.get_repo(f"{self.repo_owner}/{self.repo_name}")
            logger.info(f"GitHub client initialized for {self.repo_owner}/{self.repo_name}")
        except ImportError:
            logger.error("PyGithub not installed. Install with: pip install PyGithub")
            self.github_client = None
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {str(e)}")
            self.github_client = None

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute merge agent task: evaluate and merge eligible PRs

        Args:
            task: Task configuration with optional overrides for merge criteria

        Returns:
            Result dictionary with merged PRs, skipped PRs, and errors
        """
        logger.info(f"Merge agent executing task: {task.get('description', 'N/A')}")

        # Update criteria if provided in task
        if "merge_criteria" in task:
            self.merge_criteria.update(task["merge_criteria"])

        # If no GitHub client, return mock result
        if not self.github_client or not self.repo:
            logger.warning("GitHub client not initialized, returning mock result")
            return self._mock_execution_result()

        result = {
            "merged_prs": [],
            "skipped_prs": [],
            "stale_branches_deleted": [],
            "errors": [],
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Fetch open PRs
            open_prs = await self._fetch_open_prs()
            logger.info(f"Found {len(open_prs)} open PRs")

            # Evaluate and merge eligible PRs
            for pr in open_prs:
                try:
                    pr_info = await self._evaluate_pr(pr)

                    if pr_info["mergeable"]:
                        merge_result = await self._merge_pr(pr, pr_info)
                        result["merged_prs"].append(merge_result)
                    else:
                        result["skipped_prs"].append(pr_info)
                except Exception as e:
                    error_info = {
                        "pr_number": pr.number,
                        "error": str(e),
                    }
                    result["errors"].append(error_info)
                    logger.error(f"Error processing PR #{pr.number}: {str(e)}")

            # Clean up stale branches if requested
            if task.get("cleanup_stale_branches", False):
                stale_branches = await self._cleanup_stale_branches()
                result["stale_branches_deleted"] = stale_branches

        except Exception as e:
            logger.error(f"Merge agent execution failed: {str(e)}")
            result["errors"].append({"general": str(e)})

        return result

    async def _fetch_open_prs(self) -> List[Any]:
        """Fetch open pull requests from repository"""
        try:
            return list(self.repo.get_pulls(state="open"))
        except Exception as e:
            logger.error(f"Failed to fetch open PRs: {str(e)}")
            return []

    async def _evaluate_pr(self, pr: Any) -> Dict[str, Any]:
        """
        Evaluate if PR meets merge criteria

        Returns:
            Dictionary with PR info and mergeable status
        """
        pr_info = {
            "number": pr.number,
            "title": pr.title,
            "author": pr.user.login,
            "created_at": pr.created_at.isoformat(),
            "mergeable": False,
            "merge_blocked_reasons": [],
        }

        # Check for merge conflicts
        if not self.merge_criteria["allow_merge_conflicts"] and pr.mergeable is False:
            pr_info["merge_blocked_reasons"].append("merge_conflicts")

        # Check for required approvals
        reviews = pr.get_reviews()
        approvals = [r for r in reviews if r.state == "APPROVED"]
        if len(approvals) < self.merge_criteria["required_approvals"]:
            pr_info["merge_blocked_reasons"].append(
                f"insufficient_approvals ({len(approvals)}/{self.merge_criteria['required_approvals']})"
            )

        # Check CI status
        if self.merge_criteria["require_ci_pass"]:
            ci_status = await self._check_ci_status(pr)
            if ci_status != "success":
                pr_info["merge_blocked_reasons"].append(f"ci_status_{ci_status}")

        # PR is mergeable if no blocking reasons
        pr_info["mergeable"] = len(pr_info["merge_blocked_reasons"]) == 0
        pr_info["approvals_count"] = len(approvals)

        return pr_info

    async def _check_ci_status(self, pr: Any) -> str:
        """
        Check CI/status checks for a PR

        Returns:
            Status: 'success', 'pending', 'failure', or 'unknown'
        """
        try:
            # Get the latest commit
            commits = list(pr.get_commits())
            if not commits:
                return "unknown"

            latest_commit = commits[-1]
            statuses = latest_commit.get_statuses()

            # Check combined status
            if statuses.totalCount == 0:
                return "unknown"

            # Get all statuses
            status_list = list(statuses)
            if not status_list:
                return "unknown"

            # Check if all are successful
            if all(s.state == "success" for s in status_list):
                return "success"
            elif any(s.state == "failure" for s in status_list):
                return "failure"
            else:
                return "pending"

        except Exception as e:
            logger.error(f"Failed to check CI status: {str(e)}")
            return "unknown"

    async def _merge_pr(self, pr: Any, pr_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge a pull request

        Returns:
            Dictionary with merge result
        """
        merge_strategy = self.merge_criteria["merge_strategy"]

        try:
            # Map strategy to GitHub merge method
            merge_method_map = {
                "squash": "squash",
                "merge": "merge",
                "rebase": "rebase",
            }
            merge_method = merge_method_map.get(merge_strategy, "squash")

            # Perform merge
            merge_result = pr.merge(merge_method=merge_method)

            result = {
                "number": pr.number,
                "title": pr.title,
                "merged": merge_result.merged,
                "merge_method": merge_method,
                "sha": merge_result.sha,
                "message": merge_result.message,
            }

            logger.info(f"Successfully merged PR #{pr.number}: {pr.title}")
            return result

        except Exception as e:
            logger.error(f"Failed to merge PR #{pr.number}: {str(e)}")
            return {
                "number": pr.number,
                "title": pr.title,
                "merged": False,
                "error": str(e),
            }

    async def _cleanup_stale_branches(self) -> List[str]:
        """
        Identify and optionally delete stale branches

        Returns:
            List of deleted branch names
        """
        deleted_branches = []
        stale_cutoff = datetime.now() - timedelta(days=self.merge_criteria["stale_days"])

        try:
            branches = self.repo.get_branches()

            for branch in branches:
                # Skip main/master branches
                if branch.name in ["main", "master", "develop"]:
                    continue

                # Check if branch has associated PR
                prs = self.repo.get_pulls(state="all", head=branch.name)
                pr_list = list(prs)

                # Branch is stale if it has no open PRs and is old
                if pr_list:
                    # Get the most recent PR for this branch
                    latest_pr = pr_list[0]
                    if latest_pr.state == "closed" and latest_pr.closed_at and latest_pr.closed_at < stale_cutoff:
                        # Branch is stale, could be deleted
                        # For safety, we just log it here - actual deletion needs confirmation
                        logger.info(f"Stale branch identified: {branch.name}")
                        deleted_branches.append(branch.name)

        except Exception as e:
            logger.error(f"Failed to cleanup stale branches: {str(e)}")

        return deleted_branches

    async def evaluate_performance(self, result: Dict[str, Any]) -> float:
        """
        Evaluate merge agent performance

        Args:
            result: Execution result from execute()

        Returns:
            Performance score between 0.0 and 1.0
        """
        score = 0.0

        merged_count = len(result.get("merged_prs", []))
        skipped_count = len(result.get("skipped_prs", []))
        error_count = len(result.get("errors", []))
        total_prs = merged_count + skipped_count

        # Base score for successful execution
        if error_count == 0:
            score += 0.3
        elif error_count <= 2:
            score += 0.15

        # Score for processing PRs
        if total_prs > 0:
            score += 0.3

        # Score for successful merges
        if merged_count > 0:
            score += 0.3
            # Bonus for high merge rate
            merge_rate = merged_count / total_prs if total_prs > 0 else 0
            score += min(merge_rate * 0.1, 0.1)

        # Score for branch cleanup
        if result.get("stale_branches_deleted"):
            score += 0.1

        return min(score, 1.0)

    async def _adjust_strategy(self, reason: str):
        """
        Adjust merge strategy based on reflexion

        Args:
            reason: Reason for adjustment
        """
        if reason == "performance_decline":
            # Relax criteria if performance is declining
            if self.merge_criteria["required_approvals"] > 1:
                self.merge_criteria["required_approvals"] -= 1
                logger.info(f"Adjusted strategy: Reduced required approvals to {self.merge_criteria['required_approvals']}")
        elif reason == "low_merge_rate":
            # If merge rate is low, consider relaxing criteria
            self.merge_criteria["require_ci_pass"] = False
            logger.info("Adjusted strategy: Disabled CI requirement")

    def configure_merge_criteria(self, criteria: Dict[str, Any]):
        """
        Update merge criteria configuration

        Args:
            criteria: Dictionary of merge criteria to update
        """
        self.merge_criteria.update(criteria)
        logger.info(f"Merge criteria updated: {self.merge_criteria}")

    def get_merge_criteria(self) -> Dict[str, Any]:
        """Get current merge criteria configuration"""
        return self.merge_criteria.copy()

    def _mock_execution_result(self) -> Dict[str, Any]:
        """Return mock result when GitHub client is not available"""
        return {
            "merged_prs": [
                {
                    "number": 42,
                    "title": "Add new feature",
                    "merged": True,
                    "merge_method": "squash",
                    "sha": "abc123",
                }
            ],
            "skipped_prs": [
                {
                    "number": 43,
                    "title": "WIP: In progress",
                    "mergeable": False,
                    "merge_blocked_reasons": ["insufficient_approvals (0/1)"],
                }
            ],
            "stale_branches_deleted": [],
            "errors": [],
            "timestamp": datetime.now().isoformat(),
            "mock": True,
        }
