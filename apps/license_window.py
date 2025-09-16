import logging
import pipeline.libs.config as cfg

import pipeline
import pipeline.widgets.gui as gui
import pipeline.widgets.inputs as inputs
import pipeline.libs.lic as lic
import pipeline.apps.massage as massage
from pipeline.libs.Qt import QtGui, QtWidgets, QtCore



logger = logging.getLogger(__name__)

class License_dialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        print("activation code")

        # super(License_dialog, self).__init__(parent)
        # self.setStyleSheet(cfg.stylesheet)
        # self.layout = QtWidgets.QVBoxLayout(self)

        # self.pipelineUI = self.parent()
        # self.version = pipeline.version

        # self.input_widget = QtWidgets.QWidget(self)
        # self.input_layout = QtWidgets.QVBoxLayout(self.input_widget)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # self.input_layout.setContentsMargins(5, 5, 5, 5)
        # self.layout.setContentsMargins(10, 10, 10, 10)

        # self.title = gui.Title(self, label="Please enter your Pipeline {} license key:".format(self.version[0]), seperator=False)
        # self.title.layout.setContentsMargins(5, 0, 5, 0)
        # self.input_layout.addWidget(self.title)
        # self.note = gui.Title(self, label="Activation requires internet connection.")
        # font = QtGui.QFont()
        # font.setItalic(True)
        # self.note.label.setFont(font)
        # self.input_layout.addWidget(self.note)

        # self.key_widget = inputs.GroupInput(self, label="Key", inputWidget=QtWidgets.QLineEdit(self), ic=cfg.lock_icon)
        # self.key_input = self.key_widget.input
        # self.key_widget.label.setMinimumSize(QtCore.QSize(10, 30))
        # self.key_widget.label.setText("")
        # self.key_input.setMinimumSize(QtCore.QSize(300, 30))
        # self.input_layout.addWidget(self.key_widget)
        # self.layout.addWidget(self.input_widget)

        # ok = QtWidgets.QPushButton("Activate")
        # ok.setDefault(True)

        # canc = QtWidgets.QPushButton("Cancel")

        # buttons = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal)
        # buttons.addButton(ok, QtWidgets.QDialogButtonBox.AcceptRole)
        # buttons.addButton(canc, QtWidgets.QDialogButtonBox.RejectRole)

        # buttons.accepted.connect(self.accept)
        # buttons.rejected.connect(self.reject)
        # self.layout.addWidget(buttons)



    def pupup(self, m):
        print("activation code")
        # massage.massage(icon="massage", title="", message=m)

    def accept(self):
        print("activation code")
        # logger.info("activating with {}".format(self.key_input.text()))

        # activiation = lic.License_check_thread(key=self.key_input.text())
        # activiation.start()
        # activiation.join()
        # if activiation.result == lic.License_Verify.result_success:

        #     key = self.key_input.text()

        #     fullname = activiation.response["purchase"]["full_name"] if "full_name" in activiation.response["purchase"] else None
        #     email = activiation.response["purchase"]["email"]
        #     id = activiation.response["purchase"]["id"]

        #     lic.License_node(version=self.version).create(
        #                               key=key,
        #                               name=fullname,
        #                               email=email,
        #                               id=id)


        #     QtWidgets.QDialog.accept(self)
        #     self.pipelineUI.remove_activation_button()
        #     # TODO: add a nice polite massge here...

        # else:
        #     #TODO: add a nice polite massge here...
        #     logger.info(activiation.result)


    def result(self):
        print("activation code")
        # res = dict()
        # res["key"] = self.key_input.text()
        # return res

