import logging
import streamlit as st
import pandas as pd
import altair as alt
from interface import FlightPricesChecker
from controller import FlightsController


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


if __name__ == "__main__":
    pd.options.mode.copy_on_write = True
    alt.theme.enable("powerbi")

    if "controller" not in st.session_state:
        controller = FlightsController()
        controller.authenticate_endpoints_with_threads()
        st.session_state["controller"] = controller
    
    if "interface" not in st.session_state:
        st.session_state["interface"] = FlightPricesChecker()

    app: FlightPricesChecker = st.session_state["interface"]
    app.run()
