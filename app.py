import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
from PIL import Image
import io
import json
import streamlit as st

st.set_page_config(
    page_title="Scientific Plot Digitizer",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Scientific Plot Digitizer")

st.markdown("""
**Developed by Manasij Yadava**

Extract numerical data from plots using interactive point selection.

Features:
- Zoom and pan
- Click-to-select points
- Automatic scaling
- Export to CSV and Excel
- Save and reload sessions
""")

st.set_page_config(layout="wide")

st.title("Scientific Plot Digitizer")

# --------------------------
# Session state initialization
# --------------------------

def init_session():
    if "x_refs" not in st.session_state:
        st.session_state.x_refs = []

    if "y_refs" not in st.session_state:
        st.session_state.y_refs = []

    if "data_points" not in st.session_state:
        st.session_state.data_points = []

    if "mode" not in st.session_state:
        st.session_state.mode = "data"

init_session()

# --------------------------
# Sidebar controls
# --------------------------

st.sidebar.header("Controls")

mode = st.sidebar.radio(
    "Select mode",
    ["x_ref", "y_ref", "data"],
    format_func=lambda x: {
        "x_ref": "X reference points",
        "y_ref": "Y reference points",
        "data": "Data points"
    }[x]
)

st.session_state.mode = mode

num_points = st.sidebar.number_input(
    "Max data points",
    min_value=1,
    value=50
)

# Undo button
if st.sidebar.button("Undo last point"):

    if mode == "x_ref" and st.session_state.x_refs:
        st.session_state.x_refs.pop()

    elif mode == "y_ref" and st.session_state.y_refs:
        st.session_state.y_refs.pop()

    elif mode == "data" and st.session_state.data_points:
        st.session_state.data_points.pop()

# Reset button
if st.sidebar.button("Reset session"):

    st.session_state.x_refs = []
    st.session_state.y_refs = []
    st.session_state.data_points = []

# Save session
if st.sidebar.button("Save session"):

    session_data = {
        "x_refs": st.session_state.x_refs,
        "y_refs": st.session_state.y_refs,
        "data_points": st.session_state.data_points
    }

    st.sidebar.download_button(
        "Download session file",
        json.dumps(session_data),
        "session.json"
    )

# Load session
uploaded_session = st.sidebar.file_uploader(
    "Load session",
    type=["json"]
)

if uploaded_session:

    session_data = json.load(uploaded_session)

    st.session_state.x_refs = session_data["x_refs"]
    st.session_state.y_refs = session_data["y_refs"]
    st.session_state.data_points = session_data["data_points"]

# --------------------------
# Upload image
# --------------------------

uploaded_image = st.file_uploader(
    "Upload image",
    type=["png", "jpg", "jpeg"]
)

if uploaded_image is None:
    st.stop()

image = Image.open(uploaded_image)
img_array = np.array(image)

height, width = img_array.shape[:2]

# --------------------------
# Plotly figure (zoom/pan enabled)
# --------------------------

fig = go.Figure()

fig.add_layout_image(
    dict(
        source=image,
        xref="x",
        yref="y",
        x=0,
        y=0,
        sizex=width,
        sizey=height,
        sizing="stretch",
        layer="below"
    )
)

fig.update_xaxes(range=[0, width])
fig.update_yaxes(range=[height, 0])

fig.update_layout(
    dragmode="pan",
    width=900,
    height=700
)

# Plot existing points with numbering

def plot_points(points, color, label):

    if points:

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        fig.add_trace(go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            marker=dict(color=color, size=10),
            text=[f"{label}{i+1}" for i in range(len(points))],
            textposition="top center"
        ))

plot_points(st.session_state.x_refs, "red", "X")
plot_points(st.session_state.y_refs, "green", "Y")
plot_points(st.session_state.data_points, "blue", "P")

# --------------------------
# Capture click events
# --------------------------

clicks = plotly_events(fig, click_event=True)

if clicks:

    x = clicks[0]["x"]
    y = clicks[0]["y"]

    if mode == "x_ref" and len(st.session_state.x_refs) < 2:
        st.session_state.x_refs.append([x, y])

    elif mode == "y_ref" and len(st.session_state.y_refs) < 2:
        st.session_state.y_refs.append([x, y])

    elif mode == "data" and len(st.session_state.data_points) < num_points:
        st.session_state.data_points.append([x, y])

    st.rerun()

# --------------------------
# Scaling input
# --------------------------

if len(st.session_state.x_refs) == 2 and len(st.session_state.y_refs) == 2:

    st.header("Scaling parameters")

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
            st.session_state.x_refs[1][0] - st.session_state.x_refs[0][0]
        )

        xoffset = x1 - xscale * st.session_state.x_refs[0][0]

        yscale = (y2 - y1) / (
            st.session_state.y_refs[1][1] - st.session_state.y_refs[0][1]
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

        # CSV download
        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "data.csv"
        )

        # Excel download
        excel_buffer = io.BytesIO()

        df.to_excel(excel_buffer, index=False)

        st.download_button(
            "Download Excel",
            excel_buffer.getvalue(),
            "data.xlsx"
        )

