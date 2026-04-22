# -*- coding: utf-8 -*-
"""
Zacasno postavi ACTIVE=1 za vse celice/transmitterje dane lokacije
v atoll_d96, pozeni poljubno delo, nato povrne ACTIVE=0.

Namenjeno je za studije upravicenosti / pokrivanja planiranih (se ne
zivih) baznih postaj — npr. SCVEN — kjer so celice v SQL-ju oznacene
kot ACTIVE=0, zato se ne sinhronizirajo v Atoll. Za eno-kratni export
jih zacasno postavimo na 1, spustimo coverage pipeline, in takoj
povrnemo na 0, da nocna sinhronizacija ne vleche planiranih celic
v produkcijo.

Uporaba (kot context manager):

    from sql_toggle_active_celice import zacasno_aktivne_celice

    with zacasno_aktivne_celice("SCVEN"):
        # tvoja koda — npr. pozeni VBS chain + SignalsExport
        ...

Uporaba (direkten toggle):

    from sql_toggle_active_celice import nastavi_active_po_seznamu
    nastavi_active_po_seznamu(['SCVEN07A', 'SCVEN08A'], 1)
    # ... delo ...
    nastavi_active_po_seznamu(['SCVEN07A', 'SCVEN08A'], 0)

OPOZORILA:
  * Vedno try/finally (oz. `with`). Ce proces pade sredi dela, bodo
    celice ostale ACTIVE=1 in bodo pricurljale v naslednjo nocno
    sinhronizacijo.
  * `LIKE 'SCVEN%'` ujame tudi morebitne podobne lokacije. Za
    produkcijo raje uporabi `nastavi_active_po_seznamu` z eksplicitnim
    seznamom TX_ID.
  * Ta toggle obide kolega's Novo/Spremeni CSV pipeline. Po spremembi
    ACTIVE flaga je treba Atoll ATL sproviciti, da prebere novo
    stanje — ponavadi preko
    `posodobi_atoll_3794_update_planirano_comp_zone.vbs`.
"""
import pyodbc
from contextlib import contextmanager


# ---------------------------------------------------------------------------
# Povezava na SQL (enake credentialse kot naredi_shp_za_112.py)
# ---------------------------------------------------------------------------
def _connect():
    return pyodbc.connect(
        'Driver={SQL Server};'
        'Server=BPW-DENALI;'
        'Database=atoll_d96;'
        'UID=beribaze;'
        'PWD=beribaze'
    )


# Tabele transmitterjev, kjer lezi ACTIVE flag.
# TX_ID se ponavadi zacne z imenom lokacije (npr. SCVEN07A, SCVEN1, ...).
_TABELE_TX = [
    "atoll_d96.dbo.gtransmitters",   # GSM
    "atoll_d96.dbo.utransmitters",   # UMTS
    "atoll_d96.dbo.xgtransmitters",  # LTE/NR
]


# ---------------------------------------------------------------------------
# Pomozna funkcija: zberi vse TX_ID, ki ustrezajo lokaciji (za log)
# ---------------------------------------------------------------------------
def _zberi_tx_id(cur, lokacija):
    """Vrne seznam (tabela, TX_ID) vseh kandidatov pred toggle-om."""
    najdeno = []
    for tab in _TABELE_TX:
        cur.execute(
            f"SELECT TX_ID FROM {tab} "
            f"WHERE TX_ID LIKE ? AND ACTIVE = 0",
            (lokacija + '%',)
        )
        for (tx_id,) in cur.fetchall():
            najdeno.append((tab, tx_id))
    return najdeno


# ---------------------------------------------------------------------------
# Toggle po imenu lokacije (LIKE 'lokacija%')
# ---------------------------------------------------------------------------
def nastavi_active(lokacija, vrednost):
    """
    Postavi ACTIVE=vrednost za vse transmitterje, katerih TX_ID se zacne
    z `lokacija`. vrednost = 0 ali 1.

    Vraca stevilo spremenjenih vrstic. Ce nastavljamo na 1, iscemo samo
    tiste, ki so trenutno 0 (in obratno), da ne kvarimo celic, ki so
    bile rocno drugace postavljene.
    """
    assert vrednost in (0, 1)
    conn = _connect()
    cur = conn.cursor()
    skupaj = 0
    for tab in _TABELE_TX:
        obratna = 1 - vrednost
        cur.execute(
            f"UPDATE {tab} SET ACTIVE = ? "
            f"WHERE TX_ID LIKE ? AND ACTIVE = ?",
            (vrednost, lokacija + '%', obratna)
        )
        skupaj += cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    print(f"[{lokacija}] ACTIVE={vrednost} -> spremenjeno {skupaj} vrstic")
    return skupaj


# ---------------------------------------------------------------------------
# Context manager: aktiviraj, pozeni blok, revert
# ---------------------------------------------------------------------------
@contextmanager
def zacasno_aktivne_celice(lokacija):
    """
    Aktivira celice za lokacijo, pozene blok pod `with`, nato jih
    vrne v stanje ACTIVE=0. Try/finally poskrbi za revert tudi ob
    izjemi — NE pa pri kill -9 oz. crashu procesa.
    """
    spremenjenih = nastavi_active(lokacija, 1)
    try:
        yield spremenjenih
    finally:
        # Revertiramo samo tiste, ki so zdaj 1. Opomba: ce je bilo kaj
        # rocno postavljeno na 1 med nasim blokom, bomo tudi to vrnili
        # na 0. Mozna izboljsava je shraniti konkretni seznam TX_ID
        # pred UPDATE-om in povrniti po tem seznamu.
        nastavi_active(lokacija, 0)


# ---------------------------------------------------------------------------
# Natancnejsi toggle: po eksplicitnem seznamu TX_ID
# ---------------------------------------------------------------------------
def nastavi_active_po_seznamu(tx_id_seznam, vrednost):
    """
    Natancnejsi toggle: tocno doloceni TX_ID. Primeren za produkcijo,
    ker ne potepa po LIKE vzorcu.

    tx_id_seznam = ['SCVEN07A', 'SCVEN08A', ...]
    vrednost     = 0 ali 1
    """
    assert vrednost in (0, 1)
    if not tx_id_seznam:
        return 0
    conn = _connect()
    cur = conn.cursor()
    placeholders = ",".join("?" * len(tx_id_seznam))
    skupaj = 0
    for tab in _TABELE_TX:
        cur.execute(
            f"UPDATE {tab} SET ACTIVE = ? "
            f"WHERE TX_ID IN ({placeholders})",
            [vrednost, *tx_id_seznam]
        )
        skupaj += cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    print(
        f"ACTIVE={vrednost} -> spremenjeno {skupaj} vrstic "
        f"za {len(tx_id_seznam)} TX_ID"
    )
    return skupaj


# ---------------------------------------------------------------------------
# CLI primer uporabe
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    lok = sys.argv[1] if len(sys.argv) > 1 else "SCVEN"

    with zacasno_aktivne_celice(lok):
        print(f"Celice za {lok} so zdaj aktivne. Pozeni export / analizo...")
        # Primer:
        # import subprocess
        # subprocess.run([
        #     'cscript',
        #     r'D:\Atoll_projects_planer01\Skripte\VBasic\posodobi_atoll_3794_update_planirano_comp_zone.vbs'
        # ])
        input("Pritisni ENTER ko si koncal, da revertiram ACTIVE na 0...")
