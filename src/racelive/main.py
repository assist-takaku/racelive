""" ---------------------------------------------------------------------------------------------------------
    Super Formula Race Live   Ver : 1.2.5  2025.06

    poetry run streamlit run src/racelive/main.py
    終了方法 : ターミナルでCtrl + Cを押すと Local host が停止しStreamlitが終了します。

    seleniumを使用して、Webページからデータを取得し、Streamlitで表示するアプリケーションです。
    1.  Seleniumを使用して、指定されたURLからデータを取得します。
    2.  取得したデータをDataFrameに変換し、Streamlitで表示します。
    3.  Ambient APIを使用して、指定されたIDとreadKeyを使用しデータを取得しDataFrameに変換し、Streamlitで表示します。
    4.  ウェザーデータ・フォルダーに記録されるデータ使用してDataFrameに変換し、Streamlitで表示します。
    5.  DataFrameに変換したデータはグラフでも表示されます。
    6.  各セッションやレースの開始時間と終了時間を指定し、指定された時間にデータを取得します。
    7.  レースタブでは、レースのラップタイムの表示やレース戦略の表示ができます。
    8.  タブ前のデータ表示エリアでは、タブを移動しても見ることができるようにAmbientとウェザーデータを表示します。
    9.  スクレイピング、Ambient API、ウェザーデータは、スレッドを使用して同時に実行されます。
    10. 取得したデータはそれぞれCSVファイルに保存します。
    11. イベント終了後、取得したデータを元にライブと同じようにリプレイすることができます。
    12. イベントやチーム情報はDATAフォルダー内のJSONファイルを読み込み、変更があったときには修正保存できる。
    13. サイドバーにセッションを選択するドロップダウンメニューを作成し選択したセッションの情報を表示します。
    14. コードが長くなったてきたので Ver1.2以降で、スクリプト、関数を分けて整理しました。

    プロジェクトのファイル構成
    ├── racelive
        ├── .streamlit
        │   ├── config.toml          # Streamlitの設定ファイル
        ├── data
        │   ├── racelive.json        # 設定用JSONファイル
        │   ├── livetime.csv         # ライブタイムデータ一時保存ファイル
        ├── src/racelive
            ├── livego.py            # スクレイピング・メソッド、Webページからデータを取得csvにする
            ├── main.py              # Streamlitダッシュボードアプリケーション
            ├── utils.py             # ユーティリティ（データの保存や読み込みなど、複数のファイルで共通して使う関数）
            ├── scraperead.py        # livegor.pyで取得したデータをDataFrameに変換するメソッド
            ├── const.py             # streamlit定数設定
            ├── pages                # ページ設定
                ├── 01_practice.py   # Practiceセッション・ページ
                ├── 02_race.py       # Raceセッション・ページ
                ├── 03_weather.py    # Weatherセッション・ページ
                ├── 04_about.py      # このアプリケーションについて

----------------------------------------------------------------------------------------------------------"""
import os
import sys
from pathlib import Path
import time
import threading
import json
import schedule
import concurrent.futures
import subprocess
import signal
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from plotly import graph_objects as go
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import streamlit as st
from streamlit.column_config import Column
from streamlit_autorefresh import st_autorefresh

# psutilのインポート（プロセス管理用）
import psutil

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from racelive.scraperead import Racelivescraper
from racelive.utils import Datalist
from racelive import const


st.set_page_config(**const.SET_PAGE_CONFIG)
st.markdown(const.HIDE_ST_STYLE,unsafe_allow_html=True)


# -------------------------- 設定用Jsonファイルの読み込み -----------------------------------------------------
sf_setfile = json.load(open("./data/racelive.json", "r", encoding="utf-8"))

category_list = [n["Name"] for n in sf_setfile["Category"]]
circuit_list = [n["Name"] for n in sf_setfile["Circuit"]]
session_list = [n["Name"] for n in sf_setfile["Session"]]

