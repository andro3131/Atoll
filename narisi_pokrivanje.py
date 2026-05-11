# -*- coding: utf-8 -*-
r"""
Splosna skripta za risanje PNG slik pokrivanja za poljubno BP.
Predpostavlja, da je upravicenost analiza ze tekla in so v Slike\ mapi
generirani TIF + SHP fajli (...Izboljsava_Naslovi_best_outdoor_<TEH>...).

Uporaba:
  py -3.10 narisi_pokrivanje.py <LOKACIJA>
  py -3.10 narisi_pokrivanje.py <LOK1> <LOK2> <LOK3> ...

Primeri:
  py -3.10 narisi_pokrivanje.py PANKAC
  py -3.10 narisi_pokrivanje.py KJROVT MCERSA SCVEN

Za vsako lokacijo generira (ce so dostopni TIF+SHP):
  <LOKACIJA>_<TEH>_pokrivanje.png         (vsi naslovi)
  <LOKACIJA>_<TEH>_pokrivanje_zoom.png    (PERCENTILE_ZOOM% najblizjih)

Predpogoji:
  py -3.10 -m pip install contextily geopandas rasterio matplotlib pip-system-certs
"""

import os
import sys
import numpy as np
import pandas as pd
import pyodbc
import rasterio
import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt

# ============= Nastavitve =============
POKRIVANJA_BASE_DIR = r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje"
TEHNOLOGIJE = ["LTE", "NR"]   # GSM nima slike (kolegov design)

BUFFER_M = 500            # dodaten pas okrog autocrop bounding box
MIN_RADIUS_M = 1000       # fallback radius okrog BP, ce SHP/TIF nepouporabna
SQUARE_CROP = True        # True = kvadratni izrez (boljse za slide); False = naravni AR

DPI = 200
FIGSIZE = (10, 10)

OVERLAY_ALPHA = 0.6       # transparenca raster overlay-a (0=nevidno, 1=neprozorno)
POINTS_ALPHA = 0.8        # transparenca rdecih pik naslovov

# Zoom slika: koliko % najblizjih naslovov ohranimo. Per-tech.
# LTE in NR imata pogosto zelo razlicno razprseno pokrivanje, zato locena nastavitev.
PERCENTILE_ZOOM = {
    "LTE": 90,
    "NR": 97,
    # nizja stevilka = bolj agresivni crop (npr. 80 ali 85 za zelo razprsene primere)
}
PERCENTILE_ZOOM_DEFAULT = 95   # ce technologija ni v slovarju zgoraj

BASEMAP_PROVIDER = ctx.providers.OpenStreetMap.Mapnik
# Alternative iz OSM/topo druzine (vse brezplacne, brez API kljuca):
#   ctx.providers.OpenStreetMap.Mapnik       # klasicna OSM cestna karta (trenutna)
#   ctx.providers.OpenStreetMap.HOT          # OSM Humanitarian
#   ctx.providers.OpenStreetMap.DE           # OSM nemski stil
#   ctx.providers.CyclOSM                    # kolesarska OSM razlicica
#   ctx.providers.OpenTopoMap                # topografska s hill-shading
#   ctx.providers.Esri.WorldTopoMap          # Esri topo
#   ctx.providers.CartoDB.Voyager            # bolj moderna
#   ctx.providers.CartoDB.Positron           # zelo svetla, minimalisticna
#   ctx.providers.Esri.WorldImagery          # satelitska


# ============= SQL za BP koord =============
conn_atoll = pyodbc.connect(
    'Driver={SQL Server};'
    'Server=BPW-DENALI;'
    'Database=atoll_d96;'
    'UID=beribaze;'
    'PWD=beribaze'
)


def bp_koord(lokacija):
    """Vrne (X, Y) v EPSG:3794, ali None ce BP ni v atoll_d96.sites."""
    sites = pd.read_sql(
        f"SELECT NAME, LONGITUDE, LATITUDE FROM atoll_d96.dbo.sites WHERE NAME='{lokacija}'",
        conn_atoll
    )
    if sites.shape[0] == 0:
        return None
    return float(sites.iloc[0]['LONGITUDE']), float(sites.iloc[0]['LATITUDE'])


