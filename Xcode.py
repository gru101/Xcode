import sys
from PySide6.QtWidgets import (QWidget, QApplication, QMainWindow, QToolBar, QStatusBar, QFileDialog, QInputDialog, QTextBrowser, QTextEdit, QMessageBox, QPushButton )
from PySide6.QtGui import Qt, QAction, QScreen, QIcon, QPixmap, QKeySequence, QSyntaxHighlighter, QFont, QColor, QTextCharFormat, QSyntaxHighlighter, QTextCursor, QClipboard
from PySide6.QtCore import QSize,QRegularExpression
import os
from llama_index.llms.groq import Groq
from llama_index.core.prompts import RichPromptTemplate
import re

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Bold)

        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda", "None",
            "nonlocal", "not", "or", "pass", "raise", "return", "True",
            "try", "while", "with", "yield"
        ]

        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        pattern = QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"')
        self.highlighting_rules.append((pattern, string_format))

        pattern = QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'")
        self.highlighting_rules.append((pattern, string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        pattern = QRegularExpression(r'#[^\n]*')
        self.highlighting_rules.append((pattern, comment_format))

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA"))
        pattern = QRegularExpression(r'\b[A-Za-z0-9_]+(?=\s*\()')
        self.highlighting_rules.append((pattern, function_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class CodeWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Code Recommendation")
        self.setFixedSize(350,350)

        self.recommended_code = QTextBrowser()

        self.setCentralWidget(self.recommended_code)

        self.buttons_bar = QToolBar()
        self.accept = QAction("Accept", self)
        self.reject = QAction("Reject", self)
        self.buttons_bar.addAction(self.accept)
        self.buttons_bar.addAction(self.reject)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea,self.buttons_bar)
        self.buttons_bar.setMovable(False)

        self.reject.triggered.connect(self.close)

    def AddText(self, text):
        self.recommended_code.setText(text)

    def close(self):
        super().hide()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("XCode")
        self.resize(800, 500)

        logo = QIcon(QPixmap("C:/Users/kandg/Downloads/xcode(1)(1).png"))
        self.setWindowIcon(logo)

        self.open_file = QAction("Open File", self)
        self.open_file.setStatusTip("Open File")
        self.open_file.triggered.connect(self.OpenFile)
        self.open_file.setShortcut("Ctrl+O")

        self.new_file = QAction("New File", self)
        self.new_file.setStatusTip("Create a new file")
        self.new_file.triggered.connect(self.NewFile)
        self.new_file.setShortcut("Ctrl+N")

        self.save = QAction("Save", self)
        self.save.setStatusTip("Save File")
        self.save.triggered.connect(self.Save)
        self.save.setShortcut("Ctrl+S")

        self.save_as = QAction("Save As", self)
        self.save_as.setStatusTip("Save File in preferred your format")
        self.save_as.triggered.connect(self.SaveAs)
        self.save_as.setShortcut("Ctrl+Shift+S")

        self.get_api_key = QAction("API Key", self)
        self.get_api_key.setStatusTip("Set you API Key")
        self.get_api_key.triggered.connect(self.GetAPIKey)
        self.get_api_key.setShortcut("Shift+K")

        self.code_recommendation = QAction("Ask AI", self)
        self.code_recommendation.triggered.connect(self.RecommendCode)
        self.code_recommendation.setShortcut("Shift+R")

        self.setStatusBar(QStatusBar(self))

        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        api_key = menu.addAction(self.get_api_key)
        code_recommendation = menu.addAction(self.code_recommendation)

        file_menu.addAction(self.new_file)
        file_menu.addSeparator()
        file_menu.addAction(self.open_file)
        file_menu.addSeparator()
        file_menu.addAction(self.save)
        file_menu.addSeparator()
        file_menu.addAction(self.save_as)

        self.text_editor = QTextEdit()
        self.setCentralWidget(self.text_editor)
        self.text_editor.setVisible(False)

        self.current_file = None
        self.current_file_content = None
        self.user_api_key = None

        self.recommendation_window = None  # Store a reference

        self.clipboard = QClipboard()
        self.cursor_ = QTextCursor()

    def GetAPIKey(self):
        key, ok = QInputDialog.getText(self,"Enter your API Key", "API Key")
        self.user_api_key = key

    def OpenFile(self, check):
        file_path, _ = QFileDialog.getOpenFileName()
        if file_path:
            self.current_file = file_path
            with open(file_path, "r", encoding="utf-8") as file:
                contents = file.read()
                self.text_editor.setText(contents)
                self.text_editor.setVisible(True)
                PythonSyntaxHighlighter(self.text_editor.document())
            self.text_editor.textChanged.connect(self.update_file_content)

    def NewFile(self, check):
        self.text_editor.setText("")
        self.text_editor.setVisible(True)
        self.text_editor.textChanged.connect(self.update_file_content)
        PythonSyntaxHighlighter(self.text_editor.document())


    def update_file_content(self):
        self.current_file_content = self.text_editor.document()

    def Save(self):
        if self.current_file:
            with open(self.current_file, "w", encoding="utf-8") as file:
                file.write(self.text_editor.toPlainText())  # Save
        else:
            self.SaveAs()

    def SaveAs(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;All Files (*);;.py")
        if file_path:
            self.current_file = file_path
            self.Save()

    def RecommendCode(self, check):
        self.update_file_content()

        if self.user_api_key is None:
            message = QMessageBox()
            message.information(self,"API key not set", "Set an API Key first")
            message.resize(350, 150)
            return

        model = "qwen-2.5-coder-32b"
        llm = Groq(model=model,api_key=self.user_api_key)

        query = QInputDialog.getMultiLineText(self, "Enter query", "Ask your question ?")
        qa_prompt_tmpl_str = """\
        Context information is below.
        ---------------------
        {{ context_str }}
        ---------------------
        Given the context information (the existing code) and not prior knowledge, act as a highly skilled coding assistant.  
        Your role is to analyze, debug, optimize, and improve the provided code while ensuring best practices for maintainability, efficiency, and readability.  

        You should:  
        - Explain the purpose and functionality of the given code.  
        - Identify and fix potential bugs, inefficiencies, or security vulnerabilities.  
        - Suggest improvements, optimizations, and alternative solutions when relevant.  
        - Ensure adherence to industry standards and best practices.  
        - Consider edge cases, error handling, and performance implications.  

        Query: {{ query_str }}  
        Answer: \
        """

        prompt_template = RichPromptTemplate(qa_prompt_tmpl_str)
        prompt = prompt_template.format(context_str=self.current_file_content.toPlainText(), query_str=query)

        response = str(llm.complete(prompt))
        pattern = r"```python\s*([\s\S]*?)\s*```"
        code = re.findall(pattern, response, re.DOTALL)  # Extract all matches

        # Check if the window is already open
        if not self.recommendation_window or not self.recommendation_window.isVisible():
            extracted_code = "\n\n".join(code)  # Join multiple code blocks with spacing
            self.recommendation_window = CodeWindow()
            self.recommendation_window.AddText(extracted_code)
            self.clipboard.setText(extracted_code)
            PythonSyntaxHighlighter(self.recommendation_window.recommended_code.document())
            self.recommendation_window.show()

        self.recommendation_window.accept.triggered.connect(self.AcceptCode)

    def AcceptCode(self):
        cursor = self.text_editor.textCursor()
        cursor.insertText(self.clipboard.text())
        self.recommendation_window.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()