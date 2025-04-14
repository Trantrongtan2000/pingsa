import streamlit as st
import time
import threading
from ping3 import ping
import schedule

# Khởi tạo session_state
if 'devices' not in st.session_state:
    st.session_state.devices = [
        ('8.8.8.8', 'Google DNS'),
        ('10.30.10.50', 'Địa chỉ VRpacs'),
        ('172.20.12.245', 'Địa chỉ VRpacs')
    ]
if 'ping_results' not in st.session_state:
    st.session_state.ping_results = []
if 'manual_ping' not in st.session_state:
    st.session_state.manual_ping = False
if 'ping_counts' not in st.session_state:
    st.session_state.ping_counts = {}
else:
    for ip in st.session_state.ping_counts:
        if st.session_state.ping_counts[ip] not in [None, 1, 5, 10]:
            st.session_state.ping_counts[ip] = None

# Hàm ping
def ping_ip(ip_address, device_name):
    try:
        response = ping(ip_address, timeout=2)
        if response is not None:
            response_ms = round(response * 1000, 1)
            result = f"Ping {ip_address} ({device_name}) thành công: {response_ms}ms"
        else:
            result = f"Ping {ip_address} ({device_name}) thất bại: Không có phản hồi"
    except Exception as e:
        result = f"Lỗi khi ping {ip_address} ({device_name}): {str(e)}"
    return result

# Hàm ping với số lần cụ thể (mỗi giây)
def ping_with_interval(ip, name, count, result_container):
    for _ in range(count):
        result = ping_ip(ip, name)
        st.session_state.ping_results.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {result}")
        result_container.write(st.session_state.ping_results[::-1])
        time.sleep(1)

# Hàm ping mỗi phút trong 10 phút
def ping_per_minute(ip, name, result_container):
    start_time = time.time()
    max_duration = 600  # 10 phút = 600 giây
    while time.time() - start_time < max_duration:
        result = ping_ip(ip, name)
        st.session_state.ping_results.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {result}")
        result_container.write(st.session_state.ping_results[::-1])
        time.sleep(60)  # Chờ 1 phút

# Hàm ping tự động
def auto_ping(devices):
    def job():
        for ip, name in devices:
            result = ping_ip(ip, name)
            st.session_state.ping_results.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {result}")
            if len(st.session_state.ping_results) > 100:
                st.session_state.ping_results = st.session_state.ping_results[-100:]
    schedule.every(5).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Giao diện Streamlit
st.title("Ứng dụng Ping IP")

# Quản lý thiết bị
st.subheader("Quản lý danh sách thiết bị")
col_ip, col_name = st.columns(2)
with col_ip:
    ip_input = st.text_input("Nhập địa chỉ IP mới:")
with col_name:
    name_input = st.text_input("Nhập tên thiết bị:")
if st.button("Thêm thiết bị"):
    if ip_input and name_input:
        if not any(ip == ip_input for ip, _ in st.session_state.devices):
            st.session_state.devices.append((ip_input, name_input))
            st.session_state.ping_counts[ip_input] = None
            st.success(f"Đã thêm {ip_input} ({name_input}) vào danh sách!")
        else:
            st.warning(f"Địa chỉ IP {ip_input} đã có trong danh sách!")
    else:
        st.error("Vui lòng nhập cả địa chỉ IP và tên thiết bị!")

# Danh sách thiết bị
st.write("Danh sách thiết bị hiện tại:")
for i, (ip, name) in enumerate(st.session_state.devices):
    col1, col2, col3, col4 = st.columns([4, 1, 1, 2])
    col1.write(f"{ip} ({name})")
    if col2.button("Xóa", key=f"delete_{i}"):
        st.session_state.devices.pop(i)
        st.session_state.ping_counts.pop(ip, None)
        st.success(f"Đã xóa {ip} ({name}) khỏi danh sách!")
        st.rerun()
    if col3.button("Ping", key=f"ping_{i}"):
        result_container = st.empty()
        ping_count = st.session_state.ping_counts.get(ip, None)
        if ping_count is None:
            # Ping mỗi phút trong 10 phút
            ping_per_minute(ip, name, result_container)
        else:
            # Ping mỗi giây cho số lần cụ thể
            ping_with_interval(ip, name, ping_count, result_container)
            st.session_state.ping_counts[ip] = None
        st.session_state.manual_ping = True
    ping_options = ["Ping mỗi phút", "1", "5", "10"]
    current_count = st.session_state.ping_counts.get(ip, None)
    index = 0  # Mặc định là "Ping mỗi phút"
    if current_count is not None and str(current_count) in ping_options[1:]:
        index = ping_options.index(str(current_count))
    selected_count = col4.selectbox(
        "Số lần ping",
        ping_options,
        index=index,
        key=f"count_{i}"
    )
    if selected_count == "Ping mỗi phút":
        st.session_state.ping_counts[ip] = None
    else:
        st.session_state.ping_counts[ip] = int(selected_count)

# Ping tất cả thiết bị
st.subheader("Ping tất cả thiết bị")
all_ping_count = st.selectbox("Số lần ping cho tất cả thiết bị:", ["Ping mỗi phút", "1", "5", "10"], key="all_ping_count")
if st.button("Ping thủ công tất cả thiết bị"):
    result_container = st.empty()
    if all_ping_count == "Ping mỗi phút (tối đa 10 phút)":
        start_time = time.time()
        max_duration = 600  # 10 phút
        while time.time() - start_time < max_duration:
            for ip, name in st.session_state.devices:
                result = ping_ip(ip, name)
                st.session_state.ping_results.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {result}")
                result_container.write(st.session_state.ping_results[::-1])
            time.sleep(60)
    else:
        count = int(all_ping_count)
        for _ in range(count):
            for ip, name in st.session_state.devices:
                result = ping_ip(ip, name)
                st.session_state.ping_results.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {result}")
                result_container.write(st.session_state.ping_results[::-1])
            time.sleep(1)
    st.session_state.manual_ping = True

# Hiển thị kết quả
st.subheader("Kết quả Ping")
result_display = st.empty()
if st.button("Xóa kết quả"):
    st.session_state.ping_results = []
    result_display.write("Chưa có kết quả ping.")
if st.session_state.ping_results:
    result_display.write(st.session_state.ping_results[::-1])
else:
    result_display.write("Chưa có kết quả ping.")

# Chạy ping tự động
if st.session_state.devices:
    if 'auto_ping_thread' not in st.session_state:
        st.session_state.auto_ping_thread = threading.Thread(
            target=auto_ping, args=(st.session_state.devices,), daemon=True
        )
        st.session_state.auto_ping_thread.start()
        st.write(f"Bắt đầu tự động ping các thiết bị trong danh sách mỗi 1 phút...")