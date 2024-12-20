import yfinance as yf
import pandas as pd
import hvplot.pandas
import panel as pn
import param

#####-----INITIALIZATION OF VARIABLES AND WIDGETS CREATION-----#################################################################################################################################

# enable the panel extension--> allows to work with widgets 
pn.extension('tabulator') # for interactive data tables

# global variables
ticker_symbol:str = ''

# ETF input and fetch button 
etf_input = pn.widgets.TextInput(name="ETF NAME", placeholder="Enter ETF symbol here:")
fetch_data_button = pn.widgets.Button(name="🔍 Fetch Data", button_type="success", width=300)

# Display panes (1st tab)
spread_volume_pane = pn.pane.Markdown("### Spread and Volume\n\nEnter an ETF and click Fetch Data to see updates.",
    styles={"background-color": "#e0e0e0", "padding": "10px",
            "border": "1px solid #c0c0c0", "border-radius": "5px",
            "font-size": "16px"}, 
    width=600,
    height=350
)

replication_pane = pn.pane.Markdown("### ETF overview:",
    styles={"background-color": "#e0e0e0", "padding": "10px",
            "border": "1px solid #c0c0c0", "border-radius": "5px",
            "font-size": "16px"}, 
    width=600, 
    height=350
)

news_pane = pn.pane.Markdown("### News\n\nEnter an ETF and click Fetch Data to see updates.",
    styles={"background-color": "#e0e0e0", "padding": "10px",
            "border": "1px solid #c0c0c0", "border-radius": "5px",
            "font-size": "16px"}, 
    width=1220,
    height=500
)

# Widgets for interactive plots (2nd tab)
wd_plot1_Top = pn.widgets.IntSlider(name='Value Threshold (# companies)', start=1, end=20, value=10)
wd_plot2_Top = pn.widgets.IntSlider(name='Value Threshold (# sectors)', start=1, end=11, value=10)
years_input = pn.widgets.IntInput(name='Years', value=5, step=1, start=1)

# Placeholder panes for interactive plots (2nd tab)--> used to update and clear when inserting new ETF
p1_interactive = pn.Column()
p2_interactive = pn.Column()
linked_data = pn.Column()
linked_data_2 = pn.Column()

#####-----FUNCTIONS-----#########################################################################################################################################

