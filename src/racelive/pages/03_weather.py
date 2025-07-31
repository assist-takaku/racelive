""" ---------------------------------------------------------------------------------------------------------
    Weather Page for RaceLive

----------------------------------------------------------------------------------------------------------"""
import time
import json
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
from streamlit.column_config import Column
import plotly.express as px
from plotly import graph_objects as go
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import schedule
# import ambient


st.set_page_config(page_title="気象データ・セッション", layout="wide")
st.title("Weatherページ")



# sf_setfile = json.load(open("./data/racelive.json", "r", encoding="utf-8"))
# weapath = sf_setfile["weather Path"]

# weather_toggle = st.toggle("路気温データ取得・終了")

# # AmbientデータとWeatherデータの表示エリアを分けるために、2つの列を作成
# col_we1, col_we2 = st.columns([1, 1])

# # Ambientデータのデータフレーム表示エリア
# with col_we1:
#     # Containerを使用してグループ化
#     with st.container(border=True):
#         st.write("Ambientデータ")
#         # 空のデータフレームを作成
#         empty_ambient_df = pd.DataFrame(columns=["時間", "気温 (Ambient)", "ピット", "路温", "湿度 (Ambient)", "気圧 (Ambient)"])
#         # カスタム列設定
#         column_config_a = {
#             "時間": Column(label="時間", width=50),
#             "気温 (Ambient)": Column(label="気温", width=50),
#             "ピット": Column(label="ピット", width=50),
#             "路温": Column(label="路温", width=50),
#             "湿度 (Ambient)": Column(label="湿度", width=50),
#             "気圧 (Ambient)": Column(label="気圧", width=50)
#         }

#         # プレースホルダーを作成
#         ambient_table_placeholder = st.empty()

#         empty_ambient_df = empty_ambient_df.set_index("時間")  # 時間をインデックスに設定

#         # 空のデータフレームを初期表示
#         ambient_table_placeholder.dataframe(empty_ambient_df, height=300, column_config=column_config_a)

# # Weatherデータのデータフレーム表示エリア
# with col_we2:
#     # Containerを使用してグループ化
#     with st.container(border=True):
#         st.write("Weatherデータ")
#         # 空のデータフレームを作成
#         empty_weather_df = pd.DataFrame(columns=["時間", "気温", "湿度", "風速", "風向", "気圧"])
#         # カスタム列設定
#         column_config_w = {
#             "時間": Column(label="時間", width=50),
#             "気温": Column(label="気温", width=50),
#             "湿度": Column(label="湿度", width=50),
#             "風速": Column(label="風速", width=50),
#             "風向": Column(label="風向", width=50),
#             "気圧": Column(label="気圧", width=50),
#         }

#         # プレースホルダーを作成
#         weather_table_placeholder = st.empty()

#         # 日付をインデックスに設定
#         empty_weather_df = empty_weather_df.set_index("時間")  # 日付をインデックスに設定

#         # 空のデータフレームを初期表示
#         weather_table_placeholder.dataframe(empty_weather_df, height=300, column_config=column_config_w)

# # AmbientデータとWeatherデータのグラフ表示エリアを分けるために、2つの列を作成
# col_we3, col_we4 = st.columns([1, 1])

# # Ambientデータのグラフ表示エリア
# with col_we3:
#     # Containerを使用してグループ化
#     with st.container(border=True):
#         st.write("Ambientデータ")
#         # グラフ用のプレースホルダーをcontainer内で作成
#         ambient_graph_placeholder = st.empty()

# # Weatherデータのグラフ表示エリア
# with col_we4:
#     # Containerを使用してグループ化
#     with st.container(border=True):
#         st.write("Weatherデータ")
#         # グラフ用のプレースホルダーをcontainer内で作成
#         weather_graph_placeholder = st.empty()

# # AmbientデータとWeatherデータの取得・保存をスレッドで実行
# if weather_toggle:
#     # セッションステートから値を取得（なければデフォルト値を使う）
#     ambient_id = st.session_state.get("ambient_id", 51094)
#     ambient_read_key = st.session_state.get("ambient_readKey", "35059f455d307f2d")

#     am = ambient.Ambient(ambient_id, "", ambient_read_key)


#     def ambientdata():
#         # 最新のデータを取得
#         d = am.read(n=1)
#         df = pd.DataFrame(d)
#         df["created"] = pd.to_datetime(list(df["created"])).tz_convert("Asia/Tokyo").tz_localize(None)
#         df = df.set_index("created")

#         # インデックスをリセットしてリストに変換
#         df_reset = df.reset_index()
#         data_list = df_reset.values.tolist()

#         # セッションステートにデータを追加
#         if "ambdata" not in st.session_state:
#             st.session_state.ambdata = []
#         st.session_state.ambdata.extend(data_list)

