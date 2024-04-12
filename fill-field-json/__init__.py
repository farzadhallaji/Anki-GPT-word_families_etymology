import sys
import re
from aqt import mw
from aqt.utils import showInfo, qconnect
from aqt.qt import *
from aqt.utils import showInfo, getText, showWarning
from aqt.qt import QAction, qconnect
from aqt.progress import ProgressManager
from PyQt6.QtWidgets import QProgressDialog
from PyQt6.QtCore import Qt
import json
from PyQt6.QtWidgets import QFileDialog
from aqt.qt import QAction, QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton

class TranslationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fill Fields from JSON")
        layout = QVBoxLayout(self)
        
        # Create line edits and combo boxes for inputs
        self.deck_name_input = QLineEdit(self)
        self.source_field_input = QLineEdit(self)
        self.target_field_input = QLineEdit(self)
        self.json_path_input = QLineEdit(self)
        self.json_key_input = QLineEdit(self)
        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.browse_file)
        
        # Add widgets to the layout
        layout.addWidget(QLabel("Deck Name:"))
        layout.addWidget(self.deck_name_input)
        layout.addWidget(QLabel("Source Field:"))
        layout.addWidget(self.source_field_input)
        layout.addWidget(QLabel("Target Field:"))
        layout.addWidget(self.target_field_input)
        layout.addWidget(QLabel("JSON File Path:"))
        layout.addWidget(self.json_path_input)
        layout.addWidget(self.browse_button)
        layout.addWidget(QLabel("JSON Key:"))
        layout.addWidget(self.json_key_input)
        
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        
    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select JSON file", "", "JSON files (*.json)")
        if path:
            self.json_path_input.setText(path)
    
    def getInputs(self):
        return (self.deck_name_input.text(), self.source_field_input.text(),
                self.target_field_input.text(), self.json_path_input.text(),
                self.json_key_input.text())

 
def fill_field_to_deck(deck_name, source_field, target_field, json_data, json_key):
    deck_id = mw.col.decks.id(deck_name)
    mw.col.decks.select(deck_id)
    card_ids = mw.col.find_cards(f'"deck:{deck_name}"')
    progressDialog = QProgressDialog("Filling Field...", "Abort", 0, len(card_ids), mw)
    progressDialog.setWindowModality(Qt.WindowModality.WindowModal)
    progressDialog.setMinimumDuration(0)
    progressDialog.setAutoClose(True)
    
    for idx, cid in enumerate(card_ids):
        if progressDialog.wasCanceled():
            break
        
        card = mw.col.get_card(cid)
        note = card.note()
        if source_field in note.fields:
            source_value = note[source_field]
            if source_value in json_data and json_key in json_data[source_value]:
                note[target_field] = json_data[source_value][json_key]
            else:
                # If the source value or json_key is not found, you might want to handle it
                # For now, maybe leave it unchanged or clear it.
                note[target_field] = ""  # or you can skip setting this
        note.flush()
        progressDialog.setValue(idx + 1)
    
    progressDialog.setValue(len(card_ids))
    showInfo(f"Processed deck: {deck_name}")


def showDialog():
    dialog = TranslationDialog(mw)
    if dialog.exec():
        deck_name, source_field, target_field, json_path, json_key = dialog.getInputs()
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            fill_field_to_deck(deck_name, source_field, target_field, data, json_key)
            showInfo(f"Field Filled in deck: {deck_name}")
        except Exception as e:
            showInfo(f"Exception during filling: {e}")

def add_menu_item():
    action = QAction("Fill Field with Json", mw)
    action.triggered.connect(showDialog)
    mw.form.menuTools.addAction(action)

add_menu_item()
