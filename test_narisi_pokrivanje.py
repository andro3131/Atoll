# -*- coding: utf-8 -*-
r"""
Test skripta za generiranje PNG slike pokrivanja iz obstojecih PANKAC TIF + SHP.
Output: <SLIKE_DIR>\PANKAC_<TEH>_pokrivanje.png za vsako tehnologijo (LTE, NR).

Po validaciji se ta logika preseli v preverba_upravicenost_bazne_postaje.py.

Run: py -3.10 test_narisi_pokrivanje.py

Predpogoji:
  py -3.10 -m pip install contextily
  (rasterio, geopandas, matplotlib, pyodbc - ze namesceni)
"""

import os
import numpy as np
import pandas as pd
import pyodbc
import rasterio
import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt

# ============= Nastavitve =============
LOKACIJA = "PANKAC"
SLIKE_DIR = r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\PANKAC\Slike"
TEHNOLOGIJE = ["LTE", "NR"]

BUFFER_M = 500            # dodaten pas okrog autocrop bounding box
MIN_RADIUS_M = 1000       # fallback radius okrog BP, ce TIF nima uporabnih bounds
SQUARE_CROP = True        # True = kvadratni izrez (boljse za slide); False = naravni AR

DPI = 200
FIGSIZE = (10, 10)

OVERLAY_ALPHA = 0.6       # transparenca raster overlay-a (0=nevidno, 1=neprozorno)
POINTS_ALPHA = 1.0        # transparenca rdecih pik naslovov
PERCENTILE_ZOOM = 95      # za zoom slike zanemarimo (100 - PERCENTILE_ZOOM)% najbolj oddaljenih naslovov od BP

# Izbira podlage. Lahko probamo razne, da vidimo kateri stil ustreza:
BASEMAP_PROVIDER = ctx.providers.OpenTopoMap
# Alternative:
#   ctx.providers.OpenStreetMap.Mapnik       # cestna karta (klasicni OSM)
#   ctx.providers.CartoDB.Positron           # svetla, minimalisticna
#   ctx.providers.Esri.WorldTopoMap          # Esri topo
#   ctx.providers.Esri.WorldImagery          # satelitska
#   ctx.providers.CartoDB.Voyager            # uravnotezena

# ============= SQL za fallback BP koord =============
conn_atoll = pyodbc.connect(
    'Driver={SQL Server};'
    'Server=BPW-DENALI;'
    'Database=atoll_d96;'
    'UID=beribaze;'
    'PWD=beribaze'
)


def bp_koord(lokacija):
    """Vrne (X, Y) v EPSG:3794, ali None ce ne najde."""
    sites = pd.read_sql(
        f"SELECT NAME, LONGITUDE, LATITUDE FROM atoll_d96.dbo.sites WHERE NAME='{lokacija}'",
        conn_atoll
    )
    if sites.shape[0] == 0:
        return None
    return float(sites.iloc[0]['LONGITUDE']), float(sites.iloc[0]['LATITUDE'])


