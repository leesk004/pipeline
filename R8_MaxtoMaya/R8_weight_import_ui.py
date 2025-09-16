"""
스킨 웨이트 임포트 UI 클래스
"""

import os
import time
import json
import xml.etree.ElementTree as ET
import maya.cmds as cmds
import maya.mel as mel

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


class SkinWeightImportUI(QtWidgets.QWidget):
    """스킨 웨이트 임포트 UI 클래스"""
    
    def __init__(self, core_instance, parent=None):
        super(SkinWeightImportUI, self).__init__(parent)
        
        # 핵심 기능 클래스 참조
        self.core = core_instance
        
        # UI 구성
        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        
        # 윈도우 열릴 때 Weight Folder List 자동 새로고침
        self.refresh_import_files()
    
    def create_widgets(self):
        """UI 위젯을 생성합니다."""
        # WeightIO 파일 리스트
        self.import_files_group = QtWidgets.QGroupBox("Weight Folder List")
        self.import_files_table = QtWidgets.QTableWidget()
        self.import_files_table.setColumnCount(3)
        self.import_files_table.setHorizontalHeaderLabels(["폴더명", "파일 수", "수정 날짜"])
        self.import_files_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.import_files_table.setAlternatingRowColors(True)
        # 컬럼 너비 조정
        header = self.import_files_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)  # 폴더명 컬럼 늘어남
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)  # 파일 수 컬럼 내용에 맞춤
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)  # 수정 날짜 컬럼 내용에 맞춤
        self.import_files_table.setMinimumHeight(200)
        self.import_refresh_files_btn = QtWidgets.QPushButton("Refresh List")
        self.import_open_folder_btn = QtWidgets.QPushButton("Open Folder")
        self.import_weight_info_btn = QtWidgets.QPushButton("Weight Info")
        self.import_weight_info_btn.setEnabled(False)  # 초기에는 비활성화
        
        # 조인트 리매핑 그룹
        self.joint_remap_group = QtWidgets.QGroupBox("Remapping (선택사항)")
        self.joint_remap_table = QtWidgets.QTableWidget()
        self.joint_remap_table.setColumnCount(2)
        self.joint_remap_table.setHorizontalHeaderLabels(["Original Joint", "Target Joint"])
        self.joint_remap_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.joint_remap_table.setAlternatingRowColors(True)
        # 컬럼 너비 조정
        remap_header = self.joint_remap_table.horizontalHeader()
        remap_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)  # 원본 조인트 컬럼 늘어남
        remap_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)  # 대상 조인트 컬럼 늘어남
        self.joint_remap_table.setMinimumHeight(150)
        self.joint_remap_table.setMaximumHeight(200)
        
        # 조인트 리매핑 버튼들
        self.remapping_btn = QtWidgets.QPushButton("ReMapping")
        self.add_remap_btn = QtWidgets.QPushButton("Add Mapping")
        self.remove_remap_btn = QtWidgets.QPushButton("Remove Mapping")
        self.clear_remap_btn = QtWidgets.QPushButton("Clear All")
        
        # 조인트 리매핑 활성화 체크박스
        self.remap_enable_check = QtWidgets.QCheckBox("조인트 리매핑 활성화")
        self.remap_enable_check.setChecked(False)
        
        # 조인트 매핑 내보내기/불러오기 버튼들
        self.export_remap_xml_btn = QtWidgets.QPushButton("Export XML")
        self.export_remap_json_btn = QtWidgets.QPushButton("Export JSON")
        self.import_remap_xml_btn = QtWidgets.QPushButton("Import XML")
        self.import_remap_json_btn = QtWidgets.QPushButton("Import JSON")
        
        # 임포트 실행 버튼
        self.import_btn = QtWidgets.QPushButton("Weight Import")
        self.import_btn.setMinimumHeight(40)
        
        # 임포트 도움말 버튼
        self.import_help_btn = QtWidgets.QPushButton("Help")
        self.import_help_btn.setFixedHeight(30)
    
    def create_layouts(self):
        """레이아웃을 생성합니다."""
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # WeightIO 파일 리스트
        import_files_layout = QtWidgets.QVBoxLayout(self.import_files_group)
        import_files_layout.addWidget(self.import_files_table)
        im_folder_layout = QtWidgets.QHBoxLayout()
        im_folder_layout.addWidget(self.import_refresh_files_btn)
        im_folder_layout.addWidget(self.import_open_folder_btn)
        im_folder_layout.addWidget(self.import_weight_info_btn)
        import_files_layout.addLayout(im_folder_layout)
        import_files_layout.addStretch()
        
        # 조인트 리매핑 레이아웃
        joint_remap_layout = QtWidgets.QVBoxLayout(self.joint_remap_group)
        joint_remap_layout.addWidget(self.remap_enable_check)
        joint_remap_layout.addWidget(self.joint_remap_table)
        
        # 조인트 리매핑 버튼 레이아웃
        remap_btn_layout = QtWidgets.QHBoxLayout()
        remap_btn_layout.addWidget(self.remapping_btn)
        remap_btn_layout.addWidget(self.add_remap_btn)
        remap_btn_layout.addWidget(self.remove_remap_btn)
        remap_btn_layout.addWidget(self.clear_remap_btn)
        remap_btn_layout.addStretch()
        joint_remap_layout.addLayout(remap_btn_layout)
        
        # 조인트 매핑 파일 입출력 버튼 레이아웃
        remap_io_layout = QtWidgets.QHBoxLayout()
        remap_io_layout.addWidget(self.export_remap_xml_btn)
        remap_io_layout.addWidget(self.export_remap_json_btn)
        remap_io_layout.addWidget(self.import_remap_xml_btn)
        remap_io_layout.addWidget(self.import_remap_json_btn)
        joint_remap_layout.addLayout(remap_io_layout)
        
        # 메인 레이아웃에 추가
        main_layout.addWidget(self.import_files_group)
        main_layout.addWidget(self.joint_remap_group)
        main_layout.addStretch()
        main_layout.addWidget(self.import_btn)
        
        # 하단 도움말 버튼 레이아웃
        import_help_layout = QtWidgets.QHBoxLayout()
        import_help_layout.addWidget(self.import_help_btn)
        import_help_layout.addStretch()  # 오른쪽 공간 채우기
        main_layout.addLayout(import_help_layout)
    
    def create_connections(self):
        """시그널과 슬롯을 연결합니다."""
        # 임포트 탭
        self.import_refresh_files_btn.clicked.connect(self.refresh_import_files)
        self.import_open_folder_btn.clicked.connect(self.open_import_folder)
        self.import_weight_info_btn.clicked.connect(self.show_weight_info)
        self.import_btn.clicked.connect(self.import_weights)
        self.import_help_btn.clicked.connect(self.show_import_help)
        
        # 조인트 리매핑 관련
        self.remapping_btn.clicked.connect(self.apply_remapping)
        self.add_remap_btn.clicked.connect(self.add_joint_remap)
        self.remove_remap_btn.clicked.connect(self.remove_joint_remap)
        self.clear_remap_btn.clicked.connect(self.clear_joint_remap)
        self.remap_enable_check.toggled.connect(self.toggle_joint_remap)
        
        # 조인트 매핑 파일 입출력 관련
        self.export_remap_xml_btn.clicked.connect(self.export_joint_remap_xml)
        self.export_remap_json_btn.clicked.connect(self.export_joint_remap_json)
        self.import_remap_xml_btn.clicked.connect(self.import_joint_remap_xml)
        self.import_remap_json_btn.clicked.connect(self.import_joint_remap_json)
        
        # 조인트 리매핑 초기 상태 설정
        self.toggle_joint_remap(False)
        
        # 폴더 테이블 선택 변경 시 웨이트 정보 버튼 활성화/비활성화
        self.import_files_table.selectionModel().selectionChanged.connect(self.on_import_folder_selection_changed)
    
    def refresh_import_files(self):
        """WeightIO 폴더의 폴더 목록을 새로고침합니다."""
        self.import_files_table.setRowCount(0)
        self.import_files_table.setHorizontalHeaderLabels(["폴더명", "파일 수", "수정 날짜"])
        
        folders = self.core.get_weightio_folders()
        self.import_files_table.setRowCount(len(folders))
        
        for i, folder_data in enumerate(folders):
            # 폴더명
            folder_item = QtWidgets.QTableWidgetItem(folder_data['name'])
            folder_item.setData(QtCore.Qt.UserRole, folder_data)  # 폴더 데이터 저장
            self.import_files_table.setItem(i, 0, folder_item)
            
            # 파일 수
            file_count_item = QtWidgets.QTableWidgetItem(f"{folder_data['file_count']}개")
            self.import_files_table.setItem(i, 1, file_count_item)
            
            # 수정 날짜
            date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(folder_data['modified']))
            date_item = QtWidgets.QTableWidgetItem(date_str)
            self.import_files_table.setItem(i, 2, date_item)
        
        self.import_open_folder_btn.setEnabled(bool(folders))

    def open_import_folder(self):
        """WeightIO 폴더를 엽니다."""
        weightio_folder = self.core.get_weightio_folder()
        os.startfile(weightio_folder)
    
    def add_joint_remap(self):
        """조인트 리매핑을 추가합니다."""
        row_count = self.joint_remap_table.rowCount()
        self.joint_remap_table.insertRow(row_count)
        
        # 편집 가능한 아이템 생성
        source_item = QtWidgets.QTableWidgetItem("")
        source_item.setFlags(source_item.flags() | QtCore.Qt.ItemIsEditable)
        target_item = QtWidgets.QTableWidgetItem("")
        target_item.setFlags(target_item.flags() | QtCore.Qt.ItemIsEditable)
        
        self.joint_remap_table.setItem(row_count, 0, source_item)
        self.joint_remap_table.setItem(row_count, 1, target_item)
        
        # 새로 추가된 행을 선택하고 편집 모드로 전환
        self.joint_remap_table.selectRow(row_count)
        self.joint_remap_table.editItem(source_item)
    
    def remove_joint_remap(self):
        """선택된 조인트 리매핑을 삭제합니다."""
        current_row = self.joint_remap_table.currentRow()
        if current_row >= 0:
            self.joint_remap_table.removeRow(current_row)
    
    def clear_joint_remap(self):
        """모든 조인트 리매핑을 삭제합니다."""
        self.joint_remap_table.setRowCount(0)
    
    def toggle_joint_remap(self, enabled):
        """조인트 리매핑 활성화/비활성화를 토글합니다."""
        self.joint_remap_table.setEnabled(enabled)
        self.add_remap_btn.setEnabled(enabled)
        self.remove_remap_btn.setEnabled(enabled)
        self.clear_remap_btn.setEnabled(enabled)
        self.export_remap_xml_btn.setEnabled(enabled)
        self.export_remap_json_btn.setEnabled(enabled)
        self.import_remap_xml_btn.setEnabled(enabled)
        self.import_remap_json_btn.setEnabled(enabled)
    
    def get_joint_remap_dict(self):
        """조인트 리매핑 딕셔너리를 반환합니다."""
        if not self.remap_enable_check.isChecked():
            return {}
        
        remap_dict = {}
        for i in range(self.joint_remap_table.rowCount()):
            source_item = self.joint_remap_table.item(i, 0)
            target_item = self.joint_remap_table.item(i, 1)
            
            if source_item and target_item:
                source_joint = source_item.text().strip()
                target_joint = target_item.text().strip()
                
                if source_joint and target_joint:
                    remap_dict[source_joint] = target_joint
        
        return remap_dict
    
    def import_weights(self):
        """선택된 폴더의 모든 _skinWeights 파일을 불러옵니다 (파일명 기반 자동 메시 매칭)."""
        selected_rows = self.import_files_table.selectionModel().selectedRows()
        if not selected_rows:
            self.show_error("오류", "불러올 폴더를 선택해주세요.")
            return
        
        # 선택된 첫 번째 폴더 가져오기
        row = selected_rows[0].row()
        folder_item = self.import_files_table.item(row, 0)
        if not folder_item:
            self.show_error("오류", "선택된 폴더를 찾을 수 없습니다.")
            return
        
        folder_data = folder_item.data(QtCore.Qt.UserRole)
        if not folder_data or not os.path.exists(folder_data['path']):
            self.show_error("오류", "선택된 폴더를 찾을 수 없습니다.")
            return
        
        # _skinWeights 파일이 있는지 확인
        if folder_data['file_count'] == 0:
            self.show_error("오류", f"'{folder_data['name']}' 폴더에 _skinWeights 파일이 없습니다.")
            return
        
        # 시작 시간 기록
        import time
        start_time = time.time()
        
        # 진행 상황 콜백 설정
        def update_progress(value, message=""):
            # 부모 UI에 진행 상황 전달
            if hasattr(self.parent(), 'update_progress'):
                self.parent().update_progress(value, message)
        
        try:
            # 불러오기 버튼 비활성화
            self.import_btn.setEnabled(False)
            
            # 조인트 리매핑 딕셔너리 가져오기
            joint_remap_dict = self.get_joint_remap_dict()
            
            # 성능 옵션 기본값 설정 (UI에서 제거된 항목들)
            use_high_performance = True  # 고성능 모드 활성화
            use_batch_processing = False  # 배치 처리 비활성화
            batch_size = 5000  # 배치 크기
            
            folder_path = folder_data['path']
            skinweight_files = folder_data['files']
            
            success_count = 0
            failed_files = []
            
            # 조인트 리매핑 정보 표시
            remap_info = ""
            if joint_remap_dict:
                remap_info = f" (조인트 리매핑: {len(joint_remap_dict)}개)"
            
            update_progress(0, f"폴더 '{folder_data['name']}'에서 {len(skinweight_files)}개 파일 처리 시작...{remap_info}")
            
            # 각 _skinWeights 파일을 순차적으로 처리
            for i, filename in enumerate(skinweight_files):
                try:
                    file_path = os.path.join(folder_path, filename)
                    file_ext = os.path.splitext(filename)[1].lower()
                    
                    # 파일명에서 메시명 추출 (메시명_skinWeights.확장자 형식)
                    base_name = os.path.splitext(filename)[0]
                    if base_name.endswith('_skinWeights'):
                        mesh_name = base_name[:-12]  # '_skinWeights' 제거
                    else:
                        mesh_name = base_name
                    
                    # 파일 시작 진행률 계산 (각 파일에 대해 동일한 비중 할당)
                    file_start_progress = (i / len(skinweight_files)) * 100
                    file_end_progress = ((i + 1) / len(skinweight_files)) * 100
                    
                    # 파일 처리 시작 진행 상황 업데이트
                    update_progress(int(file_start_progress), f"처리 중... ({i+1}/{len(skinweight_files)}) - {filename}")
                    
                    # 메시가 씬에 존재하는지 확인
                    if not cmds.objExists(mesh_name):
                        failed_files.append(f"{filename} (메시 '{mesh_name}' 없음)")
                        # 실패한 파일도 진행률 업데이트
                        update_progress(int(file_end_progress), f"건너뜀... ({i+1}/{len(skinweight_files)}) - {filename} (메시 없음)")
                        continue
                    
                    # 파일 불러오기 중간 진행률 업데이트
                    mid_progress = file_start_progress + (file_end_progress - file_start_progress) * 0.5
                    update_progress(int(mid_progress), f"적용 중... ({i+1}/{len(skinweight_files)}) - {mesh_name}")
                    
                    # 파일 형식에 따른 불러오기 실행 (조인트 리매핑 포함)
                    result = False
                    if file_ext == '.xml':
                        if use_high_performance and use_batch_processing:
                            result = self.core.batch_import_weights_from_xml(
                                file_path, mesh_name, None, batch_size, joint_remap_dict
                            )
                        elif use_high_performance:
                            result = self.core.import_weights_from_xml(
                                file_path, mesh_name, None, joint_remap_dict
                            )
                        else:
                            result = self.core.import_weights_from_xml(
                                file_path, mesh_name, None, joint_remap_dict
                            )
                    elif file_ext == '.json':
                        if use_high_performance:
                            result = self.core.import_weights_from_json(
                                file_path, mesh_name, None, joint_remap_dict
                            )
                        else:
                            result = self.core.import_weights_from_json(
                                file_path, mesh_name, None, joint_remap_dict
                            )
                    
                    # 파일 처리 완료 진행률 업데이트
                    if result:
                        success_count += 1
                        update_progress(int(file_end_progress), f"완료... ({i+1}/{len(skinweight_files)}) - {mesh_name} ✓")
                        print(f"적용됨: {filename} -> {mesh_name}")
                    else:
                        failed_files.append(f"{filename} (적용 실패)")
                        update_progress(int(file_end_progress), f"실패... ({i+1}/{len(skinweight_files)}) - {filename} ✗")
                        
                except Exception as e:
                    failed_files.append(f"{filename} (오류: {str(e)})")
                    # 오류 발생 시에도 진행률 업데이트
                    file_end_progress = ((i + 1) / len(skinweight_files)) * 100
                    update_progress(int(file_end_progress), f"오류... ({i+1}/{len(skinweight_files)}) - {filename} ✗")
            
            # 소요 시간 계산
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # 시간 포맷팅 (초 단위)
            if elapsed_time < 60:
                time_str = f"{elapsed_time:.1f}초"
            else:
                minutes = int(elapsed_time // 60)
                seconds = elapsed_time % 60
                time_str = f"{minutes}분 {seconds:.1f}초"
            
            # 최종 결과 표시
            update_progress(100, f"폴더 불러오기 완료! (소요 시간: {time_str})")
            
            # Maya 최적화 실행 (성공한 파일이 있을 때만)
            if success_count > 0:
                update_progress(100, f"Maya 최적화 실행 중... (소요 시간: {time_str})")
                self.maya_optimize()
                update_progress(100, f"모든 작업 완료! (소요 시간: {time_str})")
            
            # 결과에 따른 메시지 표시
            if success_count == len(skinweight_files):
                performance_info = " (고성능 모드)"  # 항상 고성능 모드
                if joint_remap_dict:
                    performance_info += f" (조인트 리매핑: {len(joint_remap_dict)}개)"
                
                self.show_info("불러오기 성공", 
                             f"폴더 '{folder_data['name']}'의 모든 스킨 웨이트가 성공적으로 적용되었습니다.\n"
                             f"성공: {success_count}개{performance_info}\n"
                             f"소요 시간: {time_str}\n\n"
                             f"파일명에서 자동으로 메시명을 추출하여 적용했습니다.\n"
                             f"Maya 최적화가 완료되었습니다.")
            elif success_count > 0:
                error_msg = (f"폴더 '{folder_data['name']}'의 일부 파일만 적용되었습니다.\n"
                           f"성공: {success_count}개\n"
                           f"실패: {len(failed_files)}개\n"
                           f"소요 시간: {time_str}\n"
                           f"Maya 최적화가 완료되었습니다.")
                if failed_files:
                    error_msg += f"\n\n실패한 파일:\n" + "\n".join(failed_files[:5])
                    if len(failed_files) > 5:
                        error_msg += f"\n... 및 {len(failed_files) - 5}개 더"
                self.show_info("부분 성공", error_msg)
            else:
                error_msg = (f"폴더 '{folder_data['name']}'의 모든 파일 적용이 실패했습니다.\n"
                           f"소요 시간: {time_str}")
                if failed_files:
                    error_msg += f"\n\n실패한 파일:\n" + "\n".join(failed_files[:5])
                    if len(failed_files) > 5:
                        error_msg += f"\n... 및 {len(failed_files) - 5}개 더"
                self.show_error("불러오기 실패", error_msg)
            
        except Exception as e:
            # 오류 발생 시에도 소요 시간 계산
            end_time = time.time()
            elapsed_time = end_time - start_time
            if elapsed_time < 60:
                time_str = f"{elapsed_time:.1f}초"
            else:
                minutes = int(elapsed_time // 60)
                seconds = elapsed_time % 60
                time_str = f"{minutes}분 {seconds:.1f}초"
            
            update_progress(0, f"오류 발생 (소요 시간: {time_str}): {str(e)}")
            self.show_error("불러오기 오류", f"{str(e)}\n\n소요 시간: {time_str}")
        finally:
            # 불러오기 버튼 다시 활성화
            self.import_btn.setEnabled(True)
    
    def maya_optimize(self):
        """Maya 옵티마이즈 실행"""
        try:
            if "MAYA_TESTING_CLEANUP" not in os.environ:
                os.environ["MAYA_TESTING_CLEANUP"] = "enable"
                mel.eval("cleanUpScene 1;")
                del os.environ["MAYA_TESTING_CLEANUP"]
            else: 
                mel.eval("cleanUpScene 1;")       
            print("Maya Optimize Scene Size 완료되었습니다.")
            
        except Exception as e:
            print(f"Maya Optimize Scene Size 실행 중 오류: {str(e)}")

    def on_import_folder_selection_changed(self):
        """폴더 테이블 선택 변경 시 웨이트 정보 버튼 활성화/비활성화"""
        selected_rows = self.import_files_table.selectionModel().selectedRows()
        if selected_rows:
            self.import_weight_info_btn.setEnabled(True)
        else:
            self.import_weight_info_btn.setEnabled(False)

    def show_weight_info(self):
        """선택된 폴더의 웨이트 정보를 팝업으로 표시합니다."""
        selected_rows = self.import_files_table.selectionModel().selectedRows()
        if not selected_rows:
            self.show_error("오류", "먼저 정보를 확인할 폴더를 선택해주세요.")
            return
        
        # 선택된 첫 번째 폴더 가져오기
        row = selected_rows[0].row()
        folder_item = self.import_files_table.item(row, 0)
        if not folder_item:
            return
        
        folder_data = folder_item.data(QtCore.Qt.UserRole)
        if not folder_data:
            self.show_error("오류", "폴더 데이터를 가져올 수 없습니다.")
            return
        
        try:
            # WeightInfoDialog 임포트 및 팝업 표시 (모달리스로 변경)
            from R8_MaxtoMaya.R8_weight_info_dialog import WeightInfoDialog
            
            # 부모 UI 참조를 전달하되, Qt 부모는 None으로 설정
            dialog = WeightInfoDialog(folder_data, self)
            dialog.show()  # exec_() 대신 show() 사용하여 모달리스로 실행
            
            # 다이얼로그 참조를 유지하여 가비지 컬렉션 방지
            self.weight_info_dialog = dialog
            
            # 다이얼로그가 닫힐 때 조인트 매핑 정보를 가져와서 메인 UI에 반영하는 기능은 
            # WeightInfoDialog의 apply_mapping 메서드에서 처리됩니다.
                                 
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"WeightInfoDialog 생성 오류 상세: {error_details}")
            self.show_error("웨이트 정보 오류", f"웨이트 정보를 표시하는 중 오류가 발생했습니다:\n{str(e)}\n\n상세 정보는 Script Editor를 확인하세요.")

    def export_joint_remap_xml(self):
        """조인트 리매핑을 XML 파일로 내보냅니다."""
        try:
            # 현재 리매핑 딕셔너리 가져오기
            remap_dict = {}
            for i in range(self.joint_remap_table.rowCount()):
                source_item = self.joint_remap_table.item(i, 0)
                target_item = self.joint_remap_table.item(i, 1)
                
                if source_item and target_item:
                    source_joint = source_item.text().strip()
                    target_joint = target_item.text().strip()
                    
                    if source_joint and target_joint:
                        remap_dict[source_joint] = target_joint
            
            if not remap_dict:
                self.show_error("오류", "저장할 조인트 매핑이 없습니다.")
                return
            
            # 파일 저장 다이얼로그
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "조인트 매핑 XML 저장", 
                os.path.join(os.path.expanduser("~"), "Documents", "joint_mapping.xml"), 
                "XML Files (*.xml)"
            )
            
            if not file_path:
                return
            
            # XML 생성
            root = ET.Element("JointMapping")
            
            for source, target in remap_dict.items():
                mapping_elem = ET.SubElement(root, "Mapping")
                mapping_elem.set("source", source)
                mapping_elem.set("target", target)
            
            # XML 파일 저장
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            
            self.show_info("저장 완료", f"조인트 매핑이 XML 파일로 저장되었습니다:\n{file_path}\n매핑 수: {len(remap_dict)}개")
            
        except Exception as e:
            self.show_error("XML 저장 오류", f"조인트 매핑 XML 저장 중 오류가 발생했습니다:\n{str(e)}")
    
    def export_joint_remap_json(self):
        """조인트 리매핑을 JSON 파일로 내보냅니다."""
        try:
            # 현재 리매핑 딕셔너리 가져오기
            remap_dict = {}
            for i in range(self.joint_remap_table.rowCount()):
                source_item = self.joint_remap_table.item(i, 0)
                target_item = self.joint_remap_table.item(i, 1)
                
                if source_item and target_item:
                    source_joint = source_item.text().strip()
                    target_joint = target_item.text().strip()
                    
                    if source_joint and target_joint:
                        remap_dict[source_joint] = target_joint
            
            if not remap_dict:
                self.show_error("오류", "저장할 조인트 매핑이 없습니다.")
                return
            
            # 파일 저장 다이얼로그
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "조인트 매핑 JSON 저장", 
                os.path.join(os.path.expanduser("~"), "Documents", "joint_mapping.json"), 
                "JSON Files (*.json)"
            )
            
            if not file_path:
                return
            
            # JSON 데이터 구성
            json_data = {
                "joint_mapping": remap_dict,
                "created_time": time.strftime('%Y-%m-%d %H:%M:%S'),
                "description": "Maya Skin Weight Tool - Joint Mapping"
            }
            
            # JSON 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.show_info("저장 완료", f"조인트 매핑이 JSON 파일로 저장되었습니다:\n{file_path}\n매핑 수: {len(remap_dict)}개")
            
        except Exception as e:
            self.show_error("JSON 저장 오류", f"조인트 매핑 JSON 저장 중 오류가 발생했습니다:\n{str(e)}")
    
    def import_joint_remap_xml(self):
        """XML 파일에서 조인트 리매핑을 불러옵니다."""
        try:
            # 파일 선택 다이얼로그
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "조인트 매핑 XML 불러오기", 
                os.path.join(os.path.expanduser("~"), "Documents"), 
                "XML Files (*.xml)"
            )
            
            if not file_path:
                return
            
            # XML 파일 파싱
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            if root.tag != "JointMapping":
                self.show_error("파일 오류", "올바른 조인트 매핑 XML 파일이 아닙니다.")
                return
            
            # 기존 테이블 내용 지우기
            self.joint_remap_table.setRowCount(0)
            
            # XML에서 매핑 정보 로드
            mapping_count = 0
            for mapping_elem in root.findall("Mapping"):
                source = mapping_elem.get("source", "")
                target = mapping_elem.get("target", "")
                
                if source and target:
                    row = self.joint_remap_table.rowCount()
                    self.joint_remap_table.insertRow(row)
                    
                    source_item = QtWidgets.QTableWidgetItem(source)
                    target_item = QtWidgets.QTableWidgetItem(target)
                    source_item.setFlags(source_item.flags() | QtCore.Qt.ItemIsEditable)
                    target_item.setFlags(target_item.flags() | QtCore.Qt.ItemIsEditable)
                    
                    self.joint_remap_table.setItem(row, 0, source_item)
                    self.joint_remap_table.setItem(row, 1, target_item)
                    mapping_count += 1
            
            # 조인트 리매핑 활성화
            if mapping_count > 0:
                self.remap_enable_check.setChecked(True)
            
            self.show_info("불러오기 완료", f"조인트 매핑이 XML에서 불러와졌습니다:\n{file_path}\n매핑 수: {mapping_count}개")
            
        except Exception as e:
            self.show_error("XML 불러오기 오류", f"조인트 매핑 XML 불러오기 중 오류가 발생했습니다:\n{str(e)}")
    
    def import_joint_remap_json(self):
        """JSON 파일에서 조인트 리매핑을 불러옵니다."""
        try:
            # 파일 선택 다이얼로그
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "조인트 매핑 JSON 불러오기", 
                os.path.join(os.path.expanduser("~"), "Documents"), 
                "JSON Files (*.json)"
            )
            
            if not file_path:
                return
            
            # JSON 파일 로드
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 조인트 매핑 데이터 추출
            remap_dict = {}
            if "joint_mapping" in json_data:
                remap_dict = json_data["joint_mapping"]
            elif isinstance(json_data, dict):
                # 직접 딕셔너리 형태인 경우
                remap_dict = json_data
            else:
                self.show_error("파일 오류", "올바른 조인트 매핑 JSON 파일이 아닙니다.")
                return
            
            if not remap_dict:
                self.show_error("파일 오류", "조인트 매핑 데이터가 없습니다.")
                return
            
            # 기존 테이블 내용 지우기
            self.joint_remap_table.setRowCount(0)
            
            # JSON에서 매핑 정보 로드
            mapping_count = 0
            for source, target in remap_dict.items():
                if source and target:
                    row = self.joint_remap_table.rowCount()
                    self.joint_remap_table.insertRow(row)
                    
                    source_item = QtWidgets.QTableWidgetItem(str(source))
                    target_item = QtWidgets.QTableWidgetItem(str(target))
                    source_item.setFlags(source_item.flags() | QtCore.Qt.ItemIsEditable)
                    target_item.setFlags(target_item.flags() | QtCore.Qt.ItemIsEditable)
                    
                    self.joint_remap_table.setItem(row, 0, source_item)
                    self.joint_remap_table.setItem(row, 1, target_item)
                    mapping_count += 1
            
            # 조인트 리매핑 활성화
            if mapping_count > 0:
                self.remap_enable_check.setChecked(True)
            
            self.show_info("불러오기 완료", f"조인트 매핑이 JSON에서 불러와졌습니다:\n{file_path}\n매핑 수: {mapping_count}개")
            
        except Exception as e:
            self.show_error("JSON 불러오기 오류", f"조인트 매핑 JSON 불러오기 중 오류가 발생했습니다:\n{str(e)}")
    
    def show_import_help(self):
        """Import 탭 사용법을 보여줍니다."""
        help_text = """
<h3>📥 Import 탭 사용법</h3>

<h4>1. 웨이트 파일 준비</h4>
• WeightIO 폴더에 저장된 웨이트 파일을 사용합니다<br>
• 파일명은 "{메시명}_skinWeights.xml" 또는 "{메시명}_skinWeights.json" 형식이어야 합니다<br>
• 폴더 단위로 여러 메시의 웨이트를 일괄 적용할 수 있습니다

<h4>2. 폴더 선택</h4>
• <b>Weight Folder List</b>에서 불러올 폴더를 선택하세요<br>
• <b>Refresh List</b> 버튼으로 폴더 목록을 새로고침할 수 있습니다<br>
• <b>Open Folder</b> 버튼으로 WeightIO 폴더를 탐색기에서 열 수 있습니다<br>
• <b>Weight Info</b> 버튼으로 선택된 폴더의 상세 정보를 확인할 수 있습니다

<h4>3. 조인트 리매핑 (선택사항)</h4>
• 웨이트 파일의 조인트명과 현재 씬의 조인트명이 다를 때 사용합니다<br>
• <b>조인트 리매핑 활성화</b> 체크박스를 선택하세요<br>
• <b>Add Mapping</b>으로 매핑 규칙을 추가할 수 있습니다<br>
• <b>ReMapping</b> 버튼으로 일괄 변경 규칙을 적용할 수 있습니다<br>
• XML/JSON 파일로 매핑 정보를 저장/불러오기할 수 있습니다

<h4>4. 웨이트 적용</h4>
• Maya 씬에 대상 메시가 존재해야 합니다<br>
• <b>Weight Import</b> 버튼을 클릭하여 웨이트를 적용합니다<br>
• 파일명에서 자동으로 메시명을 추출하여 해당 메시에 적용됩니다<br>
• 고성능 모드로 빠른 처리가 가능합니다

<h4>5. 주의사항</h4>
• 메시명이 파일명과 정확히 일치해야 합니다<br>
• 스킨 클러스터가 없는 메시는 자동으로 생성됩니다<br>
• 조인트 리매핑을 사용할 때는 대상 조인트가 씬에 존재해야 합니다
"""
        QtWidgets.QMessageBox.information(self, "Import 탭 사용법", help_text)

    def apply_remapping(self):
        """Search, Replace, Prefix, Suffix 내용을 joint_table에 반영합니다."""
        # 이 기능은 현재 UI에 해당하는 위젯이 없어서 빈 구현으로 둡니다.
        # WeightInfoDialog에서 사용됩니다.
        pass

    def show_error(self, title, message):
        """에러 메시지를 표시합니다."""
        QtWidgets.QMessageBox.critical(self, title, message)
    
    def show_info(self, title, message):
        """정보 메시지를 표시합니다."""
        QtWidgets.QMessageBox.information(self, title, message) 