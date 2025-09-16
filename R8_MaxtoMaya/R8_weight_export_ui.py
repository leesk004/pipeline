"""
스킨 웨이트 익스포트 UI 클래스
"""

import os
import time
import maya.cmds as cmds

# PySide 임포트 (Maya 버전에 따라)
try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui


def get_maya_main_window():
    """Maya 메인 윈도우를 반환합니다."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class SkinWeightExportUI(QtWidgets.QWidget):
    """스킨 웨이트 익스포트 UI 클래스"""
    
    def __init__(self, core_instance, parent=None):
        super(SkinWeightExportUI, self).__init__(parent)
        
        # 핵심 기능 클래스 참조
        self.core = core_instance
        
        # UI 구성
        self.create_widgets()
        self.create_layouts()
        self.create_connections()
    
    def create_widgets(self):
        """UI 위젯을 생성합니다."""
        # 메시 정보 그룹 - 테이블 위젯으로 변경
        self.export_mesh_group = QtWidgets.QGroupBox("Mesh List")
        self.export_mesh_table = QtWidgets.QTableWidget()
        self.export_mesh_table.setColumnCount(3)
        self.export_mesh_table.setHorizontalHeaderLabels(["메시 이름", "버텍스 수", "스킨 클러스터 이름"])
        self.export_mesh_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.export_mesh_table.setAlternatingRowColors(True)
        # 컬럼 너비 조정
        header = self.export_mesh_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)  # 메시명 컬럼 늘어남
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)  # 버텍스 수 컬럼 내용에 맞춤
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)  # 스킨 클러스터 컬럼 내용에 맞춤
        self.export_mesh_table.setMinimumHeight(300)  # 높이 증가
        self.export_refresh_btn = QtWidgets.QPushButton("Load Mesh")
        self.export_select_all_btn = QtWidgets.QPushButton("Select All")
        self.export_select_none_btn = QtWidgets.QPushButton("Select None")
        
        # 파일 형식 그룹
        self.export_format_group = QtWidgets.QGroupBox("파일 형식")
        self.export_json_radio = QtWidgets.QRadioButton("JSON")
        self.export_xml_radio = QtWidgets.QRadioButton("XML")
        self.export_json_radio.setChecked(True)  # 기본값은 JSON
        
        # 폴더명 지정 그룹
        self.export_folder_group = QtWidgets.QGroupBox("저장 폴더 이름")
        self.export_folder_label = QtWidgets.QLabel("폴더 이름:")
        self.export_folder_field = QtWidgets.QLineEdit()
        self.export_folder_field.setPlaceholderText("저장할 폴더명을 입력하세요")
        
        # 익스포트 실행 버튼
        self.export_btn = QtWidgets.QPushButton("Weight Export")
        self.export_btn.setFixedHeight(40)
        
        # 익스포트 도움말 버튼
        self.export_help_btn = QtWidgets.QPushButton("Help")
        self.export_help_btn.setFixedHeight(30)
    
    def create_layouts(self):
        """레이아웃을 생성합니다."""
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # 메시 정보 레이아웃
        export_mesh_layout = QtWidgets.QVBoxLayout(self.export_mesh_group)
        export_mesh_layout.addWidget(self.export_mesh_table)
        export_mesh_btn_layout = QtWidgets.QHBoxLayout()
        export_mesh_btn_layout.addWidget(self.export_refresh_btn)
        export_mesh_btn_layout.addWidget(self.export_select_all_btn)
        export_mesh_btn_layout.addWidget(self.export_select_none_btn)
        export_mesh_layout.addLayout(export_mesh_btn_layout)
        
        # 파일 형식 레이아웃
        export_format_layout = QtWidgets.QHBoxLayout(self.export_format_group)
        export_format_layout.addWidget(self.export_json_radio)
        export_format_layout.addWidget(self.export_xml_radio)
        export_format_layout.addStretch()
        
        # 폴더명 지정 레이아웃
        export_folder_layout = QtWidgets.QHBoxLayout(self.export_folder_group)
        export_folder_layout.addWidget(self.export_folder_label)
        export_folder_layout.addWidget(self.export_folder_field)
        export_folder_layout.addStretch()
        
        # 메인 레이아웃에 추가
        main_layout.addWidget(self.export_mesh_group)
        main_layout.addWidget(self.export_format_group)
        main_layout.addWidget(self.export_folder_group)
        main_layout.addStretch()  # 빈 공간 추가
        main_layout.addWidget(self.export_btn)
        
        # 하단 도움말 버튼 레이아웃
        export_help_layout = QtWidgets.QHBoxLayout()
        export_help_layout.addWidget(self.export_help_btn)
        export_help_layout.addStretch()  # 오른쪽 공간 채우기
        main_layout.addLayout(export_help_layout)
    
    def create_connections(self):
        """시그널과 슬롯을 연결합니다."""
        self.export_refresh_btn.clicked.connect(self.refresh_export_mesh)
        self.export_select_all_btn.clicked.connect(self.select_all_export_meshes)
        self.export_select_none_btn.clicked.connect(self.select_none_export_meshes)
        self.export_btn.clicked.connect(self.export_weights)
        self.export_help_btn.clicked.connect(self.show_export_help)
    
    def refresh_export_mesh(self):
        """익스포트용 메시 정보를 새로고침합니다."""
        try:
            # 선택된 모든 transform 노드 가져오기
            selection = cmds.ls(selection=True, type="transform")
            valid_meshes = []
            
            # 각 선택된 객체가 메시인지 확인
            for obj in selection:
                shapes = cmds.listRelatives(obj, shapes=True, type="mesh")
                if shapes:
                    valid_meshes.append(obj)
            
            # 테이블 설정
            self.export_mesh_table.setRowCount(len(valid_meshes))
            
            if not valid_meshes:
                # 선택된 메시가 없는 경우
                return
            
            # 테이블에 메시 정보 추가
            for i, mesh_transform in enumerate(valid_meshes):
                shapes = cmds.listRelatives(mesh_transform, shapes=True, type="mesh")
                if shapes:
                    mesh_shape = shapes[0]
                    
                    # 메시명
                    mesh_item = QtWidgets.QTableWidgetItem(mesh_transform)
                    mesh_item.setCheckState(QtCore.Qt.Checked)  # 기본적으로 체크됨
                    self.export_mesh_table.setItem(i, 0, mesh_item)
                    
                    # 버텍스 수
                    vertex_count = cmds.polyEvaluate(mesh_shape, vertex=True)
                    vertex_item = QtWidgets.QTableWidgetItem(f"{vertex_count:,}")
                    self.export_mesh_table.setItem(i, 1, vertex_item)
                    
                    # 스킨 클러스터
                    skin_cluster = self.core.get_skin_cluster(mesh_transform)
                    skin_item = QtWidgets.QTableWidgetItem(skin_cluster if skin_cluster else "없음")
                    if not skin_cluster:
                        mesh_item.setCheckState(QtCore.Qt.Unchecked)  # 스킨 클러스터가 없으면 체크 해제
                    
                    self.export_mesh_table.setItem(i, 2, skin_item)
                    
                    # 체크박스 활성화
                    mesh_item.setFlags(mesh_item.flags() | QtCore.Qt.ItemIsUserCheckable)
                    
        except Exception as e:
            self.show_error("메시 새로고침 오류", str(e))

    def select_all_export_meshes(self):
        """모든 익스포트 메시를 선택합니다."""
        for i in range(self.export_mesh_table.rowCount()):
            item = self.export_mesh_table.item(i, 0)
            if item:
                item.setCheckState(QtCore.Qt.Checked)

    def select_none_export_meshes(self):
        """모든 익스포트 메시 선택을 해제합니다."""
        for i in range(self.export_mesh_table.rowCount()):
            item = self.export_mesh_table.item(i, 0)
            if item:
                item.setCheckState(QtCore.Qt.Unchecked)

    def export_weights(self):
        """스킨 웨이트를 내보냅니다."""
        # 선택된 메시들 가져오기
        selected_meshes = self.get_selected_export_meshes()
        
        if not selected_meshes:
            self.show_error("오류", "내보낼 메시를 테이블에서 선택해주세요.")
            return
        
        # 폴더명 확인
        folder_name = self.export_folder_field.text().strip()
        if not folder_name:
            self.show_error("오류", "저장할 폴더명을 입력해주세요.")
            return
        
        # 진행 상황 콜백 설정
        def update_progress(value, message=""):
            # 부모 UI에 진행 상황 전달
            if hasattr(self.parent(), 'update_progress'):
                self.parent().update_progress(value, message)
        
        try:
            # 내보내기 버튼 비활성화
            self.export_btn.setEnabled(False)
            
            # 파일 형식에 따른 확장자 설정
            if self.export_xml_radio.isChecked():
                extension = ".xml"
            else:
                extension = ".json"
            
            # WeightIO 폴더 경로와 지정된 폴더명 결합
            weightio_folder = self.core.get_weightio_folder()
            export_folder = os.path.join(weightio_folder, folder_name)
            
            # 폴더가 없으면 생성
            if not os.path.exists(export_folder):
                os.makedirs(export_folder)
                print(f"폴더가 생성되었습니다: {export_folder}")
            
            success_count = 0
            failed_meshes = []
            
            # 각 선택된 메시에 대해 순차적으로 내보내기 실행 (테이블 순서대로)
            for i, mesh_name in enumerate(selected_meshes):
                try:
                    # 진행 상황 표시
                    progress = int((i / len(selected_meshes)) * 100)
                    update_progress(progress, f"내보내기 중... ({i+1}/{len(selected_meshes)}) - {mesh_name}")
                    
                    # 메시 이름 기반으로 파일명 자동 생성 (접미사 "_skinWeights" 추가)
                    filename = f"{mesh_name}_skinWeights{extension}"
                    export_path = os.path.join(export_folder, filename)
                    
                    # 임시로 메시 선택 (내보내기 함수에서 필요)
                    cmds.select(mesh_name, replace=True)
                    
                    # 파일 형식에 따른 내보내기 실행
                    if self.export_xml_radio.isChecked():
                        result_path = self.core.export_weights_to_xml(
                            mesh_name, export_path, None  # 개별 진행표시 비활성화
                        )
                    else:
                        result_path = self.core.export_weights_to_json(
                            mesh_name, export_path, None  # 개별 진행표시 비활성화
                        )
                    
                    if result_path:
                        success_count += 1
                        print(f"저장됨: {result_path}")
                    else:
                        failed_meshes.append(mesh_name)
                        
                except Exception as e:
                    failed_meshes.append(f"{mesh_name} (오류: {str(e)})")
            
            # 최종 결과 표시
            update_progress(100, "내보내기 완료!")
            
            # 결과에 따른 메시지 표시
            if success_count == len(selected_meshes):
                self.show_info("내보내기 성공", 
                             f"모든 메시의 스킨 웨이트가 성공적으로 저장되었습니다.\n"
                             f"성공: {success_count}개\n"
                             f"파일 형식: {extension.upper()}\n"
                             f"저장 폴더: {export_folder}")
            elif success_count > 0:
                error_msg = (f"일부 메시만 저장되었습니다.\n"
                           f"성공: {success_count}개\n"
                           f"실패: {len(failed_meshes)}개\n"
                           f"저장 폴더: {export_folder}")
                if failed_meshes:
                    error_msg += f"\n\n실패한 메시:\n" + "\n".join(failed_meshes[:5])  # 최대 5개만 표시
                    if len(failed_meshes) > 5:
                        error_msg += f"\n... 및 {len(failed_meshes) - 5}개 더"
                self.show_info("부분 성공", error_msg)
            else:
                error_msg = f"모든 메시 내보내기가 실패했습니다."
                if failed_meshes:
                    error_msg += f"\n\n실패한 메시:\n" + "\n".join(failed_meshes[:5])
                    if len(failed_meshes) > 5:
                        error_msg += f"\n... 및 {len(failed_meshes) - 5}개 더"
                self.show_error("내보내기 실패", error_msg)
            
        except Exception as e:
            update_progress(0, f"오류: {str(e)}")
            self.show_error("내보내기 오류", str(e))
        finally:
            # 내보내기 버튼 다시 활성화
            self.export_btn.setEnabled(True)

    def get_selected_export_meshes(self):
        """익스포트 테이블에서 체크된 메시들을 반환합니다."""
        selected_meshes = []
        
        for i in range(self.export_mesh_table.rowCount()):
            mesh_item = self.export_mesh_table.item(i, 0)
            if mesh_item and mesh_item.checkState() == QtCore.Qt.Checked:
                mesh_name = mesh_item.text()
                selected_meshes.append(mesh_name)
        
        return selected_meshes

    def show_export_help(self):
        """Export 탭 사용법을 보여줍니다."""
        help_text = """
