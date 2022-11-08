# -*- coding: utf-8 -*-
# Copyright 2018-2022 Streamlit Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""An example of showing geographic data."""

import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from datetime import datetime


# SETTING PAGE CONFIG TO WIDE MODE AND ADDING A TITLE AND FAVICON
st.set_page_config(layout="wide", page_title="European Air Pollution", page_icon=":cloud:")

# LOAD DATA ONCE
@st.experimental_singleton
def load_data():
    data = pd.read_csv(
        "uk_france_italy_o3_nans_no2_no_non_strict_drop_dups.csv",
        #"all_test_countries_o3_nans_no2_no_non_strict_drop_dups.csv",
        #"both_ukfrit_and_test_countries_o3_nans_no2_no_non_strict_drop_dups.csv",
        #nrows=1000000,  # approx. 10% of data # this is so fucking weird, why does it only work when we select nrows = 1000000 when we use both...
        names=[
            "datetime",
            "lat",
            "lon",
            "o3",
        ],  # specify names directly since they don't change
        skiprows=1,  # don't read header since names specified directly
        usecols=[0, 4, 5, 18],  # doesn't load last column, constant value "B02512"
        parse_dates=[
            "datetime"
        ],  # set as datetime instead of converting after the fact
    )

    return data


# FUNCTION FOR AIRPORT MAPS
def map(df, lat, lon, zoom):
    st.write(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state={
                "latitude": lat,
                "longitude": lon,
                "zoom": zoom,
                "pitch": 50,
            },
            layers=[
                pdk.Layer(
                    "ColumnLayer",
                    data=df,
                    get_position=["lat", "lon"],
                    get_elevation="o3",
                    get_fill_color=["o3*3", "200-o3*2", 100],
                    radius=6000,
                    elevation_scale=2000,
                    elevation_range=[100, 1000],
                    pickable=True,
                    extruded=True,
                    auto_highlight=True
                ),
            ],
        )
    )


# FILTER DATA FOR A SPECIFIC HOUR, CACHE
@st.experimental_memo
def filterdata(df, date_selected):
    #return df[df["datetime"].dt.date == date_selected]
    data_specific_datetime = df[df["datetime"] == date_selected]
    return data_specific_datetime


# CALCULATE MIDPOINT FOR GIVEN SET OF DATA
@st.experimental_memo
def mpoint(lat, lon):
    return (np.average(lat), np.average(lon))


# FILTER DATA BY HOUR - this is basically unnecessary...! But it could be useful later for selecting by month, for example.

@st.experimental_memo
def histdata(df, day):
    filtered = data[
        (df["datetime"] >= day) & (df["datetime"] < (day + 1))
    ]

    hist = np.histogram(filtered["datetime"].dt.minute, bins=60, range=(0, 60))[0]

    return pd.DataFrame({"minute": range(60), "pickups": hist})


# STREAMLIT APP LAYOUT
data = load_data()

#min_o3 = data["o3"].min()
#max_o3 = data["o3"].max()

# LAYING OUT THE TOP SECTION OF THE APP
row1_1, row1_2 = st.columns((2, 3))

# SEE IF THERE'S A QUERY PARAM IN THE URL (e.g. ?pickup_hour=2)
# THIS ALLOWS YOU TO PASS A STATEFUL URL TO SOMEONE WITH A SPECIFIC HOUR SELECTED,
# E.G. https://share.streamlit.io/streamlit/demo-uber-nyc-pickups/main?pickup_hour=2
#if not st.session_state.get("url_synced", False):
#    try:
#        date = int(st.experimental_get_query_params()["date"][0])
#        st.session_state["date"] = date
#        st.session_state["url_synced"] = True
#    except KeyError:
#        pass

# IF THE SLIDER CHANGES, UPDATE THE QUERY PARAM
def update_query_params():
    date_selected = st.session_state["date"]
    st.experimental_set_query_params(date=date_selected)

# important note here: this breaks when we use different dates! Safe is 2007, 9, 9
# I expect this just requires us to reload the webpage in a fuller way...
with row1_1:
    st.title("European Ozone Air Pollution")
    date_selected = st.slider(
        "Select date", value=datetime(2011, 9, 9), format="DD/MM/YYYY", key="date", on_change=update_query_params
    )


with row1_2:
    st.write(
        """
    ##
    Illustrating how ozone air pollution measured at stations across Europe can vary with time. Focus in on three cities: London, Paris, and Rome.
    By sliding the slider on the left you can view different slices of time and explore ozone.
    """
    )

# LAYING OUT THE MIDDLE SECTION OF THE APP WITH THE MAPS
row2_1, row2_2, row2_3, row2_4 = st.columns((2, 1, 1, 1))

# SETTING THE ZOOM LOCATIONS FOR THE AIRPORTS
london = [51.504831314, -0.123499506]
paris = [48.858370, 2.294481]
rome = [41.8874314503, 12.4886930452]
zoom_level = 6
midpoint = mpoint(data["lat"], data["lon"])

with row2_1:
    st.write(
        f"""**All Europe on {date_selected}**"""
    )
    map(filterdata(data, date_selected), midpoint[0], midpoint[1], 3.7)

with row2_2:
    st.write("**London**")
    map(filterdata(data, date_selected), london[0], london[1], zoom_level)

with row2_3:
    st.write("**Paris**")
    map(filterdata(data, date_selected), paris[0], paris[1], zoom_level)

with row2_4:
    st.write("**Rome**")
    map(filterdata(data, date_selected), rome[0], rome[1], zoom_level)

# CALCULATING DATA FOR THE HISTOGRAM
#chart_data = histdata(data, hour_selected)

# LAYING OUT THE HISTOGRAM SECTION
#st.write(
#    f"""**Breakdown of rides per minute between {hour_selected}:00 and {(hour_selected + 1) % 24}:00**"""
#)

#st.altair_chart(
#    alt.Chart(chart_data)
#    .mark_area(
#        interpolate="step-after",
#    )
#    .encode(
#        x=alt.X("minute:Q", scale=alt.Scale(nice=False)),
#        y=alt.Y("pickups:Q"),
#        tooltip=["minute", "pickups"],
#    )
#    .configure_mark(opacity=0.2, color="red"),
#    use_container_width=True,
#)
