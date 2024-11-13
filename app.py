import streamlit as st
import websockets
import asyncio
import json

# WebSocket URI for Binance Futures
BINANCE_WS_URI = "wss://fstream.binance.com/ws/!miniTicker@arr"

# Function to fetch data from WebSocket
async def get_binance_futures_data():
    try:
        async with websockets.connect(BINANCE_WS_URI) as websocket:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                yield data  # Async generator yielding data
    except Exception as e:
        print(f"Error: {e}")
        await asyncio.sleep(5)  # Retry after 5 seconds

# Streamlit UI
st.title("Vadeli Coinler Streamlit Uygulaması")

# Display the live data from WebSocket
st.subheader("Vadeli Coin Verisi")

# Set up a container to display the data
container = st.empty()

# Function to display futures data in Streamlit
async def display_futures_data():
    async for data in get_binance_futures_data():
        container.json(data)  # Display the live data as JSON
        await asyncio.sleep(1)  # Pause briefly before next update

# Run the async WebSocket task
def run_display():
    asyncio.run(display_futures_data())  # Run the async function

# Run the display function
if __name__ == "__main__":
    run_display()
