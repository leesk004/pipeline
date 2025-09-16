import os
import json
from maya import cmds, mel
import maya.OpenMayaUI as omui

# Maya 버전에 따른 PySide 모듈 임포트 개선
maya_version = mel.eval('getApplicationVersionAsFloat()')
try:
    if maya_version >= 2025.0:
        from PySide6 import QtWidgets, QtCore
        from shiboken6 import wrapInstance
        print("PySide6를 사용합니다.")
    else:
        from PySide2 import QtWidgets, QtCore
        from shiboken2 import wrapInstance
        print("PySide2를 사용합니다.")
except ImportError as e:
    print(f"PySide 모듈 임포트 오류: {e}")
    try:
        from PySide2 import QtWidgets, QtCore
        from shiboken2 import wrapInstance
        print("PySide2로 fallback 성공")
    except ImportError:
        try:
            from PySide6 import QtWidgets, QtCore
            from shiboken6 import wrapInstance
            print("PySide6로 fallback 성공")
        except ImportError:
            raise ImportError("PySide2 또는 PySide6를 찾을 수 없습니다.")

# 의존 모듈들을 안전하게 임포트
try:
    import R8_MaxtoMaya.R8_ani_skeleton_match as R8_ani_skeleton_match
    import R8_MaxtoMaya.R8_ani_batch_process as R8_ani_batch_process
    import R8_MaxtoMaya.R8_ani_reference_remove as R8_ani_reference_remove
    from importlib import reload
    reload(R8_ani_skeleton_match)
    reload(R8_ani_batch_process)
    reload(R8_ani_reference_remove)
    print("모든 의존 모듈이 성공적으로 로드되었습니다.")
except ImportError as e:
    print(f"의존 모듈 임포트 오류: {e}")
    print("일부 기능이 제한될 수 있습니다.")
    # 더미 모듈 생성 (UI는 실행되지만 해당 기능은 작동하지 않음)
    class DummyModule:
        """
        더미 모듈 클래스 - 의존 모듈이 없을 때 대체용
        
        실제 모듈을 임포트할 수 없을 때 프로그램이 중단되지 않도록 
        같은 이름의 메서드들을 제공하는 가짜 모듈입니다.
        
        @staticmethod 데코레이터를 사용하는 이유:
        1. 인스턴스를 생성하지 않고도 메서드를 호출할 수 있음
        2. 클래스 변수나 인스턴스 변수에 접근할 필요가 없음
        3. 실제 모듈의 함수들과 동일한 방식으로 호출 가능
        4. 메모리 효율적 (self 파라미터가 필요없음)
        """
        
        @staticmethod
        def skeleton_control_match(*args, **kwargs):
            """스켈레톤 컨트롤 매치 더미 함수"""
            print("경고: R8_ani_skeleton_match 모듈이 없어 skeleton_control_match 실행할 수 없습니다.")
        
        @staticmethod
        def control_bake(*args, **kwargs):
            """컨트롤 베이크 더미 함수"""
            print("경고: R8_ani_skeleton_match 모듈이 없어 control_bake 실행할 수 없습니다.")
        
        @staticmethod
        def delete_constraint(*args, **kwargs):
            """제약 삭제 더미 함수"""
            print("경고: R8_ani_skeleton_match 모듈이 없어 delete_constraint 실행할 수 없습니다.")
        
        @staticmethod
        def delete_key_control(*args, **kwargs):
            """키 삭제 더미 함수"""
            print("경고: R8_ani_skeleton_match 모듈이 없어 delete_key_control 실행할 수 없습니다.")
        
        @staticmethod
        def start_batch_process(*args, **kwargs):
            """배치 프로세스 시작 더미 함수"""
            print("경고: R8_ani_batch_process 모듈이 없어 start_batch_process 실행할 수 없습니다.")
        
        @staticmethod
        def cancel_batch_process(*args, **kwargs):
            """배치 프로세스 취소 더미 함수"""
            print("경고: R8_ani_batch_process 모듈이 없어 cancel_batch_process 실행할 수 없습니다.")
        
        @staticmethod
        def remove_all_animation_references(*args, **kwargs):
            """애니메이션 레퍼런스 제거 더미 함수"""
            print("경고: R8_ani_reference_remove 모듈이 없어 remove_all_animation_references 실행할 수 없습니다.")
    
    # 더미 모듈 인스턴스 생성 - 실제 모듈처럼 사용 가능
    R8_ani_skeleton_match = DummyModule()
    R8_ani_batch_process = DummyModule()
    R8_ani_reference_remove = DummyModule()

# 상수 정의 - OS 호환성 개선
IMPORTER_NAME = 'Ani FBX Importer'
DEFAULT_FOLDER_PATH = r''

# JSON 파일 경로를 사용자 홈 디렉토리 또는 Maya 설정 디렉토리로 변경
try:
    # Maya 설정 디렉토리 사용 (더 안전함)
    maya_app_dir = cmds.internalVar(userAppDir=True)
    JSON_FILE_PATH = os.path.join(maya_app_dir, 'ani_fbx_set.json')
except:
    # fallback: 사용자 홈 디렉토리 사용
    home_dir = os.path.expanduser('~')
    JSON_FILE_PATH = os.path.join(home_dir, 'ani_fbx_set.json')

# OS 호환 파일/폴더 열기 함수
def open_file_or_folder(path):
    """OS에 맞게 파일이나 폴더를 엽니다."""
    import platform
    system = platform.system()
    
    try:
        if system == 'Windows':
            os.startfile(path)
        elif system == 'Darwin':  # macOS
            os.system(f'open "{path}"')
        else:  # Linux
            os.system(f'xdg-open "{path}"')
    except Exception as e:
        print(f"파일/폴더 열기 오류: {e}")

