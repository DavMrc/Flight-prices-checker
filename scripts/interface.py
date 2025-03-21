import streamlit as st
import plotly.express as px
import pandas as pd
import datetime
import logging
from controller import FlightsController


class FlightPricesChecker:
    def __init__(self):
        logging.info("Initializing FlightPricesChecker...")
        self.controller: FlightsController = st.session_state["controller"]

        self.airports_json = self.controller.get_airports_json()
        st.session_state["search_by"] = "iata code"
    
    def run(self):
        self.__home_pg = st.Page(self.home, title="Home")
        self.__flights_pg = st.Page(self.flights, title="Flights")

        nav = st.navigation(
            [
                self.__home_pg,
                self.__flights_pg
            ],
            position="hidden"
        )
        nav.run()

    def __keep(self, key):
        # https://stackoverflow.com/a/76211845
        st.session_state[key] = st.session_state['_'+key]

    def __airport_option_fmt(self, option):
        if st.session_state["search_by"] == "iata code":
            return option["iata_code"]
        else:
            return option["name"]

    def home(self):
        st.set_page_config(layout="centered")
        # Title of the app
        st.title("Flight Prices Checker")

        # Dropdown to select between "iata code" and "airport name"
        st.radio("Search by", ["iata code", "airport name"], horizontal=True, key="_search_by",
                 on_change=self.__keep, args=["search_by"])
        
        # Airport selectboxes side by side
        col1, col2 = st.columns(2)
        with col1:
            ix = 0
            if "dep_airport" in st.session_state:
                ix = st.session_state["dep_airport"]["index"]

            st.selectbox("Departure", options=self.airports_json, key="_dep_airport", index=ix,
                         format_func=self.__airport_option_fmt,
                         on_change=self.__keep, args=["dep_airport"])
        with col2:
            ix = 0
            if "arr_airport" in st.session_state:
                ix = st.session_state["arr_airport"]["index"]

            st.selectbox("Arrival", options=self.airports_json, key="_arr_airport", index=ix,
                         format_func=self.__airport_option_fmt,
                         on_change=self.__keep, args=["arr_airport"])

        # Date range input
        if "date_range" in st.session_state and len(st.session_state["date_range"]) == 2:
            min_date, max_date = st.session_state["date_range"]
        else:
            min_date = datetime.date.today()
            max_date = datetime.date.today() + datetime.timedelta(days=1)

        st.date_input("Select Date Range", value=(min_date, max_date), key="_date_range",
                      on_change=self.__keep, args=["date_range"])

        # Range slider for minDays and maxDays
        try:
            if "days_range" in st.session_state:
                min_days, max_days = st.session_state["days_range"]
            else:
                min_days = 0
                start_date, end_date = st.session_state["_date_range"]
                max_days = (end_date - start_date).days
                max_days = max(max_days, 1)

            st.slider("Select range of days", 0, max_days, (min_days, max_days), key="_days_range",
                      on_change=self.__keep, args=["days_range"])
        except ValueError:
            st.warning("Please select both start and end dates.")

        #  Navigate to next page
        st.page_link(self.__flights_pg, label="Search Flights", icon="🔍")

    def flights(self):
        st.set_page_config(layout="wide")

        st.page_link(self.__home_pg, icon="⬅", label="Back")

        start_date, end_date = st.session_state["date_range"]
        min_days, max_days = st.session_state["days_range"]
        params = {
            "departureAirport" : st.session_state["dep_airport"]["iata_code"],
            "destinationAirport" : st.session_state["arr_airport"]["iata_code"],
            "startDate" : start_date.strftime("%Y-%m-%d"),
            "returnDate" : end_date.strftime("%Y-%m-%d"),
            "minDays" : min_days,
            "maxDays" : max_days,
            "maxPrice": 0,      # st.session_state["max_price"],
            "maxDuration": 0,   # st.session_state["max_duration"],
        }

        col1, col2 = st.columns([0.2, 0.8])
        with col2:
            with st.spinner("Loading alternatives...", show_time=True):
                if "price_graph_df" not in st.session_state:
                    price_graph_df = self.controller.get_price_graph(params)
                    st.session_state["price_graph_df"] = price_graph_df

                price_graph_df: pd.DataFrame = st.session_state["price_graph_df"]
                query_df = price_graph_df

                # Filter based on max price
                if "_max_price" in st.session_state:
                    max_price = st.session_state["_max_price"]
                    query_df = price_graph_df[price_graph_df["Price"] <= max_price]

                # Plot the chart
                fig = px.timeline(
                    query_df,
                    x_start="startDate",
                    x_end="returnDate",
                    y=query_df.index,
                    color="Price",
                    range_x=[query_df['startDate'].min(), query_df['returnDate'].max()],
                    range_y=[query_df.index.min(), query_df.index.max()],
                    color_continuous_scale=px.colors.sequential.speed
                )
                fig.update_yaxes(
                    autorange="reversed",
                    showticklabels=False,
                    title_text='',
                    fixedrange=True
                )
                fig.update_xaxes(
                    fixedrange=True,
                    tickangle=-90,
                    tickmode='array',
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='LightGray'
                )
                fig.update_layout(
                    bargap=0.2,
                    height=600,
                )
                st.plotly_chart(fig, use_container_width=True)

        with col1:
            # Display selected airports
            col1_sub, col2_sub = st.columns(2)
            with col1_sub:
                ix = st.session_state["dep_airport"]["index"]
                st.selectbox("Departure", options=self.airports_json, key="_dep_airport", index=ix,
                         format_func=self.__airport_option_fmt, disabled=True)

            with col2_sub:
                ix = st.session_state["arr_airport"]["index"]
                st.selectbox("Arrival", options=self.airports_json, key="_arr_airport", index=ix,
                         format_func=self.__airport_option_fmt, disabled=True)

            # Date range input
            min_date, max_date = st.session_state["date_range"]
            st.date_input("Select Date Range", value=(min_date, max_date), key="_date_range",
                      disabled=True)

            # Range slider for minDays and maxDays
            min_days, max_days = st.session_state["days_range"]
            st.slider("Select range of days", 0, 30, (min_days, max_days), key="_days_range",
                      disabled=True)

            # Initial max price
            max_price = price_graph_df["Price"].max()
            curr_price = max_price
            if "_max_price" in st.session_state:
                curr_price = st.session_state["_max_price"]

            st.slider("Max Price", min_value=0, max_value=max_price, value=curr_price, key="_max_price")

            # Max duration
            st.time_input("Max Duration", value=datetime.time(0, 0),
                            step=datetime.timedelta(minutes=30), key="_max_duration")
