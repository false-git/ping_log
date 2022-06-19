# ping log

* 一定間隔で指定ホストにpingを打ち、response timeを記録します。
  * zabbix.db に sqlite3 でデータを記録します。
  * zabbixの設定があれば、zabbixにデータを送ります。
* ping_log.ini に設定を書きます。
  * ping セクション
    * host: pingを打つホスト。省略すると google DNS(8.8.8.8)
    * interval: ping を打つ間隔。省略すると10秒
  * zabbix セクション
    * server: zabbix server。省略すると zabbix_sender を呼ばない
    * port: zabbix serverのport。省略すると10051
    * host: zabbix に識別してもらうホスト名
    * key: zabbix trapperのkey
* `poetry install` で.venvを作ります。
* `poetry run python ping_log.py` でpingを無限実行します。
* `poetry run python ping_graph.py` で graph/ping.html にグラフを描きます。
  * 手抜きなので、全データを bokeh で出力します。
  * データ量が多くなるとまともに動かないと思います。
