#!/usr/bin/env python3
"""
Fetch GitHub language stats and generate terminal-style bars for README.
Usage: python gen_lang_bars.py <username>
"""

import os
import re
import sys
import json
import urllib.request
import urllib.error

GITHUB_USER = os.environ.get("GITHUB_USER", "Mangalasridharan")
README_PATH = os.environ.get("README_PATH", "README.md")
BAR_WIDTH = 25
MIN_LANGS = 5

def github_api(url, token=None):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    if token:
        req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"Rate limited. Using GITHUB_TOKEN env var for higher limits.", file=sys.stderr)
        raise
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}")

def fetch_repos(username, token=None):
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}&type=owner"
        data = github_api(url, token)
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos

def compute_lang_stats(repos):
    lang_repos = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            lang_repos.setdefault(lang, 0)
            lang_repos[lang] += 1
    total = sum(lang_repos.values())
    if total == 0:
        return []
    stats = []
    for lang, count in lang_repos.items():
        pct = (count / total) * 100
        stats.append((lang, count, pct))
    stats.sort(key=lambda x: x[2], reverse=True)
    return stats

def build_bar(pct):
    filled = round((pct / 100) * BAR_WIDTH)
    return "█" * filled + "░" * (BAR_WIDTH - filled)

def generate_terminal_block(stats):
    lines = []
    for lang, count, pct in stats:
        bar = build_bar(pct)
        repo_word = "repo" if count == 1 else "repos"
        line = f"{lang:<13} {count:>3} {repo_word:<5} {bar} {pct:>6.2f} %"
        lines.append(line)
    return "\n".join(lines)

def update_readme(block):
    start = "<!-- LANG_BARS_START -->"
    end = "<!-- LANG_BARS_END -->"
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(f"{re.escape(start)}.*?{re.escape(end)}", re.DOTALL)
    if not pattern.search(content):
        print(f"ERROR: Could not find {start} ... {end} markers in {README_PATH}", file=sys.stderr)
        sys.exit(1)
    new_block = f"{start}\n{block}\n{end}"
    updated = pattern.sub(new_block, content)
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"Updated {README_PATH} with language bars")

def main():
    token = os.environ.get("GITHUB_TOKEN")
    username = sys.argv[1] if len(sys.argv) > 1 else GITHUB_USER
    repos = fetch_repos(username, token)
    repos = [r for r in repos if not r.get("fork")]
    stats = compute_lang_stats(repos)
    stats = stats[:MIN_LANGS]
    block = generate_terminal_block(stats)
    update_readme(block)
    print(block)

if __name__ == "__main__":
    main()
