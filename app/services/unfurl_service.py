
import httpx
from typing import Optional, Tuple

import unfurl

def unfurl_preview(url: str, timeout: int = 5) -> Tuple[Optional[str], Optional[str]]:
    """
    Extrae (title, description) o (None, None) si falla.
    """

    try:
        # primero traemos HTML
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            html = resp.text

        # luego parseamos
        u = unfurl()
        meta = u.parse(html)

        # Prioridad: OG > Twitter > <title> > meta[name=description]
        title = (
            meta.get("og:title")
            or meta.get("twitter:title")
            or meta.get("title")
        )

        description = (
            meta.get("og:description")
            or meta.get("twitter:description")
            or meta.get("description")
        )

        # Limpieza
        if title:
            title = title.strip()
        if description:
            description = description.strip()

        return title, description

    except Exception:
        return None, None