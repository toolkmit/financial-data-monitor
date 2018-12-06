import numpy as np
import pandas as pd
import math as math


def get_roll_date(i, df_dict, contracts, roll_rule, start=np.datetime64('1900-01-01')):
    """
    Calculate roll date given a dataframe of individual futures contracts

    # Arguments
        df_dict: Nested dataframe of futures contract data
        contracts: List of futures contract names
        i: Index into contracts
        roll_rule: Rule for calculating roll date
            open_interest: Use contract with highest open interest
            exp_month: Roll on first day of expiration month
            expiration: Roll when contract expires
        start: Start date for Open Interest roll

    # Returns
        roll_date
    """

    cur_con = df_dict[contracts[i]]

    if roll_rule == 'open_interest':
        try:
            next_con = df_dict[contracts[i + 1]]
            sub = next_con.merge(cur_con, how='inner', left_index=True, right_index=True)
            sub = sub[sub.index.values > start]
            sub = sub[sub['Open Interest_x'] > sub['Open Interest_y']]
            if sub.empty:
                start = cur_con.index.values[len(cur_con) - 1]
            else:
                start = sub.index.values[0]
        except IndexError:
            return np.datetime64('1900-01-01')
    elif roll_rule == 'exp_month':
        starts = cur_con.index - pd.offsets.MonthBegin(1)
        start = starts.values[len(cur_con) - 1]
    else:
        start = cur_con.index.values[len(cur_con) - 1]

    return start


def create_continuous_future(futures_symbol, data_directory, CME_months, CME_years, roll_rule, is_backadjusted):
    df_dict = {}
    contracts = []
    roll_dates = []
    start = np.datetime64('1900-01-01')

    CONTRACT_DATA_DIRNAME = data_directory / 'raw_csv' / 'futures' / f'{futures_symbol}' / 'daily'

    for i in range(0, len(CME_months) * len(CME_years)):
        month = CME_months[i % len(CME_months)]
        year = CME_years[math.floor(i / len(CME_months))]
        contract = futures_symbol + month + str(year)
        contracts.append(contract)
        current_df = pd.read_csv(CONTRACT_DATA_DIRNAME / f'{futures_symbol}{month}{year}.csv')
        current_df.set_index('Date', inplace=True)
        current_df.index = pd.to_datetime(current_df.index)
        current_df['Close'] = np.where(current_df['Last'].isnull(), current_df['Settle'], current_df['Last'])
        current_df['Open Interest'] = current_df[current_df.columns[7]]
        current_df = current_df[['Open', 'High', 'Low', 'Close', 'Volume', 'Open Interest']]
        df_dict[contract] = current_df

        if i > 0:
            roll_date = get_roll_date(i - 1, df_dict, contracts, roll_rule, start)
            if start != roll_date:
                roll_dates.append(roll_date)
                start = roll_date
            else:
                del roll_dates[-1]
                break

    cont = df_dict[contracts[0]]
    start = roll_dates[0]
    switch_post = pd.DataFrame(columns=('Open', 'High', 'Low', 'Close', 'Volume', 'Open Interest'))
    switch_pre = pd.DataFrame(columns=('Open', 'High', 'Low', 'Close', 'Volume', 'Open Interest'))
    switch_pre = switch_pre.append(cont.iloc[cont.index.get_loc(start, method='bfill')])

    for i in range(1, len(roll_dates) + 1):
        cur = df_dict[contracts[i]]
        cur = cur[cur.index.values >= start]
        if len(cur.index) != 0:
            switch_post = switch_post.append(cur.iloc[0])
            cont = cont.append(cur)
            if i != len(roll_dates):
                start = roll_dates[i]
                switch_pre = switch_pre.append(cur.iloc[cur.index.get_loc(start, method='bfill')])

    switch_post['Change'] = switch_post['Close'].values - switch_pre['Close'].values
    switch_post = pd.DataFrame(switch_post['Change'])

    main = cont.merge(switch_post, how='left', left_index=True, right_index=True)
    main['Change'].fillna(0, inplace=True)
    main = main.reset_index().drop_duplicates(subset='index', keep='last').set_index('index')
    main['BAdj'] = main.loc[::-1, 'Change'].cumsum()[::-1]
    main['BAdj'] = main['BAdj'].shift(-1)
    main['BAdj'].fillna(0, inplace=True)

    if is_backadjusted:
        main['Open'] = main['Open'] + main['BAdj']
        main['High'] = main['High'] + main['BAdj']
        main['Low'] = main['Low'] + main['BAdj']
        main['Close'] = main['Close'] + main['BAdj']

    main.drop(columns=['Change', 'BAdj'], inplace=True)

    return main


def get_cme_data(futures_symbol, cme_futures, cme_metadata):
    futures_name = cme_futures.loc[futures_symbol, 'Name']
    month_codes = cme_futures.loc[futures_symbol, 'Priced Roll Cycle']
    last_month_code = month_codes[-1]

    length = (cme_metadata['code'].str.len() == len(futures_symbol) + 5)
    first_year = int(cme_futures.loc[futures_symbol, 'Start Year'])
    starts_with = cme_metadata['code'].str.startswith(futures_symbol + last_month_code)
    results = cme_metadata[length & starts_with]
    last_year = int(results.iloc[-1, 0][-4:])

    CME_months = month_codes
    CME_years = [i for i in range(first_year, last_year + 1)]

    return futures_name, CME_months, CME_years