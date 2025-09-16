"""
웨이트 정보 다이얼로그 클래스
"""

import os
import time
import json
import xml.etree.ElementTree as ET
import maya.cmds as cmds

# PySide 임포트 (Maya 버전에 따라)
try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
    PYSIDE_VERSION = 6
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore, QtGui
        from shiboken2 import wrapInstance
        PYSIDE_VERSION = 2
    except ImportError:
        try:
            from PySide import QtGui as QtWidgets, QtCore
            from shiboken import wrapInstance
            QtWidgets.QWidget = QtWidgets.QWidget
            PYSIDE_VERSION = 1
        except ImportError:
            raise ImportError("PySide를 찾을 수 없습니다. Maya에서 실행해주세요.")

import maya.OpenMayaUI as omui


def get_maya_main_window():
    """Maya 메인 윈도우를 반환합니다."""
    try:
        main_window_ptr = omui.MQtUtil.mainWindow()
        if main_window_ptr is None:
            return None
            
        # 포인터 값 검증
        ptr_value = int(main_window_ptr)
        if ptr_value == 0:
            return None
            
        return wrapInstance(ptr_value, QtWidgets.QWidget)
    except Exception as e:
        print(f"Maya 메인 윈도우 가져오기 오류: {str(e)}")
        return None


