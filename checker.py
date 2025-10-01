import os, requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage

URL = "https://www.janestreet.com/puzzles/current-puzzle/"
STATE_PATH = ".state/pdf_url.txt"

SMTP_HOST = os.environ.get("SMTP_HOST")      # p.ej. smtp.gmail.com
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")      # tu email remitente
SMTP_PASS = os.environ.get("SMTP_PASS")      # app password (no tu contraseña normal)
MAIL_TO   = franrodriguezcarretero@gmail.com        # destinatario
MAIL_SUBJ = "Jane Street: ¡nuevo puzzle!"

def get_current_pdf_url():
    # Descarga y obtiene el primer enlace a PDF (el del puzzle)
    r = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # Busca <a ... href="...pdf">
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            # Normaliza URLs relativas
            if href.startswith("/"):
                return "https://www.janestreet.com" + href
            return href
    # Si no hay PDF, devolvemos None
    return None

def read_prev():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def write_state(s):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        f.write(s if s else "")

def send_email(subject, body):
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MAIL_TO]):
        print("Faltan variables SMTP → no se envía email.")
        return
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

def main():
    cur_pdf = get_current_pdf_url()
    prev_pdf = read_prev()

    if prev_pdf is None:
        # Primera ejecución del mes: guarda y no notifica para evitar falsa alarma
        write_state(cur_pdf or "")
        print("Estado inicial guardado:", cur_pdf)
        return

    if cur_pdf and cur_pdf != prev_pdf:
        write_state(cur_pdf)
        body = f"Se ha detectado un nuevo puzzle.\n\nPágina: {URL}\nPDF: {cur_pdf}\n"
        send_email(MAIL_SUBJ, body)
        print("Cambio detectado. Email enviado.")
    else:
        print("Sin cambios.")

if __name__ == "__main__":
    main()
