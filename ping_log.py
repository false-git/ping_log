"""pingのログを取る."""
import bokeh.models as bm
import bokeh.plotting as bp
import configparser
import datetime
import dateutil.parser
import pandas as pd
import subprocess
import sqlite3
import time
import typing as typ
import ping3

GRAPH_DAYS: int = 2


def load_data(conn: sqlite3.Connection) -> pd.Series:
    """データをロードする.

    Returns:
        データ(直近GRAPH_DAYS日分)
    """
    ping_dict: typ.Dict[datetime.datetime, typ.Optional[float]] = {}
    for row in conn.execute(
        "select * from ping where created_at > ? order by created_at",
        (datetime.datetime.utcnow() - datetime.timedelta(GRAPH_DAYS),),
    ):
        timestamp: datetime.datetime = (
            dateutil.parser.parse(row[2]).replace(tzinfo=datetime.timezone.utc).astimezone().replace(tzinfo=None)
        )
        ping_dict[timestamp] = row[1]
    return pd.Series(ping_dict)


def draw_graph(sr: pd.Series) -> None:
    """グラフを描く.

    Args:
        sr: データ
    """
    df: pd.DataFrame = sr.resample("5min").agg(["min", "max", "mean"])
    df["timestamp"] = df.index
    source: bp.ColumnDataSource = bp.ColumnDataSource(df)
    tooltips: typ.List[typ.Tuple[str, str]] = [
        ("time", "@timestamp{%F %T}"),
        ("最小値", "@{min}{0,0.000}"),
        ("最大値", "@{max}{0,0.000}"),
        ("平均値", "@{mean}{0,0.000}"),
    ]
    hover_tool: bm.HoverTool = bm.HoverTool(tooltips=tooltips, formatters={"@timestamp": "datetime"})
    bp.output_file("graph/ping.html", title="Ping graph")
    fig: bp.figure = bp.figure(
        title="Ping graph",
        x_axis_type="datetime",
        x_axis_label="日時",
        y_axis_label="ping値[ms]",
        sizing_mode="stretch_both",
    )
    fig.add_tools(hover_tool)
    fmt: typ.List[str] = ["%m/%d %H:%M:%S"]
    fig.xaxis.formatter = bm.DatetimeTickFormatter(hours=fmt, hourmin=fmt, minutes=fmt)
    fig.line("index", "min", legend_label="最小値", line_color="blue", source=source)
    fig.line("index", "max", legend_label="最大値", line_color="red", source=source)
    fig.line("index", "mean", legend_label="平均値", line_color="green", source=source)
    fig.legend.click_policy = "hide"
    fig.legend.location = "top_left"

    bp.save(fig)


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
    sr: pd.Series = load_data(conn)
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
        sr[datetime.datetime.fromtimestamp(next_time)] = ping
        sr = sr.last(f"{GRAPH_DAYS}D")
        draw_graph(sr)
    conn.close()


if __name__ == "__main__":
    main()