# 유틸리티 함수
def get_maya_main_window():
    """Maya 메인 윈도우를 반환합니다."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

def time_change_set():
    """시간 단위를 60fps로 설정합니다."""
    cmds.currentUnit(time='ntscf')

class FbxImporterUI(QtWidgets.QDialog):
    """FBX 임포터 UI 클래스"""
    
    def __init__(self, parent=get_maya_main_window()):
        super(FbxImporterUI, self).__init__(parent)
        
        # 윈도우 설정
        self.setWindowTitle(IMPORTER_NAME)
        self.resize(600, 800)  # 높이를 700에서 800으로 증가
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        # 전역 변수 초기화
        self.fbx_file_list = []
        self.project_folder = 'None'
        
        try:
            # UI 구성
            self.create_widgets()
            self.create_layouts()
            self.create_connections()
            
            # 초기 설정 - 오류가 발생해도 UI는 표시되도록 함
            try:
                self.load_json()
            except Exception as e:
                self.log_message(f"JSON 로드 중 오류 (무시됨): {e}")
                
        except Exception as e:
            self.log_message(f"UI 구성 중 오류 발생: {e}")
            raise  # UI 구성 오류는 상위로 전달
    
    def log_message(self, message):
        """로그 메시지를 QTextEdit에 추가합니다."""
        # 기존 print는 항상 실행 (Maya 스크립트 에디터에서 볼 수 있도록)
        print(message)
        
        # Qt 위젯에 대한 안전한 접근
        try:
            if hasattr(self, 'log_text_edit') and self.log_text_edit is not None:
                # Qt 객체가 아직 유효한지 확인
                if hasattr(self.log_text_edit, 'append'):
                    # 현재 시간 추가
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    formatted_message = f"[{timestamp}] {message}"
                    
                    # 로그에 메시지 추가
                    self.log_text_edit.append(formatted_message)
                    
                    # 스크롤을 맨 아래로 이동 (안전하게)
                    try:
                        scrollbar = self.log_text_edit.verticalScrollBar()
                        if scrollbar and hasattr(scrollbar, 'setValue'):
                            scrollbar.setValue(scrollbar.maximum())
                    except (RuntimeError, AttributeError):
                        # 스크롤바 접근 실패는 무시
                        pass
        except (RuntimeError, AttributeError):
            # Qt 객체가 이미 삭제된 경우 무시
            pass
        except Exception as e:
            # 기타 예상치 못한 오류는 print로만 출력
            print(f"로그 메시지 출력 중 오류: {e}")
    
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
                self.log_message(f"다이얼로그 정리 중 Qt 객체 오류 (무시됨): {e}")
            except Exception as e:
                # 기타 예상치 못한 오류
                self.log_message(f"다이얼로그 정리 중 오류: {e}")
            finally:
                # 참조 제거
                self.progress_dialog = None
    
    def _validate_paths_for_batch_process(self):
        """배치 처리를 위한 경로들을 검증합니다."""
        errors = []
        
        # 리그 파일 검증
        rig_file = self.rig_line_edit.text().strip()
        if not rig_file:
            errors.append("리그 파일을 선택해주세요.")
        elif not os.path.exists(rig_file):
            errors.append(f"리그 파일이 존재하지 않습니다: {rig_file}")
        elif not rig_file.lower().endswith(('.ma', '.mb')):
            errors.append("리그 파일은 Maya 파일(.ma 또는 .mb)이어야 합니다.")
        
        # 저장 폴더 검증
        save_folder = self.save_path_line_edit.text().strip()
        if not save_folder:
            errors.append("저장 폴더를 선택해주세요.")
        elif not os.path.exists(save_folder):
            errors.append(f"저장 폴더가 존재하지 않습니다: {save_folder}")
        elif not os.path.isdir(save_folder):
            errors.append("저장 경로가 폴더가 아닙니다.")
        
        # FBX 폴더 검증
        fbx_folder = self.path_line_edit.text().strip()
        if not fbx_folder:
            errors.append("FBX 폴더를 선택해주세요.")
        elif not os.path.exists(fbx_folder):
            errors.append(f"FBX 폴더가 존재하지 않습니다: {fbx_folder}")
        elif not os.path.isdir(fbx_folder):
            errors.append("FBX 경로가 폴더가 아닙니다.")
        
        return errors
    
    def closeEvent(self, event):
        """창이 닫힐 때 호출되는 이벤트 핸들러"""
        global fbx_importer_window
        
        try:
            # 프로그레스 다이얼로그가 있으면 정리
            self._cleanup_progress_dialog()
            
            # Qt 객체들에 대한 참조 정리
            try:
                # UI 위젯들의 시그널 연결 해제
                self.clear_log_button.clicked.disconnect()
                self.batch_button.clicked.disconnect()
                self.collapse_button.clicked.disconnect()
                
                # 기타 주요 시그널 연결 해제
                if hasattr(self, 'file_list_widget') and self.file_list_widget:
                    self.file_list_widget.itemDoubleClicked.disconnect()
                    self.file_list_widget.customContextMenuRequested.disconnect()
                
            except (RuntimeError, AttributeError) as e:
                # 이미 삭제된 객체에 접근하려 할 때 발생하는 오류 무시
                pass
            
            # 전역 변수 정리
            fbx_importer_window = None
            
            print(f"{IMPORTER_NAME} UI가 정리되었습니다.")
            
        except (RuntimeError, AttributeError) as e:
            # Qt 객체 삭제 관련 오류는 무시 (이미 삭제된 객체에 접근)
            print(f"UI 정리 중 Qt 객체 오류 (무시됨): {e}")
        except Exception as e:
            print(f"UI 정리 중 오류 (무시됨): {e}")
        
        # 부모 클래스의 closeEvent 호출
        super(FbxImporterUI, self).closeEvent(event)
    
    def create_widgets(self):
        def setup_label(text, font_size=10, color='rgb(255, 255, 0)'):
            label = QtWidgets.QLabel(text)
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
            font = label.font()
            font.setPointSize(font_size)
            label.setFont(font)
            return label
        
        """UI 위젯을 생성합니다."""
        # 마야 리그 파일 지정 위젯
        self.rig_label = setup_label('Maya Rig File :', font_size=11)
        self.rig_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.rig_label.setFixedWidth(120)  # 라벨 너비 고정
        self.rig_line_edit = QtWidgets.QLineEdit()
        self.rig_line_edit.setMinimumHeight(28)
        self.rig_line_edit.setStyleSheet('background-color: #222; color: #eee; font-size: 10pt;')
        self.rig_open_button = QtWidgets.QPushButton('Open')
        self.rig_open_button.setFixedSize(45, 28)
        self.rig_open_button.setStyleSheet('background-color: #666; color: #eee; font-weight: bold; font-size: 14px;')
        self.rig_open_button.setToolTip("파일 열기")
        self.rig_file_button = QtWidgets.QPushButton('...')
        self.rig_file_button.setFixedSize(35, 28)
        self.rig_file_button.setStyleSheet('background-color: #666; color: #eee; font-weight: bold; font-size: 14px;')
        self.rig_file_button.setToolTip("폴더 열기")
        
        # 폴더 경로 관련 위젯
        self.path_label = setup_label('Anim Location :', font_size=11)
        self.path_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.path_label.setFixedWidth(120)  # 라벨 너비 고정 (rig_label과 동일)
        self.path_line_edit = QtWidgets.QLineEdit()
        self.path_line_edit.setMinimumHeight(28)
        self.path_line_edit.setStyleSheet('background-color: #222; color: #eee; font-size: 10pt;')
        self.refresh_button = QtWidgets.QPushButton('Refresh')
        self.refresh_button.setFixedSize(60, 28)
        self.refresh_button.setStyleSheet('background-color: #666; color: #eee; font-weight: bold; font-size: 14px;')
        self.refresh_button.setToolTip("파일 새로고침")
        self.folder_button = QtWidgets.QPushButton('...')
        self.folder_button.setFixedSize(35, 28)
        self.folder_button.setStyleSheet('background-color: #666; color: #eee; font-weight: bold; font-size: 14px;')
        self.folder_button.setToolTip("폴더 열기")
        
        # 파일 리스트 테이블 위젯
        self.file_list_widget = QtWidgets.QTableWidget()
        self.file_list_widget.setColumnCount(1)
        self.file_list_widget.setHorizontalHeaderLabels(['파일명'])
        self.file_list_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.file_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.file_list_widget.horizontalHeader().setStretchLastSection(True)
        self.file_list_widget.setAlternatingRowColors(True)
        font = self.file_list_widget.font()
        font.setPointSize(8)
        self.file_list_widget.setFont(font)
        
        # 레퍼런스 버튼 위젯 추가
        self.reference_button = QtWidgets.QPushButton('Reference Selected')
        self.reference_button.setFixedHeight(30)
        self.ref_button = QtWidgets.QPushButton('Reference Editor')
        self.ref_button.setFixedHeight(30)
        
        # Process 버튼 위젯 추가
        self.match_button = QtWidgets.QPushButton('1. Skeleton Match')
        self.bake_button = QtWidgets.QPushButton('2. FK Control Bake')
        self.maya_save_button = QtWidgets.QPushButton('3. Save Scene As')
        self.delete_constraint_button = QtWidgets.QPushButton('Delete Connection')
        self.delete_constraint_button.setStyleSheet('background-color: orange; color: black; font-weight: bold;')
        
        # 파일 선택 레이블 추가
        self.file_select_label = setup_label('목록에 있는 FBX 파일을 선택하고 Batch Process 실행', font_size=8, color='rgb(255, 255, 255)')
        self.file_select_label2 = setup_label('** 선택 아이템이 없으면 모든 아이템 순서대로 Batch Process 진행', font_size=8, color='rgb(255, 0, 0)')
        
        # 프론트 Axis 체크박스 위젯
        self.frontX_checkbox = QtWidgets.QCheckBox(' FrontX ')
        self.frontZ_checkbox = QtWidgets.QCheckBox(' FrontZ ')
        
        # Collapse 버튼 추가
        self.collapse_button = QtWidgets.QPushButton('▼ Process Steps')
        self.collapse_button.setFixedHeight(30)
        self.collapse_button.setStyleSheet('background-color: lightgreen; color: black; font-weight: bold;')
        self.collapse_button.setCheckable(True)
        self.collapse_button.setChecked(False)
        
        # 프로세스 스텝 그룹
        self.process_group = QtWidgets.QGroupBox()
        self.process_group.setVisible(False)
        
        # Delete Constraint 관련 체크박스 위젯
        self.constraint_checkbox = QtWidgets.QCheckBox(' Constraint ')
        self.animation_keys_checkbox = QtWidgets.QCheckBox(' Keys ')
        self.reference_file_checkbox = QtWidgets.QCheckBox(' Reference ')
        
        # 저장 폴더 관련 위젯
        self.save_path_label = setup_label('Save Path :', font_size=11)
        self.save_path_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.save_path_label.setFixedWidth(100)  # 라벨 너비 고정
        self.save_path_line_edit = QtWidgets.QLineEdit()
        self.save_path_line_edit.setMinimumHeight(28)
        self.save_path_line_edit.setStyleSheet('background-color: #222; color: #eee; font-size: 10pt;')
        self.save_path_button = QtWidgets.QPushButton('...')
        self.save_path_button.setFixedSize(35, 28)
        self.save_path_button.setStyleSheet('background-color: #666; color: #eee; font-weight: bold; font-size: 14px;')
        self.save_path_button.setToolTip("폴더 열기")
        
        # 마야 파일 열기 버튼 추가
        self.open_maya_file_button = QtWidgets.QPushButton('Open')
        self.open_maya_file_button.setFixedSize(45, 28)
        self.open_maya_file_button.setStyleSheet('background-color: #666; color: #eee; font-weight: bold; font-size: 14px;')
        self.open_maya_file_button.setToolTip("마야 파일 열기")
        
        # 저장 경로 익스플로러 열기 버튼 추가
        self.open_save_folder_button = QtWidgets.QPushButton()
        self.open_save_folder_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogOpenButton))
        self.open_save_folder_button.setFixedSize(28, 28)
        self.open_save_folder_button.setStyleSheet('background-color: #666; color: #eee; font-weight: bold; font-size: 14px;')
        self.open_save_folder_button.setToolTip("폴더 열기")
        
        # 버튼 위젯
        self.batch_button = QtWidgets.QPushButton('Batch Process')
        self.batch_button.setFixedHeight(40)
        self.batch_button.setStyleSheet('background-color: lightyellow; color: black; font-weight: bold;')
        
        for button in [self.match_button, self.bake_button, self.maya_save_button]:
            button.setFixedHeight(30)
            button.setStyleSheet('background-color: lightgrey; color: black; font-weight: bold;')
        
        # Delete Constraint 버튼 높이 설정
        self.delete_constraint_button.setFixedHeight(30)
        
        
        # 로그 출력 위젯 추가
        self.log_label = setup_label('실행 로그 :', font_size=11)
        self.log_text_edit = QtWidgets.QTextEdit()
        self.log_text_edit.setMaximumHeight(150)  # 로그 창 높이 제한
        self.log_text_edit.setMinimumHeight(100)   # 최소 높이 설정
        self.log_text_edit.setStyleSheet('background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace; font-size: 9pt;')
        self.log_text_edit.setReadOnly(True)  # 읽기 전용으로 설정
        
        # 로그 클리어 버튼 추가
        self.clear_log_button = QtWidgets.QPushButton('Clear Log')
        self.clear_log_button.setFixedHeight(25)
        self.clear_log_button.setStyleSheet('background-color: #555; color: #eee; font-weight: bold;')
    
    def create_layouts(self):
        """레이아웃을 구성합니다."""
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # 마야 리그 파일 지정 레이아웃 - 개선된 배치
        rig_layout = QtWidgets.QHBoxLayout()
        rig_layout.addWidget(self.rig_label)
        rig_layout.addWidget(self.rig_line_edit)
        rig_layout.addWidget(self.rig_open_button)
        rig_layout.addWidget(self.rig_file_button)
        # 라벨과 라인에디트 사이 비율 설정 (1:4 비율)
        rig_layout.setStretchFactor(self.rig_label, 0)
        rig_layout.setStretchFactor(self.rig_line_edit, 1)
        main_layout.addLayout(rig_layout)
        
        # 폴더 경로 레이아웃 - 개선된 배치
        folder_layout = QtWidgets.QHBoxLayout()
        folder_layout.addWidget(self.path_label)
        folder_layout.addWidget(self.path_line_edit)
        folder_layout.addWidget(self.refresh_button)
        folder_layout.addWidget(self.folder_button)
        
        # 라벨과 라인에디트 사이 비율 설정 (1:4 비율)
        folder_layout.setStretchFactor(self.path_label, 0)
        folder_layout.setStretchFactor(self.path_line_edit, 1)
        main_layout.addLayout(folder_layout)
        
        # 파일 리스트 레이아웃
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFocusPolicy(QtCore.Qt.NoFocus)
        scroll_area.setWidget(self.file_list_widget)
        main_layout.addWidget(scroll_area)
        
        # 레퍼런스 버튼 레이아웃 추가
        ref_import_layout = QtWidgets.QHBoxLayout()
        ref_import_layout.addWidget(self.reference_button)
        ref_import_layout.addWidget(self.ref_button)
        main_layout.addLayout(ref_import_layout)
        
        # 구분선 추가
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(separator)
           
        # 체크박스 레이아웃
        checkbox_layout = QtWidgets.QHBoxLayout()
        checkbox_layout.addWidget(self.frontX_checkbox)
        checkbox_layout.addWidget(self.frontZ_checkbox)
        main_layout.addLayout(checkbox_layout)  
     
        # Collapse 버튼 레이아웃
        collapse_layout = QtWidgets.QHBoxLayout()
        collapse_layout.addWidget(self.collapse_button)
        main_layout.addLayout(collapse_layout)
        
        # 프로세스 스텝 그룹 레이아웃
        process_layout = QtWidgets.QVBoxLayout(self.process_group)
        process_layout.addWidget(self.match_button)
        process_layout.addWidget(self.bake_button)
        process_layout.addWidget(self.maya_save_button)
        # 구분선 추가
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        process_layout.addWidget(separator)
        
        constraint_layout = QtWidgets.QHBoxLayout()
        constraint_layout.addWidget(self.constraint_checkbox)
        constraint_layout.addWidget(self.animation_keys_checkbox)
        constraint_layout.addWidget(self.reference_file_checkbox)
        delete_layout = QtWidgets.QVBoxLayout()
        delete_layout.addWidget(self.delete_constraint_button)
        process_layout.addLayout(constraint_layout)
        process_layout.addLayout(delete_layout)
        main_layout.addWidget(self.process_group)
        
        # 구분선 추가
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # 저장 폴더 레이아웃
        save_folder_layout = QtWidgets.QHBoxLayout()
        save_folder_layout.addWidget(self.save_path_label)
        save_folder_layout.addWidget(self.save_path_line_edit)
        save_folder_layout.addWidget(self.open_save_folder_button)
        save_folder_layout.addWidget(self.open_maya_file_button)
        save_folder_layout.addWidget(self.save_path_button)
        
        # 라벨과 라인에디트 사이 비율 설정
        save_folder_layout.setStretchFactor(self.save_path_label, 0)
        save_folder_layout.setStretchFactor(self.save_path_line_edit, 1)
        main_layout.addLayout(save_folder_layout)
        
        # 구분선 추가
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # 파일 선택 레이아웃
        file_select_layout = QtWidgets.QVBoxLayout()
        file_select_layout.addWidget(self.file_select_label)
        file_select_layout.addWidget(self.file_select_label2)
        file_select_layout.addWidget(self.batch_button)
        main_layout.addLayout(file_select_layout)
        
        # 구분선 추가
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # 로그 레이아웃 추가
        log_header_layout = QtWidgets.QHBoxLayout()
        log_header_layout.addWidget(self.log_label)
        log_header_layout.addStretch()  # 공간을 채워서 버튼을 오른쪽으로 밀기
        log_header_layout.addWidget(self.clear_log_button)
        main_layout.addLayout(log_header_layout)
        main_layout.addWidget(self.log_text_edit)
        
    def create_connections(self):
        """시그널과 슬롯을 연결합니다."""
        # 버튼 연결
        self.rig_file_button.clicked.connect(self.set_rig_file)
        self.rig_open_button.clicked.connect(self.open_rig_file)
        self.folder_button.clicked.connect(self.set_folder)
        self.refresh_button.clicked.connect(self.refresh_folder)
        self.save_path_button.clicked.connect(self.set_save_folder)
        self.open_maya_file_button.clicked.connect(self.open_maya_file_from_save_path)
        self.open_save_folder_button.clicked.connect(self.open_save_folder)
        self.match_button.clicked.connect(self.skeleton_match_func)
        self.bake_button.clicked.connect(self.control_bake_func)
        self.maya_save_button.clicked.connect(self.maya_file_save_func)
        self.delete_constraint_button.clicked.connect(self.delete_constraint_func)
        self.batch_button.clicked.connect(self.batch_process)
        self.collapse_button.clicked.connect(self.toggle_process_group)
        
        # 로그 클리어 버튼 연결 추가
        self.clear_log_button.clicked.connect(self.clear_log)
        
        # 레퍼런스 버튼 연결 추가
        self.reference_button.clicked.connect(self.reference_selected_files)
        self.ref_button.clicked.connect(self.reference_editor_open)
        
        # 체크박스 연결
        self.frontX_checkbox.stateChanged.connect(self.on_frontX_changed)
        self.frontZ_checkbox.stateChanged.connect(self.on_frontZ_changed)
        
        # Delete Constraint 체크박스 연결 (필요시 메서드 추가)
        # self.constraint_checkbox.stateChanged.connect(self.on_constraint_changed)
        # self.animation_keys_checkbox.stateChanged.connect(self.on_animation_keys_changed)  
        # self.reference_file_checkbox.stateChanged.connect(self.on_reference_file_changed)
        
        # 파일 리스트 연결
        self.file_list_widget.itemDoubleClicked.connect(self.file_double_clicked)
        self.file_list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.file_list_widget.customContextMenuRequested.connect(self.show_file_context_menu)
        
        # 초기 체크박스 상태 설정
        self.frontX_checkbox.setChecked(True)
        
        # Delete Constraint 체크박스 초기 상태 설정
        self.constraint_checkbox.setChecked(True)
        self.animation_keys_checkbox.setChecked(True)
        self.reference_file_checkbox.setChecked(True)
        
        # 초기 로그 메시지
        self.log_message("FBX 임포터가 시작되었습니다.")
    
    def clear_log(self):
        """로그를 클리어합니다."""
        self.log_text_edit.clear()
        self.log_message("로그가 클리어되었습니다.")
    
    def add_fbx_files_from_folder(self, folder_path):
        """선택된 폴더의 FBX 파일을 리스트로 교체합니다."""
        if folder_path and os.path.isdir(folder_path):
            fbx_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.fbx')]
            self.fbx_file_list = fbx_files  # 기존 리스트를 새로운 리스트로 교체
            self.file_list_widget.setRowCount(0)  # 테이블 초기화
            
            for fbx_file in fbx_files:
                row_position = self.file_list_widget.rowCount()
                self.file_list_widget.insertRow(row_position)
                
                # 파일명 추가
                file_item = QtWidgets.QTableWidgetItem(fbx_file)
                self.file_list_widget.setItem(row_position, 0, file_item)
            
            self.save_json(folder_path)
            self.log_message(f"{len(fbx_files)}개의 FBX 파일을 선택했습니다.")
    
    def set_folder(self):
        """FBX 파일을 선택하고 리스트를 교체합니다."""
        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            'Select FBX Files',
            self.path_line_edit.text(),
            'FBX Files (*.fbx)'
        )
        
        if file_paths:
            directory = os.path.dirname(file_paths[0])
            self.path_line_edit.setText(directory)
            
            # 항상 Reset 모드: 기존 리스트를 교체
            self.fbx_file_list = []
            self.file_list_widget.setRowCount(0)  # 테이블 초기화
            
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                self.fbx_file_list.append(file_name)
                
                row_position = self.file_list_widget.rowCount()
                self.file_list_widget.insertRow(row_position)
                
                # 파일명 추가
                file_item = QtWidgets.QTableWidgetItem(file_name)
                self.file_list_widget.setItem(row_position, 0, file_item)
            
            self.save_json(directory)
            self.log_message(f"{len(file_paths)}개의 FBX 파일을 선택했습니다.")
    
    def set_save_folder(self):
        """저장 폴더를 선택하고 설정합니다."""
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Set Save Folder', self.save_path_line_edit.text())
        if folder_path:
            self.save_path_line_edit.setText(folder_path)
            self.save_json(folder_path, is_save_path=True)
            self.log_message(f"저장 폴더가 설정되었습니다: {folder_path}")
    
    def reference_selected_files(self):
        """선택된 FBX 파일을 레퍼런스로 불러옵니다."""
        selected_rows = set()
        for item in self.file_list_widget.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            self.log_message("선택된 파일이 없습니다.")
            return
        
        base_path = self.path_line_edit.text()
        for row in selected_rows:
            file_name = self.file_list_widget.item(row, 0).text()
            file_path = os.path.join(base_path, file_name)
            file_name_no_ext = os.path.splitext(file_name)[0]
            cmds.file(file_path, reference=True, namespace=file_name_no_ext)
            self.log_message(f"레퍼런스로 로드했습니다: {file_name}")
        time_change_set()
    
    def import_selected_files(self):
        """선택된 FBX 파일을 임포트합니다."""
        selected_rows = set()
        for item in self.file_list_widget.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            self.log_message("선택된 파일이 없습니다.")
            return
        
        base_path = self.path_line_edit.text()
        for row in selected_rows:
            file_name = self.file_list_widget.item(row, 0).text()
            file_path = os.path.join(base_path, file_name)
            file_name_no_ext = os.path.splitext(file_name)[0]
            cmds.file(file_path, i=True, type='FBX', namespace=file_name_no_ext)
            self.log_message(f"임포트했습니다: {file_name}")
        time_change_set()
    
    def on_frontX_changed(self, state):
        """FrontX 체크박스 상태 변경 처리"""
        if state:
            self.frontZ_checkbox.setChecked(False)
        else:
            self.frontZ_checkbox.setChecked(True)
    
    def on_frontZ_changed(self, state):
        """FrontZ 체크박스 상태 변경 처리"""
        if state:
            self.frontX_checkbox.setChecked(False)
        else:
            self.frontX_checkbox.setChecked(True)
    
    def show_file_context_menu(self, position):
        """우클릭 메뉴를 표시합니다."""
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            return
            
        menu = QtWidgets.QMenu()
        
        # 파일명 복사
        copy_file_name_action = menu.addAction("Copy File Name")
        copy_file_name_action.triggered.connect(self.copy_file_name)
        
        # 구분선 추가
        menu.addSeparator()
        
        # 탐색기에서 열기
        open_in_explorer_action = menu.addAction("Open in Explorer")
        open_in_explorer_action.triggered.connect(self.open_in_explorer)
        
        # 메뉴 표시
        menu.exec_(self.file_list_widget.mapToGlobal(position))
    
    def copy_file_name(self):
        """선택된 파일의 파일명을 클립보드에 복사합니다."""
        selected_items = self.file_list_widget.selectedItems()
        if selected_items:
            # 선택된 모든 파일명을 가져오기
            selected_rows = set()
            for item in selected_items:
                selected_rows.add(item.row())
            
            file_names = []
            for row in sorted(selected_rows):
                file_name = self.file_list_widget.item(row, 0).text()
                # 확장자 제거
                file_name_without_ext = os.path.splitext(file_name)[0]
                file_names.append(file_name_without_ext)
            
            # 클립보드에 복사 (여러 파일인 경우 줄바꿈으로 구분)
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText('\n'.join(file_names))
            
            # 사용자에게 피드백 제공
            if len(file_names) == 1:
                self.log_message(f"파일명이 복사되었습니다: {file_names[0]}")
            else:
                self.log_message(f"{len(file_names)}개 파일명이 복사되었습니다.")
    
    def open_in_explorer(self):
        """선택된 파일의 폴더를 탐색기에서 엽니다."""
        selected_items = self.file_list_widget.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            file_name = self.file_list_widget.item(row, 0).text()
            folder_path = self.path_line_edit.text()
            file_path = os.path.join(folder_path, file_name)
            if os.path.exists(file_path):
                open_file_or_folder(os.path.dirname(file_path))
                self.log_message(f"탐색기에서 폴더를 열었습니다: {os.path.dirname(file_path)}")
            else:
                # 파일이 존재하지 않으면 폴더만 열기
                if os.path.exists(folder_path):
                    open_file_or_folder(folder_path)
                    self.log_message(f"탐색기에서 폴더를 열었습니다: {folder_path}")
    
    def control_bake_func(self):
        """컨트롤 베이크를 실행합니다."""
        self.log_message("컨트롤 베이크를 시작합니다...")
        R8_ani_skeleton_match.control_bake()
        R8_ani_reference_remove.remove_all_animation_references()
        self.log_message("컨트롤 베이크가 완료되었습니다.")
    
    def skeleton_match_func(self):
        """스켈레톤 매치를 실행합니다."""
        frontX_v = self.frontX_checkbox.isChecked()
        direction = 'frontX' if frontX_v else 'frontZ'
        self.log_message(f"스켈레톤 매치를 시작합니다 (방향: {direction})...")
        R8_ani_skeleton_match.skeleton_control_match(direction)
        self.log_message("스켈레톤 매치가 완료되었습니다.")
    
    def reference_editor_open(self):
        """레퍼런스 에디터를 엽니다."""
        cmds.ReferenceEditor()
        self.log_message("레퍼런스 에디터를 열었습니다.")
    
    def delete_constraint_func(self):
        """체크박스 상태에 따라 제약, 애니메이션 키, 레퍼런스 파일을 삭제합니다."""
        try:
            # 체크박스 상태 확인
            delete_constraint = self.constraint_checkbox.isChecked()
            delete_animation_keys = self.animation_keys_checkbox.isChecked()
            delete_reference_file = self.reference_file_checkbox.isChecked()
            
            # Bake_Control_Set 셋트 멤버 리스트 가져오기
            bake_control_set = "Bake_Control_Set"
            controllers = []
            if cmds.objExists(bake_control_set):
                controllers = cmds.sets(bake_control_set, query=True)
                if controllers:
                    self.log_message(f"Bake_Control_Set 멤버: {controllers}")
                else:
                    self.log_message("Bake_Control_Set이 비어있습니다.")
            else:
                self.log_message("Bake_Control_Set이 존재하지 않습니다.")
            
            # 체크박스 상태에 따라 실행
            if delete_constraint:
                self.log_message("제약 노드 삭제 중...")
                R8_ani_skeleton_match.delete_constraint(controllers)
                
            if delete_animation_keys:
                self.log_message("애니메이션 키 삭제 중...")
                R8_ani_skeleton_match.delete_key_control(controllers)
                
            if delete_reference_file:
                self.log_message("레퍼런스 파일 제거 중...")
                R8_ani_reference_remove.remove_all_animation_references()
                
            if not (delete_constraint or delete_animation_keys or delete_reference_file):
                self.log_message("삭제할 항목이 선택되지 않았습니다.")
            else:
                self.log_message("삭제 작업이 완료되었습니다.")
                
        except Exception as e:
            self.log_message(f"삭제 작업 중 오류 발생: {e}")

    def maya_file_save_func(self):
        """현재 마야 파일을 저장 다이얼로그를 통해 저장합니다."""
        save_folder = self.save_path_line_edit.text().strip()
        
        # 초기 경로 설정 (save_path가 있으면 사용, 없으면 현재 작업 디렉토리)
        if save_folder and os.path.exists(save_folder):
            initial_path = save_folder
        else:
            initial_path = os.getcwd()
        
        # 현재 파일명 가져오기 (기본 파일명으로 사용)
        current_file = cmds.file(query=True, sceneName=True)
        if current_file:
            current_filename = os.path.basename(current_file)
            base_name = os.path.splitext(current_filename)[0]
        else:
            base_name = "untitled"
        
        # 기본 저장 경로 생성
        default_save_path = os.path.join(initial_path, f"{base_name}.ma")
        
        # 파일 저장 다이얼로그 열기
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Save Maya File',
            default_save_path,
            'Maya ASCII Files (*.ma);;Maya Binary Files (*.mb);;All Files (*.*)'
        )
        
        if file_path:
            try:
                # 파일 확장자에 따라 저장 타입 결정
                if file_path.lower().endswith('.mb'):
                    file_type = 'mayaBinary'
                else:
                    file_type = 'mayaAscii'
                    # .ma 확장자가 없으면 추가
                    if not file_path.lower().endswith('.ma'):
                        file_path += '.ma'
                
                # 마야 파일 저장
                cmds.file(rename=file_path)
                cmds.file(save=True, type=file_type)
                
                QtWidgets.QMessageBox.information(self, "저장 완료", f"마야 파일이 저장되었습니다:\n{file_path}")
                self.log_message(f"마야 파일 저장 완료: {file_path}")
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "저장 오류", f"마야 파일 저장 중 오류가 발생했습니다:\n{str(e)}")
                self.log_message(f"마야 파일 저장 오류: {str(e)}")
    
    def file_double_clicked(self, item):
        """파일 더블클릭 시 레퍼런스/임포트 다이얼로그를 표시합니다."""
        if item:
            # 테이블에서 해당 행을 선택
            self.file_list_widget.selectRow(item.row())
            
            dialog = ReferenceImportDialog(self)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                if dialog.result == 'Reference':
                    self.reference_selected_files()
                elif dialog.result == 'Import':
                    self.import_selected_files()
    
    def load_json(self):
        """JSON 파일에서 프로젝트 폴더 경로를 로드합니다."""
        try:
            if os.path.exists(JSON_FILE_PATH):
                with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    if 'project_folder' in data:
                        self.project_folder = data['project_folder']
                        self.path_line_edit.setText(self.project_folder)
                    if 'save_folder' in data:
                        self.save_path_line_edit.setText(data['save_folder'])
                    if 'rig_file' in data:
                        self.rig_line_edit.setText(data['rig_file'])
            elif os.name == 'nt':
                self.path_line_edit.setText(DEFAULT_FOLDER_PATH)
        except (json.JSONDecodeError, IOError, KeyError) as e:
            self.log_message(f"JSON 설정 파일 로드 중 오류: {e}")
            # 기본값으로 설정
            if os.name == 'nt':
                self.path_line_edit.setText(DEFAULT_FOLDER_PATH)
        except Exception as e:
            self.log_message(f"예상치 못한 오류 발생: {e}")
    
    def save_json(self, folder_path, is_save_path=False, is_rig_file=False):
        """프로젝트 폴더 경로를 JSON 파일에 저장합니다."""
        try:
            # 기존 데이터 로드
            data = {}
            if os.path.exists(JSON_FILE_PATH):
                try:
                    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                except (json.JSONDecodeError, IOError):
                    # 파일이 손상된 경우 새로 시작
                    data = {}
                    
            # 새 데이터 설정
            if is_save_path:
                data['save_folder'] = folder_path
            elif is_rig_file:
                data['rig_file'] = folder_path
            else:
                data['project_folder'] = folder_path
                
            # 파일 저장
            with open(JSON_FILE_PATH, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                
        except (IOError, json.JSONEncodeError) as e:
            self.log_message(f"JSON 설정 파일 저장 중 오류: {e}")
        except Exception as e:
            self.log_message(f"예상치 못한 오류 발생: {e}")
    
    def batch_process(self):
        """선택된 파일들을 백그라운드에서 순차적으로 처리합니다."""
        # 기존 프로그레스 다이얼로그가 있으면 먼저 정리
        self._cleanup_progress_dialog()
        
        self.log_message("배치 처리를 준비 중입니다...")
        
        selected_items = self.file_list_widget.selectedItems()
        
        # 선택된 아이템이 없으면 모든 아이템을 대상으로 함
        if not selected_items:
            # 테이블에 있는 모든 행을 순서대로 가져오기
            all_files = []
            for row in range(self.file_list_widget.rowCount()):
                file_name = self.file_list_widget.item(row, 0).text()
                all_files.append(file_name)
            
            if not all_files:
                QtWidgets.QMessageBox.warning(self, "경고", "처리할 파일이 리스트에 없습니다.")
                self.log_message("경고: 처리할 파일이 리스트에 없습니다.")
                return
            
            # 모든 파일을 선택된 파일로 설정
            selected_files = all_files
            self.log_message(f"선택된 파일이 없어 전체 {len(all_files)}개 파일을 처리합니다.")
        else:
            # 선택된 행들에서 파일명 추출
            selected_rows = set()
            for item in selected_items:
                selected_rows.add(item.row())
            
            selected_files = []
            for row in selected_rows:
                file_name = self.file_list_widget.item(row, 0).text()
                selected_files.append(file_name)
            
            self.log_message(f"선택된 {len(selected_files)}개 파일을 처리합니다.")
        
        # 경로 검증
        validation_errors = self._validate_paths_for_batch_process()
        if validation_errors:
            error_message = "다음 문제들을 해결해주세요:\n\n" + "\n".join([f"• {error}" for error in validation_errors])
            QtWidgets.QMessageBox.warning(self, "검증 오류", error_message)
            for error in validation_errors:
                self.log_message(f"검증 오류: {error}")
            return
        
        # 검증 통과 후 변수 설정
        rig_file = self.rig_line_edit.text().strip()
        save_folder = self.save_path_line_edit.text().strip()
        fbx_folder = self.path_line_edit.text().strip()
        
        # 선택된 파일 목록 준비
        fbx_files = selected_files
        frontX_v = self.frontX_checkbox.isChecked()
        
        # 배치 처리 정보 로그에 기록
        selection_info = "선택된 파일들" if len(fbx_files) < self.file_list_widget.rowCount() else "전체 파일들"
        self.log_message(f"배치 처리 설정:")
        self.log_message(f"  - 처리할 파일: {len(fbx_files)}개 ({selection_info})")
        self.log_message(f"  - 리그 파일: {os.path.basename(rig_file)}")
        self.log_message(f"  - 저장 폴더: {save_folder}")
        self.log_message(f"  - 방향 설정: {'FrontX' if frontX_v else 'FrontZ'}")
        
        # 사용자에게 배치 처리 정보 확인
        info_msg = f"""배치 처리를 시작합니다.

