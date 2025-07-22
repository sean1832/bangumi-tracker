import argparse
import logging

# from fnmatch import fnmatch
import re
import time
import tomllib
from datetime import datetime
from pathlib import Path
from typing import List

import qbittorrentapi
import requests

from bangumi_tracker import __version__, logger
from bangumi_tracker.configs import BangumiConfig, load_config
from bangumi_tracker.episode import Episode
from bangumi_tracker.rss import RssFeed
from bangumi_tracker.torrent import TorrentFetcher


def configure_logging(dir: Path, debug: bool) -> None:
    # Ensure your log directory exists
    dir.mkdir(parents=True, exist_ok=True)

    # Compute today’s filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = dir / f"{date_str}.log"

    # Pick your level
    level = logging.DEBUG if debug else logging.INFO

    # Create handlers
    handlers = []  #  type is list[Any], so you can mix handlers
    handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    handlers.append(logging.StreamHandler())

    # Apply configuration
    logging.basicConfig(
        level=level,
        format="%(asctime)s - [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Bangumi Tracker CLI")
    parser.add_argument("--version", action="version", version=f"Bangumi Tracker {__version__}")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to the configuration file. must be toml format.",
        required=True,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def operation(
    config: BangumiConfig, client: qbittorrentapi.Client, torrent_fetcher: TorrentFetcher
):
    """Perform the main operation of the Bangumi Tracker.

    Args:
        config (BangumiConfig): The configuration object.
        client (qbittorrentapi.Client): The qBittorrent client object.
    """

    # fetch existing torrents from qBittorrent
    torrents = client.torrents_info()
    existing_hashes = {torrent.hash for torrent in torrents}
    logger.info(f"Fetched {len(existing_hashes)} existing torrents from qBittorrent")

    # match RSS feeds with existing torrents
    episodes_to_download: List[Episode] = []
    for show in config.shows:
        episodes = RssFeed.fetch_episodes(show.url, reverse=True)
        i = 0
        for episode in episodes:
            logger.debug(f"Found new episode: {episode.title}")
            # check if the episode title matches any exclude patterns
            if show.exclude_patterns:
                # Use regex to match exclude patterns
                if any(re.search(pattern, episode.title) for pattern in show.exclude_patterns):
                    logger.debug(f"Excluding episode {episode.title} due to exclude patterns")
                    continue

            # fetch the torrent metadata including hash and name
            episode.torrent = torrent_fetcher.fetch_meta(episode.torrent.url)
            logger.debug(f"Fetched torrent metadata for episode {episode.title}")

            # check if current hash is already in qBittorrent
            if episode.torrent.hash in existing_hashes:
                logger.debug(f"Episode {episode.title} already exists in qBittorrent")
                continue

            i += 1

            folder_name = f"{show.title} - S{show.season:02d}E{i:02d}"
            if episode.torrent.name:
                folder_name = Path(episode.torrent.name).stem

            # set the path for the episode
            episode.save_path = (
                Path(config.qbittorrent.save_path_root).expanduser().resolve()
                / show.title
                / f"Season {show.season}"
                / folder_name
            )
            episode.season = show.season
            episode.show_title = show.title
            episode.category = show.category

            episodes_to_download.append(episode)

    if not episodes_to_download:
        logger.warning("No new episodes found")

    # send new episodes to qBittorrent
    for episode in episodes_to_download:
        try:
            resp = client.torrents_add(
                urls=episode.torrent.url,
                save_path=str(episode.save_path),
                is_paused=False,
                use_auto_torrent_management=False,
                content_layout="NoSubfolder",
                tags=[
                    f"FILTER:s=={episode.season}",
                    f"NAME:{episode.show_title}",
                    "DIRECT:true",
                ],  # tags for py-qbot extra arguments
                category=episode.category,
            )
            if resp != "Ok.":
                logger.error(f"Failed to add torrent for episode {episode.title}: {resp}")
                continue
            logger.info(f"Send torrent for episode: {episode.title}")
        except Exception as e:
            logger.error(f"Failed to add torrent for episode {episode.title}: {e}")
            return


def main():
    args = parse_args()
    configure_logging(Path("logs"), args.debug)

    logger.info(f"Starting Bangumi Tracker CLI version {__version__}")
    logger.debug(f"Using configuration file: {args.config}")
    try:
        with open(args.config, "rb") as f:
            config_raw = tomllib.load(f)
        logger.debug(f"Configuration loaded: {config_raw}")
    except Exception as e:
        logger.error(f"Failed to load configuration file: {e}")
        return
    config = load_config(config_raw)
    logger.info("Configuration loaded successfully")

    # Initialize qBittorrent client
    try:
        client = qbittorrentapi.Client(
            host=config.qbittorrent.host,
            port=config.qbittorrent.port,
            username=config.qbittorrent.username,
            password=config.qbittorrent.password,
        )
        client.auth_log_in()
        logger.info("Connected to qBittorrent successfully")
    except qbittorrentapi.LoginFailed as e:
        logger.error(f"Failed to connect to qBittorrent: {e}")
        return

    # initialize torrent fetcher session
    session = requests.Session()
    torrent_fetcher = TorrentFetcher(session=session)
    try:
        while True:
            try:
                operation(config, client, torrent_fetcher)
            except Exception as e:
                logger.error(f"Operation failed: {e}")
            logger.info(f"Sleeping {config.pull_interval_sec}s...")
            time.sleep(config.pull_interval_sec)
    except KeyboardInterrupt:
        logger.info("User cancelled, exiting...")
    finally:
        session.close()
        logger.info("HTTP session closed")


if __name__ == "__main__":
    main()