def izracunaj_crop_tif(tif_path, fallback_bp_coords):
    """FALLBACK: bounds iz TIF kadar SHP ni uporaben (visible alpha pixels)."""
    with rasterio.open(tif_path) as src:
        img = src.read()
        transform = src.transform
        full_bounds = src.bounds

    if img.shape[0] == 4:
        visible_mask = img[3] > 0
    elif img.shape[0] == 3:
        visible_mask = ~((img[0] == 255) & (img[1] == 255) & (img[2] == 255))
    else:
        visible_mask = (img[0] > 0) & (img[0] < 255)

    if not visible_mask.any():
        empty = True
        xmin = ymin = xmax = ymax = 0
    else:
        rows, cols = np.where(visible_mask)
        min_col, max_col = int(cols.min()), int(cols.max())
        min_row, max_row = int(rows.min()), int(rows.max())
        x_tl, y_tl = transform * (min_col, min_row)
        x_br, y_br = transform * (max_col + 1, max_row + 1)
        xmin, xmax = min(x_tl, x_br), max(x_tl, x_br)
        ymin, ymax = min(y_tl, y_br), max(y_tl, y_br)
        empty = False

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


def izracunaj_crop_naslovi(shp_path, fallback_bp_coords, percentile=100):
    """
    PRIMARNI crop: bounds iz SHP naslovov.
      percentile=100  -> vsi naslovi
      percentile<100  -> odvrze (100-percentile)% najbolj oddaljenih
    Vrne None, ce SHP ni uporaben (klicec naj pade na izracunaj_crop_tif).
    """
    if not os.path.exists(shp_path):
        return None
    points = gpd.read_file(shp_path)
    if points.empty:
        return None
    if points.crs is None:
        points = points.set_crs("EPSG:3794")
    elif points.crs.to_string() != "EPSG:3794":
        points = points.to_crs("EPSG:3794")

    if percentile < 100 and len(points) >= 2:
        if fallback_bp_coords:
            cx, cy = fallback_bp_coords
        else:
            cx = points.geometry.x.mean()
            cy = points.geometry.y.mean()
        dist = np.sqrt((points.geometry.x.values - cx) ** 2 + (points.geometry.y.values - cy) ** 2)
        threshold = np.percentile(dist, percentile)
        kept = points[dist <= threshold]
        print(f"  CROP {percentile}%: odvrzemo {len(points) - len(kept)} od {len(points)} pik (max razdalja od BP: {threshold:.0f}m)")
    else:
        kept = points
        print(f"  CROP 100%: vseh {len(points)} pik")

    if kept.empty:
        return None

    xmin = float(kept.geometry.x.min())
    xmax = float(kept.geometry.x.max())
    ymin = float(kept.geometry.y.min())
    ymax = float(kept.geometry.y.max())

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

    # 1. Basemap
    ctx.add_basemap(ax, crs="EPSG:3794", source=BASEMAP_PROVIDER)

    # 2. Naslovi (SHP) POD raster overlay
    if os.path.exists(shp_path):
        points = gpd.read_file(shp_path)
        if points.crs is None:
            points = points.set_crs("EPSG:3794")
        elif points.crs.to_string() != "EPSG:3794":
            points = points.to_crs("EPSG:3794")
        points.plot(ax=ax, color='red', markersize=15, edgecolor='black', linewidth=0.5, zorder=2, alpha=POINTS_ALPHA)

    # 3. Raster overlay (TIF z alpha kanalom)
    with rasterio.open(tif_path) as src:
        img = src.read()
        b = src.bounds
        ext = [b.left, b.right, b.bottom, b.top]
    if img.shape[0] >= 3:
        img = img.transpose(1, 2, 0)
    else:
        img = img[0]
    ax.imshow(img, extent=ext, origin='upper', interpolation='nearest', zorder=3, alpha=OVERLAY_ALPHA)

    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', pad_inches=0)
    plt.close(fig)


