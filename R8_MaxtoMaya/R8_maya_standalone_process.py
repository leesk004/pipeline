'''
Maya Standalone File Processor
ma, fbx 파일들을 처리하는 Maya Standalone 도구

사용법:
import R8_MaxtoMaya.R8_maya_standalone_process as standalone_process
from importlib import reload
reload(standalone_process)
standalone_process.show_ui()
'''

import os
import json
import subprocess
import platform
import time
import tempfile
import maya.OpenMayaUI as omui

# Maya 버전에 따른 PySide 모듈 임포트
try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance

# =============================================================================
# 상수 및 설정
# =============================================================================

TOOL_NAME = 'Maya Standalone File Processor'

# 설정 파일 경로
USER_HOME = os.path.expanduser('~')
CONFIG_DIR = os.path.join(USER_HOME, '.maya_standalone_processor')
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'processor_config.json')

# =============================================================================
# 유틸리티 함수
# =============================================================================

def get_maya_main_window():
    """Maya 메인 윈도우를 반환합니다."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

# =============================================================================
# 메인 UI 클래스
# =============================================================================

class MayaStandaloneProcessorUI(QtWidgets.QDialog):
    """Maya Standalone File Processor UI 클래스"""
    
    def __init__(self, parent=get_maya_main_window()):
        super(MayaStandaloneProcessorUI, self).__init__(parent)
        
        # 윈도우 설정
        self.setWindowTitle(TOOL_NAME)
        self.resize(650, 700)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        # 변수 초기화
        self.file_folder = None
        self.rig_folder = None
        self.output_folder = None  # 출력 폴더 경로
        self.file_list = []
        self.selected_python_file = None
        self.selected_function = None
        self.available_functions = []
        self.execution_logs = []  # 실행 로그 저장
        
        # UI 구성
        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        
        # 설정 로드
        self.load_config()
    
    def create_widgets(self):
        """UI 위젯 생성"""
        
        # 라벨 스타일 설정 함수
        def setup_label(text, font_size=11):
            label = QtWidgets.QLabel(text)
            label.setStyleSheet("color: rgb(200, 255, 0);")
            font = label.font()
            font.setPointSize(font_size)
            label.setFont(font)
            return label
        
        # file Path (상단 첫 번째 경로)
        self.file_path_label = setup_label("File Path : ")
        self.file_folder_line_edit = QtWidgets.QLineEdit()
        self.file_folder_line_edit.setPlaceholderText("file 파일이 있는 폴더를 선택하세요...")
        
        # 새로고침 버튼 (아이콘)
        self.file_refresh_button = QtWidgets.QPushButton()
        self.file_refresh_button.setFixedSize(28, 28)
        try:
            # Qt 객체가 유효한지 확인 후 아이콘 설정
            if hasattr(self, 'style') and self.style() is not None:
                self.file_refresh_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
            else:
                self.file_refresh_button.setText("↻")
        except (RuntimeError, AttributeError, TypeError):
            # PySide6 객체 삭제 에러 방지 - 텍스트로 대체
            self.file_refresh_button.setText("↻")
        self.file_refresh_button.setToolTip("파일 새로고침")
        
        # 폴더 선택 버튼 (아이콘)
        self.file_folder_button = QtWidgets.QPushButton("")
        self.file_folder_button.setFixedSize(28, 28)
        try:
            # Qt 객체가 유효한지 확인 후 아이콘 설정
            if hasattr(self, 'style') and self.style() is not None:
                self.file_folder_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogOpenButton))
            else:
                self.file_folder_button.setText("📁")
        except (RuntimeError, AttributeError, TypeError):
            # PySide6 객체 삭제 에러 방지 - 텍스트로 대체
            self.file_folder_button.setText("📁")
        self.file_folder_button.setToolTip("file 폴더 선택")
        
        # 파일 목록 테이블
        self.file_table_group = QtWidgets.QGroupBox("FBX 파일명")
        self.file_table_widget = QtWidgets.QTableWidget()
        self.file_table_widget.setColumnCount(2)
        self.file_table_widget.setHorizontalHeaderLabels(['파일명', '타입'])
        self.file_table_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.file_table_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.file_table_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.file_table_widget.setAlternatingRowColors(True)
        
        # 테이블 컬럼 크기 설정
        self.file_table_widget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.file_table_widget.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.file_table_widget.setMinimumHeight(250)
        
        # 컨텍스트 메뉴 설정
        self.file_table_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        
        # 출력 폴더 설정
        self.output_folder_group = QtWidgets.QGroupBox("출력 폴더 설정")
        self.output_folder_label = setup_label("Output Folder : ")
        self.output_folder_line_edit = QtWidgets.QLineEdit()
        self.output_folder_line_edit.setPlaceholderText("처리된 파일을 저장할 폴더를 선택하세요...")
        
        # 출력 폴더 선택 버튼
        self.output_folder_button = QtWidgets.QPushButton("")
        self.output_folder_button.setFixedSize(28, 28)
        try:
            # Qt 객체가 유효한지 확인 후 아이콘 설정
            if hasattr(self, 'style') and self.style() is not None:
                self.output_folder_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogOpenButton))
            else:
                self.output_folder_button.setText("📁")
        except (RuntimeError, AttributeError, TypeError):
            # PySide6 객체 삭제 에러 방지 - 텍스트로 대체
            self.output_folder_button.setText("📁")
        self.output_folder_button.setToolTip("출력 폴더 선택")
        
        # 하단 처리 버튼들
        self.process_selected_button = QtWidgets.QPushButton("선택된 파일 처리 (0개)")
        self.process_selected_button.setFixedHeight(40)
        self.process_selected_button.setEnabled(False)  # 초기에는 비활성화
        
        self.process_all_button = QtWidgets.QPushButton("모든 파일 처리 (0개)")
        self.process_all_button.setFixedHeight(40)
        self.process_all_button.setEnabled(False)  # 초기에는 비활성화
        
        # 실행 로그 텍스트 창
        self.execution_log_text = QtWidgets.QTextEdit()
        self.execution_log_text.setMinimumHeight(150)
        self.execution_log_text.setMaximumHeight(200)
        self.execution_log_text.setReadOnly(True)
        self.execution_log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 14px;
            }
        """)
        self.execution_log_text.setPlaceholderText("실행 로그가 여기에 표시됩니다...")
        
        # 파일 타입 필터
        self.filter_group = QtWidgets.QGroupBox("파일 타입 필터")
        self.show_all_radio = QtWidgets.QRadioButton("All Files")
        self.show_fbx_radio = QtWidgets.QRadioButton("FBX")
        self.show_ma_radio = QtWidgets.QRadioButton("MA")
        self.show_ma_radio.setChecked(True)  # 기본값
        
        # 필터 라디오 버튼 그룹
        self.filter_button_group = QtWidgets.QButtonGroup(self)
        self.filter_button_group.addButton(self.show_all_radio)
        self.filter_button_group.addButton(self.show_fbx_radio)
        self.filter_button_group.addButton(self.show_ma_radio)
        self.filter_button_group.setExclusive(True)
        
        # Python 함수 선택 그룹
        self.function_group = QtWidgets.QGroupBox("Python 함수 선택")
        
        # Python 파일 선택
        self.python_file_label = setup_label("Python File : ")
        self.python_file_line_edit = QtWidgets.QLineEdit()
        self.python_file_line_edit.setPlaceholderText("Python 파일을 선택하세요...")
        self.python_file_line_edit.setReadOnly(True)
        
        self.python_file_button = QtWidgets.QPushButton("")
        self.python_file_button.setFixedSize(28, 28)
        try:
            # Qt 객체가 유효한지 확인 후 아이콘 설정
            if hasattr(self, 'style') and self.style() is not None:
                self.python_file_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogOpenButton))
            else:
                self.python_file_button.setText("📄")
        except (RuntimeError, AttributeError, TypeError):
            # PySide6 객체 삭제 에러 방지 - 텍스트로 대체
            self.python_file_button.setText("📄")
        self.python_file_button.setToolTip("Python 파일 선택")
        
        # 함수 선택
        self.function_label = setup_label("Function : ")
        self.function_combo = QtWidgets.QComboBox()
        self.function_combo.setPlaceholderText("함수를 선택하세요...")
        self.function_combo.setEnabled(False)
        
        # 함수 새로고침 버튼
        self.refresh_functions_button = QtWidgets.QPushButton("새로고침")
        self.refresh_functions_button.setFixedHeight(28)
        self.refresh_functions_button.setEnabled(False)
        self.refresh_functions_button.setToolTip("함수 목록 새로고침")
    
    def create_layouts(self):
        """레이아웃 생성"""
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # file Path 레이아웃 (상단 첫 번째)
        file_path_layout = QtWidgets.QHBoxLayout()
        file_path_layout.addWidget(self.file_path_label)
        file_path_layout.addWidget(self.file_folder_line_edit)
        file_path_layout.addWidget(self.file_refresh_button)
        file_path_layout.addWidget(self.file_folder_button)
        main_layout.addLayout(file_path_layout)
        
        # 파일 타입 필터 그룹
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(self.show_all_radio)
        filter_layout.addWidget(self.show_fbx_radio)
        filter_layout.addWidget(self.show_ma_radio)
        filter_layout.addStretch()
        self.filter_group.setLayout(filter_layout)
        main_layout.addWidget(self.filter_group)
        
        # Python 함수 선택 그룹
        function_layout = QtWidgets.QVBoxLayout()
        
        # Python 파일 선택 레이아웃
        python_file_layout = QtWidgets.QHBoxLayout()
        python_file_layout.addWidget(self.python_file_label)
        python_file_layout.addWidget(self.python_file_line_edit)
        python_file_layout.addWidget(self.python_file_button)
        function_layout.addLayout(python_file_layout)
        
        # 함수 선택 레이아웃
        function_select_layout = QtWidgets.QHBoxLayout()
        function_select_layout.addWidget(self.function_label)
        function_select_layout.addWidget(self.function_combo)
        function_select_layout.addWidget(self.refresh_functions_button)
        function_layout.addLayout(function_select_layout)
        
        self.function_group.setLayout(function_layout)
        main_layout.addWidget(self.function_group)
        
        # 파일 테이블 그룹
        file_table_layout = QtWidgets.QVBoxLayout()
        file_table_layout.addWidget(self.file_table_widget)
        self.file_table_group.setLayout(file_table_layout)
        main_layout.addWidget(self.file_table_group)
        
        # 출력 폴더 그룹
        output_folder_layout = QtWidgets.QHBoxLayout()
        output_folder_layout.addWidget(self.output_folder_label)
        output_folder_layout.addWidget(self.output_folder_line_edit)
        output_folder_layout.addWidget(self.output_folder_button)
        self.output_folder_group.setLayout(output_folder_layout)
        main_layout.addWidget(self.output_folder_group)
        
        # 처리 버튼들
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.process_selected_button)
        button_layout.addWidget(self.process_all_button)
        main_layout.addLayout(button_layout)
        
        # 실행 로그 창
        execution_log_group = QtWidgets.QGroupBox("실행 로그")
        execution_log_layout = QtWidgets.QVBoxLayout()
        
        # 실행 로그 관리 버튼들
        log_button_layout = QtWidgets.QHBoxLayout()
        self.clear_log_button = QtWidgets.QPushButton("Clear Log")
        self.clear_log_button.clicked.connect(self.clear_execution_logs)
        
        
        log_button_layout.addWidget(self.clear_log_button)
        log_button_layout.addStretch()
        
        execution_log_layout.addLayout(log_button_layout)
        execution_log_layout.addWidget(self.execution_log_text)
        execution_log_group.setLayout(execution_log_layout)
        main_layout.addWidget(execution_log_group)
    
    def create_connections(self):
        """시그널-슬롯 연결"""
        self.file_folder_button.clicked.connect(self.select_file_folder)
        self.file_refresh_button.clicked.connect(self.refresh_files)
        self.process_selected_button.clicked.connect(lambda: self.process_files(selected_only=True))
        self.process_all_button.clicked.connect(lambda: self.process_files(selected_only=False))
        
        # 출력 폴더 선택 연결
        self.output_folder_button.clicked.connect(self.select_output_folder)
        
        # Python 함수 선택 관련 연결
        self.python_file_button.clicked.connect(self.select_python_file)
        self.refresh_functions_button.clicked.connect(self.refresh_functions)
        self.function_combo.currentTextChanged.connect(self.on_function_selected)
        
        # 파일 타입 필터 연결
        self.filter_button_group.buttonClicked.connect(self.apply_file_filter)
        
        # 파일 테이블 컨텍스트 메뉴
        self.file_table_widget.customContextMenuRequested.connect(self.show_file_context_menu)
        
        # 파일 선택 상태 변경 시 버튼 업데이트
        self.file_table_widget.selectionModel().selectionChanged.connect(self.update_button_states)
    
    def select_file_folder(self):
        """file 폴더 선택"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "file 폴더 선택", self.file_folder or "")
        
        if folder:
            self.file_folder = folder
            self.file_folder_line_edit.setText(folder)
            self.refresh_files()
            self.save_config()
    
    def select_output_folder(self):
        """출력 폴더 선택"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "출력 폴더 선택", self.output_folder or "")
        
        if folder:
            self.output_folder = folder
            self.output_folder_line_edit.setText(folder)
            self.save_config()
            self.add_execution_log("INFO", f"출력 폴더 설정: {folder}")
    
    def select_rig_folder(self):
        """Rig 폴더 선택"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Rig 폴더 선택", self.rig_folder or "")
        
        if folder:
            self.rig_folder = folder
            self.rig_folder_line_edit.setText(folder)
            self.save_config()
    
    def select_python_file(self):
        """Python 파일 선택"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Python 파일 선택", "", "Python Files (*.py)")
        
        if file_path and os.path.exists(file_path):
            self.selected_python_file = file_path
            self.python_file_line_edit.setText(file_path)
            self.refresh_functions()
            self.save_config()
            print(f"Python 파일 선택: {file_path}")
            
            # 버튼 상태 업데이트
            self.update_button_states()
    
    def refresh_functions(self):
        """선택된 Python 파일에서 함수 목록 추출"""
        if not self.selected_python_file or not os.path.exists(self.selected_python_file):
            QtWidgets.QMessageBox.warning(self, "경고", "Python 파일을 먼저 선택하세요.")
            return
        
        try:
            # Python 파일에서 함수 목록 추출
            functions = self.extract_functions_from_file(self.selected_python_file)
            self.available_functions = functions
            
            # 콤보박스 업데이트
            self.function_combo.clear()
            if functions:
                self.function_combo.addItems(functions)
                self.function_combo.setEnabled(True)
                self.refresh_functions_button.setEnabled(True)
                print(f"발견된 함수: {functions}")
            else:
                self.function_combo.setEnabled(False)
                self.refresh_functions_button.setEnabled(False)
                QtWidgets.QMessageBox.information(self, "정보", "선택된 파일에서 함수를 찾을 수 없습니다.")
            
            # 버튼 상태 업데이트
            self.update_button_states()
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"함수 분석 중 오류가 발생했습니다:\n{e}")
            print(f"함수 분석 오류: {e}")
            # 오류 발생 시에도 버튼 상태 업데이트
            self.update_button_states()
    
    def extract_functions_from_file(self, file_path):
        """Python 파일에서 함수 목록 추출"""
        import ast
        
        functions = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AST 파싱
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 함수 정의 발견
                    func_name = node.name
                    # private 함수나 특수 함수 제외
                    if not func_name.startswith('_'):
                        functions.append(func_name)
                        
        except Exception as e:
            print(f"파일 파싱 오류: {e}")
            
        return sorted(functions)
    
    def on_function_selected(self, function_name):
        """함수 선택 시 호출"""
        if function_name:
            self.selected_function = function_name
            print(f"선택된 함수: {function_name}")
        else:
            self.selected_function = None
        
        # 버튼 상태 업데이트
        self.update_button_states()
    
    def refresh_files(self):
        """파일 목록 새로고침"""
        if not self.file_folder or not os.path.exists(self.file_folder):
            return
        
        # 지원되는 파일 확장자
        supported_extensions = ['.fbx', '.ma']
        
        # 파일 찾기
        files = []
        for file in os.listdir(self.file_folder):
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in supported_extensions:
                file_type = file_ext.upper()[1:]  # .fbx -> FBX
                files.append((file, file_type))
        
        files.sort()
        self.file_list = files
        
        # 현재 필터 적용
        self.apply_file_filter()
        
        print(f"총 {len(files)}개의 파일을 찾았습니다.")
    
    def apply_file_filter(self):
        """파일 타입 필터 적용"""
        if not self.file_list:
            self.file_table_widget.setRowCount(0)
            return
        
        # 현재 선택된 필터 확인
        if self.show_fbx_radio.isChecked():
            filtered_files = [(f, t) for f, t in self.file_list if t == 'FBX']
        elif self.show_ma_radio.isChecked():
            filtered_files = [(f, t) for f, t in self.file_list if t == 'MA']
        else:  # All Files
            filtered_files = self.file_list[:]
        
        # 테이블 업데이트
        self.file_table_widget.setRowCount(len(filtered_files))
        for i, (filename, file_type) in enumerate(filtered_files):
            # 파일명 아이템
            filename_item = QtWidgets.QTableWidgetItem(filename)
            self.file_table_widget.setItem(i, 0, filename_item)
            
            # 파일 타입 아이템 (기본 색상)
            type_item = QtWidgets.QTableWidgetItem(file_type)
            self.file_table_widget.setItem(i, 1, type_item)
        
        # 그룹박스 제목 업데이트
        self.file_table_group.setTitle(f"파일 목록 ({len(filtered_files)}개)")
        
        # 버튼 상태 업데이트
        self.update_button_states()
    
    def show_file_context_menu(self, position):
        """파일 테이블 우클릭 컨텍스트 메뉴 표시"""
        item = self.file_table_widget.itemAt(position)
        if not item:
            return
        
        context_menu = QtWidgets.QMenu(self)
        
        # Maya 관련 메뉴
        maya_menu = context_menu.addMenu("Maya")
        open_scene_action = maya_menu.addAction("Open Scene")
        import_scene_action = maya_menu.addAction("Import Scene")
        
        context_menu.addSeparator()
        open_folder_action = context_menu.addAction("Open File Folder")
        
        # 메뉴 실행
        action = context_menu.exec_(self.file_table_widget.viewport().mapToGlobal(position))
        
        if action == open_scene_action:
            self.open_maya_scene()
        elif action == import_scene_action:
            self.import_maya_scene()
        elif action == open_folder_action:
            self.open_containing_folder()
    
    def open_containing_folder(self):
        """file_folder_line_edit에 입력된 폴더 열기"""
        import os
        folder_path = self.file_folder_line_edit.text().strip()
        
        if not folder_path:
            QtWidgets.QMessageBox.warning(self, "경고", "File Path가 입력되지 않았습니다.")
            return
        
        if not os.path.exists(folder_path):
            QtWidgets.QMessageBox.warning(self, "경고", f"폴더가 존재하지 않습니다:\n{folder_path}")
            return
        
        try:
            try:
                os.startfile(folder_path)
                print(f"폴더 열기: {folder_path}")

            except Exception as e:
                print(f"폴더 열기 실패: {e}")
                QtWidgets.QMessageBox.critical(self, "오류", f"폴더 열기 중 오류가 발생했습니다:\n{e}")
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"폴더 열기 중 오류가 발생했습니다:\n{e}")
            print(f"폴더 열기 오류: {e}")
    
    def open_maya_scene(self):
        """선택된 파일을 Maya에서 열기"""
        selected_rows = sorted({i.row() for i in self.file_table_widget.selectedIndexes()})
        if not selected_rows:
            QtWidgets.QMessageBox.warning(self, "경고", "열 파일을 선택하세요.")
            return
        
        if len(selected_rows) > 1:
            QtWidgets.QMessageBox.warning(self, "경고", "하나의 파일만 선택하세요.")
            return
        
        try:
            # 선택된 파일 정보 가져오기
            row = selected_rows[0]
            filename_item = self.file_table_widget.item(row, 0)
            if not filename_item:
                return
            
            filename = filename_item.text()
            file_path = os.path.join(self.file_folder, filename)
            
            if not os.path.exists(file_path):
                QtWidgets.QMessageBox.warning(self, "경고", f"파일이 존재하지 않습니다:\n{file_path}")
                return
            
            # Maya에서 파일 열기
            import maya.cmds as cmds
            
            # 현재 씬이 수정되었는지 확인
            if cmds.file(query=True, modified=True):
                reply = QtWidgets.QMessageBox.question(
                    self, "씬 저장", 
                    "현재 씬이 수정되었습니다. 저장하시겠습니까?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
                
                if reply == QtWidgets.QMessageBox.Yes:
                    cmds.file(save=True)
                elif reply == QtWidgets.QMessageBox.Cancel:
                    return
            
            # 파일 열기
            cmds.file(file_path, open=True, force=True)
            print(f"Maya에서 파일 열기: {file_path}")
            QtWidgets.QMessageBox.information(self, "완료", f"파일을 열었습니다:\n{filename}")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"Maya 씬 열기 중 오류가 발생했습니다:\n{e}")
            print(f"Maya 씬 열기 오류: {e}")
    
    def import_maya_scene(self):
        """선택된 파일을 Maya에 임포트"""
        selected_rows = sorted({i.row() for i in self.file_table_widget.selectedIndexes()})
        if not selected_rows:
            QtWidgets.QMessageBox.warning(self, "경고", "임포트할 파일을 선택하세요.")
            return
        
        try:
            import maya.cmds as cmds
            
            imported_count = 0
            failed_files = []
            
            for row in selected_rows:
                filename_item = self.file_table_widget.item(row, 0)
                if not filename_item:
                    continue
                
                filename = filename_item.text()
                file_path = os.path.join(self.file_folder, filename)
                
                if not os.path.exists(file_path):
                    failed_files.append(f"{filename} (파일 없음)")
                    continue
                
                try:
                    # 파일 임포트
                    cmds.file(file_path, i=True, force=True)
                    imported_count += 1
                    print(f"Maya에 파일 임포트: {file_path}")
                    
                except Exception as import_error:
                    failed_files.append(f"{filename} ({str(import_error)})")
                    print(f"임포트 실패: {filename} - {import_error}")
            
            # 결과 메시지 표시
            if imported_count > 0:
                message = f"{imported_count}개 파일이 성공적으로 임포트되었습니다."
                if failed_files:
                    message += f"\n\n실패한 파일 ({len(failed_files)}개):\n" + "\n".join(failed_files)
                QtWidgets.QMessageBox.information(self, "임포트 완료", message)
            else:
                QtWidgets.QMessageBox.warning(self, "임포트 실패", "모든 파일 임포트에 실패했습니다.")
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"Maya 씬 임포트 중 오류가 발생했습니다:\n{e}")
            print(f"Maya 씬 임포트 오류: {e}")
    
    def process_files(self, selected_only=True):
        """파일들을 처리합니다.
        
        Args:
            selected_only (bool): True면 선택된 파일만, False면 모든 파일 처리
        """
        files_to_process = self.get_files_to_process(selected_only=selected_only)
        
        if not files_to_process:
            if selected_only:
                QtWidgets.QMessageBox.warning(self, "경고", "처리할 파일을 선택하세요.")
            else:
                QtWidgets.QMessageBox.warning(self, "경고", "처리할 파일이 없습니다.")
            return
        
        # 선택된 파일과 모든 파일 처리 정보를 전달
        self.start_file_processing(files_to_process, selected_only=selected_only)
    
    def get_files_to_process(self, selected_only=True):
        """처리할 파일 목록을 가져옵니다.
        
        Args:
            selected_only (bool): True면 선택된 파일만, False면 모든 파일 반환
            
        Returns:
            list: (filename, file_type) 튜플의 리스트
        """
        if selected_only:
            # 선택된 행들 가져오기
            selected_rows = sorted({i.row() for i in self.file_table_widget.selectedIndexes()})
            if not selected_rows:
                return []
            
            files_to_process = []
            for row in selected_rows:
                filename_item = self.file_table_widget.item(row, 0)
                file_type_item = self.file_table_widget.item(row, 1)
                if filename_item and file_type_item:
                    files_to_process.append((filename_item.text(), file_type_item.text()))
        else:
            # 현재 필터된 모든 파일들 가져오기
            files_to_process = []
            for i in range(self.file_table_widget.rowCount()):
                filename_item = self.file_table_widget.item(i, 0)
                file_type_item = self.file_table_widget.item(i, 1)
                if filename_item and file_type_item:
                    files_to_process.append((filename_item.text(), file_type_item.text()))
        
        return files_to_process
    
    def update_button_states(self):
        """버튼 상태를 업데이트합니다."""
        # 선택된 파일 개수
        selected_count = len(self.file_table_widget.selectedIndexes()) // 2  # 행당 2개 컬럼이므로 2로 나눔
        selected_count = max(0, selected_count)  # 음수 방지
        
        # 전체 파일 개수 (현재 필터된 파일들)
        total_count = self.file_table_widget.rowCount()
        
        # Python 파일과 함수 선택 상태 확인
        has_python_file = bool(self.selected_python_file)
        has_function = bool(self.selected_function)
        can_process = has_python_file and has_function
        
        # 선택된 파일 처리 버튼 업데이트
        self.process_selected_button.setText(f"선택된 파일 처리 ({selected_count}개)")
        self.process_selected_button.setEnabled(selected_count > 0 and can_process)
        
        # 모든 파일 처리 버튼 업데이트
        self.process_all_button.setText(f"모든 파일 처리 ({total_count}개)")
        self.process_all_button.setEnabled(total_count > 0 and can_process)
    
    def start_file_processing(self, files_to_process, selected_only=True):
        """파일 처리 시작 - Maya Standalone 실행"""
        if not files_to_process:
            return
        
        # 기존 프로그레스 다이얼로그가 있으면 먼저 정리
        self._cleanup_progress_dialog()
        
        # Python 파일과 함수 선택 확인
        if not self.selected_python_file:
            QtWidgets.QMessageBox.warning(
                self, "Python 파일 미선택", 
                "Python 파일을 먼저 선택하세요.")
            return
        
        if not self.selected_function:
            QtWidgets.QMessageBox.warning(
                self, "함수 미선택", 
                "처리할 함수를 먼저 선택하세요.")
            return
        
        # 현재 Maya 버전 확인
        current_maya_version = self.get_current_maya_version()
        if not current_maya_version:
            QtWidgets.QMessageBox.warning(
                self, "Maya 버전 오류", 
                "현재 Maya 버전을 확인할 수 없습니다.\nMaya가 실행 중인지 확인해주세요.")
            return
        
        
        # 실행 로그 추가
        processing_type = "선택된 파일" if selected_only else "모든 파일"
        self.add_execution_log("INFO", f"{processing_type} 처리 시작: {len(files_to_process)}개 파일")
        self.add_execution_log("INFO", f"선택된 함수: {self.selected_function}")
        
        # 처리할 파일 목록 로그에 기록
        self.add_execution_log("INFO", f"처리할 파일 목록 ({processing_type}):")
        for i, (filename, file_type) in enumerate(files_to_process, 1):
            self.add_execution_log("INFO", f"  {i}. {filename} ({file_type})")
        
        # 진행 상황을 보여주는 프로그레스 다이얼로그 생성
        dialog_title = f"Maya Standalone {processing_type} 처리"
        self.progress_dialog = QtWidgets.QProgressDialog(f"Maya Standalone {processing_type} 처리 준비 중...", "", 0, len(files_to_process), self)
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        self.progress_dialog.setWindowTitle(dialog_title)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setMinimumSize(400, 120)
        self.progress_dialog.setCancelButton(None)
        
        # 취소 플래그 초기화
        self.processing_cancelled = False
        self.is_cancelled = False  # R8_ani_batch_process.py와 동일한 방식
        
        # 백그라운드 처리용 변수들 (R8_ani_batch_process.py 방식)
        self.file_queue = files_to_process
        self.current_index = 0
        self.progress_callback = None
        self.file_result_callback = None
        self.current_process = None
        
        # 취소 버튼 클릭 시 처리 취소
        def on_cancel_clicked():
            self.add_execution_log("WARNING", "사용자가 Maya Standalone 처리 취소를 요청했습니다.")
            print("Maya Standalone 처리 취소 요청됨")
            try:
                # Maya Standalone 처리 취소
                self.cancel_processing()
                
                # 프로그레스 다이얼로그 닫기 및 정리
                self._cleanup_progress_dialog()
                
            except Exception as e:
                self.add_execution_log("ERROR", f"Maya Standalone 처리 취소 중 오류: {e}")
                # 다이얼로그 정리
                self._cleanup_progress_dialog()
                QtWidgets.QMessageBox.warning(self, "취소 오류", f"Maya Standalone 처리 취소 중 오류가 발생했습니다:\n{str(e)}")
        
        # 취소 버튼 연결
        self.progress_dialog.canceled.connect(on_cancel_clicked)
        self.progress_dialog.show()
        
        # 처리 결과 저장용
        self.processing_results = {
            'total': len(files_to_process),
            'completed': 0,
            'failed': 0,
            'success_files': [],
            'failed_files': [],
            'completion_message_shown': False
        }
        
        # 진행 상황 업데이트 콜백 함수
        def progress_callback(message, current, total):
            # 콜백을 인스턴스 변수로 저장
            self.progress_callback = progress_callback
            # 프로그레스 콜백 메시지를 로그에도 기록
            self.add_execution_log("INFO", f"진행상황: {message} ({current}/{total})")
            
            if hasattr(self, 'progress_dialog') and self.progress_dialog is not None:
                # 진행률 계산
                progress_percent = int((current / total) * 100) if total > 0 else 0
                
                # 메시지 업데이트
                detailed_message = f"{message}\n\n진행률: {current}/{total} ({progress_percent}%)"
                self.progress_dialog.setLabelText(detailed_message)
                self.progress_dialog.setValue(current)
                
                # 처리 완료 시 (한 번만 실행되도록 플래그 체크)
                if current >= total and not self.processing_results['completion_message_shown']:
                    self.processing_results['completion_message_shown'] = True
                    
                    self._cleanup_progress_dialog()
                    
                    # 결과 요약 표시
                    success_count = self.processing_results['completed']
                    failed_count = self.processing_results['failed']
                    
                    # 로그에 최종 결과 기록
                    self.add_execution_log("=" * 50, "처리 완료")
                    self.add_execution_log("SUCCESS", f"총 파일: {total}개")
                    self.add_execution_log("SUCCESS", f"성공: {success_count}개")
                    self.add_execution_log("SUCCESS", f"실패: {failed_count}개")
                    
                    if self.processing_results['success_files']:
                        self.add_execution_log("INFO", "성공한 파일들:")
                        for file in self.processing_results['success_files']:
                            self.add_execution_log("INFO", f"  ✓ {file}")
                    
                    if self.processing_results['failed_files']:
                        self.add_execution_log("WARNING", "실패한 파일들:")
                        for file in self.processing_results['failed_files']:
                            self.add_execution_log("WARNING", f"  ✗ {file}")
                    
                    self.add_execution_log("=" * 50, "처리 완료")
                    
                    result_msg = f"""Maya Standalone 처리가 완료되었습니다!

총 파일: {total}개
성공: {success_count}개
실패: {failed_count}개"""
                    
                    if self.processing_results['success_files']:
                        result_msg += "\n\n성공한 파일들:\n" + "\n".join([f"• {f}" for f in self.processing_results['success_files'][:5]])
                        if len(self.processing_results['success_files']) > 5:
                            result_msg += f"\n... 외 {len(self.processing_results['success_files']) - 5}개"
                    
                    if self.processing_results['failed_files']:
                        result_msg += "\n\n실패한 파일들:\n" + "\n".join([f"• {f}" for f in self.processing_results['failed_files'][:5]])
                        if len(self.processing_results['failed_files']) > 5:
                            result_msg += f"\n... 외 {len(self.processing_results['failed_files']) - 5}개"
                    
                    if failed_count == 0:
                        QtWidgets.QMessageBox.information(self, "처리 완료", result_msg)
                    else:
                        QtWidgets.QMessageBox.warning(self, "처리 완료 (일부 실패)", result_msg)
        
        # 개별 파일 처리 결과 콜백
        def file_result_callback(filename, success):
            if success:
                self.processing_results['completed'] += 1
                self.processing_results['success_files'].append(filename)
                self.add_execution_log("SUCCESS", f"✓ 성공: {filename}")
            else:
                self.processing_results['failed'] += 1
                self.processing_results['failed_files'].append(filename)
                self.add_execution_log("ERROR", f"✗ 실패: {filename}")
        
        try:
            # 백그라운드 처리용 콜백 저장
            self.progress_callback = progress_callback
            self.file_result_callback = file_result_callback
            
            # 백그라운드 처리 시작
            self.add_execution_log("INFO", f"Maya Standalone {processing_type} 처리가 시작되었습니다: {len(files_to_process)}개 파일")
            QtCore.QTimer.singleShot(500, self.process_next_file)
            
        except Exception as e:
            self.add_execution_log("ERROR", f"처리 시작 중 오류가 발생했습니다: {str(e)}")
            self._cleanup_progress_dialog()
            QtWidgets.QMessageBox.critical(self, "오류", f"처리 시작 중 오류가 발생했습니다:\n{str(e)}")
        
        # 처리 완료 후 버튼 상태 업데이트
        self.update_button_states()
        
        # 실행 로그 업데이트
        self.update_execution_log_display()
    
    
    
    def run_maya_standalone_for_files(self, files_to_process, progress_dialog):
        """여러 파일을 개별적으로 Maya Standalone에서 처리"""
        processed_count = 0
        failed_files = []
        
        for i, (filename, file_type) in enumerate(files_to_process):
            # UI 이벤트 처리 (취소 버튼 반응성 향상)
            QtCore.QCoreApplication.processEvents()
            
            # 취소 확인
            if progress_dialog.wasCanceled() or (hasattr(self, 'processing_cancelled') and self.processing_cancelled):
                self.processing_cancelled = True
                self.add_execution_log("WARNING", "사용자에 의해 처리가 취소되었습니다.")
                break
            
            # 진행 상황 업데이트
            progress_dialog.setLabelText(f"처리 중: {filename} ({i+1}/{len(files_to_process)})")
            progress_dialog.setValue(i)
            QtCore.QCoreApplication.processEvents()
            
            # 파일 처리 시작 시간 기록
            try:
                # PySide6
                file_start_time = QtCore.QDateTime.currentDateTime().toMSecsSinceEpoch()
            except AttributeError:
                # PySide2
                file_start_time = QtCore.QDateTime.currentDateTime().msecsSinceEpoch()
            self.add_execution_log("INFO", f"파일 처리 시작: {filename} ({i+1}/{len(files_to_process)})")
            
            try:
                # 개별 파일 처리
                success = self.run_maya_standalone_for_single_file(filename, file_type)
                
                # 파일 처리 후 UI 이벤트 처리 및 취소 확인
                QtCore.QCoreApplication.processEvents()
                if hasattr(self, 'processing_cancelled') and self.processing_cancelled:
                    self.add_execution_log("WARNING", "파일 처리 중 취소됨")
                    break
                
                if success:
                    processed_count += 1
                    self.add_execution_log_with_duration("SUCCESS", f"파일 처리 완료: {filename}", file_start_time)
                else:
                    failed_files.append(filename)
                    self.add_execution_log_with_duration("ERROR", f"파일 처리 실패: {filename}", file_start_time)
                    
            except Exception as e:
                failed_files.append(filename)
                self.add_execution_log("ERROR", f"파일 처리 중 오류: {filename} - {e}")
                print(f"파일 처리 오류: {filename} - {e}")
        
        # 최종 진행 상황 업데이트
        progress_dialog.setValue(len(files_to_process))
        
        # 결과 요약 (처리 시간은 상위 함수에서 표시되므로 여기서는 간단한 요약만)
        if self.processing_cancelled:
            return False
        elif processed_count > 0:
            if failed_files:
                self.add_execution_log("WARNING", f"처리 완료: {processed_count}개 성공, {len(failed_files)}개 실패")
            else:
                self.add_execution_log("SUCCESS", f"모든 파일 처리 완료: {processed_count}개")
            return True
        else:
            self.add_execution_log("ERROR", "모든 파일 처리에 실패했습니다.")
            return False
    
    
    def generate_maya_standalone_script_for_single_file(self, file_path, filename):
        """단일 파일을 처리하는 Maya Standalone용 스크립트 생성 (백그라운드 최적화)"""
        
        # 안전한 경로 처리 (Unix 스타일 사용)
        safe_file_path = file_path.replace('\\', '/')
        
        # Python 파일 정보 처리
        python_file_abs_path = os.path.abspath(self.selected_python_file)
        python_file_dir = os.path.dirname(python_file_abs_path).replace('\\', '/')
        python_file_name = os.path.splitext(os.path.basename(python_file_abs_path))[0]
        safe_function_name = self.selected_function
        
        # 출력 폴더 처리
        output_folder = self.output_folder or ''
        safe_output_folder = output_folder.replace('\\', '/') if output_folder else ''
        
        # 로그 파일 경로 생성
        log_dir = os.path.join(tempfile.gettempdir(), 'maya_standalone_logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"{filename}_{int(time.time())}.log").replace('\\', '/')
        
        # 진행 상황 파일 경로
        progress_file_path = os.path.join(log_dir, f"{filename}_progress.json").replace('\\', '/')
        
        # 스크립트 내용을 개별 변수로 구성하여 f-string 문제 해결
        script_parts = {
            'safe_file_path': safe_file_path,
            'filename': filename,
            'python_file_dir': python_file_dir,
            'python_file_name': python_file_name,
            'safe_function_name': safe_function_name,
            'safe_output_folder': safe_output_folder,
            'log_file_path': log_file_path,
            'progress_file_path': progress_file_path
        }
        
        script_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Maya Standalone 백그라운드 처리 스크립트
파일: ''' + script_parts['safe_file_path'] + '''
Python 파일: ''' + script_parts['python_file_name'] + '''
함수: ''' + script_parts['safe_function_name'] + '''
로그 파일: ''' + script_parts['log_file_path'] + '''
"""

import sys
import os
import json
import traceback
import time
from datetime import datetime

# 전역 변수 설정
FILENAME = "''' + script_parts['filename'] + '''"
PYTHON_FILE_DIR = r"''' + script_parts['python_file_dir'] + '''"
PYTHON_FILE_NAME = "''' + script_parts['python_file_name'] + '''"
FUNCTION_NAME = "''' + script_parts['safe_function_name'] + '''"
FILE_PATH = r"''' + script_parts['safe_file_path'] + '''"
OUTPUT_FOLDER = r"''' + script_parts['safe_output_folder'] + '''"
LOG_FILE = r"''' + script_parts['log_file_path'] + '''"
PROGRESS_FILE = r"''' + script_parts['progress_file_path'] + '''"

def write_log(message, log_type="INFO"):
    """로그 파일과 콘솔에 메시지 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {log_type}: {message}"
    
    # 콘솔 출력
    print(log_message)
    
    # 파일 출력
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message + "\\n")
    except Exception as e:
        print(f"로그 파일 쓰기 실패: {e}")