처리할 파일: {len(fbx_files)}개 ({selection_info})
리그 파일: {os.path.basename(rig_file)}
저장 폴더: {save_folder}
방향 설정: {'FrontX' if frontX_v else 'FrontZ'}

각 FBX 파일마다:
1. 새로운 씬에서 리그 파일 로드
2. FBX 파일 레퍼런스 로드  
3. 스켈레톤 매칭 및 베이킹
4. Maya 파일로 저장

계속하시겠습니까?"""
        
        reply = QtWidgets.QMessageBox.question(self, "배치 처리 확인", info_msg,
                                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply != QtWidgets.QMessageBox.Yes:
            self.log_message("사용자가 배치 처리를 취소했습니다.")
            return
        
        self.log_message("배치 처리를 시작합니다...")
        
        # 진행 상황을 보여주는 프로그레스 다이얼로그 생성
        self.progress_dialog = QtWidgets.QProgressDialog("배치 처리 준비 중...", "취소", 0, len(fbx_files), self)
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        self.progress_dialog.setWindowTitle("백그라운드 배치 처리")
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setMinimumSize(400, 120)
        
        # 취소 버튼 클릭 시 배치 프로세스 취소
        def on_cancel_clicked():
            self.log_message("사용자가 배치 처리 취소를 요청했습니다.")
            try:
                # 배치 프로세스 취소
                R8_ani_batch_process.cancel_batch_process()
                
                # 프로그레스 다이얼로그 닫기 및 정리
                self._cleanup_progress_dialog()
                
            except Exception as e:
                self.log_message(f"배치 처리 취소 중 오류: {e}")
                # 다이얼로그 정리
                self._cleanup_progress_dialog()
                QtWidgets.QMessageBox.warning(self, "취소 오류", f"배치 처리 취소 중 오류가 발생했습니다:\n{str(e)}")
        
        # 취소 버튼 연결
        self.progress_dialog.canceled.connect(on_cancel_clicked)
        self.progress_dialog.show()
        
        # 처리 결과 저장용
        self.batch_results = {
            'total': len(fbx_files),
            'completed': 0,
            'failed': 0,
            'success_files': [],
            'failed_files': [],
            'completion_message_shown': False  # 완료 메시지 표시 플래그 추가
        }
        
        # 진행 상황 업데이트 콜백 함수
        def progress_callback(message, current, total):
            # 프로그레스 콜백 메시지를 로그에도 기록
            self.log_message(f"진행상황: {message} ({current}/{total})")
            
            if hasattr(self, 'progress_dialog') and self.progress_dialog is not None:
                # 진행률 계산
                progress_percent = int((current / total) * 100) if total > 0 else 0
                
                # 메시지 업데이트
                detailed_message = f"{message}\n\n진행률: {current}/{total} ({progress_percent}%)"
                self.progress_dialog.setLabelText(detailed_message)
                self.progress_dialog.setValue(current)
                
                # 처리 완료 시 (한 번만 실행되도록 플래그 체크)
                if current >= total and not self.batch_results['completion_message_shown']:
                    self.batch_results['completion_message_shown'] = True  # 플래그 설정
                    
                    self._cleanup_progress_dialog()
                    
                    # 결과 요약 표시
                    success_count = self.batch_results['completed']
                    failed_count = self.batch_results['failed']
                    
                    # 로그에 최종 결과 기록
                    self.log_message("=" * 50)
                    self.log_message("배치 처리가 완료되었습니다!")
                    self.log_message(f"총 파일: {total}개")
                    self.log_message(f"성공: {success_count}개")
                    self.log_message(f"실패: {failed_count}개")
                    
                    if self.batch_results['success_files']:
                        self.log_message("성공한 파일들:")
                        for file in self.batch_results['success_files']:
                            self.log_message(f"  ✓ {file}")
                    
                    if self.batch_results['failed_files']:
                        self.log_message("실패한 파일들:")
                        for file in self.batch_results['failed_files']:
                            self.log_message(f"  ✗ {file}")
                    
                    self.log_message("=" * 50)
                    
                    result_msg = f"""배치 처리가 완료되었습니다!