def izracunaj_crop(tif_path, fallback_bp_coords):
    """
    Vrne (xmin, ymin, xmax, ymax) v EPSG:3794 za izrez.
    Logika:
      1. TIF cesto pokriva celoten computation zone (25km) s prozornimi pikami zunaj izboljsave.
         Zato iscemo bounding box VIDNIH pikslov (alpha > 0), ne src.bounds.
      2. Iz pixel coords izracunamo world coords preko transform-a.
      3. Ce TIF nima vidnih pikslov, fallback na BP center +/- MIN_RADIUS_M.
      4. Po izbiri kvadratiziramo (SQUARE_CROP).
      5. Dodamo BUFFER_M na vse strani.
    """
    with rasterio.open(tif_path) as src:
        img = src.read()        # (bands, h, w)
        transform = src.transform
        full_bounds = src.bounds

    # Najdi vidne piksle
    if img.shape[0] == 4:       # RGBA - vidno = alpha > 0
        visible_mask = img[3] > 0
    elif img.shape[0] == 3:     # RGB brez alpha - predpostavimo, da je belo (255,255,255) ozadje
        visible_mask = ~((img[0] == 255) & (img[1] == 255) & (img[2] == 255))
    else:                       # 1 band - vidno = ni 0/255
        visible_mask = (img[0] > 0) & (img[0] < 255)

    if not visible_mask.any():
        # prazen TIF
        empty = True
        xmin = ymin = xmax = ymax = 0
    else:
        rows, cols = np.where(visible_mask)
        min_col, max_col = int(cols.min()), int(cols.max())
        min_row, max_row = int(rows.min()), int(rows.max())
        # transform * (col, row) -> (x, y) v world coords (zg. levi vogal pixla)
        x_tl, y_tl = transform * (min_col, min_row)
        x_br, y_br = transform * (max_col + 1, max_row + 1)
        xmin, xmax = min(x_tl, x_br), max(x_tl, x_br)
        ymin, ymax = min(y_tl, y_br), max(y_tl, y_br)
        empty = False

    print(f"  TIF full bounds:    x=[{full_bounds.left:.0f}, {full_bounds.right:.0f}], y=[{full_bounds.bottom:.0f}, {full_bounds.top:.0f}]")
    if not empty:
        print(f"  TIF visible bounds: x=[{xmin:.0f}, {xmax:.0f}], y=[{ymin:.0f}, {ymax:.0f}]")
    else:
        print(f"  TIF nima vidnih pikslov - fallback na BP center")

    if empty or (xmax - xmin) < 100 or (ymax - ymin) < 100:
        if fallback_bp_coords:
            cx, cy = fallback_bp_coords
        else:
            cx = (full_bounds.left + full_bounds.right) / 2
            cy = (full_bounds.bottom + full_bounds.top) / 2
        xmin = cx - MIN_RADIUS_M
        xmax = cx + MIN_RADIUS_M
        ymin = cy - MIN_RADIUS_M
        ymax = cy + MIN_RADIUS_M

    if SQUARE_CROP:
        dx = xmax - xmin
        dy = ymax - ymin
        d = max(dx, dy) / 2
        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2
        xmin, xmax = cx - d, cx + d
        ymin, ymax = cy - d, cy + d

    return xmin - BUFFER_M, ymin - BUFFER_M, xmax + BUFFER_M, ymax + BUFFER_M


def izracunaj_crop_zoom(shp_path, fallback_bp_coords, percentile=PERCENTILE_ZOOM):
    """
    Vrne (xmin, ymin, xmax, ymax) za zoom slik. Bazirano na naslovih iz SHP.
      1. Bere SHP, racuna razdalje od BP centra (ali centroida ce BP koord ni).
      2. Odvrze (100-percentile)% najbolj oddaljenih.
      3. Bounding box preostalih + kvadrat + buffer.
    Vrne None ce SHP nima dovolj podatkov za smiseln zoom.
    """
    if not os.path.exists(shp_path):
        return None
    points = gpd.read_file(shp_path)
    if points.empty or len(points) < 5:
        return None
    if points.crs is None:
        points = points.set_crs("EPSG:3794")
    elif points.crs.to_string() != "EPSG:3794":
        points = points.to_crs("EPSG:3794")

    if fallback_bp_coords:
        cx, cy = fallback_bp_coords
    else:
        cx = points.geometry.x.mean()
        cy = points.geometry.y.mean()

    dist = np.sqrt((points.geometry.x.values - cx) ** 2 + (points.geometry.y.values - cy) ** 2)
    threshold = np.percentile(dist, percentile)
    kept = points[dist <= threshold]
    if kept.empty:
        return None

    xmin = float(kept.geometry.x.min())
    xmax = float(kept.geometry.x.max())
    ymin = float(kept.geometry.y.min())
    ymax = float(kept.geometry.y.max())

    print(f"  ZOOM ({percentile}% najblizjih): odvrzemo {len(points) - len(kept)} od {len(points)} pik, max razdalja od BP: {threshold:.0f}m")

    if SQUARE_CROP:
        dx = xmax - xmin
        dy = ymax - ymin
        d = max(dx, dy) / 2
        cx_box = (xmin + xmax) / 2
        cy_box = (ymin + ymax) / 2
        xmin, xmax = cx_box - d, cx_box + d
        ymin, ymax = cy_box - d, cy_box + d

    return xmin - BUFFER_M, ymin - BUFFER_M, xmax + BUFFER_M, ymax + BUFFER_M


