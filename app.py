import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from streamlit_image_coordinates import streamlit_image_coordinates
import io
import json

# -------------------------
# Page setup
# -------------------------

st.set_page_config(
    page_title="Scientific Plot Digitizer",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Scientific Plot Digitizer")
st.write("Developed by Manasij Yadava")

# -------------------------
# Session initialization
# -------------------------

def init_session():

    defaults = {
        "x_refs": [],
        "y_refs": [],
        "data_points": [],
        "image": None
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# -------------------------
# Sidebar controls
# -------------------------

st.sidebar.header("Controls")

mode = st.sidebar.radio(
    "Selection mode",
    ["Data points", "X reference", "Y reference"]
)

# Undo
if st.sidebar.button("Undo last point"):

    if mode == "Data points" and st.session_state.data_points:
        st.session_state.data_points.pop()

    elif mode == "X reference" and st.session_state.x_refs:
        st.session_state.x_refs.pop()

    elif mode == "Y reference" and st.session_state.y_refs:
        st.session_state.y_refs.pop()

# Reset
if st.sidebar.button("Reset all"):

    st.session_state.x_refs = []
    st.session_state.y_refs = []
    st.session_state.data_points = []

# Save session
if st.sidebar.button("Save session"):

    session = {
        "x_refs": st.session_state.x_refs,
        "y_refs": st.session_state.y_refs,
        "data_points": st.session_state.data_points
    }

    st.sidebar.download_button(
        "Download session file",
        json.dumps(session),
        "digitizer_session.json"
    )

# Load session
uploaded_session = st.sidebar.file_uploader(
    "Load session",
    type="json"
)

if uploaded_session:

    session = json.load(uploaded_session)

    st.session_state.x_refs = session["x_refs"]
    st.session_state.y_refs = session["y_refs"]
    st.session_state.data_points = session["data_points"]

# -------------------------
# Upload image
# -------------------------

uploaded_image = st.file_uploader(
    "Upload plot image",
    type=["png", "jpg", "jpeg"]
)

if uploaded_image:

    st.session_state.image = Image.open(uploaded_image)

if st.session_state.image is None:

    st.stop()

image = st.session_state.image.copy()

# -------------------------
# Draw numbered points
# -------------------------

draw = ImageDraw.Draw(image)

def draw_points(points, color, prefix):

    for i, (x, y) in enumerate(points):

        r = 5

        draw.ellipse(
            (x-r, y-r, x+r, y+r),
            fill=color
        )

        draw.text(
            (x+5, y+5),
            f"{prefix}{i+1}",
            fill=color
        )

draw_points(st.session_state.x_refs, "red", "X")
draw_points(st.session_state.y_refs, "green", "Y")
draw_points(st.session_state.data_points, "blue", "P")

# -------------------------
# Capture clicks
# -------------------------

st.write(f"Mode: {mode}")

coords = streamlit_image_coordinates(
    image,
    key="plot",
)

if coords:

    x = coords["x"]
    y = coords["y"]

    point = [x, y]

    if mode == "Data points":

        if point not in st.session_state.data_points:
            st.session_state.data_points.append(point)

    elif mode == "X reference":

        if len(st.session_state.x_refs) < 2:
            st.session_state.x_refs.append(point)

    elif mode == "Y reference":

        if len(st.session_state.y_refs) < 2:
            st.session_state.y_refs.append(point)

# -------------------------
# Show point lists
# -------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.write("X refs:", st.session_state.x_refs)

with col2:
    st.write("Y refs:", st.session_state.y_refs)

with col3:
    st.write("Data:", len(st.session_state.data_points), "points")

# -------------------------
# Scaling and export
# -------------------------

if len(st.session_state.x_refs) == 2 and len(st.session_state.y_refs) == 2:

    st.header("Enter actual reference values")

    col1, col2 = st.columns(2)

    with col1:

        x1 = st.number_input("X value ref 1")
        x2 = st.number_input("X value ref 2")

    with col2:

        y1 = st.number_input("Y value ref 1")
        y2 = st.number_input("Y value ref 2")

    def convert():

        xpix = np.array([p[0] for p in st.session_state.data_points])
        ypix = np.array([p[1] for p in st.session_state.data_points])

        xscale = (x2 - x1) / (
            st.session_state.x_refs[1][0]
            - st.session_state.x_refs[0][0]
        )

        xoffset = x1 - xscale * st.session_state.x_refs[0][0]

        yscale = (y2 - y1) / (
            st.session_state.y_refs[1][1]
            - st.session_state.y_refs[0][1]
        )

        yoffset = y1 - yscale * st.session_state.y_refs[0][1]

        xdata = xscale * xpix + xoffset
        ydata = yscale * ypix + yoffset

        return pd.DataFrame({
            "x": xdata,
            "y": ydata
        })

    if st.button("Generate output"):

        df = convert()

        st.dataframe(df)

        # CSV
        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "digitized_data.csv"
        )

        # Excel
        excel_buffer = io.BytesIO()

        df.to_excel(excel_buffer, index=False)

        st.download_button(
            "Download Excel",
            excel_buffer.getvalue(),
            "digitized_data.xlsx"
        )
