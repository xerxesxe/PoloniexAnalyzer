"""
Analyzer for running analysis on given data models :)

Hopefully all the methods in here will be uses for analyzing the data. If that
stops being true and if I were a good developer (it wouldn't have happened in
the first place) I would update this documentation.
"""
import operator
import time
from collections import defaultdict

import math

import dev_utils
import matplotlib.dates as mpldate
import poloniex_apis.trading_api as trading_api
import utils
from poloniex_apis import public_api
from poloniex_apis.api_models.balances import Balances
from poloniex_apis.api_models.deposit_withdrawal_history import DWHistory
from poloniex_apis.api_models.ticker_price import TickerPrice
from poloniex_apis.api_models.trade_history import TradeHistory
from poloniex_apis.public_api import return_usd_btc
from utils import _get_epoch, _to_percent_change, _plot_graph


def get_overview():
    balances = Balances(trading_api.return_complete_balances())
    dw_history = DWHistory(trading_api.return_deposits_withdrawals())

    balance, deposits, withdrawals = dw_history.get_btc_dw_history()
    current = balances.get_btc_total()

    usd_btc_price = return_usd_btc()
    balance_percentage = float("{:.4}".format(current / balance * 100))
    btc_balance_sum = current - balance
    usd_balance_sum = "{:.2f}".format(btc_balance_sum * usd_btc_price)

    # TODO This is really WET
    print "---Earnings/Losses Against Balance--"
    print "{} BTC/${}".format(btc_balance_sum, usd_balance_sum)
    if balance_percentage < 100:
        print "Stop trading, you're an idiot"
        print "{}%".format(balance_percentage)
    elif balance_percentage < 110:
        print "Put your funds in an index, dumb dumb"
        print "{}%".format(balance_percentage)
    elif balance_percentage < 150:
        print "Not bad"
        print "{}%".format(balance_percentage)
    elif balance_percentage < 175:
        print "You belong here"
        print "{}%".format(balance_percentage)
    elif balance_percentage < 200:
        print "Like striking crypto-oil"
        print "{}%".format(balance_percentage)
    elif balance_percentage < 250:
        print "On your way to becoming a bitcoin millionaire"
        print "{}%".format(balance_percentage)
    else:
        print "Cryptocurrencies can get heavy, you should send them over to me for safe keeping!"
        print "{}%".format(balance_percentage)

    deposits_percentage = float("{:.4}".format(current / deposits * 100))
    btc_deposits_sum = current - deposits
    usd_deposits_sum = "{:.2f}".format(btc_deposits_sum * usd_btc_price)

    print "--Earnings/Losses Against Deposits--"
    print "{} BTC/${}".format(btc_deposits_sum, usd_deposits_sum)
    if deposits_percentage < 100:
        print "Stop trading, you're an idiot"
        print "{}%".format(deposits_percentage)
    elif deposits_percentage < 110:
        print "Put your funds in an index, dumb dumb"
        print "{}%".format(deposits_percentage)
    elif deposits_percentage < 150:
        print "Not bad"
        print "{}%".format(deposits_percentage)
    elif deposits_percentage < 175:
        print "You belong here"
        print "{}%".format(deposits_percentage)
    elif deposits_percentage < 200:
        print "Like striking crypto-oil"
        print "{}%".format(deposits_percentage)
    elif deposits_percentage < 250:
        print "On your way to becoming a bitcoin millionaire"
        print "{}%".format(deposits_percentage)
    else:
        print "Cryptocurrencies can get heavy, you should send them over to me for safe keeping!"
        print "{}%".format(deposits_percentage)


