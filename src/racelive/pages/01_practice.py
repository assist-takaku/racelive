""" ---------------------------------------------------------------------------------------------------------
    Practice Page for RaceLive Ver1.2

----------------------------------------------------------------------------------------------------------"""
import os
import sys
from pathlib import Path
import time
from datetime import datetime
import json
import numpy as np
import pandas as pd
import threading
import pyperclip
import plotly.express as px

import streamlit as st
from streamlit.column_config import Column
from streamlit_autorefresh import st_autorefresh

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from racelive.scraperead import Racelivescraper
from racelive.utils import Datalist
from racelive import const


st.set_page_config(page_title="Practiceページ", layout="wide")


# -------------------------- 設定用Jsonファイルの読み込み ------------------------------------------------------------
# 時間表示フォーマット
datetime.now().strftime("%Y/%m/%d %H:%M:%S")
today = datetime.now().strftime("%Y/%m/%d")

sf_setfile = json.load(open("./data/racelive.json", "r", encoding="utf-8"))

session_list = [n["Name"] for n in sf_setfile["Session"]]
race_lap = sf_setfile["Race Lap"]
lastcategory = sf_setfile["Last Category"]
url = sf_setfile["Last URL"]
# セクターの値を取得
sector = st.session_state.get("sector", 4)

# カテゴリに基づいてチームリストを取得
datal = Datalist(lastcategory)
teamlist, mk, mk2 = datal.teamlist()
df0 = datal.data_db(race_lap)
driver_list, car_no_list = datal.driverlist()

weather_Path = sf_setfile["weather Path"]
ambientid = sf_setfile["ambient ID"]
ambientreadKey = sf_setfile["ambient readKey"]

csv_path = "./data/livetime.csv"

# 空のデータフレーム用車両台数
try:
    max_pos = int(len(driver_list))
except Exception:
    max_pos = 22  # デフォルト値


