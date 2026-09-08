import streamlit as st
import paho.mqtt.client as mqtt
import pandas as pd
import time
import requests
from datetime import datetime
import pytz
import os

# 1. Page Configuration
st.set_page_config(
    page_title="Solar PV Monitoring Dashboard",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. CSS Styling
st.markdown("""
<style>
    * { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important; }
    
    /* Transparent overlays */
    .stApp, [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Background styling */
    [data-testid="stAppViewContainer"] { 
        background-image: linear-gradient(rgba(255, 255, 255, 0.80), rgba(240, 248, 255, 0.90)), url('https://images.unsplash.com/photo-1509391365360-2e959784a276?q=85&w=2560&auto=format&fit=crop') !important;
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
    }

    button[data-baseweb="tab"] {
        font-size: 17px !important;
        font-weight: bold !important;
    }

    [data-testid="stAppViewBlockContainer"], .main .block-container {
        max-width: 1050px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        margin: 0 auto !important;
    }

    /* Header Box */
    .header-box {
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 16px 24px;
        border: 1px solid rgba(255, 255, 255, 0.9);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        direction: ltr;
    }
    .header-item { color: #1e293b; font-size: 16px; font-weight: bold; }
    .header-highlight { color: #2563eb; font-weight: bold; font-family: 'Times New Roman', serif !important; }

    [data-testid="stExpander"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        margin-bottom: 20px !important;
    }
    [data-testid="stExpander"] details {
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.9) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08) !important;
        padding: 0 !important;
    }
    [data-testid="stExpander"] details summary {
        direction: ltr;
    }
    [data-testid="stExpander"] details summary p {
        font-size: 18px !important;
        font-weight: bold !important;
        width: 100%;
        text-align: center !important;
        color: #0f172a !important;
    }

    /* Live Metrics Panel */
    .metrics-container {
        padding: 15px 5px;
        display: flex;
        flex-direction: column;
        gap: 25px;
        direction: ltr;
    }
    .metrics-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        flex-wrap: wrap;
        gap: 15px;
    }
    .metric-item {
        flex: 1;
        min-width: 160px;
        text-align: center;
        background: rgba(248, 250, 252, 0.7);
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 12px;
        padding: 12px 8px;
    }
    .metric-title {
        color: #475569;
        font-size: 15px;
        font-weight: bold;
        margin-bottom: 6px;
    }
    .metric-val {
        color: #0f172a;
        font-size: 26px;
        font-weight: bold;
        font-family: 'Times New Roman', serif !important;
        display: inline-block;
    }

    /* Headings */
    h1 { 
        font-size: 34px !important; 
        color: #0f172a !important; 
        font-weight: bold !important; 
        text-align: center !important; 
        margin-bottom: 20px !important;
        text-shadow: 0 1px 6px rgba(255, 255, 255, 0.9);
        letter-spacing: 1px;
    }
    h2, h3, .stSubheader { 
        font-size: 24px !important; 
        color: #0f172a !important; 
        font-weight: bold !important; 
        text-align: center !important; 
        margin-bottom: 15px !important;
        text-shadow: 0 1px 6px rgba(255, 255, 255, 0.9);
    }
    h5 { 
        font-size: 17px !important; 
        color: #1e293b !important; 
        font-weight: bold !important; 
        text-align: center !important; 
        margin-top: 20px !important; 
        margin-bottom: 8px !important; 
    }
    
    /* Timeframe Selector Styling */
    div[data-testid="stRadio"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    div[role="radiogroup"] {
        display: inline-flex !important;
        justify-content: center !important;
        align-items: center !important;
        flex-wrap: wrap !important;
        margin: 0 auto !important;
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(8px) !important;
        padding: 10px 20px !important;
        border-radius: 50px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        direction: ltr !important;
    }
    div[role="radiogroup"] label {
        display: inline-flex !important;
        align-items: center !important;
        margin: 0 8px !important;
        cursor: pointer !important;
    }
    div[role="radiogroup"] label p { 
        font-size: 15px !important; 
        font-weight: bold !important; 
        color: #0f172a !important; 
    }

    /* Charts Container */
    div[data-testid="stVegaLiteChart"], div[data-testid="stArrowVegaLiteChart"] {
        direction: ltr !important;
        background-color: #ffffff !important;
        border-radius: 16px !important;
        padding: 14px !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        overflow: hidden !important;
    }
    div[data-testid="stVegaLiteChart"] summary, div[data-testid="stArrowVegaLiteChart"] summary {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Sidebar Settings
st.sidebar.markdown("### ⚙️ Dashboard Settings")
live_update = st.sidebar.checkbox("🔄 Live Update", value=True, help="Uncheck to pause live data streaming.")
st.sidebar.markdown("---")
st.sidebar.info("🎓 **IUST Solar PV DAQ System**\n\nB.Sc. Thesis Project\n\nReal-time IoT Monitoring & Analysis")

# 4. Weather Fetcher for Tehran
@st.cache_data(ttl=300)
def get_tehran_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=35.6892&longitude=51.3890&current=temperature_2m,relative_humidity_2m"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        if 'current' in data:
            temp = data['current']['temperature_2m']
            hum = data['current']['relative_humidity_2m']
            return f"{temp} °C", f"{hum} %"
    except:
        pass
    return "28.0 °C", "35 %"

tehran_tz = pytz.timezone('Asia/Tehran')
now_tehran = datetime.now(tehran_tz)
date_str = now_tehran.strftime("%Y-%m-%d")
time_str = now_tehran.strftime("%H:%M:%S")
tehran_temp, tehran_hum = get_tehran_weather()

st.markdown(f"""
<div class="header-box">
    <div class="header-item">📅 Date: <span class="header-highlight">{date_str}</span></div>
    <div class="header-item">⏰ Time: <span class="header-highlight">{time_str}</span></div>
    <div class="header-item">🌤️ Tehran Temp: <span class="header-highlight">{tehran_temp}</span></div>
    <div class="header-item">💧 Humidity: <span class="header-highlight">{tehran_hum}</span></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<h1>Advanced Solar PV Monitoring</h1>", unsafe_allow_html=True)

# 5. In-Memory Data Store
@st.cache_resource
def get_sensor_data():
    return {
        'voltage': 0.0, 'current': 0.0, 'power': 0.0, 'temp': 0.0, 'lux': 0.0, 'watts': 0.0,
        'hist_voltage': [], 'hist_current': [], 'hist_power': [], 'hist_temp': [], 'hist_lux': [], 'hist_watts': [],
        'timestamps': [],
        'log_records': [],
        'last_time': '',
        'mqtt_connected': False,
        'msg_count': 0,
        'last_topic': '-',
        'last_payload': '-'
    }

sensor_data = get_sensor_data()

# 6. MQTT Callbacks
def on_connect(client, userdata, flags, rc, properties=None):
    sensor_data['mqtt_connected'] = True
    client.subscribe("my_powerplant/#")

def on_message(client, userdata, msg):
    topic = msg.topic.lower()
    payload = msg.payload.decode().strip('\x00').strip()
    
    sensor_data['msg_count'] += 1
    sensor_data['last_topic'] = topic
    sensor_data['last_payload'] = payload
    
    try:
        value = float(payload)
        current_time = datetime.now(tehran_tz).strftime("%H:%M:%S")
        sensor_name = topic.split('/')[-1]
        
        if sensor_name == "voltage":
            sensor_data['voltage'] = value
        elif sensor_name == "current":
            sensor_data['current'] = value
        elif sensor_name == "power":
            sensor_data['power'] = value
        elif sensor_name == "temperature":
            sensor_data['temp'] = value
        elif sensor_name == "lux":
            sensor_data['lux'] = value
        elif sensor_name == "watts":
            sensor_data['watts'] = value
            
        if sensor_data['last_time'] != current_time:
            sensor_data['last_time'] = current_time
            
            sensor_data['timestamps'].append(current_time)
            sensor_data['hist_voltage'].append(sensor_data['voltage'])
            sensor_data['hist_current'].append(sensor_data['current'])
            sensor_data['hist_power'].append(sensor_data['power'])
            sensor_data['hist_temp'].append(sensor_data['temp'])
            sensor_data['hist_lux'].append(sensor_data['lux'])
            sensor_data['hist_watts'].append(sensor_data['watts'])
            
            record = {
                'Time': current_time,
                'Voltage (V)': sensor_data['voltage'],
                'Current (mA)': sensor_data['current'],
                'Power (mW)': sensor_data['power'],
                'Temp (°C)': sensor_data['temp'],
                'Lux': sensor_data['lux'],
                'Irradiance (W/m2)': sensor_data['watts']
            }
            sensor_data['log_records'].append(record)

            # Auto-backup to disk CSV
            try:
                df_save = pd.DataFrame([record])
                df_save.to_csv('solar_backup.csv', mode='a', header=not os.path.exists('solar_backup.csv'), index=False)
            except:
                pass

            if len(sensor_data['timestamps']) > 20000:
                sensor_data['timestamps'].pop(0)
                sensor_data['hist_voltage'].pop(0)
                sensor_data['hist_current'].pop(0)
                sensor_data['hist_power'].pop(0)
                sensor_data['hist_temp'].pop(0)
                sensor_data['hist_lux'].pop(0)
                sensor_data['hist_watts'].pop(0)
                sensor_data['log_records'].pop(0)
    except:
        pass

# 7. MQTT Client Initialization
@st.cache_resource
def init_mqtt():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    except:
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except:
            client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect("broker.emqx.io", 1883, keepalive=60)
    except:
        client.connect("broker.hivemq.com", 1883, keepalive=60)
        
    client.loop_start()
    return client

try:
    mqtt_client = init_mqtt()
except Exception as e:
    st.error(f"MQTT Client Init Error: {e}")

# ==========================================
# Tabs Architecture: Live Monitoring & Historical Analysis
# ==========================================
tabs = st.tabs(["🔴 Live Monitoring", "📂 Historical Analysis"])

# ==========================================
# Tab 1: Live Monitoring
# ==========================================
with tabs[0]:
    # 8. MQTT Connection Status Expander
    with st.expander("🛠️ MQTT Network & Connection Status", expanded=not sensor_data['mqtt_connected']):
        status_color = "🟢 Connected" if sensor_data['mqtt_connected'] else "🔴 Connecting..."
        st.markdown(f"<div style='text-align: center; font-size: 17px;'><b>Connection Status:</b> {status_color}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; font-size: 17px;'><b>Total Messages Received:</b> <span style='font-family: Times New Roman, serif;'>{sensor_data['msg_count']}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; font-size: 17px;'><b>Last Topic:</b> <span style='font-family: Times New Roman, serif; color: #2563eb;'>{sensor_data['last_topic']}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; font-size: 17px;'><b>Last Payload:</b> <span style='font-family: Times New Roman, serif; color: #2563eb;'>{sensor_data['last_payload']}</span></div>", unsafe_allow_html=True)

    st.divider()

    # 9. Panel Efficiency Calculation
    # Formula: Power (W) / (Irradiance W/m² * Area 0.38 m²) * 100
    power_w = (sensor_data['power'] / 1000.0) if sensor_data['power'] > 0 else 0.0
    irradiance_val = sensor_data['watts']
    panel_area = 0.38
    if irradiance_val > 0 and (irradiance_val * panel_area) > 0 and power_w > 0:
        efficiency = (power_w / (irradiance_val * panel_area)) * 100.0
        efficiency = min(max(efficiency, 0.0), 100.0)
    else:
        efficiency = 0.0

    # Live Numerical Metrics
    with st.expander("📊 Live System Metrics", expanded=True):
        metrics_html = f"""
        <div class="metrics-container">
            <div class="metrics-row">
                <div class="metric-item">
                    <div class="metric-title">⚡ Operating Voltage</div>
                    <div class="metric-val">{sensor_data['voltage']:.2f} <span style="font-size: 15px;">V</span></div>
                </div>
                <div class="metric-item">
                    <div class="metric-title">🔌 Output Current</div>
                    <div class="metric-val">{sensor_data['current']:.2f} <span style="font-size: 15px;">mA</span></div>
                </div>
                <div class="metric-item">
                    <div class="metric-title">🔋 Generated Power</div>
                    <div class="metric-val">{sensor_data['power']:.2f} <span style="font-size: 15px;">mW</span></div>
                </div>
                <div class="metric-item">
                    <div class="metric-title">🌱 Panel Efficiency</div>
                    <div class="metric-val">{efficiency:.2f} <span style="font-size: 15px;">%</span></div>
                </div>
            </div>
            <div class="metrics-row">
                <div class="metric-item">
                    <div class="metric-title">🌡️ Panel Temperature</div>
                    <div class="metric-val">{sensor_data['temp']:.2f} <span style="font-size: 15px;">°C</span></div>
                </div>
                <div class="metric-item">
                    <div class="metric-title">☀️ Illuminance</div>
                    <div class="metric-val">{sensor_data['lux']:.1f} <span style="font-size: 15px;">Lux</span></div>
                </div>
                <div class="metric-item">
                    <div class="metric-title">🔆 Solar Irradiance</div>
                    <div class="metric-val">{sensor_data['watts']:.2f} <span style="font-size: 15px;">W/m²</span></div>
                </div>
            </div>
        </div>
        """
        st.markdown(metrics_html, unsafe_allow_html=True)

    st.divider()

    # 10. Daily Maximums (Daily Max) extracted from In-Memory arrays
    max_power = max(sensor_data['hist_power']) if len(sensor_data['hist_power']) > 0 else sensor_data['power']
    max_temp = max(sensor_data['hist_temp']) if len(sensor_data['hist_temp']) > 0 else sensor_data['temp']
    max_irradiance = max(sensor_data['hist_watts']) if len(sensor_data['hist_watts']) > 0 else sensor_data['watts']

    st.markdown("### 🏆 Daily Maximums (Daily Max)")
    col_max1, col_max2, col_max3 = st.columns(3)

    with col_max1:
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 14px; padding: 14px 10px; text-align: center; border: 1px solid rgba(226, 232, 240, 0.9); box-shadow: 0 4px 15px rgba(0, 0, 0, 0.06); margin-bottom: 15px;">
            <div style="color: #475569; font-size: 16px; font-weight: bold; margin-bottom: 6px;">⚡ Max Power</div>
            <div style="color: #059669; font-size: 26px; font-weight: bold; font-family: 'Times New Roman', serif;">{max_power:.2f} <span style="font-size: 15px;">mW</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col_max2:
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 14px; padding: 14px 10px; text-align: center; border: 1px solid rgba(226, 232, 240, 0.9); box-shadow: 0 4px 15px rgba(0, 0, 0, 0.06); margin-bottom: 15px;">
            <div style="color: #475569; font-size: 16px; font-weight: bold; margin-bottom: 6px;">🌡️ Max Temp</div>
            <div style="color: #dc2626; font-size: 26px; font-weight: bold; font-family: 'Times New Roman', serif;">{max_temp:.2f} <span style="font-size: 15px;">°C</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col_max3:
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 14px; padding: 14px 10px; text-align: center; border: 1px solid rgba(226, 232, 240, 0.9); box-shadow: 0 4px 15px rgba(0, 0, 0, 0.06); margin-bottom: 15px;">
            <div style="color: #475569; font-size: 16px; font-weight: bold; margin-bottom: 6px;">🔆 Peak Irradiance</div>
            <div style="color: #ea580c; font-size: 26px; font-weight: bold; font-family: 'Times New Roman', serif;">{max_irradiance:.2f} <span style="font-size: 15px;">W/m²</span></div>
        </div>
        """, unsafe_allow_html=True)

    # 11. Real-Time Dynamic Charts
    st.subheader("📈 Real-Time Trend Charts")

    timeframe = st.radio(
        label="Timeframe", 
        options=["1 Min", "5 Mins", "15 Mins", "1 Hour", "12 Hours", "All-Time"],
        horizontal=True,
        index=1,
        label_visibility="collapsed"
    )

    limit_map = {
        "1 Min": 12,
        "5 Mins": 60,
        "15 Mins": 180,
        "1 Hour": 720,
        "12 Hours": 8640,
        "All-Time": None
    }
    point_limit = limit_map[timeframe]

    def draw_chart(data_list, time_list, chart_name, line_color, limit=None):
        if len(data_list) > 0 and len(time_list) == len(data_list):
            if limit and len(data_list) > limit:
                sub_data = data_list[-limit:]
                sub_time = time_list[-limit:]
            else:
                sub_data = data_list
                sub_time = time_list
                
            df = pd.DataFrame({
                'Time': sub_time,
                chart_name: sub_data
            })
            df = df.set_index('Time')
            st.line_chart(df, color=line_color, height=280)
        else:
            st.info("Collecting sensor data...")

    st.markdown("##### ⚡ Output Voltage (V)")
    draw_chart(sensor_data['hist_voltage'], sensor_data['timestamps'], "Voltage (V)", "#2563eb", limit=point_limit)

    st.markdown("##### 🔌 Load Current (mA)")
    draw_chart(sensor_data['hist_current'], sensor_data['timestamps'], "Current (mA)", "#d97706", limit=point_limit)

    st.markdown("##### 🔋 Generated Power (mW)")
    draw_chart(sensor_data['hist_power'], sensor_data['timestamps'], "Power (mW)", "#059669", limit=point_limit)

    st.markdown("##### ☀️ Illuminance (Lux)")
    draw_chart(sensor_data['hist_lux'], sensor_data['timestamps'], "Illuminance (Lux)", "#ca8a04", limit=point_limit)

    st.markdown("##### 🔆 Solar Irradiance (W/m²)")
    draw_chart(sensor_data['hist_watts'], sensor_data['timestamps'], "Irradiance (W/m²)", "#ea580c", limit=point_limit)

    st.markdown("##### 🌡️ Panel Temperature (°C)")
    draw_chart(sensor_data['hist_temp'], sensor_data['timestamps'], "Temperature (°C)", "#dc2626", limit=point_limit)

    st.divider()

    # 12. Data Log Archive Table & Download
    with st.expander("🗃️ View & Download Data Log Archive", expanded=False):
        if len(sensor_data['log_records']) > 0:
            df_logs = pd.DataFrame(sensor_data['log_records'])
            st.dataframe(df_logs.iloc[::-1], width='stretch', height=280)
            
            csv_data = df_logs.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV Archive",
                data=csv_data,
                file_name=f"solar_log_{date_str}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Waiting for first data packet from microcontroller...")

# ==========================================
# Tab 2: Historical Analysis
# ==========================================
with tabs[1]:
    st.subheader("📂 Historical Data Analysis")
    st.caption("💡 Tip: You can temporarily uncheck 'Live Update' in the sidebar to review historical data without interruptions.")
    
    uploaded_file = st.file_uploader(
        "📂 Upload Historical Data File (CSV)", 
        type=["csv"],
        help="Upload a previously saved solar monitoring CSV file."
    )
    
    if uploaded_file is not None:
        try:
            try:
                hist_df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
            except Exception:
                uploaded_file.seek(0)
                try:
                    hist_df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
                except Exception:
                    uploaded_file.seek(0)
                    hist_df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File loaded successfully. Total records: {len(hist_df):,}")
            
            with st.expander("👀 View Uploaded Data Table", expanded=False):
                st.dataframe(hist_df, width='stretch', height=280)
            
            # Detect time column for x-axis
            time_col = None
            for c in ['Time', 'time', 'timestamp', 'Timestamp', 'Date', 'date', 'datetime', 'Datetime']:
                if c in hist_df.columns:
                    time_col = c
                    break
            if time_col is None:
                time_col = hist_df.columns[0]
            
            def find_col(candidates):
                for cand in candidates:
                    for c in hist_df.columns:
                        if cand.lower() in c.lower():
                            return c
                return None
            
            col_v = find_col(['voltage', 'volt', 'v'])
            col_i = find_col(['current', 'curr', 'amp', 'i'])
            col_p = find_col(['power', 'watt', 'p'])
            col_t = find_col(['temp', 'temperature', 't'])
            col_w = find_col(['irradiance', 'watts', 'solar', 'rad', 'w/m2', 'w/m²'])
            col_lux = find_col(['lux', 'illuminance', 'light'])

            # Summary statistics of uploaded file
            hist_max_cols = st.columns(3)
            with hist_max_cols[0]:
                if col_p and pd.to_numeric(hist_df[col_p], errors='coerce').notnull().any():
                    max_p_file = pd.to_numeric(hist_df[col_p], errors='coerce').max()
                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 10px; text-align: center; border: 1px solid #e2e8f0; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                        <div style="color: #475569; font-size: 15px; font-weight: bold;">⚡ Max Power in File</div>
                        <div style="color: #059669; font-size: 22px; font-weight: bold; font-family: 'Times New Roman', serif;">{max_p_file:.2f} mW</div>
                    </div>
                    """, unsafe_allow_html=True)
            with hist_max_cols[1]:
                if col_t and pd.to_numeric(hist_df[col_t], errors='coerce').notnull().any():
                    max_t_file = pd.to_numeric(hist_df[col_t], errors='coerce').max()
                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 10px; text-align: center; border: 1px solid #e2e8f0; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                        <div style="color: #475569; font-size: 15px; font-weight: bold;">🌡️ Max Temp in File</div>
                        <div style="color: #dc2626; font-size: 22px; font-weight: bold; font-family: 'Times New Roman', serif;">{max_t_file:.2f} °C</div>
                    </div>
                    """, unsafe_allow_html=True)
            with hist_max_cols[2]:
                if col_w and pd.to_numeric(hist_df[col_w], errors='coerce').notnull().any():
                    max_w_file = pd.to_numeric(hist_df[col_w], errors='coerce').max()
                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 10px; text-align: center; border: 1px solid #e2e8f0; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                        <div style="color: #475569; font-size: 15px; font-weight: bold;">🔆 Peak Irradiance in File</div>
                        <div style="color: #ea580c; font-size: 22px; font-weight: bold; font-family: 'Times New Roman', serif;">{max_w_file:.2f} W/m²</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Historical trend charts
            if col_v and col_v in hist_df.columns:
                st.markdown(f"##### ⚡ Voltage ({col_v})")
                chart_df_v = pd.DataFrame({time_col: hist_df[time_col], col_v: hist_df[col_v]}).set_index(time_col)
                st.line_chart(chart_df_v, color="#2563eb", height=280)

            if col_i and col_i in hist_df.columns:
                st.markdown(f"##### 🔌 Current ({col_i})")
                chart_df_i = pd.DataFrame({time_col: hist_df[time_col], col_i: hist_df[col_i]}).set_index(time_col)
                st.line_chart(chart_df_i, color="#d97706", height=280)

            if col_p and col_p in hist_df.columns:
                st.markdown(f"##### 🔋 Power ({col_p})")
                chart_df_p = pd.DataFrame({time_col: hist_df[time_col], col_p: hist_df[col_p]}).set_index(time_col)
                st.line_chart(chart_df_p, color="#059669", height=280)

            if col_lux and col_lux in hist_df.columns:
                st.markdown(f"##### ☀️ Illuminance ({col_lux})")
                chart_df_lux = pd.DataFrame({time_col: hist_df[time_col], col_lux: hist_df[col_lux]}).set_index(time_col)
                st.line_chart(chart_df_lux, color="#ca8a04", height=280)

            if col_w and col_w in hist_df.columns:
                st.markdown(f"##### 🔆 Solar Irradiance ({col_w})")
                chart_df_w = pd.DataFrame({time_col: hist_df[time_col], col_w: hist_df[col_w]}).set_index(time_col)
                st.line_chart(chart_df_w, color="#ea580c", height=280)

            if col_t and col_t in hist_df.columns:
                st.markdown(f"##### 🌡️ Panel Temperature ({col_t})")
                chart_df_t = pd.DataFrame({time_col: hist_df[time_col], col_t: hist_df[col_t]}).set_index(time_col)
                st.line_chart(chart_df_t, color="#dc2626", height=280)

        except Exception as e:
            st.error(f"Error processing CSV file: {e}")
    else:
        st.info("💡 Please upload a CSV file containing historical solar monitoring data to plot trend charts.")

# 13. Auto-Rerun Control
if live_update:
    time.sleep(3)
    st.rerun()
