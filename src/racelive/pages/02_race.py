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
    if pd.isna(sec) or not np.isfinite(sec):
        return ""
    m = int(sec // 60)
    s = sec % 60
    return f"{m}:{s:06.3f}"

def format_time_or_number(value):
    """数値やタイムデータのNoneを空文字列に変換"""
    if pd.isna(value) or not np.isfinite(value):
        return ""
    return str(value)

def format_sec_time(value):
    """Sec列用：小数点以下3位で表示"""
    if pd.isna(value) or not np.isfinite(value):
        return ""
    return f"{value:.3f}"

def format_speed(value):
    """Speed列用：小数点以下2位で表示"""
    if pd.isna(value) or not np.isfinite(value):
        return ""
    return f"{value:.2f}"


# -------------------------- サイドバー設定 ----------------------------------------------------------------------------------
st.sidebar.markdown("## タイムデータ表示")


# -------------------------- 空データフレーム事前設定 --------------------------------------------------------------------------

# レース Columns1設定
if sector == 3:
    race_columns1 = ["Pos", "CarNo", "Driver Name", "Lap", "Gap", "Diff", 
                    "LapTime", "Sec 1", "Sec 2", "Sec 3", "Speed", "Base Time", 
                    "PitIn1", "Stint1", "Avg1", "PitIn2", "Stint2", "Avg2", "PitIn3", "Stint3", "Avg3"]
else:
    race_columns1 = ["Pos", "CarNo", "Driver Name", "Lap", "Gap", "Diff", 
                    "LapTime", "Sec 1", "Sec 2", "Sec 3", "Sec 4", "Speed", "Base Time", 
                    "PitIn1", "Stint1", "Avg1", "PitIn2", "Stint2", "Avg2", "PitIn3", "Stint3", "Avg3"]


# レース総合タイム・データ用
race_df0 = pd.DataFrame({col: [""] * max_pos for col in race_columns1})
# Pos列に1からmax_posまでの順位を設定
race_df0["Pos"] = range(1, max_pos + 1)
# Lap列の初期値を0に設定
race_df0["Lap"] = 0
# Base Time列の初期値を空文字列に設定
race_df0["Base Time"] = ""
# PitIn列の初期値を空文字列に設定
race_df0["PitIn1"] = ""
race_df0["PitIn2"] = ""
race_df0["PitIn3"] = ""
# Stint列とAvg列の初期値を空文字列に設定
race_df0["Stint1"] = ""
race_df0["Avg1"] = ""
race_df0["Stint2"] = ""
race_df0["Avg2"] = ""
race_df0["Stint3"] = ""
race_df0["Avg3"] = ""


# セッションステートにレース用データフレームを保持
if "display_race_df0" not in st.session_state:
    st.session_state.display_race_df0 = race_df0.copy()



# -------------------------- ライブタイムデータ表示エリア ----------------------------------------------------------------------

# スクレイピング開始・停止をトグルで管理
livego_race = st.sidebar.toggle("タイム表示/停止", key="livego_race")

# Averageの倍率を取得
average_multiplier = st.sidebar.number_input("Average", min_value=1.00, max_value=1.50, value=1.05, step=0.01)

with st.container(border=True):
    # 統合されたデータフレーム用の列設定
    column_config = {
        "Pos": Column(label="Pos", width=30),
        "CarNo": Column(label="Car No", width=30),
        "Driver Name": Column(label="Driver", width=120),
        "Lap": Column(label="Lap", width=30),
        "Gap": Column(label="Gap", width=50),
        "Diff": Column(label="Diff", width=50),
        "LapTime": Column(label="Lap Time", width=100),
        "Sec 1": Column(label="Sec 1", width=60),
        "Sec 2": Column(label="Sec 2", width=60),
        "Sec 3": Column(label="Sec 3", width=60),
        "Speed": Column(label="Speed", width=60),
        "Base Time": Column(label="Base Time", width=100),
        "PitIn1": Column(label="PitIn1", width=30),
        "Stint1": Column(label="Stint1", width=30),
        "Avg1": Column(label="Avg1", width=70),
        "PitIn2": Column(label="PitIn2", width=30),
        "Stint2": Column(label="Stint2", width=30),
        "Avg2": Column(label="Avg2", width=70),
        "PitIn3": Column(label="PitIn3", width=30),
        "Stint3": Column(label="Stint3", width=30),
        "Avg3": Column(label="Avg3", width=70),
    }
    # セクター4がある場合の追加設定
    if sector == 4:
        column_config["Sec 4"] = Column(label="Sec 4", width=60)
    
    # 統合データフレームを作成
    st.dataframe(
        st.session_state.display_race_df0,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        height=810 
    )


# -------------------------- CSVファイルの自動リフレッシュ -----------------------------------------------------
if livego_race:

    st_autorefresh(interval=5000, key="autorefresh")
    if os.path.exists(csv_path):
        mtime = os.path.getmtime(csv_path)
        if "csv_mtime" not in st.session_state:
            st.session_state.csv_mtime = 0
        if mtime != st.session_state.csv_mtime:
            try:
                race_df1 = pd.read_csv(csv_path, encoding="shift-jis")
                # CSVファイルが空または列がない場合はスキップ
                if race_df1.empty or len(race_df1.columns) == 0:
                    st.session_state.csv_mtime = mtime
                else:
                    # 正常にデータが読み込めた場合のみ処理を続行
                    process_data = True
            except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
                # CSVファイルの読み込みエラーが発生した場合はスキップ
                st.session_state.csv_mtime = mtime
                process_data = False
            
            if not locals().get('process_data', False):
                pass  # データ処理をスキップ
            else:
                # LapTime, Sec, Speed列を数値型に変換（エラー時はNaN）
                num_cols = ["LapTime", "Sec 1", "Sec 2", "Sec 3", "Sec 4", "Speed", "Lap", "Pos"]
                for col in num_cols:
                    if col in race_df1.columns:
                        race_df1[col] = pd.to_numeric(race_df1[col], errors="coerce")

                # 各CarNoについて、Sec 1またはSpeedにデータがある最新のLapの行のみを抽出
                if "CarNo" in race_df1.columns and "Lap" in race_df1.columns and ("Sec 1" in race_df1.columns or "Speed" in race_df1.columns):
                    # Sec 1またはSpeedにデータがある行のみをフィルタ
                    sec1_condition = race_df1["Sec 1"].notna() & (race_df1["Sec 1"] != "") if "Sec 1" in race_df1.columns else pd.Series([False] * len(race_df1))
                    speed_condition = race_df1["Speed"].notna() & (race_df1["Speed"] != "") if "Speed" in race_df1.columns else pd.Series([False] * len(race_df1))
                    valid_data = race_df1[sec1_condition | speed_condition]
                    
                    if not valid_data.empty:
                        # 各CarNoについて最大のLapの行を取得
                        latest_laps = valid_data.groupby("CarNo")["Lap"].idxmax()
                        race_df1 = race_df1.loc[latest_laps]
                    
                # 表示する列をrace_columns1に制限（CSVに存在する列のみ）
                available_columns = [col for col in race_columns1 if col in race_df1.columns]
                race_df1 = race_df1[available_columns]
                    
                # 既存のデータと新しいデータをマージして保持
                current_df = st.session_state.display_race_df0.copy()
                
                # 新しいデータで既存データを更新
                if not race_df1.empty and "CarNo" in race_df1.columns:
                    for _, new_row in race_df1.iterrows():
                        car_no = new_row["CarNo"]
                        # 既存データの中で該当するCarNoの行を探す
                        mask = current_df["CarNo"] == car_no
                        if mask.any():
                            # 既存の行を更新（データがある列のみ）
                            for col in race_columns1:
                                if col in new_row.index and pd.notna(new_row[col]) and str(new_row[col]).strip() != "":
                                    # Lapの場合は、Sec 1またはSpeedにデータがある場合のみ更新
                                    if col == "Lap":
                                        sec1_has_data = "Sec 1" in new_row.index and pd.notna(new_row["Sec 1"]) and str(new_row["Sec 1"]).strip() != ""
                                        speed_has_data = "Speed" in new_row.index and pd.notna(new_row["Speed"]) and str(new_row["Speed"]).strip() != ""
                                        if sec1_has_data or speed_has_data:
                                            current_df.loc[mask, col] = new_row[col]
                                    else:
                                        current_df.loc[mask, col] = new_row[col]
                        else:
                            # 新しい車両の場合、空いている行に追加
                            empty_mask = (current_df["CarNo"] == "") | current_df["CarNo"].isna()
                            if empty_mask.any():
                                first_empty_idx = current_df[empty_mask].index[0]
                                for col in race_columns1:
                                    if col in new_row.index:
                                        # Lapの場合は、Sec 1またはSpeedにデータがある場合のみ更新
                                        if col == "Lap":
                                            sec1_has_data = "Sec 1" in new_row.index and pd.notna(new_row["Sec 1"]) and str(new_row["Sec 1"]).strip() != ""
                                            speed_has_data = "Speed" in new_row.index and pd.notna(new_row["Speed"]) and str(new_row["Speed"]).strip() != ""
                                            if sec1_has_data or speed_has_data:
                                                current_df.loc[first_empty_idx, col] = new_row[col]
                                            elif col == "Lap":
                                                current_df.loc[first_empty_idx, col] = 0  # データがない場合は0を保持
                                        else:
                                            current_df.loc[first_empty_idx, col] = new_row[col]
                
                # LapTimeを mm:ss.000 形式に変換
                if "LapTime" in current_df.columns:
                    current_df["LapTime"] = pd.to_numeric(current_df["LapTime"], errors="coerce").apply(seconds_to_laptime)
                
                # Base Time（各CarNoの最小LapTime）を計算・更新
                if "CarNo" in current_df.columns and "LapTime" in current_df.columns:
                    # 全データから各CarNoの最小LapTimeを計算
                    if os.path.exists(csv_path):
                        try:
                            all_data = pd.read_csv(csv_path, encoding="shift-jis")
                            if not all_data.empty and "LapTime" in all_data.columns and "CarNo" in all_data.columns:
                                all_data["LapTime"] = pd.to_numeric(all_data["LapTime"], errors="coerce")
                                # 各CarNoの最小LapTimeを取得（NaNを除外）
                                min_laptimes = all_data.groupby("CarNo")["LapTime"].min()
                                
                                # current_dfの各CarNoに対してBase Timeを設定
                                for idx, row in current_df.iterrows():
                                    car_no = row["CarNo"]
                                    if car_no and car_no in min_laptimes:
                                        min_time = min_laptimes[car_no]
                                        if pd.notna(min_time):
                                            current_df.loc[idx, "Base Time"] = seconds_to_laptime(min_time)
                                        else:
                                            current_df.loc[idx, "Base Time"] = ""
                                    else:
                                        current_df.loc[idx, "Base Time"] = ""
                        except (pd.errors.EmptyDataError, pd.errors.ParserError):
                            # Base Time計算でエラーが発生した場合は空文字列で埋める
                            for idx in current_df.index:
                                current_df.loc[idx, "Base Time"] = ""
                
                # PitIn情報を計算・更新（各CarNoのPit履歴を取得）
                if "CarNo" in current_df.columns:
                    # 全データからPit履歴を計算
                    if os.path.exists(csv_path):
                        try:
                            all_data = pd.read_csv(csv_path, encoding="shift-jis")
                            if not all_data.empty and "CarNo" in all_data.columns and "Pit" in all_data.columns and "Lap" in all_data.columns:
                                # Pit列がPit（ピットイン）の行のみを抽出
                                pit_data = all_data[all_data["Pit"] == "Pit"]
                                
                                # current_dfの各CarNoに対してPitIn情報とStint情報を設定
                                for idx, row in current_df.iterrows():
                                    car_no = row["CarNo"]
                                    if car_no:
                                        # 該当するCarNoのPit履歴を取得（Lap順でソート）
                                        car_pit_data = pit_data[pit_data["CarNo"] == car_no].sort_values("Lap")
                                        
                                        # PitIn1, PitIn2, PitIn3に設定
                                        pit_laps = car_pit_data["Lap"].tolist()
                                        current_df.loc[idx, "PitIn1"] = str(pit_laps[0]) if len(pit_laps) >= 1 else ""
                                        current_df.loc[idx, "PitIn2"] = str(pit_laps[1]) if len(pit_laps) >= 2 else ""
                                        current_df.loc[idx, "PitIn3"] = str(pit_laps[2]) if len(pit_laps) >= 3 else ""
                                        
                                        # 該当するCarNoの全ラップタイムデータを取得
                                        car_all_data = all_data[all_data["CarNo"] == car_no].copy()
                                        car_all_data["LapTime"] = pd.to_numeric(car_all_data["LapTime"], errors="coerce")
                                        car_all_data["Lap"] = pd.to_numeric(car_all_data["Lap"], errors="coerce")
                                        car_all_data = car_all_data.dropna(subset=["LapTime", "Lap"])
                                        
                                        if not car_all_data.empty:
                                            current_lap = int(row["Lap"]) if pd.notna(row["Lap"]) and row["Lap"] != "" else 0
                                            
                                            # Stint1の計算
                                            if len(pit_laps) >= 1:
                                                stint1_start = 1
                                                stint1_end = int(pit_laps[0])
                                                current_df.loc[idx, "Stint1"] = str(stint1_end - stint1_start + 1)
                                            else:
                                                stint1_start = 1
                                                stint1_end = current_lap
                                                current_df.loc[idx, "Stint1"] = str(stint1_end - stint1_start + 1) if current_lap > 0 else ""
                                            
                                            # Stint2の計算
                                            if len(pit_laps) >= 2:
                                                stint2_start = int(pit_laps[0]) + 1
                                                stint2_end = int(pit_laps[1])
                                                current_df.loc[idx, "Stint2"] = str(stint2_end - stint2_start + 1)
                                            elif len(pit_laps) == 1:
                                                stint2_start = int(pit_laps[0]) + 1
                                                stint2_end = current_lap
                                                current_df.loc[idx, "Stint2"] = str(stint2_end - stint2_start + 1) if current_lap > stint2_start else ""
                                            else:
                                                current_df.loc[idx, "Stint2"] = ""
                                            
                                            # Stint3の計算
                                            if len(pit_laps) >= 3:
                                                stint3_start = int(pit_laps[1]) + 1
                                                stint3_end = int(pit_laps[2])
                                                current_df.loc[idx, "Stint3"] = str(stint3_end - stint3_start + 1)
                                            elif len(pit_laps) == 2:
                                                stint3_start = int(pit_laps[1]) + 1
                                                stint3_end = current_lap
                                                current_df.loc[idx, "Stint3"] = str(stint3_end - stint3_start + 1) if current_lap > stint3_start else ""
                                            else:
                                                current_df.loc[idx, "Stint3"] = ""
                                            
                                            # 各Stintの平均タイム計算
                                            def calculate_stint_average(start_lap, end_lap, car_data, multiplier):
                                                stint_data = car_data[(car_data["Lap"] >= start_lap) & (car_data["Lap"] <= end_lap)]
                                                if stint_data.empty:
                                                    return ""
                                                
                                                # そのStintのベストタイムを取得
                                                best_time = stint_data["LapTime"].min()
                                                if pd.isna(best_time):
                                                    return ""
                                                
                                                # ベストタイム × multiplierより小さいタイムのみでフィルタ
                                                threshold = best_time * multiplier
                                                filtered_data = stint_data[stint_data["LapTime"] <= threshold]
                                                
                                                if filtered_data.empty:
                                                    return ""
                                                
                                                avg_time = filtered_data["LapTime"].mean()
                                                return seconds_to_laptime(avg_time) if pd.notna(avg_time) else ""
                                            
                                            # Avg1の計算
                                            if len(pit_laps) >= 1:
                                                avg1 = calculate_stint_average(1, int(pit_laps[0]), car_all_data, average_multiplier)
                                                current_df.loc[idx, "Avg1"] = avg1
                                            else:
                                                avg1 = calculate_stint_average(1, current_lap, car_all_data, average_multiplier)
                                                current_df.loc[idx, "Avg1"] = avg1
                                            
                                            # Avg2の計算
                                            if len(pit_laps) >= 2:
                                                avg2 = calculate_stint_average(int(pit_laps[0]) + 1, int(pit_laps[1]), car_all_data, average_multiplier)
                                                current_df.loc[idx, "Avg2"] = avg2
                                            elif len(pit_laps) == 1:
                                                avg2 = calculate_stint_average(int(pit_laps[0]) + 1, current_lap, car_all_data, average_multiplier)
                                                current_df.loc[idx, "Avg2"] = avg2
                                            else:
                                                current_df.loc[idx, "Avg2"] = ""
                                            
                                            # Avg3の計算
                                            if len(pit_laps) >= 3:
                                                avg3 = calculate_stint_average(int(pit_laps[1]) + 1, int(pit_laps[2]), car_all_data, average_multiplier)
                                                current_df.loc[idx, "Avg3"] = avg3
                                            elif len(pit_laps) == 2:
                                                avg3 = calculate_stint_average(int(pit_laps[1]) + 1, current_lap, car_all_data, average_multiplier)
                                                current_df.loc[idx, "Avg3"] = avg3
                                            else:
                                                current_df.loc[idx, "Avg3"] = ""
                                        else:
                                            # データがない場合は空文字列
                                            current_df.loc[idx, "Stint1"] = ""
                                            current_df.loc[idx, "Avg1"] = ""
                                            current_df.loc[idx, "Stint2"] = ""
                                            current_df.loc[idx, "Avg2"] = ""
                                            current_df.loc[idx, "Stint3"] = ""
                                            current_df.loc[idx, "Avg3"] = ""
                                    else:
                                        current_df.loc[idx, "PitIn1"] = ""
                                        current_df.loc[idx, "PitIn2"] = ""
                                        current_df.loc[idx, "PitIn3"] = ""
                                        current_df.loc[idx, "Stint1"] = ""
                                        current_df.loc[idx, "Avg1"] = ""
                                        current_df.loc[idx, "Stint2"] = ""
                                        current_df.loc[idx, "Avg2"] = ""
                                        current_df.loc[idx, "Stint3"] = ""
                                        current_df.loc[idx, "Avg3"] = ""
                        except (pd.errors.EmptyDataError, pd.errors.ParserError):
                            # PitIn計算でエラーが発生した場合は空文字列で埋める
                            for idx in current_df.index:
                                current_df.loc[idx, "PitIn1"] = ""
                                current_df.loc[idx, "PitIn2"] = ""
                                current_df.loc[idx, "PitIn3"] = ""
                                current_df.loc[idx, "Stint1"] = ""
                                current_df.loc[idx, "Avg1"] = ""
                                current_df.loc[idx, "Stint2"] = ""
                                current_df.loc[idx, "Avg2"] = ""
                                current_df.loc[idx, "Stint3"] = ""
                                current_df.loc[idx, "Avg3"] = ""
                
                # Sec、Speed、Gap、DiffのNone値を空文字列に変換、列ごとに適切なフォーマットを適用
                # Sec列：小数点以下3位、Speed列：小数点以下2位
                sec_columns = ["Sec 1", "Sec 2", "Sec 3", "Sec 4"]
                for col in sec_columns:
                    if col in current_df.columns:
                        current_df[col] = pd.to_numeric(current_df[col], errors="coerce").apply(format_sec_time)
                
                # Speed列：小数点以下2位
                if "Speed" in current_df.columns:
                    current_df["Speed"] = pd.to_numeric(current_df["Speed"], errors="coerce").apply(format_speed)
                
                # Gap、Diff列：従来通り
                other_format_columns = ["Gap", "Diff"]
                for col in other_format_columns:
                    if col in current_df.columns:
                        current_df[col] = pd.to_numeric(current_df[col], errors="coerce").apply(format_time_or_number)
                
                # Pos列でソート（数値として扱う）
                if "Pos" in current_df.columns:
                    current_df["Pos"] = pd.to_numeric(current_df["Pos"], errors="coerce")
                    current_df = current_df.sort_values("Pos").reset_index(drop=True)
                
                # データ行数をmax_posに制限
                if len(current_df) > max_pos:
                    current_df = current_df.head(max_pos)

                st.session_state.display_race_df0 = current_df

                st.session_state.csv_mtime = mtime

    else:
        st.warning("CSVファイルが見つかりません。")


# -------------------------- サイドバー設定 ----------------------------------------------------------------------------------

