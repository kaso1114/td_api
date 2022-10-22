from datetime import date, timedelta, datetime

import secretsTDA
import pandas as pd
from tda import auth
from tda.utils import Utils
from tda.orders.options import bull_put_vertical_open


def get_sell_put_spread_chains(underlyingPrice, put_chains_df, dte):
    # Get sell put chain
    strike_price = underlyingPrice * 0.96 // 5 * 5
    sp_df = put_chains_df[(put_chains_df.daysToExpiration == dte) & (put_chains_df.strikePrice == strike_price) & (put_chains_df.symbol.str.startswith("SPXW_"))]
    if sp_df.shape[0] == 0:
        strike_price = (underlyingPrice * 0.96 // 5 * 5) - 5
        sp_df = put_chains_df[(put_chains_df.daysToExpiration == dte) & (put_chains_df.strikePrice == strike_price) & (put_chains_df.symbol.str.startswith("SPXW_"))]
        print(f'Change sell put price to {strike_price}')
    if sp_df.shape[0] == 0:
        raise ValueError(">> Can't find sell put chain")

    # Get buy put chain
    strike_price = strike_price - 50
    bp_df = put_chains_df[(put_chains_df.daysToExpiration == dte) & (put_chains_df.strikePrice == strike_price) & (put_chains_df.symbol.str.startswith("SPXW_"))]
    if bp_df.shape[0] == 0:
        strike_price = (strike_price - 50) - 5
        bp_df = put_chains_df[(put_chains_df.daysToExpiration == dte) & (put_chains_df.strikePrice == strike_price) & (put_chains_df.symbol.str.startswith("SPXW_"))]
        print(f'Change buy put price to {strike_price}')
    if bp_df.shape[0] == 0:
        raise ValueError(">> Can't find buy put chain")
    return sp_df.to_dict('records')[0], bp_df.to_dict('records')[0]


def main():
    # Get option daysToExpiration
    today = datetime.today()
    weekly = today.weekday() + 1
    if weekly in [2, 3, 4, 5]:
        dte = 1
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

    # Get latest put option chain
    r = c.get_option_chain(symbol="$SPX.X", contract_type=c.Options.ContractType.PUT, to_date=date.today() + timedelta(days=dte))
    chains = r.json()
    put_chains_df = pd.json_normalize(chains["putExpDateMap"])
    put_chains_df = [pd.json_normalize(put_chains_df[c].explode()) for c in put_chains_df.columns]
    put_chains_df = pd.concat(put_chains_df).reset_index()
    put_chains_df.delta = put_chains_df.delta.astype(float)

    # Get sell put spread chains
    underlyingPrice = chains["underlyingPrice"]
    sp, bp = get_sell_put_spread_chains(underlyingPrice, put_chains_df, dte)

    # Send order
    description = " ".join(sp["description"].split(" ")[0:4])
    mid_net = round(((sp["bid"] + sp["ask"]) - (bp["bid"] + bp["ask"])) / 2 // 0.05 * 0.05, 2)
    net = mid_net + 0.1   # add 0.1 by test..
    print(f'SPX index price: {underlyingPrice}')
    print(f'{description} {sp["strikePrice"]:.0f}/{bp["strikePrice"]:.0f} sell put spread ${net*QUANITY*100:,.0f}')
    if PLACE_ORDER:
        r = c.place_order(
            secretsTDA.account_id,
            bull_put_vertical_open(bp["symbol"], sp["symbol"], QUANITY, net).build()
        )
        r.raise_for_status()
        if r.status_code in [200, 201]:
            order_id = Utils(c, secretsTDA.account_id).extract_order_id(r)
            print(f'Send order succeed: {order_id}')
        else:
            print(f'Send order failed: {r.status_code}')
    print('-' * 50)


if __name__ == "__main__":
    PLACE_ORDER = True
    QUANITY = 2
    main()