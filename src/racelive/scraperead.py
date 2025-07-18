""" ---------------------------------------------------------------------------------------------------------
    Super Formula Race Live   Ver : 1.2  2025.05

    seleniumを使ったスクレイピング処理を記述するコードです。
    
    1. SuperFormulaのRaceLiveからデータを取得します。
    2. racelive.jpのサービスからのデータ取得なので同じフォーマットのSuperFormula Lightsも読み込み可能。
    3. ウェザーデータの取得も、ここに記述。

----------------------------------------------------------------------------------------------------------"""
import os
import time
from datetime import datetime, timedelta
import ambient
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import traceback

# -------------------------- レース・ライブタイミング・データ読み込み ----------------------------------------------------
class Racelivescraper:
    def __init__(self, url, df0, cat, sector, car_no_list, driver_list, mk, save_path):

        self.url = url
        self.df0 = df0
        self.cat = cat
        self.sector = sector
        self.car_no_list = car_no_list
        self.driver_list = driver_list
        self.mk = mk
        self.save_path = save_path

        # ブラウザを操作するためのwebdriverを設定
        options = Options()
        self.driver = webdriver.Chrome(options=options)
        # chromeを開く
        self.driver.get(self.url)
        self.driver.execute_script("document.body.style.zoom='65%'")  # 80%表示


    # ---------------------- ライブタイム・データの取得 ------------------------------------------------------------------
    def livetime(self, session_start, session_end):
        # セッション開始・終了時間を設定
        self.start_time = session_start
        self.finish_time = session_end

        self.df1 = pd.DataFrame()
        columns1 = [
            "ID", "CarNo", "Driver", "Maker", "Lap", "Position", "Sec 1", "Sec 2", "Sec 3", "Sec 4", "Speed",
            "LapTime (min)", "LapTime", "Elapsed Time", "Tire", "Pit", "Pit In No", "Track Condition",
            "Weather", "Flag", "Remaining Time", "Sampling Time", "Ambient Time", "Ambient Temp", "Ambient K Type",
            "Ambient Track", "Ambient Humidity", "Ambient Pressure", "Weather Time", "Weather Temp", "Weather Humidity",
            "Weather WindSpeed", "Weather WindDirection", "Weather Air Pressure"]


        while True:

            self.dt = datetime.now()
            ftime = int(time.mktime(self.dt.utctimetuple()))
            now = datetime.now()

            if ftime <= self.finish_time:

                if now.second in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:

                    # Super Formula スクレイピング
                    if self.cat == 0:

                        # SF スクレイピング
                        for i in (self.car_no_list):
                            c_no = ("c" + str(i))

                            # トラック・コンディションの取得
                            try:
                                trackcondi = self.driver.find_element(By.CSS_SELECTOR, "#condition")
                                trackcondi = trackcondi.get_attribute("textContent")
                            except Exception:
                                trackcondi = "---"

                            # 天気アイコンの取得
                            try:
                                liveweather = self.driver.find_element(By.XPATH, "//*[@id='weather']")
                                liveweather = liveweather.get_attribute(name="src")
                                weather_name = liveweather.split("/")[-1]
                                weather_name = weather_name[:-4]
                            except Exception:
                                weather_name = "---"

                            # 信号状態を取得
                            try:
                                liveflag = self.driver.find_element(By.XPATH, "//*[@id='liveflag']")
                                liveflag = liveflag.get_attribute(name="src")
                                flag_name = liveflag.split("/")[-1]
                                flag_name = flag_name[:-4]
                            except Exception:
                                flag_name = "---"

                            # セッション残り時間
                            remaining_txt = self.driver.find_element(By.XPATH, "//*[@id='livelaps']").text
                            try:
                                remaining = remaining_txt
                            except Exception:
                                remaining = "00:00:00"

                            try:
                                # カーナンバーを取得
                                car_no = self.driver.find_element(By.ID, c_no + "_no").text

                                # ポジションを取得
                                pos = self.driver.find_element(By.ID, c_no + "_pos").text

                                # Lap数 取得
                                lapno = self.driver.find_element(By.ID, c_no + "_laps").text
                                if lapno == "":
                                    lap = 0
                                else:
                                    lap = lapno

                                # ギャップを取得
                                gap = self.driver.find_element(By.ID, c_no + "_gap").text

                                # デフを取得
                                diff = self.driver.find_element(By.ID, c_no + "_diff").text

                                # ラップタイムを取得
                                try:
                                    lapt = self.driver.find_element(By.ID, c_no + "_last").text
                                    # 00:00.000 を文字列に変換しない
                                    laptime = lapt #.replace(":", "'")
                                except Exception:
                                    laptime = None

                                # ラップタイム（秒）を取得
                                if lapt == "":
                                    laptime_sec = None
                                else:
                                    lts3 = lapt.split(":")[0]
                                    try:
                                        ltsm = int(lts3) * 60
                                        ltss = lapt.split(":")[1]
                                        ltss = float(ltss)
                                        laptime_sec = round(ltsm + ltss, 3)
                                    except Exception:
                                        laptime_sec = None

                                # Sector1 取得
                                try:
                                    sec1 = self.driver.find_element(By.ID, c_no + "_sec1").text
                                    s1_1 = sec1.split(":")[0]
                                    s1_1 = int(s1_1) * 60
                                    s1_2 = sec1.split(":")[1]
                                    s1_2 = float(s1_2)
                                    sec1 = s1_1 + s1_2
                                except Exception:
                                    try:
                                        sec1 = self.driver.find_element(By.ID, c_no + "_sec1").text
                                        sec1 = float(sec1)
                                    except Exception:
                                        sec1 = None

                                # Sector2 取得
                                try:
                                    sec2 = self.driver.find_element(By.ID, c_no + "_sec2").text
                                    s2_1 = sec2.split(":")[0]
                                    s2_1 = int(s2_1) * 60
                                    s2_2 = sec2.split(":")[1]
                                    s2_2 = float(s2_2)
                                    sec2 = s2_1 + s2_2
                                except Exception:
                                    try:
                                        sec2 = self.driver.find_element(By.ID, c_no + "_sec2").text
                                        sec2 = float(sec2)
                                    except Exception:
                                        sec2 = None

                                # Sector3 取得
                                try:
                                    sec3 = self.driver.find_element(By.ID, c_no + "_sec3").text
                                    s3_1 = sec3.split(":")[0]
                                    s3_1 = int(s3_1) * 60
                                    s3_2 = sec3.split(":")[1]
                                    s3_2 = float(s3_2)
                                    sec3 = s3_1 + s3_2
                                except Exception:
                                    try:
                                        sec3 = self.driver.find_element(By.ID, c_no + "_sec3").text
                                        sec3 = float(sec3)
                                    except Exception:
                                        sec3 = None

                                # Sector4 取得
                                try:
                                    sec4 = self.driver.find_element(By.ID, c_no + "_sec4").text
                                    s4_1 = sec4.split(":")[0]
                                    s4_1 = int(s4_1) * 60
                                    s4_2 = sec4.split(":")[1]
                                    s4_2 = float(s4_2)
                                    sec4 = s4_1 + s4_2
                                except Exception:
                                    try:
                                        sec4 = self.driver.find_element(By.ID, c_no + "_sec4").text
                                        sec4 = float(sec4)
                                    except Exception:
                                        sec4 = None

                                # スピード取得
                                try:
                                    speed = self.driver.find_element(By.ID, c_no + "_speed").text
                                except Exception:
                                    speed = None

                                # Pit In 回数 取得
                                try:
                                    ptn = ""
                                except Exception:
                                    ptn = ""

                                # Elapsed Time (経過時間) 取得
                                etime = ""

                                # ピット画像ファイル名からピットイン情報を取得
                                pit = self.driver.find_element(By.XPATH, "//*[@id='" + c_no + "_status']/img")
                                pit_imgSrc = pit.get_attribute(name="src")
                                pit_Name = pit_imgSrc.split("/")[-1]
                                pit = pit_Name[0:3]
                                if pit == "dum":
                                    pit = ""
                                else:
                                    pit = "Pit"

                                # タイヤ画像ファイル名からスペックを取得
                                try:
                                    tire = ""
                                except Exception:
                                    tire = ""

                                # データベース用ID作成
                                id_no = str(i) + "_" + str(lap)

                                self.df0.loc[(self.df0["ID"] == id_no), "Pos"] = pos
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime (min)"] = laptime
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime"] = laptime_sec
                                self.df0.loc[(self.df0["ID"] == id_no), "Tyre"] = tire
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit"] = pit
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit In No"] = ptn

                                if self.sector == 4:
                                    if sec2 == None or sec3 == None or sec4 == None:
                                        id_no = str(car_no) + "_" + str(int(lap) + 1)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                    elif sec4 != None:
                                        id_no = str(car_no) + "_" + str(lap)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 4"] = sec4
                                else:
                                    if sec2 == None or sec3 == None:
                                        id_no = str(car_no) + "_" + str(int(lap) + 1)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                    elif sec3 != None:
                                        id_no = str(car_no) + "_" + str(lap)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3

                                self.df0.loc[(self.df0["ID"] == id_no), "Speed"] = speed

                                self.df0.loc[(self.df0["ID"] == id_no), "Track Condition"] = trackcondi
                                self.df0.loc[(self.df0["ID"] == id_no), "Wwather"] = weather_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Flag"] = flag_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Remaining Time"] = remaining

                                samptime = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                self.df0.loc[(self.df0["ID"] == id_no), "Sampling Time"] = samptime

                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Time"] = "" 
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Temp"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient K Type"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Track"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Humidity"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Pressure"] = ""

                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Time"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Temp"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Humidity"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindSpeed"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindDirection"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Air Pressure"] = ""

                                self.df0.to_csv("./data/livetime.csv", index=True, encoding="shift-jis")

                                try:
                                    car_index = self.car_no_list.index(int(car_no))
                                except Exception:
                                    car_index = self.car_no_list.index(car_no)

                                driver_name = self.driver_list[car_index]
                                maker_name = self.mk[car_index]

                                listdata1 = []
                                listdata1.append(id_no)
                                listdata1.append(car_no)
                                listdata1.append(driver_name)
                                listdata1.append(maker_name)
                                listdata1.append(lap)
                                listdata1.append(pos)
                                listdata1.append(sec1)
                                listdata1.append(sec2)
                                listdata1.append(sec3)
                                listdata1.append(sec4)
                                listdata1.append(speed)
                                listdata1.append(laptime)
                                listdata1.append(laptime_sec)
                                listdata1.append(etime)
                                listdata1.append(tire)
                                listdata1.append(pit)
                                listdata1.append(ptn)
                                listdata1.append(trackcondi)
                                listdata1.append(weather_name)
                                listdata1.append(flag_name)
                                listdata1.append(remaining)
                                listdata1.append(samptime)
                                listdata1.append("")      # Ambient Time
                                listdata1.append("")      # Ambient Temp
                                listdata1.append("")      # Ambient K Type
                                listdata1.append("")      # Ambient Track
                                listdata1.append("")      # Ambient Humidity
                                listdata1.append("")      # Ambient Pressure
                                listdata1.append("")      # Weather Time
                                listdata1.append("")      # Weather Temp
                                listdata1.append("")      # Weather Humidity
                                listdata1.append("")      # Weather WindSpeed
                                listdata1.append("")      # Weather WindDirection
                                listdata1.append("")      # Weather Air Pressure 

                                df = pd.DataFrame([listdata1])
                                df.columns = columns1

                                if not df.empty:
                                    self.df1 = pd.concat([self.df1, df], ignore_index=True)

                                self.df1.to_csv("./data/livetime_replay1.csv", index=True, encoding="shift-jis")

                            except Exception:
                                pass

                    # Super Formula Lights スクレイピング
                    elif self.cat == 1:

                        # SFL スクレイピング
                        for i in (self.car_no_list):
                            c_no = ("c" + str(i))

                            # トラック・コンディションの取得
                            try:
                                trackcondi = self.driver.find_element(By.CSS_SELECTOR, "#condition")
                                trackcondi = trackcondi.get_attribute("textContent")
                            except Exception:
                                trackcondi = "---"

                            # 天気アイコンの取得
                            try:
                                liveweather = self.driver.find_element(By.XPATH, "//*[@id='weather']")
                                liveweather = liveweather.get_attribute(name="src")
                                weather_name = liveweather.split("/")[-1]
                                weather_name = weather_name[:-4]
                            except Exception:
                                weather_name = "---"

                            # 信号状態を取得
                            try:
                                liveflag = self.driver.find_element(By.XPATH, "//*[@id='liveflag']")
                                liveflag = liveflag.get_attribute(name="src")
                                flag_name = liveflag.split("/")[-1]
                                flag_name = flag_name[:-4]
                            except Exception:
                                flag_name = "---"

                            # セッション残り時間
                            remaining_txt = self.driver.find_element(By.XPATH, "//*[@id='livelaps']").text
                            try:
                                remaining = remaining_txt
                            except Exception:
                                remaining = "00:00:00"

                            try:
                                # カーナンバーを取得
                                car_no = self.driver.find_element(By.ID, c_no + "_no").text

                                # ポジションを取得
                                pos = self.driver.find_element(By.ID, c_no + "_pos").text

                                # Lap数 取得
                                lapno = self.driver.find_element(By.ID, c_no + "_laps").text
                                if lapno == "":
                                    lap = 0
                                else:
                                    lap = lapno

                                # ギャップを取得
                                gap = self.driver.find_element(By.ID, c_no + "_gap").text

                                # デフを取得
                                diff = self.driver.find_element(By.ID, c_no + "_diff").text

                                # ラップタイムを取得
                                try:
                                    lapt = self.driver.find_element(By.ID, c_no + "_last").text
                                    # 00:00.000 を文字列に変換しない
                                    laptime = lapt #.replace(":", "'")
                                except Exception:
                                    laptime = None

                                # ラップタイム（秒）を取得
                                if lapt == "":
                                    laptime_sec = None
                                else:
                                    lts3 = lapt.split(":")[0]
                                    try:
                                        ltsm = int(lts3) * 60
                                        ltss = lapt.split(":")[1]
                                        ltss = float(ltss)
                                        laptime_sec = round(ltsm + ltss, 3)
                                    except Exception:
                                        laptime_sec = None

                                # Sector1 取得
                                try:
                                    sec1 = self.driver.find_element(By.ID, c_no + "_sec1").text
                                    s1_1 = sec1.split(":")[0]
                                    s1_1 = int(s1_1) * 60
                                    s1_2 = sec1.split(":")[1]
                                    s1_2 = float(s1_2)
                                    sec1 = s1_1 + s1_2
                                except Exception:
                                    try:
                                        sec1 = self.driver.find_element(By.ID, c_no + "_sec1").text
                                        sec1 = float(sec1)
                                    except Exception:
                                        sec1 = None

                                # Sector2 取得
                                try:
                                    sec2 = self.driver.find_element(By.ID, c_no + "_sec2").text
                                    s2_1 = sec2.split(":")[0]
                                    s2_1 = int(s2_1) * 60
                                    s2_2 = sec2.split(":")[1]
                                    s2_2 = float(s2_2)
                                    sec2 = s2_1 + s2_2
                                except Exception:
                                    try:
                                        sec2 = self.driver.find_element(By.ID, c_no + "_sec2").text
                                        sec2 = float(sec2)
                                    except Exception:
                                        sec2 = None

                                # Sector3 取得
                                try:
                                    sec3 = self.driver.find_element(By.ID, c_no + "_sec3").text
                                    s3_1 = sec3.split(":")[0]
                                    s3_1 = int(s3_1) * 60
                                    s3_2 = sec3.split(":")[1]
                                    s3_2 = float(s3_2)
                                    sec3 = s3_1 + s3_2
                                except Exception:
                                    try:
                                        sec3 = self.driver.find_element(By.ID, c_no + "_sec3").text
                                        sec3 = float(sec3)
                                    except Exception:
                                        sec3 = None

                                # Sector4 取得
                                try:
                                    sec4 = self.driver.find_element(By.ID, c_no + "_sec4").text
                                    s4_1 = sec4.split(":")[0]
                                    s4_1 = int(s4_1) * 60
                                    s4_2 = sec4.split(":")[1]
                                    s4_2 = float(s4_2)
                                    sec4 = s4_1 + s4_2
                                except Exception:
                                    try:
                                        sec4 = self.driver.find_element(By.ID, c_no + "_sec4").text
                                        sec4 = float(sec4)
                                    except Exception:
                                        sec4 = None

                                # スピード取得
                                try:
                                    speed = self.driver.find_element(By.ID, c_no + "_speed").text
                                except Exception:
                                    speed = None

                                # Pit In 回数 取得
                                try:
                                    ptn = ""
                                except Exception:
                                    ptn = ""

                                # Elapsed Time (経過時間) 取得
                                etime = ""

                                # ピット画像ファイル名からピットイン情報を取得
                                pit = self.driver.find_element(By.XPATH, "//*[@id='" + c_no + "_status']/img")
                                pit_imgSrc = pit.get_attribute(name="src")
                                pit_Name = pit_imgSrc.split("/")[-1]
                                pit = pit_Name[0:3]
                                if pit == "dum":
                                    pit = ""
                                else:
                                    pit = "Pit"

                                # タイヤ画像ファイル名からスペックを取得
                                try:
                                    tire = ""
                                except Exception:
                                    tire = ""

                                # データベース用ID作成
                                id_no = str(i) + "_" + str(lap)

                                self.df0.loc[(self.df0["ID"] == id_no), "Pos"] = pos
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime (min)"] = laptime
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime"] = laptime_sec
                                self.df0.loc[(self.df0["ID"] == id_no), "Tyre"] = tire
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit"] = pit
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit In No"] = ptn

                                if self.sector == 4:
                                    if sec2 == None or sec3 == None or sec4 == None:
                                        id_no = str(car_no) + "_" + str(int(lap) + 1)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                    elif sec4 != None:
                                        id_no = str(car_no) + "_" + str(lap)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 4"] = sec4
                                else:
                                    if sec2 == None or sec3 == None:
                                        id_no = str(car_no) + "_" + str(int(lap) + 1)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                    elif sec3 != None:
                                        id_no = str(car_no) + "_" + str(lap)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3

                                self.df0.loc[(self.df0["ID"] == id_no), "Speed"] = speed

                                self.df0.loc[(self.df0["ID"] == id_no), "Track Condition"] = trackcondi
                                self.df0.loc[(self.df0["ID"] == id_no), "Wwather"] = weather_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Flag"] = flag_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Remaining Time"] = remaining

                                samptime = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                self.df0.loc[(self.df0["ID"] == id_no), "Sampling Time"] = samptime

                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Time"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Temp"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient K Type"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Track"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Humidity"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Pressure"] = ""

                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Time"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Temp"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Humidity"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindSpeed"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindDirection"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Air Pressure"] = ""

                                self.df0.to_csv("./data/livetime.csv", index=True, encoding="shift-jis")


                                try:
                                    car_index = self.car_no_list.index(int(car_no))
                                except Exception:
                                    car_index = self.car_no_list.index(car_no)

                                driver_name = self.driver_list[car_index]
                                maker_name = self.mk[car_index]

                                listdata1 = []
                                listdata1.append(id_no)
                                listdata1.append(car_no)
                                listdata1.append(driver_name)
                                listdata1.append(maker_name)
                                listdata1.append(lap)
                                listdata1.append(pos)
                                listdata1.append(sec1)
                                listdata1.append(sec2)
                                listdata1.append(sec3)
                                listdata1.append(sec4)
                                listdata1.append(speed)
                                listdata1.append(laptime)
                                listdata1.append(laptime_sec)
                                listdata1.append(etime)
                                listdata1.append(tire)
                                listdata1.append(pit)
                                listdata1.append(ptn)
                                listdata1.append(trackcondi)
                                listdata1.append(weather_name)
                                listdata1.append(flag_name)
                                listdata1.append(remaining)
                                listdata1.append(samptime)
                                listdata1.append("")      # Ambient Time
                                listdata1.append("")      # Ambient Temp
                                listdata1.append("")      # Ambient K Type
                                listdata1.append("")      # Ambient Track
                                listdata1.append("")      # Ambient Humidity
                                listdata1.append("")      # Ambient Pressure
                                listdata1.append("")      # Weather Time
                                listdata1.append("")      # Weather Temp
                                listdata1.append("")      # Weather Humidity
                                listdata1.append("")      # Weather WindSpeed
                                listdata1.append("")      # Weather WindDirection
                                listdata1.append("")      # Weather Air Pressure 

                                df = pd.DataFrame([listdata1])
                                df.columns = columns1

                                if not df.empty:
                                    self.df1 = pd.concat([self.df1, df], ignore_index=True)

                                self.df1.to_csv("./data/livetime_replay1.csv", index=True, encoding="shift-jis")

                            except Exception:
                                pass

                    # Super GT メソッド
                    elif self.cat == 2:
                        # def racelive_sfreplay(self, racelap, car_max, start_time, finish_time):
                        return {"data": "Super GT Data"}

                    # スーパー耐久 スクレイピング
                    elif self.cat == 3:

                        # ST スクレイピング
                        for index, car_no in enumerate(self.car_no_list, start=1):

                            try:
                                i = index
                                c_no = ("c" + str(car_no))

                                # 総合順位
                                try:
                                    pos = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[1]").text
                                except Exception:
                                    pos = ""

                                # クラス順位
                                try:
                                    pic = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[2]").text
                                except Exception:
                                    pic = ""

                                # カーナンバー
                                try:
                                    car_no= self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[3]").text
                                except Exception:
                                    car_no = ""

                                # クラス
                                try:
                                    cla = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[4]").text
                                except Exception:
                                    cla = ""

                                # ラップ
                                try:
                                    lapno = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[5]").text
                                    if lapno == "":
                                        lap = 0
                                    else:
                                        lap = lapno
                                except Exception:
                                    lap = 0

                                # ドライバーID
                                try:
                                    did = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[6]").text
                                except Exception:
                                    did = ""

                                # ドライバー名
                                try:
                                    dna = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[7]").text
                                except Exception:
                                    dna = ""

                                # ラップ・タイム
                                try:
                                    lapt = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[9]").text
                                    laptime = float(lapt)  # .replace("’", ":") float(s1_2)
                                except Exception:
                                    laptime = None

                                # ラップタイム（秒）を取得
                                if lapt == "":
                                    laptime_sec = None
                                else:
                                    lts3 = lapt.split(":")[0]
                                    try:
                                        ltsm = int(lts3) * 60
                                        ltss = lapt.split(":")[1]
                                        ltss = float(ltss)
                                        laptime_sec = round(ltsm + ltss, 3)
                                    except Exception:
                                        laptime_sec = None

                                # セクター1
                                try:
                                    sec1 = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[13]").text
                                    sec1 = float(sec1)
                                except Exception:
                                    sec1 = None

                                # セクター2
                                try:
                                    sec2 = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[14]").text
                                    sec2 = float(sec2)
                                except Exception:
                                    sec2 = None

                                # セクター3
                                try:
                                    sec3 = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[15]").text
                                    sec3 = float(sec3)
                                except Exception:
                                    sec3 = None

                                # セクター4  //*[@id="timing_table"]/tr[45]/td[16]
                                if self.sector == 4:
                                    try:
                                        sec4 = self.driver.find_element(
                                            By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[16]").text
                                        sec4 = float(sec4)
                                    except Exception:
                                        sec4 = None
                                else:
                                    sec4 = None

                                # スピード  //*[@id="timing_table"]/tr[45]/td[17]
                                try:
                                    speed = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[17]").text
                                    speed = float(speed)
                                except Exception:
                                    speed = None

                                # ピットイン  //*[@id="timing_table"]/tr[45]/td[18]
                                try:
                                    pit = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[18]").text
                                except Exception:
                                    pit = ""

                                # ピットイン回数
                                try:
                                    ptn = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[19]").text
                                except Exception:
                                    ptn = ""

                                # ラスト・ピットイン  //*[@id="timing_table"]/tr[45]/td[20]
                                try:
                                    last_pit = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[20]").text
                                except Exception:
                                    last_pit = ""

                                # Elapsed Time (経過時間) 取得
                                etime = ""

                                # タイヤ画像ファイル名からスペックを取得
                                tire = ""

                                # トラック・コンディションの取得
                                trackcondi = "---"

                                # 天気アイコンの取得
                                weather_name = "---"

                                # 信号状態を取得
                                flag_name = "---"

                                # セッション残り時間
                                remaining = "00:00:00"

                                # データベース用ID作成
                                id_no = str(i) + "_" + str(lap)

                                self.df0.loc[(self.df0["ID"] == id_no), "Pos"] = pos
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime (min)"] = laptime
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime"] = laptime_sec
                                self.df0.loc[(self.df0["ID"] == id_no), "Tyre"] = tire
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit"] = pit
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit In No"] = ptn

                                # if self.sector == 4:

                                if sec2 == None or sec3 == None or sec4 == None:
                                    id_no = str(car_no) + "_" + str(int(lap) + 1)
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                elif sec4 != None:
                                    id_no = str(car_no) + "_" + str(int(lap))
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 4"] = sec4
                                # else:
                                #     if sec2 == None or sec3 == None:
                                #         id_no = str(car_no) + "_" + str(int(lap) + 1)
                                #         self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                #         self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                #     elif sec3 != None:
                                #         id_no = str(car_no) + "_" + str(lap)
                                #         self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                #         self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                #         self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3

                                self.df0.loc[(self.df0["ID"] == id_no), "Speed"] = speed

                                self.df0.loc[(self.df0["ID"] == id_no), "Track Condition"] = trackcondi
                                self.df0.loc[(self.df0["ID"] == id_no), "Wwather"] = weather_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Flag"] = flag_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Remaining Time"] = remaining

                                samptime = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                self.df0.loc[(self.df0["ID"] == id_no), "Sampling Time"] = samptime

                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Time"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Temp"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient K Type"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Track"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Humidity"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Pressure"] = ""

                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Time"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Temp"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Humidity"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindSpeed"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindDirection"] = ""
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Air Pressure"] = ""

                                self.df0.to_csv("./data/livetime.csv", index=True, encoding="shift-jis")

                                try:
                                    if car_no not in [None, ""]:
                                        try:
                                            car_index = self.car_no_list.index(int(car_no))
                                        except Exception:
                                            car_index = self.car_no_list.index(car_no)
                                        driver_name = self.driver_list[car_index]
                                        maker_name = self.mk[car_index]
                                    else:
                                        driver_name = ""
                                        maker_name = ""
                                except Exception:
                                    driver_name = ""
                                    maker_name = ""

                                driver_name = self.driver_list[car_index]
                                maker_name = self.mk[car_index]

                                listdata1 = []
                                listdata1.append(id_no)
                                listdata1.append(car_no)
                                listdata1.append(driver_name)
                                listdata1.append(maker_name)
                                listdata1.append(lap)
                                listdata1.append(pos)
                                listdata1.append(sec1)
                                listdata1.append(sec2)
                                listdata1.append(sec3)
                                listdata1.append(sec4)
                                listdata1.append(speed)
                                listdata1.append(laptime)
                                listdata1.append(laptime_sec)
                                listdata1.append(etime)
                                listdata1.append(tire)
                                listdata1.append(pit)
                                listdata1.append(ptn)
                                listdata1.append(trackcondi)
                                listdata1.append(weather_name)
                                listdata1.append(flag_name)
                                listdata1.append(remaining)
                                listdata1.append(samptime)
                                listdata1.append("")      # Ambient Time
                                listdata1.append("")      # Ambient Temp
                                listdata1.append("")      # Ambient K Type
                                listdata1.append("")      # Ambient Track
                                listdata1.append("")      # Ambient Humidity
                                listdata1.append("")      # Ambient Pressure
                                listdata1.append("")      # Weather Time
                                listdata1.append("")      # Weather Temp
                                listdata1.append("")      # Weather Humidity
                                listdata1.append("")      # Weather WindSpeed
                                listdata1.append("")      # Weather WindDirection
                                listdata1.append("")      # Weather Air Pressure 

                                df = pd.DataFrame([listdata1])
                                df.columns = columns1

                                if not df.empty:
                                    self.df1 = pd.concat([self.df1, df], ignore_index=True)

                                self.df1.to_csv("./data/livetime_replay1.csv", index=True, encoding="shift-jis")

                            except Exception:
                                pass

                    # Super Formula Replay メソッド
                    elif self.cat == 4:
                        # def racelive_sfreplay(self, racelap, car_max, start_time, finish_time):
                        return {"data": "Super Formula Data"}

                time.sleep(0.2)

            elif ftime >= self.finish_time:
                # セッション終了時の処理
                # セッション終了時の処理
                self.df0.to_csv(self.save_path + "_livetime.csv", index=True, encoding="shift-jis")
                self.df1.to_csv(self.save_path + "_livetime_replay.csv", index=True, encoding="shift-jis")
                self.driver.quit()
                break

        # ループ終了後、最終のself.df0を返す
        return self.df0


    def livetime_replay(self, file):
        self.file = file



    # ---------------------- ライブタイム・ウェザーメソッド ---------------------------------------------------------------
    def livetime_weather(self, session_start, session_end, ambient_id, ambient_read_key, wea_path):
        # セッション開始・終了時間を設定
        self.start_time = session_start
        self.finish_time = session_end
        self.ambient_id = ambient_id
        self.ambient_read_key = ambient_read_key
        self.wea_path = wea_path

        self.df1 = pd.DataFrame()
        columns1 = [
            "ID", "CarNo", "Driver", "Maker", "Lap", "Position", "Sec 1", "Sec 2", "Sec 3", "Sec 4", "Speed",
            "LapTime (min)", "LapTime", "Elapsed Time", "Tire", "Pit", "Pit In No", "Track Condition",
            "Weather", "Flag", "Remaining Time", "Sampling Time", "Ambient Time", "Ambient Temp", "Ambient K Type",
            "Ambient Track", "Ambient Humidity", "Ambient Pressure", "Weather Time", "Weather Temp", "Weather Humidity",
            "Weather WindSpeed", "Weather WindDirection", "Weather Air Pressure"]


        while True:

            self.dt = datetime.now()
            ftime = int(time.mktime(self.dt.utctimetuple()))
            now = datetime.now()

            if ftime <= self.finish_time:

                if now.second in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:

                    # ★ 5秒の時だけ追加処理
                    if now.second == 5:

                        am = ambient.Ambient(self.ambient_id, "", self.ambient_read_key)
                        da = am.read(n=1)
                        df_amb = pd.DataFrame(da)
                        df_amb["created"] = pd.to_datetime(list(df_amb["created"])).tz_convert("Asia/Tokyo").tz_localize(None)
                        df_amb = df_amb.set_index("created")

                        # インデックスをリセットしてリストに変換
                        df_reset = df_amb.reset_index()
                        data_list = df_reset.values.tolist()
                        # データフレームを作成
                        df_ambient = pd.DataFrame(data_list, columns=["日付", "Ambient Temp", "Ambient K Type", "Ambient Track", "Ambient Humidity", "Ambient Pressure"])
                        df_ambient["Ambient Time"] = df_ambient["日付"].dt.strftime("%H:%M")
                        df_ambient["日付"] = df_ambient["日付"].dt.date
                        df_ambient = df_ambient.set_index("Ambient Time")
                        df_ambient = df_ambient.drop(columns=["日付"])
                        # df_ambientの最新行（または1行目）をSeriesで取得
                        ambient_row = df_ambient.iloc[0]

                        # df_weather = pd.read_csv(self.wea_path, delim_whitespace=True, header=1)
                        df_weather = pd.read_csv(self.wea_path, sep='\s+', header=1)
                        # 最終行を取得して特定の列を選択（列番号で指定）
                        weather_last_row = df_weather.tail(1)

                    # Super Formula スクレイピング
                    if self.cat == 0:

                        # SF スクレイピング
                        for i in (self.car_no_list):
                            c_no = ("c" + str(i))

                            # トラック・コンディションの取得
                            try:
                                trackcondi = self.driver.find_element(By.CSS_SELECTOR, "#condition")
                                trackcondi = trackcondi.get_attribute("textContent")
                            except Exception:
                                trackcondi = "---"

                            # 天気アイコンの取得
                            try:
                                liveweather = self.driver.find_element(By.XPATH, "//*[@id='weather']")
                                liveweather = liveweather.get_attribute(name="src")
                                weather_name = liveweather.split("/")[-1]
                                weather_name = weather_name[:-4]
                            except Exception:
                                weather_name = "---"

                            # 信号状態を取得
                            try:
                                liveflag = self.driver.find_element(By.XPATH, "//*[@id='liveflag']")
                                liveflag = liveflag.get_attribute(name="src")
                                flag_name = liveflag.split("/")[-1]
                                flag_name = flag_name[:-4]
                            except Exception:
                                flag_name = "---"

                            # セッション残り時間
                            remaining_txt = self.driver.find_element(By.XPATH, "//*[@id='livelaps']").text
                            try:
                                remaining = remaining_txt
                            except Exception:
                                remaining = "00:00:00"

                            try:
                                # カーナンバーを取得
                                car_no = self.driver.find_element(By.ID, c_no + "_no").text

                                # ポジションを取得
                                pos = self.driver.find_element(By.ID, c_no + "_pos").text

                                # Lap数 取得
                                lapno = self.driver.find_element(By.ID, c_no + "_laps").text
                                if lapno == "":
                                    lap = 0
                                else:
                                    lap = lapno

                                # ギャップを取得
                                gap = self.driver.find_element(By.ID, c_no + "_gap").text

                                # デフを取得
                                diff = self.driver.find_element(By.ID, c_no + "_diff").text

                                # ラップタイムを取得
                                try:
                                    lapt = self.driver.find_element(By.ID, c_no + "_last").text
                                    # 00:00.000 を文字列に変換しない
                                    laptime = lapt #.replace(":", "'")
                                except Exception:
                                    laptime = None

                                # ラップタイム（秒）を取得
                                if lapt == "":
                                    laptime_sec = None
                                else:
                                    lts3 = lapt.split(":")[0]
                                    try:
                                        ltsm = int(lts3) * 60
                                        ltss = lapt.split(":")[1]
                                        ltss = float(ltss)
                                        laptime_sec = round(ltsm + ltss, 3)
                                    except Exception:
                                        laptime_sec = None

                                # Sector1 取得
                                try:
                                    sec1 = self.driver.find_element(By.ID, c_no + "_sec1").text
                                    s1_1 = sec1.split(":")[0]
                                    s1_1 = int(s1_1) * 60
                                    s1_2 = sec1.split(":")[1]
                                    s1_2 = float(s1_2)
                                    sec1 = s1_1 + s1_2
                                except Exception:
                                    try:
                                        sec1 = self.driver.find_element(By.ID, c_no + "_sec1").text
                                        sec1 = float(sec1)
                                    except Exception:
                                        sec1 = None

                                # Sector2 取得
                                try:
                                    sec2 = self.driver.find_element(By.ID, c_no + "_sec2").text
                                    s2_1 = sec2.split(":")[0]
                                    s2_1 = int(s2_1) * 60
                                    s2_2 = sec2.split(":")[1]
                                    s2_2 = float(s2_2)
                                    sec2 = s2_1 + s2_2
                                except Exception:
                                    try:
                                        sec2 = self.driver.find_element(By.ID, c_no + "_sec2").text
                                        sec2 = float(sec2)
                                    except Exception:
                                        sec2 = None

                                # Sector3 取得
                                try:
                                    sec3 = self.driver.find_element(By.ID, c_no + "_sec3").text
                                    s3_1 = sec3.split(":")[0]
                                    s3_1 = int(s3_1) * 60
                                    s3_2 = sec3.split(":")[1]
                                    s3_2 = float(s3_2)
                                    sec3 = s3_1 + s3_2
                                except Exception:
                                    try:
                                        sec3 = self.driver.find_element(By.ID, c_no + "_sec3").text
                                        sec3 = float(sec3)
                                    except Exception:
                                        sec3 = None

                                # Sector4 取得
                                try:
                                    sec4 = self.driver.find_element(By.ID, c_no + "_sec4").text
                                    s4_1 = sec4.split(":")[0]
                                    s4_1 = int(s4_1) * 60
                                    s4_2 = sec4.split(":")[1]
                                    s4_2 = float(s4_2)
                                    sec4 = s4_1 + s4_2
                                except Exception:
                                    try:
                                        sec4 = self.driver.find_element(By.ID, c_no + "_sec4").text
                                        sec4 = float(sec4)
                                    except Exception:
                                        sec4 = None

                                # スピード取得
                                try:
                                    speed = self.driver.find_element(By.ID, c_no + "_speed").text
                                except Exception:
                                    speed = None

                                # Pit In 回数 取得
                                try:
                                    ptn = ""
                                except Exception:
                                    ptn = ""

                                # Elapsed Time (経過時間) 取得
                                etime = ""

                                # ピット画像ファイル名からピットイン情報を取得
                                pit = self.driver.find_element(By.XPATH, "//*[@id='" + c_no + "_status']/img")
                                pit_imgSrc = pit.get_attribute(name="src")
                                pit_Name = pit_imgSrc.split("/")[-1]
                                pit = pit_Name[0:3]
                                if pit == "dum":
                                    pit = ""
                                else:
                                    pit = "Pit"

                                # タイヤ画像ファイル名からスペックを取得
                                try:
                                    tire = ""
                                except Exception:
                                    tire = ""

                                # データベース用ID作成
                                id_no = str(i) + "_" + str(lap)

                                self.df0.loc[(self.df0["ID"] == id_no), "Pos"] = pos
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime (min)"] = laptime
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime"] = laptime_sec
                                self.df0.loc[(self.df0["ID"] == id_no), "Tyre"] = tire
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit"] = pit
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit In No"] = ptn

                                if self.sector == 4:
                                    if sec2 == None or sec3 == None or sec4 == None:
                                        id_no = str(car_no) + "_" + str(int(lap) + 1)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                    elif sec4 != None:
                                        id_no = str(car_no) + "_" + str(lap)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 4"] = sec4
                                else:
                                    if sec2 == None or sec3 == None:
                                        id_no = str(car_no) + "_" + str(int(lap) + 1)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                    elif sec3 != None:
                                        id_no = str(car_no) + "_" + str(lap)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3

                                self.df0.loc[(self.df0["ID"] == id_no), "Speed"] = speed

                                self.df0.loc[(self.df0["ID"] == id_no), "Track Condition"] = trackcondi
                                self.df0.loc[(self.df0["ID"] == id_no), "Wwather"] = weather_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Flag"] = flag_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Remaining Time"] = remaining

                                samptime = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                self.df0.loc[(self.df0["ID"] == id_no), "Sampling Time"] = samptime

                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Time"] = ambient_row.name
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Temp"] = ambient_row["Ambient Temp"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient K Type"] = ambient_row["Ambient K Type"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Track"] = ambient_row["Ambient Track"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Humidity"] = ambient_row["Ambient Humidity"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Pressure"] = ambient_row["Ambient Pressure"]

                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Time"] = weather_last_row.iloc[0, 1]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Temp"] = weather_last_row.iloc[0, 2]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Humidity"] = weather_last_row.iloc[0, 5]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindSpeed"] = weather_last_row.iloc[0, 7]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindDirection"] = weather_last_row.iloc[0, 8]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Air Pressure"] = weather_last_row.iloc[0, 15]

                                self.df0.to_csv("./data/livetime.csv", index=True, encoding="shift-jis")

                                try:
                                    car_index = self.car_no_list.index(int(car_no))
                                except Exception:
                                    car_index = self.car_no_list.index(car_no)

                                driver_name = self.driver_list[car_index]
                                maker_name = self.mk[car_index]

                                listdata1 = []
                                listdata1.append(id_no)
                                listdata1.append(car_no)
                                listdata1.append(driver_name)
                                listdata1.append(maker_name)
                                listdata1.append(lap)
                                listdata1.append(pos)
                                listdata1.append(sec1)
                                listdata1.append(sec2)
                                listdata1.append(sec3)
                                listdata1.append(sec4)
                                listdata1.append(speed)
                                listdata1.append(laptime)
                                listdata1.append(laptime_sec)
                                listdata1.append(etime)
                                listdata1.append(tire)
                                listdata1.append(pit)
                                listdata1.append(ptn)
                                listdata1.append(trackcondi)
                                listdata1.append(weather_name)
                                listdata1.append(flag_name)
                                listdata1.append(remaining)
                                listdata1.append(samptime)
                                listdata1.append(ambient_row.name)                 # Ambient Time
                                listdata1.append(ambient_row[ "Ambient Temp"])     # Ambient Temp
                                listdata1.append(ambient_row["Ambient K Type"])    # Ambient K Type
                                listdata1.append(ambient_row["Ambient Track"])     # Ambient Track
                                listdata1.append(ambient_row["Ambient Humidity"])  # Ambient Humidity
                                listdata1.append(ambient_row["Ambient Pressure"])  # Ambient Pressure
                                listdata1.append(weather_last_row.iloc[0, 1])      # Weather Time
                                listdata1.append(weather_last_row.iloc[0, 2])      # Weather Temp
                                listdata1.append(weather_last_row.iloc[0, 5])      # Weather Humidity
                                listdata1.append(weather_last_row.iloc[0, 7])      # Weather WindSpeed
                                listdata1.append(weather_last_row.iloc[0, 8])      # Weather WindDirection
                                listdata1.append(weather_last_row.iloc[0, 15])     # Weather Air Pressure 

                                df = pd.DataFrame([listdata1])
                                df.columns = columns1

                                if not df.empty:
                                    self.df1 = pd.concat([self.df1, df], ignore_index=True)

                                self.df1.to_csv("./data/livetime_replay1.csv", index=True, encoding="shift-jis")

                            except Exception:
                                pass

                    # Super Formula Lights スクレイピング
                    elif self.cat == 1:

                        # SFL スクレイピング
                        for i in (self.car_no_list):
                            c_no = ("c" + str(i))

                            # トラック・コンディションの取得
                            try:
                                trackcondi = self.driver.find_element(By.CSS_SELECTOR, "#condition")
                                trackcondi = trackcondi.get_attribute("textContent")
                            except Exception:
                                trackcondi = "---"

                            # 天気アイコンの取得
                            try:
                                liveweather = self.driver.find_element(By.XPATH, "//*[@id='weather']")
                                liveweather = liveweather.get_attribute(name="src")
                                weather_name = liveweather.split("/")[-1]
                                weather_name = weather_name[:-4]
                            except Exception:
                                weather_name = "---"

                            # 信号状態を取得
                            try:
                                liveflag = self.driver.find_element(By.XPATH, "//*[@id='liveflag']")
                                liveflag = liveflag.get_attribute(name="src")
                                flag_name = liveflag.split("/")[-1]
                                flag_name = flag_name[:-4]
                            except Exception:
                                flag_name = "---"

                            # セッション残り時間
                            remaining_txt = self.driver.find_element(By.XPATH, "//*[@id='livelaps']").text
                            try:
                                remaining = remaining_txt
                            except Exception:
                                remaining = "00:00:00"

                            try:
                                # カーナンバーを取得
                                car_no = self.driver.find_element(By.ID, c_no + "_no").text

                                # ポジションを取得
                                pos = self.driver.find_element(By.ID, c_no + "_pos").text

                                # Lap数 取得
                                lapno = self.driver.find_element(By.ID, c_no + "_laps").text
                                if lapno == "":
                                    lap = 0
                                else:
                                    lap = lapno

                                # ギャップを取得
                                gap = self.driver.find_element(By.ID, c_no + "_gap").text

                                # デフを取得
                                diff = self.driver.find_element(By.ID, c_no + "_diff").text

                                # ラップタイムを取得
                                try:
                                    lapt = self.driver.find_element(By.ID, c_no + "_last").text
                                    # 00:00.000 を文字列に変換しない
                                    laptime = lapt #.replace(":", "'")
                                except Exception:
                                    laptime = None

                                # ラップタイム（秒）を取得
                                if lapt == "":
                                    laptime_sec = None
                                else:
                                    lts3 = lapt.split(":")[0]
                                    try:
                                        ltsm = int(lts3) * 60
                                        ltss = lapt.split(":")[1]
                                        ltss = float(ltss)
                                        laptime_sec = round(ltsm + ltss, 3)
                                    except Exception:
                                        laptime_sec = None

                                # Sector1 取得
                                try:
                                    sec1 = self.driver.find_element(By.ID, c_no + "_sec1").text
                                    s1_1 = sec1.split(":")[0]
                                    s1_1 = int(s1_1) * 60
                                    s1_2 = sec1.split(":")[1]
                                    s1_2 = float(s1_2)
                                    sec1 = s1_1 + s1_2
                                except Exception:
                                    try:
                                        sec1 = self.driver.find_element(By.ID, c_no + "_sec1").text
                                        sec1 = float(sec1)
                                    except Exception:
                                        sec1 = None

                                # Sector2 取得
                                try:
                                    sec2 = self.driver.find_element(By.ID, c_no + "_sec2").text
                                    s2_1 = sec2.split(":")[0]
                                    s2_1 = int(s2_1) * 60
                                    s2_2 = sec2.split(":")[1]
                                    s2_2 = float(s2_2)
                                    sec2 = s2_1 + s2_2
                                except Exception:
                                    try:
                                        sec2 = self.driver.find_element(By.ID, c_no + "_sec2").text
                                        sec2 = float(sec2)
                                    except Exception:
                                        sec2 = None

                                # Sector3 取得
                                try:
                                    sec3 = self.driver.find_element(By.ID, c_no + "_sec3").text
                                    s3_1 = sec3.split(":")[0]
                                    s3_1 = int(s3_1) * 60
                                    s3_2 = sec3.split(":")[1]
                                    s3_2 = float(s3_2)
                                    sec3 = s3_1 + s3_2
                                except Exception:
                                    try:
                                        sec3 = self.driver.find_element(By.ID, c_no + "_sec3").text
                                        sec3 = float(sec3)
                                    except Exception:
                                        sec3 = None

                                # Sector4 取得
                                try:
                                    sec4 = self.driver.find_element(By.ID, c_no + "_sec4").text
                                    s4_1 = sec4.split(":")[0]
                                    s4_1 = int(s4_1) * 60
                                    s4_2 = sec4.split(":")[1]
                                    s4_2 = float(s4_2)
                                    sec4 = s4_1 + s4_2
                                except Exception:
                                    try:
                                        sec4 = self.driver.find_element(By.ID, c_no + "_sec4").text
                                        sec4 = float(sec4)
                                    except Exception:
                                        sec4 = None

                                # スピード取得
                                try:
                                    speed = self.driver.find_element(By.ID, c_no + "_speed").text
                                except Exception:
                                    speed = None

                                # Pit In 回数 取得
                                try:
                                    ptn = ""
                                except Exception:
                                    ptn = ""

                                # Elapsed Time (経過時間) 取得
                                etime = ""

                                # ピット画像ファイル名からピットイン情報を取得
                                pit = self.driver.find_element(By.XPATH, "//*[@id='" + c_no + "_status']/img")
                                pit_imgSrc = pit.get_attribute(name="src")
                                pit_Name = pit_imgSrc.split("/")[-1]
                                pit = pit_Name[0:3]
                                if pit == "dum":
                                    pit = ""
                                else:
                                    pit = "Pit"

                                # タイヤ画像ファイル名からスペックを取得
                                try:
                                    tire = ""
                                except Exception:
                                    tire = ""

                                # データベース用ID作成
                                id_no = str(i) + "_" + str(lap)

                                self.df0.loc[(self.df0["ID"] == id_no), "Pos"] = pos
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime (min)"] = laptime
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime"] = laptime_sec
                                self.df0.loc[(self.df0["ID"] == id_no), "Tyre"] = tire
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit"] = pit
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit In No"] = ptn

                                if self.sector == 4:
                                    if sec2 == None or sec3 == None or sec4 == None:
                                        id_no = str(car_no) + "_" + str(int(lap) + 1)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                    elif sec4 != None:
                                        id_no = str(car_no) + "_" + str(lap)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 4"] = sec4
                                else:
                                    if sec2 == None or sec3 == None:
                                        id_no = str(car_no) + "_" + str(int(lap) + 1)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                    elif sec3 != None:
                                        id_no = str(car_no) + "_" + str(lap)
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                        self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3

                                self.df0.loc[(self.df0["ID"] == id_no), "Speed"] = speed

                                self.df0.loc[(self.df0["ID"] == id_no), "Track Condition"] = trackcondi
                                self.df0.loc[(self.df0["ID"] == id_no), "Wwather"] = weather_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Flag"] = flag_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Remaining Time"] = remaining

                                samptime = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                self.df0.loc[(self.df0["ID"] == id_no), "Sampling Time"] = samptime

                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Time"] = ambient_row.name
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Temp"] = ambient_row["Ambient Temp"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient K Type"] = ambient_row["Ambient K Type"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Track"] = ambient_row["Ambient Track"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Humidity"] = ambient_row["Ambient Humidity"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Pressure"] = ambient_row["Ambient Pressure"]

                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Time"] = weather_last_row.iloc[0, 1]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Temp"] = weather_last_row.iloc[0, 2]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Humidity"] = weather_last_row.iloc[0, 5]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindSpeed"] = weather_last_row.iloc[0, 7]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindDirection"] = weather_last_row.iloc[0, 8]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Air Pressure"] = weather_last_row.iloc[0, 15]

                                self.df0.to_csv("./data/livetime.csv", index=True, encoding="shift-jis")


                                try:
                                    car_index = self.car_no_list.index(int(car_no))
                                except Exception:
                                    car_index = self.car_no_list.index(car_no)

                                driver_name = self.driver_list[car_index]
                                maker_name = self.mk[car_index]

                                listdata1 = []
                                listdata1.append(id_no)
                                listdata1.append(car_no)
                                listdata1.append(driver_name)
                                listdata1.append(maker_name)
                                listdata1.append(lap)
                                listdata1.append(pos)
                                listdata1.append(sec1)
                                listdata1.append(sec2)
                                listdata1.append(sec3)
                                listdata1.append(sec4)
                                listdata1.append(speed)
                                listdata1.append(laptime)
                                listdata1.append(laptime_sec)
                                listdata1.append(etime)
                                listdata1.append(tire)
                                listdata1.append(pit)
                                listdata1.append(ptn)
                                listdata1.append(trackcondi)
                                listdata1.append(weather_name)
                                listdata1.append(flag_name)
                                listdata1.append(remaining)
                                listdata1.append(samptime)
                                listdata1.append(ambient_row.name)                 # Ambient Time
                                listdata1.append(ambient_row[ "Ambient Temp"])     # Ambient Temp
                                listdata1.append(ambient_row["Ambient K Type"])    # Ambient K Type
                                listdata1.append(ambient_row["Ambient Track"])     # Ambient Track
                                listdata1.append(ambient_row["Ambient Humidity"])  # Ambient Humidity
                                listdata1.append(ambient_row["Ambient Pressure"])  # Ambient Pressure
                                listdata1.append(weather_last_row.iloc[0, 1])      # Weather Time
                                listdata1.append(weather_last_row.iloc[0, 2])      # Weather Temp
                                listdata1.append(weather_last_row.iloc[0, 5])      # Weather Humidity
                                listdata1.append(weather_last_row.iloc[0, 7])      # Weather WindSpeed
                                listdata1.append(weather_last_row.iloc[0, 8])      # Weather WindDirection
                                listdata1.append(weather_last_row.iloc[0, 15])     # Weather Air Pressure 

                                df = pd.DataFrame([listdata1])
                                df.columns = columns1

                                if not df.empty:
                                    self.df1 = pd.concat([self.df1, df], ignore_index=True)

                                self.df1.to_csv("./data/livetime_replay1.csv", index=True, encoding="shift-jis")

                            except Exception:
                                pass

                    # Super GT メソッド
                    elif self.cat == 2:
                        # def racelive_sfreplay(self, racelap, car_max, start_time, finish_time):
                        return {"data": "Super GT Data"}

                    # スーパー耐久 スクレイピング
                    elif self.cat == 3:

                        # ST スクレイピング
                        for index, car_no in enumerate(self.car_no_list, start=1):

                            try:
                                i = index
                                c_no = ("c" + str(car_no))

                                # 総合順位
                                try:
                                    pos = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[1]").text
                                except Exception:
                                    pos = ""

                                # クラス順位
                                try:
                                    pic = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[2]").text
                                except Exception:
                                    pic = ""

                                # カーナンバー
                                try:
                                    car_no= self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[3]").text
                                except Exception:
                                    car_no = ""

                                # クラス
                                try:
                                    cla = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[4]").text
                                except Exception:
                                    cla = ""

                                # ラップ
                                try:
                                    lapno = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[5]").text
                                    if lapno == "":
                                        lap = 0
                                    else:
                                        lap = lapno
                                except Exception:
                                    lap = 0

                                # ドライバーID
                                try:
                                    did = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[6]").text
                                except Exception:
                                    did = ""

                                # ドライバー名
                                try:
                                    dna = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[7]").text
                                except Exception:
                                    dna = ""

                                # ラップ・タイム
                                try:
                                    lapt = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[9]").text
                                    laptime = float(lapt)  # .replace("’", ":") float(s1_2)
                                except Exception:
                                    laptime = None

                                # ラップタイム（秒）を取得
                                if lapt == "":
                                    laptime_sec = None
                                else:
                                    lts3 = lapt.split(":")[0]
                                    try:
                                        ltsm = int(lts3) * 60
                                        ltss = lapt.split(":")[1]
                                        ltss = float(ltss)
                                        laptime_sec = round(ltsm + ltss, 3)
                                    except Exception:
                                        laptime_sec = None

                                # セクター1
                                try:
                                    sec1 = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[13]").text
                                    sec1 = float(sec1)
                                except Exception:
                                    sec1 = None

                                # セクター2
                                try:
                                    sec2 = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[14]").text
                                    sec2 = float(sec2)
                                except Exception:
                                    sec2 = None

                                # セクター3
                                try:
                                    sec3 = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[15]").text
                                    sec3 = float(sec3)
                                except Exception:
                                    sec3 = None

                                # セクター4  //*[@id="timing_table"]/tr[45]/td[16]
                                if self.sector == 4:
                                    try:
                                        sec4 = self.driver.find_element(
                                            By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[16]").text
                                        sec4 = float(sec4)
                                    except Exception:
                                        sec4 = None
                                else:
                                    sec4 = None

                                # スピード  //*[@id="timing_table"]/tr[45]/td[17]
                                try:
                                    speed = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[17]").text
                                    speed = float(speed)
                                except Exception:
                                    speed = None

                                # ピットイン  //*[@id="timing_table"]/tr[45]/td[18]
                                try:
                                    pit = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[18]").text
                                except Exception:
                                    pit = ""

                                # ピットイン回数
                                try:
                                    ptn = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[19]").text
                                except Exception:
                                    ptn = ""

                                # ラスト・ピットイン  //*[@id="timing_table"]/tr[45]/td[20]
                                try:
                                    last_pit = self.driver.find_element(
                                        By.XPATH, "//*[@id='timing_table']/tr[" + str((i + 2)) + "]/td[20]").text
                                except Exception:
                                    last_pit = ""

                                # Elapsed Time (経過時間) 取得
                                etime = ""

                                # タイヤ画像ファイル名からスペックを取得
                                tire = ""

                                # トラック・コンディションの取得
                                trackcondi = "---"

                                # 天気アイコンの取得
                                weather_name = "---"

                                # 信号状態を取得
                                flag_name = "---"

                                # セッション残り時間
                                remaining = "00:00:00"

                                # データベース用ID作成
                                id_no = str(i) + "_" + str(lap)

                                self.df0.loc[(self.df0["ID"] == id_no), "Pos"] = pos
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime (min)"] = laptime
                                self.df0.loc[(self.df0["ID"] == id_no), "LapTime"] = laptime_sec
                                self.df0.loc[(self.df0["ID"] == id_no), "Tyre"] = tire
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit"] = pit
                                self.df0.loc[(self.df0["ID"] == id_no), "Pit In No"] = ptn

                                # if self.sector == 4:

                                if sec2 == None or sec3 == None or sec4 == None:
                                    id_no = str(car_no) + "_" + str(int(lap) + 1)
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                elif sec4 != None:
                                    id_no = str(car_no) + "_" + str(int(lap))
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3
                                    self.df0.loc[(self.df0["ID"] == id_no), "Sec 4"] = sec4
                                # else:
                                #     if sec2 == None or sec3 == None:
                                #         id_no = str(car_no) + "_" + str(int(lap) + 1)
                                #         self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                #         self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                #     elif sec3 != None:
                                #         id_no = str(car_no) + "_" + str(lap)
                                #         self.df0.loc[(self.df0["ID"] == id_no), "Sec 1"] = sec1
                                #         self.df0.loc[(self.df0["ID"] == id_no), "Sec 2"] = sec2
                                #         self.df0.loc[(self.df0["ID"] == id_no), "Sec 3"] = sec3

                                self.df0.loc[(self.df0["ID"] == id_no), "Speed"] = speed

                                self.df0.loc[(self.df0["ID"] == id_no), "Track Condition"] = trackcondi
                                self.df0.loc[(self.df0["ID"] == id_no), "Wwather"] = weather_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Flag"] = flag_name
                                self.df0.loc[(self.df0["ID"] == id_no), "Remaining Time"] = remaining

                                samptime = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                self.df0.loc[(self.df0["ID"] == id_no), "Sampling Time"] = samptime

                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Time"] = ambient_row.name
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Temp"] = ambient_row["Ambient Temp"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient K Type"] = ambient_row["Ambient K Type"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Track"] = ambient_row["Ambient Track"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Humidity"] = ambient_row["Ambient Humidity"]
                                self.df0.loc[(self.df0["ID"] == id_no), "Ambient Pressure"] = ambient_row["Ambient Pressure"]

                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Time"] = weather_last_row.iloc[0, 1]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Temp"] = weather_last_row.iloc[0, 2]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Humidity"] = weather_last_row.iloc[0, 5]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindSpeed"] = weather_last_row.iloc[0, 7]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather WindDirection"] = weather_last_row.iloc[0, 8]
                                self.df0.loc[(self.df0["ID"] == id_no), "Weather Air Pressure"] = weather_last_row.iloc[0, 15]

                                self.df0.to_csv("./data/livetime.csv", index=True, encoding="shift-jis")

                                try:
                                    if car_no not in [None, ""]:
                                        try:
                                            car_index = self.car_no_list.index(int(car_no))
                                        except Exception:
                                            car_index = self.car_no_list.index(car_no)
                                        driver_name = self.driver_list[car_index]
                                        maker_name = self.mk[car_index]
                                    else:
                                        driver_name = ""
                                        maker_name = ""
                                except Exception:
                                    driver_name = ""
                                    maker_name = ""

                                driver_name = self.driver_list[car_index]
                                maker_name = self.mk[car_index]

                                listdata1 = []
                                listdata1.append(id_no)
                                listdata1.append(car_no)
                                listdata1.append(driver_name)
                                listdata1.append(maker_name)
                                listdata1.append(lap)
                                listdata1.append(pos)
                                listdata1.append(sec1)
                                listdata1.append(sec2)
                                listdata1.append(sec3)
                                listdata1.append(sec4)
                                listdata1.append(speed)
                                listdata1.append(laptime)
                                listdata1.append(laptime_sec)
                                listdata1.append(etime)
                                listdata1.append(tire)
                                listdata1.append(pit)
                                listdata1.append(ptn)
                                listdata1.append(trackcondi)
                                listdata1.append(weather_name)
                                listdata1.append(flag_name)
                                listdata1.append(remaining)
                                listdata1.append(samptime)
                                listdata1.append(ambient_row.name)                 # Ambient Time
                                listdata1.append(ambient_row[ "Ambient Temp"])     # Ambient Temp
                                listdata1.append(ambient_row["Ambient K Type"])    # Ambient K Type
                                listdata1.append(ambient_row["Ambient Track"])     # Ambient Track
                                listdata1.append(ambient_row["Ambient Humidity"])  # Ambient Humidity
                                listdata1.append(ambient_row["Ambient Pressure"])  # Ambient Pressure
                                listdata1.append(weather_last_row.iloc[0, 1])      # Weather Time
                                listdata1.append(weather_last_row.iloc[0, 2])      # Weather Temp
                                listdata1.append(weather_last_row.iloc[0, 5])      # Weather Humidity
                                listdata1.append(weather_last_row.iloc[0, 7])      # Weather WindSpeed
                                listdata1.append(weather_last_row.iloc[0, 8])      # Weather WindDirection
                                listdata1.append(weather_last_row.iloc[0, 15])     # Weather Air Pressure 

                                df = pd.DataFrame([listdata1])
                                df.columns = columns1

                                if not df.empty:
                                    self.df1 = pd.concat([self.df1, df], ignore_index=True)

                                self.df1.to_csv("./data/livetime_replay1.csv", index=True, encoding="shift-jis")

                            except Exception:
                                pass

                    # Super Formula Replay メソッド
                    elif self.cat == 4:
                        # def racelive_sfreplay(self, racelap, car_max, start_time, finish_time):
                        return {"data": "Super Formula Data"}

                time.sleep(0.2)

            elif ftime >= self.finish_time:
                # セッション終了時の処理
                self.df0.to_csv(self.save_path + "_livetime.csv", index=True, encoding="shift-jis")
                self.df1.to_csv(self.save_path + "_livetime_replay.csv", index=True, encoding="shift-jis")
                self.driver.quit()
                break

        # ループ終了後、最終のself.df0を返す
        return self.df0


    def livetime_replay(self, file):
        self.file = file