def narisi_eno(tif_path, shp_path, output_path, bounds):
    xmin, ymin, xmax, ymax = bounds
    print(f"  KONCNI izrez (z bufferjem {BUFFER_M}m): x=[{xmin:.0f}, {xmax:.0f}], y=[{ymin:.0f}, {ymax:.0f}]  ({(xmax-xmin)/1000:.1f}km x {(ymax-ymin)/1000:.1f}km)")

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect('equal')

    # 1. Basemap - contextily prenese OSM/OpenTopo tile-e in jih reprojicira v nas CRS
    ctx.add_basemap(ax, crs="EPSG:3794", source=BASEMAP_PROVIDER)

    # 2. Naslovi (SHP) - rdece pike POD raster overlay (da niso v ospredju)
    if os.path.exists(shp_path):
        points = gpd.read_file(shp_path)
        if points.crs is None:
            points = points.set_crs("EPSG:3794")
        elif points.crs.to_string() != "EPSG:3794":
            points = points.to_crs("EPSG:3794")
        points.plot(ax=ax, color='red', markersize=15, edgecolor='black', linewidth=0.5, zorder=2, alpha=POINTS_ALPHA)

    # 3. Raster overlay (TIF z alpha kanalom iz transparent2) - VRH, polprozoren
    with rasterio.open(tif_path) as src:
        img = src.read()
        b = src.bounds
        ext = [b.left, b.right, b.bottom, b.top]
    if img.shape[0] >= 3:
        img = img.transpose(1, 2, 0)   # (bands, h, w) -> (h, w, bands)
    else:
        img = img[0]
    ax.imshow(img, extent=ext, origin='upper', interpolation='nearest', zorder=3, alpha=OVERLAY_ALPHA)

    # Cista slika, brez osi, brez naslova, brez legende
    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', pad_inches=0)
    plt.close(fig)


def main():
    bp_coords = bp_koord(LOKACIJA)
    if bp_coords:
        print(f"BP {LOKACIJA} koord (EPSG:3794): {bp_coords}")
    else:
        print(f"OPOZORILO: BP {LOKACIJA} ni v atoll_d96.sites - fallback brez centra")

    for teh in TEHNOLOGIJE:
        tif_path = os.path.join(
            SLIKE_DIR,
            f"{LOKACIJA}_Izboljsava_Naslovi_best_outdoor_{teh}.tif"
        )
        shp_path = os.path.join(
            SLIKE_DIR,
            f"{LOKACIJA}_Izboljsava_Naslovi_best_outdoor_{teh}_naslovi.shp"
        )
        output_path_vse = os.path.join(SLIKE_DIR, f"{LOKACIJA}_{teh}_pokrivanje.png")
        output_path_zoom = os.path.join(SLIKE_DIR, f"{LOKACIJA}_{teh}_pokrivanje_zoom.png")

        if not os.path.exists(tif_path):
            print(f"PRESKOK: ne najdem {tif_path}")
            continue

        # 1) Slika z vsemi tockami (loose, na TIF visible pixlih)
        print(f"\n[{teh}] Generiram VSE: {output_path_vse}")
        vse_bounds = izracunaj_crop(tif_path, bp_coords)
        narisi_eno(tif_path, shp_path, output_path_vse, vse_bounds)

        # 2) Zoom slika (drop 5% najbolj oddaljenih naslovov)
        zoom_bounds = izracunaj_crop_zoom(shp_path, bp_coords)
        if zoom_bounds:
            print(f"\n[{teh}] Generiram ZOOM: {output_path_zoom}")
            narisi_eno(tif_path, shp_path, output_path_zoom, zoom_bounds)
        else:
            print(f"[{teh}] SHP nima dovolj podatkov za zoom variant, preskocim")

    print("Konec.")


if __name__ == "__main__":
    main()