#         # データフレームを作成
#         # df_all_data = pd.DataFrame(data_list, columns=["日付", "気温 (Ambient)", "ピット", "路温", "湿度 (Ambient)", "気圧 (Ambient)"])
#         df_all_data = pd.DataFrame(st.session_state.ambdata, columns=["日付", "気温 (Ambient)", "ピット", "路温", "湿度 (Ambient)", "気圧 (Ambient)"])
#         df_all_data["時間"] = df_all_data["日付"].dt.strftime("%H:%M")
#         df_all_data["日付"] = df_all_data["日付"].dt.date
#         df_all_data = df_all_data.set_index("時間")
#         df_all_data = df_all_data.drop(columns=["日付"])

#         # # セッションステートに保存
#         st.session_state["ambient_data_df"] = df_all_data

#         # カスタム列設定
#         column_config = {
#             "気温 (Ambient)": Column(label="気温", width=50),
#             "ピット": Column(label="ピット", width=50),
#             "路温": Column(label="路温", width=50),
#             "湿度 (Ambient)": Column(label="湿度", width=50),
#             "気圧 (Ambient)": Column(label="気圧", width=50)
#         }

#         # テーブルを更新
#         ambient_table_placeholder.dataframe(df_all_data, height=300, column_config=column_config)

#         # Plotlyでグラフを作成
#         fig = go.Figure()

#         # 気温のラインを追加
#         fig.add_trace(go.Scatter(
#             x=df_all_data.index,
#             y=df_all_data["気温 (Ambient)"],
#             mode="lines",
#             name="Temp",
#             line=dict(color="tomato", width=2, dash="dash")
#         ))

#         # 路温のラインを追加
#         fig.add_trace(go.Scatter(
#             x=df_all_data.index,
#             y=df_all_data["路温"],
#             mode="lines",
#             name="Track",
#             line=dict(color="royalblue", width=2)
#         ))

#         # グラフのレイアウトを設定
#         fig.update_layout(
#             title="Temp & Track",
#             xaxis_title="Time",
#             yaxis_title="Temperature (°C)",
#             xaxis=dict(tickfont=dict(size=10)),
#             yaxis=dict(range=[5, 50], tickfont=dict(size=10)),
#             legend=dict(font=dict(size=10)),
#             height=300,
#             margin=dict(l=20, r=20, t=30, b=20)
#         )

#         # グラフを更新
#         ambient_graph_placeholder.plotly_chart(fig, use_container_width=True)


#     def weatherdata():
#         # Session Stateからウェザーデータ保存先を取得
#         df_weather = pd.read_csv(weapath, delim_whitespace=True, header=1)		

#         # セッションステートにデータを追加	
#         if "weather_data_list" not in st.session_state:	
#             st.session_state.weather_data_list = []	

#         # 最終行を取得して特定の列を選択（列番号で指定）	
#         weather_last_row = df_weather.tail(1)	
#         selected_columns = weather_last_row.iloc[:, [1, 2, 5, 7, 8, 15]]	

#         # 新しい列名を設定	
#         selected_columns.columns = ["時間", "気温", "湿度", "風速", "風向", "気圧"]	
#         # リストに変換してセッションステートに追加	
#         st.session_state.weather_data_list.extend(selected_columns.values.tolist())	

#         # weather_table_placeholderに渡すデータをDataFrameに変換	
#         weather_data_df = pd.DataFrame(
#             st.session_state.weather_data_list,	
#             columns=["時間", "気温", "湿度", "風速", "風向", "気圧"]  # 列名を明示的に指定	
#         )
#         # 時間をインデックスに設定	
#         weather_data_df = weather_data_df.set_index("時間")

#         # セッションステートに保存
#         st.session_state["weather_data_df"] = weather_data_df

#         # 最終行を取得して特定の列を選択
#         weather_last_row = df_weather.tail(1)

#         # カスタム列設定	
#         column_config_w = {	
#             "気温": Column(label="気温",width=50,),
#             "湿度": Column(label="湿度",width=50,),
#             "風速": Column(label="風速",width=50,),
#             "風向": Column(label="風向",width=50,),
#             "気圧": Column(label="気圧",width=50,)
#         }

#         # DataFrameを渡してテーブルを更新	
#         weather_table_placeholder.dataframe(weather_data_df, height=300, column_config=column_config_w)	

#         # Plotlyでグラフを作成
#         fig = go.Figure()

#         # 気温のラインを追加
#         fig.add_trace(go.Scatter(
#             x=weather_data_df.index,
#             y=weather_data_df["気温"],
#             mode="lines",
#             name="Temp",
#             line=dict(color="tomato", width=2, dash="dash"),
#             yaxis="y"
#         ))

