import json
import os
from models import Phim, PhongChieu, SuatChieu

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "data", "database.json")


def luu_du_lieu(ds_suat_chieu, ds_hoa_don=None):
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)

    suat_data = []
    for sc in ds_suat_chieu:
        suat_data.append({
            "ma_suat": sc.ma_suat,
            "ma_phim": sc.phim.ma_phim,
            "ten_phim": sc.phim.ten_phim,
            "thoi_luong": sc.phim.thoi_luong,
            "ma_phong": sc.phong.ma_phong,
            "ten_phong": sc.phong.ten_phong,
            "gio_chieu": sc.gio_chieu,
            "ds_ghe_dadat": sorted(list(sc.ds_ghe_dadat)),
        })

    data = {
        "suat_chieu": suat_data,
        "hoa_don": ds_hoa_don if ds_hoa_don is not None else [],
    }

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def nap_du_lieu():
    if not os.path.exists(FILE_PATH):
        p1 = Phim("P01", "Nhà ba tôi một phòng", "120 phút")
        p2 = Phim("P02", "Thỏ ơi", "127 phút")
        phong1 = PhongChieu("ROOM01", "Phòng 1")

        ds_suat = [
            SuatChieu("SC01", p1, phong1, "09:00"),
            SuatChieu("SC02", p2, phong1, "09:15"),
        ]
        luu_du_lieu(ds_suat, [])
        return ds_suat, []

    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        ds_suat = []
        for item in data.get("suat_chieu", []):
            p = Phim(item["ma_phim"], item["ten_phim"], item["thoi_luong"])
            ph = PhongChieu(item["ma_phong"], item["ten_phong"])
            sc = SuatChieu(item["ma_suat"], p, ph, item["gio_chieu"])
            sc.ds_ghe_dadat = set(item.get("ds_ghe_dadat", []))
            ds_suat.append(sc)

        return ds_suat, data.get("hoa_don", [])
    except Exception as e:
        print("Lỗi đọc database.json:", e)
        return [], []