time_path = sf_setfile["Time Path"]
weather_Path = sf_setfile["weather Path"]
ambientid = sf_setfile["ambient ID"]
ambientreadKey = sf_setfile["ambient readKey"]
lastevent = sf_setfile["Last Event"]
lastcategory = sf_setfile["Last Category"]
lastsession = sf_setfile["Last Session"]
race_lap = sf_setfile["Race Lap"]

# オフセット値を取得（デフォルト値を設定）
default_offset_start = sf_setfile.get("Offset Start", 1)
default_offset_end = sf_setfile.get("Offset End", 3)
# --------------------------------------------------------------------------------------------------------


# -------------------------- サイドバー設定 ---------------------------------------------------------------


# -------------------------- タブ前データ表示エリア ----------------------------------------------------------

# with st.container(border=True):

#     # タブ前データ表示エリア列設定
#     col_w1, col_w2, col_w3, col_w4, col_w5, col_w6, col_w7, col_w8 = st.columns([1, 1, 1, 1, 1, 1, 1, 1])

#     with col_w1: weather_temp_placeholder = st.empty()
#     with col_w2: ambient_track_temp_placeholder = st.empty()
#     with col_w3: weather_wind_speed_placeholder = st.empty()
#     with col_w4: weather_wind_dir_placeholder = st.empty()
#     with col_w5: st.write("")
#     with col_w6: st.write("")
#     with col_w7: st.write("")
#     with col_w8: st.write("")


# -------------------------- タブの作成 --------------------------------------------------------------------
setup, teaminfo, circuit = st.tabs(["Setup", "Team Information", "Circuit"])