def ambientupdate_data(ambient_id, ambient_read_key):

    am = ambient.Ambient(ambient_id, "", ambient_read_key)
    # 最新のデータを取得
    d = am.read(n=1)
    df = pd.DataFrame(d)
    df["created"] = pd.to_datetime(list(df["created"])).tz_convert("Asia/Tokyo").tz_localize(None)
    df = df.set_index("created")

    # インデックスをリセットしてリストに変換
    df_reset = df.reset_index()
    data_list = df_reset.values.tolist()

    # データフレームを作成
    df_ambient = pd.DataFrame(data_list, columns=["日付", "気温 (Ambient)", "ピット", "路温", "湿度 (Ambient)", "気圧 (Ambient)"])
    df_ambient["時間"] = df_ambient["日付"].dt.strftime("%H:%M")
    df_ambient["日付"] = df_ambient["日付"].dt.date
    df_ambient = df_ambient.set_index("時間")
    df_ambient = df_ambient.drop(columns=["日付"])

    # 既存のCSVがあれば読み込んで追記・重複排除
    csv_path = "./data/ambient.csv"
    try:
        df_existing = pd.read_csv(csv_path, encoding="shift-jis", index_col=0)
        # インデックスをリセットして結合
        df_all = pd.concat([df_existing.reset_index(), df_ambient.reset_index()], ignore_index=True)
        # 重複排除（時間が重複する場合は後のデータを優先）
        df_all = df_all.drop_duplicates(subset=["時間"], keep="last")
        df_all = df_all.set_index("時間")
    except FileNotFoundError:
        df_all = df_ambient

    df_all.to_csv(csv_path, index=True, encoding="shift-jis")


def weatherupdate_data(wea_path):
    # Session Stateからウェザーデータ保存先を取得
    df_weather = pd.read_csv(wea_path, delim_whitespace=True, header=1)

    # 最終行を取得して特定の列を選択（列番号で指定）
    weather_last_row = df_weather.tail(1)
    selected_columns = weather_last_row.iloc[:, [1, 2, 5, 7, 8, 15]]

    # 新しい列名を設定
    selected_columns.columns = ["時間", "気温", "湿度", "風速", "風向", "気圧"]
    # リストに変換してセッションステートに追加


    # weather_table_placeholderに渡すデータをDataFrameに変換
    weather_data_df = pd.DataFrame(
        columns=["時間", "気温", "湿度", "風速", "風向", "気圧"]  # 列名を明示的に指定
    )
    # 時間をインデックスに設定
    weather_data_df = weather_data_df.set_index("時間")


    # 最終行を取得して特定の列を選択
    temp = weather_last_row.iloc[0, 2]        # 気温
    wind_speed = weather_last_row.iloc[0, 7]  # 風速
    wind_dir = weather_last_row.iloc[0, 8]    # 風向


    # DataFrameを渡してテーブルを更新
    # weather_table_placeholder.dataframe(weather_data_df, height=300)

