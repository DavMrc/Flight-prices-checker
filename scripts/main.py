import logging
import os
import traceback
import pathlib
import streamlit as st
import pandas as pd
import altair as alt
from interface import FlightPricesChecker
from controller import FlightsController, DatabaseController


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


if __name__ == "__main__":
    pd.options.mode.copy_on_write = True
    alt.theme.enable("powerbi")

    # Set GCP auth credential
    CURR_PATH = pathlib.Path(__file__)
    PRJ_ROOT = CURR_PATH.parent.parent
    credential_path = PRJ_ROOT / "data/auth_files/cloud_functions.json"
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path.resolve().as_posix()

    if "controller" not in st.session_state:
        controller = FlightsController()
        controller.authenticate_endpoints_with_threads()
        st.session_state["controller"] = controller
    
    if "interface" not in st.session_state:
        st.session_state["interface"] = FlightPricesChecker()

    app: FlightPricesChecker = st.session_state["interface"]
    try:
        app.run()
    except Exception as e:
        st.error("An error occurred while running the app.")
        logging.error(f"An error occurred: {e}")
        l = traceback.format_exception(e)
        stack_trace = "".join(l)

        db_controller = DatabaseController()
        session_dump = db_controller.dump_session_state()
        db_controller.insert_error(str(e), stack_trace, session_dump)
