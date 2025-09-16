'''
from R8_MaxtoMaya import R8_mannequin_skeleton_ui
from importlib import reload
reload(R8_mannequin_skeleton_ui)
R8_mannequin_skeleton_ui.show_ui()
'''
from maya import cmds, mel
import maya.OpenMayaUI as omui
import os
import time

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

# 마네퀸 스켈레톤 모듈 임포트 
try:
    from R8_MaxtoMaya import R8_mannequin_skeleton_rebuild
    from R8_MaxtoMaya import R8_mannequin_skeleton_extra
    from R8_MaxtoMaya import R8_biped_to_mannequin_json
    from R8_MaxtoMaya import R8_weight_transfer_core  # 웨이트 트랜스퍼 핵심 기능 추가
    from importlib import reload
    reload(R8_mannequin_skeleton_rebuild)
    reload(R8_mannequin_skeleton_extra)
    reload(R8_biped_to_mannequin_json)
    reload(R8_weight_transfer_core)
except ImportError:
    # 직접 실행할 때를 위한 fallback
    try:
        import R8_mannequin_skeleton_rebuild
        import R8_mannequin_skeleton_extra
        import R8_biped_to_mannequin_json
        import R8_weight_transfer_core  # 웨이트 트랜스퍼 핵심 기능 추가
        from importlib import reload
        reload(R8_mannequin_skeleton_rebuild)
        reload(R8_mannequin_skeleton_extra)
        reload(R8_biped_to_mannequin_json)
        reload(R8_weight_transfer_core)
    except ImportError as e:
        print(f"모듈 임포트 오류: {e}")
    
