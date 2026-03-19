import logging
import traceback
import streamlit as st
import pandas as pd
import altair as alt
from interface import FlightPricesChecker


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


if __name__ == "__main__":
    pd.options.mode.copy_on_write = True
    alt.theme.enable("powerbi")

    app = FlightPricesChecker.init()
    try:
        app.run()
    except Exception as e:
        t = traceback.format_exception(e)
        stack_trace = "".join(t)
        logging.error(f"An error occurred:\n{stack_trace}")

        # Display error in the app
        st.error("An error occurred while running the app.")
        with st.expander("Details"):
            st.code(stack_trace)
