"""Downloadable resources, cached outside the repository.

* GloVe word vectors (glove-wiki-gigaword-100, Pennington et al. 2014, Public Domain Dedication
  and License v1.0), from the gensim-data release on GitHub.
* NVIDIA garak's prompt-injection probes (Apache-2.0), used as an external, held-out attack set.

Set ``MCC_CACHE`` to change the cache directory. Nothing here is committed to the repository.
"""

from __future__ import annotations

import gzip
import os
import urllib.request
from pathlib import Path

import numpy as np

CACHE = Path(os.environ.get("MCC_CACHE", Path.home() / ".cache" / "motor-claims-copilot"))
GLOVE_URL = ("https://github.com/RaRe-Technologies/gensim-data/releases/download/"
             "glove-wiki-gigaword-100/glove-wiki-gigaword-100.gz")
GARAK_BASE = "https://raw.githubusercontent.com/NVIDIA/garak/main/"
GARAK_FILES = ("garak/resources/promptinject/prompt_data.py", "garak/probes/latentinjection.py")
GLOVE_VOCAB = 200_000


def _download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        tmp = dest.with_suffix(dest.suffix + ".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.rename(dest)
    return dest


def glove(download: bool = True) -> tuple[dict[str, int], np.ndarray] | None:
    """Return (word -> row, vectors) for the 200k most frequent words, or None if unavailable."""
    npz = CACHE / "glove-100-200k.npz"
    if not npz.exists():
        gz = CACHE / "glove-wiki-gigaword-100.gz"
        try:
            if download:
                _download(GLOVE_URL, gz)
        except OSError:
            return None
        if not gz.exists():
            return None
        words, rows = [], []
        with gzip.open(gz, "rt", encoding="utf-8") as f:
            next(f)  # header: "<count> <dims>"
            for i, line in enumerate(f):
                if i >= GLOVE_VOCAB:
                    break
                parts = line.rstrip().split(" ")
                words.append(parts[0])
                rows.append(np.asarray(parts[1:], dtype=np.float32))
        np.savez_compressed(npz, words=np.array(words), vectors=np.vstack(rows))
    data = np.load(npz)
    return {w: i for i, w in enumerate(data["words"].tolist())}, data["vectors"]


def garak_sources(download: bool = True) -> dict[str, str] | None:
    out = {}
    for rel in GARAK_FILES:
        dest = CACHE / "garak" / Path(rel).name
        try:
            if download:
                _download(GARAK_BASE + rel, dest)
        except OSError:
            return None
        if not dest.exists():
            return None
        out[Path(rel).name] = dest.read_text(encoding="utf-8")
    return out