# 유틸리티 함수
def get_maya_main_window():
    """Maya 메인 윈도우를 반환합니다."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class MannequinSkeletonUI(QtWidgets.QDialog):
    """마네퀸 스켈레톤 생성 UI 클래스"""
    
    def __init__(self, parent=get_maya_main_window()):
        super(MannequinSkeletonUI, self).__init__(parent)
        
        # 윈도우 설정
        self.setWindowTitle("Mannequin Skeleton Generator")
        self.resize(600, 700)
        # 도움말 버튼 제거
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        # 기본 경로 설정 (현재 스크립트 폴더 기준)
        current_dir = os.path.dirname(__file__)
        self.skeleton_path = os.path.join(current_dir, "R8_Manny_Skeleton.ma")
        
        # UI 구성 요소 생성 및 초기화
        self.create_widgets()
        self.create_layouts()
        self.create_connections()       
        
    def create_widgets(self):
        """UI 위젯을 생성합니다."""
        # 경로 관련 위젯
        self.path_line_edit = QtWidgets.QLineEdit(self.skeleton_path)
        self.browse_button = QtWidgets.QPushButton("찾아보기")
        # 조인트 매칭 관련 위젯
        self.import_skeleton_button = QtWidgets.QPushButton("Import Skeleton")
        self.match_joints_button = QtWidgets.QPushButton("Match Joints")
        self.full_process_button = QtWidgets.QPushButton("1. Mannequin Skeleton")
        self.full_process_button.setMinimumHeight(30)
        self.full_process_button.setStyleSheet("font-weight: bold; font-size: 12px; background-color: lightblue; color: balack;")
        
        # 메시 선택 관련 위젯
        self.mesh_line_edit = QtWidgets.QLineEdit()
        self.mesh_line_edit.setPlaceholderText("스킨 메시 이름을 입력하거나 선택하세요")
        self.get_selected_mesh_button = QtWidgets.QPushButton("Get Selected Mesh")
        self.clear_mesh_button = QtWidgets.QPushButton("Clear")
        
        # 스켈레톤 생성 관련 위젯
        self.create_skeleton_button = QtWidgets.QPushButton("2. Add Sub Skeleton")
        self.create_skeleton_button.setMinimumHeight(30)
        self.create_skeleton_button.setStyleSheet("font-weight: bold; font-size: 12px; background-color: lightgreen; color: balack;")
        
        # Biped to Mannequin 매핑 관련 위젯 - biped_to_mannequin_button 삭제
        # 테이블 위젯
        self.mapping_table = QtWidgets.QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["Biped Skeleton", "Mannequin Skeleton"])  # 헤더 순서 바꿈
        
        # 열 크기를 균등하게 설정
        header = self.mapping_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        
        self.mapping_table.setAlternatingRowColors(True)
        self.mapping_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.mapping_table.setFixedHeight(200)
        
        # JSON 익스포트 관련 위젯
        self.export_json_button = QtWidgets.QPushButton("Export JSON")
        self.import_json_button = QtWidgets.QPushButton("Import JSON")
        
        # 마야 옵티마이즈 체크박스 추가
        self.maya_optimize_checkbox = QtWidgets.QCheckBox("Maya Optimize Scene Size")
        self.maya_optimize_checkbox.setChecked(True)  # 기본값 True
        
        # 웨이트 트랜스퍼 관련 위젯 추가
        self.weight_transfer_button = QtWidgets.QPushButton("3. Weight Transfer")
        self.weight_transfer_button.setMinimumHeight(30)
        self.weight_transfer_button.setStyleSheet("font-weight: bold; font-size: 12px; background-color: lightyellow; color: black;")
        
        # 그룹박스 생성
        self.path_group = QtWidgets.QGroupBox("Skeleton Path")
        self.match_group = QtWidgets.QGroupBox("Mannequin Skeleton")
        self.add_match_group = QtWidgets.QGroupBox("Add Sub Skeleton")
        self.mapping_group = QtWidgets.QGroupBox("Biped to Mannequin Mapping")
        self.weight_transfer_group = QtWidgets.QGroupBox("Weight Transfer")  # 웨이트 트랜스퍼 그룹 추가
        
        # 진행 상황 표시
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        
        # 로그 출력
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setMaximumHeight(120)
        self.log_text.setReadOnly(True)
        
        # 하단 버튼
        self.close_button = QtWidgets.QPushButton("닫기")
        self.help_button = QtWidgets.QPushButton("도움말")

    def create_layouts(self):
        """레이아웃을 생성합니다."""
        # 메인 레이아웃
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # 메시 선택 그룹 레이아웃
        mesh_layout = QtWidgets.QVBoxLayout()
        # 경로 그룹 레이아웃
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self.path_line_edit)
        path_layout.addWidget(self.browse_button)
        self.path_group.setLayout(path_layout)
        
        # 조인트 매칭 그룹 레이아웃
        match_layout = QtWidgets.QVBoxLayout()
        match_button_layout = QtWidgets.QHBoxLayout()
        match_button_layout.addWidget(self.import_skeleton_button)
        match_button_layout.addWidget(self.match_joints_button)
        
        match_layout.addLayout(match_button_layout)
        match_layout.addWidget(self.full_process_button)
        self.match_group.setLayout(match_layout)
        
        mesh_button_layout = QtWidgets.QHBoxLayout()
        mesh_button_layout.addWidget(self.get_selected_mesh_button)
        mesh_button_layout.addWidget(self.clear_mesh_button)
        
        mesh_layout.addWidget(self.mesh_line_edit)
        mesh_layout.addLayout(mesh_button_layout)
        # 스켈레톤 생성 그룹 레이아웃
        skeleton_layout = QtWidgets.QVBoxLayout()
        skeleton_layout.addWidget(self.create_skeleton_button)
        mesh_layout.addLayout(skeleton_layout)
        self.add_match_group.setLayout(mesh_layout)
        
        # Biped to Mannequin 매핑 그룹 레이아웃
        mapping_layout = QtWidgets.QVBoxLayout()
        # mapping_layout.addWidget(self.biped_to_mannequin_button) # 삭제됨
        mapping_layout.addWidget(self.mapping_table)
        
        # JSON 버튼 레이아웃
        json_button_layout = QtWidgets.QHBoxLayout()
        json_button_layout.addWidget(self.export_json_button)
        json_button_layout.addWidget(self.import_json_button)
        
        mapping_layout.addLayout(json_button_layout)
        self.mapping_group.setLayout(mapping_layout)
        
        # 웨이트 트랜스퍼 그룹 레이아웃 추가
        weight_transfer_layout = QtWidgets.QVBoxLayout()
        
        # 체크박스와 메인 버튼을 위한 상단 레이아웃
        weight_optimize_layout = QtWidgets.QHBoxLayout()
        weight_optimize_layout.addWidget(self.maya_optimize_checkbox) # 마야 옵티마이즈 체크박스를 우측에 추가
        weight_optimize_layout.addStretch()
        
        weight_transfer_button_layout = QtWidgets.QVBoxLayout()
        weight_transfer_button_layout.addWidget(self.weight_transfer_button)
        
        weight_transfer_layout.addLayout(weight_optimize_layout)
        weight_transfer_layout.addLayout(weight_transfer_button_layout)
        
        self.weight_transfer_group.setLayout(weight_transfer_layout)
        
        # 로그 그룹 생성
        log_group = QtWidgets.QGroupBox("Log")
        log_layout = QtWidgets.QVBoxLayout()
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        # 스플리터 생성 (매핑 그룹과 로그 그룹 사이)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.addWidget(self.mapping_group)
        splitter.addWidget(log_group)
        
        # 스플리터 초기 비율 설정 (매핑:로그 = 3:1)
        splitter.setSizes([400, 120])
        splitter.setCollapsible(0, False)  # 매핑 그룹은 접을 수 없게
        splitter.setCollapsible(1, False)  # 로그 그룹도 접을 수 없게
        
        # 하단 버튼 레이아웃
        bottom_button_layout = QtWidgets.QHBoxLayout()
        bottom_button_layout.addWidget(self.help_button)
        bottom_button_layout.addStretch()
        bottom_button_layout.addWidget(self.close_button)
        
        # 메인 레이아웃에 추가
        main_layout.addWidget(self.path_group)
        main_layout.addWidget(self.match_group)
        main_layout.addWidget(self.add_match_group)
        main_layout.addWidget(self.mapping_group)
        main_layout.addWidget(self.weight_transfer_group)  # 웨이트 트랜스퍼 그룹 추가
        main_layout.addWidget(log_group)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(bottom_button_layout)
        
    def create_connections(self):
        """시그널과 슬롯을 연결합니다."""
        # 메시 관련 연결
        self.get_selected_mesh_button.clicked.connect(self.get_selected_mesh)
        self.clear_mesh_button.clicked.connect(self.clear_mesh)
        
        # 스켈레톤 생성 연결
        self.create_skeleton_button.clicked.connect(self.create_mannequin_skeleton)
        
        # 조인트 매칭 관련 연결
        self.import_skeleton_button.clicked.connect(self.import_skeleton)
        self.match_joints_button.clicked.connect(self.match_joints)
        self.full_process_button.clicked.connect(self.full_process)
        
        # Biped to Mannequin 매핑 관련 연결
        # self.biped_to_mannequin_button.clicked.connect(self.load_biped_to_mannequin_mapping) # 삭제됨
        self.export_json_button.clicked.connect(self.export_mapping_to_json)
        self.import_json_button.clicked.connect(self.import_mapping_from_json)
        
        # 웨이트 트랜스퍼 버튼 연결 추가
        self.weight_transfer_button.clicked.connect(self.perform_weight_transfer)
        # self.maya_optimize_button.clicked.connect(self.maya_optimize) # 마야 옵티마이즈 버튼 연결 삭제
        
        # 경로 관련 연결
        self.browse_button.clicked.connect(self.browse_skeleton_file)
        
        # 하단 버튼 연결
        self.close_button.clicked.connect(self.close)
        self.help_button.clicked.connect(self.show_help)
        
    def log_message(self, message):
        """로그 메시지를 추가합니다."""
        self.log_text.append(f"[{cmds.date()}] {message}")
        self.log_text.ensureCursorVisible()
        
    def get_selected_mesh(self):
        """선택된 메시를 가져옵니다."""
        selected = cmds.ls(selection=True, type='transform')
        if selected:
            # 모든 선택된 객체를 쉼표로 구분하여 표시
            mesh_names = ", ".join(selected)
            self.mesh_line_edit.setText(mesh_names)
            self.log_message(f"메시 선택됨: {mesh_names} (총 {len(selected)}개)")
        else:
            self.log_message("선택된 객체가 없습니다.")
            
    def clear_mesh(self):
        """메시 입력 필드를 지웁니다."""
        self.mesh_line_edit.clear()
        self.log_message("메시 선택 해제됨")
        
    def create_mannequin_skeleton(self):
        """마네퀸 스켈레톤을 생성합니다."""
        # Undo 블록 시작
        cmds.undoInfo(openChunk=True, chunkName="Create Mannequin Skeleton")
        
        try:
            # 프로그래스바 설정 (0~100 범위)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            
            # 초기 준비 (5%)
            self.progress_bar.setValue(5)
            self.log_message("마네퀸 스켈레톤 생성 시작... (5%)")
            QtWidgets.QApplication.processEvents()
            
            mesh_names_text = self.mesh_line_edit.text().strip()
            mesh_names = None
            
            if mesh_names_text:
                # 쉼표로 구분된 메시 이름들을 리스트로 변환
                mesh_names = [name.strip() for name in mesh_names_text.split(',') if name.strip()]
                
                if len(mesh_names) == 1:
                    self.log_message(f"메시 '{mesh_names[0]}'의 인플루언스 조인트로 마네퀸 스켈레톤 생성 중...")
                    mesh_names = mesh_names[0]  # 단일 메시의 경우 문자열로 전달
                else:
                    self.log_message(f"메시들 {mesh_names}의 인플루언스 조인트로 마네퀸 스켈레톤 생성 중...")
            else:
                self.log_message("모든 Bip001 하위 조인트로 마네퀸 스켈레톤 생성 중...")
            
            # 1단계: 조인트 필터링 (10% ~ 20%)
            self.progress_bar.setValue(10)
            self.log_message("1단계: Bip001 하위 조인트 가져오기... (10%)")
            QtWidgets.QApplication.processEvents()
            
            # get_all_joints_under_bip001 호출
            select_joints = R8_mannequin_skeleton_extra.get_all_joints_under_bip001(mesh_names)
            
            if not select_joints:
                self.log_message("처리할 조인트가 없습니다.")
                QtWidgets.QMessageBox.warning(self, "경고", "처리할 조인트가 없습니다.")
                return
            
            self.progress_bar.setValue(15)
            self.log_message(f"Bip001 하위 조인트 {len(select_joints)}개 발견 (15%)")
            QtWidgets.QApplication.processEvents()
            
            # 2단계: Bip 문자 포함 조인트 제거 (20% ~ 30%)
            self.progress_bar.setValue(20)
            self.log_message("2단계: 'Bip' 문자가 포함된 조인트들 제거... (20%)")
            QtWidgets.QApplication.processEvents()
            
            bip_extra_joints = R8_mannequin_skeleton_extra.remove_bip_joints(select_joints)
            
            self.progress_bar.setValue(25)
            self.log_message(f"필터링 후 조인트 {len(bip_extra_joints)}개 (25%)")
            QtWidgets.QApplication.processEvents()
            
            # 3단계: Advanced Skeleton 조인트 처리 (30% ~ 45%)
            self.progress_bar.setValue(30)
            self.log_message("3단계: Advanced Skeleton 조인트 처리... (30%)")
            QtWidgets.QApplication.processEvents()
            
            advanced_joints = R8_mannequin_skeleton_extra.process_advanced_joints(bip_extra_joints)
            
            self.progress_bar.setValue(40)
            self.log_message(f"Advanced 조인트 {len(advanced_joints)}개 처리 완료 (40%)")
            QtWidgets.QApplication.processEvents()
            
            # 4단계: 언리얼 스켈레톤 조인트 생성 (45% ~ 60%)
            self.progress_bar.setValue(45)
            self.log_message("4단계: 언리얼 스켈레톤 조인트 생성... (45%)")
            QtWidgets.QApplication.processEvents()
            
            mannequin_joints = R8_mannequin_skeleton_extra.create_manequin_skeleton_from_selected(advanced_joints)
            
            self.progress_bar.setValue(55)
            self.log_message(f"마네퀸 조인트 {len(mannequin_joints)}개 생성 완료 (55%)")
            QtWidgets.QApplication.processEvents()
            
            # 5단계: 매핑 생성 (60% ~ 70%)
            self.progress_bar.setValue(60)
            self.log_message("5단계: 조인트 매핑 생성... (60%)")
            QtWidgets.QApplication.processEvents()
            
            # 원본 바이패드 조인트 -> 마네퀸 조인트 매핑 생성
            original_to_mannequin_mapping = {}
            mannequin_to_original_mapping = {}
            
            for i, (advance_joint_info, mannequin_joint) in enumerate(zip(advanced_joints, mannequin_joints)):
                if advance_joint_info and mannequin_joint:
                    # advance_joint_info가 딕셔너리인 경우
                    if isinstance(advance_joint_info, dict):
                        original_joint = advance_joint_info['original_joint']
                        mannequin_joint_name = advance_joint_info['name']
                        
                        # 실제 생성된 마네퀸 조인트 이름 사용
                        original_to_mannequin_mapping[original_joint] = mannequin_joint
                        mannequin_to_original_mapping[mannequin_joint] = original_joint
                        
                        # 기존 매핑도 유지
                        R8_mannequin_skeleton_extra.advance_to_mannequin_mapping[mannequin_joint_name] = mannequin_joint
                    else:
                        advance_joint_name = advance_joint_info
                        original_to_mannequin_mapping[advance_joint_name] = mannequin_joint
                        R8_mannequin_skeleton_extra.advance_to_mannequin_mapping[advance_joint_name] = mannequin_joint
            
            self.progress_bar.setValue(65)
            self.log_message(f"매핑 {len(original_to_mannequin_mapping)}개 생성 완료 (65%)")
            QtWidgets.QApplication.processEvents()
            
            # 6단계: 계층 구조 재생성 (70% ~ 80%)
            self.progress_bar.setValue(70)
            self.log_message("6단계: 계층 구조 재생성... (70%)")
            QtWidgets.QApplication.processEvents()
            
            # 원본 바이패드 조인트의 계층 구조를 기반으로 마네퀸 조인트 계층 구조 재생성
            R8_mannequin_skeleton_extra.recreate_hierarchy(original_to_mannequin_mapping.keys(), original_to_mannequin_mapping)
            
            self.progress_bar.setValue(75)
            self.log_message("계층 구조 재생성 완료 (75%)")
            QtWidgets.QApplication.processEvents()
            
            # 7단계: 기본 마네퀸 본과 연결 (80% ~ 85%)
            self.progress_bar.setValue(80)
            self.log_message("7단계: 기본 마네퀸 본과 연결... (80%)")
            QtWidgets.QApplication.processEvents()
            
            # 기본 마네퀸 본과 추가 조인트 연결
            R8_mannequin_skeleton_extra.connect_to_base_mannequin_skeleton(original_to_mannequin_mapping)
            
            self.progress_bar.setValue(85)
            self.log_message("기본 마네퀸 본 연결 완료 (85%)")
            QtWidgets.QApplication.processEvents()
            
            # 8단계: 로케이터-마네퀸 조인트 컨스트레인트 연결 (85% ~ 90%)
            self.progress_bar.setValue(85)
            self.log_message("8단계: 로케이터-마네퀸 조인트 컨스트레인트 연결... (85%)")
            QtWidgets.QApplication.processEvents()
            
            # 로케이터들이 마네퀸 조인트들을 제어하도록 컨스트레인트 연결
            R8_mannequin_skeleton_extra.connect_locators_to_mannequin_joints(advanced_joints)
            
            self.progress_bar.setValue(90)
            self.log_message("컨스트레인트 연결 완료 (90%)")
            QtWidgets.QApplication.processEvents()
            
            # 9단계: 매핑 테이블 업데이트 (90% ~ 95%)
            self.progress_bar.setValue(90)
            self.log_message("9단계: 매핑 테이블 자동 업데이트... (90%)")
            QtWidgets.QApplication.processEvents()
            
            self.load_biped_to_mannequin_mapping()
            
            self.progress_bar.setValue(95)
            self.log_message("매핑 테이블 업데이트 완료 (95%)")
            QtWidgets.QApplication.processEvents()
            
            # 최종 완료 (100%)
            self.progress_bar.setValue(100)
            self.log_message("마네퀸 스켈레톤 생성 완료! (Ctrl+Z로 실행 취소 가능) (100%)")
            QtWidgets.QApplication.processEvents()
            
            # 성공 메시지 표시
            QtWidgets.QMessageBox.information(
                self, "완료", 
                "마네퀸 스켈레톤 생성이 완료되었습니다!\n\n"
                "- 추가 조인트들이 생성되었습니다\n"
                "- 바이패드 계층 구조가 재생성되었습니다\n" 
                "- 기본 마네퀸 본과 연결되었습니다\n"
                "- 로케이터-마네퀸 조인트 컨스트레인트가 연결되었습니다\n"
                "- 매핑 테이블이 자동 업데이트되었습니다\n\n"
                "(모든 작업은 Ctrl+Z로 실행 취소 가능)"
            )
            
        except Exception as e:
            self.log_message(f"스켈레톤 생성 중 오류 발생: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "오류",
                f"스켈레톤 생성 중 오류가 발생했습니다:\n{str(e)}"
            )
        finally:
            self.progress_bar.setVisible(False)
            # Undo 블록 종료
            cmds.undoInfo(closeChunk=True)
            
    def browse_skeleton_file(self):
        """스켈레톤 파일을 찾아봅니다."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "마네퀸 스켈레톤 파일 선택",
            self.skeleton_path,
            "Maya Files (*.ma *.mb);;All Files (*)"
        )
        
        if file_path:
            self.path_line_edit.setText(file_path)
            self.skeleton_path = file_path
            self.log_message(f"스켈레톤 파일 경로 설정: {file_path}")
            
    def import_skeleton(self):
        """스켈레톤을 임포트합니다."""
        try:
            skeleton_path = self.path_line_edit.text().strip()
            
            if not skeleton_path or not os.path.exists(skeleton_path):
                self.log_message("유효한 스켈레톤 파일 경로를 설정해주세요.")
                return
                
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            self.log_message("스켈레톤 임포트 중...")
            success = R8_mannequin_skeleton_rebuild.import_mannequin_skeleton(skeleton_path)
            
            if success:
                self.log_message("스켈레톤 임포트 완료!")
            else:
                self.log_message("스켈레톤 임포트 실패!")
                
        except Exception as e:
            self.log_message(f"임포트 중 오류 발생: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            
    def match_joints(self):
        """조인트를 매칭합니다."""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            self.log_message("조인트 매칭 중...")
            result = R8_mannequin_skeleton_rebuild.mannequin_joint_match()
            
            if isinstance(result, dict):
                if result.get("success", False):
                    self.log_message("조인트 매칭 완료!")
                else:
                    # 매칭 실패 메시지 로그에 추가
                    error_msg = result.get("message", "알 수 없는 매칭 오류")
                    self.log_message(f"매칭 실패: {error_msg}")
                    
                    # 상세 에러 정보가 있으면 로그에 추가
                    error_details = result.get("error_details", [])
                    if error_details:
                        self.log_message("상세 에러 정보:")
                        for detail in error_details:
                            self.log_message(detail)
                    
                    # 에러 타입에 따른 추가 안내 메시지
                    error_type = result.get("error_type", "")
                    if "duplicate" in error_type:
                        self.log_message("해결 방법: 중복된 조인트를 제거한 후 다시 시도하세요.")
                    elif "not_found" in error_type:
                        self.log_message("해결 방법: 필요한 조인트가 씬에 존재하는지 확인하세요.")
            else:
                # 이전 방식 호환성 (결과값이 없는 경우)
                self.log_message("조인트 매칭 완료!")
            
        except Exception as e:
            self.log_message(f"조인트 매칭 중 오류 발생: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            
    def full_process(self):
        """전체 프로세스 (임포트 + 매칭)를 실행합니다."""
        try:
            skeleton_path = self.path_line_edit.text().strip()
            
            if not skeleton_path or not os.path.exists(skeleton_path):
                self.log_message("유효한 스켈레톤 파일 경로를 설정해주세요.")
                return
                
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            self.log_message("전체 프로세스 시작...")
            
            # 1. 스켈레톤 임포트
            self.log_message("1단계: 스켈레톤 임포트 중...")
            success = R8_mannequin_skeleton_rebuild.import_mannequin_skeleton(skeleton_path)
            
            if success:
                self.log_message("스켈레톤 임포트 완료!")
                
                # 2. 조인트 매칭
                self.log_message("2단계: 조인트 매칭 중...")
                result = R8_mannequin_skeleton_rebuild.mannequin_joint_match()
                
                if isinstance(result, dict):
                    if result.get("success", False):
                        self.log_message("조인트 매칭 완료!")
                        self.log_message("전체 프로세스 완료!")
                    else:
                        # 매칭 실패 시 전체 프로세스도 실패로 처리
                        error_msg = result.get("message", "알 수 없는 매칭 오류")
                        self.log_message(f"조인트 매칭 실패: {error_msg}")
                        
                        # 상세 에러 정보가 있으면 로그에 추가
                        error_details = result.get("error_details", [])
                        if error_details:
                            self.log_message("상세 에러 정보:")
                            for detail in error_details:
                                self.log_message(detail)
                        
                        # 에러 타입에 따른 추가 안내 메시지
                        error_type = result.get("error_type", "")
                        if "duplicate" in error_type:
                            self.log_message("해결 방법: 중복된 조인트를 제거한 후 다시 시도하세요.")
                        elif "not_found" in error_type:
                            self.log_message("해결 방법: 필요한 조인트가 씬에 존재하는지 확인하세요.")
                        
                        self.log_message("전체 프로세스가 조인트 매칭 실패로 인해 중단되었습니다.")
                        return  # 조인트 매칭 실패 시 전체 프로세스 중단
                else:
                    # 이전 방식 호환성 (결과값이 없는 경우)
                    self.log_message("조인트 매칭 완료!")
                    self.log_message("전체 프로세스 완료!")
            else:
                self.log_message("스켈레톤 임포트 실패로 인해 프로세스를 중단합니다.")
                
        except Exception as e:
            self.log_message(f"전체 프로세스 중 오류 발생: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            
    def load_biped_to_mannequin_mapping(self):
        """Biped to Mannequin 매핑을 로드하여 테이블에 표시합니다."""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            self.log_message("씬의 조인트 매핑 정보를 로드 중...")
            
            # 현재 씬에 존재하는 조인트들의 매핑 정보 가져오기
            mapping_data = R8_biped_to_mannequin_json.get_scene_joints_mapping()
            
            if not mapping_data:
                self.log_message("매핑할 수 있는 조인트가 씬에 없습니다.")
                return
            
            # 테이블 초기화
            self.mapping_table.setRowCount(len(mapping_data))
            
            # 테이블에 데이터 추가
            row = 0
            for biped_joint, mannequin_joint in mapping_data.items():  # 키와 밸류 순서 바꿈
                # Biped 조인트 (1열)
                biped_item = QtWidgets.QTableWidgetItem(biped_joint)
                biped_item.setFlags(biped_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.mapping_table.setItem(row, 0, biped_item)
                
                # Mannequin 조인트 (2열)
                mannequin_item = QtWidgets.QTableWidgetItem(str(mannequin_joint))
                self.mapping_table.setItem(row, 1, mannequin_item)
                
                row += 1
            
            self.log_message(f"매핑 정보 로드 완료! ({len(mapping_data)}개 조인트)")
            
        except Exception as e:
            self.log_message(f"매핑 로드 중 오류 발생: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            
    def export_mapping_to_json(self):
        """현재 테이블의 매핑 정보를 JSON 파일로 익스포트합니다."""
        try:
            # 테이블에 데이터가 있는지 확인
            if self.mapping_table.rowCount() == 0:
                self.log_message("익스포트할 매핑 데이터가 없습니다.")
                return
            
            # 파일 저장 대화상자
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "매핑 데이터 저장",
                "biped_to_mannequin_mapping.json",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # 테이블에서 매핑 데이터 수집
            mapping_data = {}
            for row in range(self.mapping_table.rowCount()):
                biped_item = self.mapping_table.item(row, 0)
                mannequin_item = self.mapping_table.item(row, 1)
                
                if biped_item and mannequin_item:
                    biped_joint = biped_item.text()
                    mannequin_joint = mannequin_item.text()
                    mapping_data[biped_joint] = mannequin_joint
            
            # JSON으로 익스포트
            success = R8_biped_to_mannequin_json.export_mapping_to_json(file_path, mapping_data)
            
            if success:
                self.log_message(f"매핑 데이터가 성공적으로 익스포트되었습니다: {file_path}")
            else:
                self.log_message("매핑 데이터 익스포트에 실패했습니다.")
                
        except Exception as e:
            self.log_message(f"JSON 익스포트 중 오류 발생: {str(e)}")
            
    def import_mapping_from_json(self):
        """JSON 파일에서 매핑 정보를 임포트하여 테이블에 표시합니다."""
        try:
            # 파일 열기 대화상자
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "매핑 데이터 불러오기",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # JSON에서 매핑 데이터 임포트
            mapping_data = R8_biped_to_mannequin_json.import_mapping_from_json(file_path)
            
            if not mapping_data:
                self.log_message("매핑 데이터를 불러올 수 없습니다.")
                return
            
            # 테이블 초기화 및 데이터 설정
            self.mapping_table.setRowCount(len(mapping_data))
            
            row = 0
            for biped_joint, mannequin_joint in mapping_data.items():
                # Biped 조인트 (1열)
                biped_item = QtWidgets.QTableWidgetItem(biped_joint)
                biped_item.setFlags(biped_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.mapping_table.setItem(row, 0, biped_item)
                
                # Mannequin 조인트 (2열)
                mannequin_item = QtWidgets.QTableWidgetItem(mannequin_joint)
                self.mapping_table.setItem(row, 1, mannequin_item)
                
                row += 1
            
            self.log_message(f"매핑 데이터가 성공적으로 임포트되었습니다: {file_path}")
            
        except Exception as e:
            self.log_message(f"JSON 임포트 중 오류 발생: {str(e)}")
            
    def perform_weight_transfer(self):
        """웨이트 트랜스퍼 수행 (메인 기능) - 다중 메시 지원"""
        try:
            # 메시 이름 가져오기
            mesh_names_text = self.mesh_line_edit.text().strip()
            if not mesh_names_text:
                QtWidgets.QMessageBox.warning(
                    self, "경고",
                    "메시를 선택해주세요."
                )
                return
            
            # 쉼표로 구분된 메시 이름들을 리스트로 변환
            mesh_names = [name.strip() for name in mesh_names_text.split(',') if name.strip()]
            
            if not mesh_names:
                QtWidgets.QMessageBox.warning(
                    self, "경고",
                    "유효한 메시 이름이 없습니다."
                )
                return
            
            # 모든 메시 존재 확인
            missing_meshes = []
            valid_meshes = []
            for mesh_name in mesh_names:
                if cmds.objExists(mesh_name):
                    valid_meshes.append(mesh_name)
                else:
                    missing_meshes.append(mesh_name)
            
            if missing_meshes:
                QtWidgets.QMessageBox.warning(
                    self, "경고",
                    f"다음 메시들이 존재하지 않습니다:\n{', '.join(missing_meshes)}"
                )
                return
            
            # 스킨 클러스터 확인
            meshes_without_skin = []
            for mesh_name in valid_meshes:
                try:
                    skin_cluster = R8_weight_transfer_core.get_skin_cluster(mesh_name)
                    if not skin_cluster:
                        meshes_without_skin.append(mesh_name)
                except:
                    meshes_without_skin.append(mesh_name)
            
            if meshes_without_skin:
                QtWidgets.QMessageBox.warning(
                    self, "경고",
                    f"다음 메시들에 스킨 클러스터가 없습니다:\n{', '.join(meshes_without_skin)}"
                )
                return
            
            # 웨이트 트랜스퍼 모듈 로드 확인
            try:
                R8_weight_transfer_core.get_skin_cluster
            except:
                QtWidgets.QMessageBox.warning(
                    self, "경고",
                    "웨이트 트랜스퍼 모듈을 로드할 수 없습니다."
                )
                return
            
            # 프로그래스바 초기화 및 표시
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.log_message(f"웨이트 트랜스퍼 준비 중... (대상 메시: {len(valid_meshes)}개) (0%)")
            QtWidgets.QApplication.processEvents()
            
            # 전체 프로세스 시작 시간 기록
            total_start_time = time.time()
            
            # 테이블에서 매핑 정보 수집 (5%)
            self.progress_bar.setValue(5)
            self.log_message("조인트 매핑 정보 수집 중... (5%)")
            QtWidgets.QApplication.processEvents()
            
            joint_mapping = {}
            for row in range(self.mapping_table.rowCount()):
                biped_item = self.mapping_table.item(row, 0)
                mannequin_item = self.mapping_table.item(row, 1)
                
                if biped_item and mannequin_item:
                    biped_joint = biped_item.text().strip()
                    mannequin_joint = mannequin_item.text().strip()
                    
                    if biped_joint and mannequin_joint:
                        joint_mapping[biped_joint] = mannequin_joint
            
            if not joint_mapping:
                QtWidgets.QMessageBox.warning(
                    self, "경고",
                    "조인트 매핑 정보가 없습니다. 먼저 매핑을 로드하거나 생성해주세요."
                )
                self.progress_bar.setVisible(False)
                return
            
            # 확인 다이얼로그 표시 (10%)
            self.progress_bar.setValue(10)
            self.log_message("사용자 확인 대기 중... (10%)")
            QtWidgets.QApplication.processEvents()
            
            confirm_msg = f"웨이트 트랜스퍼를 실행하시겠습니까?\n\n"
            confirm_msg += f"대상 메시: {len(valid_meshes)}개\n"
            confirm_msg += f"메시 목록: {', '.join(valid_meshes)}\n"
            confirm_msg += f"조인트 매핑: {len(joint_mapping)}개\n"
            
            reply = QtWidgets.QMessageBox.question(
                self, "웨이트 트랜스퍼 확인",
                confirm_msg,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                try:
                    # 다중 메시 순차 처리
                    total_meshes = len(valid_meshes)
                    successful_meshes = []
                    failed_meshes = []
                    
                    for mesh_index, mesh_name in enumerate(valid_meshes):
                        # 각 메시별 진행률 계산 (15% ~ 95% 구간을 메시 개수로 분할)
                        mesh_start_progress = 15 + (mesh_index * 80) // total_meshes
                        mesh_end_progress = 15 + ((mesh_index + 1) * 80) // total_meshes
                        
                        self.progress_bar.setValue(mesh_start_progress)
                        self.log_message(f"메시 '{mesh_name}' 처리 중... ({mesh_index + 1}/{total_meshes}) ({mesh_start_progress}%)")
                        QtWidgets.QApplication.processEvents()
                        
                        try:
                            # 매핑 검증
                            validation_result = R8_weight_transfer_core.validate_joint_mapping(joint_mapping, mesh_name)
                            valid_mappings = validation_result["valid_mappings"]
                            missing_joints = validation_result["missing_old_joints"] + validation_result["missing_new_joints"]
                            new_joints_to_add = validation_result["new_joints_to_add"]
                            
                            self.log_message(f"메시 '{mesh_name}' 매핑 검증: 유효 {len(valid_mappings)}개, 누락 {len(missing_joints)}개")
                            
                            if not valid_mappings:
                                self.log_message(f"메시 '{mesh_name}': 유효한 매핑이 없어 건너뜀")
                                failed_meshes.append(f"{mesh_name} (유효한 매핑 없음)")
                                continue
                            
                            # 새 조인트들을 스킨 클러스터에 추가
                            if new_joints_to_add:
                                self.log_message(f"메시 '{mesh_name}': 새 조인트 {len(new_joints_to_add)}개 추가 중...")
                                R8_weight_transfer_core.add_joints_to_skin_cluster(mesh_name, new_joints_to_add)
                            
                            # 웨이트 트랜스퍼 실행
                            self.log_message(f"메시 '{mesh_name}': 웨이트 트랜스퍼 실행 중... (매핑 {len(valid_mappings)}개)")
                            
                            def progress_callback(value, message):
                                # 각 메시별 진행률 구간 내에서 세부 진행률 표시
                                progress_range = mesh_end_progress - mesh_start_progress
                                adjusted_value = mesh_start_progress + (value * progress_range) // 100
                                self.progress_bar.setValue(adjusted_value)
                                self.log_message(f"메시 '{mesh_name}': {message} ({adjusted_value}%)")
                                QtWidgets.QApplication.processEvents()
                            
                            mesh_start_time = time.time()
                            result = R8_weight_transfer_core.transfer_weights_to_mapped_joints(
                                mesh_name, valid_mappings, progress_callback
                            )
                            mesh_end_time = time.time()
                            
                            if result.get("success", False):
                                processing_time = mesh_end_time - mesh_start_time
                                success_info = f"{mesh_name} (매핑: {len(valid_mappings)}개, 시간: {processing_time:.2f}초"
                                if new_joints_to_add:
                                    success_info += f", 새 조인트: {len(new_joints_to_add)}개"
                                success_info += ")"
                                successful_meshes.append(success_info)
                                self.log_message(f"메시 '{mesh_name}' 웨이트 트랜스퍼 완료! (시간: {processing_time:.2f}초)")
                            else:
                                error_msg = result.get("error", "알 수 없는 오류")
                                failed_meshes.append(f"{mesh_name} ({error_msg})")
                                self.log_message(f"메시 '{mesh_name}' 웨이트 트랜스퍼 실패: {error_msg}")
                        
                        except Exception as mesh_e:
                            failed_meshes.append(f"{mesh_name} (오류: {str(mesh_e)})")
                            self.log_message(f"메시 '{mesh_name}' 처리 중 오류: {str(mesh_e)}")
                    
                    # 최종 완료 처리 (100%)
                    self.progress_bar.setValue(100)
                    
                    # Maya Optimize 체크박스 확인 후 실행
                    if self.maya_optimize_checkbox.isChecked() and successful_meshes:
                        self.log_message("Maya Optimize Scene Size 실행 중...")
                        try:
                            if "MAYA_TESTING_CLEANUP" not in os.environ:
                                os.environ["MAYA_TESTING_CLEANUP"] = "enable"
                                mel.eval("cleanUpScene 1;")
                                del os.environ["MAYA_TESTING_CLEANUP"]
                            else: 
                                mel.eval("cleanUpScene 1;")
                            self.log_message("Maya Optimize Scene Size 완료!")
                        except Exception as opt_e:
                            self.log_message(f"Maya Optimize Scene Size 실행 중 오류: {str(opt_e)}")
                    
                    # 전체 프로세스 완료 시간 계산
                    total_end_time = time.time()
                    total_time = total_end_time - total_start_time
                    
                    # 결과 메시지 생성
                    result_msg = f"다중 메시 웨이트 트랜스퍼 완료!\n\n"
                    result_msg += f"전체 처리 시간: {total_time:.2f}초\n\n"
                    
                    if successful_meshes:
                        result_msg += f"성공한 메시 ({len(successful_meshes)}개):\n"
                        for success_info in successful_meshes:
                            result_msg += f"✓ {success_info}\n"
                        result_msg += "\n"
                    
                    if failed_meshes:
                        result_msg += f"실패한 메시 ({len(failed_meshes)}개):\n"
                        for failed_info in failed_meshes:
                            result_msg += f"✗ {failed_info}\n"
                        result_msg += "\n"
                    
                    if self.maya_optimize_checkbox.isChecked() and successful_meshes:
                        result_msg += "Maya Optimize Scene Size도 실행되었습니다."
                    
                    self.log_message(f"다중 메시 웨이트 트랜스퍼 프로세스 완료! 성공: {len(successful_meshes)}개, 실패: {len(failed_meshes)}개, 전체 시간: {total_time:.2f}초")
                    
                    # 결과에 따른 메시지 박스 표시
                    if failed_meshes:
                        QtWidgets.QMessageBox.warning(self, "부분 완료", result_msg)
                    else:
                        QtWidgets.QMessageBox.information(self, "완료", result_msg)
                
                except Exception as e:
                    error_msg = f"다중 메시 웨이트 트랜스퍼 중 오류: {str(e)}"
                    self.log_message(error_msg)
                    QtWidgets.QMessageBox.critical(self, "오류", error_msg)
                
                finally:
                    self.progress_bar.setVisible(False)
            else:
                # 사용자가 취소한 경우
                self.progress_bar.setVisible(False)
                self.log_message("웨이트 트랜스퍼가 취소되었습니다.")
        
        except Exception as e:
            self.log_message(f"웨이트 트랜스퍼 준비 중 오류: {str(e)}")
            QtWidgets.QMessageBox.critical(
                self, "오류",
                f"웨이트 트랜스퍼 준비 중 오류가 발생했습니다:\n{str(e)}"
            )
            self.progress_bar.setVisible(False)
    
    def show_help(self):
        """도움말 표시"""
        help_text = """
        <h3>Mannequin Skeleton Generator 도움말</h3>
        
        <h4>Skeleton Path (스켈레톤 파일 경로)</h4>
        <ul>
        <li><b>경로 입력:</b> 마네퀸 스켈레톤 파일(.ma/.mb) 경로를 직접 입력하거나 찾아보기 버튼으로 선택합니다.</li>
        <li><b>찾아보기:</b> 파일 브라우저를 열어 스켈레톤 파일을 선택합니다.</li>
        </ul>
        
        <h4>1. Mannequin Skeleton (마네퀸 스켈레톤 생성)</h4>
        <ul>
        <li><b>Import Skeleton:</b> 설정된 경로에서 스켈레톤 파일을 Maya로 임포트합니다.</li>
        <li><b>Match Joints:</b> 기존 Bip001 바이패드 조인트와 마네퀸 기본 조인트 매칭합니다.</li>
        <li><b>1. Mannequin Skeleton:</b> Import Skeleton + Match Joints를 한 번에 실행하는 전체 프로세스입니다.</li>
        </ul>
        
        <h4>2. Add Sub Skeleton (서브 스켈레톤 추가)</h4>
        <ul>
        <li><b>스킨 메시 입력:</b> 스킨이 적용될 메시 이름을 입력합니다. 여러 메시는 쉼표로 구분하여 입력 가능합니다.</li>
        <li><b>Get Selected Mesh:</b> 현재 Maya에서 선택된 메시를 자동으로 가져옵니다.</li>
        <li><b>Clear:</b> 메시 입력 필드를 지웁니다.</li>
        <li><b>2. Add Sub Skeleton:</b> 선택된 메시의 인플루언스 조인트 또는 모든 Bip001 하위 조인트로 마네퀸 서브 스켈레톤을 생성합니다.</li>
        <li><b>실행 시 매핑 테이블이 자동으로 업데이트됩니다.</b></li>
        </ul>
        
        <h4>3. Weight Transfer (웨이트 트랜스퍼)</h4>
        <ul>
        <li><b>3. Weight Transfer:</b> 현재 매핑 테이블과 선택된 메시를 사용하여 웨이트를 자동으로 바이패드에서 마네퀸 본으로 트랜스퍼합니다.</li>
        <li><b>Maya Optimize Scene Size:</b> 웨이트 트랜스퍼 완료 후 Maya의 씬 최적화(clean Up Scene)를 자동으로 실행합니다. (기본값: 체크됨)</li>
        </ul>
        
        <h4>권장 사용 순서</h4>
        <ol>
        <li><b>스켈레톤 준비:</b> Skeleton Path에서 마네퀸 스켈레톤 파일 경로를 설정</li>
        <li><b>기본 스켈레톤 생성:</b> "1. Mannequin Skeleton" 버튼으로 기본 마네퀸 스켈레톤 생성</li>
        <li><b>메시 선택:</b> 스킨이 적용될 메시를 선택하고 "Get Selected Mesh"로 설정</li>
        <li><b>서브 스켈레톤 추가:</b> "2. Add Sub Skeleton"으로 추가 조인트 생성 (매핑 테이블 자동 업데이트)</li>
        <li><b>매핑 확인/수정:</b> 자동 생성된 테이블에서 매핑 관계를 확인하고 필요시 수정</li>
        <li><b>웨이트 트랜스퍼:</b> "3. Weight Transfer"로 웨이트 데이터 이전 (Maya Optimize 자동 실행)</li>
        </ol>
        
        <h4>주요 기능</h4>
        <ul>
        <li><b>자동 매핑:</b> "2. Add Sub Skeleton" 실행 시 바이패드-마네퀸 조인트 매핑이 자동으로 생성됩니다.</li>
        <li><b>진행 상황 표시:</b> 각 작업의 진행률이 프로그래스바로 표시됩니다.</li>
        <li><b>실행 시간 측정:</b> 웨이트 트랜스퍼 작업 시간과 전체 프로세스 시간을 측정하여 표시합니다.</li>
        <li><b>로그 출력:</b> 모든 작업 내용과 결과가 하단 로그 창에 기록됩니다.</li>
        <li><b>JSON 저장/로드:</b> 매핑 정보를 파일로 저장하여 재사용할 수 있습니다.</li>
        <li><b>다중 메시 지원:</b> 여러 메시를 쉼표로 구분하여 동시에 처리할 수 있습니다.</li>
        <li><b>자동 최적화:</b> 웨이트 트랜스퍼 완료 후 Maya 씬 최적화를 자동으로 실행합니다.</li>
        </ul>
        
        <h4>웨이트 트랜스퍼 세부 과정</h4>
        <ul>
        <li><b>매핑 검증:</b> 존재하지 않는 조인트를 확인하고 사용자에게 알립니다.</li>
        <li><b>새 조인트 추가:</b> 필요한 경우 새로운 조인트를 스킨 클러스터에 자동으로 추가합니다.</li>
        <li><b>웨이트 데이터 전송:</b> 기존 조인트의 웨이트를 새 조인트로 복사합니다.</li>
        <li><b>씬 최적화:</b> 체크박스가 선택된 경우 Maya의 cleanUpScene을 실행합니다.</li>
        </ul>
        
        <h4>주의사항</h4>
        <ul>
        <li><b>순서 준수:</b> 각 단계는 순서대로 실행하는 것을 강력히 권장합니다.</li>
        <li><b>매핑 확인:</b> 웨이트 트랜스퍼 전에 반드시 매핑 테이블이 올바른지 확인하세요.</li>
        <li><b>백업:</b> 작업 전 씬을 저장하고, 문제 발생 시 Ctrl+Z로 되돌릴 수 있습니다.</li>
        <li><b>처리 시간:</b> 대용량 메시나 복잡한 스켈레톤의 경우 처리 시간이 오래 걸릴 수 있습니다.</li>
        <li><b>메시 선택:</b> 웨이트 트랜스퍼 시 반드시 스킨 클러스터가 적용된 메시를 선택해야 합니다.</li>
        </ul>
        
        <h4>문제 해결</h4>
        <ul>
        <li><b>매핑 테이블이 비어있는 경우:</b> "2. Add Sub Skeleton"을 먼저 실행하거나 JSON 파일을 임포트하세요.</li>
        <li><b>조인트가 존재하지 않는 경우:</b> 매핑 검증에서 확인되며, 유효한 매핑만으로 진행할 수 있습니다.</li>
        <li><b>스킨 클러스터가 없는 경우:</b> 메시에 스킨 클러스터가 적용되어 있는지 확인하세요.</li>
        <li><b>처리 시간이 오래 걸리는 경우:</b> 로그 창에서 진행 상황을 확인하고 기다려주세요.</li>
        </ul>
        """
        
        # 스크롤 가능한 도움말 다이얼로그 생성
        help_dialog = QtWidgets.QDialog(self)
        help_dialog.setWindowTitle("도움말")
        help_dialog.resize(700, 600)
        help_dialog.setWindowFlags(help_dialog.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        # 레이아웃 설정
        layout = QtWidgets.QVBoxLayout(help_dialog)
        
        # 스크롤 가능한 텍스트 위젯
        text_widget = QtWidgets.QTextEdit()
        text_widget.setHtml(help_text)
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)
        
        # 닫기 버튼
        close_button = QtWidgets.QPushButton("닫기")
        close_button.clicked.connect(help_dialog.close)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        help_dialog.exec_()


def show_ui():
    """UI 표시 함수"""
    global mannequin_skeleton_window
    try:
        mannequin_skeleton_window.close()
        mannequin_skeleton_window.deleteLater()
    except:
        pass
    
    mannequin_skeleton_window = MannequinSkeletonUI()
    mannequin_skeleton_window.show()
    
if __name__ == "__main__":
    show_ui() 