# -*- coding: utf-8 -*-
r"""
Prefetch OSM Mapnik tiles za celotno Slovenijo v lokalno mapo.

Po dokoncanem prefetch-u:
  - Tiles strukturirane kot D:\Atoll_projects_planer01\tiles_cache\{z}\{x}\{y}.png
  - narisi_pokrivanje.py jih uporabi preko lokalnega http.server-ja
    (glej narisi_pokrivanje_local.md ali komentar spodaj)

Uporaba:
  py -3.10 prefetch_osm_slovenia.py
  py -3.10 prefetch_osm_slovenia.py --zoom-max 13   # samo do zoom 13 (hitreje)

Slovenija bbox (WGS84, lon/lat):
  W=13.30, S=45.40, E=16.65, N=46.90

Tile count na zoom level (cca):
  zoom 9:   ~12 tiles    (groba pregledna)
  zoom 10:  ~42 tiles
  zoom 11:  ~168 tiles
  zoom 12:  ~672 tiles
  zoom 13:  ~2,688 tiles  (typical detail za slika v emailu)
  zoom 14:  ~10,750 tiles (detajlnejsa - ulice, stevilke hisnih stevilk)
  zoom 15:  ~43,000 tiles (BIG - ce ti res rabi ulicne razdalje)

Skupaj zoom 9-14: ~14,300 tiles, ~140 MB cca disk space.
S 0.5s delay med fetchi: ~2h za zoom 9-14 polni run.

OSM ToS opomba: bulk download dovoljen z rate limit + pravi User-Agent.
Za boljso uporabnost ALTERNATIVA: download mbtiles pack iz openmaptiles.org
(brezplacno za nekomerciale, vse Slovenije ~100MB).
"""

import argparse
import time
import sys
from pathlib import Path

import mercantile     # contextily depends on this - ze imas
import requests

# ============= Nastavitve =============
SLOVENIA_BBOX = (13.30, 45.40, 16.65, 46.90)  # W, S, E, N v WGS84

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = "Atoll-Planer-Tile-Prefetch/1.0 (planiranje@telekom.si)"

CACHE_DIR = Path(r"D:\Atoll_projects_planer01\tiles_cache")

ZOOM_DEFAULT = list(range(9, 14))   # zoom 9 do 13 (vkljucno) - polna pokritost za vse slika varianti
DELAY_S = 0.5                       # delay med tile fetchi - polite to OSM
TIMEOUT_S = 15
RETRY_ON_FAIL = 2


def fetch_tile(z, x, y, session):
    """Fetch single tile and save to local cache.
    Vrne: 'downloaded', 'cached', ali raise exception."""
    cache_file = CACHE_DIR / str(z) / str(x) / f"{y}.png"
    if cache_file.exists() and cache_file.stat().st_size > 0:
        return "cached"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    url = TILE_URL.format(z=z, x=x, y=y)
    for attempt in range(RETRY_ON_FAIL + 1):
        try:
            r = session.get(url, timeout=TIMEOUT_S)
            r.raise_for_status()
            cache_file.write_bytes(r.content)
            return "downloaded"
        except Exception as e:
            if attempt < RETRY_ON_FAIL:
                time.sleep(2 * (attempt + 1))
                continue
            raise


def main():
    parser = argparse.ArgumentParser(description="Prefetch OSM tiles za Slovenijo")
    parser.add_argument("--zoom-min", type=int, default=ZOOM_DEFAULT[0])
    parser.add_argument("--zoom-max", type=int, default=ZOOM_DEFAULT[-1])
    parser.add_argument("--delay", type=float, default=DELAY_S, help="sekund med fetchi")
    parser.add_argument("--cache-dir", type=str, default=str(CACHE_DIR))
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    global CACHE_DIR
    CACHE_DIR = cache_dir

    zoom_levels = list(range(args.zoom_min, args.zoom_max + 1))
    print(f"Slovenija bbox: {SLOVENIA_BBOX}")
    print(f"Cache dir:      {CACHE_DIR}")
    print(f"Zoom levels:    {zoom_levels}")
    print(f"Delay:          {args.delay}s")
    print()

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    total_downloaded = 0
    total_cached = 0
    total_failed = 0
    t_start = time.time()

    for zoom in zoom_levels:
        tiles = list(mercantile.tiles(*SLOVENIA_BBOX, zoom))
        print(f"--- Zoom {zoom}: {len(tiles)} tiles ---")
        z_downloaded = z_cached = z_failed = 0
        for i, tile in enumerate(tiles, 1):
            try:
                result = fetch_tile(tile.z, tile.x, tile.y, session)
                if result == "downloaded":
                    z_downloaded += 1
                    time.sleep(args.delay)
                else:
                    z_cached += 1
            except Exception as e:
                z_failed += 1
                if z_failed <= 3:
                    print(f"  FAIL {tile}: {type(e).__name__}: {e}")
                elif z_failed == 4:
                    print(f"  (additional failures suppressed)")
            if i % 200 == 0 or i == len(tiles):
                print(f"  {i}/{len(tiles)}  ({z_downloaded} new, {z_cached} cached, {z_failed} failed)")
        total_downloaded += z_downloaded
        total_cached += z_cached
        total_failed += z_failed
        print(f"Zoom {zoom} koncan: {z_downloaded} downloaded, {z_cached} cached, {z_failed} failed")
        print()

    elapsed = time.time() - t_start
    print("=" * 50)
    print(f"KONEC v {elapsed/60:.1f} min")
    print(f"  Downloaded: {total_downloaded}")
    print(f"  Cached:     {total_cached}")
    print(f"  Failed:     {total_failed}")
    print(f"  Disk:       {sum(f.stat().st_size for f in CACHE_DIR.rglob('*.png'))/1e6:.1f} MB")
    print("=" * 50)
    print()
    print("NASLEDNJI KORAK - http.server za narisi_pokrivanje:")
    print(r"  cd D:\Atoll_projects_planer01\tiles_cache")
    print(f"  py -3.10 -m http.server 8080")
    print()
    print("Nato v narisi_pokrivanje.py spremeni BASEMAP_PROVIDER na:")
    print('  BASEMAP_PROVIDER = "http://localhost:8080/{z}/{x}/{y}.png"')
    print("contextily.add_basemap sprejme tudi navaden URL string kot source.")


if __name__ == "__main__":
    main()