# function to fetch news (Tab 1)
def get_news(ticker_symbol):
    '''given a ticker as input it returns a dictionary (5 news) of dictionaries (keys: title, publisher, link), if no error occurs'''
    try:
        ticker = yf.Ticker(ticker_symbol)
        news = ticker.get_news()[:5]
        news_dict = {
            i + 1: {
                "title": item.get("title", "No title"),
                "publisher": item.get("publisher", "No publisher"),
                "link": item.get("link", "No link"),
            }
            for i, item in enumerate(news)
        }
        return news_dict
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Function to fetch spread and volume (Tab 1)
def get_spread_and_volume(ticker_symbol):
    '''given a ticker as input it returns a dictionary with info about bid, ask, spread, currency, volume, if no error occurs'''
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        # calculate bid-ask spread
        bid = info.get('bid', None)
        ask = info.get('ask', None)
        currency = info.get('currency', "Unknown")

        if bid is not None and ask is not None:
            spread = ask - bid
        else:
            spread = "N/A"

        # fetching historical data for volume
        hist = ticker.history(period="1d")
        volume = hist['Volume'].iloc[-1] if not hist.empty else "N/A"

        return {
            "bid": bid,
            "ask": ask,
            "spread": round(spread, ndigits=3) if spread != "N/A" else spread,
            "currency": currency,
            "volume": f'{volume:,}'
        }
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Callback to update panes and plots (Tab 1)
def update_panes(event):
    '''Updates the dashboard with the new ETF data'''
    global ticker_symbol
    ticker_symbol = etf_input.value.strip().upper()
    if not ticker_symbol:
        
        # Displaying error messages
        news_pane.object = "### News\n\nPlease enter a valid ETF symbol!"
        spread_volume_pane.object = "### Spread and Volume\n\nPlease enter a valid ETF symbol!"
        replication_pane.object = '### ETF overview:\n\nPlease enter a valid ETF symbol!'

        # Clearing interactive plots
        p1_interactive.clear()
        p2_interactive.clear()
        linked_data.clear()
        linked_data_2.clear()

        # Clearing benchmarking tab outputs
        ticker_param.ticker_symbol = ''
        return

    # Update replication pane
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        etf_name = info.get('longName') or info.get('shortName') or ticker_symbol

        # Get current price
        hist = ticker.history(period='1d')
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
        else:
            current_price = 'N/A'

        # Fetch additional ETF information
        net_assets = info.get('totalAssets', 'N/A')
        ytd_return = info.get('ytdReturn', 'N/A')
        etf_yield = info.get('yield', 'N/A')
        replication = info.get('longBusinessSummary')

        # Format net assets and returns if available
        if net_assets != 'N/A':
            net_assets = f"{net_assets/1e9:.2f}B"  # Convert to billions
        if ytd_return != 'N/A':
            ytd_return = f"{ytd_return*100:.2f}%"
        if etf_yield != 'N/A':
            etf_yield = f"{etf_yield*100:.2f}%"

        replication_pane.object = (
            f"### ETF Overview:\n\n"
            f"- **ETF Name**: {etf_name}\n"
            f"- **Current Price**: $ {current_price:.2f}\n"
            f"- **Net Assets**: $ {net_assets}\n"
            f"- **YTD Daily Total Return**: {ytd_return}\n"
            f"- **Yield**: {etf_yield}\n"
            f"- **Replication**: {replication}\n"
        )
    except Exception as e:
        replication_pane.object = f"### ETF Overview:\n\nError: {str(e)}"

    # Update spread and volume pane
    spread_volume_data = get_spread_and_volume(ticker_symbol)
    if "error" in spread_volume_data:
        spread_volume_pane.object = f"### Spread and Volume\n\nError: {spread_volume_data['error']}"
    else:
        spread_volume_content = (
            f"### Spread and Volume\n\n"
            f"- **Bid**: {spread_volume_data['bid']}\n"
            f"- **Ask**: {spread_volume_data['ask']}\n"
            f"- **Spread**: {spread_volume_data['spread']}\n"
            f"- **Currency**: {spread_volume_data['currency']}\n"
            f"- **Daily Volume**: {spread_volume_data['volume']}\n"
        )
        spread_volume_pane.object = spread_volume_content

    # Update news pane
    news_dict = get_news(ticker_symbol)
    if "error" in news_dict:
        news_pane.object = f"### News\n\nError: {news_dict['error']}"
    else:
        news_content = "### News\n\n"
        for idx, news in news_dict.items():
            news_content += f"- **{news['title']}**\n  *{news['publisher']}*\n  [Read more]({news['link']})\n\n"
        news_pane.object = news_content

    # Update interactive plots
    update_plots()
    
    # Update benchmarking tab
    ticker_param.ticker_symbol = ticker_symbol  # Update the parameter to trigger updates

