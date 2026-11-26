import customtkinter as ctk


def fmt_vnd(amount):
    return f"{int(amount):,}đ".replace(",", ".")


class StatsView(ctk.CTkToplevel):
    def __init__(self, parent, ds_suat, ds_hoa_don):
        super().__init__(parent)
        self.ds_suat = ds_suat
        self.ds_hoa_don = ds_hoa_don

        self.title("Thống kê bán vé & Đề xuất suất chiếu")
        self.geometry("700x540")
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="BẢNG THỐNG KÊ QUẦY THU NGÂN",
            font=("Arial", 20, "bold"),
        ).pack(pady=(16, 6))

        ctk.CTkLabel(
            self,
            text="Tổng hợp ghế đã bán, doanh thu & gợi ý phim nên tăng suất chiếu",
            font=("Arial", 13),
            text_color="#94a3b8",
        ).pack(pady=(0, 12))

        total_tickets_booked = sum(len(s.ds_ghe_dadat) for s in ds_suat)
        total_capacity = sum(s.phong.so_hang * s.phong.so_cot for s in ds_suat)
        total_revenue = sum(int(hd.get("tong_tien", 0)) for hd in ds_hoa_don)
        total_orders = len(ds_hoa_don)

        summary_card = ctk.CTkFrame(self)
        summary_card.pack(fill="x", padx=24, pady=(0, 12))

        summary_text = (
            f"Tổng hóa đơn: {total_orders}   |   "
            f"Ghế đã đặt: {total_tickets_booked}/{total_capacity}   |   "
            f"Tổng doanh thu: {fmt_vnd(total_revenue)}"
        )
        ctk.CTkLabel(
            summary_card,
            text=summary_text,
            font=("Arial", 14, "bold"),
            text_color="#22c55e",
        ).pack(padx=14, pady=12)

        scroll = ctk.CTkScrollableFrame(self, width=640, height=300)
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 10))

        movie_stats = self._aggregate_by_movie()

        if not movie_stats:
            ctk.CTkLabel(
                scroll,
                text="Chưa có dữ liệu suất chiếu để thống kê.",
                font=("Arial", 14),
            ).pack(pady=30)
        else:
            for idx, item in enumerate(movie_stats, start=1):
                row = ctk.CTkFrame(scroll)
                row.pack(fill="x", padx=6, pady=6)

                left = ctk.CTkFrame(row, fg_color="transparent")
                left.pack(side="left", fill="x", expand=True, padx=12, pady=10)

                title_line = f"#{idx}  {item['ten_phim']}  ({item['so_suat']} suất)"
                detail_line = (
                    f"Ghế bán: {item['ghe_ban']}/{item['tong_ghe']} ({item['ty_le']:.0f}%)  •  "
                    f"Doanh thu: {fmt_vnd(item['doanh_thu'])}"
                )

                ctk.CTkLabel(
                    left,
                    text=title_line,
                    font=("Arial", 15, "bold"),
                    anchor="w",
                ).pack(fill="x")

                ctk.CTkLabel(
                    left,
                    text=detail_line,
                    font=("Arial", 13),
                    text_color="#cbd5e1",
                    anchor="w",
                ).pack(fill="x", pady=(2, 0))

                if item["ty_le"] >= 70:
                    badge_text = "NÊN TĂNG SUẤT"
                    badge_color = "#16a34a"
                elif item["ty_le"] >= 40:
                    badge_text = "BÁN ỔN ĐỊNH"
                    badge_color = "#d97706"
                else:
                    badge_text = "CÂN NHẮC GIỮ/GIẢM"
                    badge_color = "#475569"

                ctk.CTkLabel(
                    row,
                    text=badge_text,
                    font=("Arial", 11, "bold"),
                    fg_color=badge_color,
                    corner_radius=6,
                    padx=10,
                    pady=6,
                ).pack(side="right", padx=12)

        ctk.CTkButton(
            self,
            text="← Trở về quầy bán vé",
            width=185,
            height=36,
            font=("Arial", 13, "bold"),
            fg_color="#475569",
            hover_color="#334155",
            command=self.close_view,
        ).pack(pady=(0, 14))

    def close_view(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _aggregate_by_movie(self):
        stats = {}

        for suat in self.ds_suat:
            ten_phim = suat.phim.ten_phim
            if ten_phim not in stats:
                stats[ten_phim] = {
                    "ten_phim": ten_phim,
                    "so_suat": 0,
                    "ghe_ban": 0,
                    "tong_ghe": 0,
                    "doanh_thu": 0,
                }
            stats[ten_phim]["so_suat"] += 1
            stats[ten_phim]["ghe_ban"] += len(suat.ds_ghe_dadat)
            stats[ten_phim]["tong_ghe"] += suat.phong.so_hang * suat.phong.so_cot

        invoice_rev_by_movie = {}
        for hd in self.ds_hoa_don:
            m_name = hd.get("ten_phim")
            if m_name:
                invoice_rev_by_movie[m_name] = invoice_rev_by_movie.get(m_name, 0) + int(
                    hd.get("tong_tien", 0)
                )

        for ten_phim, data in stats.items():
            if ten_phim in invoice_rev_by_movie:
                data["doanh_thu"] = invoice_rev_by_movie[ten_phim]
            else:
                data["doanh_thu"] = data["ghe_ban"] * 75000

            data["ty_le"] = (
                (data["ghe_ban"] / data["tong_ghe"] * 100) if data["tong_ghe"] > 0 else 0.0
            )

        return sorted(
            stats.values(),
            key=lambda x: (x["ty_le"], x["ghe_ban"], x["doanh_thu"]),
            reverse=True,
        )