from __future__ import annotations

from pathlib import Path

from server.config import load_config
from server.db import Base, engine


def main():
    config = load_config()
    Path(config.chroma_dir).mkdir(parents=True, exist_ok=True)
    Path(config.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("Storage and database initialized.")


if __name__ == "__main__":
    main()
