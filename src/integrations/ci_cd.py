#!/usr/bin/env python3
"""
CI/CD integration for AllSeeingEye
"""

import os
import json
import logging
import requests
import tempfile
import time
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AllSeeingEye-CI-CD")

class CICDIntegration:
    """Base class for CI/CD integrations"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000", 
                 api_key: Optional[str] = None):
        """
        Initialize the CI/CD integration.
        
        Args:
            base_url: Base URL for the AllSeeingEye API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        
    def get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests.
        
        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers
    
    def analyze_directory(self, 
                         directory: str,
                         exclude_dirs: List[str] = None,
                         output_format: str = "json",
                         use_llm: bool = False,
                         llm_provider: Optional[str] = None,
                         llm_model: Optional[str] = None,
                         max_workers: int = 4,
                         chunk_size: int = 100,
                         wait: bool = True,
                         timeout: int = 3600,
                         poll_interval: int = 5,
                         callback: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
        """
        Analyze a directory using the AllSeeingEye API.
        
        Args:
            directory: Path to the directory to analyze
            exclude_dirs: List of directories to exclude
            output_format: Output format (json, markdown, text)
            use_llm: Whether to use LLM for analysis
            llm_provider: LLM provider (ollama, openai, etc.)
            llm_model: LLM model name
            max_workers: Maximum number of worker processes
            chunk_size: Size of processing chunks
            wait: Whether to wait for analysis to complete
            timeout: Maximum time to wait (in seconds)
            poll_interval: Time between status checks (in seconds)
            callback: Optional callback function for progress updates
            
        Returns:
            Analysis result or task information
        """
        # Prepare request data
        request_data = {
            "directory": directory,
            "exclude_dirs": exclude_dirs or [".git", "node_modules", "__pycache__"],
            "output_format": output_format,
            "use_llm": use_llm,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "max_workers": max_workers,
            "chunk_size": chunk_size
        }
        
        # Start analysis
        logger.info(f"Starting analysis of {directory}")
        response = requests.post(
            f"{self.base_url}/analyze",
            json=request_data,
            headers=self.get_headers()
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to start analysis: {response.text}")
            response.raise_for_status()
        
        # Get task information
        task_info = response.json()
        task_id = task_info["task_id"]
        
        logger.info(f"Analysis task started: {task_id}")
        
        if not wait:
            return task_info
        
        # Wait for analysis to complete
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Get task status
            status_response = requests.get(
                f"{self.base_url}/analyze/{task_id}/status",
                headers=self.get_headers()
            )
            
            if status_response.status_code != 200:
                logger.error(f"Failed to get task status: {status_response.text}")
                status_response.raise_for_status()
            
            # Parse status
            status_info = status_response.json()
            
            # Check if task is completed
            if status_info["status"] == "completed":
                logger.info(f"Analysis completed: {task_id}")
                
                # Get result
                result_response = requests.get(
                    f"{self.base_url}/analyze/{task_id}/result",
                    headers=self.get_headers()
                )
                
                if result_response.status_code != 200:
                    logger.error(f"Failed to get task result: {result_response.text}")
                    result_response.raise_for_status()
                
                return result_response.json()
            
            # Check if task failed
            if status_info["status"] == "failed":
                logger.error(f"Analysis failed: {status_info['message']}")
                raise Exception(f"Analysis failed: {status_info['message']}")
            
            # Report progress
            if callback:
                callback(status_info["progress"], status_info["message"])
            else:
                logger.info(f"Progress: {status_info['progress']:.2f} - {status_info['message']}")
            
            # Wait for next check
            time.sleep(poll_interval)
        
        # Timeout
        logger.error(f"Analysis timed out after {timeout} seconds")
        raise TimeoutError(f"Analysis timed out after {timeout} seconds")
    
    def analyze_zip(self,
                   zip_file: str,
                   exclude_dirs: List[str] = None,
                   output_format: str = "json",
                   use_llm: bool = False,
                   llm_provider: Optional[str] = None,
                   llm_model: Optional[str] = None,
                   max_workers: int = 4,
                   chunk_size: int = 100,
                   wait: bool = True,
                   timeout: int = 3600,
                   poll_interval: int = 5,
                   callback: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
        """
        Analyze a ZIP file using the AllSeeingEye API.
        
        Args:
            zip_file: Path to the ZIP file to analyze
            exclude_dirs: List of directories to exclude
            output_format: Output format (json, markdown, text)
            use_llm: Whether to use LLM for analysis
            llm_provider: LLM provider (ollama, openai, etc.)
            llm_model: LLM model name
            max_workers: Maximum number of worker processes
            chunk_size: Size of processing chunks
            wait: Whether to wait for analysis to complete
            timeout: Maximum time to wait (in seconds)
            poll_interval: Time between status checks (in seconds)
            callback: Optional callback function for progress updates
            
        Returns:
            Analysis result or task information
        """
        # Prepare multipart form data
        files = {
            'file': (os.path.basename(zip_file), open(zip_file, 'rb'), 'application/zip')
        }
        
        data = {
            'exclude_dirs': ','.join(exclude_dirs or [".git", "node_modules", "__pycache__"]),
            'output_format': output_format,
            'use_llm': str(use_llm).lower(),
            'max_workers': str(max_workers),
            'chunk_size': str(chunk_size)
        }
        
        if use_llm and llm_provider:
            data['llm_provider'] = llm_provider
            
        if use_llm and llm_model:
            data['llm_model'] = llm_model
        
        # Start analysis
        logger.info(f"Starting analysis of ZIP file {zip_file}")
        headers = self.get_headers()
        
        # Remove Content-Type from headers for multipart form data
        if 'Content-Type' in headers:
            del headers['Content-Type']
        
        response = requests.post(
            f"{self.base_url}/analyze/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to start analysis: {response.text}")
            response.raise_for_status()
        
        # Get task information
        task_info = response.json()
        task_id = task_info["task_id"]
        
        logger.info(f"Analysis task started: {task_id}")
        
        if not wait:
            return task_info
        
        # Wait for analysis to complete
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Get task status
            status_response = requests.get(
                f"{self.base_url}/analyze/{task_id}/status",
                headers=self.get_headers()
            )
            
            if status_response.status_code != 200:
                logger.error(f"Failed to get task status: {status_response.text}")
                status_response.raise_for_status()
            
            # Parse status
            status_info = status_response.json()
            
            # Check if task is completed
            if status_info["status"] == "completed":
                logger.info(f"Analysis completed: {task_id}")
                
                # Get result
                result_response = requests.get(
                    f"{self.base_url}/analyze/{task_id}/result",
                    headers=self.get_headers()
                )
                
                if result_response.status_code != 200:
                    logger.error(f"Failed to get task result: {result_response.text}")
                    result_response.raise_for_status()
                
                return result_response.json()
            
            # Check if task failed
            if status_info["status"] == "failed":
                logger.error(f"Analysis failed: {status_info['message']}")
                raise Exception(f"Analysis failed: {status_info['message']}")
            
            # Report progress
            if callback:
                callback(status_info["progress"], status_info["message"])
            else:
                logger.info(f"Progress: {status_info['progress']:.2f} - {status_info['message']}")
            
            # Wait for next check
            time.sleep(poll_interval)
        
        # Timeout
        logger.error(f"Analysis timed out after {timeout} seconds")
        raise TimeoutError(f"Analysis timed out after {timeout} seconds")
    
    def download_result(self, task_id: str, output_path: str) -> str:
        """
        Download the result file of an analysis task.
        
        Args:
            task_id: Task ID
            output_path: Path to save the result file
            
        Returns:
            Path to the downloaded file
        """
        # Get file
        response = requests.get(
            f"{self.base_url}/analyze/{task_id}/download",
            headers=self.get_headers(),
            stream=True
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to download result: {response.text}")
            response.raise_for_status()
        
        # Save file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Result downloaded to {output_path}")
        return output_path
    
    def register_webhook(self, url: str, events: List[str] = None, headers: Dict[str, str] = None) -> str:
        """
        Register a webhook for event notifications.
        
        Args:
            url: Webhook URL
            events: List of events to listen for
            headers: Custom headers for webhook requests
            
        Returns:
            Webhook ID
        """
        # Prepare request data
        request_data = {
            "url": url,
            "events": events or ["analysis_complete", "analysis_failed"],
            "headers": headers or {}
        }
        
        # Register webhook
        response = requests.post(
            f"{self.base_url}/webhooks/register",
            json=request_data,
            headers=self.get_headers()
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to register webhook: {response.text}")
            response.raise_for_status()
        
        webhook_info = response.json()
        webhook_id = webhook_info["webhook_id"]
        
        logger.info(f"Webhook registered: {webhook_id}")
        return webhook_id
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete a registered webhook.
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            True if successful
        """
        # Delete webhook
        response = requests.delete(
            f"{self.base_url}/webhooks/{webhook_id}",
            headers=self.get_headers()
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to delete webhook: {response.text}")
            response.raise_for_status()
        
        logger.info(f"Webhook deleted: {webhook_id}")
        return True


class GitHubActionsIntegration(CICDIntegration):
    """GitHub Actions integration for AllSeeingEye"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000", 
                 api_key: Optional[str] = None,
                 github_token: Optional[str] = None):
        """
        Initialize the GitHub Actions integration.
        
        Args:
            base_url: Base URL for the AllSeeingEye API
            api_key: Optional API key for authentication
            github_token: GitHub token for API access
        """
        super().__init__(base_url, api_key)
        self.github_token = github_token
        
        # Get GitHub environment variables
        self.github_repository = os.environ.get("GITHUB_REPOSITORY")
        self.github_workflow = os.environ.get("GITHUB_WORKFLOW")
        self.github_run_id = os.environ.get("GITHUB_RUN_ID")
        self.github_ref = os.environ.get("GITHUB_REF")
        
    def post_analysis_comment(self, 
                             result: Dict[str, Any], 
                             pr_number: Optional[int] = None,
                             commit_hash: Optional[str] = None,
                             include_details: bool = False) -> bool:
        """
        Post analysis results as a GitHub comment.
        
        Args:
            result: Analysis result
            pr_number: Pull request number (or None to detect from environment)
            commit_hash: Commit hash (or None to detect from environment)
            include_details: Whether to include detailed results
            
        Returns:
            True if successful
        """
        if not self.github_token:
            logger.error("GitHub token is required for posting comments")
            return False
        
        if not self.github_repository:
            logger.error("GITHUB_REPOSITORY environment variable is not set")
            return False
        
        # Determine PR number from environment if not provided
        if not pr_number and 'pull/' in self.github_ref:
            try:
                pr_number = int(self.github_ref.split('/')[2])
            except (IndexError, ValueError):
                logger.warning("Could not determine PR number from GITHUB_REF")
        
        # Generate comment body
        comment_body = f"## AllSeeingEye Analysis Results\n\n"
        
        if "statistics" in result.get("result", {}):
            stats = result["result"]["statistics"]
            comment_body += f"- Total files: {stats.get('total_files', 0)}\n"
            comment_body += f"- Lines of code: {stats.get('total_lines', 0)}\n"
            comment_body += f"- File categories:\n"
            
            categories = stats.get("files_by_category", {})
            for category, count in categories.items():
                comment_body += f"  - {category}: {count}\n"
            
            comment_body += "\n"
        
        if "recommendations" in result.get("result", {}):
            comment_body += "### Recommendations\n\n"
            
            recommendations = result["result"]["recommendations"]
            for rec in recommendations[:5]:  # Show top 5 recommendations
                comment_body += f"- **{rec.get('title', 'Recommendation')}**: {rec.get('description', '')}\n"
            
            comment_body += "\n"
        
        comment_body += f"[View full analysis]({self.base_url}/analyze/{result['task_id']}/download)\n"
        
        # Post comment using the GitHub API
        if pr_number:
            # Comment on PR
            api_url = f"https://api.github.com/repos/{self.github_repository}/issues/{pr_number}/comments"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.post(
                api_url,
                json={"body": comment_body},
                headers=headers
            )
            
            if response.status_code not in (201, 200):
                logger.error(f"Failed to post comment on PR #{pr_number}: {response.text}")
                return False
            
            logger.info(f"Comment posted on PR #{pr_number}")
            return True
            
        elif commit_hash:
            # Comment on commit
            api_url = f"https://api.github.com/repos/{self.github_repository}/commits/{commit_hash}/comments"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.post(
                api_url,
                json={"body": comment_body},
                headers=headers
            )
            
            if response.status_code not in (201, 200):
                logger.error(f"Failed to post comment on commit {commit_hash}: {response.text}")
                return False
            
            logger.info(f"Comment posted on commit {commit_hash}")
            return True
        
        else:
            logger.error("Either PR number or commit hash is required for posting comments")
            return False


class GitLabCIIntegration(CICDIntegration):
    """GitLab CI integration for AllSeeingEye"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000", 
                 api_key: Optional[str] = None,
                 gitlab_token: Optional[str] = None):
        """
        Initialize the GitLab CI integration.
        
        Args:
            base_url: Base URL for the AllSeeingEye API
            api_key: Optional API key for authentication
            gitlab_token: GitLab token for API access
        """
        super().__init__(base_url, api_key)
        self.gitlab_token = gitlab_token
        
        # Get GitLab environment variables
        self.gitlab_project_id = os.environ.get("CI_PROJECT_ID")
        self.gitlab_merge_request_iid = os.environ.get("CI_MERGE_REQUEST_IID")
        self.gitlab_commit_sha = os.environ.get("CI_COMMIT_SHA")
        self.gitlab_api_url = os.environ.get("CI_API_V4_URL", "https://gitlab.com/api/v4")
        
    def post_analysis_comment(self, 
                             result: Dict[str, Any], 
                             mr_iid: Optional[str] = None,
                             commit_sha: Optional[str] = None,
                             include_details: bool = False) -> bool:
        """
        Post analysis results as a GitLab comment.
        
        Args:
            result: Analysis result
            mr_iid: Merge request IID (or None to detect from environment)
            commit_sha: Commit SHA (or None to detect from environment)
            include_details: Whether to include detailed results
            
        Returns:
            True if successful
        """
        if not self.gitlab_token:
            logger.error("GitLab token is required for posting comments")
            return False
        
        if not self.gitlab_project_id:
            logger.error("CI_PROJECT_ID environment variable is not set")
            return False
        
        # Use environment variables if not provided
        mr_iid = mr_iid or self.gitlab_merge_request_iid
        commit_sha = commit_sha or self.gitlab_commit_sha
        
        # Generate comment body
        comment_body = f"## AllSeeingEye Analysis Results\n\n"
        
        if "statistics" in result.get("result", {}):
            stats = result["result"]["statistics"]
            comment_body += f"- Total files: {stats.get('total_files', 0)}\n"
            comment_body += f"- Lines of code: {stats.get('total_lines', 0)}\n"
            comment_body += f"- File categories:\n"
            
            categories = stats.get("files_by_category", {})
            for category, count in categories.items():
                comment_body += f"  - {category}: {count}\n"
            
            comment_body += "\n"
        
        if "recommendations" in result.get("result", {}):
            comment_body += "### Recommendations\n\n"
            
            recommendations = result["result"]["recommendations"]
            for rec in recommendations[:5]:  # Show top 5 recommendations
                comment_body += f"- **{rec.get('title', 'Recommendation')}**: {rec.get('description', '')}\n"
            
            comment_body += "\n"
        
        comment_body += f"[View full analysis]({self.base_url}/analyze/{result['task_id']}/download)\n"
        
        # Post comment using the GitLab API
        if mr_iid:
            # Comment on merge request
            api_url = f"{self.gitlab_api_url}/projects/{self.gitlab_project_id}/merge_requests/{mr_iid}/notes"
            headers = {
                "PRIVATE-TOKEN": self.gitlab_token
            }
            
            response = requests.post(
                api_url,
                json={"body": comment_body},
                headers=headers
            )
            
            if response.status_code not in (201, 200):
                logger.error(f"Failed to post comment on MR !{mr_iid}: {response.text}")
                return False
            
            logger.info(f"Comment posted on MR !{mr_iid}")
            return True
            
        elif commit_sha:
            # Comment on commit
            api_url = f"{self.gitlab_api_url}/projects/{self.gitlab_project_id}/repository/commits/{commit_sha}/comments"
            headers = {
                "PRIVATE-TOKEN": self.gitlab_token
            }
            
            response = requests.post(
                api_url,
                json={"note": comment_body},
                headers=headers
            )
            
            if response.status_code not in (201, 200):
                logger.error(f"Failed to post comment on commit {commit_sha}: {response.text}")
                return False
            
            logger.info(f"Comment posted on commit {commit_sha}")
            return True
        
        else:
            logger.error("Either merge request IID or commit SHA is required for posting comments")
            return False


class JenkinsIntegration(CICDIntegration):
    """Jenkins integration for AllSeeingEye"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000", 
                 api_key: Optional[str] = None,
                 jenkins_url: Optional[str] = None,
                 jenkins_user: Optional[str] = None,
                 jenkins_token: Optional[str] = None):
        """
        Initialize the Jenkins integration.
        
        Args:
            base_url: Base URL for the AllSeeingEye API
            api_key: Optional API key for authentication
            jenkins_url: Jenkins server URL
            jenkins_user: Jenkins username
            jenkins_token: Jenkins API token
        """
        super().__init__(base_url, api_key)
        self.jenkins_url = jenkins_url
        self.jenkins_user = jenkins_user
        self.jenkins_token = jenkins_token
        
        # Get Jenkins environment variables
        self.build_url = os.environ.get("BUILD_URL")
        self.job_name = os.environ.get("JOB_NAME")
        self.build_number = os.environ.get("BUILD_NUMBER")
        
    def publish_artifact(self, 
                        result: Dict[str, Any], 
                        artifact_name: str = "allseeingeye_analysis.json") -> bool:
        """
        Publish analysis results as a Jenkins artifact.
        
        Args:
            result: Analysis result
            artifact_name: Name of the artifact
            
        Returns:
            True if successful
        """
        if not self.build_url or not self.job_name or not self.build_number:
            logger.error("Jenkins environment variables (BUILD_URL, JOB_NAME, BUILD_NUMBER) are not set")
            return False
        
        # Download result file
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, artifact_name)
        
        try:
            self.download_result(result["task_id"], temp_file)
            
            # Upload as artifact using Jenkins REST API
            if self.jenkins_url and self.jenkins_user and self.jenkins_token:
                # Upload via Jenkins REST API
                artifact_url = f"{self.jenkins_url}/job/{self.job_name}/{self.build_number}/artifact"
                
                with open(temp_file, 'rb') as f:
                    response = requests.post(
                        artifact_url,
                        files={"file": (artifact_name, f)},
                        auth=(self.jenkins_user, self.jenkins_token)
                    )
                    
                    if response.status_code not in (201, 200):
                        logger.error(f"Failed to upload artifact: {response.text}")
                        return False
                
                logger.info(f"Artifact uploaded to {artifact_url}/{artifact_name}")
                return True
                
            else:
                # Copy to Jenkins workspace
                workspace = os.environ.get("WORKSPACE")
                if not workspace:
                    logger.error("WORKSPACE environment variable not set")
                    return False
                
                artifact_path = os.path.join(workspace, artifact_name)
                shutil.copy(temp_file, artifact_path)
                
                logger.info(f"Artifact copied to {artifact_path}")
                return True
                
        finally:
            # Clean up
            shutil.rmtree(temp_dir)


# Factory function to get CI/CD integration based on environment
def get_ci_cd_integration(api_base_url: str = "http://localhost:8000", api_key: Optional[str] = None) -> CICDIntegration:
    """
    Get a CI/CD integration instance based on the current environment.
    
    Args:
        api_base_url: Base URL for the AllSeeingEye API
        api_key: Optional API key for authentication
        
    Returns:
        CICDIntegration instance
    """
    # Check for GitHub Actions
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return GitHubActionsIntegration(
            base_url=api_base_url,
            api_key=api_key,
            github_token=os.environ.get("GITHUB_TOKEN")
        )
    
    # Check for GitLab CI
    if os.environ.get("GITLAB_CI") == "true":
        return GitLabCIIntegration(
            base_url=api_base_url,
            api_key=api_key,
            gitlab_token=os.environ.get("GITLAB_TOKEN") or os.environ.get("CI_JOB_TOKEN")
        )
    
    # Check for Jenkins
    if os.environ.get("JENKINS_URL"):
        return JenkinsIntegration(
            base_url=api_base_url,
            api_key=api_key,
            jenkins_url=os.environ.get("JENKINS_URL"),
            jenkins_user=os.environ.get("JENKINS_USER"),
            jenkins_token=os.environ.get("JENKINS_API_TOKEN")
        )
    
    # Default integration
    return CICDIntegration(base_url=api_base_url, api_key=api_key)
