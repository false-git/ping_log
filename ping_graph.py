"""グラフを描くよ."""
import bokeh.models as bm
import bokeh.plotting as bp
import datetime
import dateutil.parser
import pandas as pd
import sqlite3
import typing as typ


def load_data() -> pd.Series:
    """データをロードする.

    Returns:
        データ
    """
    conn: sqlite3.Connection = sqlite3.connect("ping.db")
    ping_dict: typ.Dict[datetime.datetime, typ.Optional[float]] = {}
    for row in conn.execute("select * from ping order by created_at"):
        timestamp: datetime.datetime = dateutil.parser.parse(row[2]).replace(tzinfo=datetime.timezone.utc).astimezone()
        ping_dict[timestamp] = row[1]
    conn.close()
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
    sr: pd.Series = load_data()
    draw_graph(sr)


if __name__ == "__main__":
    main()
