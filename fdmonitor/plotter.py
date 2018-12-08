import argparse
import numpy as np
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc
import matplotlib.ticker as ticker
from matplotlib.backends.backend_pdf import PdfPages
import sys
sys.path.append('/code')
from fdmonitor.cont_futures import create_continuous_future, get_cme_data


def plot_data(df, ax, fmt):
    """Plot datframe on axis"""

    ax.patch.set(facecolor='w', edgecolor='k', linewidth=1.0)
    df['timestamp'] = df.index.to_pydatetime()
    df['ema'] = df['Close'].ewm(span=20, min_periods=20).mean()
    df = df[-80:]
    df = df.reset_index(drop=True)
    df['x'] = df.index

    subset = df[['x' ,'Open' ,'High' ,'Low' ,'Close']]
    tuples = [tuple(x) for x in subset.values]
    _ = candlestick_ohlc(ax, tuples, width=.5, colorup='g', colordown='r', alpha=1)
    _ = ax.plot(df['x'].tolist(), df['ema'].tolist(), color='blue', lw=0.5)

    def formatter(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, len(df.index) - 1)
        return df['timestamp'][thisind].strftime(fmt)

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(formatter))
    xticklabels = df['x'].iloc[::11].tolist()
    ax.xaxis.set_major_locator(ticker.FixedLocator(xticklabels))

    for line in ax.xaxis.get_ticklines():
        line.set_markersize(5)
    for line in ax.yaxis.get_ticklines():
        line.set_markersize(5)
    for line in ax.yaxis.get_gridlines():
        line.set(color='gray', ls='dotted', alpha=0.5)


def draw_charts(data, plot_title, pdf_pages=None):
    """Draw all charts on page"""

    fig = plt.figure(figsize=(16, 12))
    ax_daily = plt.subplot2grid((12, 16), (0, 0), colspan=16, rowspan=7)
    ax_weekly = plt.subplot2grid((12, 16), (7, 0), colspan=8, rowspan=5)
    ax_monthly = plt.subplot2grid((12, 16), (7, 8), colspan=8, rowspan=5)

    ax_daily.set_title(plot_title, fontsize=20)

    plot_data(data, ax_daily, '%b %-d')
    df_weekly = data.resample('W').agg({
        'Open': 'first',
        'High': max,
        'Low': min,
        'Close': 'last',
        'Volume': sum,
        'Open Interest': 'last'
    })
    plot_data(df_weekly, ax_weekly, "%b %y'")
    df_monthly = data.resample('M').agg({
        'Open': 'first',
        'High': max,
        'Low': min,
        'Close': 'last',
        'Volume': sum,
        'Open Interest': 'last'
    })
    plot_data(df_monthly, ax_monthly, '%b %Y')

    plt.tight_layout(pad=2.5)

    if pdf_pages:
        pdf_pages.savefig(fig)
    else:
        plt.show()


    plt.close(fig)


def create_combined_pdf(cme_futures, cme_metadata, use_s3=False):
    """
    Create one pdf for all contracts --> open interest roll,
    non backadjusted
    """

    today = date.today().isoformat()
    pdf_pages = PdfPages(f'/code/pdfs/{today}.pdf')
    futures_symbols = cme_futures.index.tolist()
    for futures_symbol in futures_symbols:
        futures_name, CME_months, CME_years = get_cme_data(futures_symbol,
                                                       cme_futures, cme_metadata)
        data = create_continuous_future(futures_symbol, CME_months, CME_years,
                                        'open_interest', is_backadjusted=False,
                                        use_s3=use_s3)
        date_string = data.index[-1].strftime('%m/%-d/%y')
        plot_title = f'{futures_name} ({futures_symbol})\n{date_string}\nRoll: open_interest'
        draw_charts(data, plot_title, pdf_pages)
    pdf_pages.close()


if __name__== "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--s3",
        default=False,
        dest='s3',
        action='store_true',
        help="Use futures data stored in S3"
    )
    args = parser.parse_args()

    cme_metadata = pd.read_csv('/code/data/CME_metadata.csv')
    cme_futures = pd.read_csv('/code/data/CME_futures.csv')
    cme_futures.set_index('Futures Symbol', inplace=True)
    print("Creating PDF")
    create_combined_pdf(cme_futures, cme_metadata, args.s3)
    print("PDF Creation Finished")