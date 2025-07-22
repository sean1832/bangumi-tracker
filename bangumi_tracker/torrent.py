import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

import bencodepy
import requests

from bangumi_tracker import logger


@dataclass
class Torrent:
    url: str
    size: Optional[int] = None  # Size in bytes, can be None if not available
    hash: Optional[str] = None  # SHA1 hash of the torrent info
    name: Optional[str] = None


class TorrentFetcher:
    def __init__(self, session: Optional[requests.Session]) -> None:
        self.session = session or requests.Session()

    def fetch(self, url: str, timeout: int = 10) -> Dict[bytes, Any]:
        try:
            resp = self.session.get(url, timeout=timeout)
            resp.raise_for_status()

            # Tell the type‑checker this is a dict
            raw = bencodepy.decode(resp.content)
            if not isinstance(raw, dict):
                raise ValueError("Unexpected metadata format")
            meta: Dict[bytes, Any] = raw
            return meta
        except requests.Timeout:
            logger.error(f"Timeout after {timeout}s")
            raise
        except requests.RequestException as e:
            logger.error(f"Fetch error: {e}")
            raise

    def fetch_meta(self, url: str, timeout: int = 10) -> Torrent:
        try:
            meta = self.fetch(url, timeout)
            return Torrent(
                url=url,
                size=self._extract_size(meta),
                hash=self._calculate_hash(meta),
                name=self._extract_name(meta),
            )

        except requests.Timeout:
            logger.error(f"Timeout after {timeout}s")
            raise
        except requests.RequestException as e:
            logger.error(f"Fetch error: {e}")
            raise

    @classmethod
    def _calculate_hash(cls, meta: Mapping[bytes, Any]) -> str:
        info = meta.get(b"info")
        if not isinstance(info, (bytes, dict, list)):
            raise ValueError("Invalid torrent metadata: missing 'info'")
        data = bencodepy.encode(info)
        return hashlib.sha1(data).hexdigest()

    @classmethod
    def _extract_name(cls, meta: Mapping[bytes, Any]) -> str:
        info = meta.get(b"info")
        if not isinstance(info, dict):
            raise ValueError("Invalid torrent metadata: missing 'info'")
        raw_name = info.get(b"name", b"")
        return raw_name.decode("utf-8", errors="replace")

    @classmethod
    def _extract_size(cls, meta: Mapping[bytes, Any]) -> int:
        info = meta.get(b"info")
        if not isinstance(info, dict):
            raise ValueError("Invalid torrent metadata: missing 'info'")
        raw_length = info.get(b"length", 0)
        if isinstance(raw_length, int):
            return raw_length
        elif isinstance(raw_length, list):
            return sum(item.get(b"length", 0) for item in raw_length)
        else:
            raise ValueError("Invalid torrent metadata: 'length' is not an integer or list")
