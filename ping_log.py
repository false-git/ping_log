"""pingのログを取る."""
import configparser
import datetime
import subprocess
import sqlite3
import time
import typing as typ
import ping3


def main():
    """メイン."""
    inifile: configparser.ConfigParser = configparser.ConfigParser()
    inifile.read("ping_log.ini", "utf-8")
    interval: int = inifile.getint("ping", "interval", fallback=10)
    ping_host: str = inifile.get("ping", "host", fallback="8.8.8.8")
    zabbix_server: str = inifile.get("zabbix", "server")
    zabbix_port: str = inifile.getint("zabbix", "port", fallback=10051)
    zabbix_host: str = inifile.get("zabbix", "host")
    zabbix_key: str = inifile.get("zabbix", "key", fallback="ping")
    if zabbix_server:
        zabbix_command: typ.List[str] = [
            "zabbix_sender",
            "-z",
            zabbix_server,
            "-p",
            f"{zabbix_port}",
            "-s",
            zabbix_host,
            "-i",
            "zabbix.trap",
        ]

    conn: sqlite3.Connection = sqlite3.connect("ping.db")
    while True:
        now: float = time.time()
        next_time: int = (int(now) // interval + 1) * interval
        time.sleep(next_time - now)
        ping: typ.Optional[float] = ping3.ping(ping_host, unit="ms")
        conn.execute(
            "insert into ping (ping, created_at) values (?, ?)", (ping, datetime.datetime.utcfromtimestamp(next_time))
        )
        conn.commit()
        if zabbix_server and ping:
            with open("zabbix.trap", "wt") as zabbix_trap:
                print(f"- {zabbix_key} {ping}", file=zabbix_trap)
            with open("zabbix.log", "wt") as zabbix_log:
                subprocess.run(zabbix_command, stdout=zabbix_log, stderr=subprocess.STDOUT)
    conn.close()


if __name__ == "__main__":
    main()
