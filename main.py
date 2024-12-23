import sys
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QLineEdit, QPushButton, QWidget, QToolBar, QTabWidget, QDialog, QVBoxLayout, QLabel, QListWidget, QHBoxLayout, QMessageBox, QMenu, QAction, QFormLayout, QInputDialog, QFileDialog)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon
import os

class DownloadManager(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Download Manager")
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout()
        self.download_list = QListWidget()
        self.layout.addWidget(self.download_list)

        self.setLayout(self.layout)
        self.downloads = []

    def add_download(self, download_item):
        item_label = QLabel(f"Downloading: {download_item.url().fileName()}")
        self.downloads.append((item_label, download_item))
        self.download_list.addItem(f"Downloading: {download_item.url().fileName()}")

    def download_completed(self, download_item):
        for i, (label, item) in enumerate(self.downloads):
            if item == download_item:
                self.download_list.takeItem(i)
                self.download_list.addItem(f"Completed: {download_item.url().fileName()}")
                self.downloads.pop(i)
                break

class BookmarksManager(QDialog):
    def __init__(self, bookmarks, browser):
        super().__init__()
        self.setWindowTitle("Bookmarks Manager")
        self.setGeometry(150, 150, 400, 300)

        self.bookmarks = bookmarks
        self.browser = browser

        self.layout = QVBoxLayout()

        self.bookmarks_list = QListWidget()
        self.update_bookmarks_list()
        self.layout.addWidget(self.bookmarks_list)

        buttons_layout = QHBoxLayout()
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_bookmark)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_bookmark)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)

        self.layout.addLayout(buttons_layout)
        self.setLayout(self.layout)

        # Connect double-click signal
        self.bookmarks_list.itemDoubleClicked.connect(self.open_bookmark)

    def update_bookmarks_list(self):
        self.bookmarks_list.clear()
        for name, url in self.bookmarks:
            self.bookmarks_list.addItem(f"{name}: {url}")

    def edit_bookmark(self):
        current_item = self.bookmarks_list.currentItem()
        if current_item:
            index = self.bookmarks_list.currentRow()
            name, url = self.bookmarks[index]

            new_name, ok_name = QInputDialog.getText(self, "Edit Bookmark Name", "Name:", text=name)
            if not ok_name:
                return

            new_url, ok_url = QInputDialog.getText(self, "Edit Bookmark URL", "URL:", text=url)
            if not ok_url:
                return

            self.bookmarks[index] = (new_name, new_url)
            self.update_bookmarks_list()

    def delete_bookmark(self):
        current_item = self.bookmarks_list.currentItem()
        if current_item:
            index = self.bookmarks_list.currentRow()
            del self.bookmarks[index]
            self.update_bookmarks_list()

    def open_bookmark(self):
        current_item = self.bookmarks_list.currentItem()
        if current_item:
            index = self.bookmarks_list.currentRow()
            _, url = self.bookmarks[index]
            self.browser.navigate_to_url(url)  # Pass the URL directly to the method
            self.accept()  # Close the dialog after opening the bookmark

