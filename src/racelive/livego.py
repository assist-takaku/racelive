""" ---------------------------------------------------------------------------------------------------------
    Super Formula Race Live   Ver : 1.2.4  2025.06

    poetry run streamlit run src/racelive/livego.py

    スクレイピング処理を記述するコードです。
    streamlitではwhile Trueのループができないので、別コードを使ってスクレイピング処理を実行します。
    ここでは、スクレイピングしたデータをCSVファイルに保存する処理を記述しています。

    1. streamlitを使って、スクレイピング処理を実行します。
    2. SuperFormulaのRaceLiveからデータを取得します。
    3. racelive.jpのサービスからのデータ取得なので同じフォーマットのSuperFormula Lightsも読み込み可能。
    4. ウェザーデータの取得も、ここに記述。

----------------------------------------------------------------------------------------------------------"""
import os
import sys
from pathlib import Path
import time
import json
import schedule
import threading
import numpy as np
import pandas as pd
import concurrent.futures
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import traceback
import streamlit as st

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from racelive.scraperead import Racelivescraper
from racelive.utils import Datalist
from racelive import const


st.set_page_config(page_title="ラップタイム・スクレイピング", initial_sidebar_state="collapsed" , layout="wide")

st.title("ラップタイム・スクレイピング・ページ")


# 時間表示フォーマット
datetime.now().strftime("%Y/%m/%d %H:%M:%S")
today = datetime.now().strftime("%Y/%m/%d")

sf_setfile = json.load(open("./data/racelive.json", "r", encoding="utf-8"))

category = sf_setfile["Category"][sf_setfile["Last Category"]]["Name"]
category_index = sf_setfile["Last Category"]
url = sf_setfile["Category"][sf_setfile["Last Category"]]["URL"]
circuit = sf_setfile["Circuit"][sf_setfile["Last Circuit"]]["Name"]
race_lap = sf_setfile["Race Lap"]
sector = sf_setfile["Circuit"][sf_setfile["Last Circuit"]]["Sector"]

time_path = sf_setfile["Time Path"]
lastevent = sf_setfile["Last Event"]

# セッション開始・終了時間を設定
session_name = sf_setfile["Session"][sf_setfile["Last Session"]]["Name"]
session_starttime = sf_setfile["Last StartTime"]
session_endtime = sf_setfile["Last EndTime"]
session_date = today

# カテゴリに基づいてチームリストを取得
datal = Datalist(sf_setfile["Last Category"])
teamlist, mk, mk2 = datal.teamlist()
driver_list, car_no_list = datal.driverlist()
# ライブデータ用空のデータフレームを作成
df0 = datal.data_db(race_lap)

ambientid = sf_setfile["ambient ID"]
ambientreadKey = sf_setfile["ambient readKey"]
weapath = sf_setfile["weather Path"]
time_path = sf_setfile["Time Path"]

save_path = os.path.join(time_path, f"{lastevent}_{session_name}")


