from typing import Any

import feedparser
from feedparser import FeedParserDict

from bangumi_tracker import logger
from bangumi_tracker.episode import Episode, Torrent


class RssFeed:
    @staticmethod
    def fetch_raw(url: str) -> Any | list[FeedParserDict]:
        feed = feedparser.parse(url)
        return feed.entries

    @staticmethod
    def fetch_episodes(url: str, reverse: bool = False) -> list[Episode]:
        entries = RssFeed.fetch_raw(url)
        logger.info(f"Fetched {len(entries)} entries from {url}")

        episodes = []
        for entry in entries:
            logger.debug(f"Processing entry: {entry.title}")
            torrent = None
            # search torrent link in entry.
            for link in entry.links:
                if link.type == "application/x-bittorrent":
                    torrent = Torrent(url=str(link.href), size=int(str(link.length)))
                    break
            if not torrent:
                logger.warning(f"No torrent found in entry: {entry.title}")
                continue

            episode = Episode(
                id=str(entry.id), title=str(entry.title), link=str(entry.link), torrent=torrent
            )
            episodes.append(episode)
        if reverse:
            episodes.reverse()
        return episodes
