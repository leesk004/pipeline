import pipeline.apps.project_outliner as outliner
import pipeline.libs.config as cfg
from pipeline.libs.Qt import QtWidgets, QtCore



class Create_from_selection(QtWidgets.QDialog):
    def __init__(self, parent = None, title = None):
        super(Create_from_selection, self).__init__(parent)

        self.setStyleSheet(cfg.stylesheet)
        self.setMaximumWidth(200)
        self.setMinimumWidth(200)
        self.setMaximumHeight(50)

        self.label = QtWidgets.QLabel()
        self.label.setPixmap(cfg.new_icon)
        #
        layout = QtWidgets.QVBoxLayout(self)
        self.item_name = QtWidgets.QLabel(title)
        # self.text_input = QtWidgets.QLineEdit()
        self.include_radio = QtWidgets.QRadioButton("Include all connections")
        self.include_radio.setChecked(True)
        self.exclude_radio = QtWidgets.QRadioButton("Include only textures")



        layout.addWidget(self.item_name)
        # layout.addWidget(self.text_input)
        layout.addWidget(self.include_radio)
        layout.addWidget(self.exclude_radio)


        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def radio_selection(self):
        if self.include_radio.isChecked():
            return outliner.create_options.E_SELECTION_ALL
        else:
            return outliner.create_options.D_SELECTION_ONLY

    def result(self):
        return self.radio_selection()