def update_progress(status, message="", progress=0, error_msg=""):
    """진행 상황 업데이트"""
    progress_data = {
        'status': status,
        'message': message,
        'progress': progress,
        'error_msg': error_msg,
        'timestamp': datetime.now().isoformat(),
        'filename': FILENAME
    }
    
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        write_log(f"진행 상황 업데이트: {status} - {message} ({progress}%)")
    except Exception as e:
        write_log(f"진행 상황 업데이트 실패: {e}", "ERROR")

def main():
    """메인 처리 함수"""
    write_log("=== Maya Standalone 백그라운드 처리 시작 ===")
    write_log(f"처리할 파일: {FILE_PATH}")
    write_log(f"Python 파일: {PYTHON_FILE_NAME}")
    write_log(f"실행할 함수: {FUNCTION_NAME}")
    write_log(f"출력 폴더: {OUTPUT_FOLDER}")
    
    update_progress("starting", "Maya Standalone 초기화 준비 중...", 5)
    
    try:
        # 1. Python 경로 설정
        write_log(f"Python 경로 추가: {PYTHON_FILE_DIR}")
        update_progress("initializing", "Python 경로 설정 중...", 10)
        
        if not os.path.exists(PYTHON_FILE_DIR):
            error_msg = f"Python 파일 디렉토리가 존재하지 않습니다: {PYTHON_FILE_DIR}"
            write_log(error_msg, "ERROR")
            update_progress("error", error_msg, 0, error_msg)
            return False
        
        if PYTHON_FILE_DIR not in sys.path:
            sys.path.insert(0, PYTHON_FILE_DIR)
            write_log(f"Python 경로 추가 완료: {PYTHON_FILE_DIR}")
        
        write_log(f"현재 Python 경로: {sys.path[:3]}")
        
        # 2. Maya 초기화
        write_log("Maya Standalone 초기화 중...")
        update_progress("initializing", "Maya Standalone 초기화 중...", 20)
        
        try:
            import maya.standalone
            maya.standalone.initialize(name='python')
            write_log("Maya Standalone 초기화 완료")
            update_progress("initialized", "Maya Standalone 초기화 완료", 30)
        except Exception as maya_init_error:
            error_msg = f"Maya Standalone 초기화 실패: {maya_init_error}"
            write_log(error_msg, "ERROR")
            write_log(traceback.format_exc(), "ERROR")
            update_progress("error", error_msg, 0, error_msg)
            return False
        
        # 3. Maya 모듈 임포트
        try:
            from maya import cmds
            write_log("Maya cmds 모듈 임포트 완료")
            update_progress("loading", "Maya 모듈 로드 완료", 35)
        except Exception as cmds_import_error:
            error_msg = f"Maya cmds 임포트 실패: {cmds_import_error}"
            write_log(error_msg, "ERROR")
            update_progress("error", error_msg, 0, error_msg)
            return False
        
        # 4. 커스텀 Python 모듈 임포트
        write_log(f"커스텀 모듈 임포트 시도: {PYTHON_FILE_NAME}")
        update_progress("importing", f"모듈 임포트: {PYTHON_FILE_NAME}", 40)
        
        custom_module = None
        try:
            # importlib를 사용한 안전한 모듈 임포트
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                PYTHON_FILE_NAME, 
                os.path.join(PYTHON_FILE_DIR, PYTHON_FILE_NAME + '.py')
            )
            
            if spec is None:
                error_msg = f"모듈 스펙을 찾을 수 없습니다: {PYTHON_FILE_NAME}"
                write_log(error_msg, "ERROR")
                update_progress("error", error_msg, 0, error_msg)
                return False
            
            custom_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(custom_module)
            
            write_log(f"모듈 임포트 성공: {PYTHON_FILE_NAME}")
            
            # 모듈 속성 확인
            available_attrs = [attr for attr in dir(custom_module) if not attr.startswith('_')]
            write_log(f"모듈 속성들: {available_attrs}")
            
            update_progress("imported", f"모듈 임포트 완료: {PYTHON_FILE_NAME}", 45)
            
        except Exception as import_error:
            error_msg = f"모듈 임포트 실패: {import_error}"
            write_log(error_msg, "ERROR")
            write_log(traceback.format_exc(), "ERROR")
            
            # 대안으로 기본 import 시도
            try:
                write_log("대안 import 시도...")
                custom_module = __import__(PYTHON_FILE_NAME)
                write_log(f"대안 import 성공: {PYTHON_FILE_NAME}")
            except Exception as alt_import_error:
                error_msg = f"대안 import도 실패: {alt_import_error}"
                write_log(error_msg, "ERROR")
                update_progress("error", error_msg, 0, error_msg)
                return False
        
        # 5. 함수 존재 확인
        if not hasattr(custom_module, FUNCTION_NAME):
            available_funcs = [attr for attr in dir(custom_module) 
                             if not attr.startswith('_') and callable(getattr(custom_module, attr))]
            error_msg = f"함수 '{FUNCTION_NAME}'을 찾을 수 없습니다. 사용 가능한 함수: {available_funcs}"
            write_log(error_msg, "ERROR")
            update_progress("error", error_msg, 0, error_msg)
            return False
        
        target_function = getattr(custom_module, FUNCTION_NAME)
        write_log(f"함수 발견: {FUNCTION_NAME}")
        update_progress("function_found", f"함수 발견: {FUNCTION_NAME}", 50)
        
        # 6. 파일 존재 확인
        if not os.path.exists(FILE_PATH):
            error_msg = f"처리할 파일이 존재하지 않습니다: {FILE_PATH}"
            write_log(error_msg, "ERROR")
            update_progress("error", error_msg, 0, error_msg)
            return False
        
        # 7. Maya 파일 열기
        write_log(f"Maya 파일 열기: {FILE_PATH}")
        update_progress("opening", "Maya 파일 열기 중...", 60)
        
        try:
            # 새 씬으로 시작
            cmds.file(new=True, force=True)
            write_log("새 씬 생성 완료")
            
            # 파일 열기
            cmds.file(FILE_PATH, open=True, force=True)
            write_log(f"파일 열기 완료: {FILENAME}")
            
            # 씬 정보 확인
            scene_objects = cmds.ls(dag=True, long=True)
            write_log(f"씬 오브젝트 개수: {len(scene_objects)}")
            
            update_progress("opened", "Maya 파일 열기 완료", 70)
            
        except Exception as open_error:
            error_msg = f"파일 열기 실패: {open_error}"
            write_log(error_msg, "ERROR")
            write_log(traceback.format_exc(), "ERROR")
            update_progress("error", error_msg, 0, error_msg)
            return False
        
        # 8. 커스텀 함수 실행
        write_log(f"함수 실행 시작: {FUNCTION_NAME}")
        update_progress("processing", f"함수 실행 중: {FUNCTION_NAME}", 80)
        
        try:
            function_start_time = time.time()
            target_function()
            function_end_time = time.time()
            
            execution_time = function_end_time - function_start_time
            write_log(f"함수 실행 완료: {FUNCTION_NAME} (실행시간: {execution_time:.2f}초)")
            update_progress("processed", f"함수 실행 완료: {FUNCTION_NAME}", 90)
            
        except Exception as func_error:
            error_msg = f"함수 실행 실패: {func_error}"
            write_log(error_msg, "ERROR")
            write_log(traceback.format_exc(), "ERROR")
            update_progress("error", error_msg, 0, error_msg)
            return False
        
        # 9. 파일 저장
        write_log("파일 저장 시작")
        update_progress("saving", "파일 저장 중...", 95)
        
        try:
            if OUTPUT_FOLDER and os.path.exists(os.path.dirname(OUTPUT_FOLDER)) if OUTPUT_FOLDER else False:
                # 출력 폴더에 저장
                if not os.path.exists(OUTPUT_FOLDER):
                    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
                    write_log(f"출력 폴더 생성: {OUTPUT_FOLDER}")
                
                output_filename = os.path.basename(FILE_PATH)
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                
                write_log(f"출력 폴더에 저장: {output_path}")
                cmds.file(rename=output_path)
                cmds.file(save=True, force=True)
                write_log(f"파일 저장 완료: {output_path}")
                
            else:
                # 원본 위치에 저장
                write_log(f"원본 위치에 저장: {FILE_PATH}")
                cmds.file(save=True, force=True)
                write_log(f"파일 저장 완료: {FILENAME}")
            
            update_progress("completed", "처리 완료", 100)
            
        except Exception as save_error:
            error_msg = f"파일 저장 실패: {save_error}"
            write_log(error_msg, "ERROR")
            write_log(traceback.format_exc(), "ERROR")
            update_progress("error", error_msg, 0, error_msg)
            return False
        
        # 10. 성공 완료
        write_log("=== 파일 처리 성공 완료 ===")
        return True
        
    except Exception as main_error:
        error_msg = f"메인 처리 중 예상치 못한 오류: {main_error}"
        write_log(error_msg, "ERROR")
        write_log(traceback.format_exc(), "ERROR")
        update_progress("error", error_msg, 0, error_msg)
        return False
    
    finally:
        # Maya 종료
        try:
            write_log("Maya Standalone 종료 중...")
            import maya.standalone
            maya.standalone.uninitialize()
            write_log("Maya Standalone 종료 완료")
        except Exception as uninit_error:
            write_log(f"Maya 종료 중 오류: {uninit_error}", "WARNING")

