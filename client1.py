import socket
import time
import threading
import subprocess
import re
from sctp import sctpsocket_tcp
import project_messages_pb2 as pb

TEAM_ID = 5
TCP_IP = "10.64.45.4"
SCTP_IP = "127.0.0.1"
TCP_PORT = 65432
SCTP_PORT = 54322

# Sender and Receiver methods
def send_msg(sock, msg):
    data = msg.SerializeToString()
    length = len(data)
    sock.sendall(length.to_bytes(4, 'big'))
    sock.sendall(data)

def receive_msg(sock):
    length_data = sock.recv(4)
    length = int.from_bytes(length_data, 'big')
    data = sock.recv(length)
    msg = pb.project_msg()
    msg.ParseFromString(data)

    """# Print message type and payload
    msg_type = msg.WhichOneof("msg")
    print(f"[RECEIVED] Message Type: {msg_type}")
    
    if msg_type == "conn_resp_msg":
        print(f"  Interval: {msg.conn_resp_msg.interval}")
    elif msg_type == "netstat_resp_msg":
        print("  NETSTAT Response received.")
    elif msg_type == "netstat_data_ack_msg":
        print("  NETSTAT Data Acknowledgment received.")
    elif msg_type == "netmeas_resp_msg":
        print(f"  Interval: {msg.netmeas_resp_msg.interval}, Port: {msg.netmeas_resp_msg.port}")
    elif msg_type == "netmeas_data_ack_msg":
        print("  NETMEAS Data Acknowledgment received.")
    elif msg_type == "hello_msg":
        print("  HELLO Message received.")
    else:
        print("  Unknown message type.") """

    return msg

# Message Creation Handlers
def new_conn_req_msg(student_details):
    header = pb.ece441_header()
    header.id = TEAM_ID
    header.type = pb.ECE441_CONN_REQ
    conn_req = pb.conn_req()
    conn_req.header.CopyFrom(header)
    for student in student_details:
        person = conn_req.student.add()
        person.aem = student['aem']
        person.name = student['name']
        person.email = student['email']
    wrapper = pb.project_msg()
    wrapper.conn_req_msg.CopyFrom(conn_req)
    return wrapper

def new_hello_msg():
    header = pb.ece441_header()
    header.id = TEAM_ID
    header.type = pb.ECE441_HELLO
    hello_msg = pb.hello()
    hello_msg.header.CopyFrom(header)
    wrapper = pb.project_msg()
    wrapper.hello_msg.CopyFrom(hello_msg)
    return wrapper

def new_netstat_req_msg(student_details):
    header = pb.ece441_header()
    header.id = TEAM_ID
    header.type = pb.ECE441_NETSTAT_REQ
    netstat_req = pb.netstat_req()
    netstat_req.header.CopyFrom(header)
    for student in student_details:
        person = netstat_req.student.add()
        person.aem = student['aem']
        person.name = student['name']
        person.email = student['email']
    wrapper = pb.project_msg()
    wrapper.netstat_req_msg.CopyFrom(netstat_req)
    return wrapper

def new_netstat_data_msg():
    header = pb.ece441_header()
    header.id = TEAM_ID
    header.type = pb.ECE441_NETSTAT_DATA
    netstat_data = pb.netstat_data()
    netstat_data.header.CopyFrom(header)
    netstat_data.mac_address = "F0:57:A6:88:34:75"
    netstat_data.ip_address = "172.28.219.240"
    wrapper = pb.project_msg()
    wrapper.netstat_data_msg.CopyFrom(netstat_data)
    return wrapper

def new_netmeas_req_msg(student_details):
    header = pb.ece441_header()
    header.id = TEAM_ID
    header.type = pb.ECE441_NETMEAS_REQ
    netmeas_req = pb.netmeas_req()
    netmeas_req.header.CopyFrom(header)
    for student in student_details:
        person = netmeas_req.student.add()
        person.aem = student['aem']
        person.name = student['name']
        person.email = student['email']
    wrapper = pb.project_msg()
    wrapper.netmeas_req_msg.CopyFrom(netmeas_req)
    return wrapper

def new_netmeas_data_msg(report):
    header = pb.ece441_header()
    header.id = TEAM_ID
    header.type = pb.ECE441_NETMEAS_DATA
    netmeas_data = pb.netmeas_data()
    netmeas_data.header.CopyFrom(header)
    netmeas_data.report = report
    wrapper = pb.project_msg()
    wrapper.netmeas_data_msg.CopyFrom(netmeas_data)
    return wrapper

