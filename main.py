from flask import Flask, jsonify, request
import yfinance as yf
import math

app = Flask(__name__)

def clean(val):
    if val is None: return None
    if isinstance(val, float) and math.isnan(val): return None
    return val

def df_to_dict(df):
    if df is None or df.empty:
        return {}
    result = {}
    for col in df.columns:
        year = str(col.year)
        result[year] = {str(k): clean(v) for k, v in df[col].items()}
    return result

@app.route('/financials')
def financials():
    ticker = request.args.get('ticker', '')
    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return jsonify({
            'marketCap':         info.get('marketCap'),
            'currentPrice':      info.get('currentPrice'),
            'fiftyTwoWeekHigh':  info.get('fiftyTwoWeekHigh'),
            'fiftyTwoWeekLow':   info.get('fiftyTwoWeekLow'),
            'priceToBook':       info.get('priceToBook'),
            'enterpriseValue':   info.get('enterpriseValue'),
            'totalDebt':         info.get('totalDebt'),
            'totalCash':         info.get('totalCash'),
            'ebitda':            info.get('ebitda'),
            'ebit':              info.get('ebit'),
            'operatingCF':       info.get('operatingCashflow'),
            'freeCashFlow':      info.get('freeCashflow'),
            'totalRevenue':      info.get('totalRevenue'),
            'netIncome':         info.get('netIncomeToCommon'),
            'grossMargins':      info.get('grossMargins'),
            'operatingMargins':  info.get('operatingMargins'),
            'returnOnEquity':    info.get('returnOnEquity'),
            'returnOnAssets':    info.get('returnOnAssets'),
            'sharesOutstanding': info.get('sharesOutstanding'),
            'bookValue':         info.get('bookValue'),
        })
    except Exception as e:
        return jsonify({'error': str(e), 'ticker': ticker}), 500

@app.route('/all')
def all_data():
    ticker = request.args.get('ticker', '')
    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return jsonify({
            'info':         info,
            'balanceSheet': df_to_dict(stock.balance_sheet),
            'income':       df_to_dict(stock.financials),
            'cashflow':     df_to_dict(stock.cashflow),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

Unten **"Commit new file"** klicken.

---

**Datei 2: `requirements.txt`**

Wieder **"Add file"** → **"Create new file"**

Name: `requirements.txt`, Inhalt:
```
flask
yfinance
gunicorn
```

**"Commit new file"** klicken.

---

## Schritt 3 — Railway deployen

1. Geh auf **railway.app**
2. **"Login with GitHub"** → GitHub-Account verbinden
3. **"New Project"** → **"Deploy from GitHub repo"**
4. `yfinance-api` auswählen
5. Railway deployed automatisch — dauert 2-3 Minuten

---

## Schritt 4 — Domain generieren

1. Im Railway Dashboard dein Projekt anklicken
2. **"Settings"** → **"Networking"**
3. **"Generate Domain"** klicken
4. Du bekommst eine URL wie:
```
https://yfinance-api-production.up.railway.app
```

---

## Schritt 5 — Testen

Im Browser aufrufen:
```
https://deine-url.up.railway.app/health
https://deine-url.up.railway.app/financials?ticker=BP.L
https://deine-url.up.railway.app/all?ticker=LMS.L
```

---

## Schritt 6 — In n8n einbinden

HTTP Request Node URL:
```
https://deine-url.up.railway.app/financials?ticker={{ $json.yahoo_ticker }}
