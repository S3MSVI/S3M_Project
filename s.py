import streamlit as st
import paho.mqtt.client as mqtt
import time

st.set_page_config(page_title="داشبورد نیروگاه", layout="wide")
st.title("🔋 مانیتورینگ جامع پنل خورشیدی و باتری")
st.divider()

# ۱. ایجاد یک فضای حافظه امن برای دور زدن محدودیت استریم‌لیت
@st.cache_resource
def get_sensor_data():
    return {
        'voltage': 0.0, 'current': 0.0, 'power': 0.0, 
        'temp': 0.0, 'light': 0.0, 'history': []
    }

sensor_data = get_sensor_data()

# ۲. توابع دریافت پیام از اینترنت
def on_connect(client, userdata, flags, rc):
    print("\n✅ به سرور متصل شدیم. منتظر دریافت دیتا از ESP32...\n")
    # عضویت هوشمند در تمام زیرشاخه‌های نیروگاه
    client.subscribe("my_powerplant/#") 

def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        value = float(msg.payload.decode())
        print(f"📥 داده دریافت شد: {topic} ---> {value}")
        
        # بروزرسانی حافظه امن (با رفع مشکل تداخل اسم‌ها)
        if topic.endswith("voltage"):
            sensor_data['voltage'] = value
            sensor_data['history'].append(value)
            if len(sensor_data['history']) > 50:
                sensor_data['history'].pop(0)
        elif topic.endswith("current"):
            sensor_data['current'] = value
        elif topic.endswith("power"):
            sensor_data['power'] = value
        elif topic.endswith("temperature"):
            sensor_data['temp'] = value
        elif topic.endswith("light"):
            sensor_data['light'] = value
    except:
        pass

# ۳. راه‌اندازی ارتباط MQTT (فقط یک بار اجرا می‌شود)
@st.cache_resource
def init_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("broker.emqx.io", 1883)
    client.loop_start()
    return client

try:
    mqtt_client = init_mqtt()
except:
    st.error("❌ ارتباط با سرور برقرار نشد.")

# ۴. نمایش دیتاهای حافظه امن روی رابط گرافیکی سایت
col1, col2, col3, col4 = st.columns(4)
col1.metric("⚡ ولتاژ باس (V)", f"{sensor_data['voltage']} V")
col2.metric("🔌 جریان (mA)", f"{sensor_data['current']} mA")
col3.metric("توان مصرفی (mW)", f"{sensor_data['power']} mW")
col4.metric("🌡️ دمای پنل", f"{sensor_data['temp']} °C")

st.divider()

col5, col6 = st.columns(2)
with col5:
    st.metric("☀️ شدت نور محیط (LDR)", f"{int(sensor_data['light'])}")
    st.caption("عدد بین ۰ (تاریکی مطلق) تا ۴۰۹۵ (نور شدید)")

with col6:
    st.subheader("📈 روند نوسانات ولتاژ")
    if len(sensor_data['history']) > 0:
        st.line_chart(sensor_data['history'])

# ۵. رفرش شدن خودکار سایت هر ۲ ثانیه
time.sleep(2)  
st.rerun() 