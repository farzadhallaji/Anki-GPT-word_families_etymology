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
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class TranslationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fill Fields from JSON")
        layout = QVBoxLayout(self)

        # Deck selection
        self.deckLabel = QLabel("Select Deck:", self)
        self.deckComboBox = QComboBox(self)
        self.decks = mw.col.decks.all_names()  # Get all deck names
        self.deckComboBox.addItems(self.decks)  # Add deck names to the combobox
        self.deckComboBox.currentIndexChanged.connect(self.update_fields)  # Update fields when deck changes

        # Source and Target Field Inputs
        self.sourceFieldLabel = QLabel("Source Field:", self)
        self.sourceFieldComboBox = QComboBox(self)
        self.targetFieldLabel = QLabel("Target Field:", self)
        self.targetFieldComboBox = QComboBox(self)

        # JSON File Path Input
        self.jsonPathLabel = QLabel("JSON File Path:", self)
        self.jsonPathInput = QLineEdit(self)
        self.browseButton = QPushButton("Browse", self)
        self.browseButton.clicked.connect(self.browse_file)

        # JSON Key Input
        self.jsonKeyLabel = QLabel("JSON Key:", self)
        self.jsonKeyInput = QLineEdit(self)

        # Convert to HTML Checkbox
        self.convertToHtmlCheckBox = QCheckBox("Convert to HTML", self)

        # OK Button
        self.okButton = QPushButton("OK", self)
        self.okButton.clicked.connect(self.accept)

        # Add widgets to the layout
        layout.addWidget(self.deckLabel)
        layout.addWidget(self.deckComboBox)
        layout.addWidget(self.sourceFieldLabel)
        layout.addWidget(self.sourceFieldComboBox)
        layout.addWidget(self.targetFieldLabel)
        layout.addWidget(self.targetFieldComboBox)
        layout.addWidget(self.jsonPathLabel)
        layout.addWidget(self.jsonPathInput)
        layout.addWidget(self.browseButton)
        layout.addWidget(self.jsonKeyLabel)
        layout.addWidget(self.jsonKeyInput)
        layout.addWidget(self.convertToHtmlCheckBox)
        layout.addWidget(self.okButton)

        # Load fields initially
        self.update_fields()

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select JSON file", "", "JSON files (*.json)")
        if path:
            self.jsonPathInput.setText(path)

    def update_fields(self):
        self.sourceFieldComboBox.clear()
        self.targetFieldComboBox.clear()

        fields = set()
        # Iterate through all models (note types) and gather their field names
        for model in mw.col.models.all():
            for field in model['flds']:  # 'flds' is a list of fields in each model
                fields.add(field['name'])

        # Sort the fields and add them to the combo boxes
        sorted_fields = sorted(fields)
        self.sourceFieldComboBox.addItems(sorted_fields)
        self.targetFieldComboBox.addItems(sorted_fields)


    def getInputs(self):
        #return {
            #'deck_name': self.deckComboBox.currentText(),
            #'source_field': self.sourceFieldComboBox.currentText(),
            #'target_field': self.targetFieldComboBox.currentText(),
            #'json_path': self.jsonPathInput.text(),
            #'json_key': self.jsonKeyInput.text(),
            #'convert_to_html': self.convertToHtmlCheckBox.isChecked()
        #}
        
        return self.deckComboBox.currentText(), self.sourceFieldComboBox.currentText(), self.targetFieldComboBox.currentText(),self.jsonPathInput.text(),self.jsonKeyInput.text(), self.convertToHtmlCheckBox.isChecked()
           
def generate_html(word, word_family):
    html_content = f"<p>Word Family of <strong>{word}</strong>:</p>\n<ul>\n"
    for item in word_family:
        html_content += f"  <li><strong>{item['word_form']}</strong> ({item['part_of_speech']}) - {item['definition']}</li>\n"
    html_content += "</ul>"
    return html_content


def fill_field_to_deck(deck_name, source_field, target_field, json_data, json_key, convert_to_html):
    logging.info("Starting to fill fields for deck: %s", deck_name)
    deck_id = mw.col.decks.id(deck_name)
    # mw.col.decks.select(deck_id)
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
        logging.debug("Processing card ID %s", cid)
        
        if source_field in note:
            source_value = note[source_field].strip().lower()
            logging.debug("Source field '%s' has value '%s'", source_field, source_value)
            if source_value in json_data:
                etymology = json_data[source_value].get(json_key, "")
                if convert_to_html:
                    note[target_field] = generate_html(source_value, etymology)
                else:
                    note[target_field] = etymology
                logging.info("Updated '%s' for card ID %s", target_field, cid)
            else:
                logging.warning("Source value '%s' not found in JSON data", source_value)
                note[target_field] = ""
            note.flush()
        else:
            logging.error("Source field '%s' not found in note for card ID %s", source_field, cid)
        progressDialog.setValue(idx + 1)
    
    progressDialog.setValue(len(card_ids))
    showInfo(f"Processed deck: {deck_name}")



def showDialog():
    dialog = TranslationDialog(mw)
    if dialog.exec():
        deck_name, source_field, target_field, json_path, json_key, convert_to_html = dialog.getInputs()
        print(f"Deck: {deck_name}, Source: {source_field}, Target: {target_field}, Path: {json_path}, Key: {json_key}, HTML: {convert_to_html}")
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            print("JSON Data Loaded Successfully")
            fill_field_to_deck(deck_name, source_field, target_field, data, json_key, convert_to_html)
            showInfo(f"Field Filled in deck: {deck_name}")
        except Exception as e:
            print(f"Exception: {e}")
            showInfo(f"Exception during filling: {e}")

def add_menu_item():
    action = QAction("Fill Field with Json", mw)
    action.triggered.connect(showDialog)
    mw.form.menuTools.addAction(action)

add_menu_item()