<h3>📤 Export 탭 사용법</h3>

<h4>1. 메시 준비</h4>
• 스킨 웨이트를 내보낼 메시를 Maya 씬에서 선택하세요<br>
• 메시에 스킨 클러스터가 적용되어 있어야 합니다

<h4>2. 메시 불러오기</h4>
• <b>Load Mesh</b> 버튼을 클릭하여 선택된 메시 정보를 테이블에 로드합니다.<br>
• 테이블에서 내보낼 메시를 체크박스로 선택/해제할 수 있습니다.<br>
• <b>Select All</b> / <b>Select None</b> 버튼으로 일괄 선택 가능합니다.<br>

<h4>3. 파일 형식 선택</h4>
• <b>JSON</b>: JSON 형식 (빠른 처리 속도, Python 친화적)<br>
• <b>XML</b>: 표준 XML 형식 (Maya 호환성 좋음)<br>

<h4>4. 폴더명 지정</h4>
• 저장할 폴더 이름을 입력하세요<br>
• WeightIO 폴더 하위에 생성됩니다<br>

<h4>5. 내보내기 실행</h4>
• <b>Weight Export</b> 버튼을 클릭하여 내보내기를 시작합니다<br>
• 파일명은 자동으로 "{메시명}_skinWeights.{확장자}" 형식으로 생성됩니다
"""
        QtWidgets.QMessageBox.information(self, "Export 탭 사용법", help_text)

    def show_error(self, title, message):
        """에러 메시지를 표시합니다."""
        QtWidgets.QMessageBox.critical(self, title, message)
    
    def show_info(self, title, message):
        """정보 메시지를 표시합니다."""
        QtWidgets.QMessageBox.information(self, title, message) 