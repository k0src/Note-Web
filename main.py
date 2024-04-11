import sys
from PyQt6.QtWidgets import QApplication, QInputDialog, QColorDialog, QSizePolicy, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QMenu, QDialog, QHBoxLayout, QTextEdit, QPushButton
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRect
from PyQt6.QtGui import QFont, QAction, QCursor, QMouseEvent, QPainter, QPen, QColor, QPalette

class MovableTextLabel(QWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.label = QLabel(text, self)
        self.label.setStyleSheet("color: #c7c7c7;")
        font = self.label.font()
        font.setPointSize(18)
        self.label.setFont(font)
        self.draggable = False
        self.offset = QPoint()
        self.label.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.draggable = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable:
            self.move(self.mapToParent(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.draggable = False

    def setText(self, text):
        self.label.setText(text)
        self.label.adjustSize()

class Subcanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(200, 200)
        self.setMinimumSize(200, 200)
        self.setMaximumSize(parent.size())
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #4e6159; border: 2px solid black; border-color: #212121;")
        self.resizing = False
        self.resize_offset = QPoint()
        self.draggable = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            resize_handle_rect = QRect(self.width() - 10, self.height() - 10, 10, 10)
            if resize_handle_rect.contains(event.pos()):
                self.resizing = True
                self.resize_offset = event.pos()
            else:
                self.draggable = True
                self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.resizing:
            current_width = self.width()
            current_height = self.height()

            new_width = max(200, current_width + (event.pos().x() - self.resize_offset.x()))
            new_height = max(200, current_height + (event.pos().y() - self.resize_offset.y()))
            
            self.resize(new_width, new_height)
            
            self.resize_offset = event.pos()
            
        elif self.draggable:
            self.move(self.mapToParent(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.resizing:
                self.resizing = False
            elif self.draggable:
                self.draggable = False

class NoteNode(QWidget):
    titleChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 120)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #4e5661; border: 2px solid black; border-color: #212121;")
        self.draggable = False
        self.offset = QPoint()
        self.text_content = ""
        self.title = ""
        self.title_label = QLabel(self.title, self)
        self.title_label.setGeometry(0, 0, self.width(), 25)
        self.title_label.setStyleSheet("color: black;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.draggable = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable:
            self.move(self.mapToParent(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.draggable = False

    def setTextContent(self, text):
        self.text_content = text

    def setTitle(self, title):
        self.title = title
        self.title_label.setText(title)
        self.titleChanged.emit(title)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.drawText(10, 20, self.title)

class NoteEditWindow(QDialog):
    noteSaved = pyqtSignal(str)

    def __init__(self, note_node, text_content="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Note")
        self.resize(500, 600)
        self.note_node = note_node
        
        layout = QVBoxLayout()
        
        self.title_label = QLabel("")
        layout.addWidget(self.title_label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setText(text_content)
        layout.addWidget(self.text_edit)
        
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.saveNote)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

        self.title_label.setText(self.note_node.title)

    def updateTitleLabelText(self, title):
        self.title_label.setText(title)

    def saveNote(self):
        text = self.text_edit.toPlainText()
        self.noteSaved.emit(text)
        self.close()

class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Notes")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        self.title_label = QLabel("My Notes")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(20)
        self.setStyleSheet("color: #c7c7c7;")
        self.title_label.setFont(font)
        layout.addWidget(self.title_label)
        self.title_label.setMouseTracking(True)
        self.title_label.installEventFilter(self)
        self.note_nodes = []
        self.subcanvases = []
        self.text_labels = []

    def eventFilter(self, obj, event):
        if obj == self.title_label and event.type() == event.Type.MouseButtonDblClick:
            self.editTitle()
        return super().eventFilter(obj, event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        new_note_action = menu.addAction("New Note")
        new_subcanvas_action = menu.addAction("New Canvas")
        new_text_label_action = menu.addAction("New Text Label")

        separator = QAction(self)
        separator.setSeparator(True)
        menu.addAction(separator)

        edit_note_action = menu.addAction("Edit")
        note_color_action = menu.addAction("Change Color")
        rename_note_action = menu.addAction("Rename")

        separator = QAction(self)
        separator.setSeparator(True)
        menu.addAction(separator)
        
        copy_action = menu.addAction("Copy")
        cut_action = menu.addAction("Cut")
        paste_action = menu.addAction("Paste")

        separator = QAction(self)
        separator.setSeparator(True)
        menu.addAction(separator)

        delete_action = menu.addAction("Delete")

        separator = QAction(self)
        separator.setSeparator(True)
        menu.addAction(separator)

        bring_to_front_action = menu.addAction("Bring to Front")
        send_to_back_action = menu.addAction("Send to Back")

        new_note_action.triggered.connect(self.createNewNote)
        new_subcanvas_action.triggered.connect(self.createSubcanvas)
        new_text_label_action.triggered.connect(self.createNewTextLabel)

        edit_note_action.triggered.connect(self.editNote)
        rename_note_action.triggered.connect(self.renameNote)
        note_color_action.triggered.connect(self.changeNoteColor)
       
        copy_action.triggered.connect(self.copyActionTriggered)
        cut_action.triggered.connect(self.cutActionTriggered)
        paste_action.triggered.connect(self.pasteActionTriggered)
        delete_action.triggered.connect(self.deleteActionTriggered)

        bring_to_front_action.triggered.connect(self.bringToFront)
        send_to_back_action.triggered.connect(self.sendToBack)

        action = menu.exec(self.mapToGlobal(event.pos()))

    def createNewNote(self):
        cursor_pos = QCursor.pos()
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("New Note")
        input_dialog.setLabelText("Enter Note Name:")
        input_dialog.resize(300 , 100)
        input_dialog.move(cursor_pos)
        ok = input_dialog.exec()
        if ok:
            title = input_dialog.textValue()
            note_node = NoteNode(self)
            note_node.move(cursor_pos)
            note_node.setTitle(title)
            self.note_nodes.append(note_node)
            note_node.show()

    def createNewTextLabel(self):
        cursor_pos = QCursor.pos()
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("New Text Label")
        input_dialog.setLabelText("Enter Text:")
        input_dialog.resize(300 , 100)
        input_dialog.move(cursor_pos)
        ok = input_dialog.exec()
        if ok:
            text_label = MovableTextLabel(input_dialog.textValue(), self)
            text_label.move(cursor_pos)
            self.text_labels.append(text_label)
            text_label.adjustSize()
            text_label.show()

    def editNote(self):
        for note_node in self.note_nodes:
            if note_node.underMouse():
                edit_window = NoteEditWindow(note_node, text_content=note_node.text_content, parent=self)
                edit_window.noteSaved.connect(note_node.setTextContent)
                edit_window.exec()
                break

    def renameNote(self):
        for note_node in self.note_nodes:
            if note_node.underMouse():
                cursor_pos = QCursor.pos()
                input_dialog = QInputDialog(self)
                input_dialog.setWindowTitle("Rename Note")
                input_dialog.setLabelText("Enter Note Name:")
                input_dialog.resize(300 , 100)
                input_dialog.move(cursor_pos)
                ok = input_dialog.exec()
                if ok:
                    title = input_dialog.textValue()
                    note_node.setTitle(title)
                break

        for text_label in self.text_labels:
            if text_label.underMouse():
                cursor_pos = QCursor.pos()
                input_dialog = QInputDialog(self)
                input_dialog.setWindowTitle("Rename Text Label")
                input_dialog.setLabelText("Enter Text:")
                input_dialog.resize(300, 100)
                input_dialog.move(cursor_pos)
                ok = input_dialog.exec()
                if ok:
                    new_text = input_dialog.textValue()
                    text_label.setText(new_text)
                break

    def changeNoteColor(self):
        for note_node in self.note_nodes:
            if note_node.underMouse():
                current_color = note_node.palette().color(QPalette.ColorRole.Window)
                color = QColorDialog.getColor(current_color, self)
                if color.isValid():
                    note_node.setStyleSheet(f"background-color: {color.name()}; border: 2px solid black; border-color: #212121;")
                    break

        for subcanvas in self.subcanvases:
            if subcanvas.underMouse():
                current_color = subcanvas.palette().color(QPalette.ColorRole.Window)
                color = QColorDialog.getColor(current_color, self)
                if color.isValid():
                    subcanvas.setStyleSheet(f"background-color: {color.name()}; border: 2px solid black; border-color: #212121;")
                    break

        for text_label in self.text_labels:
            if text_label.underMouse():
                current_color = text_label.palette().color(QPalette.ColorRole.Window)
                color = QColorDialog.getColor(current_color, self)
                if color.isValid():
                    text_label.label.setStyleSheet(f"color: {color.name()};")
                    break

    def bringToFront(self):
        for note_node in self.note_nodes:
            if note_node.underMouse():
                note_node.raise_()
                break

        for subcanvas in self.subcanvases:
            if subcanvas.underMouse():
                subcanvas.raise_()
                break

        for text_label in self.text_labels:
            if text_label.underMouse():
                text_label.raise_()
                break

    def sendToBack(self):
        for note_node in self.note_nodes:
            if note_node.underMouse():
                note_node.lower()
                break

        for subcanvas in self.subcanvases:
            if subcanvas.underMouse():
                subcanvas.lower()
                break

        for text_label in self.text_labels:
            if text_label.underMouse():
                text_label.lower()
                break

    def createSubcanvas(self):
        cursor_pos = QCursor.pos()
        subcanvas = Subcanvas(parent=self)
        subcanvas.move(cursor_pos)
        subcanvas.lower()
        self.subcanvases.append(subcanvas)
        subcanvas.show()

    def copyActionTriggered(self):
        print("Copy")

    def cutActionTriggered(self):
        print("Cut")

    def pasteActionTriggered(self):
        print("Paste")

    def deleteActionTriggered(self):
        for subcanvas in self.subcanvases:
            if subcanvas.underMouse():
                subcanvas.deleteLater()
                self.subcanvases.remove(subcanvas)
                return

        for note_node in self.note_nodes:
            if note_node.underMouse():
                note_node.deleteLater()
                self.note_nodes.remove(note_node)
                return  
            
        for text_label in self.text_labels:
            if text_label.underMouse():
                text_label.deleteLater()
                self.text_labels.remove(text_label)
                return

    def editTitle(self):
        self.title_edit = QLineEdit(self.title_label.text())
        self.title_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_edit.setStyleSheet("font-size: 20px;")
        self.title_edit.setFixedHeight(35)
        self.title_edit.returnPressed.connect(self.updateTitle)
        self.layout().replaceWidget(self.title_label, self.title_edit)
        self.title_edit.selectAll()
        self.title_edit.setFocus()

    def updateTitle(self):
        new_title = self.title_edit.text()
        self.layout().replaceWidget(self.title_edit, self.title_label)
        self.title_label.setText(new_title)
        self.title_edit.deleteLater()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.canvas = Canvas()
        self.setCentralWidget(self.canvas)
        self.setWindowTitle("Note Blocks v0.1")

        file_menu = self.menuBar().addMenu("&File")

        new_action = QAction("&New", self)
        open_action = QAction("&Open", self)
        save_action = QAction("&Save", self)
        save_as_action = QAction("Save &As", self)

        separator = QAction(self)
        separator.setSeparator(True)
        file_menu.addAction(separator)

        exit_action = QAction("&Exit", self)

        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        new_action.triggered.connect(self.newFile)
        open_action.triggered.connect(self.openFile)
        save_action.triggered.connect(self.saveFile)
        save_as_action.triggered.connect(self.saveAsFile)
        exit_action.triggered.connect(self.exitApp)

    def newFile(self):
        print("New")

    def openFile(self):
        print("Open")

    def saveFile(self):
        print("Save")

    def saveAsFile(self):
        print("Save As")

    def exitApp(self):
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()