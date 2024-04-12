import os
from aqt import mw
from aqt.qt import QAction, QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton
from aqt.utils import showInfo

class SaveFieldContentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Field Contents to File")
        self.setupUi()

    def setupUi(self):
        layout = QVBoxLayout(self)

        # Deck selection
        self.deckLabel = QLabel("Select Deck:")
        self.deckComboBox = QComboBox()
        self.decks = mw.col.decks.all_names()
        self.deckComboBox.addItems(self.decks)

        # Target field input
        self.fieldLabel = QLabel("Target Field:")
        self.fieldInput = QLineEdit()

        # File path input
        self.fileLabel = QLabel("File Path:")
        self.fileInput = QLineEdit()

        # Submit button
        self.submitButton = QPushButton("Save to File")
        self.submitButton.clicked.connect(self.accept)

        layout.addWidget(self.deckLabel)
        layout.addWidget(self.deckComboBox)
        layout.addWidget(self.fieldLabel)
        layout.addWidget(self.fieldInput)
        layout.addWidget(self.fileLabel)
        layout.addWidget(self.fileInput)
        layout.addWidget(self.submitButton)

    def getInputs(self):
        return (self.deckComboBox.currentText(), self.fieldInput.text(), self.fileInput.text())

def save_field_contents(deck_name, target_field, file_path):
    deck_id = mw.col.decks.id(deck_name)
    card_ids = mw.col.find_cards(f'"deck:{deck_name}"')
    lines = []

    for cid in card_ids:
        card = mw.col.get_card(cid)
        note = card.note()
        if target_field in note:
            field_content = note[target_field]
            lines.append(field_content + "\n")

    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(lines)

    showInfo(f"Contents saved to {file_path}")

def showDialog():
    dialog = SaveFieldContentDialog(mw)
    if dialog.exec():
        deck_name, target_field, file_path = dialog.getInputs()
        try:
            save_field_contents(deck_name, target_field, file_path)
        except Exception as e:
            showInfo(f"Error: {e}")

def add_menu_item():
    action = QAction("Save Field Contents to File", mw)
    action.triggered.connect(showDialog)
    mw.form.menuTools.addAction(action)

add_menu_item()
