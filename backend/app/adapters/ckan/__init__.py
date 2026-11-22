"""HTTP client for a CKAN open-data portal, with a simple on-disk cache of raw files."""

import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class CkanError(RuntimeError):
    pass


class CkanClient:
    """Implements `CatalogPort` against the CKAN Action API.

    Downloaded files are cached in `cache_dir` (keyed by URL) so re-running the ingestion does not
    download them again. Delete the cache folder to force a fresh download.
    """

    def __init__(
        self,
        api_url: str,
        cache_dir: Path | None = None,
        timeout_seconds: float = 300,
        session: requests.Session | None = None,
    ) -> None:
        self._api_url = api_url.rstrip("/")
        self._cache_dir = cache_dir
        # (connect timeout, read timeout)
        self._timeout = (10, timeout_seconds)
        self._session = session or requests.Session()

    def get_dataset(self, dataset_id: str) -> dict:
        response = self._session.get(
            f"{self._api_url}/package_show", params={"id": dataset_id}, timeout=self._timeout
        )
        response.raise_for_status()
        body = response.json()
        if not body.get("success"):
            raise CkanError(f"CKAN package_show failed for '{dataset_id}': {body.get('error')}")
        return body["result"]

    def download(self, url: str) -> bytes:
        cached = self._cache_path(url)
        if cached and cached.exists():
            logger.info("Using cached file %s", cached.name)
            return cached.read_bytes()

        logger.info("Downloading %s", url)
        response = self._session.get(url, timeout=self._timeout)
        response.raise_for_status()
        content = response.content
        if cached:
            cached.parent.mkdir(parents=True, exist_ok=True)
            partial = cached.with_suffix(cached.suffix + ".part")
            partial.write_bytes(content)
            partial.replace(cached)  # never leave a half-written file in the cache
        return content

    def _cache_path(self, url: str) -> Path | None:
        if self._cache_dir is None:
            return None
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        suffix = Path(urlparse(url).path).suffix.lower()
        return self._cache_dir / f"{digest}{suffix}"
