@app.route('/financials')
def financials():
    ticker = request.args.get('ticker', '')
    meldung_id = request.args.get('meldung_id', '')  # ← neu
    
    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return jsonify({
            'meldung_id':        meldung_id,             # ← neu
            'ticker':            ticker,                  # ← neu (hilfreich für debugging)
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
