import streamlit as st
import streamlit.components.v1 as components

from supabase import create_client
from dotenv import load_dotenv

import os
import time
import random
import pickle
import base64
import io

import pandas as pd
import requests
from datetime import datetime

import barcode
from barcode.writer import ImageWriter

from dotenv import load_dotenv 
load_dotenv()
# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(page_title="Parcel System", layout="wide")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# ✅ ADD THIS HERE
def load_global_css():
    st.markdown("""
    <style>
   /* ------- input box --------*/
    /* Input box container */
    div[data-baseweb="input"] > div {
        background-color: #FFFFFF !important;  /* White background */
        border: 2px solid #1E5AA8 !important;  /* Blue border */
        border-radius: 8px;
    }

    /* Input text */
    div[data-baseweb="input"] input {
        color: #000000 !important;  /* Black text */
    }

    /* Placeholder text */
    div[data-baseweb="input"] input::placeholder {
        color: #666666 !important;  /* Slight gray */
    }

    /* Focus effect */
    div[data-baseweb="input"] > div:focus-within {
        border: 2px solid #0D3C84 !important;  /* Darker blue on click */
    }

    /* -------- GLOBAL BACKGROUND -------- */
    .stApp {
        background-color: #FFFFFF !important;
        color: #1A1A1A;
    }
    
    /* Remove default grey from main container */
    .main {
        background-color: #FFFFFF !important;
    }
    
    /* Extra safety (Streamlit layers) */
    section.main > div {
        background-color: #FFFFFF !important;
    }

    header {visibility:hidden;}

    /* -------- LAYOUT SPACING -------- */
    .block-container {
        padding-top: 70px;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* -------- SIDEBAR -------- */
    [data-testid="stSidebar"] {
        position: fixed;
        top: 60px;
        width: 260px;
        height: calc(100vh - 60px);
        background: #1E5AA8;
        border-right: 2px solid #0B3D91;
    }

    section.main > div {
        margin-left: 260px;
        margin-top: 60px;
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF;
    }

    /* -------- SELECTBOX -------- */
    div[data-baseweb="select"] > div {
        background-color: #1E5AA8 !important;
        color: #FFFFFF !important;
        border-radius: 8px;
    }

    ul {
        background-color: #FFFFFF !important;
        color: #1E5AA8 !important;
    }

    /* -------- BUTTON -------- */
    .stButton > button {
        background-color: #0B3D91;
        color: #FFFFFF;
        border-radius: 8px;
        border: none;
        font-weight: 500;
    }

    .stButton > button:hover {
        transition: background-color 0.4s;
        background-color:  #4169E1;
        color: #FFFFFF;
    }

    /* -------- NAVBAR -------- */
    .navbar {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 60px;
        background: #0B3D91;
        display: flex;
        align-items: center;
        padding: 0px 30px;
        z-index: 1000;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.15);
    }

    .logo {
        display: flex;
        align-items: center;
    }

    .logo img {
        width: 42px;
        margin-right: 10px;
    }

    .logo-text {
        color: #FFFFFF;
        font-size: 20px;
        font-weight: bold;
    }

    /* -------- FORM / CARD -------- */
    div[data-testid="stForm"] {
        background-color: #FFFFFF;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    }

    /* -------- GENERAL CARD -------- */
    .card {
        background: #FFFFFF;
        border-left: 5px solid #2E8B57;
        padding: 15px;
        border-radius: 10px;
        color: #1A1A1A;
    }

    /* -------- HEADINGS -------- */
    h1, h2, h3, h4 {
        color: #0B3D91;
    }
    /* Form submit button */
    div[data-testid="stFormSubmitButton"] button {
        background-color: #FFFFFF !important;  /* White background */
        color: #000000 !important;            /* Black text */
        border: 2px solid #1E5AA8 !important; /* Blue border */
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
    }

    /* Hover effect */
    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #1E5AA8 !important; /* Blue background */
        color: #FFFFFF !important;            /* White text */
    }

    /* Click (active) effect */
    div[data-testid="stFormSubmitButton"] button:active {
        background-color: #0D3C84 !important; /* Darker blue */
        color: #FFFFFF !important;
    }



    </style>
    """, unsafe_allow_html=True)



load_global_css()


supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        st.error("❌ Missing Supabase ENV variables")
except Exception as e:
    st.error(f"Supabase error: {e}")
# -------------------------------
# SESSION
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

if "username" not in st.session_state:
    st.session_state.username = None