# Function to update plots in (Tab 2)
def update_plots():
    '''Updates plots that depend on the ticker symbol'''
    p1_interactive.clear()
    p2_interactive.clear()
    linked_data.clear()
    linked_data_2.clear()

    # Fetch data for plots
    ticker = yf.Ticker(ticker_symbol)
    try:
        data_2 = ticker.funds_data
    except Exception as e:
        data_2 = None

    try:
        prices = ticker.history(period="max")
    except Exception as e:
        prices = None

    # Function to create a bar chart for top companies
    def p1_Companies_weight(threshold):
        try:
            Companies_weig = data_2.top_holdings.reset_index().sort_values(by="Holding Percent", ascending=False)
            Companies_weig["Position"] = [i + 1 for i in range(len(Companies_weig["Symbol"]))]

            # Filter data based on the threshold
            filtered_data = Companies_weig[Companies_weig["Position"] <= threshold]
            sum_weights = filtered_data['Holding Percent'].sum()

            # Create the bar chart
            plot = filtered_data.hvplot.bar(
                x='Symbol', y='Holding Percent', color='skyblue',
                title=f'The Top {threshold} Companies represent {sum_weights:.2%}',
                rot=90, ylabel="Weight (%)"
            )
            return plot
        except Exception as e:
            return pn.pane.Markdown(f"### Error\n\nUnable to fetch data for {ticker_symbol}.")

    # Function to create a bar chart for sector weights
    def p2_Sector_weight(threshold):
        try:
            # Create a DataFrame for sector weights
            sect_we = pd.DataFrame({
                "Sector": list(data_2.sector_weightings.keys()),
                "Sector_weight": list(data_2.sector_weightings.values())
            }).sort_values(by=["Sector_weight"], ascending=False)
            sect_we["Position"] = [i + 1 for i in range(len(sect_we["Sector"]))]

            # Filter data based on the threshold
            filtered_data = sect_we[sect_we['Position'] <= threshold]
            sum_weights = filtered_data['Sector_weight'].sum()

            # Create the bar chart
            plot = filtered_data.hvplot.bar(
                x='Sector', y='Sector_weight', color='skyblue',
                title=f"Top {threshold} sectors representing {sum_weights:.2%} of portfolio",
                ylabel="Weight (%)"
            )
            return plot
        except Exception as e:
            return pn.pane.Markdown(f"### Error\n\nUnable to fetch data for {ticker_symbol}.")

    # Function to plot historical returns
    def returns_plot(years):
        try:
            days = years * 252
            prices[f"{years} Year Close Price Change"] = prices["Close"].pct_change(periods=days)
            returns_data = prices[f"{years} Year Close Price Change"].dropna()
            plot = returns_data.hvplot(
                kind="line", colorbar=False, width=600,
                title=f"{years}-Year Rolling Returns for {ticker_symbol}"
            )
            return plot
        except Exception as e:
            return pn.pane.Markdown(f"### Error\n\nUnable to fetch data for {ticker_symbol}.")

    # Function to calculate mean and standard deviation
    def mean_std(years):
        try:
            days = years * 252
            prices[f"{years} Year Close Price Change"] = prices["Close"].pct_change(periods=days).dropna()
            mean_return = prices[f"{years} Year Close Price Change"].mean()
            std_dev = prices[f"{years} Year Close Price Change"].std()
            return pn.pane.Markdown(
                "### Key Statistics\n"
                f"**Mean Return:** {mean_return:.2%}\n**Standard Deviation:** {std_dev:.2%}"
            )
            # old--> f"### Key Statistics\n\**Mean Return:** {mean_return:.2%}\n**Standard Deviation:** {std_dev:.2%}"
        except Exception as e:
            return f"### Error\n\nUnable to fetch data for {ticker_symbol}."

    # Bind the functions to the widgets
    p1_plot = pn.bind(p1_Companies_weight, threshold=wd_plot1_Top)
    p2_plot = pn.bind(p2_Sector_weight, threshold=wd_plot2_Top)
    returns_plot_bind = pn.bind(returns_plot, years=years_input)
    mean_std_bind = pn.bind(mean_std, years=years_input)

    # Update the interactive plots
    p1_interactive.append(p1_plot)
    p2_interactive.append(p2_plot)
    linked_data.append(returns_plot_bind)
    linked_data_2.append(mean_std_bind)
    #linked_data_2.object = mean_std_bind

# link the fetch data button to the update function (Tab 2)
fetch_data_button.on_click(update_panes)

# widgets for benchmarking tab (Tab 3)
investment_years = pn.widgets.IntInput(name='Investment Duration (Years)', value=5, step=1, start=1)
investment_amount = pn.widgets.IntInput(name='Investment Amount', value=100, start=0)
investment_period = pn.widgets.Select(name='Frequency of Investment', options=["Yearly", "Monthly", "Quarterly"])
benchmark_select = pn.widgets.TextInput(name="Benchmark ETF NAME", placeholder="Enter the ETF symbol that will be used as benchmark:") 

