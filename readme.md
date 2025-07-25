# Bangumi Tracker
A CLI tool to track anime RSS feeds and download episodes via qBittorrent.

## Installation

```bash
git clone https://github.com/sean1832/bangumi-tracker.git
cd bangumi-tracker
pip install -e .

# Configuration
cp config.toml.example config.toml
# Edit config.toml to add your RSS feeds and qBittorrent settings
```

## Usage

```bash
bangumi-tracker [config.toml] [Args]
```
- `-h`, `--help`: Show help message and exit.
- `-v`, `--version`: Show version information and exit.

### Usage with `tmux`
You can run the tracker in a `tmux` session to keep it running in the background:

```bash
tmux new -s bangumi-tracker
bangumi-tracker config.toml
```
> To detach from the session, press `Ctrl+b`, then `d`. To reattach, use `tmux attach -t bangumi-tracker`.
>
> To kill the session, use `tmux kill-session -t bangumi-tracker`.

### Usage with `cron`
You can set up a cron job to run the tracker periodically. For example, to run it every hour:

```bash
0 * * * * /path/to/bangumi-tracker /path/to/config.toml
```
## Configuration
Edit `config.toml` to add your RSS feeds and qBittorrent settings. The configuration file should look like this:

```toml
[settings]
pull_interval_sec = 300 # how often to check for new episodes in seconds
log_dir = "~/logs" # log directory. It will save as log/yyyy-mm-dd.log
log_level = "INFO" # log level, can be DEBUG, INFO, WARNING, ERROR, CRITICAL

[qbittorrent]
host = "localhost"
port = 8080
username = "admin"
password = "password"
save_path_root = "/mnt/nas/Media/animes" # where your plex server is looking for files
category = "anime"


[[shows]]
title = "your title"
url = "https://xxx"
season = 1
exclude_patterns = ["720"]  # regex patterns to exclude

# (optional) defaults "anime"
#category = "anime" 


# [[shows]]
# more...
```