import sqlite3
import json


class VolcanDB:
    def __init__(self, nomDB):
        self.__conn = sqlite3.connect(nomDB)

    def __del__(self):
        self.__conn.close()

    def get_number_of_volcanos(self):
        try:
            self.__cursor = self.__conn.cursor()
            self.__cursor.execute("SELECT COUNT(*) FROM volcans")
            return (
                "There are "
                + str(self.__cursor.fetchone()[0])
                + " volcanos in the database."
            )
        except Exception as err:
            print(err)
            return None

    def get_list_of_volcanos(self):
        try:
            self.__cursor = self.__conn.cursor()
            self.__cursor.execute("SELECT name,lat,lon FROM volcans")
            volcanos = self.__cursor.fetchall()
            res = {}
            i = 1
            for volcano in volcanos:
                res[str(i)] = {"name": volcano[0], "lat": volcano[1], "lon": volcano[2]}
                i += 1
            return json.dumps(res)
        except Exception as err:
            print(err)
            return None

    def get_localisation_by_name(self, name):
        try:
            self.__cursor = self.__conn.cursor()
            self.__cursor.execute("SELECT lat,lon FROM volcans WHERE name=?", (name,))
            lat, lon = self.__cursor.fetchone()
            return name + " is located at lat=" + str(lat) + ", lon=" + str(lon)
        except Exception as err:
            print(err)
            return None

    def get_volcanos_erupted_after(self, year):
        try:
            self.__cursor = self.__conn.cursor()
            self.__cursor.execute(
                "SELECT name FROM volcans WHERE eruption_year>=?", (year,)
            )
            volcanos = self.__cursor.fetchall()
            return (
                "Volcanos erupted after "
                + str(year)
                + " : "
                + str([k[0] for k in volcanos])
            )
        except Exception as err:
            print(err)
            return None

    def get_infos_of_volcano(self, name):
        try:
            self.__cursor = self.__conn.cursor()
            self.__cursor.execute("SELECT * FROM volcans WHERE name=?", (name,))
            infos = self.__cursor.fetchone()
            columns = [
                "volcano",
                "name",
                "wiki",
                "elevation",
                "lat",
                "lon",
                "eruption_date",
                "eruption_year",
                "abstract",
                "photo",
            ]
            res = ""
            for i in range(len(columns)):
                res += f"{columns[i]}: {infos[i]}\n"
            return res
        except Exception as err:
            print(err)
            return None


if __name__ == "__main__":
    db = VolcanDB("volcans/volcans.db")
    print(db.get_number_of_volcanos())
    print(db.get_localisation_by_name("Maipo"))
    print(db.get_volcanos_erupted_after(1922))
    print(db.get_list_of_volcanos())
    print(db.get_infos_of_volcano("Acamarachi"))