stop_hello = threading.Event()

# HELLO Thread Handler
def hello_thread(sctp_sock, interval):
    while not stop_hello.is_set():
        # Wait for the specified interval
        time.sleep(interval)

        # Send HELLO message
        hello_message = new_hello_msg()
        send_msg(sctp_sock, hello_message)
        print("[HELLO] Sent HELLO message.")

        # Try to receive a HELLO message from the server after sending
        try:
            sctp_sock.settimeout(1)  # Set a short timeout for receiving
            received_message = receive_msg(sctp_sock)
            if received_message.WhichOneof("msg") == "hello_msg":
                print(f"[HELLO] Received HELLO message from server with ID: {received_message.hello_msg.header.id}")
        except socket.timeout:
            print("[HELLO] No HELLO message received after sending.")





# Main Execution
if __name__ == "__main__":
    # TCP Connection
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect((TCP_IP, TCP_PORT))
    print("[TCP] Connected.")

    students = [
        {"aem": 2572, "name": "Daniil Mavroudis", "email": "dmavroudis@uth.gr"},
        {"aem": 2497, "name": "Konstantinos Vakalis", "email": "kvakalis@uth.gr"},
        {"aem": 1414, "name": "Alexandros Aristeidou", "email": "aristeid@uth.gr"},
        {"aem": 3498, "name": "Dimitris Revythis", "email": "drevythis@uth.gr"}
    ]

    # CONN_REQ and CONN_RESP
    conn_req_message = new_conn_req_msg(students)
    send_msg(tcp_sock, conn_req_message)
    conn_resp_message = receive_msg(tcp_sock)
    interval = conn_resp_message.conn_resp_msg.interval
    print(f"[CONN_RESP] Received interval: {interval}.")

    # SCTP Connection
    sctp_sock = sctpsocket_tcp(socket.AF_INET)
    sctp_sock.connect((SCTP_IP, SCTP_PORT))
    print("[SCTP] Connected.")

    # Start HELLO Thread
    thrd = threading.Thread(target=hello_thread, args=(sctp_sock, interval), daemon=True)
    thrd.start()

    # NETSTAT_REQ and NETSTAT_RESP
    netstat_req_message = new_netstat_req_msg(students)
    send_msg(tcp_sock, netstat_req_message)
    netstat_resp_message = receive_msg(tcp_sock)
    print("[NETSTAT_RESP] Received NETSTAT response.")

    # NETSTAT_DATA and NETSTAT_DATA_ACK
    netstat_data_message = new_netstat_data_msg()
    send_msg(tcp_sock, netstat_data_message)
    netstat_data_ack_message = receive_msg(tcp_sock)
    print("[NETSTAT_DATA_ACK] Received NETSTAT data acknowledgment.")

    # NETMEAS_REQ and NETMEAS_RESP
    netmeas_req_message = new_netmeas_req_msg(students)
    send_msg(tcp_sock, netmeas_req_message)
    netmeas_resp_message = receive_msg(tcp_sock)
    interval, port = netmeas_resp_message.netmeas_resp_msg.interval, netmeas_resp_message.netmeas_resp_msg.port
    print(f"[NETMEAS_RESP] Received server port: {port}, interval: {interval}.")

    # iperf3 Throughput Test
    result = subprocess.run([
        "iperf3", "-c", TCP_IP, "-p", str(port), "-t", str(interval)
    ], capture_output=True, text=True)

    # Extract bandwidth from standard output using regex
    match = re.search(r'(\d+.\d+)\s+Mbits/sec', result.stdout)
    if match:
        bandwidth = float(match.group(1))
        print(f"[IPERF3] Bandwidth: {bandwidth:.2f} Mbps.")
    else:
        print("[ERROR] Unable to extract bandwidth from iperf3 output.")


    # NETMEAS_DATA and NETMEAS_DATA_ACK
    netmeas_data_message = new_netmeas_data_msg(bandwidth)
    send_msg(tcp_sock, netmeas_data_message)
    netmeas_data_ack_message = receive_msg(tcp_sock)
    print("[NETMEAS_DATA_ACK] Received NETMEAS data acknowledgment.")

    stop_hello.set()
    thrd.join()
    # Cleanup
    sctp_sock.close()
    tcp_sock.close()
    print("All connections closed.")