#         # 湿度のラインを追加
#         fig.add_trace(go.Scatter(
#             x=weather_data_df.index,
#             y=weather_data_df["湿度"],
#             mode="lines",
#             name="Hum %",
#             line=dict(color="royalblue", width=2),
#             yaxis="y2"
#         ))

#         # グラフのレイアウトを設定
#         fig.update_layout(
#             title="Temp & Hum",
#             xaxis_title="Time",
#             yaxis=dict(
#                 title="Temp (°C)",
#                 range=[5, 50],
#                 tickfont=dict(size=10),
#                 side="left"
#             ),
#             yaxis2=dict(
#                 title="Humidity (%)",
#                 range=[0, 100],
#                 tickfont=dict(size=10),
#                 side="right",
#                 overlaying="y"
#             ),
#             xaxis=dict(tickfont=dict(size=10)),
#             legend=dict(font=dict(size=10)),
#             height=300,
#             margin=dict(l=20, r=20, t=30, b=20)
#         )

#         # グラフを更新
#         weather_graph_placeholder.plotly_chart(fig, use_container_width=True)


#     # スケジュール設定
#     schedule.every().minute.at(":03").do(ambientdata)
#     schedule.every().minute.at(":05").do(weatherdata)

#     # データ更新ループ
#     while weather_toggle:
#         schedule.run_pending()
#         time.sleep(1)

#     else:
#         st.write("データ取得が停止しました。")


# # データ表示部分（トグルの状態に関係なく常に表示）
# # Ambientデータ表示
# if "ambient_data_df" in st.session_state:
#     ambient_table_placeholder.dataframe(
#         st.session_state["ambient_data_df"],
#         height=300,
#         column_config={
#             "気温 (Ambient)": Column(label="気温", width=50),
#             "ピット": Column(label="ピット", width=50),
#             "路温": Column(label="路温", width=50),
#             "湿度 (Ambient)": Column(label="湿度", width=50),
#             "気圧 (Ambient)": Column(label="気圧", width=50)
#         }
#     )
#     # グラフも再描画
#     df_all_data = st.session_state["ambient_data_df"]
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=df_all_data.index,
#         y=df_all_data["気温 (Ambient)"],
#         mode="lines",
#         name="Temp",
#         line=dict(color="tomato", width=2, dash="dash")
#     ))
#     fig.add_trace(go.Scatter(
#         x=df_all_data.index,
#         y=df_all_data["路温"],
#         mode="lines",
#         name="Track",
#         line=dict(color="royalblue", width=2)
#     ))
#     fig.update_layout(
#         title="Temp & Track",
#         xaxis_title="Time",
#         yaxis_title="Temperature (°C)",
#         xaxis=dict(tickfont=dict(size=10)),
#         yaxis=dict(range=[5, 50], tickfont=dict(size=10)),
#         legend=dict(font=dict(size=10)),
#         height=300,
#         margin=dict(l=20, r=20, t=30, b=20)
#     )
#     ambient_graph_placeholder.plotly_chart(fig, use_container_width=True)

# # Weatherデータ表示
# if "weather_data_df" in st.session_state:
#     weather_table_placeholder.dataframe(
#         st.session_state["weather_data_df"],
#         height=300,
#         column_config={
#             "気温": Column(label="気温", width=50),
#             "湿度": Column(label="湿度", width=50),
#             "風速": Column(label="風速", width=50),
#             "風向": Column(label="風向", width=50),
#             "気圧": Column(label="気圧", width=50)
#         }
#     )
#     weather_data_df = st.session_state["weather_data_df"]
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=weather_data_df.index,
#         y=weather_data_df["気温"],
#         mode="lines",
#         name="Temp",
#         line=dict(color="tomato", width=2, dash="dash"),
#         yaxis="y"
#     ))
#     fig.add_trace(go.Scatter(
#         x=weather_data_df.index,
#         y=weather_data_df["湿度"],
#         mode="lines",
#         name="Hum %",
#         line=dict(color="royalblue", width=2),
#         yaxis="y2"
#     ))
#     fig.update_layout(
#         title="Temp & Hum",
#         xaxis_title="Time",
#         yaxis=dict(
#             title="Temp (°C)",
#             range=[5, 50],
#             tickfont=dict(size=10),
#             side="left"
#         ),
#         yaxis2=dict(
#             title="Humidity (%)",
#             range=[0, 100],
#             tickfont=dict(size=10),
#             side="right",
#             overlaying="y"
#         ),
#         xaxis=dict(tickfont=dict(size=10)),
#         legend=dict(font=dict(size=10)),
#         height=300,
#         margin=dict(l=20, r=20, t=30, b=20)
#     )
#     weather_graph_placeholder.plotly_chart(fig, use_container_width=True)
