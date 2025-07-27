""" ---------------------------------------------------------------------------------------------------------
    Super Formula Race Live   Ver : 1.2.4  2025.06

    python src/racelive/livego.py

    スクレイピング処理を記述するコードです。
    制御ファイルを監視して、スクレイピング処理を実行します。
    ここでは、スクレイピングしたデータをCSVファイルに保存する処理を記述しています。

    1. 制御ファイルを監視して、スクレイピング処理を実行します。
    2. SuperFormulaのRaceLiveからデータを取得します。
    3. racelive.jpのサービスからのデータ取得なので同じフォーマットのSuperFormula Lightsも読み込み可能。
    4. ウェザーデータの取得も、ここに記述。

----------------------------------------------------------------------------------------------------------"""
import os
import sys
from pathlib import Path
import time
import json
import threading
import schedule
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import traceback

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from racelive.scraperead import Racelivescraper
from racelive.utils import Datalist

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

def update_scraping_status(status, message=""):
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
        if message:
            control_data["message"] = message
        
        os.makedirs(os.path.dirname(control_file), exist_ok=True)
        with open(control_file, "w", encoding="utf-8") as f:
            json.dump(control_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"制御ファイルの更新エラー: {e}")

def load_settings():
    """設定ファイルを読み込み"""
    try:
        with open("./data/racelive.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return None

def main():
    print("スクレイピング監視を開始しました...")
    print("Ctrl+C で終了")
    
    scraping_active = False
    scheduler = schedule.Scheduler()
    scheduled_job = None
    
    while True:
        try:
            # 制御ファイルをチェック
            should_scraping = check_scraping_control()
            
            if should_scraping and not scraping_active:
                # スクレイピング開始
                print("スクレイピング開始指示を受信")
                
                # 設定読み込み
                sf_setfile = load_settings()
                if not sf_setfile:
                    print("設定ファイルが読み込めません")
                    time.sleep(5)
                    continue
                
                # 設定値取得
                category = sf_setfile["Category"][sf_setfile["Last Category"]]["Name"]
                category_index = sf_setfile["Last Category"]
                url = sf_setfile["Category"][sf_setfile["Last Category"]]["URL"]
                circuit = sf_setfile["Circuit"][sf_setfile["Last Circuit"]]["Name"]
                race_lap = sf_setfile["Race Lap"]
                sector = sf_setfile["Circuit"][sf_setfile["Last Circuit"]]["Sector"]
                
                time_path = sf_setfile["Time Path"]
                lastevent = sf_setfile["Last Event"]
                
                session_name = sf_setfile["Session"][sf_setfile["Last Session"]]["Name"]
                session_starttime = sf_setfile["Last StartTime"]
                session_endtime = sf_setfile["Last EndTime"]
                session_date = datetime.now().strftime("%Y/%m/%d")
                
                # オフセット値を取得（デフォルト値を設定）
                offset_start = sf_setfile.get("Offset Start", 1)  # デフォルト1分
                offset_end = sf_setfile.get("Offset End", 3)      # デフォルト3分
                
                # データ準備
                datal = Datalist(sf_setfile["Last Category"])
                teamlist, mk, mk2 = datal.teamlist()
                driver_list, car_no_list = datal.driverlist()
                df0 = datal.data_db(race_lap)
                
                save_path = os.path.join(time_path, f"{lastevent}_{session_name}")
                
                print(f"カテゴリ: {category}")
                print(f"セッション: {session_name}")
                print(f"時間: {session_starttime} - {session_endtime}")
                print(f"オフセット: 開始-{offset_start}分, 終了+{offset_end}分")
                print(f"保存先: {save_path}")
                
                # 時間計算
                try:
                    session_start_str = f"{session_date} {session_starttime}:00"
                    session_start_dt = datetime.strptime(session_start_str, "%Y/%m/%d %H:%M:%S")
                    
                    session_end_str = f"{session_date} {session_endtime}:00"
                    session_end_dt = datetime.strptime(session_end_str, "%Y/%m/%d %H:%M:%S")
                    
                    # 設定されたオフセット値を使用してスクレイピング期間を計算
                    scraping_start_dt = session_start_dt - timedelta(minutes=offset_start)
                    scraping_end_dt = session_end_dt + timedelta(minutes=offset_end)
                    
                    # scraper.livetimeにはオフセット前の元の時間を使用
                    original_session_start_timestamp = int(time.mktime(session_start_dt.timetuple()))
                    original_session_end_timestamp = int(time.mktime(session_end_dt.timetuple()))
                    
                    # 終了時間はオフセット後の時間を使用
                    scraping_end_timestamp = int(time.mktime(scraping_end_dt.timetuple()))
                    
                    now = datetime.now()
                    
                    if now > scraping_end_dt:
                        print("⚠️ スクレイピング終了時刻を過ぎています")
                        update_scraping_status(False, "終了時刻を過ぎています")
                        time.sleep(5)
                        continue
                    
                    # スクレイピング実行関数
                    def run_scraping():
                        try:
                            print("📡 スクレイピング開始")
                            print(f"📅 セッション時間: {session_start_dt} - {session_end_dt}")
                            print(f"🕒 実際のスクレイピング期間: {scraping_start_dt} - {scraping_end_dt}")
                            update_scraping_status(True, "実行中")
                            
                            # timedataとして元のsession_start_dtの情報を保持
                            timedata = session_start_dt
                            
                            scraper = Racelivescraper(url, df0, category_index, sector, car_no_list, driver_list, mk, save_path)
                            # 開始時間：オフセット前、終了時間：オフセット後
                            scraper.livetime(original_session_start_timestamp, scraping_end_timestamp)
                            print("✅ スクレイピング完了")
                            update_scraping_status(False, "完了")
                        except Exception as e:
                            print(f"❌ スクレイピングエラー: {e}")
                            traceback.print_exc()
                            update_scraping_status(False, f"エラー: {str(e)}")
                    
                    # オフセット後のscraping_start_dtの時間にスケジュール
                    schedule_time = scraping_start_dt.strftime("%H:%M")
                    scheduled_job = scheduler.every().day.at(schedule_time).do(run_scraping)
                    
                    if now < scraping_start_dt:
                        remaining_time = scraping_start_dt - now
                        print(f"⏰ スクレイピング開始まで: {remaining_time}")
                        print(f"📅 スケジュール設定: {schedule_time}に実行（オフセット後の時刻）")
                        update_scraping_status(True, f"開始予定: {schedule_time}")
                    else:
                        print("▶️ スクレイピング時間中 - 即座に実行")
                        run_scraping()
                    
                except ValueError as e:
                    print(f"時刻の形式エラー: {e}")
                    original_session_start_timestamp = int(time.mktime(datetime.now().timetuple()))
                    scraping_end_timestamp = int(time.mktime((datetime.now() + timedelta(minutes=2)).timetuple()))
                
                scraping_active = True
                
            elif not should_scraping and scraping_active:
                # スクレイピング停止
                print("🛑 スクレイピング停止指示を受信")
                if scheduled_job:
                    scheduler.cancel_job(scheduled_job)
                    scheduled_job = None
                scraping_active = False
                update_scraping_status(False, "手動停止")
            
            # スケジューラーを実行
            if scraping_active:
                scheduler.run_pending()
            
            time.sleep(1)  # 1秒間隔でチェック
            
        except KeyboardInterrupt:
            print("\n🔚 終了します...")
            if scraping_active:
                update_scraping_status(False, "プログラム終了")
            break
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            traceback.print_exc()
            time.sleep(5)

if __name__ == "__main__":
    main()
