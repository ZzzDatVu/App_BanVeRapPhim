import customtkinter as ctk
from services.auth_service import authenticate


def safe_destroy(window) -> None:
    try:
        for after_id in window.tk.eval("after info").split():
            try:
                window.after_cancel(after_id)
            except Exception:
                pass
    except Exception:
        pass
    window.destroy()


class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.title("Cinema Booking App - Login")
        self.geometry("420x320")
        self.on_login_success = on_login_success

        ctk.CTkLabel(
            self,
            text="CINEMA SYSTEM LOGIN",
            font=("Arial", 20, "bold"),
        ).pack(pady=(28, 14))

        self.entry_username = ctk.CTkEntry(
            self,
            placeholder_text="Username (admin / staff01)",
            width=270,
            height=36,
        )
        self.entry_username.pack(pady=6)

        self.entry_password = ctk.CTkEntry(
            self,
            placeholder_text="Password",
            show="*",
            width=270,
            height=36,
        )
        self.entry_password.pack(pady=6)
        self.entry_password.bind("<Return>", lambda _event: self.handle_login())

        self.lbl_error = ctk.CTkLabel(
            self,
            text="",
            text_color="#ef4444",
            font=("Arial", 12),
        )
        self.lbl_error.pack(pady=4)

        self.btn_login = ctk.CTkButton(
            self,
            text="Login",
            width=270,
            height=38,
            font=("Arial", 13, "bold"),
            command=self.handle_login,
        )
        self.btn_login.pack(pady=6)

        ctk.CTkLabel(
            self,
            text="Default: admin / 123  |  staff01 / 123",
            text_color="gray",
            font=("Arial", 12),
        ).pack(pady=(10, 0))

    def handle_login(self) -> None:
        user = authenticate(self.entry_username.get(), self.entry_password.get())
        if not user:
            self.lbl_error.configure(text="Invalid username or password!")
            return

        self.lbl_error.configure(text="")
        callback = self.on_login_success
        safe_destroy(self)
        callback(user)