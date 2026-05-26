from fnmatch import fnmatch
import os
from pathlib import Path


DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".cache",
}

DEFAULT_SENSITIVE_PATTERNS = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_ed25519",
    "*secret*",
    "*credential*",
    "*token*",
]


def default_workspace_policy():
    return {
        "mode": "read_only",
        "max_file_size_bytes": 1_000_000,
        "max_entries": 500,
        "exclude_dirs": sorted(DEFAULT_EXCLUDE_DIRS),
        "sensitive_patterns": DEFAULT_SENSITIVE_PATTERNS,
    }


def authorize_workspace(config, workspace_path, policy=None):
    root = Path(workspace_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Workspace path is not a directory: {root}")
    merged_policy = default_workspace_policy()
    if policy:
        merged_policy.update(policy)
    config.workspace_path = str(root)
    config.workspace_policy = merged_policy
    return config


def index_workspace(config):
    if not config.workspace_path:
        raise ValueError("No workspace is authorized. Run `bairui-agent authorize` first.")
    root = Path(config.workspace_path).resolve()
    policy = {**default_workspace_policy(), **(config.workspace_policy or {})}
    max_entries = int(policy.get("max_entries", 500))
    entries = []
    skipped = []

    exclude_dirs = set(policy.get("exclude_dirs") or [])
    for current_root, dirs, files in os.walk(root):
        current = Path(current_root)
        dirs.sort()
        files.sort()
        for dirname in list(dirs):
            path = current / dirname
            rel = path.relative_to(root).as_posix()
            reason = skip_reason(path, root, policy)
            if reason:
                skipped.append({"path": rel, "reason": reason})
                dirs.remove(dirname)
                continue
            if len(entries) >= max_entries:
                skipped.append({"path": rel, "reason": "max_entries_reached"})
                return _index_result(root, policy, entries, skipped)
            entries.append({"path": rel, "type": "dir"})

        dirs[:] = [dirname for dirname in dirs if dirname not in exclude_dirs]

        for filename in files:
            path = current / filename
            rel = path.relative_to(root).as_posix()
            if len(entries) >= max_entries:
                skipped.append({"path": rel, "reason": "max_entries_reached"})
                return _index_result(root, policy, entries, skipped)
            reason = skip_reason(path, root, policy)
            if reason:
                skipped.append({"path": rel, "reason": reason})
                continue
            entries.append({"path": rel, "type": "file", "size_bytes": path.stat().st_size})

    return _index_result(root, policy, entries, skipped)


def _index_result(root, policy, entries, skipped):
    return {
        "root": str(root),
        "policy": policy,
        "entries": entries,
        "skipped": skipped,
        "counts": {
            "entries": len(entries),
            "skipped": len(skipped),
        },
    }


def skip_reason(path, root, policy):
    rel_parts = path.relative_to(root).parts
    exclude_dirs = set(policy.get("exclude_dirs") or [])
    if any(part in exclude_dirs for part in rel_parts[:-1] if part):
        return "excluded_parent_dir"
    if path.is_dir() and path.name in exclude_dirs:
        return "excluded_dir"
    rel = path.relative_to(root).as_posix()
    name = path.name
    for pattern in policy.get("sensitive_patterns") or []:
        if fnmatch(name.lower(), pattern.lower()) or fnmatch(rel.lower(), pattern.lower()):
            return "sensitive_pattern"
    if path.is_file() and path.stat().st_size > int(policy.get("max_file_size_bytes", 1_000_000)):
        return "file_too_large"
    return ""
