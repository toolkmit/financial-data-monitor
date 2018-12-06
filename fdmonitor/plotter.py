import numpy as np
import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc
import matplotlib.ticker as ticker


def plot_data(df, ax, fmt):
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