# -------------------------- イベント情報の表示・編集タブ --------------------------------------------------
with setup:

    # タイトルメッセージ表示
    st.write("# Super Formula Race Live SetUp")
    st.write("")

    # カテゴリ選択ボックス
    col_s1, col_s2, col_s3, col_s4, col_s5, col_s6, col_s7 = st.columns([1, 1, 1, 1, 1, 1, 1])

    with col_s1:
        with st.container(border=True):
            # カテゴリ選択ボックス
            category_name = st.selectbox(
                "カテゴリ選択",
                category_list,
                index=category_list.index(st.session_state.get("last_selected_category", category_list[lastcategory])),
            )
            # 選択されたカテゴリをセッションステートに保存
            st.session_state["category_name"] = category_name

            # 選択されたカテゴリのインデックスを取得
            selected_category_index = category_list.index(category_name)

            # サイドバーに条件付きでfile_uploaderを表示
            if category_name == "SF RePlay":
                uploaded_file = st.file_uploader(
                    label="",  # ラベルを空にする
                    type="csv",
                    label_visibility="collapsed"  # ラベルとスペースを非表示
                )
                # ファイルがアップロードされた場合
                if uploaded_file is not None:
                    try:
                        # アップロードされたCSVファイルをDataFrameとして読み込む
                        df_uploaded = pd.read_csv(uploaded_file, encoding="shift-jis")
                    except Exception as e:
                        st.error(f"ファイルの読み込みに失敗しました: {e}")

            # 選択されたカテゴリに基づいてURLを更新
            if "categoryurl" not in st.session_state or st.session_state.get("last_selected_category") != category_name:
                st.session_state["categoryurl"] = sf_setfile["Category"][selected_category_index]["URL"]
                st.session_state["last_selected_category"] = category_name # 選択されたカテゴリを記録

            # カテゴリに基づいてチームリストを取得
            datal = Datalist(selected_category_index)
            teamlist, mk, mk2 = datal.teamlist()
            driver_list, car_no_list = datal.driverlist()
            # DataFrame に変換してセッションステートに保存
            df_team = pd.DataFrame(teamlist)
            st.session_state["df_team"] = df_team

    # イベント名入力
    with col_s2:
        with st.container(border=True):
            st.text_input("イベント", value=lastevent, key="lastevent_name")

    # サーキット選択ボックス
    with col_s3:
        with st.container(border=True):
            last_circuit_index = sf_setfile["Last Circuit"]
            # サーキット選択ボックス
            circuit_name = st.selectbox(
                "サーキット選択",
                circuit_list,
                index=circuit_list.index(st.session_state.get("circuit_name", circuit_list[last_circuit_index])),
                key="circuit_name"
            )
            # 選択されたサーキットのインデックスを取得
            selected_circuit_index = circuit_list.index(circuit_name)
            st.session_state["selected_circuit_index"] = selected_circuit_index
            sector = sf_setfile["Circuit"][selected_circuit_index]["Sector"]
            st.session_state["sector"] = sector

    # 参加台数表示
    with col_s4:
        with st.container(border=True):
            car_max = st.text_input("参加台数 :", value=len(car_no_list ), key="car_max")

    # セッション・スタート・オフセット値入力
    with col_s5:
        with st.container(border=True):
            offset_start= st.number_input(
                "スタート・オフセット・分単位",
                min_value=0,
                max_value=10,
                value=default_offset_start,
                step=1
            )

    # セッション・エンド・オフセット値入力
    with col_s6:
        with st.container(border=True):
            offset_end = st.number_input(
                "エンド・オフセット・分単位",
                min_value=0,
                max_value=10,
                value=default_offset_end,
                step=1
            )

    # 設定保存ボタン
    with col_s7:
        with st.container(border=True):
            st.write("")
            # プッシュボタン
            if st.button("データ保存"):
                # JSONデータを更新
                sf_setfile["Time Path"] = st.session_state.get("livetime_file_path", time_path)
                sf_setfile["weather Path"] = st.session_state.get("weather_file_path", weather_Path)
                sf_setfile["ambient ID"] = st.session_state.get("ambient_id", ambientid)
                sf_setfile["ambient readKey"] = st.session_state.get("ambient_readKey", ambientreadKey)
                sf_setfile["Last Event"] = st.session_state.get("lastevent_name", lastevent)
                sf_setfile["Last Circuit"] = st.session_state.get("selected_circuit_index", sf_setfile["Last Circuit"])
                sf_setfile["Last URL"] = st.session_state.get("categoryurl", sf_setfile["Last URL"])
                sf_setfile["Last Category"] = category_list.index(st.session_state["category_name"])
                sf_setfile["Last Session"] = st.session_state.get("selected_session_index", 0)
                
                # オフセット値を保存
                sf_setfile["Offset Start"] = offset_start
                sf_setfile["Offset End"] = offset_end

                # 選択されたカテゴリのURLを更新
                selected_category_index = category_list.index(st.session_state.get("last_selected_category", category_list[0]))
                sf_setfile["Category"][selected_category_index]["URL"] = st.session_state.get("categoryurl", "")

                # イベント・タイム・テーブルのデータを更新
                for i in range(10):  # セッションは1～10まで
                    session_key = f"session{i+1}_name"
                    date_key = f"session{i+1}_date"
                    start_key = f"session{i+1}_start"
                    end_key = f"session{i+1}_end"

                    sf_setfile["Session"][i]["Name"] = st.session_state.get(session_key, sf_setfile["Session"][i]["Name"])
                    sf_setfile["Session"][i]["Date"] = st.session_state.get(date_key, sf_setfile["Session"][i]["Date"])
                    sf_setfile["Session"][i]["StartTime"] = st.session_state.get(start_key, sf_setfile["Session"][i]["StartTime"])
                    sf_setfile["Session"][i]["EndTime"] = st.session_state.get(end_key, sf_setfile["Session"][i]["EndTime"])
                    sf_setfile["Session"][i]["Lap"] = st.session_state.get(f"session{i+1}_lap", sf_setfile["Session"][i]["Lap"])

                # JSONファイルに書き込み
                with open("./data/racelive.json", "w", encoding="utf-8") as f:
                    json.dump(sf_setfile, f, ensure_ascii=False, indent=4)

                # セッションリストを更新してサイドバーに反映
                session_list = [n["Name"] for n in sf_setfile["Session"]]
                
                # 保存成功フラグを設定
                st.session_state["save_success"] = True
                
                # ページを再読み込みしてサイドバーの表示を更新
                st.rerun()
            
            # 保存成功メッセージ表示
            if st.session_state.get("save_success"):
                # カスタムCSSでメッセージボックスのサイズを調整
                st.markdown(
                    """
                    <style>
                    .custom-success {
                        background-color: #d4edda;
                        border: 1px solid #c3e6cb;
                        color: #155724;
                        padding: 8px 12px;
                        border-radius: 4px;
                        margin: 4px 0;
                        font-size: 14px;
                        text-align: center;
                    }
                    </style>
                    <div class="custom-success">
                        ✅ 変更を保存しました。
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                # メッセージを一度だけ表示するためにフラグをリセット
                st.session_state["save_success"] = False


    with st.container(border=True):
        st.write("イベント・タイム・テーブル")
        ses1, ses2, ses3, ses4, ses5, ses6, ses7, ses8, sec9, sec10= st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        with ses1:
            with st.container(border=True):
                st.text_input("セッション1", value=sf_setfile["Session"][0]["Name"], key="session1_name")
                st.text_input("日時", value=sf_setfile["Session"][0]["Date"], key="session1_date")
                st.text_input("開始時間", value=sf_setfile["Session"][0]["StartTime"], key="session1_start")
                st.text_input("終了時間", value=sf_setfile["Session"][0]["EndTime"], key="session1_end")
                st.text_input("周回数", value=sf_setfile["Session"][0]["Lap"], key="session1_lap")
        with ses2:
            with st.container(border=True):
                st.text_input("セッション2", value=sf_setfile["Session"][1]["Name"], key="session2_name")
                st.text_input("日時", value=sf_setfile["Session"][1]["Date"], key="session2_date")
                st.text_input("開始時間", value=sf_setfile["Session"][1]["StartTime"], key="session2_start")
                st.text_input("終了時間", value=sf_setfile["Session"][1]["EndTime"], key="session2_end")
                st.text_input("周回数", value=sf_setfile["Session"][1]["Lap"], key="session2_lap")
        with ses3:
            with st.container(border=True):
                st.text_input("セッション3", value=sf_setfile["Session"][2]["Name"], key="session3_name")
                st.text_input("日時", value=sf_setfile["Session"][2]["Date"], key="session3_date")
                st.text_input("開始時間", value=sf_setfile["Session"][2]["StartTime"], key="session3_start")
                st.text_input("終了時間", value=sf_setfile["Session"][2]["EndTime"], key="session3_end")
                st.text_input("周回数", value=sf_setfile["Session"][2]["Lap"], key="session3_lap")
        with ses4:
            with st.container(border=True):
                st.text_input("セッション4", value=sf_setfile["Session"][3]["Name"], key="session4_name")
                st.text_input("日時", value=sf_setfile["Session"][3]["Date"], key="session4_date")
                st.text_input("開始時間", value=sf_setfile["Session"][3]["StartTime"], key="session4_start")
                st.text_input("終了時間", value=sf_setfile["Session"][3]["EndTime"], key="session4_end")
                st.text_input("周回数", value=sf_setfile["Session"][3]["Lap"], key="session4_lap")
        with ses5:
            with st.container(border=True):
                st.text_input("セッション5", value=sf_setfile["Session"][4]["Name"], key="session5_name")
                st.text_input("日時", value=sf_setfile["Session"][4]["Date"], key="session5_date")
                st.text_input("開始時間", value=sf_setfile["Session"][4]["StartTime"], key="session5_start")
                st.text_input("終了時間", value=sf_setfile["Session"][4]["EndTime"], key="session5_end")
                st.text_input("周回数", value=sf_setfile["Session"][4]["Lap"], key="session5_lap")
        with ses6:
            with st.container(border=True):
                st.text_input("セッション6", value=sf_setfile["Session"][5]["Name"], key="session6_name")
                st.text_input("日時", value=sf_setfile["Session"][5]["Date"], key="session6_date")
                st.text_input("開始時間", value=sf_setfile["Session"][5]["StartTime"], key="session6_start")
                st.text_input("終了時間", value=sf_setfile["Session"][5]["EndTime"], key="session6_end")
                st.text_input("周回数", value=sf_setfile["Session"][5]["Lap"], key="session6_lap")
        with ses7:
            with st.container(border=True):
                st.text_input("セッション7", value=sf_setfile["Session"][6]["Name"], key="session7_name")
                st.text_input("日時", value=sf_setfile["Session"][6]["Date"], key="session7_date")
                st.text_input("開始時間", value=sf_setfile["Session"][6]["StartTime"], key="session7_start")
                st.text_input("終了時間", value=sf_setfile["Session"][6]["EndTime"], key="session7_end")
                st.text_input("周回数", value=sf_setfile["Session"][6]["Lap"], key="session7_lap")
        with ses8:
            with st.container(border=True):
                st.text_input("セッション8", value=sf_setfile["Session"][7]["Name"], key="session8_name")
                st.text_input("日時", value=sf_setfile["Session"][7]["Date"], key="session8_date")
                st.text_input("開始時間", value=sf_setfile["Session"][7]["StartTime"], key="session8_start")
                st.text_input("終了時間", value=sf_setfile["Session"][7]["EndTime"], key="session8_end")
                st.text_input("周回数", value=sf_setfile["Session"][7]["Lap"], key="session8_lap")
        with sec9:
            with st.container(border=True):
                st.text_input("セッション9", value=sf_setfile["Session"][8]["Name"], key="session9_name")
                st.text_input("日時", value=sf_setfile["Session"][8]["Date"], key="session9_date")
                st.text_input("開始時間", value=sf_setfile["Session"][8]["StartTime"], key="session9_start")
                st.text_input("終了時間", value=sf_setfile["Session"][8]["EndTime"], key="session9_end")
                st.text_input("周回数", value=sf_setfile["Session"][8]["Lap"], key="session9_lap")
        with sec10:
            with st.container(border=True):
                st.text_input("セッション10", value=sf_setfile["Session"][9]["Name"], key="session10_name")
                st.text_input("日時", value=sf_setfile["Session"][9]["Date"], key="session10_date")
                st.text_input("開始時間", value=sf_setfile["Session"][9]["StartTime"], key="session10_start")
                st.text_input("終了時間", value=sf_setfile["Session"][9]["EndTime"], key="session10_end")
                st.text_input("周回数", value=sf_setfile["Session"][9]["Lap"], key="session10_lap")

    # 設定タブ：情報表示・編集3列目
    col_s10, col_s11 = st.columns([1, 1])
    with col_s10:
        with st.container(border=True):
            col_s6_1, col_s6_2 = st.columns([1, 2])
            with col_s6_1:
                st.markdown(
                    """
                    <div style="display: flex; justify-content: center; align-items: center; height: 100%; 
                    color: black; font-size: 14px; font-weight: bold;">
                        タイムデータ保存先
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_s6_2:
                st.text_input("タイムデータ保存先", label_visibility="collapsed", value=time_path, key="livetime_file_path")

    with col_s11:
        with st.container(border=True):
            col_s7_1, col_s7_2 = st.columns([1, 2])
            with col_s7_1:
                st.markdown(
                    """
                    <div style="display: flex; justify-content: center; align-items: center; height: 100%; 
                    color: black; font-size: 14px; font-weight: bold;">
                        ウェザーデータ読み込み先
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_s7_2:
                st.text_input("ウェザーデータ読み込み先", label_visibility="collapsed", value=weather_Path, key="weather_file_path")

    # 設定タブ：情報表示・編集4列目
    with st.container(border=True):
        col_s9, col_s10, col_s11, col_s12, col_s13, col_s14 = st.columns([1, 1, 1, 1, 1, 3])
        with col_s9:
            st.write("Ambient ID")
        with col_s10:
            ambientid = st.text_input("Ambient ID", label_visibility="collapsed", value=ambientid, key="ambient_id")
        with col_s11:
            st.write("Ambient ReadKey")
        with col_s12:
            ambientkey = st.text_input("Ambient ReadKey", label_visibility="collapsed", value=ambientreadKey, key="ambient_readKey")
        with col_s13:
            st.write("Race Live URL")
        with col_s14:
            url = st.text_input("URL", label_visibility="collapsed", key="categoryurl")


# -------------------------- チーム情報の表示・編集タブ ----------------------------------------------------
with teaminfo:
    st.write("Team Data")

    with st.container(border=True):

        edited_df_team = st.data_editor(df_team.reset_index(drop=True), height=600, hide_index=True, num_rows="dynamic")

        # 保存ボタン　メーカー（S耐クラス）順でソートして、Car Noの最小値でソート
        if st.button("チーム情報を保存"):
            team_json_list = []
            def car_no_key(x):
                try:
                    return int(x)
                except Exception:
                    return x

            # Team NameとMakerの両方でグループ化
            for (team_name, maker), group in edited_df_team.groupby(["Team Name", "Maker"]):
                group_sorted = group.copy()
                group_sorted["Car No Sort"] = group_sorted["Car No"].apply(car_no_key)
                group_sorted = group_sorted.sort_values("Car No Sort").drop(columns="Car No Sort")
                car_list = []
                for _, row in group_sorted.iterrows():
                    car = [
                        row["Car No"],
                        row["Driver Name1"],
                        row["Driver Name2"],
                        row["Driver Name3"],
                        row["Driver URL"]
                    ]
                    car_list.append(car)
                # チームごとの最小Car Noを取得（ソート用）
                min_car_no = min([car_no_key(row["Car No"]) for _, row in group_sorted.iterrows()])
                team_json_list.append({
                    "Name": team_name,
                    "Maker": maker,
                    "Car": car_list,
                    "_sort_maker": maker,
                    "_sort_carno": min_car_no
                })

            # チームリストを「Car No（最小）」→「Maker」順でソート
            team_json_list = sorted(team_json_list, key=lambda x: (x["_sort_carno"], x["_sort_maker"]))

            # ソート用の一時キーを削除
            for team in team_json_list:
                team.pop("_sort_maker")
                team.pop("_sort_carno")

            sf_setfile["Category"][selected_category_index]["Team"] = team_json_list

            with open("./data/racelive.json", "w", encoding="utf-8") as f:
                json.dump(sf_setfile, f, ensure_ascii=False, indent=4)

            st.success("チーム情報を保存しました")


# -------------------------- レースタブ ------------------------------------------------------------------
with circuit:
    st.write("Circuit Data")

    # CircuitデータをDataFrame化
    circuit_df = pd.DataFrame(sf_setfile["Circuit"])

    # 編集用データフレーム
    edited_circuit_df = st.data_editor(
        circuit_df,
        height=400,
        hide_index=True,
        num_rows="dynamic"
    )

    # 保存ボタン
    if st.button("サーキット情報を保存"):
        # DataFrameをdictのリストに変換してJSONへ反映
        sf_setfile["Circuit"] = edited_circuit_df.to_dict(orient="records")
        with open("./data/racelive.json", "w", encoding="utf-8") as f:
            json.dump(sf_setfile, f, ensure_ascii=False, indent=4)
        st.success("サーキット情報を保存しました")


# -------------------------- サイドバー設定 ----------------------------------------------------------------
# サイドバーにスクレイピング制御を追加
with st.sidebar:
    st.markdown("### スクレイピング制御")
    
    # 制御ファイルのパス
    control_file = "./data/scraping_control.json"
    
    # 現在の状態を読み込み
    if os.path.exists(control_file):
        try:
            with open(control_file, "r", encoding="utf-8") as f:
                control_data = json.load(f)
            current_status = control_data.get("scraping", False)
            status_message = control_data.get("message", "")
            last_update = control_data.get("timestamp", "")
        except:
            current_status = False
            status_message = ""
            last_update = ""
    else:
        current_status = False
        status_message = ""
        last_update = ""
    
    # 状態表示
    status_text = "🟢 実行中" if current_status else "🔴 停止中"
    st.write(f"**現在の状態**: {status_text}")
    # if status_message:
    #     st.caption(f"詳細: {status_message}")
    # if last_update:
    #     st.caption(f"更新時刻: {last_update[:19]}")
    
    # トグルで制御
    scraping_status = st.toggle("スクレイピング制御", value=current_status, key="scraping_control")
    
    # 状態が変更された場合にファイルに保存
    if scraping_status != current_status:
        control_data = {
            "scraping": scraping_status,
            "timestamp": datetime.now().isoformat(),
            "command_from": "main.py"
        }
        
        os.makedirs(os.path.dirname(control_file), exist_ok=True)
        with open(control_file, "w", encoding="utf-8") as f:
            json.dump(control_data, f, ensure_ascii=False, indent=2)
        
        if scraping_status:
            st.success("✅ スクレイピング開始指示を送信")
        else:
            st.info("⏹️ スクレイピング停止指示を送信")

    # 最新のJSONファイルを再読み込みしてセッションリストを更新
    current_sf_setfile = json.load(open("./data/racelive.json", "r", encoding="utf-8"))
    current_session_list = [n["Name"] for n in current_sf_setfile["Session"]]
    
    # 選択されたセッションのインデックスを取得
    session_name = st.sidebar.selectbox("セッション選択", current_session_list, index=current_sf_setfile["Last Session"])
    selected_session_index = current_session_list.index(session_name)

    # 選択されたセッションの詳細を取得
    time_path = current_sf_setfile["Time Path"]
    lastevent = current_sf_setfile["Last Event"]
    selected_session = current_sf_setfile["Session"][selected_session_index]
    session_date = selected_session["Date"]
    session_start = selected_session["StartTime"]
    session_end = selected_session["EndTime"]
    lap_number = selected_session["Lap"]

    # サイドバーに日時、開始時間、終了時間を表示
    st.sidebar.markdown(f"**日時:** {session_date}")
    st.sidebar.markdown(f"**開始時間:** {session_start}")
    st.sidebar.markdown(f"**終了時間:** {session_end}")
    st.sidebar.markdown(f"**周回数:** {lap_number}")
    
    # 操作手順をより綺麗に表示
    st.sidebar.markdown("---")
    st.sidebar.info(
        """
        📝 **操作手順**
        
        1. セッションを選択
        2. OKボタンを押す
        3. スクレイピングを実行
        """
    )

    # セッション選択ボタンの処理
    if st.sidebar.button("OK"):
        # JSONファイルのデータを更新
        current_sf_setfile["Last Session"] = selected_session_index
        current_sf_setfile["Last StartTime"] = session_start
        current_sf_setfile["Last EndTime"] = session_end
        current_sf_setfile["Race Lap"] = lap_number
        
        # JSONファイルに保存
        with open("./data/racelive.json", "w", encoding="utf-8") as f:
            json.dump(current_sf_setfile, f, ensure_ascii=False, indent=4)


    st.markdown("---")
    st.markdown("### プロセス制御")
    
    # livego.pyのプロセス状態をチェック
    def is_livego_running():
        """livego.pyが実行中かチェック"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('livego.py' in arg for arg in cmdline):
                        return True, proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False, None
        except Exception:
            return False, None
    
    is_running, pid = is_livego_running()
    
    # プロセス状態表示
    if is_running:
        st.success(f"🟢 livego.py 実行中 (PID: {pid})")
        
        # 停止ボタン
        if st.button("🛑 livego.py 停止", key="stop_livego"):
            try:
                if pid:
                    os.kill(pid, signal.SIGTERM)
                    st.success("livego.pyを停止しました")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"停止エラー: {e}")
    else:
        st.info("⚪ livego.py 停止中")
        
        # 開始ボタン
        if st.button("▶️ livego.py 開始", key="start_livego"):
            try:
                # バックグラウンドでlivego.pyを起動
                subprocess.Popen([
                    sys.executable, 
                    "src/racelive/livego.py"
                ], 
                cwd=os.getcwd(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
                )
                st.success("livego.pyを開始しました")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"開始エラー: {e}")

    # st.markdown("---")
    # st.caption("または、ターミナルでバックグラウンド実行")
    # st.code("poetry run python src/racelive/livego.py")
