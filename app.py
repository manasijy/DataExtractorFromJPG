import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
import io
import json
from streamlit_image_coordinates import streamlit_image_coordinates

# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(
    page_title="Scientific Plot Digitizer",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Scientific Plot Digitizer")
st.write("Professional digitizer with zoom, scaling, and export")

# -------------------------
# SESSION INIT
# -------------------------

def init():

    defaults = {
        "image": None,
        "x_refs": [],
        "y_refs": [],
        "data_points": [],
        "last_point": None
    }

    for k, v in defaults.items():

        if k not in st.session_state:
            st.session_state[k] = v

init()

# -------------------------
# SIDEBAR
# -------------------------

st.sidebar.header("Controls")

mode = st.sidebar.radio(
    "Selection mode",
    ["Data points", "X reference", "Y reference"]
)

zoom = st.sidebar.slider(
    "Zoom",
    0.5,
    3.0,
    1.0,
    0.1
)

# Undo
if st.sidebar.button("Undo last point"):

    if mode == "Data points" and st.session_state.data_points:
        st.session_state.data_points.pop()

    elif mode == "X reference" and st.session_state.x_refs:
        st.session_state.x_refs.pop()

    elif mode == "Y reference" and st.session_state.y_refs:
        st.session_state.y_refs.pop()

# Delete specific point
if st.sidebar.button("Delete last data point"):

    if st.session_state.data_points:
        st.session_state.data_points.pop()

# Reset
if st.sidebar.button("Reset ALL"):

    st.session_state.x_refs = []
    st.session_state.y_refs = []
    st.session_state.data_points = []
    st.session_state.last_point = None

# Save session
if st.sidebar.button("Save session"):

    session = {
        "x_refs": st.session_state.x_refs,
        "y_refs": st.session_state.y_refs,
        "data_points": st.session_state.data_points
    }

    st.sidebar.download_button(
        "Download session",
        json.dumps(session),
        "session.json"
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
# IMAGE LOAD
# -------------------------

uploaded_image = st.file_uploader(
    "Upload plot image",
    type=["png", "jpg", "jpeg"]
)

if uploaded_image:

    st.session_state.image = Image.open(uploaded_image)

if st.session_state.image is None:
    st.stop()

# Apply zoom
base_image = st.session_state.image
width, height = base_image.size

image = base_image.resize(
    (int(width * zoom), int(height * zoom))
)

draw = ImageDraw.Draw(image)

# -------------------------
# DRAW POINTS
# -------------------------

def draw_points(points, color, label):

    for i, (x, y) in enumerate(points):

        zx = int(x * zoom)
        zy = int(y * zoom)

        r = 4

        draw.ellipse(
            (zx-r, zy-r, zx+r, zy+r),
            fill=color
        )

        draw.text(
            (zx+5, zy+5),
            f"{label}{i+1}",
            fill=color
        )

draw_points(st.session_state.x_refs, "red", "X")
draw_points(st.session_state.y_refs, "green", "Y")
draw_points(st.session_state.data_points, "blue", "P")

# -------------------------
# CLICK CAPTURE
# -------------------------

st.write("Mode:", mode)

coords = streamlit_image_coordinates(
    image,
    key="digitizer"
)

if coords is not None:

    x = int(coords["x"] / zoom)
    y = int(coords["y"] / zoom)

    new_point = [x, y]

    if st.session_state.last_point != new_point:

        st.session_state.last_point = new_point

        if mode == "Data points":

            if new_point not in st.session_state.data_points:
                st.session_state.data_points.append(new_point)

        elif mode == "X reference":

            if len(st.session_state.x_refs) < 2:
                st.session_state.x_refs.append(new_point)

        elif mode == "Y reference":

            if len(st.session_state.y_refs) < 2:
                st.session_state.y_refs.append(new_point)

# -------------------------
# DISPLAY STATUS
# -------------------------

col1, col2, col3 = st.columns(3)

col1.write("X refs:", st.session_state.x_refs)
col2.write("Y refs:", st.session_state.y_refs)
col3.write("Data points:", len(st.session_state.data_points))

# -------------------------
# SCALING
# -------------------------

if len(st.session_state.x_refs) == 2 and len(st.session_state.y_refs) == 2:

    st.header("Enter reference values")

    col1, col2 = st.columns(2)

    with col1:

        x1 = st.number_input("X reference 1 value")
        x2 = st.number_input("X reference 2 value")

    with col2:

        y1 = st.number_input("Y reference 1 value")
        y2 = st.number_input("Y reference 2 value")

    def convert():

        xpix = np.array([p[0] for p in st.session_state.data_points])
        ypix = np.array([p[1] for p in st.session_state.data_points])

        xref = st.session_state.x_refs
        yref = st.session_state.y_refs

        xscale = (x2 - x1) / (xref[1][0] - xref[0][0])
        xoffset = x1 - xscale * xref[0][0]

        # FIXED Y INVERSION
        yscale = (y2 - y1) / (yref[0][1] - yref[1][1])
        yoffset = y1 - yscale * yref[0][1]

        xdata = xscale * xpix + xoffset
        ydata = yscale * ypix + yoffset

        return pd.DataFrame({"x": xdata, "y": ydata})

    if st.button("Generate output"):

        df = convert()

        st.dataframe(df)

        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "digitized_data.csv"
        )

        excel = io.BytesIO()
        df.to_excel(excel, index=False)

        st.download_button(
            "Download Excel",
            excel.getvalue(),
            "digitized_data.xlsx"
        )
