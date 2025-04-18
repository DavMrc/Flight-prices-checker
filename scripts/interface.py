import streamlit as st
import altair as alt
import pandas as pd
import datetime
import logging
from my_enums import TripType
from controller import FlightsController
from helpers import fmt_duration, gantt_chart_height_proportion


class FlightPricesChecker:
    def __init__(self):
        logging.info("Initializing FlightPricesChecker...")
        self.controller: FlightsController = st.session_state["controller"]

        if "airports_json" not in st.session_state:
            airports_json = self.controller.get_airports_json()
            st.session_state["airports_json"] = airports_json

    def __keep(self, key):
        # https://stackoverflow.com/a/76211845
        st.session_state[key] = st.session_state['_'+key]

    def __airport_option_fmt(self, option):
        if st.session_state["search_by"] == "iata code":
            return option["iata_code"]
        else:
            return option["name"]

    def __create_debug_session__(self):
        if "debug" not in st.session_state:
            import json
            # Load dumped session state
            path = "F:/Programmazione/Flight prices checker/data"
            sess_state_debug: dict = json.load(open(path+"/debugging-st-session.json"))
            sess_state: dict = sess_state_debug
            date_cols = ["date_range", "_date_range"]

            for col in date_cols:
                parsed_date_list = []
                for date_str in sess_state_debug[col]:
                    parsed_date = datetime.datetime.fromisoformat(date_str).date()
                    parsed_date_list.append(parsed_date)
                
                sess_state.update({col: parsed_date_list})
            
            st.session_state.update(sess_state)

            # --- Load dataframes
            inb_df = pd.read_pickle(path+"/samples/inb_df.pkl")
            outb_df = pd.read_pickle(path+"/samples/outb_df.pkl")
            merged_df_orig = pd.read_pickle(path+"/samples/merged_df_orig.pkl")

            st.session_state["inb_df"] = inb_df
            st.session_state["outb_df"] = outb_df
            st.session_state["merged_df"] = merged_df_orig
            st.session_state["debug"] = True

    def run(self):
        self.__home_pg = st.Page(self.home, title="Home")
        self.__flights_pg = st.Page(self.flights, title="Flights")
        self.__offers_pg = st.Page(self.offers, title="Offers")

        nav = st.navigation(
            [
                self.__home_pg,
                self.__flights_pg,
                self.__offers_pg
            ],
            position="hidden"
        )
        nav.run()

    def home(self):
        st.set_page_config(layout="centered")
        # Title of the app
        st.title("Flight Prices Checker", anchor=False)

        # Dropdown to select between "iata code" and "airport name"
        UIComponents.search_by_picker(on_change=self.__keep)
        
        # Airport selectboxes side by side
        UIComponents.airport_pickers(format_func=self.__airport_option_fmt, on_change=self.__keep)

        # Date range input
        UIComponents.date_picker()

        # Range slider for minDays and maxDays
        UIComponents.min_max_days_picker(on_change=self.__keep)

        #  Navigate to next page
        _, col = st.columns([0.8, 0.2])
        with col:
            if st.button(label="Search Flights", icon="🔍"):
                st.switch_page(self.__flights_pg)

    def flights(self):
        # TODO aggiungere barra KPI
        st.set_page_config(layout="wide")

        if st.button(label="Back", icon="⬅"):
            # Remove price_graph_df so that next time the user
            # goes back to this page, the graph is reloaded
            st.session_state.pop("price_graph_df")
            st.switch_page(self.__home_pg)

        start_date, end_date = st.session_state["date_range"]
        min_days, max_days = st.session_state["days_range"]
        max_price = 0
        if "max_price" in st.session_state:
            max_price = st.session_state["max_price"]

        params = {
            "departureAirport" : st.session_state["dep_airport"]["iata_code"],
            "destinationAirport" : st.session_state["arr_airport"]["iata_code"],
            "startDate" : start_date.strftime("%Y-%m-%d"),
            "returnDate" : end_date.strftime("%Y-%m-%d"),
            "minDays" : min_days,
            "maxDays" : max_days,
            "maxPrice": max_price
        }

        col1, col2 = st.columns([0.2, 0.8])
        with col2:
            with st.spinner("Loading alternatives...", show_time=True):
                if "price_graph_df" not in st.session_state:
                    price_graph_df = self.controller.get_price_graph(params)
                    st.session_state["price_graph_df"] = price_graph_df

                price_graph_df: pd.DataFrame = st.session_state["price_graph_df"]
                query_df = self.controller.filter_price_graph(price_graph_df, params)

                if len(query_df) > 0:
                    # Plot the chart
                    height = gantt_chart_height_proportion(query_df) + 40
                    if height > 800:
                        height = 800
                    if height < 200:
                        height = 200

                    with st.container(height=height):
                        UIComponents.gantt_chart(query_df)
                else:
                    st.write("There are no offers matching the applied filters.")

        with col1:
            # Display selected airports
            UIComponents.airport_pickers(format_func=self.__airport_option_fmt, on_change=self.__keep, disabled=True)

            # Date range input
            UIComponents.date_picker(disabled=True)

            # Range slider for minDays and maxDays
            UIComponents.min_max_days_picker(on_change=self.__keep, disabled=True)

            # Initial max price
            limit_min = int(price_graph_df["Price"].min())
            limit_max = int(price_graph_df["Price"].max())
            help_msg = "_Only in this page_, the maximum price shown is an **estimate** based on Google's statistics"
            UIComponents.max_price_picker(limit_min_price=limit_min, limit_max_price=limit_max,
                                          on_change=self.__keep, help=help_msg)

        #  Navigate to next page        
        _, col = st.columns([0.8, 0.2])
        with col:
            if st.button(label="Search Offers", icon="🔍"):
                st.session_state["price_graph_df"] = query_df
                st.switch_page(self.__offers_pg)

    def offers(self):
        # TODO mettere un bottone di reset dei filtri
        # TODO aggiungere barra KPI
        st.set_page_config(layout="wide")

        if st.button(label="Back", icon="⬅"):
            st.session_state.pop("merged_df")
            st.switch_page(self.__flights_pg)

        col1, col2 = st.columns([0.2, 0.8])
        # First displayed col2 so that session state is updated with
        # all necessary values
        with col2:
            start_date, end_date = st.session_state["date_range"]
            min_days, max_days = st.session_state["days_range"]

            max_duration = -1
            if "max_duration" in st.session_state:
                max_duration = st.session_state["max_duration"] * 60

            params = {
                "departureAirport" : st.session_state["dep_airport"]["iata_code"],
                "destinationAirport" : st.session_state["arr_airport"]["iata_code"],
                "startDate" : start_date.strftime("%Y-%m-%d"),
                "returnDate" : end_date.strftime("%Y-%m-%d"),
                "minDays" : min_days,
                "maxDays" : max_days,
                "maxPrice" : st.session_state["max_price"],
                "maxDuration": max_duration
            }

            if "merged_df" not in st.session_state:
                with st.spinner(show_time=True):
                    price_graph_df = st.session_state["price_graph_df"]
                    outb_df = self.controller.get_offers(price_graph_df, params, trip_type=TripType.OUTBOUND)
                    inb_df = self.controller.get_offers(price_graph_df, params, trip_type=TripType.INBOUND)
                    merged_df = self.controller.merge_offers(outb_df, inb_df)

                st.session_state["outb_df"] = outb_df
                st.session_state["inb_df"] = inb_df
                st.session_state["merged_df"] = merged_df

            merged_df_orig: pd.DataFrame = st.session_state["merged_df"]

            if "absolute_max_duration" not in st.session_state:
                st.session_state["absolute_max_duration"] = self.controller._concat_offers_duration(merged_df_orig).max()

            if "max_duration" not in st.session_state:
                st.session_state["max_duration"] = st.session_state["absolute_max_duration"]
            
            if "selected_heatmap_point" in st.session_state:
                selection = st.session_state["selected_heatmap_point"]["selection"]["selected_point"]
                if selection and selection[0]["Number of Flights"] > 0:
                    params.update({"selected_heatmap_point": selection[0]})

            merged_df = self.controller.filter_merged_offers(merged_df_orig, params)
            if len(merged_df) > 0:
                col1_s, col2_s = st.columns(2)
                with col1_s:
                    # Flight count heatmap
                    heatmap_data = self.controller.flight_count_heatmap(merged_df)
                    UIComponents.flight_count_heatmap(heatmap_data)
                
                with col2_s:
                    # Flight duration barchart
                    duration_df = self.controller.flight_duration_barchart(merged_df)
                    UIComponents.flight_duration_barchart(duration_df)

                # Offer list
                # TODO rendere parametrizzabile
                per_page_rows = 5
                UIComponents.offer_list(merged_df, per_page_rows)
            else:
                st.write("There are no offers matching the applied filters.")
        
        with col1:
            # Display selected airports
            UIComponents.airport_pickers(format_func=self.__airport_option_fmt, on_change=self.__keep, disabled=True)

            # Date range input
            UIComponents.date_picker(disabled=True)

            # Range slider for minDays and maxDays
            UIComponents.min_max_days_picker(on_change=self.__keep, disabled=True)

            # Max price
            min_price = merged_df_orig["fullPrice"].min()
            max_price = merged_df_orig["fullPrice"].max()
            UIComponents.max_price_picker(limit_min_price=min_price, limit_max_price=max_price, on_change=self.__keep)

            # Max duration slider
            UIComponents.max_duration_picker(on_change=self.__keep)


