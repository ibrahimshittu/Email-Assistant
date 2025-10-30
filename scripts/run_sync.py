from __future__ import annotations

import requests

from server.config import load_config


def main():
    cfg = load_config()
    url = f"{cfg.backend_base_url}/sync/latest"
    resp = requests.post(url, timeout=60)
    print(resp.status_code, resp.text)


if __name__ == "__main__":
    main()
