import logging
import traceback
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
        st.session_state["controller"] = controller
    
    if "interface" not in st.session_state:
        st.session_state["interface"] = FlightPricesChecker()

    app: FlightPricesChecker = st.session_state["interface"]
    try:
        app.run()
    except Exception as e:
        st.error("An error occurred while running the app.")
        t = traceback.format_exception(e)
        stack_trace = "".join(t)
        logging.error(f"An error occurred:\n{stack_trace}")