# 메인 실행
if __name__ == "__main__":
    try:
        success = main()
        if success:
            write_log("프로세스 정상 완료 - 종료 코드: 0")
            sys.exit(0)
        else:
            write_log("프로세스 실패 완료 - 종료 코드: 1")
            sys.exit(1)
    except Exception as script_error:
        write_log(f"스크립트 실행 중 치명적 오류: {script_error}", "ERROR")
        write_log(traceback.format_exc(), "ERROR")
        update_progress("error", f"스크립트 오류: {script_error}", 0, str(script_error))
        sys.exit(1)
'''
        
        return script_content, log_file_path, progress_file_path
    
    def generate_maya_standalone_script_for_files(self, files_to_process):
        """여러 파일을 처리하는 Maya Standalone용 스크립트 생성"""
        # 파일 경로들을 안전하게 처리
        safe_file_paths = []
        for filename, file_type in files_to_process:
            file_path = os.path.join(self.file_folder, filename)
            if os.path.exists(file_path):
                safe_file_path = file_path.replace('\\', '\\\\')
                safe_file_paths.append((safe_file_path, filename, file_type))
        
        if not safe_file_paths:
            return ""
        
        # 선택된 Python 파일과 함수 정보 (필수)
        python_file_dir = os.path.dirname(self.selected_python_file)
        safe_python_file_dir = python_file_dir.replace('\\', '\\\\')
        python_file_name = os.path.splitext(os.path.basename(self.selected_python_file))[0]
        safe_python_file_name = python_file_name.replace('\\', '\\\\')
        safe_function_name = self.selected_function.replace('\\', '\\\\')
        
        # 파일 처리 루프 생성
        file_processing_loop = ""
        for i, (safe_file_path, filename, file_type) in enumerate(safe_file_paths):
            file_processing_loop += f'''
    # 파일 {i+1}/{len(safe_file_paths)}: {filename}
    filename = "{filename}"
    try:
        file_path = r"{safe_file_path}"
        print(f"파일 열기: {{file_path}}")
        cmds.file(file_path, open=True, force=True)
        
        # 선택된 함수 실행
        if hasattr(custom_func, '{safe_function_name}'):
            func = getattr(custom_func, '{safe_function_name}')
            print(f"함수 {safe_function_name} 실행 중... ({{filename}})")
            func()
            print(f"함수 {safe_function_name} 실행 완료 ({{filename}})")
        else:
            print(f"함수 {safe_function_name}을 찾을 수 없습니다.")
        
        # 파일 저장
        print(f"파일 저장: {{file_path}}")
        cmds.file(save=True, force=True)
        print(f"파일 저장 완료: {{filename}}")
        
    except Exception as file_error:
        print(f"파일 처리 중 오류: {{filename}} - {{file_error}}")
        import traceback
        print(traceback.format_exc())
