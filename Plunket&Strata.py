import sys
import subprocess
import importlib.util
import webbrowser
import time
import os
import socket
import platform
from datetime import datetime

def install_and_import(package, import_name=None):
    """Install package if not available and import it"""
    if import_name is None:
        import_name = package
    
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
        print(f"{package} installed successfully!")
    return importlib.import_module(import_name)

print("Checking dependencies...")
install_and_import("requests")
install_and_import("PyQt5")
psutil = install_and_import("psutil")
print("All dependencies ready!\n")

import random
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                              QLineEdit, QTextBrowser, QHBoxLayout, QPushButton)
from PyQt5.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal
from PyQt5.QtGui import QFont

class OpenAIThread(QThread):
    """Thread for handling OpenAI API calls"""
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_key, message, conversation_history):
        super().__init__()
        self.api_key = api_key
        self.message = message
        self.conversation_history = conversation_history
        
    def run(self):
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = self.conversation_history + [
                {"role": "user", "content": self.message}
            ]
            
            data = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                reply = result['choices'][0]['message']['content']
                self.response_ready.emit(reply)
            else:
                self.error_occurred.emit(f"API Error: {response.status_code}")
                
        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")

class StrataThread(QThread):
    """Thread for running Strata diagnostics"""
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def __init__(self, diag_type):
        super().__init__()
        self.diag_type = diag_type
        
    def run(self):
        self.update_signal.emit(f"<b>Running {self.diag_type.replace('_', ' ').title()} Diagnostics...</b>")
        findings = self.run_diagnostics()
        
        for finding in findings:
            self.update_signal.emit(f"- {finding}")
            time.sleep(0.3)
        
        self.finished_signal.emit()
    
    def run_diagnostics(self):
        if self.diag_type == "network":
            return self.net_diag()
        elif self.diag_type == "performance":
            return self.perf_diag()
        elif self.diag_type == "hardware":
            return self.hw_diag()
        elif self.diag_type == "security":
            return self.sec_diag()
        elif self.diag_type == "full":
            return self.net_diag() + self.perf_diag() + self.hw_diag() + self.sec_diag()
        return ["No diagnostics available."]
    
    def net_diag(self):
        fnd = []
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            fnd.append("Internet: Active")
        except OSError:
            fnd.append("Internet: No access")
        
        try:
            r = subprocess.run(["ping", "-c" if platform.system() != "Windows" else "-n", "4", "8.8.8.8"], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            fnd.append("Ping: Successful" if r.returncode == 0 else "Ping: Failed")
        except:
            fnd.append("Ping: Unable to test")
        
        try:
            socket.gethostbyname("www.google.com")
            fnd.append("DNS: Successful")
        except socket.gaierror:
            fnd.append("DNS: Failed")
        
        return fnd
    
    def perf_diag(self):
        return [
            f"CPU: {psutil.cpu_percent(interval=1)}% usage",
            f"Memory: {psutil.virtual_memory().percent}% usage"
        ]
    
    def hw_diag(self):
        b = psutil.sensors_battery()
        return [
            f"Battery: {b.percent}% remaining" if b else "Battery: Not available",
            f"Disk: {psutil.disk_usage('/').percent}% used"
        ]
    
    def sec_diag(self):
        fnd = []
        if platform.system().lower() == 'windows':
            try:
                r = subprocess.run(["netsh", "advfirewall", "show", "allprofiles"], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
                fnd.append("Firewall: Active" if b"State ON" in r.stdout else "Firewall: Inactive")
            except:
                fnd.append("Firewall: Unable to check")
        else:
            fnd.append("Firewall: Check not available on this OS")
        
        av = [p.info['name'] for p in psutil.process_iter(['name']) 
              if any(a in p.info['name'].lower() for a in ['avast', 'avg', 'defender', 'norton', 'mcafee'])]
        fnd.append(f"Antivirus: {', '.join(av)} running" if av else "Antivirus: None detected")
        
        return fnd

class Plunket(QWidget):
    def __init__(self):
        super().__init__()
        
        self.api_key = "YOUR_OPENAI_API_KEY_HERE"
        
        self.mood = 'neutral'
        self.moods = {
            'neutral': {'face': '(◕‿◕)', 'msg': ""},
            'happy': {'face': '(◕‿◕)', 'msg': ""},
            'excited': {'face': '(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧', 'msg': ""},
            'sleepy': {'face': '(－ω－)', 'msg': ""},
            'sad': {'face': '(╥﹏╥)', 'msg': ""},
            'surprised': {'face': '(⊙_⊙)', 'msg': ""},
            'thinking': {'face': '(¬‿¬)', 'msg': ""}
        }
        
        self.conversation_history = [
            {"role": "system", "content": "You are Plunket, a helpful desktop companion. Keep responses concise and natural."}
        ]
        
        self.dark_mode = False
        self.dragging = False
        self.offset = QPoint()
        self.chat_thread = None
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Plunket')
        self.setFixedSize(600, 650)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.container = QWidget()
        self.container.setStyleSheet("""
            background-color: rgb(250, 250, 250);
            border-radius: 10px;
            border: 1px solid rgb(200, 200, 200);
        """)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(12)
        
        top_bar = QHBoxLayout()
        
        title_label = QLabel('Plunket')
        title_label.setFont(QFont('Arial', 11))
        title_label.setStyleSheet("background-color: transparent; color: #666;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        self.theme_btn = QPushButton('🌙')
        self.theme_btn.setFont(QFont('Arial', 14))
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
        """)
        self.theme_btn.setFixedSize(32, 24)
        self.theme_btn.clicked.connect(self.toggle_dark_mode)
        top_bar.addWidget(self.theme_btn)
        
        close_btn = QPushButton('×')
        close_btn.setFont(QFont('Arial', 16, QFont.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                color: #333;
            }
        """)
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)
        
        container_layout.addLayout(top_bar)
        
        self.face_label = QLabel(self.moods[self.mood]['face'])
        self.face_label.setFont(QFont('Courier New', 48))
        self.face_label.setAlignment(Qt.AlignCenter)
        self.face_label.setStyleSheet("background-color: transparent; color: #333;")
        self.face_label.setMinimumHeight(80)
        container_layout.addWidget(self.face_label)
        
        self.chat_history = QTextBrowser()
        self.chat_history.setOpenExternalLinks(True)
        self.chat_history.setFont(QFont('Arial', 11))
        self.chat_history.setStyleSheet("""
            QTextBrowser {
                background-color: rgb(245, 245, 245);
                color: #2a2a2a;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #ccc;
                border-radius: 4px;
            }
        """)
        self.chat_history.setMinimumHeight(350)
        self.chat_history.setLineWrapMode(QTextBrowser.WidgetWidth)
        self.chat_history.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        container_layout.addWidget(self.chat_history)
        
        if self.api_key == "YOUR_OPENAI_API_KEY_HERE":
            self.add_message("System", "To use Plunket, you need an OpenAI API key.")
            self.add_message("System", '<a href="https://platform.openai.com/api-keys" style="color: #4285f4;">Click here to get your OpenAI API Key</a>')
            self.add_message("System", "Once you have your key, paste it in the chat below to activate Plunket.")
        else:
            self.add_message("Plunket", "Hello! I'm Plunket. How can I help?")
        
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type here...")
        self.input_field.setFont(QFont('Arial', 11))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgb(255, 255, 255);
                color: #2a2a2a;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px;
            }
            QLineEdit:focus {
                border: 1px solid #999;
            }
        """)
        self.input_field.setMinimumHeight(40)
        self.input_field.returnPressed.connect(self.handle_input)
        input_layout.addWidget(self.input_field)
        
        container_layout.addLayout(input_layout)
        
        self.container.setLayout(container_layout)
        main_layout.addWidget(self.container)
        self.setLayout(main_layout)
        
    def update_theme(self):
        if self.dark_mode:
            self.container.setStyleSheet("""
                background-color: rgb(35, 35, 38);
                border-radius: 10px;
                border: 1px solid rgb(60, 60, 63);
            """)
            
            self.face_label.setStyleSheet("background-color: transparent; color: #ddd;")
            
            self.chat_history.setStyleSheet("""
                QTextBrowser {
                    background-color: rgb(45, 45, 48);
                    color: #e0e0e0;
                    border: 1px solid #555;
                    border-radius: 6px;
                    padding: 10px;
                }
                QScrollBar:vertical {
                    background: transparent;
                    width: 8px;
                }
                QScrollBar::handle:vertical {
                    background: #666;
                    border-radius: 4px;
                }
            """)
            
            self.input_field.setStyleSheet("""
                QLineEdit {
                    background-color: rgb(45, 45, 48);
                    color: #e0e0e0;
                    border: 1px solid #555;
                    border-radius: 6px;
                    padding: 10px;
                }
                QLineEdit:focus {
                    border: 1px solid #777;
                }
            """)
            
            self.theme_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #aaa;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                }
            """)
        else:
            self.container.setStyleSheet("""
                background-color: rgb(250, 250, 250);
                border-radius: 10px;
                border: 1px solid rgb(200, 200, 200);
            """)
            
            self.face_label.setStyleSheet("background-color: transparent; color: #333;")
            
            self.chat_history.setStyleSheet("""
                QTextBrowser {
                    background-color: rgb(245, 245, 245);
                    color: #2a2a2a;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 10px;
                }
                QScrollBar:vertical {
                    background: transparent;
                    width: 8px;
                }
                QScrollBar::handle:vertical {
                    background: #ccc;
                    border-radius: 4px;
                }
            """)
            
            self.input_field.setStyleSheet("""
                QLineEdit {
                    background-color: rgb(255, 255, 255);
                    color: #2a2a2a;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 10px;
                }
                QLineEdit:focus {
                    border: 1px solid #999;
                }
            """)
            
            self.theme_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #666;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                }
            """)
    
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.theme_btn.setText('☀️' if self.dark_mode else '🌙')
        self.update_theme()
        
    def add_message(self, sender, message):
        if sender == "You":
            formatted = f'<p style="margin: 8px 0;"><span style="color: #666; font-weight: 500;">{sender}:</span> {message}</p>'
        elif sender == "System":
            formatted = f'<p style="margin: 8px 0; color: #999; font-size: 10px;">{message}</p>'
        else:
            formatted = f'<p style="margin: 8px 0;"><span style="color: #666; font-weight: 500;">{sender}:</span> {message}</p>'
        
        self.chat_history.append(formatted)
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )
        
    def handle_input(self):
        text = self.input_field.text().strip()
        if not text:
            return
        
        if text == "/commands":
            self.add_message("System", "<b>Available Commands:</b>")
            self.add_message("System", "/commands - Show this list")
            self.add_message("System", "/clear - Clear chat history")
            self.add_message("System", "/mood [name] - Change mood (happy, excited, sleepy, sad, surprised, thinking)")
            self.add_message("System", "/reset - Reset API key")
            self.add_message("System", "/strata - System diagnostics menu")
            self.input_field.clear()
            return
        
        if text == "/strata":
            self.show_strata_menu()
            self.input_field.clear()
            return
        
        if text == "/clear":
            self.chat_history.clear()
            self.conversation_history = [
                {"role": "system", "content": "You are Plunket, a helpful desktop companion. Keep responses concise and natural."}
            ]
            self.add_message("System", "Chat history cleared.")
            self.input_field.clear()
            return
        
        if text.startswith("/mood "):
            mood_name = text.split(" ", 1)[1].strip()
            if mood_name in self.moods:
                self.change_mood(mood_name)
                self.add_message("System", f"Mood changed to {mood_name}.")
            else:
                self.add_message("System", f"Unknown mood. Available: {', '.join(self.moods.keys())}")
            self.input_field.clear()
            return
        
        if text == "/reset":
            self.api_key = "YOUR_OPENAI_API_KEY_HERE"
            self.chat_history.clear()
            self.conversation_history = [
                {"role": "system", "content": "You are Plunket, a helpful desktop companion. Keep responses concise and natural."}
            ]
            self.add_message("System", "API key reset. Please enter a new API key to continue.")
            self.input_field.clear()
            return
        
        if text.startswith("/strata "):
            diag_type = text.split(" ", 1)[1].strip()
            valid_types = ["network", "performance", "hardware", "security", "full"]
            if diag_type in valid_types:
                self.run_strata_diagnostic(diag_type)
            else:
                self.add_message("System", f"Unknown diagnostic type. Use: {', '.join(valid_types)}")
            self.input_field.clear()
            return
        
        if self.api_key == "YOUR_OPENAI_API_KEY_HERE":
            if text.startswith("sk-"):
                self.api_key = text
                self.add_message("System", "API key saved! You can now chat with Plunket.")
                self.input_field.clear()
                return
            else:
                self.add_message("System", "Please enter your OpenAI API key (it should start with 'sk-')")
                self.input_field.clear()
                return
            
        self.add_message("You", text)
        self.input_field.clear()
        self.input_field.setEnabled(False)
        
        self.change_mood('thinking')
        self.add_message("Plunket", "...")
        
        self.chat_thread = OpenAIThread(self.api_key, text, self.conversation_history)
        self.chat_thread.response_ready.connect(self.handle_response)
        self.chat_thread.error_occurred.connect(self.handle_error)
        self.chat_thread.start()
        
    def handle_response(self, response):
        html = self.chat_history.toHtml()
        lines = html.split('<p')
        if len(lines) > 1:
            html = '<p'.join(lines[:-1])
        self.chat_history.setHtml(html)
        
        self.add_message("Plunket", response)
        
        user_message = self.chat_thread.message
        
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        if len(self.conversation_history) > 11:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-10:]
        
        self.change_mood('neutral')
        
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        
    def handle_error(self, error_msg):
        html = self.chat_history.toHtml()
        lines = html.split('<p')
        if len(lines) > 1:
            html = '<p'.join(lines[:-1])
        self.chat_history.setHtml(html)
        
        self.add_message("System", error_msg)
        self.change_mood('neutral')
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        
    def change_mood(self, new_mood):
        if new_mood in self.moods:
            self.mood = new_mood
            self.face_label.setText(self.moods[new_mood]['face'])
    
    def show_strata_menu(self):
        self.add_message("System", "<b>Strata System Diagnostics</b>")
        self.add_message("System", "Type one of the following:")
        self.add_message("System", "/strata network - Network diagnostics")
        self.add_message("System", "/strata performance - Performance check")
        self.add_message("System", "/strata hardware - Hardware status")
        self.add_message("System", "/strata security - Security scan")
        self.add_message("System", "/strata full - Full system check")
        self.strata_mode = True
    
    def run_strata_diagnostic(self, diag_type):
        self.change_mood('thinking')
        self.input_field.setEnabled(False)
        
        self.strata_thread = StrataThread(diag_type)
        self.strata_thread.update_signal.connect(self.add_strata_update)
        self.strata_thread.finished_signal.connect(self.strata_finished)
        self.strata_thread.start()
    
    def add_strata_update(self, message):
        self.add_message("Strata", message)
    
    def strata_finished(self):
        self.change_mood('happy')
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        self.add_message("Strata", "<b>Diagnostic complete!</b>")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.pos() + event.pos() - self.offset)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

def main():
    app = QApplication(sys.argv)
    plunket = Plunket()
    plunket.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