def get_detailed_overview():
    ticker_price = TickerPrice(public_api.return_ticker())
    trade_history = trading_api.return_trade_history()
    print "Warning, if you made non BTC trades, for example, ETH to ETC, some"
    print "of the values may look unusual. Since non BTC trades have not been"
    print "calculated in."
    for ticker in trade_history:
        if ticker.startswith("BTC_"):
            current = list(reversed(trade_history[ticker]))
            btc_sum = 0
            for trade in current:
                if trade['type'] == 'buy':
                    btc_sum += float(trade["total"])
                else:
                    # For some reason, the total for sells do not include the
                    # fee so we include it here.
                    btc_sum -= (float(trade["total"]) * (1 - float(trade["fee"])))

            ticker_sum = 0
            for trade in current:
                if trade['type'] == 'buy':
                    ticker_sum += float(trade["amount"])  # Total
                    ticker_sum -= float(trade["amount"]) * float(trade["fee"])  # Fee
                else:
                    ticker_sum -= float(trade["amount"])
            if ticker_sum > 0.000000001:
                current_btc_sum = float(ticker_price.get_price_for_ticker(ticker)) * ticker_sum
                total_btc = current_btc_sum - btc_sum
                total_usd = float("{:.4}".format(total_btc * ticker_price.get_price_for_ticker("USDT_BTC")))
                print "--------------{}----------------".format(ticker)
                print "You invested {} BTC for {} {}/{} BTC".format(btc_sum, ticker_sum, ticker.split("_")[1],
                                                                    current_btc_sum)
                print "If you sold it all at the current price (assuming enough sell orders)"

                if total_btc < 0:
                    print utils.bcolors.RED,
                else:
                    print utils.bcolors.GREEN,
                print "{} BTC/{} USD".format(total_btc, total_usd)
                print utils.bcolors.END_COLOR,

    return current


def calculate_fees():
    # TODO Should this take in the data models or call it itself
    trade_history = TradeHistory(trading_api.return_trade_history())
    all_fees = trade_history.get_all_fees()

    print "--------------All Fees--------------"
    for stock, fees in all_fees.iteritems():
        print "{}={}".format(stock, fees)
    print "------------------------------------"
    total=0
    for stock, fees in all_fees.iteritems():
        total +=fees
    print "Total={}".format(total)


def get_change_over_time():
    """
    Returns a list of currencies whose volume is over the threshold.
    :return:
    """
    threshold = 1000
    currency_list = []

    volume_data = public_api.return_24_hour_volume()
    for item in volume_data:
        if item.startswith('BTC'):
            if float(volume_data.get(item).get('BTC')) > threshold:
                currency_list.append(item)

    currencies = {}
    for currency_pair in currency_list:
        currencies[currency_pair] = float(volume_data.get(currency_pair).get(u'BTC'))
    sorted_currencies = sorted(currencies.items(), key=operator.itemgetter(1), reverse=True)

    period = 300
    print "Change over time for BTC traded currencies with volume > 1000 BTC"
    for currency in sorted_currencies:
        now = int(time.time())
        last_week = now - 604800
        history = public_api.return_chart_data(
            period=period,
            currency_pair=currency[0],
            start=last_week,
        )
        print "Currency: {}, Volume: {}".format(currency[0], currency[1])
        print "  1H: {}, 24H: {}, 2D: {}, 3D: {}, 4D: {}, 1W: {}".format(
            _to_percent_change(history[-1]['close'] / history[-(3600 / period - 1)]['close']),
            _to_percent_change(history[-1]['close'] / history[-(86400 / period - 1)]['close']),
            _to_percent_change(history[-1]['close'] / history[-(172800 / period - 1)]['close']),
            _to_percent_change(history[-1]['close'] / history[-(259200 / period - 1)]['close']),
            _to_percent_change(history[-1]['close'] / history[-(345600 / period - 1)]['close']),
            _to_percent_change(history[-1]['close'] / history[-(604800 / period - 1)]['close']),
        )
        time.sleep(1)