def seconds_to_laptime(sec):
    """秒(float)を mm:ss.000 形式の文字列に変換"""
    if not np.isfinite(sec):
        return np.nan
    m = int(sec // 60)
    s = sec % 60
    return f"{m}:{s:06.3f}"



# -------------------------- サイドバー設定 ------------------------------------------------------------------------
st.sidebar.markdown("## Session Info")

# 選択されたセッションのインデックスを取得
session_name = st.sidebar.selectbox("セッション選択", session_list, index=0)
selected_session_index = session_list.index(session_name)

# 選択されたセッションの詳細を取得
time_path = sf_setfile["Time Path"]
lastevent = sf_setfile["Last Event"]
selected_session = sf_setfile["Session"][selected_session_index]
session_date = selected_session["Date"]
session_start = selected_session["StartTime"]
session_end = selected_session["EndTime"]
race_lap = st.session_state.get("race_lap", race_lap)

# サイドバーに日時、開始時間、終了時間を表示
st.sidebar.markdown(f"**日時:** {session_date}")
st.sidebar.markdown(f"**開始時間:** {session_start}")
st.sidebar.markdown(f"**終了時間:** {session_end}")
st.sidebar.markdown(f"**レースラップ:** {race_lap}")
st.sidebar.write("")

# セッション選択ボタンの処理
if st.sidebar.button("セッション選択"):
    # JSONファイルのデータを更新
    sf_setfile["Last Session"] = selected_session_index
    sf_setfile["Last StartTime"] = session_start
    sf_setfile["Last EndTime"] = session_end
    
    # JSONファイルに保存
    with open("./data/racelive.json", "w", encoding="utf-8") as f:
        json.dump(sf_setfile, f, ensure_ascii=False, indent=4)

st.sidebar.write("")
st.sidebar.write("")


# -------------------------- 空データフレーム事前設定 ------------------------------------------------------------------------
# -------------------------- Sectorの値によって表示カラムを切り替え -----------------------------------------------------------
# メーカー別 Coliumns設定
if sector == 3:
    time_display_columns = ["Pos", "CarNo", "Driver Name", "LapTime", "Sec 1", "Sec 2", "Sec 3", "Speed"]
    column_config = {
        "Pos": Column(label="Pos", width=15),
        "CarNo": Column(label="No", width=15),
        "Driver Name": Column(label="Driver", width=150),
        "LapTime": Column(label="LapTime", width=50),
        "Sec 1": Column(label="Sector1", width=40),
        "Sec 2": Column(label="Sector2", width=40),
        "Sec 3": Column(label="Sector3", width=40),
        "Speed": Column(label="Speed", width=40),
    }
else:
    time_display_columns = ["Pos", "CarNo", "Driver Name", "LapTime", "Sec 1", "Sec 2", "Sec 3", "Sec 4", "Speed"]
    column_config = {
        "Pos": Column(label="Pos", width=15),
        "CarNo": Column(label="No", width=15),
        "Driver Name": Column(label="Driver", width=150),
        "LapTime": Column(label="LapTime", width=50),
        "Sec 1": Column(label="Sector1", width=40),
        "Sec 2": Column(label="Sector2", width=40),
        "Sec 3": Column(label="Sector3", width=40),
        "Sec 4": Column(label="Sector4", width=40),
        "Speed": Column(label="Speed", width=40),
    }

# ベスト Coliumns設定
if sector == 3:
    best_display_columns = ["Driver Name", "LapTime", "Sec 1", "Sec 2", "Sec 3", "Speed"]
    column_config = {
        "Driver Name": Column(label="Driver", width=150),
        "LapTime": Column(label="LapTime", width=50),
        "Sec 1": Column(label="Sector1", width=40),
        "Sec 2": Column(label="Sector2", width=40),
        "Sec 3": Column(label="Sector3", width=40),
        "Speed": Column(label="Speed", width=40),
    }
else:
    best_display_columns = ["Driver Name", "LapTime", "Sec 1", "Sec 2", "Sec 3", "Sec 4", "Speed"]
    column_config = {
        "Driver Name": Column(label="Driver", width=150),
        "LapTime": Column(label="LapTime", width=50),
        "Sec 1": Column(label="Sector1", width=40),
        "Sec 2": Column(label="Sector2", width=40),
        "Sec 3": Column(label="Sector3", width=40),
        "Sec 4": Column(label="Sector4", width=40),
        "Speed": Column(label="Speed", width=40),
    }


# ドライバー別 Coliumns設定1
if sector == 3:
    dr_display_columns1 = ["", "LapTime", "Sec 1", "Sec 2", "Sec 3", "Speed"]
    column_config = {
        "": Column(label="", width=50),
        "LapTime": Column(label="LapTime", width=50),
        "Sec 1": Column(label="Sec 1", width=40),
        "Sec 2": Column(label="Sec 2", width=40),
        "Sec 3": Column(label="Sec 3", width=40),
        "Speed": Column(label="Speed", width=40),
    }
else:
    dr_display_columns1 = ["", "LapTime", "Sec 1", "Sec 2", "Sec 3", "Sec 4", "Speed"]
    column_config = {
        "": Column(label="", width=50),
        "LapTime": Column(label="LapTime", width=50),
        "Sec 1": Column(label="Sec 1", width=40),
        "Sec 2": Column(label="Sec 2", width=40),
        "Sec 3": Column(label="Sec 3", width=40),
        "Sec 4": Column(label="Sec 4", width=40),
        "Speed": Column(label="Speed", width=40),
    }

# ドライバー別 Coliumns設定2
if sector == 3:
    dr_display_columns2 = ["Lap", "LapTime", "Sec 1", "Sec 2", "Sec 3", "Speed"]
    column_config = {
        "Lap": Column(label="Lap", width=15),
        "LapTime": Column(label="LapTime", width=50),
        "Sec 1": Column(label="Sec 1", width=40),
        "Sec 2": Column(label="Sec 2", width=40),
        "Sec 3": Column(label="Sec 3", width=40),
        "Speed": Column(label="Speed", width=40),
    }
else:
    dr_display_columns2 = ["Lap", "LapTime", "Sec 1", "Sec 2", "Sec 3", "Sec 4", "Speed"]
    column_config = {
        "Lap": Column(label="Lap", width=15),
        "LapTime": Column(label="LapTime", width=50),
        "Sec 1": Column(label="Sec 1", width=40),
        "Sec 2": Column(label="Sec 2", width=40),
        "Sec 3": Column(label="Sec 3", width=40),
        "Sec 4": Column(label="Sec 4", width=40),
        "Speed": Column(label="Speed", width=40),
    }



# 空のデータフレームを作成
# メーカー別タイム・データ用
empty_time_df = pd.DataFrame({col: [""] * max_pos for col in time_display_columns})

# 選択ドライバー・ベストタイム・データ用
empty_timebest_df = pd.DataFrame({col: ["", ""] for col in best_display_columns})
empty_timebest_df.iloc[1, 0] = "Theoretical Time"

empty_dr_timebest_df = pd.DataFrame({col: ["", ""] for col in best_display_columns})

# ドライバー別タイム・データ用
empty_driver_df1 = pd.DataFrame({col: ["", ""] for col in dr_display_columns1})
empty_driver_df1.iloc[0, 0] = "Best Time"
empty_driver_df1.iloc[1, 0] = "Theoretical"
empty_driver_df2 = pd.DataFrame({col: [""] * max_pos for col in dr_display_columns2})
if "Lap" in empty_driver_df2.columns:
    empty_driver_df2["Lap"] = range(1, max_pos + 1)


# セクター別タイム・データ用・ラップタイムベスト順
if "sector_display_df0" not in st.session_state:
    st.session_state.sector_display_df0 = pd.DataFrame({col: [""] * max_pos for col in ["Pos", "CarNo", "Driver Name", "LapTime"]})
# セクター別タイム・データ用・セクター1ベスト順
if "sector_display_df1" not in st.session_state:
    st.session_state.sector_display_df1 = pd.DataFrame({col: [""] * max_pos for col in ["Pos", "CarNo", "Driver Name", "Sec 1"]})
# セクター別タイム・データ用・セクター2ベスト順
if "sector_display_df2" not in st.session_state:
    st.session_state.sector_display_df2 = pd.DataFrame({col: [""] * max_pos for col in ["Pos", "CarNo", "Driver Name", "Sec 2"]})
# セクター別タイム・データ用・セクター3ベスト順
if "sector_display_df3" not in st.session_state:
    st.session_state.sector_display_df3 = pd.DataFrame({col: [""] * max_pos for col in ["Pos", "CarNo", "Driver Name", "Sec 3"]})
# セクター別タイム・データ用・セクター4ベスト順
if "sector_display_df4" not in st.session_state:
    st.session_state.sector_display_df4 = pd.DataFrame({col: [""] * max_pos for col in ["Pos", "CarNo", "Driver Name", "Sec 4"]})
# セクター別タイム・データ用・スピードベスト順
if "sector_display_df5" not in st.session_state:
    st.session_state.sector_display_df5 = pd.DataFrame({col: [""] * max_pos for col in ["Pos", "CarNo", "Driver Name", "Speed"]})


# セッション状態にデータフレームを保持
# メーカー別タイム・データ用
if "display_time_df1" not in st.session_state:
    st.session_state.display_time_df1 = empty_time_df.copy()
if "display_time_df2" not in st.session_state:
    st.session_state.display_time_df2 = empty_time_df.copy()

# ベストタイム・サマリー用
if "display_timebest_df1" not in st.session_state:
    st.session_state.display_timebest_df1 = empty_timebest_df.copy()

if "display_vs_driver_df1" not in st.session_state:
    st.session_state.display_vs_driver_df1 = empty_dr_timebest_df.copy()
if "display_vs_driver_df2" not in st.session_state:
    st.session_state.display_vs_driver_df2 = empty_dr_timebest_df.copy()

# ドライバー別タイム・データ用
if "driver_display_df1_1" not in st.session_state:
    st.session_state.driver_display_df1_1 = empty_driver_df1.copy()
if "driver_display_df1_2" not in st.session_state:
    st.session_state.driver_display_df1_2 = empty_driver_df2.copy()

if "driver_display_df2_1" not in st.session_state:
    st.session_state.driver_display_df2_1 = empty_driver_df1.copy()
if "driver_display_df2_2" not in st.session_state:
    st.session_state.driver_display_df2_2 = empty_driver_df2.copy()

if "driver_display_df3_1" not in st.session_state:
    st.session_state.driver_display_df3_1 = empty_driver_df1.copy()
if "driver_display_df3_2" not in st.session_state:
    st.session_state.driver_display_df3_2 = empty_driver_df2.copy()

if "driver_display_df4_1" not in st.session_state:
    st.session_state.driver_display_df4_1 = empty_driver_df1.copy()
if "driver_display_df4_2" not in st.session_state:
    st.session_state.driver_display_df4_2 = empty_driver_df2.copy()


# セクター別タイム・データ用・ラップタイムベスト順
if "sector_display_df0" not in st.session_state:
    st.session_state.sector_display_df0 = empty_time_df.copy()
# セクター別タイム・データ用・セクター1ベスト順
if "sector_display_df1" not in st.session_state:
    st.session_state.sector_display_df1 = empty_time_df.copy()
# セクター別タイム・データ用・セクター2ベスト順
if "sector_display_df2" not in st.session_state:
    st.session_state.sector_display_df2 = empty_time_df.copy()
# セクター別タイム・データ用・セクター3ベスト順
if "sector_display_df3" not in st.session_state:
    st.session_state.sector_display_df3 = empty_time_df.copy()
# セクター別タイム・データ用・セクター4ベスト順
if "sector_display_df4" not in st.session_state:
    st.session_state.sector_display_df4 = empty_time_df.copy()
# セクター別タイム・データ用・スピードベスト順
if "sector_display_df5" not in st.session_state:
    st.session_state.sector_display_df5 = empty_time_df.copy()



# -------------------------- 最上部気象データ表示エリア ------------------------------------------------------------
with st.container(border=True):
    # 気象データ表示エリア列設定
    col_w1, col_w2, col_w3, col_w4, col_w5, col_w6, col_w7, col_w8 = st.columns([1, 1, 1, 1, 1, 1, 1, 1])

    with col_w1: st.write("")
    with col_w2: st.write("")
    with col_w3: st.write("")
    with col_w4: st.write("")
    with col_w5: st.write("")
    with col_w6: st.write("")
    with col_w7: st.write("")
    with col_w8: st.write("")



# -------------------------- ライブタイムデータ表示エリア ------------------------------------------------------------

# スクレイピング開始・停止をトグルで管理
livego_practice = st.sidebar.toggle("Live開始/停止", key="livego_practice")


col_p1, col_p2, col_p3 = st.columns([1, 1, 1])

# メーカー別タイム・データの表示エリア
with col_p1:
    with st.container(border=True):
        col_p1_s1, col_p1_s2 = st.columns([1, 2])
        with col_p1_s1:
            selected_maker1 = st.selectbox("メーカー選択", mk2, index=0, key="timesummary_maker1", label_visibility="collapsed")
        with col_p1_s2:
            st.write("")

    with st.container(border=True):
        # st.write("メーカー別タイム・データの表示エリア")
        column_config = {
            "Pos": Column(label="Pos", width=25),
            "CarNo": Column(label="No", width=25),
            "Driver Name": Column(label="Driver", width=120),
            "LapTime": Column(label="LapTime", width=50),
            "Sec 1": Column(label="Sector1", width=40),
            "Sec 2": Column(label="Sector2", width=40),
            "Sec 3": Column(label="Sector3", width=40),
            "Sec 4": Column(label="Sector4", width=40),
            "Speed": Column(label="Speed", width=40),
        }
        st.dataframe(
            st.session_state.display_time_df1,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
            height=500 
        )

# セッションベスト＆選択ドライバーのタイム比較表示エリア
with col_p2:
    with st.container(border=True):
        st.write("Fastest & Theoretical LapTime")
        column_config2 = {
            "Driver Name": Column(label="Driver", width=120),
            "LapTime": Column(label="LapTime", width=50),
            "Sec 1": Column(label="Sector1", width=40),
            "Sec 2": Column(label="Sector2", width=40),
            "Sec 3": Column(label="Sector3", width=40),
            "Sec 4": Column(label="Sector4", width=40),
            "Speed": Column(label="Speed", width=40),
        }
        st.dataframe(
            st.session_state.display_timebest_df1, 
            use_container_width=True, 
            hide_index=True,
            column_config=column_config2,
        )

    with st.container(border=True):
        col_dr1, col_dr2= st.columns([1, 3])
        with col_dr1:
            selected_driver1 = st.selectbox(
                "ドライバー選択", 
                driver_list, index=13, 
                key="selected_driver1", 
                label_visibility="collapsed"
            )
        with col_dr2:
            st.write("")

        # 選択ドライバーのベストタイム表示エリア
        st.dataframe(st.session_state.display_vs_driver_df1, use_container_width=True, hide_index=True)

    with st.container(border=True):
        col_dr3, col_dr4= st.columns([1, 3])
        with col_dr3:
            selected_driver2 = st.selectbox(
                "ドライバー選択", 
                driver_list, index=14, 
                key="selected_driver2", 
                label_visibility="collapsed"
            )
        with col_dr4:
            st.write("")

        # 選択ドライバーのベストタイム表示エリア
        st.dataframe(st.session_state.display_vs_driver_df2, use_container_width=True, hide_index=True)

# メーカー別タイム・データの表示エリア
with col_p3:
    with st.container(border=True):
        col_p3_s1, col_p3_s2 = st.columns([1, 2])
        with col_p3_s1:
            selected_maker2 = st.selectbox("メーカー選択", mk2, index=1, key="timesummary_maker2", label_visibility="collapsed")
        with col_p3_s2:
            st.write("")

    with st.container(border=True):
        # st.write("メーカー別タイム・データの表示エリア")
        column_config = {
            "Pos": Column(label="Pos", width=25),
            "CarNo": Column(label="No", width=25),
            "Driver Name": Column(label="Driver", width=120),
            "LapTime": Column(label="LapTime", width=50),
            "Sec 1": Column(label="Sector1", width=40),
            "Sec 2": Column(label="Sector2", width=40),
            "Sec 3": Column(label="Sector3", width=40),
            "Sec 4": Column(label="Sector4", width=40),
            "Speed": Column(label="Speed", width=40),
        }
        st.dataframe(
            st.session_state.display_time_df2,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
            height=500 
        )


# -------------------------- ドライバー別タイムデータ表示エリア -------------------------------------------------------
col_d1, col_d2, col_d3, col_d4= st.columns([1, 1, 1, 1])

# ドライバー1タイムデータ表示エリア
with col_d1:
    # ドライバー選択 
    with st.container(border=True):
        with st.container(border=True):
            col_d1_s1, col_d1_s2, col_d1_s3= st.columns([1, 1, 1])
            with col_d1_s1:
                st.write("Driver")
            with col_d1_s2:
                selected_driver3 = st.selectbox("ドライバー選択", driver_list, index=13, key="selected_driver3", label_visibility="collapsed")
            with col_d1_s3:
                st.write("")

        # 選択ドライバーのベストタイム表示エリア
        with st.container(border=True):
            st.dataframe(st.session_state.driver_display_df1_1, use_container_width=True, hide_index=True)
        # 選択ドライバーのタイム・データの表示エリア
        with st.container(border=True):
            st.dataframe(st.session_state.driver_display_df1_2, use_container_width=True, hide_index=True)

# ドライバー2タイムデータ表示エリア
with col_d2:
    # ドライバー選択 
    with st.container(border=True):
        with st.container(border=True):
            col_d2_s1, col_d2_s2, col_d2_s3= st.columns([1, 1, 1])
            with col_d2_s1:
                st.write("Driver")
            with col_d2_s2:
                selected_driver4 = st.selectbox("ドライバー選択", driver_list, index=14, key="selected_driver4", label_visibility="collapsed")
            with col_d2_s3:
                st.write("")

        # 選択ドライバーのベストタイム表示エリア
        with st.container(border=True):
            st.dataframe(st.session_state.driver_display_df2_1, use_container_width=True, hide_index=True)
        # 選択ドライバーのタイム・データの表示エリア
        with st.container(border=True):
            st.dataframe(st.session_state.driver_display_df2_2, use_container_width=True, hide_index=True)

# ドライバー3タイムデータ表示エリア
with col_d3:
    # ドライバー選択 
    with st.container(border=True):
        with st.container(border=True):
            col_d3_s1, col_d3_s2, col_d3_s3= st.columns([1, 1, 1])
            with col_d3_s1:
                st.write("Driver")
            with col_d3_s2:
                selected_driver5 = st.selectbox("ドライバー選択", driver_list, index=0, key="selected_driver5", label_visibility="collapsed")
            with col_d3_s3:
                st.write("")

        # 選択ドライバーのベストタイム表示エリア
        with st.container(border=True):
            st.dataframe(st.session_state.driver_display_df3_1, use_container_width=True, hide_index=True)
        # 選択ドライバーのタイム・データの表示エリア
        with st.container(border=True):
            st.dataframe(st.session_state.driver_display_df3_2, use_container_width=True, hide_index=True)

# ドライバー4タイムデータ表示エリア
with col_d4:
    # ドライバー選択 
    with st.container(border=True):
        with st.container(border=True):
            col_d4_s1, col_d4_s2, col_d4_s3= st.columns([1, 1, 1])
            with col_d4_s1:
                st.write("Driver")
            with col_d4_s2:
                selected_driver6 = st.selectbox("ドライバー選択", driver_list, index=0, key="selected_driver6", label_visibility="collapsed")
            with col_d4_s3:
                st.write("")


        # 選択ドライバーのベストタイム表示エリア
        with st.container(border=True):
            st.dataframe(st.session_state.driver_display_df4_1, use_container_width=True, hide_index=True)
        # 選択ドライバーのタイム・データの表示エリア
        with st.container(border=True):
            st.dataframe(st.session_state.driver_display_df4_2, use_container_width=True, hide_index=True)


# -------------------------- セクター・サマリー表示エリア ------------------------------------------------------------

# セクター３用列エリア
if sector == 3:
    col4, col5, col6, col7, col9 = st.columns([1, 1, 1, 1, 1])
    # Laptimeベスト順
    with col4:
        with st.container(border=True):
            st.write("LapTime Best")
            st.dataframe(st.session_state.sector_display_df0, use_container_width=True, hide_index=True, height=820)
    # Sector1ベスト順
    with col5:
        with st.container(border=True):
            st.write("Sector 1 Best")
            st.dataframe(st.session_state.sector_display_df1, use_container_width=True, hide_index=True, height=820)
    # Sector2ベスト順
    with col6:
        with st.container(border=True):
            st.write("Sector 2 Best")
            st.dataframe(st.session_state.sector_display_df2, use_container_width=True, hide_index=True, height=820)
    # Sector3ベスト順
    with col7:
        with st.container(border=True):
            st.write("Sector 3 Best")
            st.dataframe(st.session_state.sector_display_df3, use_container_width=True, hide_index=True, height=820)
    # Speedベスト順
    with col9:
        with st.container(border=True):
            st.write("Speed Best")
            st.dataframe(st.session_state.sector_display_df5, use_container_width=True, hide_index=True, height=820)

# セクター４用列エリア
else:
    col4, col5, col6, col7, col8, col9 = st.columns([1, 1, 1, 1, 1, 1])
    # Laptimeベスト順
    with col4:
        with st.container(border=True):
            st.write("LapTime Best")
            st.dataframe(st.session_state.sector_display_df0, use_container_width=True, hide_index=True, height=820)
    # Sector1ベスト順
    with col5:
        with st.container(border=True):
            st.write("Sector 1 Best")
            st.dataframe(st.session_state.sector_display_df1, use_container_width=True, hide_index=True, height=820)
    # Sector2ベスト順
    with col6:
        with st.container(border=True):
            st.write("Sector 2 Best")
            st.dataframe(st.session_state.sector_display_df2, use_container_width=True, hide_index=True, height=820)
    # Sector3ベスト順
    with col7:
        with st.container(border=True):
            st.write("Sector 3 Best")
            st.dataframe(st.session_state.sector_display_df3, use_container_width=True, hide_index=True, height=820)
    # Sector4ベスト順
    with col8:
        with st.container(border=True):
            st.write("Sector 4 Best")
            st.dataframe(st.session_state.sector_display_df4, use_container_width=True, hide_index=True, height=820)
    # Speedベスト順
    with col9:
        with st.container(border=True):
            st.write("Speed Best")
            st.dataframe(st.session_state.sector_display_df5, use_container_width=True, hide_index=True, height=820)


# -------------------------- CSVファイルの自動リフレッシュ -----------------------------------------------------
if livego_practice:
    st_autorefresh(interval=5000, key="autorefresh")
    if os.path.exists(csv_path):
        mtime = os.path.getmtime(csv_path)
        if "csv_mtime" not in st.session_state:
            st.session_state.csv_mtime = 0
        if mtime != st.session_state.csv_mtime:
            practice_df = pd.read_csv(csv_path, encoding="shift-jis")

            # LapTime, Sec, Speed列を数値型に変換（エラー時はNaN）
            num_cols = ["LapTime", "Sec 1", "Sec 2", "Sec 3", "Sec 4", "Speed"]
            for col in num_cols:
                if col in practice_df.columns:
                    practice_df[col] = pd.to_numeric(practice_df[col], errors="coerce")


            # ----------------------------- CSVファイルの読み込みとデータフレームの作成 -----------------------------------------------------
            # 1つ目のデータフレーム
            # Maker列で絞り込み 各ドライバーのLapTimeが最小の行のみ抽出
            if "Maker" in practice_df.columns and "LapTime" in practice_df.columns:
                # Makerで絞り込み、CarNoごとにLapTimeが最小の行のみ抽出
                filtered_df = practice_df[practice_df["Maker"] == selected_maker1].copy()
                idx = filtered_df.groupby("CarNo")["LapTime"].idxmin()
                idx = idx.dropna()  # NaNを除外
                timesummary1 = filtered_df.loc[idx].copy()
                # "LapTime"の昇順で順位をつけてPos列を再設定
                timesummary1 = timesummary1.sort_values("LapTime", ascending=True)
                timesummary1["Pos"] = range(1, len(timesummary1) + 1)
                timesummary1 = (
                    timesummary1
                    .reindex(columns=time_display_columns)
                    .head(max_pos)
                    .fillna("")
                )
                # LapTime列をmm:ss.000形式に変換
                if "LapTime" in timesummary1.columns:
                    timesummary1["LapTime"] = timesummary1["LapTime"].apply(seconds_to_laptime)
                # Sec列（Sec 1, Sec 2, Sec 3, Sec 4）は小数点以下3位
                for sec_col in ["Sec 1", "Sec 2", "Sec 3", "Sec 4"]:
                    if sec_col in timesummary1.columns:
                        timesummary1[sec_col] = pd.to_numeric(timesummary1[sec_col], errors="coerce").map(lambda x: f"{x:.3f}" if pd.notnull(x) else "")
                # Speed列は小数点以下2位
                if "Speed" in timesummary1.columns:
                    timesummary1["Speed"] = pd.to_numeric(timesummary1["Speed"], errors="coerce").map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
            else:
                timesummary1 = practice_df.reindex(columns=time_display_columns).head(max_pos).fillna("")

            # 2つ目のデータフレーム
            # Maker列で絞り込み 各ドライバーのLapTimeが最小の行のみ抽出
            if "Maker" in practice_df.columns and "LapTime" in practice_df.columns:
                # Makerで絞り込み、CarNoごとにLapTimeが最小の行のみ抽出
                filtered_df = practice_df[practice_df["Maker"] == selected_maker2].copy()
                idx = filtered_df.groupby("CarNo")["LapTime"].idxmin()
                idx = idx.dropna()  # NaNを除外
                timesummary2 = filtered_df.loc[idx].copy()
                # "LapTime"の昇順で順位をつけてPos列を再設定
                timesummary2 = timesummary2.sort_values("LapTime", ascending=True)
                timesummary2["Pos"] = range(1, len(timesummary2) + 1)
                timesummary2 = (
                    timesummary2
                    .reindex(columns=time_display_columns)
                    .head(max_pos)
                    .fillna("")
                )
                # LapTime列をmm:ss.000形式に変換
                if "LapTime" in timesummary2.columns:
                    timesummary2["LapTime"] = timesummary2["LapTime"].apply(seconds_to_laptime)
                # Sec列（Sec 1, Sec 2, Sec 3, Sec 4）は小数点以下3位
                for sec_col in ["Sec 1", "Sec 2", "Sec 3", "Sec 4"]:
                    if sec_col in timesummary2.columns:
                        timesummary2[sec_col] = pd.to_numeric(timesummary2[sec_col], errors="coerce").map(lambda x: f"{x:.3f}" if pd.notnull(x) else "")
                # Speed列は小数点以下2位
                if "Speed" in timesummary2.columns:
                    timesummary2["Speed"] = pd.to_numeric(timesummary2["Speed"], errors="coerce").map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
            else:
                timesummary2 = practice_df.reindex(columns=time_display_columns).head(max_pos).fillna("")


            # ----------------------------- ベストタイム・サマリーの作成 -----------------------------------------------------
            # セッション・ベストタイムの抽出
            if "LapTime" in practice_df.columns and not practice_df["LapTime"].isna().all():
                # LapTimeにNaNでない値が存在する場合のみ処理を実行
                min_laptime_idx = practice_df["LapTime"].idxmin()
                
                # min_laptime_idxがNaNでないことを確認
                if pd.notnull(min_laptime_idx):
                    best_laptime_row = practice_df.loc[[min_laptime_idx]].reindex(columns=best_display_columns).fillna("")

                    # LapTime列をmm:ss.000形式に変換
                    if "LapTime" in best_laptime_row.columns:
                        best_laptime_row["LapTime"] = best_laptime_row["LapTime"].apply(seconds_to_laptime)

                    # 2行目: 各Secの最小値とSpeed最大値の行
                    if sector == 3:
                        sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3"] if col in practice_df.columns]
                    else:
                        sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3", "Sec 4"] if col in practice_df.columns]
                    
                    # NaNでない値が存在するかチェック
                    best_sec_values = {}
                    for col in sec_cols:
                        if col in practice_df.columns and not practice_df[col].isna().all():
                            best_sec_values[col] = practice_df[col].min()
                        else:
                            best_sec_values[col] = None
                    
                    best_speed_value = None
                    if "Speed" in practice_df.columns and not practice_df["Speed"].isna().all():
                        best_speed_value = practice_df["Speed"].max()

                    # 2行目のベース（LapTime最小行のコピー）
                    theoretical_row = practice_df.loc[[min_laptime_idx]].copy()
                    # 各Sec列を最小値、Speedを最大値に置換
                    for col in sec_cols:
                        if best_sec_values[col] is not None:
                            theoretical_row[col] = best_sec_values[col]
                    if best_speed_value is not None:
                        theoretical_row["Speed"] = best_speed_value
                    # LapTime列はSec合計値をセット（理論値なので）
                    if "LapTime" in theoretical_row.columns:
                        valid_secs = [v for v in best_sec_values.values() if v is not None]
                        if valid_secs:
                            sec_sum = sum(valid_secs)
                            theoretical_row["LapTime"] = seconds_to_laptime(sec_sum)
                    # Driver Name列に"Theoretical Time"をセット
                    if "Driver Name" in theoretical_row.columns:
                        theoretical_row["Driver Name"] = "Theoretical Time"

                    theoretical_row = theoretical_row.reindex(columns=best_display_columns).fillna("")

                    # 2行を結合
                    besttime_summary1 = pd.concat([best_laptime_row, theoretical_row], ignore_index=True)
                else:
                    # min_laptime_idxがNaNの場合は空のデータフレームを作成
                    besttime_summary1 = pd.DataFrame({col: ["", ""] for col in best_display_columns})
                    besttime_summary1.iloc[1, 0] = "Theoretical Time"
            else:
                # LapTimeが存在しないか全てNaNの場合は空のデータフレームを作成
                besttime_summary1 = pd.DataFrame({col: ["", ""] for col in best_display_columns})
                besttime_summary1.iloc[1, 0] = "Theoretical Time"


            # selected_driver1のベストタイムとセッションベストとの比較
            if "Driver" in practice_df.columns and "LapTime" in practice_df.columns:
                # selected_driver1のデータを抽出
                driver1_df = practice_df[practice_df["Driver"] == selected_driver1]
                if not driver1_df.empty and not driver1_df["LapTime"].isna().all():
                    # 1行目: selected_driver1のLapTime最小の行
                    min_idx = driver1_df["LapTime"].idxmin()
                    if pd.notnull(min_idx):
                        driver1_best_row = driver1_df.loc[[min_idx]].reindex(columns=best_display_columns).fillna("")
                        
                        # LapTimeをmm:ss.000形式に変換
                        if "LapTime" in driver1_best_row.columns:
                            driver1_best_row["LapTime"] = driver1_best_row["LapTime"].apply(seconds_to_laptime)
                        
                        # 2行目: セッションベストとの差分を計算
                        if "LapTime" in practice_df.columns:
                            session_best_laptime = practice_df["LapTime"].min()
                            driver1_best_laptime = driver1_df["LapTime"].min()
                            
                            # 差分行を作成
                            diff_row = driver1_best_row.copy()
                            
                            # LapTimeの差分を計算
                            if pd.notnull(driver1_best_laptime) and pd.notnull(session_best_laptime):
                                laptime_diff = driver1_best_laptime - session_best_laptime
                                if laptime_diff >= 0:
                                    diff_row["LapTime"] = f"+{laptime_diff:.3f}"
                                else:
                                    diff_row["LapTime"] = f"{laptime_diff:.3f}"
                            else:
                                diff_row["LapTime"] = ""

                            # セクタータイムの差分を計算
                            if sector == 3:
                                sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3"] if col in practice_df.columns]
                            else:
                                sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3", "Sec 4"] if col in practice_df.columns]
                            
                            for sec_col in sec_cols:
                                if sec_col in practice_df.columns:
                                    session_best_sec = practice_df[sec_col].min()
                                    driver1_best_sec = driver1_df[sec_col].min()
                                    
                                    if pd.notnull(driver1_best_sec) and pd.notnull(session_best_sec):
                                        sec_diff = driver1_best_sec - session_best_sec
                                        if sec_diff >= 0:
                                            diff_row[sec_col] = f"+{sec_diff:.3f}"
                                        else:
                                            diff_row[sec_col] = f"{sec_diff:.3f}"
                                    else:
                                        diff_row[sec_col] = ""
                            
                            # Speedの差分を計算
                            if "Speed" in practice_df.columns:
                                session_best_speed = practice_df["Speed"].max()
                                driver1_best_speed = driver1_df["Speed"].max()
                                
                                if pd.notnull(driver1_best_speed) and pd.notnull(session_best_speed):
                                    speed_diff = driver1_best_speed - session_best_speed
                                    if speed_diff >= 0:
                                        diff_row["Speed"] = f"+{speed_diff:.2f}"
                                    else:
                                        diff_row["Speed"] = f"{speed_diff:.2f}"
                                else:
                                    diff_row["Speed"] = ""
                            
                            # Driver Name列を設定
                            if "Driver Name" in diff_row.columns:
                                diff_row["Driver Name"] = "Difference"
                            
                            # 2行を結合
                            total_vs_driver_summary1 = pd.concat([driver1_best_row, diff_row], ignore_index=True)
                        else:
                            total_vs_driver_summary1 = driver1_best_row
                    else:
                        # min_idxがNaNの場合
                        total_vs_driver_summary1 = pd.DataFrame({col: ["", ""] for col in best_display_columns})
                else:
                    # ドライバーのデータがない場合
                    total_vs_driver_summary1 = pd.DataFrame({col: ["", ""] for col in best_display_columns})
            else:
                total_vs_driver_summary1 = pd.DataFrame({col: ["", ""] for col in best_display_columns})


            # selected_driver2のベストタイムとセッションベストとの比較
            if "Driver" in practice_df.columns and "LapTime" in practice_df.columns:
                # selected_driver2のデータを抽出
                driver2_df = practice_df[practice_df["Driver"] == selected_driver2]
                if not driver2_df.empty and not driver2_df["LapTime"].isna().all():
                    # 1行目: selected_driver2のLapTime最小の行
                    min_idx = driver2_df["LapTime"].idxmin()
                    if pd.notnull(min_idx):
                        driver2_best_row = driver2_df.loc[[min_idx]].reindex(columns=best_display_columns).fillna("")
                        
                        # LapTimeをmm:ss.000形式に変換
                        if "LapTime" in driver2_best_row.columns:
                            driver2_best_row["LapTime"] = driver2_best_row["LapTime"].apply(seconds_to_laptime)
                        
                        # 2行目: セッションベストとの差分を計算
                        if "LapTime" in practice_df.columns:
                            session_best_laptime = practice_df["LapTime"].min()
                            driver2_best_laptime = driver2_df["LapTime"].min()
                            
                            # 差分行を作成
                            diff_row = driver2_best_row.copy()
                            
                            # LapTimeの差分を計算
                            if pd.notnull(driver2_best_laptime) and pd.notnull(session_best_laptime):
                                laptime_diff = driver2_best_laptime - session_best_laptime
                                if laptime_diff >= 0:
                                    diff_row["LapTime"] = f"+{laptime_diff:.3f}"
                                else:
                                    diff_row["LapTime"] = f"{laptime_diff:.3f}"
                            else:
                                diff_row["LapTime"] = ""

                            
                            # セクタータイムの差分を計算
                            if sector == 3:
                                sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3"] if col in practice_df.columns]
                            else:
                                sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3", "Sec 4"] if col in practice_df.columns]
                            
                            for sec_col in sec_cols:
                                if sec_col in practice_df.columns:
                                    session_best_sec = practice_df[sec_col].min()
                                    driver2_best_sec = driver2_df[sec_col].min()
                                    
                                    if pd.notnull(driver2_best_sec) and pd.notnull(session_best_sec):
                                        sec_diff = driver2_best_sec - session_best_sec
                                        if sec_diff >= 0:
                                            diff_row[sec_col] = f"+{sec_diff:.3f}"
                                        else:
                                            diff_row[sec_col] = f"{sec_diff:.3f}"
                                    else:
                                        diff_row[sec_col] = ""

                            
                            # Speedの差分を計算
                            if "Speed" in practice_df.columns:
                                session_best_speed = practice_df["Speed"].max()
                                driver2_best_speed = driver2_df["Speed"].max()
                                
                                if pd.notnull(driver2_best_speed) and pd.notnull(session_best_speed):
                                    speed_diff = driver2_best_speed - session_best_speed
                                    if speed_diff >= 0:
                                        diff_row["Speed"] = f"+{speed_diff:.2f}"
                                    else:
                                        diff_row["Speed"] = f"{speed_diff:.2f}"
                                else:
                                    diff_row["Speed"] = ""
                            
                            # Driver Name列を設定
                            if "Driver Name" in diff_row.columns:
                                diff_row["Driver Name"] = "Difference"
                            
                            # 2行を結合
                            total_vs_driver_summary2 = pd.concat([driver2_best_row, diff_row], ignore_index=True)
                        else:
                            total_vs_driver_summary2 = driver2_best_row
                    else:
                        # min_idxがNaNの場合
                        total_vs_driver_summary2 = pd.DataFrame({col: ["", ""] for col in best_display_columns})
                else:
                    # ドライバーのデータがない場合
                    total_vs_driver_summary2 = pd.DataFrame({col: ["", ""] for col in best_display_columns})
            else:
                total_vs_driver_summary2 = pd.DataFrame({col: ["", ""] for col in best_display_columns})


            # ----------------------------- ドライバー別タイム・データの作成 -----------------------------------------------------
            # ドライバー1のタイムデータ
            if "Driver" in practice_df.columns and "LapTime" in practice_df.columns:
                driver_df = practice_df[practice_df["Driver"] == selected_driver3]
                if not driver_df.empty and not driver_df["LapTime"].isna().all():
                    # 1行目: LapTime最小の行
                    min_idx = driver_df["LapTime"].idxmin()
                    if pd.notnull(min_idx):
                        best_row = driver_df.loc[[min_idx]].reindex(columns=dr_display_columns1).fillna("")
                        # LapTimeをmm:ss.000形式に
                        if "LapTime" in best_row.columns:
                            best_row["LapTime"] = best_row["LapTime"].apply(seconds_to_laptime)

                        # 2行目: 各Secの最小値＋Speed最大値＋LapTimeはSec合計
                        if sector == 3:
                            sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3"] if col in driver_df.columns]
                        else:
                            sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3", "Sec 4"] if col in driver_df.columns]
                        best_sec_values = {col: driver_df[col].min() for col in sec_cols}
                        best_speed_value = driver_df["Speed"].max() if "Speed" in driver_df.columns else None

                        theoretical_row = best_row.copy()
                        for col in sec_cols:
                            theoretical_row[col] = best_sec_values[col]
                        if "Speed" in driver_df.columns and best_speed_value is not None:
                            theoretical_row["Speed"] = best_speed_value
                        # LapTimeはSec合計
                        if "LapTime" in theoretical_row.columns:
                            sec_sum = sum([best_sec_values[col] for col in sec_cols])
                            theoretical_row["LapTime"] = seconds_to_laptime(sec_sum)
                        # 1列目ラベル
                        if "" in best_row.columns:
                            best_row.iloc[0, 0] = "Best Time"
                            theoretical_row.iloc[0, 0] = "Theoretical"
                        # 結合
                        drivertime_df1_1 = pd.concat([best_row, theoretical_row], ignore_index=True)
                    else:
                        # min_idxがNaNの場合
                        drivertime_df1_1 = pd.DataFrame(columns=dr_display_columns1)
                else:
                    drivertime_df1_1 = pd.DataFrame(columns=dr_display_columns1)
            else:
                drivertime_df1_1 = pd.DataFrame(columns=dr_display_columns1)

            # selected_driver3で抽出
            if "Driver" in practice_df.columns:
                drivertime_df1_2 = (
                    practice_df[practice_df["Driver"] == selected_driver3]
                    .reindex(columns=dr_display_columns2)
                    .fillna("")
                )
                # LapTime列をmm:ss.000形式に変換
                if "LapTime" in drivertime_df1_2.columns:
                    drivertime_df1_2["LapTime"] = pd.to_numeric(drivertime_df1_2["LapTime"], errors="coerce").apply(seconds_to_laptime)
            else:
                drivertime_df1_2 = pd.DataFrame(columns=dr_display_columns2)

            # ドライバー2のタイムデータ
            if "Driver" in practice_df.columns and "LapTime" in practice_df.columns:
                driver_df = practice_df[practice_df["Driver"] == selected_driver4]
                if not driver_df.empty and not driver_df["LapTime"].isna().all():
                    # 1行目: LapTime最小の行
                    min_idx = driver_df["LapTime"].idxmin()
                    if pd.notnull(min_idx):
                        best_row = driver_df.loc[[min_idx]].reindex(columns=dr_display_columns1).fillna("")
                        # LapTimeをmm:ss.000形式に
                        if "LapTime" in best_row.columns:
                            best_row["LapTime"] = best_row["LapTime"].apply(seconds_to_laptime)

                        # 2行目: 各Secの最小値＋Speed最大値＋LapTimeはSec合計
                        if sector == 3:
                            sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3"] if col in driver_df.columns]
                        else:
                            sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3", "Sec 4"] if col in driver_df.columns]
                        best_sec_values = {col: driver_df[col].min() for col in sec_cols}
                        best_speed_value = driver_df["Speed"].max() if "Speed" in driver_df.columns else None

                        theoretical_row = best_row.copy()
                        for col in sec_cols:
                            theoretical_row[col] = best_sec_values[col]
                        if "Speed" in driver_df.columns and best_speed_value is not None:
                            theoretical_row["Speed"] = best_speed_value
                        # LapTimeはSec合計
                        if "LapTime" in theoretical_row.columns:
                            sec_sum = sum([best_sec_values[col] for col in sec_cols])
                            theoretical_row["LapTime"] = seconds_to_laptime(sec_sum)
                        # 1列目ラベル
                        if "" in best_row.columns:
                            best_row.iloc[0, 0] = "Best Time"
                            theoretical_row.iloc[0, 0] = "Theoretical"
                        # 結合
                        drivertime_df2_1 = pd.concat([best_row, theoretical_row], ignore_index=True)
                    else:
                        # min_idxがNaNの場合
                        drivertime_df2_1 = pd.DataFrame(columns=dr_display_columns1)
                else:
                    drivertime_df2_1 = pd.DataFrame(columns=dr_display_columns1)
            else:
                drivertime_df2_1 = pd.DataFrame(columns=dr_display_columns1)

            # selected_driver4で抽出
            if "Driver" in practice_df.columns:
                drivertime_df2_2 = (
                    practice_df[practice_df["Driver"] == selected_driver4]
                    .reindex(columns=dr_display_columns2)
                    .fillna("")
                )
                # LapTime列をmm:ss.000形式に変換
                if "LapTime" in drivertime_df2_2.columns:
                    drivertime_df2_2["LapTime"] = pd.to_numeric(drivertime_df2_2["LapTime"], errors="coerce").apply(seconds_to_laptime)
            else:
                drivertime_df2_2 = pd.DataFrame(columns=dr_display_columns2)

            # ドライバー3のタイムデータ
            if "Driver" in practice_df.columns and "LapTime" in practice_df.columns:
                driver_df = practice_df[practice_df["Driver"] == selected_driver5]
                if not driver_df.empty and not driver_df["LapTime"].isna().all():
                    # 1行目: LapTime最小の行
                    min_idx = driver_df["LapTime"].idxmin()
                    if pd.notnull(min_idx):
                        best_row = driver_df.loc[[min_idx]].reindex(columns=dr_display_columns1).fillna("")
                        # LapTimeをmm:ss.000形式に
                        if "LapTime" in best_row.columns:
                            best_row["LapTime"] = best_row["LapTime"].apply(seconds_to_laptime)

                        # 2行目: 各Secの最小値＋Speed最大値＋LapTimeはSec合計
                        if sector == 3:
                            sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3"] if col in driver_df.columns]
                        else:
                            sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3", "Sec 4"] if col in driver_df.columns]
                        best_sec_values = {col: driver_df[col].min() for col in sec_cols}
                        best_speed_value = driver_df["Speed"].max() if "Speed" in driver_df.columns else None

                        theoretical_row = best_row.copy()
                        for col in sec_cols:
                            theoretical_row[col] = best_sec_values[col]
                        if "Speed" in driver_df.columns and best_speed_value is not None:
                            theoretical_row["Speed"] = best_speed_value
                        # LapTimeはSec合計
                        if "LapTime" in theoretical_row.columns:
                            sec_sum = sum([best_sec_values[col] for col in sec_cols])
                            theoretical_row["LapTime"] = seconds_to_laptime(sec_sum)
                        # 1列目ラベル
                        if "" in best_row.columns:
                            best_row.iloc[0, 0] = "Best Time"
                            theoretical_row.iloc[0, 0] = "Theoretical"
                        # 結合
                        drivertime_df3_1 = pd.concat([best_row, theoretical_row], ignore_index=True)
                    else:
                        # min_idxがNaNの場合
                        drivertime_df3_1 = pd.DataFrame(columns=dr_display_columns1)
                else:
                    drivertime_df3_1 = pd.DataFrame(columns=dr_display_columns1)
            else:
                drivertime_df3_1 = pd.DataFrame(columns=dr_display_columns1)

            # selected_driver5で抽出
            if "Driver" in practice_df.columns:
                drivertime_df3_2 = (
                    practice_df[practice_df["Driver"] == selected_driver5]
                    .reindex(columns=dr_display_columns2)
                    .fillna("")
                )
                # LapTime列をmm:ss.000形式に変換
                if "LapTime" in drivertime_df3_2.columns:
                    drivertime_df3_2["LapTime"] = pd.to_numeric(drivertime_df3_2["LapTime"], errors="coerce").apply(seconds_to_laptime)
            else:
                drivertime_df3_2 = pd.DataFrame(columns=dr_display_columns2)

            # ドライバー4のタイムデータ
            if "Driver" in practice_df.columns and "LapTime" in practice_df.columns:
                driver_df = practice_df[practice_df["Driver"] == selected_driver6]
                if not driver_df.empty and not driver_df["LapTime"].isna().all():
                    # 1行目: LapTime最小の行
                    min_idx = driver_df["LapTime"].idxmin()
                    if pd.notnull(min_idx):
                        best_row = driver_df.loc[[min_idx]].reindex(columns=dr_display_columns1).fillna("")
                        # LapTimeをmm:ss.000形式に
                        if "LapTime" in best_row.columns:
                            best_row["LapTime"] = best_row["LapTime"].apply(seconds_to_laptime)

                        # 2行目: 各Secの最小値＋Speed最大値＋LapTimeはSec合計
                        if sector == 3:
                            sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3"] if col in driver_df.columns]
                        else:
                            sec_cols = [col for col in ["Sec 1", "Sec 2", "Sec 3", "Sec 4"] if col in driver_df.columns]
                        best_sec_values = {col: driver_df[col].min() for col in sec_cols}
                        best_speed_value = driver_df["Speed"].max() if "Speed" in driver_df.columns else None

                        theoretical_row = best_row.copy()
                        for col in sec_cols:
                            theoretical_row[col] = best_sec_values[col]
                        if "Speed" in driver_df.columns and best_speed_value is not None:
                            theoretical_row["Speed"] = best_speed_value
                        # LapTimeはSec合計
                        if "LapTime" in theoretical_row.columns:
                            sec_sum = sum([best_sec_values[col] for col in sec_cols])
                            theoretical_row["LapTime"] = seconds_to_laptime(sec_sum)
                        # 1列目ラベル
                        if "" in best_row.columns:
                            best_row.iloc[0, 0] = "Best Time"
                            theoretical_row.iloc[0, 0] = "Theoretical"
                        # 結合
                        drivertime_df4_1 = pd.concat([best_row, theoretical_row], ignore_index=True)
                    else:
                        # min_idxがNaNの場合
                        drivertime_df4_1 = pd.DataFrame(columns=dr_display_columns1)
                else:
                    drivertime_df4_1 = pd.DataFrame(columns=dr_display_columns1)
            else:
                drivertime_df4_1 = pd.DataFrame(columns=dr_display_columns1)

            # selected_driver6で抽出
            if "Driver" in practice_df.columns:
                drivertime_df4_2 = (
                    practice_df[practice_df["Driver"] == selected_driver6]
                    .reindex(columns=dr_display_columns2)
                    .fillna("")
                )
                # LapTime列をmm:ss.000形式に変換
                if "LapTime" in drivertime_df4_2.columns:
                    drivertime_df4_2["LapTime"] = pd.to_numeric(drivertime_df4_2["LapTime"], errors="coerce").apply(seconds_to_laptime)
            else:
                drivertime_df4_2 = pd.DataFrame(columns=dr_display_columns2)


            # CarNoごとにLapTimeベスト
            if "CarNo" in practice_df.columns and "LapTime" in practice_df.columns:
                filtered_df3 = practice_df.copy()
                idx3 = filtered_df3.groupby("CarNo")["LapTime"].idxmin()
                idx3 = idx3.dropna()  # NaNを除外
                sectorsummary_df0 = filtered_df3.loc[idx3].copy()
                # LapTimeの昇順で順位をつけてPos列を再設定
                sectorsummary_df0 = sectorsummary_df0.sort_values("LapTime", ascending=True)
                sectorsummary_df0["Pos"] = range(1, len(sectorsummary_df0) + 1)
                sectorsummary_df0 = (
                    sectorsummary_df0
                    .reindex(columns=["Pos", "CarNo", "Driver Name", "LapTime"])
                    .head(max_pos)
                    .fillna("")
                )
                # LapTime列をmm:ss.000形式に変換
                if "LapTime" in sectorsummary_df0.columns:
                    sectorsummary_df0["LapTime"] = pd.to_numeric(sectorsummary_df0["LapTime"], errors="coerce").apply(seconds_to_laptime)
            else:
                sectorsummary_df0 = practice_df.reindex(columns=["Pos", "CarNo", "Driver Name", "LapTime"]).head(max_pos).fillna("")

            # CarNoごとにSec 1ベスト
            if "CarNo" in practice_df.columns and "Sec 1" in practice_df.columns:
                filtered_df4 = practice_df.copy()
                # Sec 1がNaNでない行だけを対象にする
                filtered_df4 = filtered_df4[filtered_df4["Sec 1"].notna()]
                idx4 = filtered_df4.groupby("CarNo")["Sec 1"].idxmin()
                idx4 = idx4.dropna()  # NaNを除外
                sectorsummary_df1 = filtered_df4.loc[idx4].copy()
                # Sec 1の昇順で順位をつけてPos列を再設定
                sectorsummary_df1 = sectorsummary_df1.sort_values("Sec 1", ascending=True)
                sectorsummary_df1["Pos"] = range(1, len(sectorsummary_df1) + 1)
                sectorsummary_df1 = (
                    sectorsummary_df1
                    .reindex(columns=["Pos", "CarNo", "Driver Name", "Sec 1"])
                    .head(max_pos)
                    .fillna("")
                )
            else:
                sectorsummary_df1 = practice_df.reindex(columns=["Pos", "CarNo", "Driver Name", "Sec 1"]).head(max_pos).fillna("")

            # CarNoごとにSec 2ベスト
            if "CarNo" in practice_df.columns and "Sec 2" in practice_df.columns:
                filtered_df5 = practice_df.copy()
                # Sec 2がNaNでない行だけを対象にする
                filtered_df5 = filtered_df5[filtered_df5["Sec 2"].notna()]
                idx5 = filtered_df5.groupby("CarNo")["Sec 2"].idxmin()
                idx5 = idx5.dropna()  # NaNを除外
                sectorsummary_df2 = filtered_df5.loc[idx5].copy()
                # Sec 2の昇順で順位をつけてPos列を再設定
                sectorsummary_df2 = sectorsummary_df2.sort_values("Sec 2", ascending=True)
                sectorsummary_df2["Pos"] = range(1, len(sectorsummary_df2) + 1)
                sectorsummary_df2 = (
                    sectorsummary_df2
                    .reindex(columns=["Pos", "CarNo", "Driver Name", "Sec 2"])
                    .head(max_pos)
                    .fillna("")
                )
            else:
                sectorsummary_df2 = practice_df.reindex(columns=["Pos", "CarNo", "Driver Name", "Sec 2"]).head(max_pos).fillna("")

            # CarNoごとにSec 3ベスト
            if "CarNo" in practice_df.columns and "Sec 3" in practice_df.columns:
                filtered_df6 = practice_df.copy()
                # Sec 3がNaNでない行だけを対象にする
                filtered_df6 = filtered_df6[filtered_df6["Sec 3"].notna()]
                idx6 = filtered_df6.groupby("CarNo")["Sec 3"].idxmin()
                idx6 = idx6.dropna()  # NaNを除外
                sectorsummary_df3 = filtered_df6.loc[idx6].copy()
                # Sec 3の昇順で順位をつけてPos列を再設定
                sectorsummary_df3 = sectorsummary_df3.sort_values("Sec 3", ascending=True)
                sectorsummary_df3["Pos"] = range(1, len(sectorsummary_df3) + 1)
                sectorsummary_df3 = (
                    sectorsummary_df3
                    .reindex(columns=["Pos", "CarNo", "Driver Name", "Sec 3"])
                    .head(max_pos)
                    .fillna("")
                )
            else:
                sectorsummary_df3 = practice_df.reindex(columns=["Pos", "CarNo", "Driver Name", "Sec 3"]).head(max_pos).fillna("")

            # CarNoごとにSec 4ベスト
            if "CarNo" in practice_df.columns and "Sec 4" in practice_df.columns:
                filtered_df7 = practice_df.copy()
                # Sec 4がNaNでない行だけを対象にする
                filtered_df7 = filtered_df7[filtered_df7["Sec 4"].notna()]
                idx7 = filtered_df7.groupby("CarNo")["Sec 4"].idxmin()
                idx7 = idx7.dropna()  # NaNを除外
                sectorsummary_df4 = filtered_df7.loc[idx7].copy()
                # Sec 4の昇順で順位をつけてPos列を再設定
                sectorsummary_df4 = sectorsummary_df4.sort_values("Sec 4", ascending=True)
                sectorsummary_df4["Pos"] = range(1, len(sectorsummary_df4) + 1)
                sectorsummary_df4 = (
                    sectorsummary_df4
                    .reindex(columns=["Pos", "CarNo", "Driver Name", "Sec 4"])
                    .head(max_pos)
                    .fillna("")
                )
            else:
                sectorsummary_df4 = practice_df.reindex(columns=["Pos", "CarNo", "Driver Name", "Sec 4"]).head(max_pos).fillna("")

            # CarNoごとにSpeedベスト
            if "CarNo" in practice_df.columns and "Speed" in practice_df.columns:
                filtered_df8 = practice_df.copy()
                # SpeedがNaNでない行だけを対象にする
                filtered_df8 = filtered_df8[filtered_df8["Speed"].notna()]
                idx8 = filtered_df8.groupby("CarNo")["Speed"].idxmax()
                idx8 = idx8.dropna()  # NaNを除外
                sectorsummary_df5 = filtered_df8.loc[idx8].copy()
                # Speedの昇順で順位をつけてPos列を再設定
                sectorsummary_df5 = sectorsummary_df5.sort_values("Speed", ascending=False)
                sectorsummary_df5["Pos"] = range(1, len(sectorsummary_df5) + 1)
                sectorsummary_df5 = (
                    sectorsummary_df5
                    .reindex(columns=["Pos", "CarNo", "Driver Name", "Speed"])
                    .head(max_pos)
                    .fillna("")
                )
            else:
                sectorsummary_df5 = practice_df.reindex(columns=["Pos", "CarNo", "Driver Name", "Speed"]).head(max_pos).fillna("")


            # メーカー別タイム・サマリー
            st.session_state.display_time_df1 = timesummary1
            st.session_state.display_time_df2 = timesummary2

            # ベスト・タイム・サマリー
            st.session_state.display_timebest_df1 = besttime_summary1

            # 選択ドライバー vs トータルタイム・サマリー
            st.session_state.display_vs_driver_df1 = total_vs_driver_summary1
            st.session_state.display_vs_driver_df2 = total_vs_driver_summary2

            # ドライバー別タイム・データ
            st.session_state.driver_display_df1_1 = drivertime_df1_1
            st.session_state.driver_display_df1_2 = drivertime_df1_2
            st.session_state.driver_display_df2_1 = drivertime_df2_1
            st.session_state.driver_display_df2_2 = drivertime_df2_2
            st.session_state.driver_display_df3_1 = drivertime_df3_1
            st.session_state.driver_display_df3_2 = drivertime_df3_2
            st.session_state.driver_display_df4_1 = drivertime_df4_1
            st.session_state.driver_display_df4_2 = drivertime_df4_2

            # セクター別タイム・サマリー
            st.session_state.sector_display_df0 = sectorsummary_df0
            st.session_state.sector_display_df1 = sectorsummary_df1
            st.session_state.sector_display_df2 = sectorsummary_df2
            st.session_state.sector_display_df3 = sectorsummary_df3
            st.session_state.sector_display_df4 = sectorsummary_df4
            st.session_state.sector_display_df5 = sectorsummary_df5

            st.session_state.csv_mtime = mtime
    else:
        st.warning("CSVファイルが見つかりません。")

