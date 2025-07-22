from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from bangumi_tracker.torrent import Torrent


@dataclass
class Episode:
    id: str
    title: str
    link: str
    torrent: Torrent
    show_title: Optional[str] = None
    season: Optional[int] = None
    save_path: Optional[Path] = None
    category: Optional[str] = None
