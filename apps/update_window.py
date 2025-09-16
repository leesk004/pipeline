import logging
import pipeline.libs.config as cfg
import pipeline.libs.settings as settings
import pipeline.widgets.gui as gui
import pipeline.widgets.inputs as inputs

from pipeline.libs.Qt import QtGui, QtWidgets, QtCore



logger = logging.getLogger(__name__)

class Update_window(QtWidgets.QMainWindow):

    update_session = None

    def __init__(self, parent=None):
        super(Update_window, self).__init__(parent)

        # self.pipelineUI = self.parent()
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.main_widget)

        self.setStyleSheet(cfg.stylesheet)
        self.layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(10, 5, 10, 10)

        self.setMinimumHeight(120)
        self.setMaximumHeight(120)
        self.setMinimumWidth(600)
        self.setMaximumWidth(600)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # self.center_to_maya_window()

        # self.current_version = current_version
        self.caption = gui.Title(self,label="", seperator=False)

        self.link_label = Click_label()
        self.link_label.setHidden(True)
        self.layout.addWidget(self.link_label)
        self.layout.addWidget(self.caption)

        self.startup_switch = inputs.GroupInput(self, label="Check for updates on startup", inputWidget= QtWidgets.QCheckBox())
        self.startup_switch_input = self.startup_switch.input

        if settings.settings_node().check_for_updates:
            self.startup_switch_input.setCheckState(QtCore.Qt.Checked)

        self.startup_switch_input.stateChanged.connect(self.start_updates_toggle)
        self.layout.addWidget(self.startup_switch)

        self.ok = QtWidgets.QPushButton("Abort")
        self.ok.setIconSize(QtCore.QSize(20, 20))

        self.ok.setIcon(QtGui.QIcon(cfg.no_icon))
        self.ok.clicked.connect(self.close)
        self.layout.addWidget(self.ok)

    def center_to_maya_window(self):
        # self.move(self.pipeline_window.maya_main.window().frameGeometry().topLeft() + self.pipeline_window.maya_main.window().rect().center() - self.rect().center())

        frameGm = self.frameGeometry()
        # Qt6 compatible screen centering
        try:
            # Try Qt6 approach first
            cursor_pos = QtGui.QCursor.pos()
            screen = QtWidgets.QApplication.screenAt(cursor_pos)
            if screen is None:
                screen = QtWidgets.QApplication.primaryScreen()
            centerPoint = screen.geometry().center()
        except AttributeError:
            # Fallback for older Qt versions
            screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
            centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())


    def show_with_massage(self, massage = ""):
        print("This function will be implemented - update_window")
        # self.caption.label.setText(massage)

        # if 'pipeline.nnl.tv' in massage:# == '':
        #     self.caption.setHidden(True)
        #     self.link_label.setHidden(False)
        #     self.link_label.setText(massage)
        #     self.link_label.clicked.connect(self.launch_link)


        # self.show()
        # return 200


    def launch_link(self):
        print("This function will implement soon")
        # import webbrowser
        # webbrowser.open('http://pipeline.nnl.tv/')

    def start_updates_toggle(self, state):
        if state == QtCore.Qt.Checked:
            logger.info("enable updates check on startup")
            settings.settings_node().check_for_updates = True
        else:
            logger.info("disable updates check on startup")
            settings.settings_node().check_for_updates = False

    def dismiss_label(self):
        self.ok.setText("Dismiss")
        self.ok.setIcon(QtGui.QIcon(cfg.yes_icon))



class Click_label(QtWidgets.QLabel):
    clicked = QtCore.Signal()

    def __init__(self):
        super(Click_label, self).__init__()

    def mouseReleaseEvent(self, e):
        logger.info(e)
        self.clicked.emit()
        e.accept()