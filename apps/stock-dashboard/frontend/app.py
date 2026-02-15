# frontend/app.py
from shiny import App, render, ui, reactive
from shiny.ui import HTML
import requests
import pandas as pd
import plotly.graph_objects as go
import logging
import os

logger = logging.getLogger(__name__)

# Backend API URL
API_URL = os.getenv("BACKEND_URL", "http://backend:5000")

TICKERS = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMD"]

# Define UI
app_ui = ui.page_fluid(
    ui.h1("Stock Market Dashboard"),
    ui.row(
        ui.column(3, 
                  ui.input_selectize("ticker",
                                     "Select Ticker",
                                     choices=TICKERS,
                                     selected=TICKERS[0]
                    ),
                    ui.input_action_button("fetch_btn", "Fetch Data",
                                           class_="btn-primary btn-block")
        ),
        ui.column(9,
                  ui.output_text("status")
        )
    ),
    ui.row(
        ui.column(12,
                  ui.output_ui("chart")
        )
    ),
    ui.row(
        ui.column(12,
                  ui.output_table("data_table")
        )
    )
)

def server(input, output, session):
    """Server logic"""

    status_message = reactive.Value("")
    chart_data = reactive.Value(None)

    @reactive.Effect
    @reactive.event(input.fetch_btn)
    def fetch_data():
        """Fetch stock data on button click"""
        ticker = input.ticker()

        try:
            status_message.set(f"Fetching {ticker}...")

            # Fetch from backend
            response = requests.get(f"{API_URL}/api/fetch/{ticker}")
            if response.status_code == 200:
                result = response.json()
                status_message.set(
                    f"    {ticker}: {result['rows_imported']} rows imported"
                    f"({result['date_range']})"
                )
            else:
                status_message.set(f"    Error: {response.json()['error']}")
        
        except Exception as e:
            status_message.set(f"    Error: {str(e)}")

    @render.ui
    def chart():
        """Render candlestick + Bollinger Bands + SMAs"""
        ticker = input.ticker()

        try:
            response = requests.get(f"{API_URL}/api/indicators/{ticker}")
            if response.status_code != 200:
                return None
            
            data = response.json()["data"]
            df = pd.DataFrame(data)
            df["time"] = pd.to_datetime(df["time"])

            # Create candlestick chart
            fig = go.Figure()

            # Candlesticks
            fig.add_trace(go.Candlestick(
                x=df["time"],
                open = df.get("open", df["close"]),
                high = df.get("high", df["close"]),
                low = df.get("low", df["close"]),
                close=df["close"],
                name="Price"
            ))

            # Bollinger Bands
            fig.add_trace(go.Scatter(
                x = df["time"], y = df["bb_upper"],
                fill = None,
                mode = "lines",
                line_color = "rgba(0,0,0,0)",
                name = "BB Upper"
            ))

            fig.add_trace(go.Scatter(
                x = df["time"], y = df["bb_lower"],
                fill = "tonexty",
                mode = "lines",
                line_color = "rgba(0,0,0,0)",
                name = "BB Lower",
                fillcolor="rgba(0,100,255,0.2)"
            ))

            # SMAs
            fig.add_trace(go.Scatter(
                x = df["time"], y = df["sma_20"],
                name = "SMA 20",
                line = dict(color = "orange", width = 1)
            ))

            fig.add_trace(go.Scatter(
                x = df["time"], y = df["sma_50"],
                name = "SMA 50",
                line = dict(color = "blue", width = 1)
            ))

            fig.add_trace(go.Scatter(
                x = df["time"], y = df["sma_100"],
                name = "SMA 100",
                line = dict(color = "green", width = 1)
            ))

            fig.update_layout(
                title=f"{ticker} - Bollinger Bands & Moving Averages ({len(df)} days)",
                yaxis_title="Price (USD)",
                xaxis_title="Date",
                template="plotly_dark",
                height=600,
                hovermode="x unified",
                xaxis_rangeslider_visible=False,
                # IMPORTANT: Force x-axis to show all data
                xaxis=dict(
                    range=[df["time"].min(), df["time"].max()],  # Show full range
                    type='date',
                    rangeslider=dict(visible=True)
                )
            )

            return HTML(fig.to_html(include_plotlyjs='cdn', div_id=f'chart-{ticker}'))

        except Exception as e:
            logger.error(f"Chart error: {e}")
            return None
        
    @render.table
    def data_table():
        """Render data table"""
        ticker = input.ticker()

        try:
            response = requests.get(f"{API_URL}/api/indicators/{ticker}")

            if response.status_code != 200:
                return pd.DataFrame()
            
            data = response.json()["data"]
            df = pd.DataFrame(data)

            # Format Columns
            cols = ["time", "close", "sma_20", "sma_50", "sma_100",
                    "bb_upper", "bb_lower"]
            display_df = df[cols].tail(20).copy()

            # Round to 2 decimals
            for col in cols[1:]:
                if col in display_df.columns:
                    display_df[col] = display_df[col].round(2)
            
            return display_df
        
        except Exception as e:
            logger.error(f"Table error: {e}")
            return pd.DataFrame()
    
    @render.text
    def status():
        return status_message()
    
# Create app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")