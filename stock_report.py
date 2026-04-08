
import yfinance as yf
import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os

TICKERS = {
    "AIG":         "AIG",
    "BIDU":        "BIDU",
    "GOOGL":       "GOOGL",
    "JPM":         "JPM",
    "META":        "META",
    "QQQ":         "QQQ",
    "SHOP":        "SHOP",
    "SPY":         "SPY",
    "S&P 500 ETF": "SPY",
    "XLE":         "XLE",
    "XLP":         "XLP",
}

EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_TO   = "sriosrios97@gmail.com"


def get_price(ticker_symbol, target_date):
    """Busca el precio de cierre más cercano a target_date (hacia atrás)."""
    start = target_date - timedelta(days=5)
    end   = target_date + timedelta(days=1)
    raw = yf.download(ticker_symbol, start=start, end=end, progress=False, auto_adjust=True)

    if raw.empty:
        return None

    # Aplanar columnas si son MultiIndex
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.droplevel(1)

    close = raw["Close"]
    close.index = pd.to_datetime(close.index).normalize()
    target = pd.Timestamp(target_date).normalize()

    for delta in range(5):
        d = target - timedelta(days=delta)
        if d in close.index:
            val = close.loc[d]
            if isinstance(val, pd.Series):
                val = val.iloc[0]
            return float(val)
    return None


def build_html_table(rows, date_this, date_prev):
    fmt = lambda d: d.strftime("%d/%m/%Y")
    html = f"""
    <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:14px;">
      <tr style="background:#1a1a2e;color:white;">
        <th style="padding:10px 14px;text-align:left;">Ticker</th>
        <th style="padding:10px 14px;text-align:right;">{fmt(date_prev)}</th>
        <th style="padding:10px 14px;text-align:right;">{fmt(date_this)}</th>
        <th style="padding:10px 14px;text-align:right;">Var $</th>
        <th style="padding:10px 14px;text-align:right;">Var %</th>
      </tr>"""
    for i, (name, p_now, p_prev) in enumerate(rows):
        bg = "#f8f8f8" if i % 2 == 0 else "white"
        if p_now is not None and p_prev is not None:
            diff  = p_now - p_prev
            pct   = (diff / p_prev) * 100
            color = "#1a7a4a" if diff >= 0 else "#b81c1c"
            arrow = "▲" if diff >= 0 else "▼"
            v1 = f'<span style="color:{color}">{arrow} ${abs(diff):.2f}</span>'
            v2 = f'<span style="color:{color}">{arrow} {abs(pct):.2f}%</span>'
            s_prev = f"${p_prev:.2f}"
            s_now  = f"${p_now:.2f}"
        else:
            v1 = v2 = s_prev = s_now = "N/D"
        html += f"""
      <tr style="background:{bg};">
        <td style="padding:9px 14px;font-weight:bold;">{name}</td>
        <td style="padding:9px 14px;text-align:right;">{s_prev}</td>
        <td style="padding:9px 14px;text-align:right;">{s_now}</td>
        <td style="padding:9px 14px;text-align:right;">{v1}</td>
        <td style="padding:9px 14px;text-align:right;">{v2}</td>
      </tr>"""
    return html + "</table>"


def send_email(html_body, date_this):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Reporte semanal de acciones — {date_this.strftime('%d/%m/%Y')}"
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    print("Email enviado correctamente.")


def main():
    today = datetime.today()
    days_since_wed = (today.weekday() - 2) % 7
    last_wed = (today - timedelta(days=days_since_wed)).replace(hour=0, minute=0, second=0, microsecond=0)
    prev_wed = last_wed - timedelta(days=7)

    rows = []
    for name, symbol in TICKERS.items():
        p_now  = get_price(symbol, last_wed)
        p_prev = get_price(symbol, prev_wed)
        print(f"{name}: {p_prev} → {p_now}")
        rows.append((name, p_now, p_prev))

    html = f"""<html><body style="font-family:Arial,sans-serif;padding:20px;">
    <h2 style="color:#1a1a2e;">Reporte semanal de acciones</h2>
    <p style="color:#555;">Comparación miércoles a miércoles.</p>
    {build_html_table(rows, last_wed, prev_wed)}
    <p style="color:#999;font-size:12px;margin-top:16px;">Fuente: Yahoo Finance. Generado automáticamente.</p>
    </body></html>"""

    send_email(html, last_wed)


if __name__ == "__main__":
    main()
