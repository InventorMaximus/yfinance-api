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
    meldung_id = request.args.get('meldung_id', '')

    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return jsonify({
            'meldung_id':        meldung_id,
            'ticker':            ticker,
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
        return jsonify({'error': str(e), 'ticker': ticker, 'meldung_id': meldung_id}), 500

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