# -------------------------------
# UTILITIES
# -------------------------------
def style_dataframe(df):
    # Step 1: Clean column names
    df.columns = [col.replace("_", " ").title() for col in df.columns]

    # Step 2: Rename properly
    rename_map = {
        "Oprsno": "Bus No",
        "Servicedocid": "Service ID",
        "Scheduledarrival": "Scheduled Arrival",
        "Servicestarttime": "Start Time",
        "Serviceendtime": "End Time",
        "Sourcename": "Source",
        "Destinationname": "Destination"
    }
    df.rename(columns=rename_map, inplace=True)

    # ✅ Step 3: REMOVE DUPLICATES (CRITICAL FIX)
    df = df.loc[:, ~df.columns.duplicated()]

    # Styling
    try:
        return df.style.set_properties(**{
            'background-color': '#f9f9f9',
            'color': '#151b54',
            'border-color': '#ddd',
            'text-align': 'center'
        }).set_table_styles([
            {'selector': 'th', 'props': [('background-color', 'crimson'), ('color', 'white'), ('font-weight', 'bold')]},
            {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#f2f2f2')]}
        ])
    except Exception:
        return df

# -------------------------------
# ORDER PAGE
# -------------------------------
def order_page():

    url = "https://suryavardhanc8-apsrtc-api.hf.space/route"
    # -------------------------------
    # Page Config
    # -------------------------------
    # Removed to avoid StreamlitAPIException

    # -------------------------------
    # Session State
    # -------------------------------
    if "order" not in st.session_state:
        st.session_state.order = None

    if "parcel_id" not in st.session_state:
        st.session_state.parcel_id = None

    if "invoice_ready" not in st.session_state:
        st.session_state.invoice_ready = False

    if "confirmed_path" not in st.session_state:
        st.session_state.confirmed_path = None

    # -------------------------------
    # Styling
    # -------------------------------

    # -------------------------------
    # Images
    # -------------------------------
    LOGO_URL = "https://play-lh.googleusercontent.com/lN7A23bINlQu9l8ab9QrlJJpAMs3FtOqj7Z5qlz4YCrTvDc2_4pIg4fg2f89hJUZ0Rw"
    BANNER_URL = "https://images.railyatri.in/ry_images_prod/APSRTC-1603954318.png"

    # -------------------------------
    # Navbar
    # -------------------------------
    st.markdown(f"""
    <div class="navbar">

    <div class="logo">
    <img src="{LOGO_URL}">
    <div class="logo-text">APSRTC Parcel</div>
    </div>

    <div class="nav-items">
    
    </div>

    </div>""", unsafe_allow_html=True)

    # -------------------------------
    # Load Environment
    # -------------------------------


    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # -------------------------------
    # Load Places
    # -------------------------------
    try:
        places_df = pd.read_csv("data.csv")
    except:
        st.error("❌ data.csv not found")
        st.stop()

    try:
        with open("apsrtc_main_graph.pkl","rb") as f:
            g = pickle.load(f)
    except:
        st.error("❌ graph file missing")
        st.stop()

    places_df = places_df[places_df["placeId"].isin(g.nodes)]

    place_names = places_df["placeName"].unique().tolist()

    # -------------------------------
    # Parcel ID Generator
    # -------------------------------
    def generate_parcel_id(source,destination):

        src = source[:3].upper()
        dest = destination[:3].upper()

        number = random.randint(10000,99999)

        return f"{src}-{dest}-{number}"

    # -------------------------------
    # Barcode Generator
    # -------------------------------
    def generate_barcode_base64(data):

        CODE128 = barcode.get_barcode_class("code128")
        writer = ImageWriter()

        barcode_obj = CODE128(data, writer=writer)

        buffer = io.BytesIO()

        barcode_obj.write(
            buffer,
            {
                "module_width":0.3,
                "module_height":15,
                "font_size":12,
                "text_distance":5,
                "quiet_zone":6
            }
        )

        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode()


    # -------------------------------
    # Invoice Generator
    # -------------------------------
    def generate_invoice_html(order, path=None):

        barcode_image = generate_barcode_base64(order["order_id"])

        path_html = ""
        if path:
            stops = [leg["sourceName"] for leg in path]
            stops.append(path[-1]["destinationName"])
            path_str = " ➝ ".join(stops)
            path_html = f"""
            <tr>
            <th colspan="1">Selected Route</th>
            <td colspan="3">{path_str}</td>
            </tr>
            """

        html = f"""
    <html>
    <head>

    <style>

    body {{
        font-family:'Segoe UI',Arial;
        background:#f4f6fa;
        padding:30px;
    }}

    .container {{
        max-width:900px;
        margin:auto;
        background:white;
        padding:30px;
        border-radius:12px;
        box-shadow:0px 10px 30px rgba(0,0,0,0.15);
    }}

    .header {{
        text-align:center;
        border-bottom:4px solid crimson;
        padding-bottom:10px;
    }}

    .header h2 {{
        color:crimson;
    }}

    table {{
        width:100%;
        border-collapse:collapse;
        margin-top:20px;
    }}

    th {{
        background:crimson;
        color:white;
        padding:10px;
        text-align:left;
    }}

    td {{
        padding:10px;
        border:1px solid #ddd;
    }}

    .barcode-section {{
        text-align:center;
        margin-top:30px;
        background:#f4f6fa;
        padding:20px;
        border-radius:10px;
    }}

    .barcode-section img {{
        width:350px;
    }}

    </style>

    </head>

    <body>

    <div class="container">

    <div class="header">

    <img src="{LOGO_URL}" width="90">

    <h2>APSRTC Parcel Invoice</h2>

    </div>

    <table>

    <tr>
    <th>Order ID</th>
    <td>{order['order_id']}</td>

    <th>Booking Date</th>
    <td>{order['booking_date']}</td>
    </tr>

    <tr>
    <th>Customer</th>
    <td>{order['customer_name']}</td>

    <th>Phone</th>
    <td>{order['customer_phone']}</td>
    </tr>

    <tr>
    <th>From</th>
    <td>{order['source_place']} ({order['source_id']})</td>

    <th>To</th>
    <td>{order['destination_place']} ({order['destination_id']})</td>
    </tr>

    {path_html}

    </table>

    <div class="barcode-section">

    <h3>Tracking Barcode</h3>

    <img src="data:image/png;base64,{barcode_image}">

    <p><b>{order['order_id']}</b></p>

    </div>

    </div>

    </body>

    </html>
    """

        return html
    
    # -------------------------------
    # Layout
    # -------------------------------
    col1,col2 = st.columns([1.3,1])

    with col1:
        st.image(BANNER_URL,width=800)

    with col2:

        with st.form("parcel_form"):

            st.subheader("Book Your Parcel")

            customer_name = st.text_input("Customer Name")
            customer_phone = st.text_input("Customer Phone")
            
            st.markdown("""
            <style>
            
            /* ---------- SELECT BOX ---------- */
            div[data-baseweb="select"] > div {
                background-color: #FFFFFF !important;
                border: 2px solid #1E5AA8 !important;
                border-radius: 8px;
                color: #1A1A1A !important;
            }
            
            /* Selected value */
            div[data-baseweb="select"] span {
                color: #1A1A1A !important;
            }
            
            /* ---------- REMOVE FADED EFFECT ---------- */
            div[data-baseweb="popover"],
            div[data-baseweb="menu"],
            ul[role="listbox"] {
                opacity: 1 !important;
                background-color: #FFFFFF !important;
                filter: none !important;
                backdrop-filter: none !important;
            }
            
            /* ---------- OPTIONS ---------- */
            ul[role="listbox"] li {
                color: #1A1A1A !important;
                background-color: #FFFFFF !important;
            }
            
            /* Hover */
            ul[role="listbox"] li:hover {
                background-color: #E6F0FA !important;
                color: #1A1A1A !important;
            }
            
            /* Selected */
            ul[role="listbox"] li[aria-selected="true"] {
                background-color: #D0E2FF !important;
                color: #1A1A1A !important;
            }
            
            /* ---------- FIX DIM OVERLAY (IMPORTANT) ---------- */
            body > div {
                opacity: 1 !important;
            }
            
            /* Remove any gray overlay layer */
            div[style*="opacity"] {
                opacity: 1 !important;
            }
            
            </style>
            """, unsafe_allow_html=True)

            source_place = st.selectbox("Source",place_names)
            destination_place = st.selectbox("Destination",place_names)

            submit = st.form_submit_button("Book Parcel")

    # -----------------------------------
    # SESSION INIT
    # -----------------------------------
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if "routes_data" not in st.session_state:
        st.session_state.routes_data = None

    if "selected_route" not in st.session_state:
        st.session_state.selected_route = None

    if "invoice_ready" not in st.session_state:
        st.session_state.invoice_ready = False

    if "confirmed_path" not in st.session_state:
        st.session_state.confirmed_path = None

    # -----------------------------------
    # STEP 1: BOOKING
    # -----------------------------------
    if submit:
        if source_place == destination_place:
            st.error("Source and Destination cannot be same")
            st.stop()

        source_id = places_df.loc[
            places_df["placeName"] == source_place, "placeId"
        ].values[0]

        destination_id = places_df.loc[
            places_df["placeName"] == destination_place, "placeId"
        ].values[0]

        # Generate parcel ID
        st.session_state.parcel_id = generate_parcel_id(source_place, destination_place)

        order = {
            "order_id": st.session_state.parcel_id,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "source_place": source_place,
            "destination_place": destination_place,
            "source_id": str(source_id),
            "destination_id": str(destination_id),
            "booking_date": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        }

        if supabase is None:
            st.error("Supabase is not configured. Please set SUPABASE_URL and SUPABASE_KEY in a .env file.")
            st.stop()

        # Save to DB
        supabase.table("orders").insert({
            "order_id": order["order_id"],
            "customer_name": order["customer_name"],
            "customer_phone": order["customer_phone"],
            "source_place": order["source_place"],
            "destination_place": order["destination_place"],
            "source_id": order["source_id"],
            "destination_id": order["destination_id"]
        }).execute()

        # Store state
        st.session_state.order = order
        st.session_state.submitted = True
        st.session_state.routes_data = None  # reset routes

        st.success("Parcel booked successfully!")

    # -----------------------------------
    # STEP 2: ROUTE SELECTION
    # -----------------------------------
    if st.session_state.submitted:

        order = st.session_state.order

        st.divider()
        st.subheader("🚍 Select Route")

        # API CALL (ONLY ONCE)
        if st.session_state.routes_data is None:
            with st.spinner("Loading routes..."):

                try:
                    response = requests.get(
                        url,
                        params={
                            "source": order["source_id"],
                            "target": order["destination_id"]
                        }
                    )

                    st.session_state.routes_data = response.json()
                except Exception as e:

                    st.error(f"API Error: {e}")
                    st.stop()

        data_ = st.session_state.routes_data or {}
        paths = data_.get("all_possible_paths", [])

        if not paths:
            st.error("No routes found")

        else:
            st.success(f"{len(paths)} routes available")

            labels = []
            mapping = {}

            for i, path in enumerate(paths):
                stops = [leg["sourceName"] for leg in path]
                stops.append(path[-1]["destinationName"])

                label = f"Route {i+1}: {' ➝ '.join(stops)}"
                labels.append(label)
                mapping[label] = path

            # SAFE DEFAULT
            if st.session_state.selected_route not in labels:
                st.session_state.selected_route = labels[0]

            selected = st.radio(
                "Select Route",
                labels,
                index=labels.index(st.session_state.selected_route)
            )

            st.session_state.selected_route = selected
            selected_path = mapping[selected]

            # -----------------------------------
            # SHOW SELECTED ROUTE
            # -----------------------------------
            st.subheader("🛣 Selected Route")

            for leg in selected_path:
                st.markdown(f"""
                <div style="background:#e6f2ff;padding:15px;border-radius:10px;margin:10px;border-left:5px solid #1f77b4;">
                <b>{leg['sourceName']} ➝ {leg['destinationName']}</b><br>
                🚌 Bus: {leg['oprsNo']}<br>
                ⏱ {str(leg['serviceStartTime'])[:10]+"  "+str(leg['serviceStartTime'])[11:]} → {leg['serviceEndTime']}
                </div>
                """, unsafe_allow_html=True)

            # -----------------------------------
            # CONFIRM BUTTON
            # -----------------------------------
            if st.button("🚚 Confirm Route & Save Path"):

                for leg in selected_path:
                    row = {
                        "servicedocid": leg["serviceDocId"],
                        "sourcename": leg["sourceName"],
                        "destinationname": leg["destinationName"],
                        "servicestarttime": leg["serviceStartTime"],
                        "serviceendtime": leg["serviceEndTime"],
                        "oprsno": leg["oprsNo"],
                        "scheduledarrival": leg.get("scheduledArrival"),
                        "order_id": st.session_state.parcel_id
                    }

                    try:
                        supabase.table("order_path").insert(row).execute()
                    except Exception as e:
                        st.error(f"Database Error: {e}")

                st.session_state.invoice_ready = True
                st.session_state.confirmed_path = selected_path
                st.rerun()

    # -----------------------------------
    # STEP 3: INVOICE
    # -----------------------------------
    if st.session_state.invoice_ready:

        st.divider()
        st.subheader("📄 Parcel Booking Invoice")

        order = st.session_state.order
        path = st.session_state.confirmed_path

        invoice_html = generate_invoice_html(order, path)

        st.components.v1.html(invoice_html, height=700)

        st.download_button(
            "⬇ Download Invoice",
            data=invoice_html,
            file_name=f"Invoice_{order['order_id']}.html",
            mime="text/html"
        )
# -------------------------------
# SCAN PAGE
# -------------------------------
def scan_page():

    url = "https://suryavardhanc8-apsrtc-api.hf.space/route"

    # -------------------------------
    # Page Config
    # -------------------------------
    # Removed to avoid StreamlitAPIException

    # -------------------------------
    # Session State
    # -------------------------------
    if "order" not in st.session_state:
        st.session_state.order = None

    if "parcel_id" not in st.session_state:
        st.session_state.parcel_id = None

    # -------------------------------
    # Styling
    # -------------------------------

    # -------------------------------
    # Images
    # -------------------------------
    LOGO_URL = "https://play-lh.googleusercontent.com/lN7A23bINlQu9l8ab9QrlJJpAMs3FtOqj7Z5qlz4YCrTvDc2_4pIg4fg2f89hJUZ0Rw"
    BANNER_URL = "https://images.railyatri.in/ry_images_prod/APSRTC-1603954318.png"

    # -------------------------------
    # Navbar
    # -------------------------------
    st.markdown(f"""
    <div class="navbar">

    <div class="logo">
    <img src="{LOGO_URL}">
    <div class="logo-text">APSRTC Parcel</div>
    </div>

    <div class="nav-items">

    </div>

    </div>
    """, unsafe_allow_html=True)

    # -------------------------------
    # Load Environment
    # -------------------------------



    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            st.error(f"Supabase client init failed: {e}")
            return
    else:
        st.error("Supabase is not configured. Please set SUPABASE_URL and SUPABASE_KEY in a .env file.")
        return

    # -------------------------------
    # Load Places
    # -------------------------------
    places_df = pd.read_csv("data.csv")

    with open("apsrtc_main_graph.pkl","rb") as f:
        g = pickle.load(f)

    places_df = places_df[places_df["placeId"].isin(g.nodes)]

    place_names = places_df["placeName"].unique().tolist()

    col1,col2 = st.columns([1.3,1])

    with col1:
        st.image(BANNER_URL,width=800)
    with col2:

        with st.form("parcel_form"):

            st.subheader("Transmit Parcel")

            barcodeid = st.text_input("Parcel Id:")
            sourcename = st.selectbox("Place:", place_names)

            submit = st.form_submit_button("Submit")

    if submit:
        st.markdown("""
            <style>
            .card {
                background-color: #1e1e2f;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                color: white;
                margin-bottom: 20px;
            }
            .title {
                font-size: 20px;
                font-weight: bold;
                color: #00d4ff;
            }
            .label {
                font-weight: bold;
                color: #bbbbbb;
            }
            .value {
                font-size: 18px;
                margin-bottom: 8px;
            }
            .success {
                color: #00ff9c;
                font-weight: bold;
            }
            .warning {
                color: orange;
                font-weight: bold;
            }
            .error {
                color: red;
                font-weight: bold;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="card">
                <div class="title">📦 Order Details</div>
                <div class="label">ID:</div>
                <div class="value">{barcodeid}</div>
                <div class="label">Place:</div>
                <div class="value">{sourcename}</div>
            </div>
        """, unsafe_allow_html=True)

        try:
            # STEP 1: FETCH servicedocid
            response = supabase.table("order_path") \
                .select("servicedocid") \
                .eq("order_id", barcodeid) \
                .eq("sourcename", sourcename) \
                .execute()

            if response.data:

                servicedocid = response.data[0]["servicedocid"]

                check = supabase.table("track") \
                    .select("*") \
                    .eq("order_id", barcodeid) \
                    .execute()

                if check.data:
                    supabase.table("track") \
                        .update({"presentservicedocid": servicedocid}) \
                        .eq("order_id", barcodeid) \
                        .execute()

                    st.markdown('<div class="success">✅ Updated Successfully</div>', unsafe_allow_html=True)

                else:
                    supabase.table("track") \
                        .insert({
                            "order_id": barcodeid,
                            "presentservicedocid": servicedocid
                        }) \
                        .execute()

                    st.markdown('<div class="success">✅ Inserted Successfully</div>', unsafe_allow_html=True)

            else:
                st.markdown('<div class="warning">⚠️ No matching record found</div>', unsafe_allow_html=True)

            # STEP 2: FETCH destination + time
            response = supabase.table("order_path") \
                .select("destinationname,servicestarttime") \
                .eq("order_id", barcodeid) \
                .eq("sourcename", sourcename) \
                .execute()

            if response.data:
                destinationname = response.data[0]["destinationname"]
                servicestarttime = response.data[0]["servicestarttime"]

                st.markdown(f"""
                    <div class="card">
                        <div class="title">🚚 Travel Info</div>
                        <div class="label">Destination:</div>
                        <div class="value">{destinationname}</div>
                        <div class="label">Bus Time:</div>
                        <div class="value">{str(servicestarttime)[-8:]}</div>
                    </div>
                """, unsafe_allow_html=True)

            else:
                st.markdown('<div class="warning">⚠️ No matching record found</div>', unsafe_allow_html=True)

        except Exception as e:
            st.markdown(f'<div class="error">❌ Error: {e}</div>', unsafe_allow_html=True)
# ----------------------------------------------------------------------------------------------------------------------------------------
# TRACK PAGE (PUBLIC)
# -------------------------------
def track_page():


    # -------------------------------
    # LOAD ENV
    # -------------------------------



    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # -------------------------------
    # PAGE CONFIG
    # -------------------------------
    # Removed to avoid StreamlitAPIException

    # -------------------------------
    # SESSION STATE
    # -------------------------------
    if "order" not in st.session_state:
        st.session_state.order = None

    if "parcel_id" not in st.session_state:
        st.session_state.parcel_id = None

    # -------------------------------
    # STYLING
    # -------------------------------

    # -------------------------------
    # NAVBAR
    # -------------------------------
    LOGO_URL = "https://play-lh.googleusercontent.com/lN7A23bINlQu9l8ab9QrlJJpAMs3FtOqj7Z5qlz4YCrTvDc2_4pIg4fg2f89hJUZ0Rw"

    st.markdown(f"""
    <div class="navbar">

    <div class="logo">
    <img src="{LOGO_URL}">
    <div class="logo-text">APSRTC Parcel</div>
    </div>

    <div class="nav-items">

    </div>

    </div>
    """, unsafe_allow_html=True)

    # -------------------------------
    # TITLE
    # -------------------------------
    st.markdown("<h1 style='color:#0B3D91;;'>Track Your Parcel</h1>", unsafe_allow_html=True)

    # -------------------------------
    # INPUT
    # -------------------------------
    st.markdown("""
    <style>
    /* Target text input box */
    div[data-baseweb="input"] > div {
        border: 2px solid #4169E1;  /* Change color here */
        border-radius: 8px;
    }

    /* On focus (when clicked) */
    div[data-baseweb="input"] > div:focus-within {
        border: 2px solid #4169E1;  /* Focus color */
        box-shadow: 0 0 5px #4169E1;
    }
    </style>
    """, unsafe_allow_html=True)

    # Input field
    order_id = st.text_input("Enter Order ID")

    # -------------------------------
    # FUNCTIONS
    # -------------------------------
    def get_doc_id(order_id):
        try:
            res = supabase.table("track") \
                .select("presentservicedocid") \
                .eq("order_id", order_id) \
                .execute()

            if res.data:
                return res.data[0]["presentservicedocid"]
            return None
        except:
            return None


    def get_source(order_id):
        try:
            res = supabase.table("order_path") \
                .select("sourcename") \
                .eq("order_id", order_id) \
                .execute()

            if res.data:
                return res.data[0]["sourcename"]
            return None
        except:
            return None


    def fetch_bus_data(doc_id):
        url = "https://utsappapicached01.apsrtconline.in/uts-vts-api/servicewaypointdetails/bydocid"

        try:
            response = requests.post(url, json={"docId": doc_id})
            data = response.json()

            if "data" not in data:
                return None

            return data["data"]
        except:
            return None


    def render_stops(stops, source , destination ):

        stops = sorted(stops, key=lambda x: x["seqNo"])
        current_index = -1
        for i, stop in enumerate(stops):
            if stop.get("vtsArrivalTime"):
                current_index = i
        
        filtered_stops = []
        enter=0

        #st.write(source,"-->",destination)

        for i, stop in enumerate(stops):
            #st.write(stop.get("wayPointName",""),"all")
            if stop.get("wayPointName","")==source:
                enter=1
                filtered_stops.append(stop)
                #st.write(stop.get("wayPointName",""),"source")
            elif stop.get("wayPointName","")==destination:
                filtered_stops.append(stop)
                #st.write(stop.get("wayPointName",""),"destination")
                enter=0
            else:
                if enter==1:
                    filtered_stops.append(stop)
                    #st.write(stop.get("wayPointName",""),"intermediate")



        # -------------------------------
        # COLLECT ALL HTML FIRST
        # -------------------------------
        all_items_html = ""
        if len(filtered_stops) <=2:
            stops_list = filtered_stops
        else:
            stops_list = stops
        for i, stop in enumerate(filtered_stops):

            # -------------------------------
            # STATUS LOGIC
            # -------------------------------
            if i < current_index:
                status = "Left"
                color = "#273c75"
                icon = ""
            elif i == current_index:
                status = "Current Stop"
                color = "#dfe6e9"
                icon = "🚌"
            else:
                status = "Upcoming"
                color = "#55efc4"
                icon = ""

            if i == len(stops) - 1:
                status = "Destination"

            # -------------------------------
            # ETA
            # -------------------------------
            eta = ""
            if stop.get("ETA") and i > current_index:
                try:
                    t = datetime.fromisoformat(stop["ETA"])
                    eta = f"ETA: {t.strftime('%H:%M')}"
                except:
                    pass

            # -------------------------------
            # EACH ROW (NO LINE HERE)
            # -------------------------------
            item_html = f"""
            <div style="display:flex;align-items:center;margin:50px 0; position:relative; z-index:1;">

                <!-- LEFT TIME -->
                <div style="width:100px;text-align:right;font-weight:bold;">
                    {stop.get("scheduleArrTime","")}
                    <div style="color:red;font-size:12px;">{eta}</div>
                </div>

                <!-- TIMELINE (DOT ONLY) -->
                <div style="width:60px;display:flex;justify-content:center; position:relative;">
                    <div style="
                        width:28px;
                        height:28px;
                        border-radius:50%;
                        background:{color};
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        z-index:2;
                    ">
                        {icon}
                    </div>
                </div>

                <!-- STOP INFO -->
                <div style="flex:1;padding-left:10px;">
                    <div style="font-weight:bold;">{stop.get("wayPointName","")}</div>
                    <div style="font-size:13px;color:#273c75;">{status}</div>
                </div>

                <!-- RIGHT TIME -->
                <div style="width:100px;text-align:left;font-weight:bold;color:green;">
                    {stop.get("placeTime","")}
                </div>

            </div>
            """

            all_items_html += item_html

        # -------------------------------
        # FINAL HTML WITH ONE CONTINUOUS LINE
        # -------------------------------
        final_html = f"""
        <div style="position:relative; padding:10px 0;">

            <!-- CONTINUOUS LINE -->
            <div style="
                position:absolute;
                top:0;
                bottom:0;
                left:130px;
                width:3px;
                background:#2f3640;
                z-index:0;
            "></div>

            {all_items_html}

        </div>
        """

        # -------------------------------
        # RENDER ONCE (IMPORTANT)
        # -------------------------------
        st.components.v1.html(final_html, height=120 * len(stops))
        












        
    # BUTTON ACTION
    # -------------------------------
    # -------------------------------
    # BUTTON ACTION
    # -------------------------------
    if st.button("Track Order"):

        if not order_id:
            st.warning("Please enter correct Order ID")

        else:
            # 🔥 NEW: FETCH FULL ORDER PATH DATA
            try:
                res = supabase.table("order_path") \
                    .select("*") \
                    .eq("order_id", order_id) \
                    .execute()

                st.subheader("Parcel Path")
                df = pd.DataFrame(res.data)

                # ✅ remove duplicates
                df = df.loc[:, ~df.columns.duplicated()]

                # ✅ then style / use
                df_clean = df.copy()

                # ✅ rename manually (SAFE)
                df_clean = df_clean.rename(columns={
                    "sourcename": "Source",
                    "destinationname": "Destination",
                    "servicestarttime": "Start Time",
                    "scheduledarrival": "Scheduled Arrival",
                    "servicedocid": "Service ID"
                })

                # ✅ now safely select columns
                required_cols = ["Source", "Destination", "Start Time", "Scheduled Arrival", "Service ID"]

                missing = [col for col in required_cols if col not in df_clean.columns]

                if missing:
                    st.error(f"Missing columns: {missing}")
                    st.write("Available columns:", df_clean.columns.tolist())
                    st.stop()

                df_clean = df_clean[required_cols]



                # -------------------------------
                  # SAMPLE DATA (replace with your df)
                # -------------------------------

                # Convert datetime
                # Convert datetime (USE df_clean ✅)
                df_clean["Start Time"] = pd.to_datetime(df_clean["Start Time"], errors="coerce")
                df_clean["Scheduled Arrival"] = pd.to_datetime(df_clean["Scheduled Arrival"], errors="coerce")

                current_time = datetime.now()

                def get_status(row):
                    if current_time > row["Scheduled Arrival"]:
                        return "completed"
                    elif row["Start Time"] <= current_time <= row["Scheduled Arrival"]:
                        return "running"
                    else:
                        return "upcoming"

                df_clean["status"] = df_clean.apply(get_status, axis=1)

                # -------------------------------
                # CSS (PRO UI)
                # ------------------------------

                st.markdown('<div class="header">Route Tracking</div>', unsafe_allow_html=True)

                # -------------------------------
                # BUILD UI
                # -------------------------------
                html_ = """
                <style>
                body {
                    background-color: #f4f6f9;
                }
                .timeline {
                    position: relative;
                    margin: 20px;
                }
                .timeline::before {
                    content: '';
                    position: absolute;
                    left: 25px;
                    width: 4px;
                    height: 100%;
                    background: #dcdcdc;
                }
                .step {
                    display: flex;
                    align-items: center;
                    margin-bottom: 40px;
                }
                .circle {
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    margin-right: 20px;
                }
                .completed { background-color: #28a745; }
                .running { background-color: #ffc107; }
                .upcoming { background-color: #6c757d; }
                .card {
                    padding: 15px 20px;
                    border-radius: 12px;
                    width: 75%;
                    background: white;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }
                .route {
                    font-size: 18px;
                    font-weight: bold;
                }
                .time {
                    color: #666;
                    font-size: 14px;
                }
                .status {
                    float: right;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 4px 10px;
                    border-radius: 8px;
                }
                .completed-text { background: #d4edda; color: #155724; }
                .running-text { background: #fff3cd; color: #856404; }
                .upcoming-text { background: #e2e3e5; color: #383d41; }
                </style>

                <div class="timeline">
                """

                for _, row in df_clean.iterrows():
                    status_class = row["status"]

                    html_ += f"""
                    <div class="step">
                        <div class="circle {status_class}"></div>

                        <div class="card">
                            <div class="route">
                                {row['Source']} ➝ {row['Destination']}
                                <span class="status {status_class}-text">
                                    {row['status'].upper()}
                                </span>
                            </div>

                            <div class="time">
                                {row['Start Time'].strftime('%d %b %H:%M')}
                                →
                                {row['Scheduled Arrival'].strftime('%d %b %H:%M')}
                            </div>
                        </div>
                    </div>
                    """

                html_ += "</div>"

                components.html(html_, height=600, scrolling=True)





            except Exception as e:
                st.error(f"Error fetching order_path: {e}")

            # -------------------------------
            # EXISTING LOGIC
            # -------------------------------
            doc_id = get_doc_id(order_id)

            if doc_id:
                row = df_clean[df_clean['Service ID'] == doc_id]

                if row.empty:
                    st.error("❌ Service ID not found in path")
                    st.stop()

                source = row['Source'].iloc[0]
                destination = row['Destination'].iloc[0]
                placeholder = st.empty()

                while True:

                    with placeholder.container():

                        st.info("Fetching live location...")

                        data = fetch_bus_data(doc_id)

                        if not data:
                            st.error("No route data found")
                            st.write("Doc ID:", doc_id)
                        else:
                            st.markdown("<h3 style='color:#0B3D91;;'>Parcel live location</h3>", unsafe_allow_html=True)
                            render_stops(data,source,destination)

                    time.sleep(10)

            else:
                source = get_source(order_id)

                if source:
                    st.warning(f"📍 Parcel is still at: {source}")
                else:
                    st.error("❌ Invalid Order ID. Please check again.")

# -------------------------------
# CUSTOM CSS (FIXED SIDEBAR + COLORS)
# -------------------------------

# -------------------------------
# SESSION STATE INIT
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""
    st.session_state.menu_choice = "Login"
# -------------------------------
# NAVIGATION (SIDEBAR)
# -------------------------------
LOGO_URL = "https://play-lh.googleusercontent.com/lN7A23bINlQu9l8ab9QrlJJpAMs3FtOqj7Z5qlz4YCrTvDc2_4pIg4fg2f89hJUZ0Rw"

st.sidebar.markdown(f"""
<div style="display: flex; align-items: center; padding: 10px;">
    <h3 style="margin: 0;">MENU</h3>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()


# -------------------------------
# LOGIN FUNCTION
# -------------------------------
def login_page():
    LOGO_URL = "https://play-lh.googleusercontent.com/lN7A23bINlQu9l8ab9QrlJJpAMs3FtOqj7Z5qlz4YCrTvDc2_4pIg4fg2f89hJUZ0Rw"
    
    st.markdown(f"""
    <div class="navbar">
        <div class="logo">
            <img src="{LOGO_URL}">
            <div class="logo-text">APSRTC Parcel</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        with st.form("login_form"):

            st.markdown("<h1 style='text-align:center; color:#0B3D91;'>Govt Staff Login</h1>", unsafe_allow_html=True)

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            st.markdown("""
                <style>
                /* Form submit button */
                div[data-testid="stFormSubmitButton"] button {
                    background-color: #FFFFFF !important;  /* White background */
                    color: #000000 !important;            /* Black text */
                    border: 2px solid #1E5AA8 !important; /* Blue border */
                    border-radius: 8px;
                    padding: 8px 20px;
                    font-weight: 600;
                }
            
                /* Hover effect */
                div[data-testid="stFormSubmitButton"] button:hover {
                    background-color: #1E5AA8 !important; /* Blue background */
                    color: #FFFFFF !important;            /* White text */
                }
            
                /* Click (active) effect */
                div[data-testid="stFormSubmitButton"] button:active {
                    background-color: #0D3C84 !important; /* Darker blue */
                    color: #FFFFFF !important;
                }
                </style>
            """, unsafe_allow_html=True)

            submit = st.form_submit_button("Login")

            if submit:
                if not username or not password:
                    st.warning("Please enter username and password")
                    return

                res = supabase.table("users") \
                    .select("*") \
                    .eq("username", username) \
                    .execute()

                if res.data:
                    user = res.data[0]

                    # ⚠️ NOTE: Replace with hashed password check in production
                    if user["password_hash"] == password:
                        st.session_state.logged_in = True
                        st.session_state.role = user["role"].lower()
                        st.session_state.username = user["full_name"]
                        role = user["role"].lower()

                        if role == "order":
                            st.session_state.menu_choice = "Order Page"

                        elif role in ["scanner", "transmiter"]:
                            st.session_state.menu_choice = "Scan Page"

                        else:
                            st.session_state.menu_choice = "Track Parcel"
                        st.success("Login successful")
                        st.rerun()
                    else:
                        st.error("Wrong password")
                else:
                    st.error("User not found")
# -------------------------------
# MENU LOGIC (BUTTON VERSION - FIXED)
# -------------------------------
if st.session_state.logged_in:

    role = st.session_state.role

    if role == "order":
        menu = ["Order Page", "Track Parcel"]

    elif role in ["scanner", "transmiter"]:
        menu = ["Scan Page", "Track Parcel"]

    else:
        menu = ["Track Parcel"]

else:
    menu = ["Login", "Track Parcel"]


# -------------------------------
# BUTTON NAVIGATION (IMPORTANT FIX)
# -------------------------------
for item in menu:
    if st.sidebar.button(item, use_container_width=True):
        st.session_state.menu_choice = item


# Default selection safety
if "menu_choice" not in st.session_state or st.session_state.menu_choice not in menu:
    st.session_state.menu_choice = menu[0]

choice = st.session_state.menu_choice
st.session_state.menu_choice = choice

# -------------------------------
# USER INFO + LOGOUT
# -------------------------------
if st.session_state.logged_in:
    st.sidebar.markdown(f"**👤 {st.session_state.username}**")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

# -------------------------------
# ROUTING
# -------------------------------
choice = st.session_state.menu_choice

if choice == "Login":
    login_page()

elif choice == "Order Page":
    if st.session_state.role == "order":
        order_page()
    else:
        st.error("Access Denied")

elif choice == "Scan Page":
    if st.session_state.role in ["scanner", "transmiter"]:
        scan_page()
    else:
        st.error("Access Denied")

elif choice == "Track Parcel":
    track_page()