class BrowserTab(QWidget):
    def __init__(self, download_manager):
        super().__init__()
        self.download_manager = download_manager
        layout = QVBoxLayout()
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.duckduckgo.com"))
        self.browser.page().profile().downloadRequested.connect(self.handle_download)
        layout.addWidget(self.browser)
        self.setLayout(layout)

    def close(self):
        self.browser.setParent(None)
        self.browser.deleteLater()  # Ensure the browser is deleted
        self.deleteLater()

    def handle_download(self, download_item):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", download_item.url().fileName())
        if file_path:
            download_item.setPath(file_path)
            self.download_manager.add_download(download_item)
            download_item.finished.connect(lambda: self.download_manager.download_completed(download_item))
            download_item.accept()

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Web Browser")

        self.download_manager = DownloadManager()
        self.bookmarks = []

        # Tab widget for managing tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_tab_controls)
        self.setCentralWidget(self.tabs)

        # Navigation bar
        self.navbar = QToolBar()
        self.addToolBar(self.navbar)

        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.navigate_back)
        self.back_btn.setEnabled(False)
        self.navbar.addWidget(self.back_btn)

        self.forward_btn = QPushButton("Forward")
        self.forward_btn.clicked.connect(self.navigate_forward)
        self.forward_btn.setEnabled(False)
        self.navbar.addWidget(self.forward_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_page)
        self.navbar.addWidget(refresh_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self.stop_loading)
        self.navbar.addWidget(stop_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.navbar.addWidget(self.url_bar)

        new_tab_btn = QPushButton("+")
        new_tab_btn.clicked.connect(self.add_new_tab)
        self.navbar.addWidget(new_tab_btn)

        downloads_btn = QPushButton("Downloads")
        downloads_btn.clicked.connect(self.show_download_manager)
        self.navbar.addWidget(downloads_btn)

        bookmarks_btn = QPushButton("Bookmarks")
        bookmarks_btn.clicked.connect(self.show_bookmarks_manager)
        self.navbar.addWidget(bookmarks_btn)

        bookmark_btn = QPushButton("+ BM")  # Button to add a bookmark
        bookmark_btn.clicked.connect(self.add_bookmark)
        self.navbar.addWidget(bookmark_btn)

        self.add_new_tab()

    def add_new_tab(self, url=None):
        new_tab = BrowserTab(self.download_manager)
        if url:
            new_tab.browser.setUrl(QUrl(url))
        new_tab.browser.urlChanged.connect(self.update_url_bar)
        new_tab.browser.iconChanged.connect(lambda: self.update_favicon(new_tab))
        new_tab.browser.loadFinished.connect(lambda: self.update_tab_title(new_tab))

        i = self.tabs.addTab(new_tab, "New Tab")
        self.tabs.setCurrentIndex(i)
        self.update_tab_controls()

    def close_tab(self, index):
        if self.tabs.count() > 1:
            tab_to_close = self.tabs.widget(index)
            tab_to_close.browser.setUrl(QUrl("about:blank"))  # Stop any loading or media
            tab_to_close.browser.deleteLater()  # Ensure resources are released
            tab_to_close.close()
            self.tabs.removeTab(index)
        self.update_tab_controls()

    def update_tab_controls(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            self.setWindowTitle(current_tab.browser.title() or "Python Web Browser")
            self.back_btn.setEnabled(current_tab.browser.history().canGoBack())
            self.forward_btn.setEnabled(current_tab.browser.history().canGoForward())
        else:
            self.back_btn.setEnabled(False)
            self.forward_btn.setEnabled(False)

    def update_tab_title(self, tab):
        index = self.tabs.indexOf(tab)
        if index != -1:
            self.tabs.setTabText(index, tab.browser.title() or "New Tab")

    def update_favicon(self, tab):
        icon = tab.browser.icon()
        index = self.tabs.indexOf(tab)
        if index != -1:
            self.tabs.setTabIcon(index, icon)

    def navigate_to_url(self):
        url = self.url_bar.text()
    
        # Check if the URL contains a TLD (like .com, .org, etc.)
        if re.match(r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', url):
            # If it's a valid domain without the protocol, add 'https://' automatically
            if not re.match(r'https?://', url):
                url = 'https://' + url
            current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.browser.setUrl(QUrl(url))
        else:
            # If it's a search term or doesn't have a TLD, search DuckDuckGo
            search_url = f"https://www.duckduckgo.com/?q={url}"
            current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.browser.setUrl(QUrl(search_url))
        
        self.update_tab_controls()  # Ensure buttons are updated after navigation

    def update_url_bar(self, qurl):
        current_tab = self.tabs.currentWidget()
        if current_tab and current_tab.browser.url() == qurl:
            self.url_bar.setText(qurl.toString())

    def navigate_back(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.browser.back()
        self.update_tab_controls()  # Update the back/forward buttons

    def navigate_forward(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.browser.forward()
        self.update_tab_controls()  # Update the back/forward buttons

    def refresh_page(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.browser.reload()

    def stop_loading(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.browser.stop()

    def show_download_manager(self):
        self.download_manager.exec_()

    def show_bookmarks_manager(self):
        manager = BookmarksManager(self.bookmarks, self)
        manager.exec_()

    def add_bookmark(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            name, ok = QInputDialog.getText(self, "Add Bookmark", "Enter bookmark name:")
            if ok:
                url = current_tab.browser.url().toString()
                self.bookmarks.append((name, url))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = Browser()
    browser.show()
    sys.exit(app.exec_())
