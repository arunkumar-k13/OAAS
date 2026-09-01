"""
Traversal engine for recursively downloading ICD-11 terminology hierarchy with checkpointing and resume support.
"""

import signal
import sys
from collections import deque
from typing import List, Optional, Set
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config.settings import settings
from database.repositories import RawDataRepository
from extractor.icd11_client import ICD11Client
from utils.logger import api_logger, mongo_logger


class ICD11Downloader:
    """BFS Downloader for WHO ICD-11 hierarchy with state recovery and graceful shutdown."""

    def __init__(self, client: Optional[ICD11Client] = None, repo: Optional[RawDataRepository] = None):
        self.client = client or ICD11Client()
        self.repo = repo or RawDataRepository()
        self.interrupted = False

        # Register SIGINT / Ctrl+C handler
        signal.signal(signal.SIGINT, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        """Signal handler for graceful stop on SIGINT."""
        api_logger.warning("Received cancellation signal (Ctrl+C). Finishing current item and saving progress...")
        self.interrupted = True

    def download_hierarchy(self, root_uris: Optional[List[str]] = None, max_depth: Optional[int] = None) -> int:
        """
        Recursively download ICD-11 entities starting from root linearization.

        Args:
            root_uris: Optional list of starting URIs. If None, fetches root MMS chapters.
            max_depth: Optional limit on hierarchy traversal depth.

        Returns:
            Total count of newly downloaded entity documents.
        """
        self.interrupted = False
        api_logger.info("Initializing ICD-11 hierarchy downloader...")

        # Load existing downloaded URIs for checkpoint resume
        already_downloaded = self.repo.get_all_downloaded_uris()
        api_logger.info(f"Loaded {len(already_downloaded)} existing entities from database (Resume Checkpoint).")

        visited: Set[str] = set(already_downloaded)
        queue: deque = deque()
        download_count = 0

        # Discover initial seeds
        if root_uris:
            seeds = root_uris
        else:
            try:
                root_payload = self.client.get_linearization_root()
                # Save root document itself
                self.repo.insert_or_update_raw_entity(root_payload)
                seeds = root_payload.get("child", [])
            except Exception as err:
                api_logger.error(f"Failed to fetch linearization root: {err}")
                raise

        for seed in seeds:
            if seed not in visited:
                queue.append((seed, 1))
                visited.add(seed)

        # Discover unvisited child targets from existing downloaded documents (Resume Checkpoint)
        raw_docs = self.repo.fetch_all_raw_documents()
        for raw in raw_docs:
            children = raw.get("child", [])
            for child_uri in children:
                if child_uri not in visited:
                    queue.append((child_uri, 3))
                    visited.add(child_uri)

        api_logger.info(f"Queue populated with {len(queue)} entity targets to download.")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Downloading ICD-11 Entities...", total=len(queue) + len(already_downloaded))

            batch_buffer = []
            BATCH_SIZE = 50

            while queue and not self.interrupted:
                current_uri, depth = queue.popleft()
                progress.update(task, advance=1, description=f"[cyan]Fetching Entity (Depth {depth})...")

                try:
                    entity_json = self.client.get_entity(current_uri)
                    batch_buffer.append(entity_json)
                    download_count += 1

                    # Discover children for next depth
                    if max_depth is None or depth < max_depth:
                        children = entity_json.get("child", [])
                        for child_uri in children:
                            if child_uri not in visited:
                                visited.add(child_uri)
                                queue.append((child_uri, depth + 1))
                                progress.update(task, total=progress.tasks[0].total + 1)

                    # Flush buffer when batch size is reached
                    if len(batch_buffer) >= BATCH_SIZE:
                        saved = self.repo.bulk_insert_raw_entities(batch_buffer)
                        mongo_logger.info(f"Persisted batch of {saved} raw entity documents to icd11_raw.")
                        batch_buffer.clear()

                except Exception as err:
                    api_logger.error(f"Error fetching entity at URI '{current_uri}': {err}")
                    continue

            # Flush remaining items in buffer
            if batch_buffer:
                saved = self.repo.bulk_insert_raw_entities(batch_buffer)
                mongo_logger.info(f"Persisted final batch of {saved} raw entity documents to icd11_raw.")
                batch_buffer.clear()

        if self.interrupted:
            api_logger.warning(f"Download process interrupted by user. Total downloaded this run: {download_count}")
        else:
            api_logger.info(f"Download process completed successfully. Total downloaded this run: {download_count}")

        return download_count
