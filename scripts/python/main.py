# Caveat to avoid Streamlit useless warns about caching
import sys

class FilteredStderr:
    def __init__(self, original):
        self.original = original

    def write(self, text):
        # Filter out this Streamlit warning message
        if "No runtime found, using MemoryCacheStorageManager" not in text:
            self.original.write(text)

    def flush(self):
        self.original.flush()

sys.stderr = FilteredStderr(sys.stderr)

# Begin script
import logging
import traceback
import streamlit as st
import pandas as pd
import altair as alt
from interface import FlightPricesChecker


if __name__ == "__main__":
    pd.options.mode.copy_on_write = True
    alt.theme.enable("powerbi")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    app: FlightPricesChecker = FlightPricesChecker.init()
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
