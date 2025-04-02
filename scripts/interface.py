import streamlit as st
import altair as alt
import pandas as pd
import datetime
import logging
from my_enums import TripType
from controller import FlightsController
from helpers import fmt_duration


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
        st.title("Flight Prices Checker")

        # Dropdown to select between "iata code" and "airport name"
        UIComponents.search_by_picker(on_change=self.__keep)
        
        # Airport selectboxes side by side
        UIComponents.airport_pickers(format_func=self.__airport_option_fmt, on_change=self.__keep)

        # Date range input
        UIComponents.date_picker(on_change=self.__keep)

        # Range slider for minDays and maxDays
        UIComponents.min_max_days_picker(on_change=self.__keep)

        #  Navigate to next page
        # TODO: align right
        if st.button(label="Search Flights", icon="🔍"):
            st.switch_page(self.__flights_pg)

    def flights(self):
        st.set_page_config(layout="wide")

        if st.button(label="Back", icon="⬅"):
            st.session_state.pop("price_graph_df")

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
                UIComponents.gantt_chart(query_df)

        with col1:
            # Display selected airports
            UIComponents.airport_pickers(format_func=self.__airport_option_fmt, on_change=self.__keep, disabled=True)

            # Date range input
            UIComponents.date_picker(on_change=self.__keep, disabled=True)

            # Range slider for minDays and maxDays
            UIComponents.min_max_days_picker(on_change=self.__keep, disabled=True)

            # Initial max price
            UIComponents.max_price_picker(price_graph_df["Price"].max(), on_change=self.__keep)

        #  Navigate to next page        
        # TODO: align right
        if st.button(label="Search Offers", icon="🔍"):
            st.session_state["price_graph_df"] = query_df
            st.switch_page(self.__offers_pg)

    def offers(self):
        st.set_page_config(layout="wide")

        if st.button(label="Back", icon="⬅"):
            st.switch_page(self.__flights_pg)

        col1, col2 = st.columns([0.2, 0.8])
        with col1:
            # Display selected airports
            UIComponents.airport_pickers(format_func=self.__airport_option_fmt, on_change=self.__keep, disabled=True)

            # Date range input
            UIComponents.date_picker(on_change=self.__keep, disabled=True)

            # Range slider for minDays and maxDays
            UIComponents.min_max_days_picker(on_change=self.__keep, disabled=True)

            # Initial max price
            max_price = st.session_state["max_price"]
            UIComponents.max_price_picker(max_price, disabled=True)

        with col2:
            start_date, end_date = st.session_state["date_range"]
            min_days, max_days = st.session_state["days_range"]

            if "max_duration" not in st.session_state:
                st.session_state["max_duration"] = 0

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
                    outb_df = self.controller.get_offers(price_graph_df, params, trip_type=TripType.OUTBOUND)
                    inb_df = self.controller.get_offers(price_graph_df, params, trip_type=TripType.INBOUND)
                    merged_df = self.controller.merge_offers(outb_df, inb_df, params, filter=False)

                st.session_state["outb_df"] = outb_df
                st.session_state["inb_df"] = inb_df
                st.session_state["merged_df"] = merged_df
                st.session_state["absolute_max_duration"] = self.controller._concat_offers_duration(merged_df).max()

            merged_df_orig: pd.DataFrame = st.session_state["merged_df"]
            merged_df = self.controller.filter_merged_offers(merged_df_orig, params)

            # Filter df based on selection made on the barchart (see below)
            if "max_duration" in st.session_state:
                max_duration: int = st.session_state["max_duration"] * 60

                if max_duration and max_duration > 0:
                    merged_df = self.controller._filter_merged_df_on_max_duration(max_duration, merged_df_orig)

            if len(merged_df) > 0:
                col1_s, col2_s = st.columns(2)
                with col1_s:
                    # Flight count heatmap
                    UIComponents.flight_count_heatmap(merged_df)
                
                with col2_s:
                    # Flight duration barchart
                    combined_durations = self.controller._concat_offers_duration(merged_df)
                    UIComponents.flight_duration_barchart(combined_durations)

                    # Max duration slider
                    UIComponents.max_duration_picker(on_change=self.__keep)

                # Offer list
                # TODO rendere parametrizzabile
                per_page_rows = 5
                UIComponents.offer_list(merged_df, per_page_rows)

                # Offer list page buttons
                UIComponents.offer_pagination(merged_df, per_page_rows)
            else:
                st.write("There are no offers matching the applied filters.")