# カスタムCSS
st.markdown("""
<style>
.info-box {
    background-color: #f0f2f6;
    padding: 10px;
    border-radius: 5px;
    border: 2px solid #0066cc;
    text-align: center;
    margin: 5px;
}
.info-label {
    font-weight: bold;
    font-size: 14px;
    color: #0066cc;
}
.info-value {
    font-size: 25px;
    color: #333;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)


# 設定情報表示
col_1, col_2, col_3, col_4 = st.columns([1, 1, 1, 1])

with col_1:
    st.markdown(f"""
    <div class="info-box">
        <div class="info-label">カテゴリ</div>
        <div class="info-value">{category}</div>
    </div>
    """, unsafe_allow_html=True)

with col_2:
    st.markdown(f"""
    <div class="info-box">
        <div class="info-label">サーキット</div>
        <div class="info-value">{circuit}</div>
    </div>
    """, unsafe_allow_html=True)

with col_3:
    st.markdown(f"""
    <div class="info-box">
        <div class="info-label">レースラップ</div>
        <div class="info-value">{race_lap}</div>
    </div>
    """, unsafe_allow_html=True)

with col_4:
    st.markdown(f"""
    <div class="info-box">
        <div class="info-label">セクター</div>
        <div class="info-value">{sector}</div>
    </div>
    """, unsafe_allow_html=True)


col_5, col_6, col_7, col_8 = st.columns([1, 1, 1, 1])

with col_5:
    st.markdown(f"""
    <div class="info-box">
        <div class="info-label">セッション</div>
        <div class="info-value">{session_name}</div>
    </div>
    """, unsafe_allow_html=True)

with col_6:
    st.markdown(f"""
    <div class="info-box">
        <div class="info-label">開始時間</div>
        <div class="info-value">{session_starttime}</div>
    </div>
    """, unsafe_allow_html=True)

with col_7:
    st.markdown(f"""
    <div class="info-box">
        <div class="info-label">終了時間</div>
        <div class="info-value">{session_endtime}</div>
    </div>
    """, unsafe_allow_html=True)

with col_8:
    st.write("")

st.write("---")

# 制御ファイルのパス
control_file = "./data/scraping_control.json"

def check_scraping_control():
    """制御ファイルを確認してスクレイピング状態を取得"""
    if os.path.exists(control_file):
        try:
            with open(control_file, "r", encoding="utf-8") as f:
                control_data = json.load(f)
            return control_data.get("scraping", False)
        except:
            return False
    return False

def update_scraping_status(status):
    """制御ファイルにスクレイピング状態を更新"""
    try:
        if os.path.exists(control_file):
            with open(control_file, "r", encoding="utf-8") as f:
                control_data = json.load(f)
        else:
            control_data = {}
        
        control_data["scraping"] = status
        control_data["timestamp"] = datetime.now().isoformat()
        control_data["status_from"] = "livego.py"
        
        os.makedirs(os.path.dirname(control_file), exist_ok=True)
        with open(control_file, "w", encoding="utf-8") as f:
            json.dump(control_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"制御ファイルの更新エラー: {e}")

st.write("---")

# 制御ファイルを監視してスクレイピングを制御
scraping = check_scraping_control()

# スクレイピング状態表示
if scraping:
    st.markdown("#### 🟢 スクレイピング実行中")
    status_color = "green"
else:
    st.markdown("#### 🔴 スクレイピング停止中")
    status_color = "red"

# 状態表示ボックス
st.markdown(f"""
<div style="background-color: {status_color}; padding: 10px; border-radius: 5px; color: white; text-align: center; margin: 10px 0;">
    <h3>制御状態: {'実行中' if scraping else '停止中'}</h3>
</div>
""", unsafe_allow_html=True)

# 手動制御用のトグル（オプション）
manual_control = st.toggle("手動制御", key="manual_toggle")
if manual_control:
    manual_scraping = st.toggle("手動スクレイピング開始/停止", value=scraping, key="manual_scraping")
    if manual_scraping != scraping:
        update_scraping_status(manual_scraping)
        st.rerun()

if scraping:
    # 既存のスクレイピング処理
    try:
        # セッション開始時間をdatetimeオブジェクトに変換
        session_start_str = f"{session_date} {session_starttime}:00"
        session_start_dt = datetime.strptime(session_start_str, "%Y/%m/%d %H:%M:%S")
        
        # セッション終了時間をdatetimeオブジェクトに変換
        session_end_str = f"{session_date} {session_endtime}:00"
        session_end_dt = datetime.strptime(session_end_str, "%Y/%m/%d %H:%M:%S")
        
        # 開始時間の1分前に設定
        scraping_start_dt = session_start_dt - timedelta(minutes=1)

        # 終了時間の3分後に設定
        scraping_end_dt = session_end_dt + timedelta(minutes=3)
        
        # UNIXタイムスタンプに変換
        session_start = int(time.mktime(scraping_start_dt.timetuple()))
        session_end = int(time.mktime(scraping_end_dt.timetuple()))
        
        # 現在時刻との比較表示
        now = datetime.now()

        # 開始時刻まで待機するかどうかの判定
        if now < scraping_start_dt:
            remaining_time = scraping_start_dt - now
            st.info(f"⏰ 開始まで: {remaining_time}")
        elif now > scraping_end_dt:
            st.error("⚠️ スクレイピング終了時刻を過ぎています")
            # 自動的に停止
            update_scraping_status(False)
        else:
            st.success("✅ スクレイピング実行中")
        
    except ValueError as e:
        st.error(f"時刻の形式エラー: {e}")
        # エラーの場合は現在時刻から2分間のデフォルト設定
        session_start = int(time.mktime(datetime.now().timetuple()))
        session_end = int(time.mktime((datetime.now() + timedelta(minutes=2)).timetuple()))

    # スクレイピング実行
    try:
        scraper = Racelivescraper(url, df0, category_index, sector, car_no_list, driver_list, mk, save_path)
        timedata = scraper.livetime(session_start, session_end)
    except Exception as e:
        st.error(f"スクレイピングエラー: {e}")
        # エラー時は自動停止
        update_scraping_status(False)

# 自動リフレッシュ（1秒毎に制御ファイルをチェック）
time.sleep(1)
st.rerun()
