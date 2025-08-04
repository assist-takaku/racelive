""" ---------------------------------------------------------------------------------------------------------
    Super Formula Race Live   Ver : 1.2  2025.05

    データの保存や読み込みなど、複数のファイルで共通して使う関数を記述するコードです。
    
    1. 設定ファイルのJSONファイルの読み込みや買い込みを行います。
    2. racelive.jpのサービスから取得したデータの一時保存や読み書き。
    3. ウェザーデータの取得したデータの一時保存や読み書き。

----------------------------------------------------------------------------------------------------------"""
import os
import json
import pandas as pd


# -------------------------- 設定用Jsonファイルの読み込み ------------------------------------------------------------
class Datalist:
    def __init__(self, cat):
        self.category_index = cat
        self.sf_setfile = json.load(open("./data/racelive.json", "r", encoding="utf-8"))
        self.list_team = self.sf_setfile["Category"][self.category_index]["Team"]
        self.list_cat = self.sf_setfile["Category"][self.category_index]["Name"]

        # データベース用リストを作成
        self.team_data = []
        for team in self.list_team:
            for car in team["Car"]:
                if car[0]:  # カーナンバーが存在する場合のみ追加
                    self.team_data.append({
                        "Team Name": team["Name"],
                        "Maker": team["Maker"],
                        "Car No": car[0],
                        "Driver Name1": car[1],
                        "Driver Name2": car[2],
                        "Driver Name3": car[3],
                        "Driver URL": car[4]
                    })
        # ドライバーリストを作成
        self.df_team = pd.DataFrame(self.team_data)
        self.car_no_list = self.df_team["Car No"].tolist()          # Car No 列をリストに変換
        self.name1_list = self.df_team["Driver Name1"].tolist()     # Driver Name1 列をリストに変換
        self.name3_list = self.df_team["Driver Name3"].tolist()     # Driver Name3 列をリストに変換
        self.maker_list = self.df_team["Maker"].tolist()            # Maker 列をリストに変換


    # -------------------------- 参加チーム・インフォメーション・リスト作成関数 -------------------------------------------
    def teamlist(self):

        mk = self.maker_list
        teamlist = pd.DataFrame(self.team_data)
        mk2 = list(set(mk))  # 重複を削除したメーカーリストを作成

        return teamlist, mk, mk2


    # -------------------------- 参加チーム・ドライバー ・リスト作成関数 ------------------------------------------------
    def driverlist(self):

        no_list = self.car_no_list
        driver_list = []
        for i in self.name3_list:
            s = self.car_no_list[self.name3_list.index(i)]
            cno = s
            dn = i
            if len(str(cno)) == 1:
                d_name = "#  " + str(cno) + " " + dn
            else:
                d_name = "# " + str(cno) + " " + dn
            driver_list.append(d_name)
        driver_list = driver_list

        return driver_list, no_list


    # -------------------------- ライブデータ用データベースファイル作成 --------------------------------------------------
    def data_db(self, racelap, sess):

        self.racelap = racelap
        self.sess = sess

        # 参加ドライバーリストの空のデータベースを作成
        d_id = []
        for i in (self.car_no_list):
            for s in range(0, int(self.racelap) + 1):
                c_id = str(i) + str("_") + str(s)
                d_id.append(c_id)

        category = []
        for n in (self.car_no_list):
            for s in range(0, int(self.racelap) + 1):
                category.append(self.list_cat)

        ses_name = []
        for n in (self.car_no_list):
            for s in range(0, int(self.racelap) + 1):
                ses_name.append(self.sess)

        c_no = []
        for i in (self.car_no_list):
            for s in range(0, int(self.racelap) + 1):
                cno = i
                c_no.append(cno)

        dr1 = []
        for i, driver in zip(self.car_no_list, self.name3_list):
            for _ in range(0, int(self.racelap) + 1):
                if len(str(i)) == 1:
                    d_name = f"#  {i} {driver}"
                else:
                    d_name = f"# {i} {driver}"
                dr1.append(d_name)

        dr2 = []
        for driver in self.name1_list:
            for _ in range(0, int(self.racelap) + 1):
                dr2.append(driver)

        mk = []
        for maker in self.maker_list:
            for _ in range(0, int(self.racelap) + 1):
                mk.append(maker)

        lap = []
        for n in (self.car_no_list):
            for s in range(0, int(self.racelap) + 1):
                lap.append(s)

        df_list = {"ID": d_id, "Category": category, "Session": ses_name, "CarNo": c_no, "Driver": dr1, "Driver Name": dr2, "Maker": mk, "Lap": lap}
        df0 = pd.DataFrame.from_dict(df_list)

        df0["Pos"] = ""
        df0["Sec 1"] = pd.Series(dtype='float64')
        df0["Sec 2"] = pd.Series(dtype='float64')
        df0["Sec 3"] = pd.Series(dtype='float64')
        df0["Sec 4"] = pd.Series(dtype='float64')
        df0["Speed"] = None
        df0["LapTime (min)"] = None
        df0["LapTime"] = None
        df0["Gap"] = None
        df0["Diff"] = None
        df0["E Time"] = ""
        df0["Tyre"] = ""
        df0["Pit"] = ""
        df0["Pit In No"] = ""
        df0["Track Condition"] = ""
        df0["Weather"] = ""
        df0["Flag"] = ""
        df0["Remaining Time"] = ""
        df0["Sampling Time"] = ""
        df0["Ambient Time"] = ""
        df0["Ambient Temp"] = ""
        df0["Ambient K Type"] = ""
        df0["Ambient Track"] = ""
        df0["Ambient Humidity"] = ""
        df0["Ambient Pressure"] = ""
        df0["Weather Time"] = ""
        df0["Weather Temp"] = ""
        df0["Weather Humidity"] = ""
        df0["Weather WindSpeed"] = ""
        df0["Weather WindDirection"] = ""
        df0["Weather Air Pressure"] = ""

        return df0
