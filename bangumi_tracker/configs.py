from dataclasses import dataclass
from typing import List


@dataclass
class QbittorrentConfig:
    host: str
    port: int
    username: str
    password: str
    save_path_root: str


@dataclass
class ShowConfig:
    url: str
    title: str
    season: int
    exclude_patterns: List[str]  # Optional patterns to exclude certain episodes
    category: str


@dataclass
class BangumiConfig:
    qbittorrent: QbittorrentConfig
    shows: List[ShowConfig]
    pull_interval_sec: int


def load_config(config_data: dict) -> BangumiConfig:
    qbittorrent_config = QbittorrentConfig(
        host=config_data["qbittorrent"]["host"],
        port=config_data["qbittorrent"]["port"],
        username=config_data["qbittorrent"]["username"],
        password=config_data["qbittorrent"]["password"],
        save_path_root=config_data["qbittorrent"]["save_path_root"],
    )

    shows = [
        ShowConfig(
            url=feed["url"],
            title=feed["title"],
            season=feed["season"],
            exclude_patterns=feed.get("exclude_patterns", []),
            category=feed.get("category", "anime"),
        )
        for feed in config_data["shows"]
    ]
    pull_interval = config_data["settings"].get(
        "pull_interval_sec", 1800
    )  # Default to 30 minutes if not specified

    return BangumiConfig(
        qbittorrent=qbittorrent_config,
        shows=shows,
        pull_interval_sec=pull_interval,
    )
