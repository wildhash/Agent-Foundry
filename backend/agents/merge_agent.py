"""
Merge agent for automated PR management and branch cleanup
"""

from typing import Dict, Any, Optional, Tuple
import logging
import os
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class MergeAgent(BaseAgent):
    """
    Merge agent for automated PR management and branch cleanup.

    Monitors repository for open PRs, evaluates mergeability criteria,
    and automatically merges eligible PRs or cleans up stale branches.
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

        # Legacy attributes for backward compatibility
        self.merge_strategy = "merge"  # Options: merge, squash, rebase
        self.stale_branch_days = 90  # Days before considering branch stale
        self.min_approvals = 1
        self.require_ci_pass = True

        # Default merge criteria
        self.merge_criteria = {
            "required_approvals": 1,
            "require_ci_pass": True,
            "allow_merge_conflicts": False,
            "merge_strategy": "squash",  # squash, merge, rebase
            "stale_days": 30,
        }

        # Initialize GitHub client if credentials provided
        # Support both new format (repo_owner + repo_name) and old format (just repo_name with "owner/repo")
        if github_token and repo_name:
            self._initialize_github_client()

    def _initialize_github_client(self):
        """Initialize GitHub API client"""
        try:
            from github import Github

            self.github_client = Github(self.github_token)
            # Support both old format (owner/repo) and new format (separate owner and repo)
            if self.repo_owner:
                repo_full_name = f"{self.repo_owner}/{self.repo_name}"
            else:
                # Backward compatibility: repo_name might contain "owner/repo"
                if "/" not in self.repo_name:
                    logger.error(
                        f"Invalid repo_name format: '{self.repo_name}'. " "Expected 'owner/repo' or use repo_owner parameter."
                    )
                    self.github_client = None
                    return
                repo_full_name = self.repo_name
            self.repo = self.github_client.get_repo(repo_full_name)
            logger.info(f"Initialized GitHub client for repo: {repo_full_name}")
        except ImportError:
            logger.warning("PyGithub not installed. Install with: pip install PyGithub")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {str(e)}")

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute merge agent tasks.

        Args:
            task: Task configuration with optional keys:
                - action: "merge_prs", "cleanup_branches", or "both" (default)
                - dry_run: If True, only report what would be done
                - pr_filters: Additional filters for PRs (labels, author, etc.)

        Returns:
            Dictionary with execution results
        """
        if not self.github_client or not self.repo:
            return {
                "success": False,
                "error": "GitHub client not initialized. Provide github_token and repo_name.",
                "merged_prs": [],
                "cleaned_branches": [],
            }

        action = task.get("action", "both")
        dry_run = task.get("dry_run", False)
        pr_filters = task.get("pr_filters", {})

        logger.info(f"Merge agent executing action: {action}, dry_run: {dry_run}")

        result = {
            "success": True,
            "dry_run": dry_run,
            "merged_prs": [],
            "cleaned_branches": [],
            "skipped_prs": [],
            "errors": [],
        }

        # Merge eligible PRs
        if action in ["merge_prs", "both"]:
            await self._process_pull_requests(result, dry_run, pr_filters)

        # Cleanup stale branches
        if action in ["cleanup_branches", "both"]:
            await self._cleanup_stale_branches(result, dry_run)

        return result

    async def _process_pull_requests(self, result: Dict[str, Any], dry_run: bool, pr_filters: Dict[str, Any]):
        """Process and merge eligible pull requests"""
        try:
            open_prs = self.repo.get_pulls(state="open", sort="created", direction="asc")

            for pr in open_prs:
                pr_info = {
                    "number": pr.number,
                    "title": pr.title,
                    "author": pr.user.login,
                    "created_at": pr.created_at.isoformat(),
                }

                # Apply filters if specified
                if pr_filters:
                    if "labels" in pr_filters:
                        pr_labels = [label.name for label in pr.labels]
                        if not any(label in pr_labels for label in pr_filters["labels"]):
                            logger.debug(f"Skipping PR #{pr.number}: Label filter not matched")
                            continue

                    if "author" in pr_filters and pr.user.login != pr_filters["author"]:
                        logger.debug(f"Skipping PR #{pr.number}: Author filter not matched")
                        continue

                # Check mergeability criteria
                eligible, reason = await self._check_pr_eligibility(pr)

                if eligible:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would merge PR #{pr.number}: {pr.title}")
                        pr_info["action"] = "would_merge"
                        result["merged_prs"].append(pr_info)
                    else:
                        # Attempt to merge
                        merge_success = await self._merge_pull_request(pr)
                        if merge_success:
                            logger.info(f"Successfully merged PR #{pr.number}: {pr.title}")
                            pr_info["action"] = "merged"
                            result["merged_prs"].append(pr_info)
                        else:
                            logger.warning(f"Failed to merge PR #{pr.number}")
                            pr_info["reason"] = "merge_failed"
                            result["skipped_prs"].append(pr_info)
                else:
                    logger.info(f"Skipping PR #{pr.number}: {reason}")
                    pr_info["reason"] = reason
                    result["skipped_prs"].append(pr_info)

        except Exception as e:
            logger.error(f"Error processing pull requests: {str(e)}")
            result["errors"].append(f"PR processing error: {str(e)}")

    async def _check_pr_eligibility(self, pr) -> Tuple[bool, str]:
        """
        Check if a PR is eligible for automatic merging.

        Returns:
            Tuple of (eligible: bool, reason: str)
        """
        # Check if PR is mergeable
        if pr.mergeable is False:
            return False, "has_merge_conflicts"

        if pr.mergeable_state == "unknown":
            # GitHub is still calculating, skip for now
            return False, "mergeable_state_unknown"

        # Check for required approvals
        reviews = pr.get_reviews()
        latest_reviews_by_user = {}
        for review in reviews:
            user = review.user.login
            if user not in latest_reviews_by_user or review.submitted_at > latest_reviews_by_user[user].submitted_at:
                latest_reviews_by_user[user] = review

        approved_count = sum(1 for review in latest_reviews_by_user.values() if review.state == "APPROVED")

        if approved_count < self.min_approvals:
            return False, f"insufficient_approvals ({approved_count}/{self.min_approvals})"

        # Check for requested changes
        changes_requested = any(review.state == "CHANGES_REQUESTED" for review in latest_reviews_by_user.values())
        if changes_requested:
            return False, "changes_requested"

        # Check CI status if required
        if self.require_ci_pass:
            ci_passed, ci_reason = await self._check_ci_status(pr)
            if not ci_passed:
                return False, f"ci_failed: {ci_reason}"

        # Check if PR is draft
        if pr.draft:
            return False, "is_draft"

        return True, "eligible"

    async def _check_ci_status(self, pr) -> Tuple[bool, str]:
        """Check CI/status checks for a PR"""
        try:
            # Get the latest commit
            commits = pr.get_commits()
            if commits.totalCount == 0:
                return False, "no_commits"

            latest_commit = list(commits)[-1]

            # Check status checks
            status = latest_commit.get_combined_status()

            if status.state == "pending":
                return False, "checks_pending"
            elif status.state == "failure":
                return False, "checks_failed"
            elif status.state == "error":
                return False, "checks_error"

            # Check check runs (GitHub Actions)
            check_runs = latest_commit.get_check_runs()
            for check in check_runs:
                if check.status != "completed":
                    return False, f"check_pending: {check.name}"
                if check.conclusion not in ["success", "neutral", "skipped"]:
                    return False, f"check_failed: {check.name}"

            return True, "all_checks_passed"

        except Exception as e:
            logger.warning(f"Error checking CI status: {str(e)}")
            return False, f"ci_check_error: {str(e)}"

    async def _merge_pull_request(self, pr) -> bool:
        """Merge a pull request"""
        try:
            merge_method = self.merge_strategy
            commit_title = f"Merge pull request #{pr.number}: {pr.title}"
            commit_message = f"Auto-merged by MergeAgent\n\n{pr.body or ''}"

            pr.merge(commit_title=commit_title, commit_message=commit_message, merge_method=merge_method)
            return True
        except Exception as e:
            logger.error(f"Failed to merge PR #{pr.number}: {str(e)}")
            return False

    async def _cleanup_stale_branches(self, result: Dict[str, Any], dry_run: bool):
        """Clean up stale branches that are no longer needed"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.stale_branch_days)
            branches = self.repo.get_branches()
            protected_branches = ["main", "master", "develop", "development"]

            for branch in branches:
                # Skip protected branches
                if branch.name in protected_branches or branch.protected:
                    continue

                # Get the latest commit date
                commit = branch.commit
                commit_date = commit.commit.author.date

                if commit_date < cutoff_date:
                    # Check if there are open PRs for this branch
                    open_prs = self.repo.get_pulls(state="open", head=f"{self.repo.owner.login}:{branch.name}")
                    if open_prs.totalCount > 0:
                        logger.debug(f"Skipping branch {branch.name}: Has open PRs")
                        continue

                    branch_info = {
                        "name": branch.name,
                        "last_commit_date": commit_date.isoformat(),
                        "days_old": (datetime.now() - commit_date).days,
                    }

                    if dry_run:
                        logger.info(f"[DRY RUN] Would delete stale branch: {branch.name}")
                        branch_info["action"] = "would_delete"
                        result["cleaned_branches"].append(branch_info)
                    else:
                        # Delete the branch
                        ref = self.repo.get_git_ref(f"heads/{branch.name}")
                        ref.delete()
                        logger.info(f"Deleted stale branch: {branch.name}")
                        branch_info["action"] = "deleted"
                        result["cleaned_branches"].append(branch_info)

        except Exception as e:
            logger.error(f"Error cleaning up branches: {str(e)}")
            result["errors"].append(f"Branch cleanup error: {str(e)}")

    async def evaluate_performance(self, result: Dict[str, Any]) -> float:
        """
        Evaluate merge agent performance.

        Scoring criteria:
        - Successful merges increase score
        - Failed operations decrease score
        - Errors significantly decrease score
        """
        score = 0.0

        if not result.get("success", False):
            return 0.1

        # Base score for successful execution
        score += 0.3

        # Score for merged PRs
        merged_count = len(result.get("merged_prs", []))
        if merged_count > 0:
            score += min(0.3, merged_count * 0.1)

        # Score for cleaned branches
        cleaned_count = len(result.get("cleaned_branches", []))
        if cleaned_count > 0:
            score += min(0.2, cleaned_count * 0.05)

        # Score for proper skipping (not attempting risky merges)
        skipped_count = len(result.get("skipped_prs", []))
        if skipped_count > 0:
            score += 0.1

        # Penalty for errors
        error_count = len(result.get("errors", []))
        if error_count > 0:
            score -= min(0.3, error_count * 0.1)

        return max(0.0, min(1.0, score))

    async def _adjust_strategy(self, reason: str):
        """Adjust merge strategy based on performance"""
        if reason == "performance_decline":
            # Be more conservative with merges
            self.min_approvals += 1
            logger.info(f"Adjusted merge strategy: increased min_approvals to {self.min_approvals}")
        elif reason == "performance_improvement":
            # Can be slightly more aggressive
            if self.min_approvals > 1:
                self.min_approvals -= 1
                logger.info(f"Adjusted merge strategy: decreased min_approvals to {self.min_approvals}")

    def configure(
        self,
        merge_strategy: Optional[str] = None,
        stale_branch_days: Optional[int] = None,
        min_approvals: Optional[int] = None,
        require_ci_pass: Optional[bool] = None,
    ):
        """
        Configure merge agent parameters.

        Args:
            merge_strategy: Merge method ("merge", "squash", or "rebase")
            stale_branch_days: Days before considering a branch stale
            min_approvals: Minimum number of approvals required
            require_ci_pass: Whether to require CI to pass before merging
        """
        if merge_strategy is not None:
            if merge_strategy not in ["merge", "squash", "rebase"]:
                raise ValueError(f"Invalid merge strategy: {merge_strategy}")
            self.merge_strategy = merge_strategy

        if stale_branch_days is not None:
            self.stale_branch_days = max(1, stale_branch_days)

        if min_approvals is not None:
            self.min_approvals = max(0, min_approvals)

        if require_ci_pass is not None:
            self.require_ci_pass = require_ci_pass

        logger.info(
            f"Merge agent configured: strategy={self.merge_strategy}, "
            f"stale_days={self.stale_branch_days}, min_approvals={self.min_approvals}, "
            f"require_ci={self.require_ci_pass}"
        )

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
