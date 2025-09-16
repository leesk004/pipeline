import functools
import logging
import os
import os.path
import sys
import traceback
import weakref

import maya.cmds as cmds
import maya.mel as mel

import pipeline
import pipeline.apps.create_files as create
import pipeline.apps.Library as lib
import pipeline.apps.massage as massage
import pipeline.apps.Navigator as nav
import pipeline.apps.project_outliner as outliner
import pipeline.apps.projects_editor as projects_editor
import pipeline.apps.text_input as text_input
import pipeline.apps.users as users
import pipeline.libs.config as cfg
import pipeline.libs.files as files
import pipeline.libs.locking as locking
import pipeline.libs.models as models
import pipeline.libs.projects as projects
import pipeline.libs.settings as settings
import pipeline.libs.views as views
import pipeline.maya_libs.maya_warpper as maya
import pipeline.widgets.gui as gui
import pipeline.widgets.inputs as inputs
from pipeline.CSS import loadCSS
from pipeline.libs import permissions
from pipeline.libs.Qt import QtGui, QtWidgets, QtCore

logger = logging.getLogger(__name__)

logging.Logger.manager.loggerDict["pipeline.libs.requests.packages.urllib3.connectionpool"].setLevel(logging.CRITICAL)



def version_string(version):
    ver_strings = [str(i) for i in version]
    return ".".join(ver_strings)

def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.info("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_uncaught_exception


class pipeLineUI(QtWidgets.QWidget):

    instances = list()

    def __init__(self, parent=None, layout=None, window_name = '', actions_menu = None):

        super(pipeLineUI, self).__init__(parent)

        # Clean up any existing instances before creating new one
        pipeLineUI.delete_instances()

        # Add this instance to the instances list with proper error handling
        try:
            self.__class__.instances.append(weakref.proxy(self))
        except Exception as e:
            logger.warning('Failed to add instance to instances list: {}'.format(e))
        # self.build_maya_ui_elements()
        self.window_name = window_name
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.ui = self.parent()
        self.main_layout = layout #self.ui.layout()
        
        # Set minimum width for the pipeline UI to allow smaller horizontal size
        self.ui.setMinimumWidth(300)  # Allow UI to be resized to smaller width
        
        # self.ui.setStyleSheet(cfg.stylesheet)
        os.chdir(os.path.dirname(pipeline.__file__))
        css_path = os.path.join(os.path.dirname(pipeline.__file__), 'CSS', 'mainWindow.css')
        css = loadCSS.loadCSS(css_path)
        self.ui.setStyleSheet(css)
        # self.layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        # self.setLayout(self.layout)


        self.projects_widget = QtWidgets.QWidget(self.ui)

        self.main_layout.addWidget(self.projects_widget)

        self.projects_widget_layout = QtWidgets.QHBoxLayout(self.projects_widget)
        self.projects_widget_layout.setContentsMargins(0,0,0,0)
        self.projects_widget_layout.setSpacing(5)
        self.projects_pushButton = QtWidgets.QPushButton('projects')
        self.projects_pushButton.setMinimumHeight(30)
        # self.projects_pushButton.setMaximumHeight(25)

        self.projects_widget_layout.addWidget(self.projects_pushButton)

        self.main_widget = QtWidgets.QWidget(self.ui)

        self.main_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.main_layout.addWidget(self.main_widget)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.main_widget)
        self.horizontalLayout.setContentsMargins(0, 0, 2, 0)
        self.splitter = QtWidgets.QSplitter(self.main_widget)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setHandleWidth(10)
        self.splitter.setChildrenCollapsible(True)
        self.horizontalLayout.addWidget(self.splitter)



        self.pipeline_navigation_mode = cfg.Pipeline_navigation_mode.SUPER

        self.new_scene_script = None
        self.install_new_scene_script()

        self.settings = settings.settings_node()
        self.permissions = permissions.Permissions
        # self.admin_role = False

        self.navigator = nav.Navigator(self)
        self.navWidget = QtWidgets.QWidget()
        self.nav_widget_layout = QtWidgets.QVBoxLayout()
        self.nav_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.navWidget.setLayout(self.nav_widget_layout)
        self.nav_widget_layout.addWidget(self.navigator)
        # self.ui.navigation_widgetLayout.addWidget(self.navWidget)

        self.splitter.addWidget(self.navWidget)

        self.component_tabs = gui.Tabs(self)
        self.component_tabs.layout.setContentsMargins(0, 5, 0, 0)
        self.splitter.addWidget(self.component_tabs)

        self.component_widget = QtWidgets.QWidget()
        self.component_layout = QtWidgets.QVBoxLayout(self.component_widget)
        self.component_layout.setContentsMargins(0,5,0,0)
        self.component_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.component_widget.setMinimumHeight(350)
        self.component_tabs.tab_widget.addTab(self.component_widget, "Shot Detail")

        self.library_widget = QtWidgets.QWidget()
        self.library_widget_layout = QtWidgets.QVBoxLayout(self.library_widget)
        self.library_widget_layout.setContentsMargins(0,5,0,0)
        self.library_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.library_widget.setMinimumHeight(250)
        self.component_tabs.tab_widget.addTab(self.library_widget, "Shot Lists")

        if self.pipeline_navigation_mode == cfg.Pipeline_navigation_mode.STANDARD:
            self.navWidget.setMinimumHeight(300)
            self.navWidget.setMaximumHeight(300)

        self.lib = lib.Library(self, settings = self.settings)
        self.library_widget_layout.addWidget(self.lib)

        self.setting_button = None
        self.activation_button = None
        self.login_button = None


        self.build_login_button()
        self.login_button.setHidden(True)
        self.build_activation_button()

        self.current_branch_path = None
        self.component_labels = list()
        self._versionsView = None
        self._mastersView = None
        self._playblastsView = None
        self._projects = None
        self._project = None
        self.component_tabs.setEnabled(False)
        self.current_loaded_compoenent = None

        self.populate_actions_menu(actions_menu)
        self.build_component_view_ui()
        self.save_version_add_menu()
        self.save_master_add_menu()
        self.set_icons()

        self.populate_projects()

        self.populate_projects_button()

        self.build_component_labels(None)
        self.set_focus_widget = None
        self.current_component = None

        self.save_menu_enable(False)

        self.navigate_to_current_file()



        self.new_file_opened = False





    @property
    def versions_view(self):
        return self._versionsView

    @versions_view.setter
    def versions_view(self, view):
        self._versionsView = view

    @property
    def masters_view(self):
        return self._mastersView

    @masters_view.setter
    def masters_view(self, view):
        self._mastersView = view

    @property
    def playblasts_view(self):
        return self._playblastsView

    @playblasts_view.setter
    def playblasts_view(self, view):
        self._playblastsView = view

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, project):
        self._project = project

    @property
    def projects(self):
        return self._projects

    @projects.setter
    def projects(self, model):
        self._projects = model








