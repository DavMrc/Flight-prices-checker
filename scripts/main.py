import streamlit as st
import logging
from interface import FlightPricesChecker
from controller import FlightsController


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


if __name__ == "__main__":
    if "controller" not in st.session_state:
        st.session_state["controller"] = FlightsController()
    
    if "interface" not in st.session_state:
        st.session_state["interface"] = FlightPricesChecker()

    app: FlightPricesChecker = st.session_state["interface"]
    app.run()
