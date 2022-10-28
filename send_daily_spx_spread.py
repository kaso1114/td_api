from datetime import date, timedelta, datetime

import secretsTDA
import pandas as pd
from tda import auth
from tda.utils import Utils
from tda.orders.options import bull_put_vertical_open


def get_sell_put_spread_chains(main_price, put_chains_df, dte):
    # Get sell put chain
    strike_price = main_price
    sp_df = put_chains_df[(put_chains_df.daysToExpiration == dte) & (put_chains_df.strikePrice == strike_price) & (put_chains_df.symbol.str.startswith("SPXW_"))]
    if sp_df.shape[0] == 0:
        strike_price = main_price - 5
        sp_df = put_chains_df[(put_chains_df.daysToExpiration == dte) & (put_chains_df.strikePrice == strike_price) & (put_chains_df.symbol.str.startswith("SPXW_"))]
        print(f'Change sell put price to {strike_price}')
    if sp_df.shape[0] == 0:
        raise ValueError(f">> Can't find sell put chain by {strike_price=}, {dte=}")

    # Get buy put chain
    strike_price_2 = strike_price - 50
    bp_df = put_chains_df[(put_chains_df.daysToExpiration == dte) & (put_chains_df.strikePrice == strike_price_2) & (put_chains_df.symbol.str.startswith("SPXW_"))]
    if bp_df.shape[0] == 0:
        strike_price_2 = strike_price - 55
        bp_df = put_chains_df[(put_chains_df.daysToExpiration == dte) & (put_chains_df.strikePrice == strike_price_2) & (put_chains_df.symbol.str.startswith("SPXW_"))]
        print(f'Change buy put price to {strike_price_2}')
    if bp_df.shape[0] == 0:
        raise ValueError(f">> Can't find buy put chain by {strike_price_2=}, {dte=}")
    return sp_df.to_dict('records')[0], bp_df.to_dict('records')[0]


def get_sell_call_spread_chains(main_price, call_chains_df, dte):
    # Get sell call chain
    strike_price = main_price
    sp_df = call_chains_df[(call_chains_df.daysToExpiration == dte) & (call_chains_df.strikePrice == strike_price) & (call_chains_df.symbol.str.startswith("SPXW_"))]
    if sp_df.shape[0] == 0:
        strike_price = main_price + 5
        sp_df = call_chains_df[(call_chains_df.daysToExpiration == dte) & (call_chains_df.strikePrice == strike_price) & (call_chains_df.symbol.str.startswith("SPXW_"))]
        print(f'Change sell call price to {strike_price}')
    if sp_df.shape[0] == 0:
        raise ValueError(f">> Can't find sell call chain by {strike_price=}, {dte=}")

    # Get buy call chain
    strike_price_2 = strike_price + 50
    bp_df = call_chains_df[(call_chains_df.daysToExpiration == dte) & (call_chains_df.strikePrice == strike_price_2) & (call_chains_df.symbol.str.startswith("SPXW_"))]
    if bp_df.shape[0] == 0:
        strike_price_2 = strike_price + 55
        bp_df = call_chains_df[(call_chains_df.daysToExpiration == dte) & (call_chains_df.strikePrice == strike_price_2) & (call_chains_df.symbol.str.startswith("SPXW_"))]
        print(f'Change buy call price to {strike_price_2}')
    if bp_df.shape[0] == 0:
        raise ValueError(f">> Can't find buy call chain by {strike_price_2=}, {dte=}")
    return sp_df.to_dict('records')[0], bp_df.to_dict('records')[0]


def place_order(c, long_put_symbol, short_put_symbol, quantity, net_credit):
    r = c.place_order(
        secretsTDA.account_id,
        bull_put_vertical_open(long_put_symbol, short_put_symbol, quantity, net_credit).build()
    )
    r.raise_for_status()
    if r.status_code in [200, 201]:
        order_id = Utils(c, secretsTDA.account_id).extract_order_id(r)
    else:
        print(f'Send order failed: {r.status_code}')


def send_order(main_opt, min_opt, c):
    # Get spread type
    if main_opt["putCall"] == "PUT":
        spread_type = "sell put"
    else:
        spread_type = "sell call"

    # Get option middle price
    mid_price = round(((main_opt["bid"] + main_opt["ask"]) - (min_opt["bid"] + min_opt["ask"])) / 2 // 0.05 * 0.05, 2)
    order_price = max(mid_price, SP_MIN_PRICE)
    description = " ".join(main_opt["description"].split(" ")[0:4])
    print(f'{description} {main_opt["strikePrice"]:.0f}/{min_opt["strikePrice"]:.0f} {spread_type} spread, {order_price=}')

    # Send mid_price order
    print(f'Send {SP_QUANITY - 1} order, get ${order_price*(SP_QUANITY - 1)*100:,.0f} premium')
    if PLACE_ORDER:
        place_order(c, min_opt["symbol"], main_opt["symbol"], SP_QUANITY - 1, order_price)

    # Send mid_price+0.5 order
    print(f'Send 1 order, get ${(order_price + 0.05)*1*100:,.0f} premium')
    if PLACE_ORDER:
        place_order(c, min_opt["symbol"], main_opt["symbol"], 1, order_price + 0.05)


def main():
    # Get days to expiration
    today = datetime.today()
    weekly = today.weekday() + 1
    if weekly in [2, 3, 4, 5]:
        dte = 1 + 2
    elif weekly == 6:
        dte = 3
    else:
        raise ValueError(f'{today} is Week {weekly}')
    print(f'Today is {today:%Y/%m/%d %H:%M}')

    # Login TD
    try:
        c = auth.client_from_token_file(secretsTDA.token_path, secretsTDA.api_key)
    except FileNotFoundError:
        c = auth.client_from_manual_flow(secretsTDA.api_key, secretsTDA.redirect_uri, secretsTDA.token_path)

    # Get latest SPX option chain
    chains = c.get_option_chain(symbol="$SPX.X", to_date=date.today() + timedelta(days=dte)).json()
    underlying_price = chains["underlyingPrice"]
    print(f'SPX index price: {underlying_price}')

    # Get put option map
    put_chains_df = pd.json_normalize(chains["putExpDateMap"])
    put_chains_df = [pd.json_normalize(put_chains_df[c].explode()) for c in put_chains_df.columns]
    put_chains_df = pd.concat(put_chains_df).reset_index()
    put_chains_df.delta = put_chains_df.delta.astype(float)

    # Get call option map
    call_chains_df = pd.json_normalize(chains["callExpDateMap"])
    call_chains_df = [pd.json_normalize(call_chains_df[c].explode()) for c in call_chains_df.columns]
    call_chains_df = pd.concat(call_chains_df).reset_index()
    call_chains_df.delta = call_chains_df.delta.astype(float)

    # Send sell put spread order
    strike_price = int(underlying_price * 0.96 // 5 * 5)
    sp, bp = get_sell_put_spread_chains(strike_price, put_chains_df, dte)
    send_order(sp, bp, c)

    # Send sell call spread order
    strike_price = int(underlying_price * 1.04 // 5 * 5)
    sc, bc = get_sell_call_spread_chains(strike_price, call_chains_df, dte)
    send_order(sc, bc, c)
    print('-' * 50)


if __name__ == "__main__":
    PLACE_ORDER = True
    # Sell put spreads
    SP_QUANITY = 3         # Quanity must >= 2
    SP_MIN_PRICE = 0.15    # If middle price < min_price, use min_price
    # Sell call spreads
    SC_QUANITY = 2         # Quanity must >= 2
    SC_MIN_PRICE = 0.15    # If middle price < min_price, use min_price
    main()