'''
        
        script_content = f'''"""
Maya Standalone 스크립트 - 여러 파일 처리
총 {len(safe_file_paths)}개 파일 처리
Python 파일: {safe_python_file_name}
함수: {safe_function_name}
"""

import sys
import os

# 선택된 Python 파일의 디렉토리를 Python 경로에 추가
python_file_dir = r"{safe_python_file_dir}"
if python_file_dir not in sys.path:
    sys.path.insert(0, python_file_dir)

# Maya 모듈 초기화
import maya.standalone
maya.standalone.initialize()

try:
    from maya import cmds
    
    # 선택된 Python 모듈에서 함수 임포트
    try:
        import {safe_python_file_name} as custom_func
        print(f"{safe_python_file_name} 모듈 임포트 성공")
        
    except ImportError as import_error:
        print(f"모듈 임포트 실패: {{import_error}}")
        custom_func = None
    
    # 각 파일 처리
    print(f"총 {len(safe_file_paths)}개 파일 처리 시작...")
    {file_processing_loop}
    
    print("모든 파일 처리 완료!")
    
except Exception as e:
    print(f"스크립트 실행 중 오류: {{e}}")
    import traceback
    print(traceback.format_exc())
finally:
    # Maya 종료
    maya.standalone.uninitialize()
'''
        
        return script_content
    
    def get_current_maya_version(self):
        """현재 실행 중인 Maya 버전을 반환"""
        try:
            import maya.cmds as cmds
            version = cmds.about(version=True)
            print(f"현재 Maya 버전: {version}")
            return version
        except ImportError:
            print("Maya 모듈을 가져올 수 없습니다.")
            return None
        except Exception as e:
            print(f"Maya 버전 확인 중 오류: {e}")
            return None
    
    def get_current_maya_standalone(self):
        """현재 Maya 버전의 Standalone 실행 파일 경로 반환"""
        try:
            import maya.cmds as cmds
            # 현재 Maya 버전 가져오기
            version = cmds.about(version=True)
            print(f"현재 Maya 버전: {version}")
            
            # 버전에서 연도 추출 (예: "2024" from "2024.0")
            version_year = version.split('.')[0]
            
            # 일반적인 Maya Standalone 설치 경로들
            maya_standalone_paths = [
                rf"C:\\Program Files\\Autodesk\\Maya{version_year}\\bin\\mayapy.exe",
                rf"C:\\Program Files\\Autodesk\\Maya{version_year}\\bin\\maya.exe",
            ]
            
            for path in maya_standalone_paths:
                if os.path.exists(path):
                    print(f"Maya Standalone 실행 파일 찾음: {path}")
                    return path
            
            # 환경변수에서 Maya 경로 찾기
            maya_path = os.environ.get('MAYA_LOCATION')
            if maya_path:
                maya_standalone = os.path.join(maya_path, 'bin', 'mayapy.exe')
                if os.path.exists(maya_standalone):
                    print(f"환경변수에서 Maya Standalone 찾음: {maya_standalone}")
                    return maya_standalone
                
                maya_exe = os.path.join(maya_path, 'bin', 'maya.exe')
                if os.path.exists(maya_exe):
                    print(f"환경변수에서 Maya 실행 파일 찾음: {maya_exe}")
                    return maya_exe
            
            print(f"Maya {version_year} Standalone 실행 파일을 찾을 수 없습니다.")
            return None
            
        except ImportError:
            print("Maya 모듈을 가져올 수 없습니다.")
            return None
        except Exception as e:
            print(f"Maya Standalone 경로 확인 중 오류: {e}")
            return None
    
    def load_config(self):
        """설정 로드"""
        try:
            if os.path.exists(CONFIG_FILE_PATH):
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.file_folder = config.get('file_folder', '')
                self.rig_folder = config.get('rig_folder', '')
                self.output_folder = config.get('output_folder', '')
                self.selected_python_file = config.get('selected_python_file', '')
                self.selected_function = config.get('selected_function', '')
                
                if self.file_folder:
                    self.file_folder_line_edit.setText(self.file_folder)
                    self.refresh_files()
                
                if self.rig_folder:
                    self.rig_folder_line_edit.setText(self.rig_folder)
                
                if self.output_folder:
                    self.output_folder_line_edit.setText(self.output_folder)
                
                if self.selected_python_file:
                    self.python_file_line_edit.setText(self.selected_python_file)
                    self.refresh_functions()
                    
                if self.selected_function:
                    index = self.function_combo.findText(self.selected_function)
                    if index >= 0:
                        self.function_combo.setCurrentIndex(index)
                    
        except Exception as e:
            print(f"설정 로드 중 오류: {e}")
    
    def save_config(self):
        """설정 저장"""
        try:
            config = {
                'file_folder': self.file_folder or '',
                'rig_folder': self.rig_folder or '',
                'output_folder': self.output_folder or '',
                'selected_python_file': self.selected_python_file or '',
                'selected_function': self.selected_function or ''
            }
            
            with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"설정 저장 중 오류: {e}")
    
    def update_execution_log_display(self):
        """실행 로그 텍스트 창 업데이트"""
        if not self.execution_logs:
            self.execution_log_text.clear()
            self.execution_log_text.setPlaceholderText("실행 로그가 여기에 표시됩니다...")
            return
        
        # 실행 로그를 텍스트로 변환
        log_text = ""
        for log in self.execution_logs:
            timestamp = log['timestamp']
            log_type = log['log_type']
            message = log['message']
            
            # 로그 타입에 따른 색상 구분 (텍스트로)
            if log_type == "ERROR":
                log_text += f"[{timestamp}] ERROR: {message}\n"
            elif log_type == "WARNING":
                log_text += f"[{timestamp}] WARNING: {message}\n"
            elif log_type == "SUCCESS":
                log_text += f"[{timestamp}] SUCCESS: {message}\n"
            else:  # INFO
                log_text += f"[{timestamp}] INFO: {message}\n"
        
        self.execution_log_text.setPlainText(log_text)
        
        # 스크롤을 맨 아래로 이동
        cursor = self.execution_log_text.textCursor()
        try:
            # PySide6
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        except AttributeError:
            # PySide2
            cursor.movePosition(cursor.End)
        self.execution_log_text.setTextCursor(cursor)
    
    def add_execution_log(self, log_type, message):
        """실행 로그 추가"""
        execution_log = {
            'log_type': log_type,
            'message': message,
            'timestamp': QtCore.QDateTime.currentDateTime().toString('hh:mm:ss')
        }
        self.execution_logs.append(execution_log)
        self.update_execution_log_display()
    
    def add_execution_log_with_duration(self, log_type, message, start_time=None):
        """실행 로그 추가 (처리 시간 포함)"""
        if start_time:
            try:
                # PySide6
                current_time = QtCore.QDateTime.currentDateTime().toMSecsSinceEpoch()
            except AttributeError:
                # PySide2
                current_time = QtCore.QDateTime.currentDateTime().msecsSinceEpoch()
            
            duration = current_time - start_time
            duration_seconds = duration / 1000.0
            if duration_seconds < 1:
                duration_text = f"{duration}ms"
            else:
                duration_text = f"{duration_seconds:.1f}초"
            message_with_duration = f"{message} (처리 시간: {duration_text})"
        else:
            message_with_duration = message
            
        self.add_execution_log(log_type, message_with_duration)
    
    def process_next_file(self):
        """다음 파일을 처리합니다. (개선된 백그라운드 처리 방식)"""
        # 취소 상태 확인
        if self.is_cancelled:
            print("Maya Standalone 처리가 취소되어 중단됩니다.")
            return
            
        if self.current_index >= len(self.file_queue):
            # 모든 파일 처리 완료
            if self.progress_callback:
                self.progress_callback("모든 파일 처리 완료", len(self.file_queue), len(self.file_queue))
            return
        
        # 현재 처리할 파일
        current_file = self.file_queue[self.current_index]
        filename, file_type = current_file
        
        # 진행 상황 업데이트
        if self.progress_callback:
            self.progress_callback(f"처리 중: {filename}", self.current_index, len(self.file_queue))
        
        # 백그라운드 프로세스 시작 (동기 처리)
        success = self.background_process_single_file(filename, file_type)
        
        # 결과 처리
        if self.file_result_callback:
            self.file_result_callback(filename, success)
        
        # 다음 파일 처리
        self.current_index += 1
        QtCore.QTimer.singleShot(100, self.process_next_file)  # 짧은 지연 후 다음 파일 처리
    
    def background_process_single_file(self, filename, file_type):
        """백그라운드에서 단일 파일 처리 (개선된 버전)"""
        if self.is_cancelled:
            return False
            
        try:
            # 파일 경로 구성
            file_path = os.path.join(self.file_folder, filename)
            if not os.path.exists(file_path):
                self.add_execution_log("ERROR", f"파일이 존재하지 않습니다: {file_path}")
                return False
            
            # 스크립트 생성
            self.add_execution_log("INFO", f"백그라운드 스크립트 생성: {filename}")
            script_content, log_file, progress_file = self.generate_maya_standalone_script_for_single_file(file_path, filename)
            
            # 임시 스크립트 파일 생성
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_script:
                temp_script.write(script_content)
                temp_script_path = temp_script.name
            
            self.add_execution_log("INFO", f"임시 스크립트 생성: {temp_script_path}")
            
            # Maya 실행 파일 확인
            maya_executable = self.get_current_maya_standalone()
            if not maya_executable:
                self.add_execution_log("ERROR", "Maya Standalone 실행 파일을 찾을 수 없습니다.")
                os.unlink(temp_script_path)
                return False
            
            # 실행 명령어 구성
            if maya_executable.endswith('mayapy.exe'):
                cmd = [maya_executable, temp_script_path]
            else:
                cmd = [maya_executable, '-batch', '-command', f'python("exec(open(r\\"{temp_script_path}\\").read())")']
            
            self.add_execution_log("INFO", f"실행 명령어: {' '.join(cmd)}")
            
            # 완전 백그라운드 실행 설정
            creationflags = 0
            if platform.system() == "Windows":
                creationflags = (
                    subprocess.CREATE_NO_WINDOW |
                    subprocess.CREATE_NEW_PROCESS_GROUP |
                    subprocess.DETACHED_PROCESS
                )
            
            # 프로세스 시작
            start_time = time.time()
            self.add_execution_log("INFO", f"백그라운드 프로세스 시작: {filename}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                creationflags=creationflags,
                cwd=tempfile.gettempdir()
            )
            
            self.add_execution_log("INFO", f"프로세스 시작됨 - PID: {process.pid}")
            
            # 프로세스 완료 대기 (타임아웃: 10분)
            try:
                stdout, stderr = process.communicate(timeout=600)
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                # 결과 처리
                if process.returncode == 0:
                    self.add_execution_log("SUCCESS", f"백그라운드 처리 완료: {filename} ({elapsed_time:.1f}초)")
                    
                    # 로그 파일에서 중요 정보 추출
                    if os.path.exists(log_file):
                        try:
                            with open(log_file, 'r', encoding='utf-8') as f:
                                log_content = f.read()
                                # 성공/에러 라인만 추출
                                for line in log_content.split('\n'):
                                    if any(keyword in line for keyword in ['완료', '성공', '실패', 'ERROR', 'SUCCESS']):
                                        if line.strip():
                                            self.add_execution_log("INFO", f"Maya Log: {line.strip()}")
                        except Exception:
                            pass
                    
                    success = True
                else:
                    self.add_execution_log("ERROR", f"백그라운드 처리 실패: {filename} (코드: {process.returncode}, {elapsed_time:.1f}초)")
                    
                    # 에러 정보 로깅
                    if stderr:
                        self.add_execution_log("ERROR", f"Maya 에러: {stderr.strip()}")
                    if stdout:
                        self.add_execution_log("INFO", f"Maya 출력: {stdout.strip()}")
                    
                    success = False
                    
            except subprocess.TimeoutExpired:
                self.add_execution_log("ERROR", f"백그라운드 처리 타임아웃: {filename}")
                process.kill()
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
                success = False
            
            # 임시 파일 정리
            try:
                if os.path.exists(temp_script_path):
                    os.unlink(temp_script_path)
            except Exception as e:
                self.add_execution_log("WARNING", f"임시 파일 삭제 실패: {e}")
            
            return success
            
        except Exception as e:
            self.add_execution_log("ERROR", f"백그라운드 처리 설정 오류: {filename} - {e}")
            return False
    
    
    def cancel_processing(self):
        """Maya Standalone 처리를 취소합니다."""
        print("Maya Standalone 처리 취소 요청...")
        self.is_cancelled = True
        self.processing_cancelled = True
        
        # 타이머 중지
        if hasattr(self, 'check_process_timer') and self.check_process_timer:
            self.check_process_timer.stop()
            self.check_process_timer = None
            print("프로세스 모니터링 타이머 중지됨")
        
        # 현재 실행 중인 프로세스 종료
        if hasattr(self, 'current_process') and self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=5)
            except Exception:
                try:
                    self.current_process.kill()
                except Exception:
                    pass
            self.current_process = None
            print("현재 실행 중인 프로세스 종료됨")
        
        # 임시 파일 정리
        if hasattr(self, 'current_file_info') and self.current_file_info:
            temp_script = self.current_file_info.get('temp_script')
            if temp_script and os.path.exists(temp_script):
                try:
                    os.unlink(temp_script)
                except Exception as e:
                    print(f"임시 파일 삭제 오류: {e}")
            self.current_file_info = None
        
        # 취소 콜백 호출
        if hasattr(self, 'progress_callback') and self.progress_callback:
            self.progress_callback("Maya Standalone 처리가 취소되었습니다.", 0, 0)
        
        print("Maya Standalone 처리 취소 완료")
    
    def _cleanup_progress_dialog(self):
        """프로그레스 다이얼로그를 안전하게 정리합니다."""
        if hasattr(self, 'progress_dialog') and self.progress_dialog is not None:
            try:
                # 시그널 연결 해제 (C++ 객체가 삭제되기 전에)
                try:
                    self.progress_dialog.canceled.disconnect()
                except (RuntimeError, AttributeError):
                    # 이미 연결이 해제되었거나 객체가 삭제된 경우
                    pass
                
                # 다이얼로그 숨기기 및 닫기
                if hasattr(self.progress_dialog, 'hide'):
                    self.progress_dialog.hide()
                
                if hasattr(self.progress_dialog, 'close'):
                    self.progress_dialog.close()
                
                # deleteLater 호출 (Qt의 안전한 삭제 방식)
                if hasattr(self.progress_dialog, 'deleteLater'):
                    self.progress_dialog.deleteLater()
                    
            except (RuntimeError, AttributeError) as e:
                # Qt 객체가 이미 삭제된 경우 발생하는 오류 무시
                self.add_execution_log("WARNING", f"다이얼로그 정리 중 Qt 객체 오류 (무시됨): {e}")
            except Exception as e:
                # 기타 예상치 못한 오류
                self.add_execution_log("ERROR", f"다이얼로그 정리 중 오류: {e}")
            finally:
                # 참조 제거
                self.progress_dialog = None
    
    
    def monitor_background_progress(self):
        """백그라운드 처리 진행 상황 실시간 모니터링"""
        if not hasattr(self, 'active_progress_files'):
            self.active_progress_files = {}
        
        # 활성 진행 파일들 확인
        for filename, progress_file in list(self.active_progress_files.items()):
            try:
                if os.path.exists(progress_file):
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        progress_data = json.load(f)
                    
                    status = progress_data.get('status', 'unknown')
                    message = progress_data.get('message', '')
                    progress_percent = progress_data.get('progress', 0)
                    
                    # UI 업데이트
                    if hasattr(self, 'progress_dialog') and self.progress_dialog:
                        detailed_message = f"처리 중: {filename}\n상태: {message}\n진행률: {progress_percent}%"
                        self.progress_dialog.setLabelText(detailed_message)
                    
                    # 완료 또는 에러 시 정리
                    if status in ['completed', 'error']:
                        if status == 'completed':
                            self.add_execution_log("SUCCESS", f"백그라운드 완료 확인: {filename}")
                        else:
                            error_msg = progress_data.get('error_msg', '알 수 없는 오류')
                            self.add_execution_log("ERROR", f"백그라운드 에러 확인: {filename} - {error_msg}")
                        
                        del self.active_progress_files[filename]
                        
            except Exception as e:
                self.add_execution_log("WARNING", f"진행 상황 모니터링 오류: {filename} - {e}")
    
    def clear_execution_logs(self):
        """실행 로그 지우기"""
        if not self.execution_logs:
            QtWidgets.QMessageBox.information(self, "Clear Log", "지울 실행 로그가 없습니다.")
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, "Clear Log", 
            "모든 실행 로그를 지우시겠습니까?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.execution_logs.clear()
            self.update_execution_log_display()
            QtWidgets.QMessageBox.information(self, "완료", "실행 로그가 지워졌습니다.")
    

# =============================================================================
# UI 생성 및 표시 함수
# =============================================================================

def show_ui():
    """UI 표시 함수"""
    global maya_standalone_processor_window
    try:
        maya_standalone_processor_window.close()
        maya_standalone_processor_window.deleteLater()
    except (NameError, AttributeError, RuntimeError):
        pass
    
    maya_standalone_processor_window = MayaStandaloneProcessorUI()
    maya_standalone_processor_window.show()
    
    return maya_standalone_processor_window

if __name__ == "__main__":
    show_ui()
