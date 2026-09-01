"""
Traversal engine for recursively downloading WHO ICD-10 2019 terminology hierarchy.
"""

import signal
from collections import deque
from typing import List, Optional, Set
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from database.repositories import ICD10RawRepository
from extractor.icd11_client import ICD11Client
from extractor.endpoints import get_icd10_base_endpoint
from utils.logger import api_logger


class ICD10Downloader:
    """BFS Downloader for WHO ICD-10 hierarchy with state recovery and graceful shutdown."""

    def __init__(self, client: Optional[ICD11Client] = None, repo: Optional[ICD10RawRepository] = None):
        self.client = client or ICD11Client()
        self.repo = repo or ICD10RawRepository()
        self.interrupted = False

        # Register SIGINT / Ctrl+C handler
        try:
            signal.signal(signal.SIGINT, self._handle_interrupt)
        except ValueError:
            pass

    def _handle_interrupt(self, signum, frame):
        """Signal handler for graceful stop on SIGINT."""
        api_logger.warning("Received cancellation signal (Ctrl+C). Finishing current item and saving progress...")
        self.interrupted = True

    def download_hierarchy(self, root_uris: Optional[List[str]] = None) -> int:
        """
        Recursively download ICD-10 entities starting from root 2019 release.

        Args:
            root_uris: Optional starting URIs.

        Returns:
            Total count of newly downloaded ICD-10 entity documents.
        """
        self.interrupted = False
        api_logger.info("Initializing ICD-10 hierarchy downloader...")

        already_downloaded = self.repo.get_all_downloaded_uris()
        api_logger.info(f"Loaded {len(already_downloaded)} existing ICD-10 entities from database (Resume Checkpoint).")

        visited: Set[str] = set(already_downloaded)
        queue: deque = deque()
        download_count = 0

        # Discover initial seeds from ICD-10 base endpoint
        if root_uris:
            seeds = root_uris
        else:
            root_endpoint = get_icd10_base_endpoint()
            api_logger.info(f"Fetching ICD-10 root release from: {root_endpoint}")
            try:
                root_payload = self.client.get_entity_by_url(root_endpoint)
                self.repo.insert_or_update_raw_entity(root_payload)
                seeds = root_payload.get("child", [])
            except Exception as e:
                api_logger.error(f"Failed to fetch ICD-10 root endpoint: {e}")
                return 0

        for seed in seeds:
            uri = seed if isinstance(seed, str) else seed.get("@id") or seed.get("uri") or seed.get("id")
            if uri and uri not in visited:
                queue.append(uri)
                visited.add(uri)

        api_logger.info(f"Starting ICD-10 traversal queue with {len(queue)} root child entities.")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            transient=False,
        ) as progress:
            task_id = progress.add_task("[cyan]Downloading WHO ICD-10 Entities...", total=len(queue))

            while queue:
                if self.interrupted:
                    api_logger.warning("Downloader stopped gracefully by user interrupt.")
                    break

                current_uri = queue.popleft()

                try:
                    entity_payload = self.client.get_entity_by_url(current_uri)
                    self.repo.insert_or_update_raw_entity(entity_payload)
                    download_count += 1

                    # Extract child entity links
                    children = entity_payload.get("child", [])
                    for child in children:
                        child_uri = child if isinstance(child, str) else child.get("@id") or child.get("uri") or child.get("id")
                        if child_uri and child_uri not in visited:
                            visited.add(child_uri)
                            queue.append(child_uri)

                except Exception as e:
                    api_logger.error(f"Error fetching ICD-10 entity '{current_uri}': {e}")

                progress.update(task_id, advance=1, total=len(visited))

        api_logger.info(f"ICD-10 download completed. {download_count} new entities downloaded.")
        return download_count