def preveri_lokacijo(lokacija):
    """
    Preveri, ce je za lokacijo na voljo izracun (Slike mapa + TIF/SHP fajli).
    Vrne tuple (status, dict_pari) kjer:
      status = 'ok' / 'manjka_mapa' / 'manjka_vse'
      dict_pari = {teh: (tif_path, shp_path)} za tehnologije, kjer obstaja TIF
    """
    slike_dir = os.path.join(POKRIVANJA_BASE_DIR, lokacija, "Slike")
    if not os.path.isdir(slike_dir):
        return 'manjka_mapa', {}

    pari = {}
    for teh in TEHNOLOGIJE:
        tif_path = os.path.join(slike_dir, f"{lokacija}_Izboljsava_Naslovi_best_outdoor_{teh}.tif")
        shp_path = os.path.join(slike_dir, f"{lokacija}_Izboljsava_Naslovi_best_outdoor_{teh}_naslovi.shp")
        if os.path.exists(tif_path):
            pari[teh] = (tif_path, shp_path)

    if not pari:
        return 'manjka_vse', {}
    return 'ok', pari


def obdelaj_lokacijo(lokacija):
    print(f"\n========== {lokacija} ==========")

    status, pari = preveri_lokacijo(lokacija)
    slike_dir = os.path.join(POKRIVANJA_BASE_DIR, lokacija, "Slike")

    if status == 'manjka_mapa':
        print(f"  NAPAKA: ne najdem mape {slike_dir}")
        print(f"  Verjetno upravicenost analiza za {lokacija} se ni bila pognana.")
        return False
    if status == 'manjka_vse':
        print(f"  NAPAKA: v {slike_dir} ne najdem nobenega TIF-a za {lokacija}")
        print(f"  Upravicenost analiza je morda padla pri risanju slik.")
        return False

    bp_coords = bp_koord(lokacija)
    if bp_coords:
        print(f"  BP koord (EPSG:3794): {bp_coords}")
    else:
        print(f"  OPOZORILO: BP {lokacija} ni v atoll_d96.sites - uporabim centroid naslovov")

    for teh, (tif_path, shp_path) in pari.items():
        output_path_vse = os.path.join(slike_dir, f"{lokacija}_{teh}_pokrivanje.png")
        output_path_zoom = os.path.join(slike_dir, f"{lokacija}_{teh}_pokrivanje_zoom.png")

        # 1) Slika z vsemi naslovi (100%)
        print(f"\n  [{teh}] Generiram VSE: {os.path.basename(output_path_vse)}")
        vse_bounds = izracunaj_crop_naslovi(shp_path, bp_coords, percentile=100)
        if not vse_bounds:
            print(f"    SHP ni uporaben, fallback na TIF visible pixle")
            vse_bounds = izracunaj_crop_tif(tif_path, bp_coords)
        narisi_eno(tif_path, shp_path, output_path_vse, vse_bounds)

        # 2) Zoom slika (per-tech percentile)
        p = PERCENTILE_ZOOM.get(teh, PERCENTILE_ZOOM_DEFAULT)
        print(f"\n  [{teh}] Generiram ZOOM (percentile={p}): {os.path.basename(output_path_zoom)}")
        zoom_bounds = izracunaj_crop_naslovi(shp_path, bp_coords, percentile=p)
        if zoom_bounds:
            narisi_eno(tif_path, shp_path, output_path_zoom, zoom_bounds)
        else:
            print(f"    SHP nima dovolj podatkov za zoom variant, preskocim")

    return True


def main():
    if len(sys.argv) < 2:
        print("Uporaba: py -3.10 narisi_pokrivanje.py <LOKACIJA> [<LOK2> <LOK3> ...]")
        print("Primer:  py -3.10 narisi_pokrivanje.py PANKAC")
        sys.exit(1)

    lokacije = sys.argv[1:]
    print(f"Bom obdelal {len(lokacije)} lokacij: {', '.join(lokacije)}")

    uspeli = []
    spodleteli = []
    for lokacija in lokacije:
        ok = obdelaj_lokacijo(lokacija)
        if ok:
            uspeli.append(lokacija)
        else:
            spodleteli.append(lokacija)

    print("\n================= KONEC =================")
    if uspeli:
        print(f"Uspesno: {', '.join(uspeli)}")
    if spodleteli:
        print(f"Spodletelo: {', '.join(spodleteli)}")


if __name__ == "__main__":
    main()
