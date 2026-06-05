from flask import Flask, jsonify, request
import yfinance as yf
import math

app = Flask(__name__)

HOLDER_BLACKLIST = {
    'spreadex', 'winterflood', 'peel hunt', 'interactive brokers',
    'hargreaves lansdown', 'ig group', 'etrade', 'td ameritrade',
    'charles schwab', 'fidelity', 'vanguard', 'blackrock',
}

def clean(val):
    if val is None: return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)): return None
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
    ticker     = request.args.get('ticker', '')
    meldung_id = request.args.get('meldung_id', '')

    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400

    try:
        stock = yf.Ticker(ticker)
        info  = stock.info
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
            'sector':            info.get('sector'),
            'industry':          info.get('industry'),
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
        info  = stock.info
        return jsonify({
            'info':         info,
            'balanceSheet': df_to_dict(stock.balance_sheet),
            'income':       df_to_dict(stock.financials),
            'cashflow':     df_to_dict(stock.cashflow),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/holders')
def holders_endpoint():
    ticker = request.args.get('ticker', '')
    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        roster     = stock.insider_roster_holders
        shares_out = info.get('sharesOutstanding') or 1

        holders = []
        if roster is not None and not roster.empty:
            for _, row in roster.iterrows():
                name = row.get('Name', '') or ''
                if any(b in name.lower() for b in HOLDER_BLACKLIST):
                    continue
                shares = row.get('Shares Owned Directly', 0) or 0
                holders.append({
                    'name':             name,
                    'shares':           int(shares),
                    'stake_pct':        round(shares / shares_out * 100, 2),
                    'last_transaction': row.get('Most Recent Transaction', ''),
                    'last_date':        str(row.get('Latest Transaction Date', ''))[:10],
                })
        holders = sorted(holders, key=lambda x: x['stake_pct'], reverse=True)

        return jsonify({'ticker': ticker, 'holders': holders})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dna')
def dna():
    ticker = request.args.get('ticker', '')
    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400

    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        # --- Helpers ---
        def truncate(text, limit=300):
            if not text: return None
            return text[:limit] + '...' if len(text) > limit else text

        def pct(val):
            if val is None: return None
            try:
                f = float(val)
                if math.isnan(f) or math.isinf(f): return None
                return round(f * 100, 1)
            except (TypeError, ValueError):
                return None

        def ratio(val):
            if val is None: return None
            try:
                f = float(val)
                if math.isnan(f) or math.isinf(f): return None
                return round(f, 1)
            except (TypeError, ValueError):
                return None

        # --- Price History: 1 Jahr, wöchentlich ---
        try:
            hist    = stock.history(period='1y', interval='1wk')
            history = [
                {
                    'date':   str(row.Index.date()),
                    'close':  round(row.Close, 4) if row.Close else None,
                    'volume': int(row.Volume)     if row.Volume else None,
                }
                for row in hist.itertuples()
                if row.Close and not math.isnan(row.Close)
            ]
        except Exception:
            history = []

        # --- Annual Statements: 3 Jahre, nur Income + Cashflow ---
        def parse_statement(df, keys):
            if df is None or df.empty:
                return {}
            result = {}
            cols = sorted(df.columns, reverse=True)[:3]
            for col in cols:
                year = str(col.year)
                row  = {}
                for k in keys:
                    val    = df.loc[k, col] if k in df.index else None
                    row[k] = clean(val)
                if any(v is not None for v in row.values()):
                    result[year] = row
            return result

        income_keys = [
            'Total Revenue',
            'Gross Profit',
            'Operating Income',
            'EBITDA',
            'Net Income',
        ]
        cashflow_keys = [
            'Operating Cash Flow',
            'Free Cash Flow',
            'Capital Expenditure',
        ]

        try:
            income   = parse_statement(stock.financials, income_keys)
        except Exception:
            income   = {}

        try:
            cashflow = parse_statement(stock.cashflow, cashflow_keys)
        except Exception:
            cashflow = {}

        # --- Holders ---
        try:
            roster     = stock.insider_roster_holders
            shares_out = info.get('sharesOutstanding') or 1
            holders    = []
            if roster is not None and not roster.empty:
                for _, row in roster.iterrows():
                    name = row.get('Name', '') or ''
                    if any(b in name.lower() for b in HOLDER_BLACKLIST):
                        continue
                    shares = row.get('Shares Owned Directly', 0) or 0
                    holders.append({
                        'name':             name,
                        'shares':           int(shares),
                        'stake_pct':        round(shares / shares_out * 100, 2),
                        'last_transaction': row.get('Most Recent Transaction', ''),
                        'last_date':        str(row.get('Latest Transaction Date', ''))[:10],
                    })
            holders = sorted(holders, key=lambda x: x['stake_pct'], reverse=True)
        except Exception:
            holders = []

        # --- DNA Status Check ---
        core_fields = [
            info.get('marketCap'),
            info.get('totalRevenue'),
            info.get('currentPrice'),
        ]
        has_core       = any(f is not None for f in core_fields)
        has_history    = len(history) > 0
        has_statements = bool(income or cashflow)

        if not has_core and not has_history and not has_statements:
            dna_status = 'no_data'
        elif not has_core:
            dna_status = 'partial'
        else:
            dna_status = 'ok'

        return jsonify({
            'ticker':     ticker,
            'dna_status': dna_status,

            'company': {
                'name':        info.get('shortName'),
                'sector':      info.get('sector'),
                'industry':    info.get('industry'),
                'employees':   info.get('fullTimeEmployees'),
                'website':     info.get('website'),
                'description': truncate(info.get('longBusinessSummary'), 300),
            },

            'snapshot': {
                'marketCap':        info.get('marketCap'),
                'currentPrice':     info.get('currentPrice'),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
                'fiftyTwoWeekLow':  info.get('fiftyTwoWeekLow'),
                'beta':             ratio(info.get('beta')),
                'insidersPct':      pct(info.get('heldPercentInsiders')),
                'institutionsPct':  pct(info.get('heldPercentInstitutions')),
            },

            'multiples': {
                'trailingPE':  ratio(info.get('trailingPE')),
                'forwardPE':   ratio(info.get('forwardPE')),
                'evToEbitda':  ratio(info.get('enterpriseToEbitda')),
                'evToRevenue': ratio(info.get('enterpriseToRevenue')),
                'priceToBook': ratio(info.get('priceToBook')),
                'pegRatio':    ratio(info.get('pegRatio')),
            },

            'financials': {
                'enterpriseValue':  info.get('enterpriseValue'),
                'totalRevenue':     info.get('totalRevenue'),
                'ebitda':           info.get('ebitda'),
                'ebit':             info.get('ebit'),
                'netIncome':        info.get('netIncomeToCommon'),
                'freeCashFlow':     info.get('freeCashflow'),
                'operatingCF':      info.get('operatingCashflow'),
                'totalDebt':        info.get('totalDebt'),
                'totalCash':        info.get('totalCash'),
                'grossMargins':     pct(info.get('grossMargins')),
                'operatingMargins': pct(info.get('operatingMargins')),
            },

            'statements': {
                'income':   income,
                'cashflow': cashflow,
            },

            'history': history,

            'holders': holders,
        })

    except Exception as e:
        return jsonify({'error': str(e), 'ticker': ticker}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
