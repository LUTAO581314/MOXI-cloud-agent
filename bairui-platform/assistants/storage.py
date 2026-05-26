import os
import re
import json
from pathlib import Path

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError


SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def ensure_storage_directories(storage):
    for path in [
        storage.root_path,
        storage.workspace_path,
        storage.files_path,
        storage.memory_path,
        storage.logs_path,
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)


def safe_filename(name):
    base = os.path.basename(name or "upload.bin")
    cleaned = SAFE_FILENAME_RE.sub("_", base).strip("._")
    return cleaned or "upload.bin"


def allocate_file(storage, uploaded_file):
    size_bytes = uploaded_file.size
    size_mb = bytes_to_quota_mb(size_bytes)
    with transaction.atomic():
        locked = type(storage).objects.select_for_update().get(pk=storage.pk)
        if locked.used_mb + size_mb > locked.quota_mb:
            raise ValidationError({"file": "存储空间不足，请删除文件或升级套餐。"})
        ensure_storage_directories(locked)
        filename = unique_file_path(locked.files_path, safe_filename(uploaded_file.name))
        with open(filename, "wb") as target:
            for chunk in uploaded_file.chunks():
                target.write(chunk)
        locked.used_mb += size_mb
        locked.save(update_fields=["used_mb", "updated_at"])
    return filename, size_bytes, size_mb


def append_memory_item(storage, memory_item):
    ensure_storage_directories(storage)
    memory_path = Path(storage.memory_path) / "memory_items.jsonl"
    payload = {
        "id": memory_item.id,
        "kind": memory_item.kind,
        "content": memory_item.content,
        "created_at": memory_item.created_at.isoformat() if memory_item.created_at else timezone.now().isoformat(),
    }
    with memory_path.open("a", encoding="utf-8") as target:
        target.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return str(memory_path)


def bytes_to_quota_mb(size_bytes):
    if size_bytes <= 0:
        return 0
    return max(1, (size_bytes + 1024 * 1024 - 1) // (1024 * 1024))


def unique_file_path(directory, filename):
    directory_path = Path(directory)
    candidate = directory_path / filename
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while candidate.exists():
        candidate = directory_path / f"{stem}_{counter}{suffix}"
        counter += 1
    return str(candidate)