class UIComponents:
    """
    A class that holds standard, reusable widgets to be used in pages of the app
    """

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
        # TODO: selezionare un range di date e tentare di modificarlo
        # fa andare a fanculo la UI
        if "date_range" in st.session_state and len(st.session_state["date_range"]) == 2:
            range_min_date, range_max_date = st.session_state["date_range"]
        else:
            range_min_date = datetime.date.today()
            range_max_date = datetime.date.today() + datetime.timedelta(days=1)

        st.date_input("Select Date Range", value=(range_min_date, range_max_date), min_value=datetime.date.today(),
                      key="_date_range", args=["date_range"], **kwargs)

    @staticmethod
    def min_max_days_picker(**kwargs):
        try:
            if "date_range" not in st.session_state:
                tup = (datetime.date.today(), datetime.date.today() + datetime.timedelta(days=1))
                st.session_state["date_range"] = tup

            start_date, end_date = st.session_state["date_range"]
            min_days = 0
            max_days = (end_date - start_date).days
            max_days = max(max_days, 1)

            st.slider("Select range of days", 0, max_days, (min_days, max_days),
                        key="_days_range", args=["days_range"], **kwargs)
        except ValueError:
            # The user has only selected one of start/end date, thus
            # the other is null
            st.warning("Please select both start and end dates.")

    @staticmethod
    def max_price_picker(limit_max_price:int, **kwargs):
        if "max_price" in st.session_state:
            curr_price = st.session_state["max_price"]
        else:
            curr_price = limit_max_price

        st.slider("Max Price", min_value=0, max_value=limit_max_price, value=curr_price,
                    key="_max_price", args=['max_price'], **kwargs)

    @staticmethod
    def max_duration_picker(**kwargs):
        max_val = st.session_state["absolute_max_duration"] / 60
        st.slider("Max duration", min_value=0.0, max_value=max_val, step=0.5, format="%0.1f hrs",
                    key="_max_duration", args=["max_duration"], **kwargs)

    # Flight offers widgets
    @staticmethod
    def offer(title: str, outdf: pd.DataFrame, indf: pd.DataFrame):
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
        rows = list(df.itertuples(index=False))
        nrows = len(rows)
        for i, row in enumerate(rows):
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
        outb_df: pd.DataFrame = st.session_state["outb_df"]
        inb_df: pd.DataFrame = st.session_state["inb_df"]

        if "page_no" not in st.session_state:
            st.session_state["page_no"] = 0

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
            title = UIComponents.__offer_title_fmt(row)
            UIComponents.offer(title, outb_chunk, inb_chunk)

    @staticmethod
    def offer_pagination(merged_df: pd.DataFrame, per_page_rows: int):
        last_page, remainder = divmod(len(merged_df), per_page_rows)
        if remainder == 0:
            last_page -= 1
        last_page = max(last_page, 1)

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

    # Charts
    @staticmethod
    def gantt_chart(df: pd.DataFrame):
        query_df = df.copy()
        gantt = alt.Chart(query_df).mark_bar().encode(
            x=alt.X('startDate:T', title=None),
            x2=alt.X2('returnDate:T', title=None),
            y=alt.Y('row_number:O', title=None, axis=None),
            color=alt.Color('Price:Q'),
            tooltip=['startDate:T', 'returnDate:T', alt.Tooltip('Price:Q', title='Price (€)')]
        ).transform_window(
            row_number='row_number()'
        ).properties(
            width=800,
            height=400
        ).configure_axisX(
            tickCount="day",
            labelAngle=-90
        )

        st.altair_chart(gantt, use_container_width=True)

    @staticmethod
    def flight_count_heatmap(merged_df: pd.DataFrame):
        df = merged_df[["departureTime_Outbound",  "departureTime_Inbound",
                "offerID_Inbound", "offerID_Outbound", "fullPrice"]].copy()
        # Keep only the date part
        df[["departureTime_Outbound", "departureTime_Inbound"]] = df[["departureTime_Outbound", "departureTime_Inbound"]]\
                                                                .apply(lambda x: x.dt.date)

        # Group by dates and count rows
        heatmap_data = df.groupby(['departureTime_Outbound', 'departureTime_Inbound']).size()\
                    .reset_index(name='Number of Flights')

        # --- Scaffold data ---
        # 
        # Add all possible combinations between the minimum departure date and the
        # maximum return date, imputing 0 number of flights. This ensures the
        # heatmaps plots correctely a box for every cell value

        # Find the overall min and max dates
        min_date = min(heatmap_data['departureTime_Outbound'].min(), heatmap_data['departureTime_Inbound'].min())
        max_date = max(heatmap_data['departureTime_Outbound'].max(), heatmap_data['departureTime_Inbound'].max())

        # Create a complete date range
        full_range = pd.date_range(start=min_date, end=max_date)
        # Generate all possible combinations of departureTime_Outbound and full_range
        all_combinations = pd.DataFrame(
            [(outb.date(), inb.date()) for outb in full_range for inb in full_range],
            columns=['departureTime_Outbound', 'departureTime_Inbound']
        )

        # Merge with existing heatmap_data to retain existing values
        heatmap_data = all_combinations.merge(
            heatmap_data,
            on=['departureTime_Outbound', 'departureTime_Inbound'],
            how='left'
        )
        # Fill missing 'Number of Flights' with 0
        heatmap_data.fillna({"Number of Flights": 0}, inplace=True)

        # Cast dates to datetime
        heatmap_data[["departureTime_Outbound", "departureTime_Inbound"]] = \
            heatmap_data[["departureTime_Outbound", "departureTime_Inbound"]].apply(pd.to_datetime)

        # Format dates into strings of format "%a %d %b"
        heatmap_data[["departureTime_Outbound_fmt", "departureTime_Inbound_fmt"]] = \
            heatmap_data[["departureTime_Outbound", "departureTime_Inbound"]].apply(lambda x: x.dt.strftime("%a %d %b"))
        
        # Format dates themselves
        heatmap_data[["departureTime_Outbound", "departureTime_Inbound"]] = \
            heatmap_data[["departureTime_Outbound", "departureTime_Inbound"]].apply(lambda x: x.dt.strftime("%Y-%m-%d"))

        # Renames columns
        outb_date_colname = "Departure Date"
        inb_date_colname = "Return Date"
        number_of_flights_colname = "Number of Flights"
        heatmap_data.rename({
            "departureTime_Outbound": outb_date_colname,
            "departureTime_Inbound": inb_date_colname,
            "departureTime_Outbound_fmt": f"{outb_date_colname}_fmt",
            "departureTime_Inbound_fmt": f"{inb_date_colname}_fmt",
        }, axis=1, inplace=True)

        # Create the heatmap
        selection_point = alt.selection_point("selected_point", empty='none', fields=[outb_date_colname, inb_date_colname])

        heatmap = alt.Chart(heatmap_data).mark_rect().encode(
            x=alt.X(f'{inb_date_colname}_fmt:O', title=inb_date_colname).sort(),
            y=alt.Y(f'{outb_date_colname}_fmt:O', title=outb_date_colname).sort(),
            color=alt.Color(f'{number_of_flights_colname}:Q'),
        ).properties(
            title="Flight Prices Heatmap"
        ).add_params(selection_point)

        # Display the heatmap in Streamlit
        data = st.altair_chart(heatmap, on_select="rerun", use_container_width=True)
        try:
            selected_point = data["selection"]["selected_point"][0]
            st.session_state["selected_heatmap_point"] = selected_point
        except Exception:
            pass
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

    @staticmethod
    def flight_duration_barchart(combined_durations: pd.Series):
        # Create bins of 2 hours (120 minutes)
        bins = range(0, int(combined_durations.max())+120, 120)

        # Calculate the count of flights in each bin
        duration_counts = pd.cut(combined_durations, bins=bins).value_counts().sort_index()

        duration_colname = 'Flight Duration'
        count_colname = 'Count'
        # bin_colname = 'Bin'
        duration_df = pd.DataFrame({
            duration_colname: [f'{interval.left //60}-{interval.right //60}h' for interval in duration_counts.index],
            count_colname: duration_counts.values,
            # bin_colname: duration_counts.index
        })

        chart = alt.Chart(duration_df).mark_bar().encode(
            x=alt.X('Flight Duration:N').sort(),
            y='Count:Q',
            color=alt.Color('Count:Q'),
            tooltip=['Flight Duration', 'Count']
        ).properties(
            title='Flight Duration vs Count'
        )
        st.altair_chart(chart, use_container_width=True)
