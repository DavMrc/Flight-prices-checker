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

    def __keep(self, key):
        # https://stackoverflow.com/a/76211845
        st.session_state[key] = st.session_state['_'+key]

    def __airport_option_fmt(self, option):
        if st.session_state["search_by"] == "iata code":
            return option["iata_code"]
        else:
            return option["name"]

    def __fmt_duration(self, duration: datetime.timedelta) -> str:
        """
        Formats a `datetime.timedelta` object into a string of format `05 hrs 45 min`
        """
        hours, remainder = divmod(duration.total_seconds(), 60*60)
        minutes = remainder // 60
        return f"{int(hours):02} hrs {int(minutes):02} min"

    def __card_title_fmt(self, df: pd.DataFrame) -> str:
        dep_date_fmt = df["startDate"].iloc[0].strftime("%a %d %b")
        total_duration_fmt = self.__fmt_duration(df["arrivalTime"].iloc[-1] - df["departureTime"].iloc[0])
        layovers = len(df)-1
        price = df["price"].iloc[0].astype(str) +"€"

        return f'##### {dep_date_fmt} | {price}\n{total_duration_fmt} | {layovers} stops'

    def __full_offer_title_fmt(self, row: pd.DataFrame) -> str:
        dep_date_fmt = row.departureTime_Outbound.strftime("%a %d %b")
        ret_date_fmt = row.departureTime_Inbound.strftime("%a %d %b")
        price = str(row.fullPrice) +"€"

        return f'{dep_date_fmt} - {ret_date_fmt} | {price}'

    def _offer_card(self, df):
        rows = list(df.itertuples(index=False))
        nrows = len(rows)
        for i, row in enumerate(rows):
            # Departure
            dep_time = row.departureTime.strftime("%H:%M")
            dep_airport = row.departureAirport

            # Duration
            duration = datetime.timedelta(minutes=row.flightDuration)
            formatted_time = self.__fmt_duration(duration)

            # Arrival
            arr_time = row.arrivalTime.strftime("%H:%M")
            arr_airport = row.arrivalAirport
            divider = "---" if i != nrows-1 else ""

            st.markdown(f'''
                - **{dep_time}** · {dep_airport}
                    - <span style="font-size: smaller; font-weight: lighter;">Travel time: {formatted_time}</span>
                - **{arr_time}** · {arr_airport}
                {divider}
                ''',
                unsafe_allow_html=True
            )

            try:
                # Layover duration
                layover_duration = (rows[i+1].departureTime - row.arrivalTime).to_pytimedelta()
                formatted_time = self.__fmt_duration(layover_duration)

                st.markdown(f"- Layover: h{formatted_time} · {row.arrivalAirport}\n---")
            except IndexError:
                # flight combination has no (or no-more) layovers
                pass

    def _full_offer_expander(self, title: str, outdf: pd.DataFrame, indf: pd.DataFrame):
        with st.expander(title):
            col1, col2 = st.columns(2, border=True)

            with col1:
                subtitle = self.__card_title_fmt(outdf)
                st.markdown(subtitle)
                self._offer_card(outdf)
            with col2:
                subtitle = self.__card_title_fmt(indf)
                st.markdown(subtitle)
                self._offer_card(indf)

    def run(self):
        self.__home_pg = st.Page(self.home, title="Home")
        self.__flights_pg = st.Page(self.flights, title="Flights")
        self.__offers_pg = st.Page(self.offers, title="Offers")

        nav = st.navigation(
            [
                # self.__home_pg,
                # self.__flights_pg,
                self.__offers_pg
            ],
            position="hidden"
        )
        nav.run()

    def home(self):
        st.set_page_config(layout="centered")
        # Title of the app
        st.title("Flight Prices Checker")

        # Dropdown to select between "iata code" and "airport name"
        if "search_by" not in st.session_state:
            st.session_state["search_by"] = "iata code"

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
            min_days = 0
            start_date, end_date = st.session_state["_date_range"]
            max_days = (end_date - start_date).days
            max_days = max(max_days, 1)

            st.slider("Select range of days", 0, max_days, (min_days, max_days), key="_days_range",
                      on_change=self.__keep, args=["days_range"])
        except ValueError:
            st.warning("Please select both start and end dates.")

        #  Navigate to next page
        # TODO: align right
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
            "maxDays" : max_days
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
                fig = px.timeline(query_df, x_start="startDate", x_end="returnDate", y=query_df.index,
                    color="Price", color_continuous_scale=px.colors.sequential.speed,
                    range_x=[query_df['startDate'].min(), query_df['returnDate'].max()],
                    range_y=[query_df.index.min(), query_df.index.max()],
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
                    height=max(1000, len(query_df) * 10),
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

            st.slider("Max Price", min_value=0, max_value=max_price, value=curr_price,
                      key="_max_price", on_change=self.__keep, args=['max_price'])

        #  Navigate to next page        
        # TODO: align right
        if st.button(label="Search Offers", icon="🔍"):
            st.session_state["price_graph_df"] = query_df
            st.switch_page(self.__offers_pg)

    def offers(self):
        st.set_page_config(layout="wide")
        st.page_link(self.__flights_pg, icon="⬅", label="Back")

        # ------
        def convert_iso_dates(data):
            arr_keys = ["_date_range", "date_range"]
            
            new_arr = []
            for k in arr_keys:
                for v in data[k]:
                    date = datetime.date.fromisoformat(v)
                    new_arr.append(date)
                data[k] = new_arr
                new_arr = []
            
            return data

        import json
        j = json.load(open('F:/Programmazione/Flight prices checker/scripts/Untitled-1.json', 'rb'))
        j = convert_iso_dates(j)
        st.session_state.update(j)

        if "max_duration" not in st.session_state:
            st.session_state["max_duration"] = 0

        start_date, end_date = st.session_state["date_range"]
        min_days, max_days = st.session_state["days_range"]
        params = {
            "departureAirport" : st.session_state["dep_airport"]["iata_code"],
            "destinationAirport" : st.session_state["arr_airport"]["iata_code"],
            "startDate" : start_date.strftime("%Y-%m-%d"),
            "returnDate" : end_date.strftime("%Y-%m-%d"),
            "minDays" : min_days,
            "maxDays" : max_days,
            "maxPrice" : st.session_state["max_price"],
            "maxDuration": st.session_state["max_duration"]
        }
        if "price_graph_df" not in st.session_state:
            st.session_state["price_graph_df"] = self.controller.get_price_graph(params)

        # -----

        col1, col2 = st.columns([0.2, 0.8])
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
            max_price = st.session_state["max_price"]
            st.number_input("Max Price", value=max_price, key="_max_price", disabled=True)

        with col2:
            start_date, end_date = st.session_state["date_range"]
            min_days, max_days = st.session_state["days_range"]

            params = {
                "departureAirport" : st.session_state["dep_airport"]["iata_code"],
                "destinationAirport" : st.session_state["arr_airport"]["iata_code"],
                "startDate" : start_date.strftime("%Y-%m-%d"),
                "returnDate" : end_date.strftime("%Y-%m-%d"),
                "minDays" : min_days,
                "maxDays" : max_days,
                "maxPrice" : st.session_state["max_price"],
                "maxDuration": st.session_state["max_duration"]
            }

            if "merged_df" not in st.session_state:
                with st.spinner(show_time=True):
                    price_graph_df = st.session_state["price_graph_df"]
                    # outb_df = self.controller.get_offers(price_graph_df, params, trip_type=TripType.OUTBOUND)
                    # inb_df = self.controller.get_offers(price_graph_df, params, trip_type=TripType.INBOUND)
                    # merged_df = self.controller.merge_offers(outb_df, inb_df, params, filter=False)
                    
                    p = "F:/Programmazione/Flight prices checker/data/samples/"
                    outb_df = pd.read_pickle(p+'outb_df.pkl')
                    inb_df = pd.read_pickle(p+'inb_df.pkl')
                    merged_df = pd.read_pickle(p+'merged_df.pkl')

                    # outb_df.to_pickle(p+'outb_df.pkl')
                    # inb_df.to_pickle(p+'inb_df.pkl')
                    # merged_df.to_pickle(p+'merged_df.pkl')

                st.session_state["outb_df"] = outb_df
                st.session_state["inb_df"] = inb_df
                st.session_state["merged_df"] = merged_df
                st.session_state["absolute_max_duration"] = self.controller._concat_offers_duration(merged_df).max()

            outb_df: pd.DataFrame = st.session_state["outb_df"]
            inb_df: pd.DataFrame = st.session_state["inb_df"]
            merged_df_orig: pd.DataFrame = st.session_state["merged_df"]
            merged_df = self.controller.filter_merged_offers(merged_df_orig, params)

            # Filter df based on selection made on the barchart (see below)
            if "max_duration" in st.session_state:
                max_duration: int = st.session_state["max_duration"] * 60

                if max_duration and max_duration > 0:
                    merged_df = self.controller._filter_merged_df_on_max_duration(max_duration, merged_df_orig)

            if len(merged_df) > 0:
                # Begin pagination
                if "page_no" not in st.session_state:
                    st.session_state["page_no"] = 0
                per_page_rows = 5
                last_page, remainder = divmod(len(merged_df), per_page_rows)

                if remainder == 0:
                    last_page -= 1

                last_page = max(last_page, 1)
                page_no = st.session_state["page_no"]
                start_idx = page_no * per_page_rows
                end_idx = (1 + page_no) * per_page_rows

                unique_offers = merged_df[start_idx:end_idx]
                for row in unique_offers.itertuples():
                    outb_chunk = outb_df[row.offerID_Outbound == outb_df["offerID"]]
                    inb_chunk = inb_df[row.offerID_Inbound == inb_df["offerID"]]

                    # Raise error if either chunk is empty
                    error_msg = " offers chunk is empty"
                    if len(outb_chunk) == 0:
                        raise ValueError("Outbound"+ error_msg)
                    if len(inb_chunk) == 0:
                        raise ValueError("Inbound"+ error_msg)

                    # Format offer title
                    title = self.__full_offer_title_fmt(row)
                    self._full_offer_expander(title, outb_chunk, inb_chunk)
                
                # Page buttons
                col1s, mid, col2s = st.columns([0.2, 0.6, 0.2])
                with col1s:
                    disabled = st.session_state["page_no"] == 0
                    if st.button("Previous", disabled=disabled):
                        if st.session_state["page_no"] > 0:
                            st.session_state["page_no"] -= 1
                with mid:
                    # TODO: fix
                    st.write(f'Page {st.session_state["page_no"]+1} / {last_page+1}')
                with col2s:
                    disabled = st.session_state["page_no"] == last_page
                    if st.button("Next", disabled=disabled):
                        if st.session_state["page_no"] < last_page:
                            st.session_state["page_no"] += 1

                # Combine flight durations
                combined_durations = self.controller._concat_offers_duration(merged_df)

                # Create bins of 2 hours (120 minutes)
                bins = range(0, int(combined_durations.max())+120, 120)

                # Calculate the count of flights in each bin
                duration_counts = pd.cut(combined_durations, bins=bins).value_counts().sort_index()

                # Create a df for the bar chart
                duration_colname = 'Flight Duration'
                count_colname = 'Count'
                bin_colname = 'Bin'
                duration_df = pd.DataFrame({
                    duration_colname: [f'{interval.left //60}-{interval.right //60}h' for interval in duration_counts.index],
                    count_colname: duration_counts.values,
                    bin_colname: duration_counts.index
                })

                # Plot bar chart
                fig = px.bar(duration_df, x=duration_colname, y=count_colname, color=count_colname,
                            color_continuous_scale=px.colors.sequential.speed
                )
                fig.update_layout(
                    yaxis={'fixedrange': True},
                    xaxis={'fixedrange': True, 'tickangle': -90},
                    dragmode=False,
                    showlegend=False
                )

                # Plot chart
                st.plotly_chart(fig)
            else:
                st.write("Oh no i'm gay")

            # Max duration slider
            max_val = st.session_state["absolute_max_duration"] / 60
            st.slider("Max duration", min_value=0.0, max_value=max_val, step=0.5, format="%0.1f hrs",
                      key="_max_duration", on_change=self.__keep, args=['max_duration'])
