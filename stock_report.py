import yfinance as yf
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os

TICKERS = {
    "AIG":   "AIG",
    "BIDU":  "BIDU",
    "GOOGL": "GOOGL",
    "JPM":   "JPM",
    "META":  "META",
    "QQQ":   "QQQ",
    "SHOP":  "SHOP",
    "SPY":   "SPY",
    "S&P 500 ETF": "SPY",
    "XLE":   "XLE",
    "XLP":   "XLP",
}

EMAIL_FROM   = os.environ["EMAIL_FROM"]    # tu Gmail
EMAIL_PASS   = os.environ["EMAIL_PASS"]    # contraseña de app Gmail
EMAIL_TO     = "sriosrios97@gmail.com"


def get_wednesday_prices(ticker_symbol):
    """Devuelve el precio de cierre de los últimos 2 miércoles."""
    today = datetime.today()
    days_since_wed = (today.weekday() - 2) % 7
    last_wed = today - timedelta(days=days_since_wed)
    prev_wed = last_wed - timedelta(days=7)

    data = yf.download(
        ticker_symbol,
        start=prev_wed - timedelta(days=1),
        end=last_wed + timedelta(days=1),
        progress=False,
        auto_adjust=True,
    )

    def price_on(date):
        for delta in range(4):
            d = (date - timedelta(days=delta)).strftime("%Y-%m-%d")
            if d in data.index.strftime("%Y-%m-%d").tolist():
                idx = data.index.strftime("%Y-%m-%d").tolist().index(d)
                return float(data["Close"].iloc[idx])
        return None

    return price_on(last_wed), price_on(prev_wed), last_wed, prev_wed


def build_html_table(rows, date_this, date_prev):
    date_fmt = lambda d: d.strftime("%d/%m/%Y")
    header = f"""
    <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:14px;">
      <tr style="background:#1a1a2e;color:white;">
        <th style="padding:10px 14px;text-align:left;">Ticker</th>
        <th style="padding:10px 14px;text-align:right;">{date_fmt(date_prev)}</th>
        <th style="padding:10px 14px;text-align:right;">{date_fmt(date_this)}</th>
        <th style="padding:10px 14px;text-align:right;">Variación $</th>
        <th style="padding:10px 14px;text-align:right;">Variación %</th>
      </tr>"""
    body = ""
    for i, (name, p_now, p_prev) in enumerate(rows):
        bg = "#f8f8f8" if i % 2 == 0 else "white"
        if p_now and p_prev:
            diff = p_now - p_prev
            pct  = (diff / p_prev) * 100
            color = "#1a7a4a" if diff >= 0 else "#b81c1c"
            arrow = "▲" if diff >= 0 else "▼"
            var_str   = f'<span style="color:{color}">{arrow} ${abs(diff):.2f}</span>'
            pct_str   = f'<span style="color:{color}">{arrow} {abs(pct):.2f}%</span>'
            prev_str  = f"${p_prev:.2f}"
            now_str   = f"${p_now:.2f}"
        else:
            var_str = pct_str = "N/D"
            prev_str = now_str = "N/D"
        body += f"""
      <tr style="background:{bg};">
        <td style="padding:9px 14px;font-weight:bold;">{name}</td>
        <td style="padding:9px 14px;text-align:right;">{prev_str}</td>
        <td style="padding:9px 14px;text-align:right;">{now_str}</td>
        <td style="padding:9px 14px;text-align:right;">{var_str}</td>
        <td style="padding:9px 14px;text-align:right;">{pct_str}</td>
      </tr>"""
    return header + body + "</table>"


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
    rows = []
    date_this = date_prev = None
    for name, symbol in TICKERS.items():
        p_now, p_prev, d_now, d_prev = get_wednesday_prices(symbol)
        date_this = d_now
        date_prev = d_prev
        rows.append((name, p_now, p_prev))
        print(f"{name}: {p_prev} → {p_now}")

    html = f"""
    <html><body style="font-family:Arial,sans-serif;padding:20px;">
    <h2 style="color:#1a1a2e;">Reporte semanal de acciones</h2>
    <p style="color:#555;">Comparación miércoles a miércoles.</p>
    {build_html_table(rows, date_this, date_prev)}
    <p style="color:#999;font-size:12px;margin-top:16px;">
      Fuente: Yahoo Finance. Generado automáticamente.
    </p>
    </body></html>"""

    send_email(html, date_this)


if __name__ == "__main__":
    main()
