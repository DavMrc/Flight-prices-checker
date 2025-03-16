import streamlit as st
import plotly.express as px
import datetime
from controller import FlightsController


class FlightPricesChecker:
    def __init__(self, controller: FlightsController):
        self.controller = controller

        self.iata_codes = self.controller.get_iata_codes_list()
        self.airports = self.controller.get_airports_tuples_list()
        self.airport_tuples = self.controller.get_airports_tuples_list()

        st.session_state["navigated"] = False
        st.session_state["_search_by"] = "iata code"
    
    def run(self):
        self.__home_pg = st.Page(self.home, title="Home")
        self.__flights_pg = st.Page(self.flights, title="Flights")

        nav = st.navigation(
            [self.__home_pg, self.__flights_pg],
            position="hidden"
        )
        nav.run()

    def __keep(self, key):
        # https://stackoverflow.com/a/76211845
        if key in ["dep_airport", "arr_airport"]:
            st.session_state[key] = st.session_state['_'+key][0]
        else:
            st.session_state[key] = st.session_state['_'+key]

    def __airport_tuple_ix(self, airport_tuple):
        if "search_by" in st.session_state:
            if st.session_state["search_by"] == "iata code":
                return airport_tuple[0]
            else:
                return airport_tuple[1]
        else:
            return airport_tuple[0]

    def home(self):
        st.set_page_config(layout="centered")
        # Title of the app
        st.title("Flight Prices Checker")

        # Dropdown to select between "iata code" and "airport name"
        search_by = st.radio("Search by", ["iata code", "airport name"], horizontal=True, key="_search_by",
                             on_change=self.__keep, args=["search_by"])

        if "search_by" in st.session_state:
            search_by = st.session_state["search_by"]

        # Airport selectboxes side by side
        col1, col2 = st.columns(2)
        with col1:
            ix = 0
            if "dep_airport" in st.session_state:
                ix = self.iata_codes.index(st.session_state["dep_airport"])

            st.selectbox("Departure", options=self.airport_tuples, key="_dep_airport", index=ix,
                         format_func=self.__airport_tuple_ix,
                         on_change=self.__keep, args=["dep_airport"])
        with col2:
            ix = 0
            if "arr_airport" in st.session_state:
                ix = self.iata_codes.index(st.session_state["arr_airport"])

            st.selectbox("Arrival", options=self.airport_tuples, key="_arr_airport", index=ix,
                         format_func=self.__airport_tuple_ix,
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
            if "days_range" in st.session_state and st.session_state["navigated"] is True:
                min_value, max_value = st.session_state["days_range"]
            else:
                min_value = 0
                start_date, end_date = st.session_state["_date_range"]
                max_value = (end_date - start_date).days
                max_value = max(max_value, 30)

            st.slider("Select range of days", 0, 30, (min_value, max_value), key="_days_range",
                      on_change=self.__keep, args=["days_range"])
        except ValueError:
            st.warning("Please select both start and end dates.")
        
        if search_by == "airport name":
            # Convert airport names to iata codes
            airport_pairings = self.controller.get_airports_json(key="name")

            if ["dep_airport", "arr_airport"] in st.session_state:
                st.session_state["dep_airport"] = airport_pairings[st.session_state["dep_airport"]]
                st.session_state["arr_airport"] = airport_pairings[st.session_state["arr_airport"]]

        st.page_link(self.__flights_pg, label="Search Flights", icon="🔍")
        st.session_state["navigated"] = False

    def flights(self):
        # # Advanced filters for maxPrice and maxDuration
        # with st.expander("Advanced filters"):
        #     self.max_price = st.number_input("Max Price", min_value=0, value=0)
        #     self.max_duration = st.number_input("Max Duration", min_value=0, value=0)
        st.set_page_config(layout="wide")

        st.session_state["navigated"] = True
        st.page_link(self.__home_pg, icon="⬅", label="Back")

        start_date, end_date = st.session_state["date_range"]
        min_days, max_days = st.session_state["days_range"]
        params = {
            "departureAirport" : st.session_state["dep_airport"],
            "destinationAirport" : st.session_state["arr_airport"],
            "startDate" : start_date.strftime("%Y-%m-%d"),
            "returnDate" : end_date.strftime("%Y-%m-%d"),
            "minDays" : min_days,
            "maxDays" : max_days,
            "maxPrice": 0,      # st.session_state["max_price"],
            "maxDuration": 0,   # st.session_state["max_duration"],
        }

        print(params)

        col1, col2 = st.columns([0.2, 0.8])
        with col1:
            st.write(st.session_state)

        with col2:
        # st.write(price_graph_df)
            with st.spinner("Loading alternatives...", show_time=True):
                price_graph_df = self.controller.get_price_graph(params)

                fig = px.timeline(
                    price_graph_df,
                    x_start="startDate",
                    x_end="returnDate",
                    y=price_graph_df.index,
                    color="Price",
                    range_x=[price_graph_df['startDate'].min(), price_graph_df['returnDate'].max()],
                    range_y=[price_graph_df.index.min(), price_graph_df.index.max()],
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
                    # height=None  # Adjust the height automatically based on the content
                )
                st.plotly_chart(fig, use_container_width=True)