#configure from here

    def build_component_view_ui(self):


        self.component_status_widget = QtWidgets.QWidget(self.component_widget)
        self.component_status_widget_layout = QtWidgets.QHBoxLayout(self.component_status_widget)
        self.component_status_widget_layout.setContentsMargins(2, 2, 2, 2)
        self.component_status_widget_layout.setSpacing(5)
        self.component_layout.addWidget(self.component_status_widget)


        self.component_meta_widget = QtWidgets.QWidget(self.component_widget)
        self.component_meta_widget_layout = QtWidgets.QHBoxLayout(self.component_meta_widget)
        self.component_meta_widget_layout.setContentsMargins(2, 2, 2, 2)
        # self.component_meta_widget_layout.setSpacing(5)
        # self.component_meta_widget.setMinimumHeight(98)
        # self.component_meta_widget.setMaximumHeight(98)
        self.component_layout.addWidget(self.component_meta_widget)

        self.thumbnail_button()


        self.component_text_box = text_input.TextBox(self.component_meta_widget, "")
        self.component_meta_widget_layout.addWidget(self.component_text_box)
        self.component_text_box.text_saved.connect(self.save_component_note)
        self.component_text_box.setMinimumHeight(96)
        self.component_text_box.setMaximumHeight(96)
        self.component_meta_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        # self.component_text_box


        self.component_sub_tabs = gui.Tabs(self)
        self.component_sub_tabs.layout.setContentsMargins(0,0,0,0)
        self.component_sub_tabs.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.splitter.addWidget(self.component_tabs)

        self.versions_widget = QtWidgets.QWidget()
        self.versions_widget_layout = QtWidgets.QVBoxLayout(self.versions_widget)
        self.versions_widget_layout.setContentsMargins(0, 4, 0, 0)
        self.versions_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.versions_widget.setMinimumHeight(250)
        self.component_sub_tabs.tab_widget.addTab(self.versions_widget, "Versions")

        self.masters_widget = QtWidgets.QWidget()
        self.masters_widget_layout = QtWidgets.QVBoxLayout(self.masters_widget)
        self.masters_widget_layout.setContentsMargins(0,2,0,0)
        self.masters_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.masters_widget.setMinimumHeight(250)
        self.component_sub_tabs.tab_widget.addTab(self.masters_widget, "Masters")

        # self.playblasts_widget = QtWidgets.QWidget()
        # self.playblasts_widget_layout = QtWidgets.QVBoxLayout(self.playblasts_widget)
        # self.playblasts_widget_layout.setContentsMargins(0,2,0,0)
        # self.playblasts_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # # self.playblasts_widget.setMinimumHeight(250)
        # self.component_sub_tabs.tab_widget.addTab(self.playblasts_widget, "Playblasts")

        # self.alembics_widget = QtWidgets.QWidget()
        # self.alembics_widget_layout = QtWidgets.QVBoxLayout(self.alembics_widget)
        # self.alembics_widget_layout.setContentsMargins(2, 2, 2, 2)
        # self.alembics_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # # self.playblasts_widget.setMinimumHeight(250)
        # self.component_sub_tabs.tab_widget.addTab(self.alembics_widget, "Alembics")


        self.versions_view = views.Versions_View(parentWidget=self.versions_widget, parent=self, settings = self.settings)
        self.versions_widget_layout.addWidget(self.versions_view)


        self.master_title = QtWidgets.QLabel("Published Master")
        self.master_versions_title = QtWidgets.QLabel("Master History")
        self.master_view = views.Masters_View(parentWidget=self.masters_widget, parent=self, settings = self.settings)
        self.masters_view = views.Masters_View(parentWidget=self.masters_widget, parent=self, settings = self.settings)

        self.master_view.setMaximumHeight(32)
        self.masters_widget_layout.addWidget(self.master_title)
        self.masters_widget_layout.addWidget(self.master_view)
        self.masters_widget_layout.addWidget(self.master_versions_title)
        self.masters_widget_layout.addWidget(self.masters_view)


        # self.playblast_title = QtWidgets.QLabel("Master Playblast")
        # self.playblast_versions_title = QtWidgets.QLabel("Playblasts History")
        # self.playblast_view = views.Playblasts_View(parentWidget=self.playblasts_widget, parent=self, settings = self.settings)
        # self.playblasts_view = views.Playblasts_View(parentWidget=self.playblasts_widget, parent=self, settings = self.settings)

        # self.playblast_view.setMaximumHeight(32)  # 53
        # self.playblasts_widget_layout.addWidget(self.playblast_title)
        # self.playblasts_widget_layout.addWidget(self.playblast_view)
        # self.playblasts_widget_layout.addWidget(self.playblast_versions_title)
        # self.playblasts_widget_layout.addWidget(self.playblasts_view)

        # self.alembics_title = QtWidgets.QLabel("Master Alembic")
        # self.alembics_versions_title = QtWidgets.QLabel("Alembics History")
        # self.alembic_view = views.Masters_View(parentWidget=self.alembics_widget, parent=self)
        # self.alembics_view = views.Masters_View(parentWidget=self.alembics_widget, parent=self)
        #
        # self.alembic_view.setMaximumHeight(32)  # 53
        # self.alembics_widget_layout.addWidget(self.alembics_title)
        # self.alembics_widget_layout.addWidget(self.alembic_view)
        # self.alembics_widget_layout.addWidget(self.alembics_versions_title)
        # self.alembics_widget_layout.addWidget(self.alembics_view)


        self.component_layout.addWidget(self.component_sub_tabs)

        self.component_actions_widget = QtWidgets.QWidget(self.component_widget)
        self.component_actions_widget_layout = QtWidgets.QHBoxLayout(self.component_actions_widget)
        self.component_actions_widget_layout.setContentsMargins(0, 0, 2, 0)
        self.component_layout.addWidget(self.component_actions_widget)

        self.save_version_pushButton = QtWidgets.QPushButton('Save version')
        self.save_master_pushButton = QtWidgets.QPushButton( 'Save master')
        self.playblast_pushButton = QtWidgets.QPushButton('Export to UE')

        self.save_version_pushButton.setMinimumHeight(30)
        self.save_master_pushButton.setMinimumHeight(30)
        self.playblast_pushButton.setMinimumHeight(30)

        # self.save_version_pushButton.clicked.connect(self.version_save)
        # self.save_version_pushButton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.save_version_pushButton.customContextMenuRequested.connect(self.save_version_options)
        self.save_master_pushButton.clicked.connect(self.master_save)
        self.playblast_pushButton.clicked.connect(self.playblast_save)

        self.component_actions_widget_layout.addWidget(self.save_version_pushButton)
        self.component_actions_widget_layout.addWidget(self.save_master_pushButton)
        self.component_actions_widget_layout.addWidget(self.playblast_pushButton)

    def toggle_pipeline_mode(self, *args):

        if self.pipeline_navigation_mode == cfg.Pipeline_navigation_mode.SUPER:
            self.pipeline_navigation_mode = cfg.Pipeline_navigation_mode.STANDARD
            self.navWidget.setMinimumHeight(300)
            self.navWidget.setMaximumHeight(300)

        else:
            self.pipeline_navigation_mode = cfg.Pipeline_navigation_mode.SUPER
            self.navWidget.setMinimumHeight(0)
            self.navWidget.setMaximumHeight(3000)

        if self.project:
            self.navigator.set_branch_root(self.project.path)


    def debug_create_dummys(self):
        projects.Dummy_project().create_dummy_project(self)

    def full_version(self):
        return True

    # def set_functionality(self, functionality):
    #     self.functionality = functionality

    def build_login_button(self):

        self.login_button =QtWidgets.QPushButton()
        self.login_button.setStyleSheet(cfg.rounded_button_stylesheet)
        self.login_button.setMinimumHeight(25)
        self.login_button.setMinimumWidth(25)
        self.login_button.setIconSize(QtCore.QSize(20, 20))
        self.login_button.setIcon(QtGui.QIcon(cfg.users_icon))
        self.login_button.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

        boldfont = QtGui.QFont()
        boldfont.setBold(True)

        self.login_button.setFont(boldfont)
        self.projects_widget_layout.addWidget(self.login_button)

        self.login_button.clicked.connect(self.login_menu)

    def login_menu(self):

        menu = QtWidgets.QMenu()
        # menu.addAction(QtWidgets.QAction("Switch user...", menu, triggered=self.switch_user))
        if self.project:
            menu.addSeparator()
            menu.addAction(QtWidgets.QAction("Log out from {}".format(self.project.nice_name), menu, triggered=self.log_out_project))
        menu.exec_(self.sender().mapToGlobal(QtCore.QPoint(15,30)))
        # self.login_button.setMenu(menu)

    #
    # def switch_user(self):
    #     project = self.project
    #     self.login_button.setHidden(True)
    #     self.set_active_project(None)
    #     self.settings.user = ['','']
    #     project.set()

    def log_out_project(self):
        self.login_button.setHidden(True)
        self.set_active_project(None)
        self.settings.user = ['','']

    def populate_projects_button(self):
        self.projects_pushButton.setMenu(None)


        self.projects_pushButton.setStyleSheet('''
                                            QPushButton::menu-indicator{
                                                subcontrol-position: right center;
                                                subcontrol-origin: padding;
                                                left: -5px;
                                            }
                                            ''')


        menu = QtWidgets.QMenu(self.projects_pushButton)

        if self.projects:
            for project in self.projects.items:
                menu.addAction(QtWidgets.QAction("{} ({})".format(project.nice_name, project.name), menu, triggered=project.set))

        menu.addSeparator()
        menu.addAction(QtWidgets.QAction("New project...", menu, triggered=functools.partial(projects_editor.ProjectsDialog._create_project, self)))
        menu.addAction(QtWidgets.QAction("Load project...", menu,triggered=functools.partial(projects_editor.ProjectsDialog._load_project, self)))
        menu.addSeparator()
        menu.addAction(QtWidgets.QAction("Projects manager...", menu, triggered=self.projects_window))

        self.projects_pushButton.setMenu(menu)

    def save_version_add_menu(self):
        # logger.info("right click")
        # menu.addActions(actions)
        # self.save_version_menu = QtWidgets.QMenu(self)
        # self.new_version_from_selection = QtWidgets.QAction("Save from selection...", self)
        # self.new_version_from_selection.triggered.connect(self.version_save_from_selection)
        # self.save_version_menu.addAction(self.new_version_from_selection)
        #
        # # self.save_version_menu.addSeparator()
        # self.new_version_from_file = QtWidgets.QAction("Save from File...", self)
        # self.save_version_menu.addAction(self.new_version_from_file)
        # self.new_version_from_file.triggered.connect(
        #     functools.partial(self.version_save, outliner.create_options.B_FILE))
        #
        # # logger.info(self.ui.save_version_pushButton.mapToGlobal(point))
        # self.save_version_menu.exec_(self.save_version_pushButton.mapToGlobal(point))

        menu = QtWidgets.QMenu(self.save_version_pushButton)

        menu.addAction(QtWidgets.QAction("Save...", menu, triggered =self.version_save))
        menu.addAction(QtWidgets.QAction("Save only selection...", menu, triggered=self.version_save_from_selection))
        menu.addAction(QtWidgets.QAction("Save from File...", menu,triggered = functools.partial(self.version_save, outliner.create_options.B_FILE)))


        self.save_version_pushButton.setMenu(menu)

    def save_master_add_menu(self):

        menu = QtWidgets.QMenu(self.save_master_pushButton)

        menu.addAction(QtWidgets.QAction("Save Master...", menu, triggered =self.master_save))
        #menu.addAction(QtWidgets.QAction("Options...", menu, triggered=self.master_save_options))
        # menu.addAction(QtWidgets.QAction("Save Alembic master...", menu, triggered=self.master_save))


        self.save_master_pushButton.setMenu(menu)


    def build_activation_button(self):
        print("Activation key valid")
        

        # if not lic.License_node.check_lic(pipeline.version):

        #     self.activation_button = QtWidgets.QPushButton()
        #     self.activation_button.setMinimumHeight(25)
        #     self.activation_button.setMinimumWidth(25)
        #     self.activation_button.setIconSize(QtCore.QSize(15, 15))
        #     self.activation_button.setIcon(QtGui.QIcon(cfg.lock_icon))
        #     self.activation_button.setStyleSheet(cfg.purple_button_stylesheet)
        #     self.activation_button.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        #     self.projects_widget_layout.addWidget(self.activation_button)
        #     self.activation_button.clicked.connect(self.activate)


    def remove_activation_button(self):
        return
        #self.activation_button.setHidden(True)



    def set_branch_root(self, path):
        # logger.info(path)
        self.current_branch_path = path
        self.lib.set_root(self.current_branch_path)



    def activate(self):
        #print("no activate needed")
        return
        # session = license_window.License_dialog(parent=self)
        # result = session.exec_()


    def set_icons(self):
        #
        # for button in [
        #     self.projects_pushButton,
        #     self.save_version_pushButton,
        #     self.save_master_pushButton,
        #     self.playblast_pushButton
        #
        # ]:
        #     button.setIconSize(QtCore.QSize(16, 16))


        self.projects_pushButton.setIcon(QtGui.QIcon(cfg.project_icon))
        self.save_version_pushButton.setIcon(QtGui.QIcon(cfg.save_icon))
        self.save_master_pushButton.setIcon(QtGui.QIcon(cfg.icons.publish))
        self.playblast_pushButton.setIcon(QtGui.QIcon(cfg.camrea_icon))

    def remove_component_labels(self):
        for label in self.component_labels:

            try:
                label.setParent(None)
                label.deleteLater()

            except Exception as e:
                logger.info("can not delete ui label {}: {}".format(label, e))
                return

        self.component_labels = list()

    def build_component_labels(self, component=None):

        if component:
            # logger.info("printing labels for {}".format(component.name))
            self.remove_component_labels()

            labels = self.current_component.summary_labels
            for label in labels:
                if label:
                    self.component_labels.append(label)
                    self.component_status_widget_layout.addWidget(label)

        else:
            # logger.info("earsing labels")
            self.remove_component_labels()
            self.component_labels.append(inputs.NiceQLabel("No selection"))
            self.component_status_widget_layout.addWidget(self.component_labels[0])

    def set_current_component(self):
        self.current_component = self.sender().current_component

        if self.current_component:

            '''
            take the curret open file path and trim it to relative path for the project
            if its working, then seperate the path and navigate accordingly all the way to the component.
            '''
            # logger.info(self.current_component.path)
            self.update_versions_table(self.current_component)
            self.update_masters_table(self.current_component)
            self.update_playblasts_table(self.current_component)
            self.build_component_labels(self.current_component)
            self.component_text_box.set_orig_text(self.current_component.component_note)
            self.set_thumbnail(self.current_component.thumbnail_pixmap)

            self.save_menu_enable(True)


            return


        self.clear_current_component()

        return

    def clear_current_component(self):
        try:
            self.update_versions_table(None)
            self.update_masters_table(None)
            self.update_playblasts_table(None)
            # self.ui.tabWidget.setEnabled(False)
            self.build_component_labels(None)
            self.component_text_box.set_orig_text("")
            self.set_thumbnail(cfg.large_image_icon_dark)

            # self.save_menu_enable.emit(False)
            self.save_menu_enable(False)
            # TODO: Clear and suspend the component views, nothing is selected.
        except Exception:
            pass

        return

    def set_current_component_loaded(self, component):

        if component:
            self.current_loaded_compoenent = component
            self.reset_component_models()
            # logger.info("current loaded component: {}".format(self.current_loaded_compoenent.name))


    def install_new_scene_script(self):



        """
        This function will install two scriptjobs to Maya main window,
         that will run when opening a scene and creating a new scene.
         each script will call a function in this class.
         >new_scene_actions
         >open_scene_actions
        """
        if self.new_scene_script:
            for script in self.new_scene_script:
                maya.kill_scriptjob(script)
                self.new_scene_script = None
            return False



        p = self.window_name#self.objectName()
        # logger.info(p)
        # self.new_scene_script = [maya.open_scene_script("{}".format(p), self.open_scene_actions)]
        self.new_scene_script = [maya.new_scene_script("{}".format(p), self.new_scene_actions),
                                 maya.open_scene_script("{}".format(p), self.open_scene_actions)]

        return True

    def open_scene_actions(self):
        # logger.info("open scene good")
        # last_file = maya.recent_files_list()[-2]
        # self.remove_lockfile(fullpath=last_file)
        pass

    def new_file_toggle(self):
        if self.new_file_opened:
            self.new_file_opened = False
        else:
            self.new_file_opened = True


    def new_scene_actions(self):
        self.new_file_toggle()
        # self.clear_current_component()
        # logger.info("new scene")
        # last_file = maya.recent_files_list()[-1]
        # self.remove_lockfile(fullpath=last_file, new_file=True)

    def remove_lockfile(self, fullpath=None, new_file=False):


        def remove_file(path):
            if locking.verifyLockFile(path):
                files.delete(path)


        # logger.info(fullpath)
        # logger.info(self.current_component.name)


        """
        This function will find the lockfile and delete it
        :new_file: bool, if its True, that mean that the function has been called when a user created a new file,
        and no question should be asked, and the lockfile should be deleted.
        If it's false, then the function ask:
        Has the current asset been changed? if so, delete.
        Has the current stage been changed? if so, delete.
        Has the current stage have changed, but the asset has been changed as well?, if so, delete
        """
        # logger.info("removing lockfile")


        #loof for a lock file in the file dir, or the file parent dir, if you find it, attampt to delete it.

        dir = os.path.dirname(fullpath)
        parent_dir = os.path.dirname(dir)
        comp_name = None

        lock_file = files.list_directory(dir, "lock")
        if lock_file:
            comp_name = os.path.split(dir)[1]
        else:
            lock_file = files.list_directory(parent_dir, "lock")
            if lock_file:
                comp_name = os.path.split(parent_dir)[1]

        try:
            if lock_file:
                if self.current_component.name != comp_name:
                    logger.info("Removed lockfile from component: {}".format(comp_name))
                    remove_file(lock_file[0])
                    # files.delete(lock_file[0])
                    return

        except Exception:
            logger.info(traceback.format_exc())
            logger.info('Cant remove lock file of component: {}'.format(comp_name))
            return
        # if lock_files:
        # logger.info(lock_files)
        # logger.info("skip")

        if self.new_file_opened:
            if lock_file:
                remove_file(lock_file[0])
                logger.info("Removed lockfile from component: {}, new  scene is opend.".format(comp_name))
                # logger.info("delete anyway!")
                self.new_file_toggle()


        return


    def navigate_to_current_file(self):

        """
        This function will try to navigate the UI to the correct comboboxes path and stage tab,
        by analyzing the current open file in the Maya session.
        TODO: this function needs to be batter documented
        """
        # logger.info(self.project.name)
        # logger.info(self.project.path)
        if self.project:
            file = maya.current_open_file()

            # logger.info(file)
            # logger.info("New scene")

            # Attempt to match with project path:

            if file.startswith(self.project.path):
                # logger.info("file {} starts with {}".format(file, self.project.path))

                relative_path = files.reletive_path(self.project.path, file)

                logger.info('Open file is: {}'.format(relative_path))

                path_elements = os.path.dirname(relative_path).split(os.sep)
                # logger.info(path_elements)
                # logger.info(path_elements)

                file_name_no_extension = files.file_name_no_extension(files.file_name(file))
                if not file_name_no_extension.endswith("MASTER"):

                    branch = path_elements[0]
                    catagories = path_elements[1:-1]
                    kind = path_elements[-1]

                else:

                    branch = path_elements[0]
                    catagories = path_elements[1:]
                    kind = "masters"

                # logger.info(branch)
                # logger.info(catagories)
                # logger.info(kind)


                self.navigator.branch_widget.set_branch(branch)
                # logger.info(catagories)
                self.navigator.branch_widget.discard_scan_update = True
                self.navigator.rootFolder.navigate(catagories)
                self.set_current_component_loaded(self.current_component)

                if kind == "masters":
                    self.component_sub_tabs.setCurrentIndex(1)

                # self.navigator.set_branch_root(os.path.join(self.project.path, branch))


    def new_project(self, project):

        projects_path = self.settings.projects

        if project:

            user_data = None
            if project.project_users:
                role = project.validate_user(self.settings.user[0], self.settings.user[1])
                user_data = {'users': True, 'user': self.settings.user[0], 'role': role}



            if projects_path:
                projects_path.append(project.path)
                self.projects.insertRows(0, 1, node=project)
                if user_data:
                    self.set_active_project(project, user_data)
                else:
                    self.set_active_project(project)

            else:
                projects_path = [project.path]
                self.projects = models.Projects_Model([project])

                if user_data:
                    self.set_active_project(project, user_data)
                else:
                    self.set_active_project(project)

            self.settings.projects = projects_path

    def remove_project(self, index):

        projects_path = self.settings.projects

        project = self.projects.getNode(index)
        self.projects.removeRows(index.row(), 1, parent=QtCore.QModelIndex())
        projects_path.remove(project.path)

        self.settings.projects = projects_path

        if self.settings.project == project.name:
            self.login_button.setHidden(True)
            self.set_active_project(None)

    def link_project(self, project):
        logger.info(self.link_project.__name__)
        projects_path = self.settings.projects

        if project:
            if projects_path:
                index = projects_path.index(project.name)
                projects_path[index] = project.path
                self.settings.projects = projects_path

    def populate_projects(self, project=None):


        projects_path = self.settings.projects

        if projects_path:

            list = []
            current = None
            for path in projects_path:

                project_name = files.path.lastdir(path)
                node = projects.ProjectNode(project_name, parent=None, pipelineUI=self, path=path)

                if not node.online():
                    index = projects_path.index(path)
                    projects_path[index] = files.path.lastdir(path)
                    self.settings.projects = projects_path

                if node.name == self.settings.project:
                    current = node

                list.append(node)

            if list:

                self.projects = models.Projects_Model(list)

                if current:

                    if current.project_users:
                        role = current.validate_user(self.settings.user[0], self.settings.user[1])
                        user_data = {'users': True, 'user': self.settings.user[0], 'role': role }
                        self.set_active_project(current, user_data)
                    else:
                        self.set_active_project(current)


                    return True

                self.projects_pushButton.setText("No Project")
                self.set_active_project(None)
                return False

        self.projects = None
        self.set_active_project(None)

        return False



    def reset_component_models(self):
        if self.masters_view.model():
            self.masters_view.model().sourceModel().reset()

        if self.master_view.model():
            self.master_view.model().sourceModel().reset()

        if self.versions_view.model():
            self.versions_view.model().sourceModel().reset()

    def update_playblasts_table(self, component_node=None):
        print("Not support playblast function in this version")
        # if component_node:

        #     self.playblast_view.setModel_(component_node.playblast_model())
        #     self.playblasts_view.setModel_(component_node.playblasts_model())

        #     if not component_node.playblast_model():
        #         self.component_sub_tabs.setCurrentIndex(0)

        #     return

        # self.playblast_view.setModel_(None)
        # self.playblasts_view.setModel_(None)

    def update_masters_table(self, component_node):
        if component_node:

            self.master_view.setModel_(component_node.master_model())
            self.masters_view.setModel_(component_node.masters_model())

            if not component_node.master_model():
                self.component_sub_tabs.setCurrentIndex(0)

            return

        self.master_view.setModel_(None)
        self.masters_view.setModel_(None)

    def update_versions_table(self, component_node):

        if component_node:
            self.versions_view.setModel_(component_node.version_model())
            return

        self.versions_view.setModel_(None)

    def updateCurrentProject(self, user_data):

        project = self.sender()
        self.set_active_project(project, user_data)

    def set_active_project(self, project, user_data = {'users': False, 'user': '', 'role': ''}):
        """
        This function will set the active project object.
        It will also register this project to the settings file,
        update the UI,
        and will call populate_navbar() and populate_dresser_navbar().
        it will also try to update the versions and masters tab
        TODO: why not playblasts tab? dose this function really needs to do this?
        After setting a project, it will validate the user role based on the user credentials found
        in the settings.
        Depending on the role, some UI elements will be hidden, disabled, etc.
        """


        if isinstance(project, projects.ProjectNode):

            if project.online():

                self.navWidget.setHidden(False)


                self.settings.project = project.name
                self.projects_pushButton.setText("{}".format(project.nice_name))
                self.project = project
                self.navigator.set_branch_root(project.path)
                self.lib.set_project(project)
                self.lib.set_root(self.current_branch_path)

                if user_data['users']:
                    # this project is permission depentednt
                    self.login_button.setHidden(False)


                    if user_data['role'] != '':
                        self.login_button.setText(user_data['user'][:2].upper())

                        # if self.project.users:
                        #     self.login_button.setHidden(False)
                        #     # self.ui.users_pushButton.setHidden(False)
                        #
                        #     # role = self.project.validate_user(self.settings.user[0], self.settings.user[1])
                        #     # logger.info(role)
                        #
                        #     if role:

                        # self.login_button.setText(self.settings.user[0][:2].upper())
                        self.login_button.setIcon(QtGui.QIcon())
                        # self.ui.users_pushButton.setText("{0}".format(self.settings.user[0]))
                        self.project_ui_Enable(True)

                        #TODO: now we have a role, let's set the UI accordingly

                        # if user_data['role'] == cfg._admin_:

                        self.settings.set_current_role(user_data['role'])
                        self.peremission_depentend_items()
                        # print self.settings.current_role(), '<<'
                        # else:
                        #     self.peremission_depentend_items(False)

                        return

                    else:
                        # got empty role
                        logger.info("could not log you into this project")

                else:

                    # this projects is not permissions dependents

                    # self.ui.users_pushButton.setHidden(True)

                    # TODO: now we have a role (no permissions needed=administrator), let's set the UI accordingly

                    # self.peremission_depentend_items(True)
                    self.login_button.setHidden(True)
                    self.login_button.setText('')
                    # self.ui.users_pushButton.setText("Not logged In")
                    self.settings.user = [None, None]
                    self.settings.set_current_role('administrator')
                    self.peremission_depentend_items()
                    self.project_ui_Enable(True)

                    return

        self.projects_pushButton.setText("No Project")

        self.project = None
        # self._stageNode = None
        self.settings.project = None
        self.navigator.set_branch_root(None)
        self.lib.set_project(None)

        self.navWidget.setHidden(True)

        return

    def set_thumbnail(self, Qpixmap):

        self.versionTumb_label.setPixmap(Qpixmap)

    def thumbnail_button(self):
        '''
        create a custom label button for the thumbnail

        first create a normal label
        then sets up a layout the the label
        on the new layout create a custom label-button with alpha

        '''

        # version thumbnail (square 1:1 96x96)


        self.versionTumb_label = QtWidgets.QLabel()

        self.versionTumb_label.setStyleSheet(cfg.stylesheet)#'''QLabel {
        # background-color: ''' + cfg.colors.DARK_GRAY_MINUS_A + ''';
        # }''')

        sizepolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizepolicy.setHeightForWidth(self.versionTumb_label.sizePolicy().hasHeightForWidth())
        self.versionTumb_label.setSizePolicy(sizepolicy)
        self.versionTumb_label.setMinimumSize(QtCore.QSize(120, 120))
        self.component_meta_widget_layout.addWidget(self.versionTumb_label)
        # self.ui.component_data_horizontalLayout.setContentsMargins(0, 5, 0, 0)

        self.set_thumbnail(cfg.large_image_icon_dark)

        layout = QtWidgets.QHBoxLayout(self.versionTumb_label)
        layout.setContentsMargins(0, 0, 0, 0)

        self.grab_thumnail_Button = inputs.AlphaButton(self, cfg.large_image_icon_click_dark)
        self.grab_thumnail_Button.set_pixmap(cfg.large_image_icon_click_dark)
        sizepolicy2 = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizepolicy2.setHeightForWidth(self.grab_thumnail_Button.sizePolicy().hasHeightForWidth())
        self.grab_thumnail_Button.setSizePolicy(sizepolicy2)
        self.grab_thumnail_Button.setMinimumSize(QtCore.QSize(200, 200))
        self.grab_thumnail_Button.button.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.grab_thumnail_Button)

        self.grab_thumnail_Button.alphaClick.connect(self.save_thumbnail)


    def save_thumbnail(self):
        # logger.info("capture thumb")
        if self.current_component and self.current_loaded_compoenent:

            if self.current_loaded_compoenent is not self.current_component:
                # prompt_user = True
                msg = "Where would you like to save this thumbnail?"  # Saving in {0}. Would you like to save in {1} Insted?".format(self.current_loaded_compoenent.name, self.current_component.name)
                ok_text = "Save in: {} (Default)".format(self.current_loaded_compoenent.name)
                cancel_text = "Save in: {}".format(self.current_component.name)

                prompt = massage.PromptUser(self, prompt=msg, override_yes_text=ok_text, override_no_label=cancel_text,
                                            cancel_button=True)
                result = prompt.exec_()
                logger.info(result)
                # logger.info()
                if result == 0:
                    # logger.info("defutlt")
                    self.current_loaded_compoenent.save_thumbnail()  # method=method)

                    return
                elif result == 1:
                    self.current_component.save_thumbnail()  # method=method)
                    # logger.info("override")
                    return
                else:
                    logger.info("Canceled...")
                    return

        if self.current_component:
            self.current_component.save_thumbnail()
            return
    def save_component_note(self, note):
        # logger.info(note)
        # return
        if self.current_component:
            self.current_component.component_note = note

    def save_version_options(self, point):
        # logger.info("right click")
        # menu.addActions(actions)
        self.save_version_menu = QtWidgets.QMenu(self)
        self.new_version_from_selection = QtWidgets.QAction("Save from selection...", self)
        self.new_version_from_selection.triggered.connect(self.version_save_from_selection)
        self.save_version_menu.addAction(self.new_version_from_selection)

        # self.save_version_menu.addSeparator()
        self.new_version_from_file = QtWidgets.QAction("Save from File...", self)
        self.save_version_menu.addAction(self.new_version_from_file)
        self.new_version_from_file.triggered.connect(
            functools.partial(self.version_save, outliner.create_options.B_FILE))

        # logger.info(self.ui.save_version_pushButton.mapToGlobal(point))
        self.save_version_menu.exec_(self.save_version_pushButton.mapToGlobal(point))

    def version_save_from_selection(self):
        dialog = create.Create_from_selection(None, title="Save from selection")
        result = dialog.exec_()
        input = dialog.result()
        if result == QtWidgets.QDialog.Accepted:
            self.version_save(method=input)

        else:
            logger.info("Not saving")
            return

    def version_save(self, method=0):
        # prompt_user = False
        if self.current_component and self.current_loaded_compoenent:

            if self.current_loaded_compoenent is not self.current_component:
                # prompt_user = True
                msg = "Where would you like to commit this version?"
                ok_text = "{} (Default)".format(self.current_loaded_compoenent.nice_full_name)
                cancel_text = "{}".format(self.current_component.nice_full_name)

                prompt = massage.PromptUser(self, prompt=msg,
                                            override_yes_text=ok_text,
                                            override_yes_icon=cfg.commit_icon,
                                            override_no_icon=cfg.pr_icon,
                                            cancel_icon=cfg.no_icon,
                                            override_no_label=cancel_text,
                                            cancel_button=True)


                # msg = "Where would you like to save this version?"  # Saving in {0}. Would you like to save in {1} Insted?".format(self.current_loaded_compoenent.name, self.current_component.name)
                # ok_text = "Save in: {} (Default)".format(self.current_loaded_compoenent.name)
                # cancel_text = "Save in: {}".format(self.current_component.name)
                #
                # prompt = massage.PromptUser(self, prompt=msg,
                #                             override_yes_text=ok_text,
                #                             override_no_label=cancel_text,
                #                             cancel_button=True)
                result = prompt.exec_()
                logger.info(result)
                # logger.info()
                if result == 0:
                    # logger.info("defutlt")
                    self.current_loaded_compoenent.save_version(method=method)
                    self.component_sub_tabs.setCurrentIndex(0)
                    self.navigate_to_current_file()
                    return
                elif result == 1:
                    self.current_component.save_version(method=method)
                    self.component_sub_tabs.setCurrentIndex(0)
                    # logger.info("override")
                    return
                else:
                    logger.info("Canceled...")
                    return

        if self.current_component:
            self.current_component.save_version(method=method)
            self.component_sub_tabs.setCurrentIndex(0)

            return

        logger.info('Not saving: No component is loaded.')

    def master_save_options(self, *args):
        import pipeline.maya_libs.maya_qt as maya_qt
        try:
            import pipeline.apps.publish_options as publish_options
            maya_qt.show(publish_options.Publish_Options_dialog, pipeline_window=self)
        except ImportError:
            logger.warning("publish_options module not found")
            pass


    def master_save(self, *args):

        if self.current_component and self.current_loaded_compoenent:

            if maya.file_modifed():
                msg = "The current file must be saved before publishing it."  # Saving in {0}. Would you like to save in {1} Insted?".format(self.current_loaded_compoenent.name, self.current_component.name)
                ok_text = "Save and proceed"
                cancel_text = "Cancel"

                prompt = massage.PromptUser(self, prompt=msg, override_yes_text=ok_text, override_no_label=cancel_text)
                result = prompt.exec_()
                logger.info(result)
                # logger.info()

                if result == 0:
                    maya.save_scene()
                else:
                    logger.info("You must save the version before publishing")
                    return

            if self.current_loaded_compoenent.name is not self.current_component.name:

                # prompt_user = True
                msg = "Where would you like to save this master?"  # Saving in {0}. Would you like to save in {1} Insted?".format(self.current_loaded_compoenent.name, self.current_component.name)
                ok_text = "Save in: {} (Default)".format(self.current_loaded_compoenent.name)
                cancel_text = "Save in: {}".format(self.current_component.name)

                prompt = massage.PromptUser(self, prompt=msg, override_yes_text=ok_text, override_no_label=cancel_text,
                                            cancel_button=True)
                result = prompt.exec_()
                logger.info(result)
                # logger.info()
                if result == 0:  # QtWidgets.QMessageBox.YesRole:
                    logger.info("default")
                    self.current_loaded_compoenent.save_master()
                    self.navigate_to_current_file()
                    self.component_sub_tabs.setCurrentIndex(1)
                    return
                elif result == 1:  # QtWidgets.QMessageBox.NoRole:
                    self.current_component.save_master()
                    self.component_sub_tabs.setCurrentIndex(1)
                    logger.info("override")
                    return
                else:
                    logger.info("Canceled...")
                    return
            else:
                self.current_component.save_master()
                self.component_sub_tabs.setCurrentIndex(1)
                # logger.info("override")
                return

        else:
            logger.info("No component selected")
            return

    def playblast_save(self, *args):
        #print("Export fbx")
        
        def sliceDir(input_string, word):

            index = input_string.find(word)
            if index != -1:
                return input_string[:index ]
            return input_string
        
        def fbxNameSpace(input_string, words_to_remove):
            for word in words_to_remove:
                input_string = input_string.replace(word, '')
            return input_string
        
        def get_text_input():
            result = cmds.promptDialog(
                title='Export fbx option',
                message='Enter the character name:',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')

            if result == 'OK':
                char_name = cmds.promptDialog(query=True, text=True)
                return char_name
            else:
                return None


        currentScene = os.path.abspath(cmds.file(q=True, sn=True))
        word_to_find = "\\AS_"
        result = sliceDir(currentScene, word_to_find)
        print("Dir Result:", result)

        directory = result
        files = os.listdir(directory)
        index = 0
        charName = get_text_input()


        min_time = int(cmds.playbackOptions(q=True, min=True))
        max_time = int(cmds.playbackOptions(q=True, max=True))
        
        while index < len(files):
            filename = files[index]
            print(filename)
            if filename.endswith(('.ma')):
                cmds.ls(sl=True,long=True)
                words_to_remove = ["_MASTER"]              
                #fbx파일포멧을 .ma파일포멧으로 바꿈
                wholeName = os.path.splitext(filename)[0] + "_" + charName + '.fbx'
                exportName = fbxNameSpace(wholeName, words_to_remove)
                exportDirectory = directory + "/"

                # #FBX export disabled options
                # mel.eval("FBXExportSmoothingGroups -v true")
                # mel.eval("FBXExportHardEdges -v false")
                # mel.eval("FBXExportTangents -v false")
                # mel.eval("FBXExportSmoothMesh -v true")
                # mel.eval("FBXExportInstances -v false")
                # mel.eval("FBXExportReferencedAssetsContent -v false")
                # mel.eval("FBXExportAnimationOnly -v false")
                #mel.eval("FBXExportUseSceneName -v false")
                #mel.eval("FBXExportQuaternion -v euler")
                #mel.eval("FBXExportShapes -v true")
                #mel.eval("FBXExportSkins -v true")
                # # # Constraints
                # # mel.eval("FBXExportConstraints -v false")
                # # # Cameras
                # # mel.eval("FBXExportCameras -v false")
                # # # Lights
                # # mel.eval("FBXExportLights -v false")
                # # # Embed Media
                # # mel.eval("FBXExportEmbeddedTextures -v false")
                # # # Connections
                # # mel.eval("FBXExportInputConnections -v false")
                # # Axis Conversion
                # mel.eval("FBXExportUpAxis z")
                # # Version
                # mel.eval("FBXExportFileVersion -v FBX201800")
                # mel.eval("FBXExportInAscii -v true")


                #FBX export enabled options
                mel.eval("FBXExportBakeComplexAnimation -v true")
                mel.eval("FBXExportBakeComplexStart -v " + str(min_time))
                mel.eval("FBXExportBakeComplexEnd -v " + str(max_time))
                mel.eval("FBXExportBakeComplexStep -v 1")

                cmds.file(exportDirectory + exportName, force=True, type="FBX export", pr=True, es=True)
            
            index += 1


                
        # if self.current_component and self.current_loaded_compoenent:

        #     if self.current_loaded_compoenent.name is not self.current_component.name:

        #         # prompt_user = True
        #         msg = "Where would you like to save this playblast?"  # Saving in {0}. Would you like to save in {1} Insted?".format(self.current_loaded_compoenent.name, self.current_component.name)
        #         ok_text = "Save in: {} (Default)".format(self.current_loaded_compoenent.name)
        #         cancel_text = "Save in: {}".format(self.current_component.name)

        #         prompt = massage.PromptUser(self, prompt=msg, override_yes_text=ok_text, override_no_label=cancel_text,
        #                                     cancel_button=True)
        #         result = prompt.exec_()
        #         logger.info(result)
        #         # logger.info()
        #         if result == 0:
        #             # logger.info("defutlt")
        #             self.current_loaded_compoenent.save_playblast()
        #             self.navigate_to_current_file()
        #             self.component_sub_tabs.setCurrentIndex(2)
        #             return
        #         elif result == 1:
        #             self.current_component.save_playblast()
        #             self.component_sub_tabs.setCurrentIndex(2)
        #             # logger.info("override")
        #             return
        #         else:
        #             logger.info("Canceled...")
        #             return
        #     else:
        #         self.current_component.save_playblast()
        #         self.component_sub_tabs.setCurrentIndex(2)
        #         # logger.info("override")
        #         return

        # else:
        #     logger.info("No component selected")
        #     return

    def projects_window(self):
        ''' start the projects window '''

        # make sure it will be the only instance of it...
        if hasattr(self, "projects_dialog"):
            if isinstance(self.projects_dialog, projects_editor.ProjectsDialog):
                self.projects_dialog.close()

        self.projects_dialog = projects_editor.ProjectsDialog(parent=self)
        self.projects_dialog.show()





    def project_ui_Enable(self, bool):

        self.component_tabs.setEnabled(bool)

    def peremission_depentend_items(self):

        if self.permissions.has_permissions(role_string=self.settings.current_role(), action=self.permissions.save_master):
            self.save_master_pushButton.setEnabled(True)
        else:
            self.save_master_pushButton.setEnabled(False)

        # if self.permissions.has_permissions(role_string=self.settings.current_role(), action=self.permissions.save_version):
        #     self.save_version_pushButton.setEnabled(True)
        #     self.playblast_pushButton.setEnabled(True)
        # else:
        #     self.save_version_pushButton.setEnabled(False)
        #     self.playblast_pushButton.setEnabled(False)


    def login_window(self):


        login = users.LoginWindow()
        result = login.exec_()
        user, password = login.result()
        if result == QtWidgets.QDialog.Accepted:
            if user != "":
                self.settings.user = [user, password]
                self.login_button.setText(self.settings.user[0][:2].upper())
                self.login_button.setIcon(QtGui.QIcon())
                # self.ui.users_pushButton.setText(user)

                if self.project:
                    role = self.project.validate_user(user, password)
                    if role:
                        self.set_active_project(self.project)
                return
                # """
                # TAKE ACTION DEPENDING ON ROLE
                # """

                #
                # self.ui.users_pushButton.setText("{0}".format(user))
                # self.project_ui_Enable(True)
                #
                # # self.unload_project()
                # return role

            self.settings.user = [None, None]
            self.set_active_project(self.project)
            self.login_button.setIcon(QtGui.QIcon(cfg.users_icon))
            self.login_button.setText('')
            # self.ui.users_pushButton.setText("Not logged In")
            return




    def populate_actions_menu(self, parent_menu):
        try:
            cmds.deleteUI(Menu_items.SAVE_VERSION_ACTION)
            cmds.deleteUI(Menu_items.SAVE_VERSION_FILE_ACTION)
            cmds.deleteUI(Menu_items.SAVE_VERSION_SEL_ACTION)
            cmds.deleteUI(Menu_items.SAVE_MASTER_ACTION)
            cmds.deleteUI(Menu_items.SAVE_PLAYBLAST_ACTION)

            cmds.deleteUI(Menu_items.SAVE_VERSION_DIV)
            cmds.deleteUI(Menu_items.SAVE_MASTER_DIV)
            cmds.deleteUI(Menu_items.SAVE_PLAYBLAST_DIV)

        except Exception:
            pass

        cmds.menuItem(Menu_items.SAVE_VERSION_DIV, parent=parent_menu, divider=True, label='Versions')
        cmds.menuItem(Menu_items.SAVE_VERSION_ACTION, parent=parent_menu, label='Save version', c=functools.partial(self.version_save, ))
        cmds.menuItem(Menu_items.SAVE_VERSION_FILE_ACTION, parent=parent_menu, label='Save version from file',c=functools.partial(self.version_save, "From File" ))
        cmds.menuItem(Menu_items.SAVE_VERSION_SEL_ACTION, parent=parent_menu, label='Save version from selection', c=functools.partial(self.version_save, "From selection" ))

        cmds.menuItem(Menu_items.SAVE_MASTER_DIV, parent=parent_menu, divider=True, label='Masters')
        cmds.menuItem(Menu_items.SAVE_MASTER_ACTION, parent=parent_menu, label='Save master',c=functools.partial(self.master_save, ))

        cmds.menuItem(Menu_items.SAVE_PLAYBLAST_DIV, parent=parent_menu, divider=True, label='Playblasts')
        #cmds.menuItem(Menu_items.SAVE_PLAYBLAST_ACTION, parent=parent_menu, label='Save playblast',c=functools.partial(self.playblast_save, ))


    def save_menu_enable(self, bool):

        save_verion = bool
        save_master = bool

        if not self.permissions.has_permissions(role_string=self.settings.current_role(),action=self.permissions.save_version):
            save_verion = False

        maya.menuItem_enable(Menu_items.SAVE_VERSION_ACTION, save_verion)
        maya.menuItem_enable(Menu_items.SAVE_VERSION_FILE_ACTION, save_verion)
        maya.menuItem_enable(Menu_items.SAVE_VERSION_SEL_ACTION, save_verion)
        maya.menuItem_enable(Menu_items.SAVE_PLAYBLAST_ACTION, save_verion)

        if not self.permissions.has_permissions(role_string=self.settings.current_role(),action=self.permissions.save_master):
            save_master = False

        maya.menuItem_enable(Menu_items.SAVE_MASTER_ACTION, save_master)


    def run(self):
        return self

    def closeEvent(self, event):
        """Handle the close event to properly clean up the instance"""
        try:
            # Remove this instance from the instances list
            if hasattr(self, '__class__') and hasattr(self.__class__, 'instances'):
                # Create a list of valid instances to keep
                valid_instances = []
                for ins in self.__class__.instances:
                    try:
                        # Check if the weakref proxy is still valid
                        _ = ins
                        if ins is not self:
                            valid_instances.append(ins)
                    except (ReferenceError, RuntimeError):
                        # Object already deleted, skip it
                        pass
                
                # Update the instances list with only valid instances
                self.__class__.instances = valid_instances
        except Exception as e:
            logger.warning('Error during closeEvent cleanup: {}'.format(e))
        
        # Call the parent closeEvent
        super(pipeLineUI, self).closeEvent(event)

    def __del__(self):
        """Destructor to ensure proper cleanup"""
        try:
            # This is a safety net in case closeEvent wasn't called
            if hasattr(self, '__class__') and hasattr(self.__class__, 'instances'):
                # Try to remove this instance from the instances list
                try:
                    if self in self.__class__.instances:
                        self.__class__.instances.remove(self)
                except (ValueError, ReferenceError):
                    # Already removed or invalid reference
                    pass
        except Exception:
            # Ignore any errors during destruction
            pass

    @staticmethod
    def delete_instances():
        # Create a copy of the list to avoid modification during iteration
        instances_copy = pipeLineUI.instances[:]
        
        for ins in instances_copy:
            try:
                # Check if the weakref proxy is still valid
                _ = ins  # This will raise ReferenceError if the object is deleted
                logger.info('Delete {}'.format(ins))
                ins.setParent(None)
                ins.deleteLater()
            except (ReferenceError, RuntimeError):
                # Object already deleted, just remove from list
                logger.info('Object already deleted, removing from instances list')
            except Exception as e:
                # Other exceptions during cleanup
                logger.warning('Exception during cleanup: {}'.format(e))
            finally:
                # Always try to remove from instances list
                try:
                    if ins in pipeLineUI.instances:
                        pipeLineUI.instances.remove(ins)
                except (ReferenceError, ValueError):
                    # Object already removed or invalid
                    pass
        
        # Clear the instances list completely
        pipeLineUI.instances.clear()

    @staticmethod
    def cleanup_invalid_instances():
        """Clean up any invalid instances from the instances list"""
        try:
            valid_instances = []
            for ins in pipeLineUI.instances:
                try:
                    # Check if the weakref proxy is still valid
                    _ = ins
                    valid_instances.append(ins)
                except (ReferenceError, RuntimeError):
                    # Object already deleted, skip it
                    logger.info('Removing invalid instance from instances list')
                    pass
            
            pipeLineUI.instances = valid_instances
            logger.info('Cleaned up instances list. Valid instances: {}'.format(len(valid_instances)))
        except Exception as e:
            logger.warning('Error during instance cleanup: {}'.format(e))


class Menu_items(object):

    @classmethod
    def __iter__(cls):
        return (getattr(cls, attr) for attr in dir(cls) if not callable(getattr(cls, attr)) and not attr.startswith("__"))


    SAVE_VERSION_DIV = 'save_version_divider'
    SAVE_MASTER_DIV = 'save_master_divider'
    SAVE_PLAYBLAST_DIV = 'save_playblast_divider'
    SAVE_VERSION_ACTION = 'save_version_action'
    SAVE_VERSION_SEL_ACTION = 'save_version_sec_action'
    SAVE_VERSION_FILE_ACTION = 'save_version_file_action'
    SAVE_MASTER_ACTION = 'save_master_action'
    SAVE_PLAYBLAST_ACTION = 'save_playblast_action'