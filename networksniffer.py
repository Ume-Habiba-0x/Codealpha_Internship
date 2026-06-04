from scapy.all import sniff, IP, Raw, Padding, TCP, wrpcap
from rich import print_json
from datetime import datetime
import ipaddress

PROTOCOL_MAP = {
    1: "ICMP",
    6: "TCP",
    17: "UDP"
}

captured_packets_list = []

stats = {
    "total": 0,
    "TCP": 0,
    "UDP": 0,
    "ICMP": 0,
    "OTHER": 0
}

user_input = input("Enter IP address: ")


def process(packet):
    if not packet.haslayer(IP):
        return

    captured_packets_list.append(packet)

    stats["total"] += 1

    protocol_name = PROTOCOL_MAP.get(packet[IP].proto, "OTHER")

    if protocol_name in stats:
        stats[protocol_name] += 1
    else:
        stats["OTHER"] += 1

    payload_info = "Control Packet (No Application Payload)"

    if packet.haslayer(Padding):
        payload_info = "Empty Hardware Network Padding"

    elif packet.haslayer(Raw):
        raw_bytes = packet[Raw].load

        decoded_text = raw_bytes.decode("utf-8", errors="ignore").strip()

        if packet.haslayer(TCP) and (
            packet[TCP].dport == 80 or packet[TCP].sport == 80
        ):
            payload_info = f"[HTTP] {decoded_text[:1000]}"

        else:
            payload_info = f"[DATA] {decoded_text[:200]}"

    packet_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Network_layer": {
            "source_ip": packet[IP].src,
            "destination_ip": packet[IP].dst,
            "ttl": packet[IP].ttl,
            "packet_size_bytes": len(packet),
            "payload": payload_info
        },
        "protocol": protocol_name
    }

    print_json(data=packet_data)


try:
    valid_ip = ipaddress.ip_address(user_input.strip())

    print(f"[+] Monitoring {valid_ip} ... Ctrl+C to stop")

    sniff(
        filter=f"host {valid_ip}",
        prn=process,
        store=False
    )

except ValueError:
    print("Invalid IP address")

except KeyboardInterrupt:
    print("\n[!] Stopping capture...")

finally:
    if captured_packets_list:
        wrpcap("codealpha_capture.pcap", captured_packets_list)

    print("\n=== FINAL SUMMARY ===")
    print(f"Total Packets : {stats['total']}")
    print(f"TCP Packets   : {stats['TCP']}")
    print(f"UDP Packets   : {stats['UDP']}")
    print(f"ICMP Packets  : {stats['ICMP']}")
    print(f"OTHER Packets : {stats['OTHER']}")
