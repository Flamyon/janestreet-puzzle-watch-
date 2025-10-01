#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import apprise

URL = "https://www.janestreet.com/puzzles/current-puzzle/"
STATE_FILE = ".puzzle_month_state.txt"
UA = "Mozilla/5.0 (compatible; JS-Puzzle-Watch/1.0)"
APPRISE_URLS = os.getenv("APPRISE_URLS", "").strip()  # p.ej. "mailto://... , tgram://TOKEN/CHATID"

def notify(title: str, body: str):
    if not APPRISE_URLS:
        print("⚠️  APPRISE_URLS vacío → no se envía notificación.")
        return
    apobj = apprise.Apprise()
    # Permite múltiples destinos separados por coma o nueva línea
    for url in [u.strip() for u in APPRISE_URLS.replace("\n", ",").split(",") if u.strip()]:
        apobj.add(url)
    apobj.notify(title=title, body=body)

def fetch_month_year():
    r = requests.get(URL, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    m = soup.select_one('input[name="puzzle_month"][type="hidden"]')
    y = soup.select_one('input[name="puzzle_year"][type="hidden"]')
    if not m or not m.has_attr("value"):
        raise RuntimeError("No se encontró input[name='puzzle_month'].")
    month = m["value"].strip()
    year = y["value"].strip() if (y and y.has_attr("value")) else ""
    return month, year

def read_prev():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = f.read().strip()
            if not data:
                return None
            parts = data.split(",")
            month = parts[0].strip()
            year = parts[1].strip() if len(parts) > 1 else ""
            return month, year
    except FileNotFoundError:
        return None

def write_state(month: str, year: str):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(f"{month},{year}")

def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    try:
        cur_m, cur_y = fetch_month_year()
    except Exception as e:
        print(f"[{now}] Error: {e}")
        sys.exit(1)

    prev = read_prev()
    if prev is None:
        write_state(cur_m, cur_y)
        print(f"[{now}] Estado inicial guardado: month={cur_m}, year={cur_y}")
        return

    prev_m, prev_y = prev
    if cur_m != prev_m:
        write_state(cur_m, cur_y)
        title = "Jane Street Puzzle: puzzle_month ha cambiado"
        body = (
            f"Anterior: {prev_m} {('(year '+prev_y+')' if prev_y else '')}\n"
            f"Actual:   {cur_m} {('(year '+cur_y+')' if cur_y else '')}\n\n"
            f"Página: {URL}\n"
            f"Fecha (UTC): {now}\n"
        )
        notify(title, body)
        print(f"[{now}] Cambio detectado → notificado.")
    else:
        print(f"[{now}] Sin cambios (month={cur_m}).")

if __name__ == "__main__":
    main()