class UIComponents:
    """
    A class that holds standard, reusable widgets to be used in pages of the app
    """

    __default_color_palette = {"scheme": "darkgreen", "reverse": True}
    color_palette = __default_color_palette
    @classmethod
    def update_color_palette(cls, color_palette: dict=None):
        """
        Default: `{"scheme": "lightgreyred", "reverse": False}`
        """
        if not color_palette:
            cls.color_palette = cls.__default_color_palette
        
        cls.color_palette = color_palette

    # Widgets
    @staticmethod
    def search_by_picker(**kwargs):
        if "search_by" not in st.session_state:
            st.session_state["search_by"] = "iata code"

        st.radio("Search by", ["iata code", "airport name"], horizontal=True, key="_search_by",
                 args=["search_by"], **kwargs)

    @staticmethod
    def airport_pickers(**kwargs):
        airports_json = st.session_state["airports_json"]
        col1, col2 = st.columns(2)
        with col1:
            ix = 0
            if "dep_airport" in st.session_state:
                ix = st.session_state["dep_airport"]["index"]

            st.selectbox("Departure", options=airports_json, key="_dep_airport", index=ix,
                         args=["dep_airport"], **kwargs)
        with col2:
            ix = 0
            if "arr_airport" in st.session_state:
                ix = st.session_state["arr_airport"]["index"]

            st.selectbox("Arrival", options=airports_json, key="_arr_airport", index=ix,
                         args=["arr_airport"], **kwargs)

    @staticmethod
    def date_picker(**kwargs):
        if "date_range" not in st.session_state:
            range_min_date = datetime.date.today()
            range_max_date = range_min_date + datetime.timedelta(days=1)
            st.session_state["date_range"] = (range_min_date, range_max_date)

        range_min_date, range_max_date = st.session_state["date_range"]
        # TODO: l'utente può fare brute-force insert di una data, facendo fallire il widget
        selected_dates = st.date_input("Select Date Range", value=(range_min_date, range_max_date),
                                        min_value=datetime.date.today(), **kwargs)

        if len(selected_dates) == 2:
            if st.session_state["date_range"] != selected_dates:
                st.session_state["date_range"] = selected_dates
                # When the user selected only one date, the execution stopped
                # (see line below). Here, we rerun the app so that the app
                # "restarts" working
                st.rerun()
        else:
            # Prevent further processing until both dates are selected
            st.warning("Please select both start and end dates.")
            st.stop()

    @staticmethod
    def min_max_days_picker(**kwargs):
        if "date_range" in st.session_state and len(st.session_state["date_range"]) == 2:
            start_date, end_date = st.session_state["date_range"]

            if "days_range" in st.session_state:
                min_days, max_days = st.session_state["days_range"]
                limit_max = (end_date - start_date).days
                limit_max = max(limit_max, 1)
            else:
                min_days = 0
                max_days = (end_date - start_date).days
                max_days = max(max_days, 1)
                limit_max = max_days

        st.slider("Select range of days", 0, limit_max, (min_days, max_days),
                key="_days_range", args=["days_range"], **kwargs)

    @staticmethod
    def max_price_picker(limit_max_price:int, limit_min_price:int=0, **kwargs):
        if "max_price" in st.session_state:
            curr_price = st.session_state["max_price"]
        else:
            curr_price = limit_max_price
            st.session_state["max_price"] = limit_max_price
        
        if limit_min_price == limit_max_price:
            limit_min_price = limit_max_price - 1

        st.slider("Max Price", min_value=limit_min_price, max_value=limit_max_price, value=curr_price,
                    key="_max_price", args=['max_price'], **kwargs)

    @staticmethod
    def max_duration_picker(**kwargs):
        max_val = st.session_state["absolute_max_duration"] / 60
        st.slider("Max duration", value=max_val, min_value=0.0, max_value=max_val, step=0.5, format="%0.1f hrs",
                    key="_max_duration", args=["max_duration"], **kwargs)

    # Flight offers widgets
    @staticmethod
    def offer(title: str, outdf: pd.DataFrame, indf: pd.DataFrame):
        """
        UI Component that consists of a `st.expander` with 
        two blocks side by side, each containing respectively
        outbound and inbound flights.
        """
        with st.expander(title):
            col1, col2 = st.columns(2, border=True)

            with col1:
                subtitle = UIComponents.__card_title_fmt(outdf)
                st.markdown(subtitle)
                UIComponents.__offer_card(outdf)
            with col2:
                subtitle = UIComponents.__card_title_fmt(indf)
                st.markdown(subtitle)
                UIComponents.__offer_card(indf)

    @staticmethod
    def __offer_card(df: pd.DataFrame):
        """
        UI component that represents a single flight offer inside of a card-like object
        """
        rows = list(df.itertuples(index=False))
        nrows = len(rows)
        for i, row in enumerate(rows):
            # TODO: sarebbe bello aggiungere il nome dell'aeroporto
            # Departure
            dep_time = row.departureTime.strftime("%H:%M")
            dep_airport = row.departureAirport

            # Duration
            duration = datetime.timedelta(minutes=row.flightDuration)
            formatted_time = fmt_duration(duration)

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
                formatted_time = fmt_duration(layover_duration)

                st.markdown(f"- Layover: h{formatted_time} · {row.arrivalAirport}\n---")
            except IndexError:
                # flight combination has no (or no-more) layovers
                pass

        st.link_button("", url=row.url, icon=":material/travel:", help="Open in Google Flights")

    @staticmethod
    def __card_title_fmt(df: pd.DataFrame):
        dep_date_fmt = df["startDate"].iloc[0].strftime("%a %d %b")
        total_duration_fmt = fmt_duration(df["arrivalTime"].iloc[-1] - df["departureTime"].iloc[0])
        layovers = len(df)-1
        price = df["price"].iloc[0].astype(str) +"€"

        return f'##### {dep_date_fmt} | {price}\n{total_duration_fmt} | {layovers} stops'

    @staticmethod
    def __offer_title_fmt(row: pd.DataFrame) -> str:
        dep_date_fmt = row.departureTime_Outbound.strftime("%a %d %b")
        ret_date_fmt = row.departureTime_Inbound.strftime("%a %d %b")
        price = str(row.fullPrice) +"€"

        return f'{dep_date_fmt} - {ret_date_fmt} | {price}'

    @staticmethod
    def offer_list(merged_df: pd.DataFrame, per_page_rows: int):
        """
        UI component that shows a vertical list of exactely `per_page_rows` `UIComponents.offer()` elements. 
        """
        if "page_no" not in st.session_state:
            st.session_state["page_no"] = 0

        page_no = st.session_state["page_no"]
        last_page, remainder = divmod(len(merged_df), per_page_rows)
        if remainder == 0:
            last_page -= 1

        if "last_page" not in st.session_state:
            # Initialization
            st.session_state["last_page"] = last_page

        if last_page < page_no:
            # Number of rows has decreased due to filters
            page_no = 0
            st.session_state["page_no"] = page_no

        st.session_state["last_page"] = last_page

        offers_container = st.container()
        pagination_container = st.container()
        # --- PAGINATION ELEMENTS ---
        with pagination_container:
            def increase():
                if st.session_state["page_no"] < st.session_state["last_page"]:
                    st.session_state["page_no"] += 1
            
            def decrease():
                if st.session_state["page_no"] > 0:
                    st.session_state["page_no"] -= 1

            col1s, mid, col2s = st.columns([0.2, 0.6, 0.2])
            with col1s:
                disabled = page_no == 0
                st.button("Previous", disabled=disabled, key="prev_button", on_click=decrease)
            with mid:
                st.write(f'Page {page_no+1} / {last_page+1}')
            with col2s:
                disabled = page_no == last_page
                st.button("Next", disabled=disabled, key="next_button", on_click=increase)

        # --- ITERATING OVER OFFERS ---
        with offers_container:
            outb_df: pd.DataFrame = st.session_state["outb_df"]
            inb_df: pd.DataFrame = st.session_state["inb_df"]

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
                title = UIComponents.__offer_title_fmt(row)
                UIComponents.offer(title, outb_chunk, inb_chunk)

    # Charts
    @classmethod
    def gantt_chart(cls, query_df: pd.DataFrame):
        height = gantt_chart_height_proportion(query_df)
        gantt = alt.Chart(query_df).mark_bar().encode(
            x=alt.X('startDate:T', title=None),
            x2=alt.X2('returnDate:T', title=None),
            y=alt.Y('row_number:O', title=None, axis=None),
            color=alt.Color('Price:Q').scale(**cls.color_palette),
            tooltip=[
                alt.Tooltip('startDate:T', title="Departure Date"),
                alt.Tooltip('returnDate:T', title="Return Date"),
                alt.Tooltip('Days:Q', title="Vacation Days"),
                alt.Tooltip('Price:Q', title='Est. price (€)')
            ]
        ).transform_window(
            row_number='row_number()'
        ).properties(
            height=height
        ).configure_axisX(
            tickCount="day",
            labelAngle=-90
        )

        # Hide options to download chart
        gantt["usermeta"] = {
            "embedOptions": {
                "actions": False,
            }
        }

        st.altair_chart(gantt, use_container_width=True)

    @classmethod
    def flight_count_heatmap(cls, heatmap_data: pd.DataFrame):
        outb_date_colname = "Departure Date"
        inb_date_colname = "Return Date"
        outb_date_colname_fmt = "Departure Date_fmt"
        inb_date_colname_fmt = "Return Date_fmt"
        number_of_flights_colname = "Number of Flights"
        days_colname = "Days"

        # Create the heatmap
        selection_point = alt.selection_point("selected_point", empty='none',
                                              fields=[outb_date_colname, inb_date_colname, number_of_flights_colname])

        heatmap = alt.Chart(heatmap_data).mark_rect().encode(
            x=alt.X(f'{inb_date_colname_fmt}:O', title=inb_date_colname).sort(),
            y=alt.Y(f'{outb_date_colname_fmt}:O', title=outb_date_colname).sort(),
            color=alt.Color(f'{number_of_flights_colname}:Q').scale(**cls.color_palette),
            tooltip=[
                # order of the fields matters!
                {"field": outb_date_colname_fmt, "title": outb_date_colname},
                {"field": inb_date_colname_fmt, "title": inb_date_colname},
                {"field": number_of_flights_colname, "title": number_of_flights_colname},
                {"field": days_colname, "title": days_colname}
            ]
        ).properties(
            title="Flight Prices Heatmap",
            height=400
        ).add_params(selection_point)

        # Hide options to download chart
        heatmap["usermeta"] = {
            "embedOptions": {
                "actions": False,
            }
        }

        # Display the heatmap in Streamlit
        st.altair_chart(heatmap, on_select="rerun", use_container_width=True, key="selected_heatmap_point")
        # Sample of return of a selection click
        # {
        #     "selection": {
        #         "selected_point": [
        #         {
        #             "Number of Flights": 36,
        #             "Return Date_fmt": "Tue 15 Apr",
        #             "Departure Date_fmt": "Thu 10 Apr",
        #             "Departure Date": "2025-04-10",
        #             "Return Date": "2025-04-15"
        #         }
        #         ]
        #     }
        # }

    @classmethod
    def flight_duration_barchart(cls, duration_df: pd.DataFrame):
        chart = alt.Chart(duration_df).mark_bar().encode(
            x=alt.X('Flight Duration:N').sort(),
            y='Count:Q',
            color=alt.Color('Count:Q').scale(**cls.color_palette),
            tooltip=['Flight Duration', 'Count']
        ).properties(
            title='Flight Duration Distribution',
            height=400
        )

        # Hide options to download chart
        chart["usermeta"] = {
            "embedOptions": {
                "actions": False,
            }
        }

        st.altair_chart(chart, use_container_width=True)