class WeightInfoDialog(QtWidgets.QDialog):
    """웨이트 파일 정보를 보여주는 팝업 다이얼로그"""
    
    def __init__(self, folder_data, parent=None):
        # 부모 위젯을 None으로 설정하여 독립적인 다이얼로그로 실행
        super(WeightInfoDialog, self).__init__(None)
        
        # folder_data 유효성 검사
        if not folder_data:
            raise ValueError("folder_data가 None입니다.")
        
        required_keys = ['name', 'path', 'file_count', 'modified']
        missing_keys = [key for key in required_keys if key not in folder_data]
        if missing_keys:
            raise ValueError(f"folder_data에 필수 키가 없습니다: {missing_keys}")
            
        self.folder_data = folder_data
        self.parent_ui = parent  # 부모 UI 참조를 별도로 저장
        
        # 윈도우 설정
        self.setWindowTitle(f"웨이트 정보 - {folder_data['name']}")
        self.resize(900, 700)  # 크기 증가
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        # Maya 메인 윈도우 위에 표시되도록 설정
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        
        try:
            self.create_widgets()
            self.create_layouts()
            self.create_connections()
            self.load_weight_files()
        except Exception as e:
            print(f"WeightInfoDialog 초기화 오류: {str(e)}")
            raise e
    
    def create_widgets(self):
        """위젯들을 생성합니다."""
        # 폴더 정보 그룹
        self.folder_info_group = QtWidgets.QGroupBox("폴더 정보")
        self.folder_name_label = QtWidgets.QLabel(f"폴더명: {self.folder_data['name']}")
        self.folder_path_label = QtWidgets.QLabel(f"경로: {self.folder_data['path']}")
        self.folder_file_count_label = QtWidgets.QLabel(f"파일 수: {self.folder_data['file_count']}개")
        date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.folder_data['modified']))
        self.folder_modified_label = QtWidgets.QLabel(f"수정 시간: {date_str}")
        
        # 파일 목록 테이블
        self.files_group = QtWidgets.QGroupBox("웨이트 파일 목록")
        self.files_table = QtWidgets.QTableWidget()
        self.files_table.setColumnCount(6)
        self.files_table.setHorizontalHeaderLabels(["파일명", "메시명", "크기", "형식", "수정 시간", "조인트 수"])
        self.files_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.files_table.setAlternatingRowColors(True)
        
        # 컬럼 너비 조정
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)  # 파일명
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)  # 메시명
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)  # 크기
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)  # 형식
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)  # 수정 시간
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)  # 조인트 수
        
        # 조인트 매핑 그룹
        self.joint_mapping_group = QtWidgets.QGroupBox("조인트 매핑")
        
        # Import 버튼들
        self.import_label = QtWidgets.QLabel("조인트 매핑 불러오기:")
        self.import_label.setStyleSheet("font-weight: bold; color: blue;")
        
        self.import_xml_btn = QtWidgets.QPushButton("Import XML")
        self.import_xml_btn.setFixedWidth(120)
        self.import_xml_btn.setMinimumHeight(30)
        self.import_xml_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        self.import_json_btn = QtWidgets.QPushButton("Import JSON")
        self.import_json_btn.setFixedWidth(120)
        self.import_json_btn.setMinimumHeight(30)
        self.import_json_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        
        # 조인트 테이블
        self.joint_table = QtWidgets.QTableWidget()
        self.joint_table.setColumnCount(2)
        self.joint_table.setHorizontalHeaderLabels(["JointName", "Set JointName"])
        self.joint_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.joint_table.setAlternatingRowColors(True)
        
        # 조인트 테이블 컬럼 너비 조정
        joint_header = self.joint_table.horizontalHeader()
        joint_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        joint_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        
        # 검색 위젯
        self.search_label = QtWidgets.QLabel("Search:")
        self.search_field = QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("조인트명 검색...")
        
        # 교체 위젯
        self.replace_label = QtWidgets.QLabel("Replace:")
        self.replace_field = QtWidgets.QLineEdit()
        self.replace_field.setPlaceholderText("교체할 텍스트")
        
        # Search/Replace 적용 버튼
        self.apply_search_replace_btn = QtWidgets.QPushButton("Apply")
        self.apply_search_replace_btn.setFixedWidth(80)
        
        # 접두사/접미사 위젯
        self.prefix_label = QtWidgets.QLabel("Prefix:")
        self.prefix_field = QtWidgets.QLineEdit()
        self.prefix_field.setPlaceholderText("접두사")
        
        self.suffix_label = QtWidgets.QLabel("Suffix:")
        self.suffix_field = QtWidgets.QLineEdit()
        self.suffix_field.setPlaceholderText("접미사")
        
        # 접두사/접미사 적용 버튼
        self.apply_prefix_suffix_btn = QtWidgets.QPushButton("Apply")
        self.apply_prefix_suffix_btn.setFixedWidth(80)
        
        # 메시 선택 위젯들
        self.mesh_label = QtWidgets.QLabel("Target Mesh:")
        self.mesh_field = QtWidgets.QLineEdit()
        self.mesh_field.setPlaceholderText("적용할 메시명을 입력하세요")
        self.get_selected_mesh_btn = QtWidgets.QPushButton("Get Selected")
        self.get_selected_mesh_btn.setFixedWidth(100)
        
        # 버튼들
        self.apply_weight_btn = QtWidgets.QPushButton("Apply Weight")
        
        # 기존 버튼들
        self.apply_mapping_btn = QtWidgets.QPushButton("매핑 적용")
        self.close_btn = QtWidgets.QPushButton("닫기")
    
    def create_layouts(self):
        """레이아웃을 생성합니다."""
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # 폴더 정보 레이아웃
        folder_info_layout = QtWidgets.QVBoxLayout(self.folder_info_group)
        folder_info_layout.addWidget(self.folder_name_label)
        folder_info_layout.addWidget(self.folder_path_label)
        folder_info_layout.addWidget(self.folder_file_count_label)
        folder_info_layout.addWidget(self.folder_modified_label)
        
        # 파일 목록 레이아웃
        files_layout = QtWidgets.QVBoxLayout(self.files_group)
        files_layout.addWidget(self.files_table)
        
        # 조인트 매핑 레이아웃
        joint_mapping_layout = QtWidgets.QVBoxLayout(self.joint_mapping_group)
        
        # Import 버튼 레이아웃
        import_btn_layout = QtWidgets.QHBoxLayout()
        import_btn_layout.addWidget(self.import_label)
        import_btn_layout.addWidget(self.import_xml_btn)
        import_btn_layout.addWidget(self.import_json_btn)
        import_btn_layout.addStretch()  # 오른쪽 공간 채우기
        
        # Search/Replace 수평 레이아웃
        search_replace_layout = QtWidgets.QHBoxLayout()
        search_replace_layout.addWidget(self.search_label)
        search_replace_layout.addWidget(self.search_field)
        search_replace_layout.addWidget(self.replace_label)
        search_replace_layout.addWidget(self.replace_field)
        search_replace_layout.addWidget(self.apply_search_replace_btn)
        
        # Prefix/Suffix 수평 레이아웃
        prefix_suffix_layout = QtWidgets.QHBoxLayout()
        prefix_suffix_layout.addWidget(self.prefix_label)
        prefix_suffix_layout.addWidget(self.prefix_field)
        prefix_suffix_layout.addWidget(self.suffix_label)
        prefix_suffix_layout.addWidget(self.suffix_field)
        prefix_suffix_layout.addWidget(self.apply_prefix_suffix_btn)
        prefix_suffix_layout.addStretch()  # 오른쪽 공간 채우기
        
        joint_mapping_layout.addLayout(import_btn_layout)
        joint_mapping_layout.addLayout(search_replace_layout)
        joint_mapping_layout.addLayout(prefix_suffix_layout)
        joint_mapping_layout.addWidget(self.joint_table)
        
        # 메시 선택 레이아웃
        mesh_selection_layout = QtWidgets.QHBoxLayout()
        mesh_selection_layout.addWidget(self.mesh_label)
        mesh_selection_layout.addWidget(self.mesh_field)
        mesh_selection_layout.addWidget(self.get_selected_mesh_btn)
        mesh_selection_layout.addStretch()  # 오른쪽 공간 채우기
        
        joint_mapping_layout.addLayout(mesh_selection_layout)
        
        # 조인트 매핑 버튼 레이아웃
        joint_btn_layout = QtWidgets.QHBoxLayout()
        joint_btn_layout.addWidget(self.apply_weight_btn)
        
        joint_mapping_layout.addLayout(joint_btn_layout)
        
        # 메인 버튼 레이아웃
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.apply_mapping_btn)
        button_layout.addWidget(self.close_btn)
        
        # 메인 레이아웃에 추가
        main_layout.addWidget(self.folder_info_group)
        main_layout.addWidget(self.files_group)
        main_layout.addWidget(self.joint_mapping_group)
        main_layout.addLayout(button_layout)
    
    def create_connections(self):
        """시그널과 슬롯을 연결합니다."""
        self.apply_mapping_btn.clicked.connect(self.apply_mapping)
        self.close_btn.clicked.connect(self.close)
        self.files_table.selectionModel().selectionChanged.connect(self.on_file_selection_changed)
        
        # Import 버튼 연결
        self.import_xml_btn.clicked.connect(self.import_xml_mapping)
        self.import_json_btn.clicked.connect(self.import_json_mapping)
        
        # 조인트 매핑 연결
        self.search_field.textChanged.connect(self.filter_joints)
        self.apply_search_replace_btn.clicked.connect(self.apply_search_replace)
        self.apply_prefix_suffix_btn.clicked.connect(self.apply_prefix_suffix)
        self.get_selected_mesh_btn.clicked.connect(self.get_selected_mesh)
        self.apply_weight_btn.clicked.connect(self.apply_weight_to_selected_mesh)
    
    def load_weight_files(self):
        """_skinWeight 파일들을 로드하여 테이블에 표시합니다."""
        try:
            folder_path = self.folder_data['path']
            print(f"폴더 경로: {folder_path}")
            
            if not os.path.exists(folder_path):
                print(f"폴더가 존재하지 않습니다: {folder_path}")
                self.files_table.setRowCount(0)
                return
            
            skinweight_files = []
            
            try:
                for filename in os.listdir(folder_path):
                    if ("_skinweight" in filename.lower() and 
                        filename.lower().endswith(('.xml', '.json'))):
                        file_path = os.path.join(folder_path, filename)
                        
                        try:
                            # 파일 정보 수집
                            file_info = {
                                'name': filename,
                                'path': file_path,
                                'size': os.path.getsize(file_path),
                                'modified': os.path.getmtime(file_path),
                                'format': os.path.splitext(filename)[1].upper()[1:],
                                'mesh_name': self.extract_mesh_name(filename),
                                'joint_count': self.get_joint_count(file_path)
                            }
                            skinweight_files.append(file_info)
                            print(f"파일 로드 성공: {filename}")
                        except Exception as file_error:
                            print(f"파일 '{filename}' 로드 실패: {str(file_error)}")
                            # 파일 로드에 실패해도 계속 진행
                            continue
                
                # 수정 시간 기준으로 내림차순 정렬
                skinweight_files.sort(key=lambda x: x['modified'], reverse=True)
                
                # 테이블에 표시
                self.files_table.setRowCount(len(skinweight_files))
                
                for i, file_info in enumerate(skinweight_files):
                    try:
                        # 파일명
                        name_item = QtWidgets.QTableWidgetItem(file_info['name'])
                        name_item.setData(QtCore.Qt.UserRole, file_info)  # 파일 정보 저장
                        self.files_table.setItem(i, 0, name_item)
                        
                        # 메시명
                        mesh_item = QtWidgets.QTableWidgetItem(file_info['mesh_name'])
                        self.files_table.setItem(i, 1, mesh_item)
                        
                        # 크기
                        size_str = self.format_file_size(file_info['size'])
                        size_item = QtWidgets.QTableWidgetItem(size_str)
                        self.files_table.setItem(i, 2, size_item)
                        
                        # 형식
                        format_item = QtWidgets.QTableWidgetItem(file_info['format'])
                        self.files_table.setItem(i, 3, format_item)
                        
                        # 수정 시간
                        date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(file_info['modified']))
                        date_item = QtWidgets.QTableWidgetItem(date_str)
                        self.files_table.setItem(i, 4, date_item)
                        
                        # 조인트 수
                        joint_count_item = QtWidgets.QTableWidgetItem(str(file_info['joint_count']))
                        self.files_table.setItem(i, 5, joint_count_item)
                        
                    except Exception as table_error:
                        print(f"테이블 항목 추가 실패 (행 {i}): {str(table_error)}")
                        continue
                
                print(f"총 {len(skinweight_files)}개의 웨이트 파일을 로드했습니다.")
                        
            except Exception as dir_error:
                print(f"디렉토리 읽기 오류: {str(dir_error)}")
                raise dir_error
                
        except Exception as e:
            print(f"load_weight_files 전체 오류: {str(e)}")
            raise e  # 상위로 오류를 전달하여 show_weight_info에서 처리할 수 있도록 함
    
    def extract_mesh_name(self, filename):
        """파일명에서 메시명을 추출합니다."""
        # {메시명}_skinWeights.확장자 형식에서 메시명 추출
        name_without_ext = os.path.splitext(filename)[0]
        if "_skinweight" in name_without_ext.lower():
            mesh_name = name_without_ext.split("_skinweight")[0].split("_skinWeight")[0]
            return mesh_name if mesh_name else "알 수 없음"
        return "알 수 없음"
    
    def get_joint_count(self, file_path):
        """파일에서 조인트 개수를 추출합니다."""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.xml':
                tree = ET.parse(file_path)
                root = tree.getroot()
                influences_elem = root.find("Influences")
                if influences_elem:
                    return len(influences_elem.findall("Influence"))
                    
            elif file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'influences' in data:
                        return len(data['influences'])
                        
        except Exception as e:
            print(f"조인트 개수 추출 오류: {str(e)}")
        
        return 0
    
    def format_file_size(self, size_bytes):
        """파일 크기를 읽기 쉬운 형식으로 변환합니다."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def on_file_selection_changed(self):
        """파일 선택 변경 시 조인트 테이블을 업데이트합니다."""
        selected_rows = self.files_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            file_item = self.files_table.item(row, 0)
            if file_item:
                file_info = file_item.data(QtCore.Qt.UserRole)
                if file_info:
                    self.load_joint_mapping(file_info)
                    return
        
        self.joint_table.setRowCount(0)
    
    def load_joint_mapping(self, file_info):
        """선택된 파일의 조인트 매핑을 로드합니다."""
        joint_list = self.get_joint_list(file_info['path'])
        
        if not joint_list:
            self.joint_table.setRowCount(0)
            return
        
        self.joint_table.setRowCount(len(joint_list))
        
        for i, joint_name in enumerate(joint_list):
            # 원본 조인트명
            original_item = QtWidgets.QTableWidgetItem(joint_name)
            original_item.setFlags(original_item.flags() & ~QtCore.Qt.ItemIsEditable)  # 읽기 전용
            
            self.joint_table.setItem(i, 0, original_item)
            
            # 설정할 조인트명 (편집 가능)
            target_item = QtWidgets.QTableWidgetItem(joint_name)
            target_item.setFlags(target_item.flags() | QtCore.Qt.ItemIsEditable)
            self.joint_table.setItem(i, 1, target_item)
    
    def get_joint_list(self, file_path):
        """파일에서 조인트 목록을 추출합니다."""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.xml':
                tree = ET.parse(file_path)
                root = tree.getroot()
                influences_elem = root.find("Influences")
                if influences_elem:
                    joints = []
                    for inf_elem in influences_elem.findall("Influence"):
                        joint_name = inf_elem.get("name")
                        if joint_name:
                            joints.append(joint_name)
                    return joints
                    
            elif file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'influences' in data:
                        return list(data['influences'])
                        
        except Exception as e:
            print(f"조인트 목록 추출 오류: {str(e)}")
        
        return []
    
    def filter_joints(self):
        """검색 텍스트에 따라 조인트를 필터링합니다."""
        search_text = self.search_field.text().lower()
        
        for row in range(self.joint_table.rowCount()):
            joint_item = self.joint_table.item(row, 0)
            if joint_item:
                joint_name = joint_item.text().lower()
                should_show = search_text in joint_name if search_text else True
                self.joint_table.setRowHidden(row, not should_show)

    def get_joint_mapping_dict(self):
        """현재 조인트 매핑을 딕셔너리로 반환합니다."""
        mapping_dict = {}
        
        for row in range(self.joint_table.rowCount()):
            original_item = self.joint_table.item(row, 0)
            target_item = self.joint_table.item(row, 1)
            
            if original_item and target_item:
                original_name = original_item.text()
                target_name = target_item.text()
                
                # 이름이 다를 때만 매핑에 추가
                if original_name != target_name and target_name.strip():
                    mapping_dict[original_name] = target_name
        
        return mapping_dict

    def apply_remapping(self):
        """Search, Replace, Prefix, Suffix 내용을 joint_table에 반영합니다."""
        search_text = self.search_field.text()
        replace_text = self.replace_field.text()
        prefix = self.prefix_field.text()
        suffix = self.suffix_field.text()
        
        # 모든 행에 대해 처리
        for row in range(self.joint_table.rowCount()):
            target_item = self.joint_table.item(row, 1)
            if target_item:
                current_name = target_item.text()
                new_name = current_name
                
                # Search & Replace 적용
                if search_text and replace_text:
                    new_name = new_name.replace(search_text, replace_text)
                
                # Prefix & Suffix 적용
                if prefix or suffix:
                    new_name = f"{prefix}{new_name}{suffix}"
                
                target_item.setText(new_name)
        
        # 적용 후 필드 초기화
        self.search_field.clear()
        self.replace_field.clear()
        self.prefix_field.clear()
        self.suffix_field.clear()
        
        QtWidgets.QMessageBox.information(self, "리매핑 완료", "조인트 리매핑이 테이블에 적용되었습니다.")
    
    def apply_weight_to_selected_mesh(self):
        """조인트 리매핑을 적용하여 선택한 메시에 웨이트 스킨을 바로 적용합니다."""
        try:
            # Core 클래스 임포트
            from R8_MaxtoMaya.R8_weight_skin_IO import SkinWeightIOCore
            
            # 선택된 파일 정보 가져오기
            selected_rows = self.files_table.selectionModel().selectedRows()
            if not selected_rows:
                QtWidgets.QMessageBox.warning(self, "경고", "먼저 웨이트 파일을 선택해주세요.")
                return
            
            row = selected_rows[0].row()
            file_item = self.files_table.item(row, 0)
            if not file_item:
                QtWidgets.QMessageBox.warning(self, "경고", "선택된 파일 정보를 가져올 수 없습니다.")
                return
            
            file_info = file_item.data(QtCore.Qt.UserRole)
            if not file_info:
                QtWidgets.QMessageBox.warning(self, "경고", "파일 정보를 가져올 수 없습니다.")
                return
            
            # 텍스트 필드에서 메시명 가져오기 (우선순위)
            mesh_name = self.mesh_field.text().strip()
            
            # 메시명이 비어있는 경우 Maya 선택에서 가져오기
            if not mesh_name:
                selected_meshes = cmds.ls(selection=True, type="transform")
                if not selected_meshes:
                    QtWidgets.QMessageBox.warning(self, "경고", "메시명을 입력하거나 Maya에서 메시를 선택해주세요.")
                    return
                mesh_name = selected_meshes[0]
            
            # 메시가 존재하는지 확인
            if not cmds.objExists(mesh_name):
                QtWidgets.QMessageBox.warning(self, "경고", f"메시 '{mesh_name}'를 찾을 수 없습니다.")
                return
            
            # 메시가 실제로 메시인지 확인
            shapes = cmds.listRelatives(mesh_name, shapes=True, type="mesh")
            if not shapes:
                QtWidgets.QMessageBox.warning(self, "경고", f"선택된 객체 '{mesh_name}'는 메시가 아닙니다.")
                return
            
            # 조인트 리매핑 딕셔너리 생성
            joint_remap_dict = self.get_joint_mapping_dict()
            
            # 파일 확장자에 따라 적절한 불러오기 함수 호출
            file_path = file_info['path']
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # 진행 상황 표시를 위한 다이얼로그
            progress_dialog = QtWidgets.QProgressDialog("웨이트 적용 중...", "취소", 0, 100, self)
            progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
            progress_dialog.show()
            
            def update_progress(value, message=""):
                progress_dialog.setValue(value)
                progress_dialog.setLabelText(message)
                QtWidgets.QApplication.processEvents()
            
            success = False
            if file_ext == '.xml':
                success = SkinWeightIOCore.import_weights_from_xml(
                    file_path, mesh_name, update_progress, joint_remap_dict
                )
            elif file_ext == '.json':
                success = SkinWeightIOCore.import_weights_from_json(
                    file_path, mesh_name, update_progress, joint_remap_dict
                )
            
            progress_dialog.close()
            
            if success:
                remap_info = f" (조인트 리매핑: {len(joint_remap_dict)}개)" if joint_remap_dict else ""
                QtWidgets.QMessageBox.information(self, "적용 완료", 
                    f"웨이트가 성공적으로 적용되었습니다.\n"
                    f"파일: {file_info['name']}\n"
                    f"메시: {mesh_name}{remap_info}")
            else:
                QtWidgets.QMessageBox.critical(self, "적용 실패", "웨이트 적용에 실패했습니다.")
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"웨이트 적용 중 오류가 발생했습니다:\n{str(e)}")

    def apply_mapping(self):
        """조인트 매핑을 메인 UI에 적용하고 다이얼로그를 닫습니다."""
        try:
            # 현재 조인트 매핑 가져오기
            joint_mapping = self.get_joint_mapping_dict()
            
            if joint_mapping and self.parent_ui:
                # 부모 UI (SkinWeightImportUI)에 조인트 매핑 적용
                parent_ui = self.parent_ui
                
                # 조인트 리매핑 활성화
                parent_ui.remap_enable_check.setChecked(True)
                
                # 기존 매핑 클리어
                parent_ui.clear_joint_remap()
                
                # 새로운 매핑 추가
                for source_joint, target_joint in joint_mapping.items():
                    row_count = parent_ui.joint_remap_table.rowCount()
                    parent_ui.joint_remap_table.insertRow(row_count)
                    
                    source_item = QtWidgets.QTableWidgetItem(source_joint)
                    source_item.setFlags(source_item.flags() | QtCore.Qt.ItemIsEditable)
                    target_item = QtWidgets.QTableWidgetItem(target_joint)
                    target_item.setFlags(target_item.flags() | QtCore.Qt.ItemIsEditable)
                    
                    parent_ui.joint_remap_table.setItem(row_count, 0, source_item)
                    parent_ui.joint_remap_table.setItem(row_count, 1, target_item)
                
                # 성공 메시지 표시
                QtWidgets.QMessageBox.information(self, "조인트 매핑 적용", 
                    f"{len(joint_mapping)}개의 조인트 매핑이 불러오기 탭에 적용되었습니다.")
            
            # 다이얼로그 닫기
            self.close()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"조인트 매핑 적용 중 오류가 발생했습니다:\n{str(e)}")

    def apply_search_replace(self):
        """Search/Replace 기능을 적용합니다. JointName에서 Search 텍스트를 찾아 Replace하고 SetJointName에 적용합니다."""
        search_text = self.search_field.text().strip()
        replace_text = self.replace_field.text()  # strip() 제거 - 공백도 유효한 replace 값
        
        if not search_text:
            QtWidgets.QMessageBox.warning(self, "경고", "검색할 텍스트를 입력해주세요.")
            return
        
        # Replace 텍스트가 공란이어도 적용 가능 (삭제 기능)
        
        replaced_count = 0
        
        # 모든 행에 대해 처리
        for row in range(self.joint_table.rowCount()):
            original_item = self.joint_table.item(row, 0)  # JointName 컬럼
            target_item = self.joint_table.item(row, 1)    # SetJointName 컬럼
            
            if original_item and target_item:
                original_name = original_item.text()
                
                # JointName에서 Search 텍스트가 포함되어 있는지 확인
                if search_text in original_name:
                    # Search 텍스트를 Replace 텍스트로 교체 (공란 포함)
                    new_name = original_name.replace(search_text, replace_text)
                    target_item.setText(new_name)
                    replaced_count += 1
        
        # 결과 메시지 표시
        if replaced_count > 0:
            if replace_text:
                QtWidgets.QMessageBox.information(self, "적용 완료", 
                    f"'{search_text}' → '{replace_text}' 교체 완료\n"
                    f"적용된 조인트 수: {replaced_count}개")
            else:
                QtWidgets.QMessageBox.information(self, "적용 완료", 
                    f"'{search_text}' 텍스트 삭제 완료\n"
                    f"적용된 조인트 수: {replaced_count}개")
        else:
            QtWidgets.QMessageBox.information(self, "적용 결과", 
                f"'{search_text}' 텍스트를 포함한 조인트가 없습니다.")
        
        # 적용 후 필드 초기화
        self.search_field.clear()
        self.replace_field.clear()

    def apply_prefix_suffix(self):
        """Prefix/Suffix 기능을 적용합니다. 현재 SetJointName 값에 접두사/접미사를 추가합니다."""
        prefix_text = self.prefix_field.text()
        suffix_text = self.suffix_field.text()
        
        if not prefix_text and not suffix_text:
            QtWidgets.QMessageBox.warning(self, "경고", "접두사 또는 접미사 중 하나 이상을 입력해주세요.")
            return
        
        applied_count = 0
        
        # 모든 행에 대해 처리
        for row in range(self.joint_table.rowCount()):
            target_item = self.joint_table.item(row, 1)    # SetJointName 컬럼
            
            if target_item:
                # 현재 SetJointName 값을 기준으로 접두사/접미사 적용
                current_name = target_item.text()
                
                # 접두사/접미사 적용
                new_name = f"{prefix_text}{current_name}{suffix_text}"
                target_item.setText(new_name)
                applied_count += 1
        
        # 결과 메시지 표시
        if applied_count > 0:
            prefix_info = f"접두사: '{prefix_text}'" if prefix_text else ""
            suffix_info = f"접미사: '{suffix_text}'" if suffix_text else ""
            
            if prefix_text and suffix_text:
                message = f"{prefix_info}, {suffix_info} 적용 완료"
            else:
                message = f"{prefix_info}{suffix_info} 적용 완료"
            
            QtWidgets.QMessageBox.information(self, "적용 완료", 
                f"{message}\n적용된 조인트 수: {applied_count}개")
        else:
            QtWidgets.QMessageBox.information(self, "적용 결과", 
                "적용할 조인트가 없습니다.")
        
        # 적용 후 필드 초기화
        self.prefix_field.clear()
        self.suffix_field.clear()

    def get_selected_mesh(self):
        """Maya에서 선택된 메시를 텍스트 필드에 설정합니다."""
        try:
            # Maya에서 선택된 메시 확인
            selected_meshes = cmds.ls(selection=True, type="transform")
            
            if not selected_meshes:
                QtWidgets.QMessageBox.warning(self, "경고", "Maya에서 메시를 선택해주세요.")
                return
            
            mesh_name = selected_meshes[0]
            
            # 메시가 실제로 메시인지 확인
            shapes = cmds.listRelatives(mesh_name, shapes=True, type="mesh")
            if not shapes:
                QtWidgets.QMessageBox.warning(self, "경고", f"선택된 객체 '{mesh_name}'는 메시가 아닙니다.")
                return
            
            # 텍스트 필드에 메시명 설정
            self.mesh_field.setText(mesh_name)
            
            # 성공 메시지 표시
            QtWidgets.QMessageBox.information(self, "메시 선택", f"메시 '{mesh_name}'가 선택되었습니다.")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"메시 선택 중 오류가 발생했습니다:\n{str(e)}")

    def import_xml_mapping(self):
        """XML 파일에서 조인트 매핑을 가져옵니다."""
        try:
            # 파일 선택 다이얼로그
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, 
                "XML 파일 선택",
                "",
                "XML Files (*.xml);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # XML 파일에서 조인트 목록 추출
            joint_list = self.get_joint_list(file_path)
            
            if not joint_list:
                QtWidgets.QMessageBox.warning(self, "경고", "XML 파일에서 조인트 정보를 찾을 수 없습니다.")
                return
            
            # 조인트 테이블에 로드
            self.load_joint_mapping_from_list(joint_list)
            
            # 성공 메시지
            QtWidgets.QMessageBox.information(self, "불러오기 완료", 
                f"XML 파일에서 {len(joint_list)}개의 조인트 매핑을 불러왔습니다.\n파일: {os.path.basename(file_path)}")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"XML 파일 불러오기 중 오류가 발생했습니다:\n{str(e)}")

    def import_json_mapping(self):
        """JSON 파일에서 조인트 매핑을 가져옵니다."""
        try:
            # 파일 선택 다이얼로그
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "JSON 파일 선택",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # JSON 파일에서 조인트 목록 추출
            joint_list = self.get_joint_list(file_path)
            
            if not joint_list:
                QtWidgets.QMessageBox.warning(self, "경고", "JSON 파일에서 조인트 정보를 찾을 수 없습니다.")
                return
            
            # 조인트 테이블에 로드
            self.load_joint_mapping_from_list(joint_list)
            
            # 성공 메시지
            QtWidgets.QMessageBox.information(self, "불러오기 완료", 
                f"JSON 파일에서 {len(joint_list)}개의 조인트 매핑을 불러왔습니다.\n파일: {os.path.basename(file_path)}")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"JSON 파일 불러오기 중 오류가 발생했습니다:\n{str(e)}")

    def load_joint_mapping_from_list(self, joint_list):
        """조인트 목록을 테이블에 로드합니다."""
        if not joint_list:
            self.joint_table.setRowCount(0)
            return
        
        self.joint_table.setRowCount(len(joint_list))
        
        for i, joint_name in enumerate(joint_list):
            # 원본 조인트명
            original_item = QtWidgets.QTableWidgetItem(joint_name)
            original_item.setFlags(original_item.flags() & ~QtCore.Qt.ItemIsEditable)  # 읽기 전용
            
            self.joint_table.setItem(i, 0, original_item)
            
            # 설정할 조인트명 (편집 가능)
            target_item = QtWidgets.QTableWidgetItem(joint_name)
            target_item.setFlags(target_item.flags() | QtCore.Qt.ItemIsEditable)
            self.joint_table.setItem(i, 1, target_item) 