# Using param for ticker symbol (Tab 3)
class TickerParam(param.Parameterized):
    ticker_symbol = param.String(default='')

ticker_param = TickerParam()

# Function to calculate future value (Tab 3)
def calculate_future_value(years, amount, period, ticker_param):
    ticker = ticker_param.ticker_symbol
    if not ticker:
        return "Please enter a valid ETF symbol and click Fetch Data."
    try:
        etf = yf.Ticker(ticker)
        prices = etf.history(period="max")
        if prices.empty:
            return f"Error: No price data available for {ticker}."
        days = years * 252
        prices[f"{years} Year Close Price Change"] = prices["Close"].pct_change(periods=days)
        max_return = prices[f"{years} Year Close Price Change"].max()
        annualised_return = max_return ** (252 / days) - 1

        periods_map = {"Yearly": 1, "Monthly": 12, "Quarterly": 4}
        n = periods_map[period]
        if annualised_return == 0:
            future_value = total_invested = amount * years * n
            total_return = 0
        else:
            future_value = amount * (((1 + annualised_return / n) ** (years * n) - 1) / (annualised_return / n))
            total_invested = amount * years * n
            total_return = future_value - total_invested

        #return f"Future Value: ${future_value:,.2f}\nAmount Invested: ${total_invested:,.2f}\nTotal Return: ${total_return:,.2f}"

        return pn.Column(
            pn.pane.Markdown(f"**Future Value: ${future_value:,.2f}**", styles={'border': '1px solid black', 'padding': '10px', 'border-radius': '5px'}, height=70, width=300, align=('center', 'center')), 
            pn.pane.Markdown(f"**Amount invested: ${total_invested:,.2f}**", styles={'border': '1px solid black', 'padding': '10px', 'border-radius': '5px'}, height=70, width=300, align=('center', 'center')),
            pn.pane.Markdown(f"**Total return: ${total_return:,.2f}**", styles={'border': '1px solid black', 'padding': '10px', 'border-radius': '5px'}, height=70, width=300, align=('center', 'center'))
            )

    except Exception as e:
        return f"Error: {str(e)}"

# Function to compare benchmarks (Tab 3)
def compare_benchmarks(years, benchmark, ticker_param):
    ticker = ticker_param.ticker_symbol
    if not ticker:
        return pn.pane.Markdown("### Error\n\nPlease enter a valid ETF symbol and click Fetch Data.")
    try:
        etf = yf.Ticker(ticker)
        etf_prices = etf.history(period="max")
        if etf_prices.empty:
            return pn.pane.Markdown(f"### Error\n\nNo price data available for {ticker}.")

        days = years * 252
        etf_prices[f"{years} Year Close Price Change"] = etf_prices["Close"].pct_change(periods=days)

        benchmark_ticker = yf.Ticker(benchmark)
        benchmark_prices = benchmark_ticker.history(period="max")
        if benchmark_prices.empty:
            return pn.pane.Markdown(f"### Error\n\nNo price data available for benchmark {benchmark}.")

        benchmark_prices[f"{years} Year Close Price Change"] = benchmark_prices["Close"].pct_change(periods=days)

        merged_prices = pd.merge(
            etf_prices[[f"{years} Year Close Price Change"]].reset_index(),
            benchmark_prices[[f"{years} Year Close Price Change"]].reset_index(),
            on="Date", how="inner"
        )
        merged_prices.rename(
            columns={
                f"{years} Year Close Price Change_x": ticker,
                f"{years} Year Close Price Change_y": benchmark
            },
            inplace=True
        )

        return merged_prices.hvplot.line(x="Date", y=[ticker, benchmark], height=500, width=1000, legend="bottom")
    except Exception as e:
        return pn.pane.Markdown(f"### Error\n\n{str(e)}")