def get_account_balance():
    # dev_utils.dict_to_file(trading_api.return_trade_history(), 'trade_history.txt')
    trade_history = dev_utils.file_to_dict('trade_history.txt')
    dw_history = dev_utils.file_to_dict('dw_history.txt')

    name = raw_input("Currency?")
    dash = trade_history[name]
    ordered_dash = sorted(dash, key=lambda x: _get_epoch(x['date']))
    dash_balance = 0
    bitcoin_balance = 0
    dates = []
    values = []
    for trade in ordered_dash:
        if trade["type"] == "buy":
            dash_balance += float(trade["amount"])*(1-float(trade["fee"]))
            bitcoin_balance -= float(trade["amount"])*float(trade["rate"])
        else:
            dash_balance -= float(trade["amount"])
            bitcoin_balance += float(trade["amount"])*float(trade["rate"])*(1-float(trade["fee"]))
        dates.append(mpldate.epoch2num(_get_epoch(trade['date'])))
        values.append(dash_balance*float(trade["rate"]) + bitcoin_balance)
    print "Meow2"

    graph_data_dict = {
        'x': dates,
        'y': values,
        'colors': None,
        'title': "Trade history for {}".format(name),
        'x-label': "Date",
        'y-label': "BTC"}
    _plot_graph(graph_data_dict)


def get_account_balance2():
    # dev_utils.dict_to_file(trading_api.return_trade_history(), 'trade_history.txt')
    trade_history = dev_utils.file_to_dict('trade_history.txt')
    dw_history = dev_utils.file_to_dict('dw_history.txt')

    master_dict = defaultdict(int)
    sorted_dw = _get_sorted_dw_history(dw_history)

    for date, value in sorted_dw:
        master_dict[date] += value
    non_btc_dict = {}


    for currency, trades in trade_history.iteritems():
        last_dash = 0
        for trade in trades:
            epoch = _get_epoch(trade["date"])
            value = float(trade["total"])
            if trade["type"] == "sell":
                value = -value
            else:
                value *= 1 - float(trade["fee"])

            if currency.startswith("BTC"):
                master_dict[epoch] += value
            else:
                if currency in non_btc_dict:
                    non_btc_dict[currency][epoch] += value
                else:
                    non_btc_dict[currency] = defaultdict(int)
                    non_btc_dict[currency][epoch] += value
            last_dash = value


    for currency, data in non_btc_dict.iteritems():
        for item in data:
            ticker = "BTC_" + currency.split("_")[0]
            estimated_price = public_api.return_chart_data(300, ticker, epoch, epoch+300)[0]['weightedAverage']
            master_dict[epoch] += estimated_price*float(data[item])

    master_list = []
    for epoch, value in master_dict.iteritems():
        master_list.append((epoch, value))
    master_list.sort(key=lambda tup: tup[0])

    dates = []
    values = []
    balance = 0
    for item in master_list:
        dates.append(mpldate.epoch2num(item[0]))
        balance += item[1]
        values.append(balance)

    graph_data_dict = {'x': dates, 'y': values, "colors": None}
    _plot_graph(graph_data_dict)


def _get_sorted_dw_history(dw_history):
    flat_dw_list = []
    for deposit in dw_history["deposits"]:
        flat_dw_list.append((deposit["timestamp"], float(deposit["amount"])))
    for withdrawal in dw_history["withdrawals"]:
        flat_dw_list.append((withdrawal["timestamp"], -float(withdrawal["amount"])))
    flat_dw_list.sort(key=lambda tup: tup[0])
    return flat_dw_list

    dates = []
    values = []
    balance = 0
    for item in flat_dw_list:
        dates.append(mpldate.epoch2num(item[0]))
        balance += item[1]
        values.append(balance)

    return dates, values


def calculate_graph_stats():
    _calculate_graph_stats(period_length=300, periods=50)


def _calculate_graph_stats(period_length, periods):
    thing = public_api.return_chart_data(
        period=period_length,
        currency_pair="BTC_DASH",
        start=time.time() - periods * period_length - 1,
        end=time.time(),
    )

    total = 0
    for item in thing:
        total += float(item['close'])
    simple_moving_average = total/periods

    total = 0
    for item in thing:
        total += (float(item['close']) - simple_moving_average)**2
    standard_deviation = math.sqrt(total/periods)

    return simple_moving_average, standard_deviation
