import customtkinter as ctk
from downloader import DownloadManager
from ui_controller import UIController
from utilities import MyLogger

class UniversalDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("")
        self.geometry("500x420")
        self.resizable(False, False)
        
        # Initialize UI controller
        self.controller = UIController(self, DownloadManager(), MyLogger())

    def show_popup(self, title, success, error_detail=None):
        self.controller.show_popup(title, success, error_detail)

if __name__ == "__main__":
    app = UniversalDownloader()
    app.mainloop()