# Create linked outputs (Tab 3)
investment_output = pn.bind(calculate_future_value, years=investment_years, amount=investment_amount, period=investment_period, ticker_param=ticker_param)
benchmark_comparison = pn.bind(compare_benchmarks, years=investment_years, benchmark=benchmark_select, ticker_param=ticker_param)

#####-----DASHBOARD DESIGN-----#################################################################################################################################

# Instruction text
side_text = pn.pane.Markdown(
    "### Tabs Information\n"
    "**Overview:** info overview on general ETF info\n"  
    "**Analysis:** companies, sectors, and returns\n"
    "**Benchmarking:** return comparison\n"
    "**PROVA:** testo di prova\n\n"
    "*ETFs examples: SPY, QQQ, VOO*\n"
    "*Possible benchmarks: Gold, URTH, SPY*\n",
    width=300,
    height=220,
    styles={
        'border': '1px solid #c0c0c0',
        'padding': '10px',
        'background-color': '#e0e0e0',
        'border-radius': '10px'
    }
)

# Sidebar layout
sidebar = pn.Column(
    pn.pane.Image('https://upload.wikimedia.org/wikipedia/de/thumb/7/77/Uni_St_Gallen_Logo.svg/2048px-Uni_St_Gallen_Logo.svg.png', width=150),
    pn.pane.Markdown("## ETF Selection and Filtering", styles={"font-weight": "bold"}),
    etf_input,
    fetch_data_button,
    side_text
)

# Tab 1 content (Overview)
top_row = pn.Row(replication_pane, spread_volume_pane)
bottom_row = pn.Row(news_pane)
tab1_content = pn.Column(
    top_row,
    bottom_row
)

# Tab 2 content (Analysis)
plot1 = pn.Column(
    "# Top Companies in the ETF",
    p1_interactive,
    wd_plot1_Top
)

plot2 = pn.Column(
    "# Top Sectors in the ETF",
    p2_interactive,
    wd_plot2_Top
)

stats_and_plot = pn.Row(
    pn.Column(
        years_input,
        linked_data_2
    ),
    linked_data
)

tab2_content = pn.Column(
    pn.Row(plot1, plot2),
    stats_and_plot
)

#Tab 3 content (benchmarking) 
middle_section = pn.Row(
    pn.Column(
        pn.pane.Markdown("### Inputs", margin=(0, 0, 10, 0)),
        investment_years, 
        investment_amount, 
        investment_period, 
        benchmark_select,
        styles={"background-color": "#e0e0e0", "padding": "10px", "border": "1px solid #c0c0c0", "border-radius": "5px", "font-size": "16px"}, 
        width=600,
        height=350
    ),   
    pn.Spacer(width=20),  # space between the two boxes
    pn.Column(
        pn.pane.Markdown("### Outputs", margin=(0, 0, 10, 0)),
        pn.panel(investment_output, width_policy="max"),
        styles={"background-color": "#e0e0e0", "padding": "10px", "border": "1px solid #c0c0c0", "border-radius": "5px", "font-size": "16px"}, 
        width=600,
        height=350
    ),
    align="start",
    height=400,
    margin=(10, 10, 0, 10)
)

tab3_content = pn.Column(
    pn.pane.Markdown("## Investment Growth and Benchmark Comparison", height=30, margin=(0, 0, 10, 0)),  
    middle_section,
    benchmark_comparison,  
)

# Tabs
tabs = pn.Tabs(
    ('Overview', tab1_content),
    ('Analysis', tab2_content),
    ('Benchmarking', tab3_content)
)

# Template design
template = pn.template.FastListTemplate(
    title="ETF Dashboard",
    sidebar=[sidebar],
    main=[tabs],
    theme_toggle=True,
)

# Changing the color for the header bar in the template
template.header_background = "green"

# Defining main to display dashboard
def main():
    template.show()

# If condition to avoid double calls
if __name__ == '__main__':
    main()
