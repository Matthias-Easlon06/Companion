import sys
import random
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                              QLineEdit, QTextEdit, QHBoxLayout, QPushButton)
from PyQt5.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal
from PyQt5.QtGui import QFont

class ChatGPTThread(QThread):
    """Thread for handling ChatGPT API calls"""
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
            
            # Build messages for API
            messages = self.conversation_history + [
                {"role": "user", "content": self.message}
            ]
            
            data = {
                "model": "gpt-4o-mini",  # Try this cheaper model first
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

class DesktopCompanion(QWidget):
    def __init__(self):
        super().__init__()
        
        # Your OpenAI API key
        self.api_key = "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"
        
        self.mood = 'happy'
        self.moods = {
            'happy': {'face': '(◕‿◕)', 'msg': "I'm feeling happy!"},
            'excited': {'face': '(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧', 'msg': "This is so exciting!"},
            'sleepy': {'face': '(－ω－)', 'msg': "Yawn... sleepy time..."},
            'love': {'face': '(♥‿♥)', 'msg': "Sending you love! 💕"},
            'sad': {'face': '(╥﹏╥)', 'msg': "Feeling a bit down..."},
            'surprised': {'face': '(⊙_⊙)', 'msg': "Oh wow!"},
            'cool': {'face': '(⌐■_■)', 'msg': "Staying cool~"},
            'angry': {'face': '(ಠ_ಠ)', 'msg': "Grr..."},
            'thinking': {'face': '(¬‿¬)', 'msg': "Hmm, let me think..."}
        }
        
        # Conversation history for ChatGPT
        self.conversation_history = [
            {"role": "system", "content": "You are a friendly desktop companion. Keep responses brief and cheerful. When you express different emotions, mention which mood you're in (happy, excited, sleepy, love, sad, surprised, cool, angry) so the UI can update accordingly."}
        ]
        
        # Dark mode toggle
        self.dark_mode = False
        
        # Dragging variables
        self.dragging = False
        self.offset = QPoint()
        
        self.chat_thread = None
        
        self.init_ui()
        
    def init_ui(self):
        # Window settings - Made wider
        self.setWindowTitle('Desktop Companion')
        self.setFixedSize(700, 700)  # Changed from 500 to 700
        
        # Transparent background, stay on top
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create a container for the content
        self.container = QWidget()
        self.container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 230);
            border-radius: 15px;
        """)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # Top bar with close button
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        
        # Close button at top right
        close_btn = QPushButton('✕')
        close_btn.setFont(QFont('Arial', 14, QFont.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        close_btn.setFixedSize(40, 40)
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)
        container_layout.addLayout(top_bar)
        
        # Face label (large ASCII art)
        self.face_label = QLabel(self.moods[self.mood]['face'])
        self.face_label.setFont(QFont('Courier New', 72))
        self.face_label.setAlignment(Qt.AlignCenter)
        self.face_label.setStyleSheet("background-color: transparent; color: black;")
        self.face_label.setMinimumHeight(120)
        container_layout.addWidget(self.face_label)
        
        # Chat history - Fixed to not cut off at bottom
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont('Arial', 12))
        self.chat_history.setStyleSheet("""
            background-color: rgba(245, 245, 245, 200);
            color: #1a1a1a;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
        """)
        self.chat_history.setMinimumHeight(300)
        # Enable word wrap to prevent horizontal cutoff
        self.chat_history.setLineWrapMode(QTextEdit.WidgetWidth)
        # Set vertical scroll bar to always be visible
        self.chat_history.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        container_layout.addWidget(self.chat_history)
        
        # Add initial message
        if self.api_key == "YOUR_OPENAI_API_KEY_HERE":
            self.add_message("System", "Please add your OpenAI API key to use ChatGPT! Edit the code and replace YOUR_OPENAI_API_KEY_HERE with your actual key.")
        else:
            self.add_message("Companion", "Hi! I'm powered by ChatGPT. Chat with me!")
        
        # Input field
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message...")
        self.input_field.setFont(QFont('Arial', 12))
        self.input_field.setStyleSheet("""
            background-color: white;
            color: #1a1a1a;
            border: 1px solid #ddd;
            border-radius: 12px;
            padding: 12px;
        """)
        self.input_field.setMinimumHeight(45)
        self.input_field.returnPressed.connect(self.handle_input)
        input_layout.addWidget(self.input_field)
        
        container_layout.addLayout(input_layout)
        
        # Bottom button row
        bottom_layout = QHBoxLayout()
        
        # Dark mode toggle button
        self.dark_mode_btn = QPushButton('🌙')
        self.dark_mode_btn.setFont(QFont('Arial', 16))
        self.dark_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        self.dark_mode_btn.setFixedSize(40, 40)
        self.dark_mode_btn.clicked.connect(self.toggle_dark_mode)
        bottom_layout.addWidget(self.dark_mode_btn)
        
        bottom_layout.addStretch()
        
        container_layout.addLayout(bottom_layout)
        
        self.container.setLayout(container_layout)
        main_layout.addWidget(self.container)
        self.setLayout(main_layout)
        
    def update_theme(self):
        """Update UI colors based on dark mode setting"""
        if self.dark_mode:
            # Dark mode colors
            self.container.setStyleSheet("""
                background-color: rgba(30, 30, 30, 230);
                border-radius: 15px;
            """)
            
            self.face_label.setStyleSheet("background-color: transparent; color: white;")
            
            self.chat_history.setStyleSheet("""
                background-color: rgba(45, 45, 45, 200);
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 12px;
            """)
            
            self.input_field.setStyleSheet("""
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 2px solid #555;
                border-radius: 8px;
                padding: 8px;
            """)
            
            self.dark_mode_btn.setStyleSheet("""
                QPushButton {
                    background-color: #555;
                    border: none;
                    border-radius: 15px;
                }
                QPushButton:hover {
                    background-color: #666;
                }
            """)
        else:
            # Light mode colors
            self.container.setStyleSheet("""
                background-color: rgba(255, 255, 255, 230);
                border-radius: 15px;
            """)
            
            self.face_label.setStyleSheet("background-color: transparent; color: black;")
            
            self.chat_history.setStyleSheet("""
                background-color: rgba(245, 245, 245, 200);
                color: #1a1a1a;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 8px;
            """)
            
            self.input_field.setStyleSheet("""
                background-color: white;
                color: #1a1a1a;
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 8px;
            """)
            
            self.dark_mode_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border: none;
                    border-radius: 15px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """)
    
    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.dark_mode_btn.setText('☀️' if self.dark_mode else '🌙')
        self.update_theme()
        
    def add_message(self, sender, message):
        """Add a message to chat history"""
        self.chat_history.append(f"<b>{sender}:</b> {message}")
        # Scroll to bottom after adding message
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )
        
    def handle_input(self):
        """Handle user input"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        # Check if API key is set
        if self.api_key == "YOUR_OPENAI_API_KEY_HERE":
            self.add_message("System", "Please add your OpenAI API key first!")
            self.input_field.clear()
            return
            
        # Add user message to chat
        self.add_message("You", text)
        self.input_field.clear()
        self.input_field.setEnabled(False)
        
        # Show thinking state
        self.change_mood('thinking')
        self.add_message("Companion", "...")
        
        # Call ChatGPT API in separate thread
        self.chat_thread = ChatGPTThread(self.api_key, text, self.conversation_history)
        self.chat_thread.response_ready.connect(self.handle_response)
        self.chat_thread.error_occurred.connect(self.handle_error)
        self.chat_thread.start()
        
    def handle_response(self, response):
        """Handle ChatGPT response"""
        # Remove the "..." message
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()
        
        # Add the actual response
        self.add_message("Companion", response)
        
        # Store the user's message from before it was cleared
        user_message = self.chat_thread.message
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Keep conversation history manageable (last 10 messages)
        if len(self.conversation_history) > 11:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-10:]
        
        # Detect mood from response
        response_lower = response.lower()
        for mood_name in self.moods.keys():
            if mood_name in response_lower:
                self.change_mood(mood_name)
                break
        else:
            self.change_mood('happy')
        
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        
    def handle_error(self, error_msg):
        """Handle API errors"""
        # Remove the "..." message
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()
        
        self.add_message("System", f"❌ {error_msg}")
        self.change_mood('sad')
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        
    def change_mood(self, new_mood):
        """Change companion mood"""
        if new_mood in self.moods:
            self.mood = new_mood
            self.face_label.setText(self.moods[new_mood]['face'])
        
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.dragging:
            self.move(self.pos() + event.pos() - self.offset)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self.dragging = False

def main():
    app = QApplication(sys.argv)
    companion = DesktopCompanion()
    companion.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
