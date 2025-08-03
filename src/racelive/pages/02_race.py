""" ---------------------------------------------------------------------------------------------------------
    Race Page for RaceLive


----------------------------------------------------------------------------------------------------------"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import json
import numpy as np
import pandas as pd
import threading
import pyperclip
import streamlit as st
from streamlit.column_config import Column
from streamlit_autorefresh import st_autorefresh
import plotly.express as px
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from racelive.scraperead import Racelivescraper
from racelive.utils import Datalist
from racelive import const

st.set_page_config(page_title="Raceページ", layout="wide")


# -------------------------- 設定用Jsonファイルの読み込み -------------------------------------------------------------------------
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
# セッション情報を取得
selected_session_index = sf_setfile.get("Last Session", 0)
selected_session = sf_setfile["Session"][selected_session_index]
session_name = selected_session["Name"]
df0 = datal.data_db(race_lap, session_name)
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

# st.title("Raceページ")

def seconds_to_laptime(sec):
    """秒(float)を mm:ss.000 形式の文字列に変換"""
    if not np.isfinite(sec):
        return np.nan
    m = int(sec // 60)
    s = sec % 60
    return f"{m}:{s:06.3f}"


# -------------------------- サイドバー設定 ----------------------------------------------------------------------------------
st.sidebar.markdown("## タイムデータ表示")





# -------------------------- 空データフレーム事前設定 --------------------------------------------------------------------------

# レース Columns1設定
if sector == 3:
    race_columns1 = ["Pos", "CarNo", "Driver Name", "Lap", "Gap", "Diff", 
                    "LapTime", "Sec 1", "Sec 2", "Sec 3", "Speed", "Best LapTime",]
else:
    race_columns1 = ["Pos", "CarNo", "Driver Name", "Lap", "Gap", "Diff", 
                    "LapTime", "Sec 1", "Sec 2", "Sec 3", "Sec 4", "Speed", "Best LapTime",]

race_columns2 = ["PitIn", "Stint", "Avg"]


# レース総合タイム・データ用
race_df0 = pd.DataFrame({col: [""] * max_pos for col in race_columns1})
# レース総合ステント１用のデータ用
race_df1 = pd.DataFrame({col: [""] * max_pos for col in race_columns2})
# レース総合ステント2用のデータ用
race_df2 = pd.DataFrame({col: [""] * max_pos for col in race_columns2})
# レース総合ステント3用のデータ用
race_df3 = pd.DataFrame({col: [""] * max_pos for col in race_columns2})


# セッションステートにレース用データフレームを保持
if "display_race_df0" not in st.session_state:
    st.session_state.display_race_df0 = race_df0.copy()

if "display_race_df1" not in st.session_state:
    st.session_state.display_race_df1 = race_df1.copy()

if "display_race_df2" not in st.session_state:
    st.session_state.display_race_df2 = race_df2.copy()

if "display_race_df3" not in st.session_state:
    st.session_state.display_race_df3 = race_df3.copy()


# -------------------------- ライブタイムデータ表示エリア ----------------------------------------------------------------------

# スクレイピング開始・停止をトグルで管理
livego_race = st.sidebar.toggle("タイム表示/停止", key="livego_race")

col_race1, col_race2, col_race3, col_race4 = st.columns([4, 1, 1, 1])

with col_race1:
    with st.container(border=True):
        with st.container(border=True):
            st.write("Race Live Timing")
        with st.container(border=True):
            # レース総合列設定
            column_config = {
                "Pos": Column(label="Pos", width=50),
                "CarNo": Column(label="Car No", width=70),
                "Driver Name": Column(label="Driver", width=120),
                "Lap": Column(label="Lap", width=60),
                "Gap": Column(label="Gap", width=80),
                "Diff": Column(label="Diff", width=80),
                "LapTime": Column(label="Lap Time", width=100),
                "Sec 1": Column(label="Sec 1", width=70),
                "Sec 2": Column(label="Sec 2", width=70),
                "Sec 3": Column(label="Sec 3", width=70),
                "Speed": Column(label="Speed", width=70),
                "Best LapTime": Column(label="Best Lap", width=100),
            }
            
            # セクター4がある場合の追加設定
            if sector == 4:
                column_config["Sec 4"] = Column(label="Sec 4", width=70)
            
            st.dataframe(
                st.session_state.display_race_df0,
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
                height=600 
            )

with col_race2:
    with st.container(border=True):
        with st.container(border=True):
            st.write("Stint 1")
        with st.container(border=True):
            # レース総合列設定
            column_config = {
                "PitIn1": Column(label="PitIn", width=50),
                "Stint1": Column(label="Stint", width=50),
                "Average1": Column(label="Avg", width=70),
            }

            st.dataframe(
                st.session_state.display_race_df1,
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
                height=600
            )

with col_race3:
    with st.container(border=True):
        with st.container(border=True):
            st.write("Stint 2")
        with st.container(border=True):
            # レース総合列設定
            column_config = {
                "PitIn2": Column(label="PitIn", width=50),
                "Stint2": Column(label="Stint", width=50),
                "Average2": Column(label="Avg", width=70),
            }

            st.dataframe(
                st.session_state.display_race_df2,
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
                height=600
            )

with col_race4:
    with st.container(border=True):
        with st.container(border=True):
            st.write("Stint 3")
        with st.container(border=True):
            # レース総合列設定
            column_config = {
                "PitIn3": Column(label="PitIn", width=50),
                "Stint3": Column(label="Stint", width=50),
                "Average3": Column(label="Avg", width=70),
            }

            st.dataframe(
                st.session_state.display_race_df3,
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
                height=600
            )


# -------------------------- CSVファイルの自動リフレッシュ -----------------------------------------------------
if livego_race:

    st_autorefresh(interval=5000, key="autorefresh")
    if os.path.exists(csv_path):
        mtime = os.path.getmtime(csv_path)
        if "csv_mtime" not in st.session_state:
            st.session_state.csv_mtime = 0
        if mtime != st.session_state.csv_mtime:
            race_df1 = pd.read_csv(csv_path, encoding="shift-jis")
            st.session_state.csv_mtime = mtime

            # LapTime, Sec, Speed列を数値型に変換（エラー時はNaN）
            num_cols = ["LapTime", "Sec 1", "Sec 2", "Sec 3", "Sec 4", "Speed"]
            for col in num_cols:
                if col in race_df1.columns:
                    race_df1[col] = pd.to_numeric(race_df1[col], errors="coerce")

            # ----------------------------- CSVファイルの読み込みとレース用データフレームの作成 -----------------------------------------------------
            # レース総合のデータフレーム
            if "CarNo" in race_df1.columns and "LapTime" in race_df1.columns:
                # CarNoごとに最新のラップタイムを取得
                latest_df = race_df1.groupby("CarNo").last().reset_index()
                # Pos列が存在する場合はPos順でソート、存在しない場合はLapTime順
                if "Pos" in latest_df.columns:
                    latest_df = latest_df.sort_values("Pos", ascending=True, na_position='last')
                else:
                    # Pos列がない場合はLapTimeの昇順でソートして順位を設定
                    latest_df = latest_df.sort_values("LapTime", ascending=True, na_position='last')
                    latest_df["Pos"] = range(1, len(latest_df) + 1)
                
                # レース用の列に合わせてデータフレームを整形
                race_summary1 = latest_df.reindex(columns=race_columns1).head(max_pos).fillna("")
                
                # LapTime列をmm:ss.000形式に変換
                if "LapTime" in race_summary1.columns:
                    race_summary1["LapTime"] = pd.to_numeric(race_summary1["LapTime"], errors="coerce").apply(seconds_to_laptime)
                
                # Sec列（Sec 1, Sec 2, Sec 3, Sec 4）は小数点以下3位
                for sec_col in ["Sec 1", "Sec 2", "Sec 3", "Sec 4"]:
                    if sec_col in race_summary1.columns:
                        race_summary1[sec_col] = pd.to_numeric(race_summary1[sec_col], errors="coerce").map(lambda x: f"{x:.3f}" if pd.notnull(x) else "")
                
                # Speed列は小数点以下2位
                if "Speed" in race_summary1.columns:
                    race_summary1["Speed"] = pd.to_numeric(race_summary1["Speed"], errors="coerce").map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
            else:
                # データがない場合は空のデータフレームを作成
                race_summary1 = pd.DataFrame({col: [""] * max_pos for col in race_columns1})

            st.session_state.display_race_df0 = race_summary1

