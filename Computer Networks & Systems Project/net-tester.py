# implement an iperf client in Python using sockets

import socket
import struct
import time
import threading
import argparse
import sys
from typing import Optional
import csv
from typing import List
import select

""""
    Usage
    -----
    - Instantiate with an optional CSV file path. Use none to disable, or a path
      like "results.csv" to enable CSV output. By default the class output performance results to "results.csv".
    - Call log_stat() to record individual measurements.
    - Call summary() to print aggregated statistics.
    - Call close() to close any open CSV resource before program exit.

    Example
    -------
    logger = Logger("out.csv")
    logger.log_info("Starting test")
    logger.log_stat(time.time(), "192.0.2.1", 5201, bandwidth=12.34)
    logger.summary()
    logger.close()
"""


class Logger:
    """
    Logger
    ------
    Logger class for recording and displaying network test metrics"""

    INFO = '\033[94m[INFO]\033[0m '
    ERROR = '\033[91m[ERROR]\033[0m '

    class Stat:
        """A class to model a single measurement record"""

        def __init__(self, timestamp: float, bandwidth: Optional[float] = None,
                     loss: Optional[float] = None, jitter: Optional[float] = None):
            self.timestamp = timestamp
            self.bandwidth = bandwidth
            self.loss = loss
            self.jitter = jitter

    def __init__(self, csv_output: Optional[str] = "results.csv"):
        """Initialize Logger with optional CSV output"""
        self.stats: List[Logger.Stat] = []  # List to store measurements
        self.csv_output = csv_output        # CSV file path or None
        self.csv_file = None               # File handle for CSV
        self.csv_writer = None             # CSV writer object

        # If the csv parameter is None, then disable CSV output
        if csv_output:
            self.csv_file = open(csv_output, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(
                ['timestamp', 'elapsed', 'bandwidth_mbps', 'loss_percent', 'jitter_ms'])

    def log_stat(self, timestamp: float, ip: str, port: int, bandwidth: Optional[float] = None,
                 loss: Optional[float] = None, jitter: Optional[float] = None) -> None:
        """
        Log a measurement (all parameters optional)
        - timestamp: Time of measurement (float)
        - ip: Client IP address (str)
        - port: Client port number (int)
        - bandwidth: Bandwidth in Mbps (float, optional)
        - loss: Packet loss in percent (float, optional)
        - jitter: Jitter in milliseconds (float, optional)
        """
        stat = Logger.Stat(timestamp, bandwidth, loss, jitter)
        self.stats.append(stat)
        elapsed = 0.0
        if len(self.stats) > 1:
            elapsed = timestamp - self.stats[0].timestamp

        # Write to CSV if enabled
        if self.csv_writer:
            self.csv_writer.writerow([
                ip, port,
                timestamp,
                f"{elapsed:.3f}",
                f"{bandwidth:.2f}" if bandwidth is not None else "",
                f"{loss:.2f}" if loss is not None else "",
                f"{jitter:.2f}" if jitter is not None else ""
            ])
            self.csv_file.flush()

        parts = [f"[{int(elapsed):03d}s] [Client:{ip}:{port}]"]

        if bandwidth is not None:
            parts.append(f"Bandwidth: {bandwidth:.2f} Mbps")
        if loss is not None:
            parts.append(f"Loss: {loss:.2f}%")
        if jitter is not None:
            parts.append(f"Jitter: {jitter:.6f} ms")

        print(" ".join(parts))

    def summary(self) -> None:
        """
        Print summary statistics
        1. Duration of the test
        2. Number of measurements
        3. For each metric (bandwidth, loss, jitter):
           - Average
           - Minimum
           - Maximum
        4. If CSV output was enabled, print the path to the CSV file
        """
        if not self.stats:
            print(f"{Logger.INFO}No statistics recorded")
            return

        print(f"\n{Logger.INFO}=== Test Summary ===")
        print(
            f"  Duration: {int(self.stats[-1].timestamp - self.stats[0].timestamp)}s")
        print(f"  Measurements: {len(self.stats)}")

        # Calculate averages
        bw_values = [
            s.bandwidth for s in self.stats if s.bandwidth is not None]
        loss_values = [s.loss for s in self.stats if s.loss is not None]
        jitter_values = [s.jitter for s in self.stats if s.jitter is not None]

        if bw_values:
            print(f"  Bandwidth: avg={sum(bw_values)/len(bw_values):.2f} Mbps, "
                  f"min={min(bw_values):.2f}, max={max(bw_values):.2f}")
        if loss_values:
            print(f"  Loss: avg={sum(loss_values)/len(loss_values):.2f}%, "
                  f"min={min(loss_values):.2f}, max={max(loss_values):.2f}")
        if jitter_values:
            print(f"  Jitter: avg={sum(jitter_values)/len(jitter_values):.6f} ms, "
                  f"min={min(jitter_values):.6f}, max={max(jitter_values):.6f}")

        if self.csv_output:
            self.log_success(f"Results saved to {self.csv_output}")

    def close(self) -> None:
        """Close CSV file if open"""
        if self.csv_file:
            self.csv_file.close()

    def log_info(self, message: str) -> None:
        """
        Print an info message to stdout
        """
        print(f"{Logger.INFO}{message}")

    def log_error(self, message: str) -> None:
        """
        Print an info message to stdout
        """
        print(f"{Logger.ERROR}{message}")

# Below you can find sample function signatures for the net-tester client and server.
# You can modify them as needed.


# ---------------------- TCP stubs (Task 2) ----------------------

def tester_tcp_client(log: Logger, server_ip: str, server_port: int,
                      duration: int, interval: int) -> None:
    """TCP client (Task 2)
    TODO:
      - Connect and send for 'duration' seconds (chunks of 'window')
      - Every 'interval' seconds, compute and log bandwidth
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))  # Establishing connection

    start_time = time.time()
    data = b"X" * 8192  # creating message
    totalBytesSent = 0
    lastTime = start_time

    log.log_info(f"Starting TCP client to {server_ip}:{server_port} "
                 f"for {duration}s")

    # While the duration of time isn't reached send all the packets and measure the bytes sent
    while time.time() - start_time < duration:
        try:
            client_socket.sendall(data)
            totalBytesSent += len(data)
        except Exception as e:
            log.log_error(f"Error: {e}")

        currentTime = time.time()
        if currentTime - lastTime >= interval:
            # Make it so if interval is reached then do this.
            elapsed = currentTime - lastTime
            bandwidth = (totalBytesSent / elapsed) * 8 / 1e6
            log.log_stat(
                timestamp=currentTime,
                ip=server_ip,  # when interval is reached, log bandwith.
                port=server_port,
                bandwidth=bandwidth
            )
            totalBytesSent = 0  # resetting for next packet
            lastTime = currentTime

    client_socket.close()
    # Skeleton only; safe no-op if not implemented.
    return None


def tester_tcp_server(log: Logger, port: int) -> None:
    """TCP server (Task 2)
    TODO:
      - Listen on 'port'; accept multiple clients
      - Receive/discard bytes; optionally log per-client bandwidth
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # establishing connection
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # binding socket to any port that is available
    server_socket.bind(("0.0.0.0", port))
    rfds = [server_socket]  # list to read file descriptors
    server_socket.listen()

    log.log_info(f"Server listening on port {port}")

    log.log_info(f"Starting TCP server on port {port}")

    while True:
        # checking sockets for data and reading
        rlist, _, _ = select.select(rfds, [], [])

        if server_socket in rlist:
            # accepts incoming client connection and returns a new socket and its address
            client_socket, client_address = server_socket.accept()
            log.log_info(f"Client connected from {client_address}")

            rfds.append(client_socket)

            rlist.remove(server_socket)

        for client_socket in rlist:
            if client_socket not in rfds:
                continue

            # recieve data up to 4096 bytes (4kb for large buffer)
            data = client_socket.recv(4096)

            if len(data) == 0:  # if there is no more data to be recieved, close connection
                client_socket.close()
                rfds.remove(client_socket)
                break

    # Skeleton only; safe no-op if not implemented.
    return None

# ---------------------- UDP stubs (Tasks 3 & 4) ----------------------


def tester_udp_client(log: Logger, server_ip: str, server_port: int,
                      duration: int, interval: int,
                      rate_kbps: int, ack: bool) -> None:
    """UDP client
    Task 3 (ack == False):
      - Send datagrams at 'rate_kbps'
      - First 4 bytes = big-endian ID; start at 1; send ID=0 to end
      - Client may log sending rate, but server computes metrics
    Task 4 (ack == True):
      - Receive acks (ID + server receive timestamp)
      - Compute client-side BW / loss (via timeout) / jitter from acks and log
    """
    log.log_info(f"Starting UDP client to {server_ip}:{server_port} "
                 f"for {duration}s at {rate_kbps} Kbps (ack={ack})")
    # Common setup (safe if left unused):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Do not forger to bind the client socket to a port if you want to receive ACKs

    packet_size = 1472

    packet_id = 1
    start_time = time.time()
    last_time = start_time
    total_bytes_sent = 0

    pkt_interval = packet_size * 8 / (rate_kbps * 1000)

    if not ack:
        # -------------------- Task 3: UDP without acks --------------------
        # TODO:
        #   - Compute packet trasnmission interval to match rate_kbps using you datagram size
        #   - Loop until 'duration' elapsed:
        #       * Build payload: 4B ID (big-endian) + (pkt_size-4) bytes
        #       * sendto(...)
        #       * sleep until next send (pkt_interval)
        #       * every 'interval' seconds, optionally log sending rate
        #   - Send ID=0 to signal end; close socket

        while time.time() - start_time < duration:
            # converting id into big endian for transmission
            header = struct.pack('!I', packet_id)

            payload = b"X" * 1468  # creating the message
            packet = header + payload

            try:
                sock.sendto(packet, (server_ip, server_port))
                total_bytes_sent += len(packet)                     #sending packet and keeping track of bytes sent
            except Exception as e:
                log.log_error(f"Error: {e}")

            currentTime = time.time()
            time.sleep(pkt_interval)

            packet_id += 1

        packet_id = 0
        header = struct.pack('!I', packet_id)
        packet = header + payload  # sending termination packet to end transmission
        sock.sendto(packet, (server_ip, server_port))
        sock.close()

        return None
    else:
        # -------------------- Task 4: UDP with acks --------------------
        # TODO:
        #   - Same sending loop as Task 3
        #   - Keep track of pending ACKs and received ACK timestamps
        #   - Non-blocking recv for acks:
        #       * parse 4B ID + server-timestamp (specify your chosen encoding)
        #       * compute RTT / arrival deltas; update metrics
        #   - Every 'interval' seconds, log client-side BW/loss/jitter via log.report(...)
        #   - End with ID=0; close socket

        sock.bind(('', 0))  # binding the socket to any available port
        sock.setblocking(False)  # making it non-blocking to receive ACKs without delaying packet sends

        packet_size = 1472
        
        pending = {}  #holds pending packets with the key being id and value being the timestamp
        acks_received_total = 0
        lost_packets_total = 0

        # Per-interval tracking
        interval_rtts = []            # roundtrips for this interval
        interval_acks_count = 0       # ACKs received in this interval

        last_report_time = start_time
        next_report_time = start_time + interval

        ack_timeout = interval  # timeout (seconds) after which a still pending packet is considered lost

        try:
            while time.time() - start_time < duration:
                send_start = time.time()

                header = struct.pack('!I', packet_id)    #converting id into big endian for transmission
                payload = b"X" * (packet_size - 4)       #creating the message
                packet = header + payload

                try:
                    sock.sendto(packet, (server_ip, server_port)) # store send timestamp in pending dict
                    pending[packet_id] = send_start
                    packet_id += 1
                except Exception as e:
                    log.log_error(f"Error: {e}")

                # To recieve all available acks 
                while True:
                    try:
                        ack_data, _ = sock.recvfrom(12)  # ACK is 4B ID + 8B 
                        if len(ack_data) < 12:
                            continue

                        ack_id, server_ts = struct.unpack('!Id', ack_data)
                        recv_time = time.time()

                        # If this ID isbnt pending, it's either duplicate or already marked lost so ignore and keep reading
                        if ack_id not in pending:
                            continue

                        # remove from pending and update counters
                        send_ts = pending.pop(ack_id)
                        acks_received_total += 1
                        interval_acks_count += 1

                        rtt = recv_time - send_ts
                        interval_rtts.append(rtt)

                    except (BlockingIOError, InterruptedError, socket.timeout):
                        #if blockingIOerror is returned, it measns that there are no more packets to be sent hence break loop
                        break
                    except Exception as e:
                        log.log_error(f"Error receiving ACK: {e}")
                        break

                currentTime = time.time()

                if currentTime >= next_report_time:
                    elapsed = currentTime - last_report_time
                    if elapsed <= 0:        # to prevent dividing by 0 in bandwith calc
                        elapsed = 1e-6 
                        
                    newly_lost = 0
                    for pid, ts in list(pending.items()):
                        if currentTime - ts >= ack_timeout:                      # Check pending packets for timeouts and mark as lost
                            newly_lost += 1
                            lost_packets_total += 1
                            del pending[pid]

                    total_considered = interval_acks_count + newly_lost

                    if total_considered > 0:
                        # Bandwidth based only on ACKed packets
                        acked_bytes = interval_acks_count * packet_size
                        bandwidth = (acked_bytes / elapsed) * 8 / 1e6

                        # Loss from ACKs vs lost packets (as requested)
                        loss = (newly_lost / total_considered) * 100.0

                        # Jitter based on variation in RTTs
                        jitter_ms = 0.0
                        if len(interval_rtts) >= 2:
                            total_jitter = 0.0
                            for i in range(1, len(interval_rtts)):
                                total_jitter += abs(
                                    interval_rtts[i] - interval_rtts[i - 1]
                                )
                            jitter_ms = (total_jitter / (len(interval_rtts) - 1)) * 1000.0

                        log.log_stat(
                            timestamp=currentTime,
                            ip=server_ip,
                            port=server_port,
                            bandwidth=bandwidth,
                            loss=loss,
                            jitter=jitter_ms
                        )

                    # reset interval accumulators
                    interval_rtts = []
                    interval_acks_count = 0
                    last_report_time = currentTime
                    next_report_time = currentTime + interval

                # try to stick to the desired sending rate
                elapsed_send = time.time() - send_start
                sleep_time = pkt_interval - elapsed_send
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:           # if keyboard interrupt is signaled, report time
            log.log_info("\nClient interrupted by user")

            currentTime = time.time()
            elapsed = currentTime - last_report_time
            if elapsed <= 0:
                elapsed = 1e-6

            # Final pass over pending to mark losses
            newly_lost = 0
            for pid, ts in list(pending.items()): #looping for packet id and time the packet was setn
                if currentTime - ts >= ack_timeout: # if packet has been waiting for too long (timeout) consider it lost
                    newly_lost += 1
                    lost_packets_total += 1
                    del pending[pid]

            total_considered = interval_acks_count + newly_lost # considered packets

            if total_considered > 0:
                acked_bytes = interval_acks_count * packet_size
                bandwidth = (acked_bytes / elapsed) * 8 / 1e6   #if there are considered packets then rest can be calclated
                loss = (newly_lost / total_considered) * 100.0

                jitter_ms = 0.0
                if len(interval_rtts) >= 2: #need at least two packets (or two round trips in this interval to calculate jitter)
                    total_jitter = 0.0
                    for i in range(1, len(interval_rtts)):
                        total_jitter += abs(
                            interval_rtts[i] - interval_rtts[i - 1]
                        )
                    jitter_ms = (total_jitter / (len(interval_rtts) - 1)) * 1000.0

                # Log final stats with current values
                log.log_stat(
                    timestamp=currentTime,
                    ip=server_ip,
                    port=server_port,
                    bandwidth=bandwidth,
                    loss=loss,
                    jitter=jitter_ms
                )

        finally:                                    
            header = struct.pack('!I', 0)       # then send termination packet
            payload = b"X" * 1468
            packet = header + payload
            try:
                sock.sendto(packet, (server_ip, server_port))
            except:
                pass  # Socket might already be closed
            sock.close()

        return None



def tester_udp_server(log: Logger, port: int, rate: int, interval: int, ack: bool,) -> None:
    """UDP server
    Task 3 (ack == False):
      - Receive datagrams from multiple clients (track by (ip,port))
      - Compute per-client bandwidth / jitter / loss from arrivals
      - Periodically log per-client metrics via log.report(...)
    Task 4 (ack == True):
      - Same as Task 3, plus send an ack for each received datagram:
        4B ID (big-endian)
    """
    log.log_info(f"Starting UDP server on port {port} (ack={ack})")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))

    clients = {}        # to log, and handle multiple clients
    start_time = time.time()
    last_time = start_time

    if not ack:
        # -------------------- Task 3: server-only metrics --------------------
        # TODO:
        #   - recvfrom(...) loop
        #   - Parse ID from first 4B; update per-client stats
        #   - When elapsed >= interval (per client), compute:
        #       * bandwidth (bytes/elapsed)
        #       * loss = 1 - (recv_count / (max_id - min_id + 1))
        #       * jitter from consecutive arrival deltas
        #     then log via: log.report("server", ip, port, bandwidth=..., loss=..., jitter=...)

        while True:
            # recieving packet and adddress which it came from, from socket
            try:
                data, addr = sock.recvfrom(1472)
            except Exception as e:
                Logger.log_error(f"Error: {e}")
                continue

            header = data[:4]  # getting the first 4 bytes
            packet_id = struct.unpack('!I', header)[0]

            currentTime = time.time()

            if packet_id == 0:  # termination packet, so log data if there is any
                log.log_info(f"Received termination datagram (ID 0) from {addr}: finishing UDP session")
                if addr in clients and len(clients[addr]['packet_ids']) > 0:

                    elapsed = currentTime - clients[addr]['last_time']
                    # calulatin for current client by fetching its stats from dict
                    bandwidth = (
                        clients[addr]['total_bytes']/elapsed) * 8 / 1e6
                    expected_interval = (1472 * 8) / (rate * 1000)

                    arrival_times = clients[addr]['arrival_times']
                    packet_ids = clients[addr]['packet_ids']

                    loss = (1 - len(packet_ids) /
                            (max(packet_ids) - min(packet_ids) + 1)) * 100
                    # calulating loss per client
                    total = 0
                    if len(packet_ids) >= 2:  # needs at least two packets to calculate jitter
                        for i in range(1, len(arrival_times)):
                            gap = arrival_times[i] - arrival_times[i-1]
                            total += abs(gap - expected_interval)

                        jitter = (total / (len(arrival_times) - 1)) * 1000
                    else:
                        jitter = 0          # what if packet 1 and 2, 4 arrives and not 3?

                    log.log_stat(
                        timestamp=currentTime,
                        ip=addr[0],
                        port=addr[1],
                        bandwidth=bandwidth,
                        loss=loss,
                        jitter=jitter
                    )

                    # Clean up client data
                    del clients[addr]
                continue

            if addr not in clients:
                clients[addr] = {
                    'packet_ids': [],  
                    'arrival_times': [],
                    'total_bytes': 0,
                    'start_time': time.time(),
                    'last_time': time.time()
                }

            clients[addr]['packet_ids'].append(packet_id)
            clients[addr]['arrival_times'].append(
                currentTime)   # populate the client dicts
            clients[addr]['total_bytes'] += len(data)

            elapsed = currentTime - clients[addr]['last_time']

            if elapsed >= interval:  # when interval is reached report the log
                bandwidth = (clients[addr]['total_bytes']/elapsed) * 8 / 1e6
                expected_interval = (1472 * 8) / (rate * 1000)

                arrival_times = clients[addr]['arrival_times']
                packet_ids = clients[addr]['packet_ids']

                loss = (1 - len(packet_ids) /
                        (max(packet_ids) - min(packet_ids) + 1)) * 100

                total = 0
                if len(packet_ids) >= 2:  # needs at least two packets to calculate jitter
                    for i in range(1, len(arrival_times)):
                        gap = arrival_times[i] - arrival_times[i-1]
                        total += abs(gap - expected_interval)

                    jitter = (total / (len(arrival_times) - 1)) * 1000

                else:
                    jitter = 0

                log.log_stat(
                    timestamp=currentTime,
                    ip=addr[0],
                    port=addr[1],
                    bandwidth=bandwidth,
                    loss=loss,
                    jitter=jitter
                )

                clients[addr]['total_bytes'] = 0
                clients[addr]['packet_ids'] = []  # resetting
                clients[addr]['arrival_times'] = []
                clients[addr]['last_time'] = currentTime

        return None
    else:
        # -------------------- Task 4: add acknowledgements --------------------
        # TODO:
        #   - Same as above, and for each received datagram:
        #       * Build ack: 4B ID + timestamp (e.g., float via struct.pack)
        #       * sendto(ack, (ip, port))
        #   - Continue periodic logging as in Task 3

        while True:
            # recieving packet and adddress which it came from from socket
            try:
                data, addr = sock.recvfrom(1472)
            except Exception as e:
                log.log_error(f"Error: {e}")
                continue

            currentTime = time.time()
            if len(data) < 4:  #if the datagram is less than 4 bytes it cant contain a valid packet id
                continue

            header = data[:4]  # getting the first 4 bytes
            packet_id = struct.unpack('!I', header)[0]

            # Build ack: 4B ID + 8B server timestamp 
            ack = struct.pack('!Id', packet_id, currentTime)
            try:
                sock.sendto(ack, addr)
            except Exception as e:
                log.log_error(f"Error sending ACK: {e}")

            if packet_id == 0:  # if termination packet is sent
                # calculating stats per client to report in log
                log.log_info(f"Received termination datagram (ID 0) from {addr}: finishing UDP session")
                if addr in clients and len(clients[addr]['packet_ids']) > 0:
                    elapsed = currentTime - clients[addr]['last_time']
                    if elapsed <= 0:
                        elapsed = 1e-6

                    bandwidth = (clients[addr]['total_bytes']/elapsed) * 8 / 1e6
                    expected_interval = (1472 * 8) / (rate * 1000)

                    arrival_times = clients[addr]['arrival_times']
                    packet_ids = clients[addr]['packet_ids']

                    loss = (1 - len(packet_ids) /
                            (max(packet_ids) - min(packet_ids) + 1)) * 100

                    total = 0.0

                    if len(arrival_times) >= 2:  # needs at least two packets to calculate jitter
                        for i in range(1, len(arrival_times)):
                            gap = arrival_times[i] - arrival_times[i-1]
                            total += abs(gap - expected_interval)

                        jitter = (total / (len(arrival_times) - 1)) * 1000.0
                    else:
                        jitter = 0.0

                    log.log_stat(
                        timestamp=currentTime,
                        ip=addr[0],
                        port=addr[1],
                        bandwidth=bandwidth,
                        loss=loss,
                        jitter=jitter
                    )

                    del clients[addr]  # reset data
                continue

            if addr not in clients:  # create new client if it does not exist yet
                clients[addr] = {
                    'packet_ids': [],
                    'arrival_times': [],
                    'total_bytes': 0,
                    'start_time': currentTime,
                    'last_time': currentTime
                }

            clients[addr]['packet_ids'].append(packet_id)
            clients[addr]['arrival_times'].append(currentTime)
            clients[addr]['total_bytes'] += len(data)

            elapsed = currentTime - clients[addr]['last_time']

            if elapsed >= interval:  # when interval is reached report the log
                if elapsed <= 0:
                    elapsed = 1e-6

                bandwidth = (clients[addr]['total_bytes']/elapsed) * 8 / 1e6
                expected_interval = (1472 * 8) / (rate * 1000)

                arrival_times = clients[addr]['arrival_times']
                packet_ids = clients[addr]['packet_ids']

                loss = (1 - len(packet_ids) /
                        (max(packet_ids) - min(packet_ids) + 1)) * 100

                total = 0.0
                if len(arrival_times) >= 2:  # needs at least two packets to calculate jitter
                    for i in range(1, len(arrival_times)):
                        gap = arrival_times[i] - arrival_times[i-1]
                        total += abs(gap - expected_interval)

                    jitter = (total / (len(arrival_times) - 1)) * 1000.0

                else:
                    jitter = 0.0

                log.log_stat(
                    timestamp=currentTime,
                    ip=addr[0],
                    port=addr[1],
                    bandwidth=bandwidth,
                    loss=loss,
                    jitter=jitter
                )

                clients[addr]['total_bytes'] = 0
                clients[addr]['packet_ids'] = []        # resetting
                clients[addr]['arrival_times'] = []
                clients[addr]['last_time'] = currentTime

        return None



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SCC.231 net-tester application")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("-s", "--server", action="store_true",
                      help="Run in server mode")
    mode.add_argument("-c", "--client", metavar="ADDR",
                      help="Run in client mode, connect to ADDR")

    parser.add_argument("-p", "--port", type=int,
                        default=5001, help="Port (default 5001)")
    parser.add_argument("-u", "--udp", action="store_true",
                        help="Use UDP (default TCP)")
    parser.add_argument("-a", "--ack", action="store_true",
                        help="(UDP) Enable acknowledgements")
    parser.add_argument("-t", "--duration", type=int,
                        default=60, help="Test duration seconds (default 60)")
    parser.add_argument("-i", "--interval", type=int, default=1,
                        help="Report interval seconds (default 1)")
    parser.add_argument("-r", "--rate", type=int, default=1000,
                        help="(UDP) send rate Kbps (default 1000)")
    parser.add_argument('-l', '--log', type=str, default=None,
                        help='Path to CSV log file (default: None)')

    args = parser.parse_args()
    log = Logger(csv_output=args.log)

    if args.server:
        if args.udp:
            # Task 3/4 (no-op until implemented)
            tester_udp_server(log, args.port, args.rate,
                              args.interval, args.ack)
        else:
            # Task 2 (no-op until implemented)
            tester_tcp_server(log, args.port)
    else:
        if args.udp:
            tester_udp_client(log, args.client, args.port,
                              args.duration, args.interval,
                              args.rate, args.ack)        # Task 3/4 (no-op until implemented)
        else:
            tester_tcp_client(log, args.client, args.port,
                              args.duration, args.interval)  # Task 2 (no-op until implemented)
    log.summary()
    log.close()