총 파일: {total}개
성공: {success_count}개
실패: {failed_count}개"""
                    
                    if self.batch_results['success_files']:
                        result_msg += f"\n\n성공한 파일들:\n" + "\n".join([f"• {f}" for f in self.batch_results['success_files'][:5]])
                        if len(self.batch_results['success_files']) > 5:
                            result_msg += f"\n... 외 {len(self.batch_results['success_files']) - 5}개"
                    
                    if self.batch_results['failed_files']:
                        result_msg += f"\n\n실패한 파일들:\n" + "\n".join([f"• {f}" for f in self.batch_results['failed_files'][:5]])
                        if len(self.batch_results['failed_files']) > 5:
                            result_msg += f"\n... 외 {len(self.batch_results['failed_files']) - 5}개"
                    
                    if failed_count == 0:
                        QtWidgets.QMessageBox.information(self, "배치 처리 완료", result_msg)
                    else:
                        QtWidgets.QMessageBox.warning(self, "배치 처리 완료 (일부 실패)", result_msg)
        
        # 개별 파일 처리 결과 콜백
        def file_result_callback(filename, success):
            if success:
                self.batch_results['completed'] += 1
                self.batch_results['success_files'].append(filename)
                self.log_message(f"✓ 성공: {filename}")
            else:
                self.batch_results['failed'] += 1
                self.batch_results['failed_files'].append(filename)
                self.log_message(f"✗ 실패: {filename}")
        
        # 처리할 파일 목록 로그에 기록
        self.log_message("처리할 파일 목록:")
        for i, filename in enumerate(fbx_files, 1):
            self.log_message(f"  {i}. {filename}")
        
        # 백그라운드 배치 프로세스 시작
        try:
            R8_ani_batch_process.start_batch_process(
                rig_file=rig_file,
                fbx_files=fbx_files,
                fbx_folder=fbx_folder,
                save_folder=save_folder,
                frontX_v=frontX_v,
                progress_callback=progress_callback,
                file_result_callback=file_result_callback
            )
            
            self.log_message(f"백그라운드 배치 처리가 시작되었습니다: {len(fbx_files)}개 파일 ({selection_info})")
            
        except Exception as e:
            self.log_message(f"배치 처리 시작 중 오류가 발생했습니다: {str(e)}")
            self._cleanup_progress_dialog()
            QtWidgets.QMessageBox.critical(self, "오류", f"배치 처리 시작 중 오류가 발생했습니다:\n{str(e)}")

    def toggle_process_group(self):
        """프로세스 스텝 그룹을 토글합니다."""
        is_checked = self.collapse_button.isChecked()
        
        # 현재 윈도우 크기 저장
        current_width = self.width()
        
        # 프로세스 그룹의 높이 계산
        if is_checked:
            # 그룹을 펼칠 때 - 필요한 높이 계산
            self.process_group.setVisible(True)
            self.process_group.updateGeometry()
            process_group_height = self.process_group.sizeHint().height()
        else:
            # 그룹을 접을 때 - 현재 높이 저장
            process_group_height = self.process_group.height()
            self.process_group.setVisible(False)
        
        # 버튼 텍스트 업데이트
        self.collapse_button.setText('▼ Process Steps' if is_checked else '▶ Process Steps')
        
        # 레이아웃 업데이트
        self.layout().invalidate()
        
        # 현재 높이 기준으로 새로운 높이 계산
        current_height = self.height()
        if is_checked:
            # 펼칠 때: 현재 높이 + 그룹 높이
            new_height = current_height + process_group_height + 10  # 여백 추가
        else:
            # 접을 때: 현재 높이 - 그룹 높이
            new_height = current_height - process_group_height - 10
        
        # 최소 크기 제한
        min_height = 500 if is_checked else 400
        new_height = max(new_height, min_height)
        
        # 크기 조정 (너비는 유지, 높이만 조정)
        self.resize(current_width, new_height)
        
        # 최소 크기 설정
        self.setMinimumSize(600, min_height)

    def refresh_folder(self):
        """현재 경로의 FBX 파일 리스트를 새로고침합니다."""
        folder_path = self.path_line_edit.text()
        if os.path.isdir(folder_path):
            self.add_fbx_files_from_folder(folder_path)
            self.log_message(f"폴더를 새로고침했습니다: {folder_path}")

    def set_rig_file(self):
        """마야 리그 파일을 선택합니다."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Select Maya Rig File',
            self.rig_line_edit.text() or '',
            'Maya Files (*.ma *.mb);;All Files (*.*)'
        )
        if file_path:
            self.rig_line_edit.setText(file_path)
            self.save_json(file_path, is_rig_file=True)
            self.log_message(f"리그 파일을 선택했습니다: {os.path.basename(file_path)}")

    def open_rig_file(self):
        """rig_line_edit에 입력된 경로의 마야 파일을 오픈합니다."""
        file_path = self.rig_line_edit.text()
        if file_path and os.path.exists(file_path):
            cmds.file(file_path, open=True, force=True)
            self.log_message(f"리그 파일을 열었습니다: {os.path.basename(file_path)}")
        else:
            self.log_message('유효한 마야 파일 경로를 입력하세요.')

    def open_maya_file_from_save_path(self):
        """저장 경로에서 마야 파일을 선택하고 오픈합니다."""
        save_folder = self.save_path_line_edit.text()
        initial_path = save_folder if save_folder and os.path.exists(save_folder) else ''
        
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Select Maya File to Open',
            initial_path,
            'Maya Files (*.ma *.mb);;All Files (*.*)'
        )
        
        if file_path and os.path.exists(file_path):
            try:
                cmds.file(file_path, open=True, force=True)
                self.log_message(f"마야 파일이 열렸습니다: {os.path.basename(file_path)}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, '오류', f'마야 파일을 여는 중 오류가 발생했습니다:\n{str(e)}')
                self.log_message(f'마야 파일 열기 오류: {str(e)}')

    def open_save_folder(self):
        """저장 경로를 윈도우 익스플로러에서 엽니다."""
        folder_path = self.save_path_line_edit.text()
        if os.path.exists(folder_path):
            open_file_or_folder(folder_path)
            self.log_message(f"폴더를 열었습니다: {folder_path}")
        else:
            self.log_message("유효한 저장 폴더를 입력하세요.")

class ReferenceImportDialog(QtWidgets.QDialog):
    """레퍼런스/임포트 선택 다이얼로그"""
    
    def __init__(self, parent=None):
        super(ReferenceImportDialog, self).__init__(parent)
        self.setWindowTitle('Reference or Import')
        self.setFixedSize(300, 100)
        
        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        
        self.result = None
    
    def create_widgets(self):
        """위젯을 생성합니다."""
        self.reference_button = QtWidgets.QPushButton('Reference')
        self.import_button = QtWidgets.QPushButton('Import')
        self.cancel_button = QtWidgets.QPushButton('Cancel')
    
    def create_layouts(self):
        """레이아웃을 구성합니다."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.reference_button)
        layout.addWidget(self.import_button)
        layout.addWidget(self.cancel_button)
    
    def create_connections(self):
        """시그널과 슬롯을 연결합니다."""
        self.reference_button.clicked.connect(self.reference_clicked)
        self.import_button.clicked.connect(self.import_clicked)
        self.cancel_button.clicked.connect(self.reject)
    
    def reference_clicked(self):
        """레퍼런스 버튼 클릭 처리"""
        self.result = 'Reference'
        self.accept()
    
    def import_clicked(self):
        """임포트 버튼 클릭 처리"""
        self.result = 'Import'
        self.accept()

# 전역 변수 선언
# fbx_importer_window = None

def show_ui():
    """UI 표시 함수"""
    global fbx_importer_window
    try:
        fbx_importer_window.close()
        fbx_importer_window.deleteLater()
        return fbx_importer_window
    except Exception as e:
        print(f"UI 생성 중 오류: {e}")

    fbx_importer_window = FbxImporterUI()
    fbx_importer_window.show()
    

if __name__ == '__main__':
    show_ui()
