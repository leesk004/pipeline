"""
마야 스킨 웨이트 저장/불러오기 도구 (XML 지원)
OpenMaya2 API를 사용한 고성능 버전

from R8_MaxtoMaya import R8_weight_skin_IO
from importlib import reload
reload(R8_weight_skin_IO)
R8_weight_skin_IO.show_ui()
"""

import os
import json
import xml.etree.ElementTree as ET
import time
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as om2Anim

# R8_weight_transfer_core에서 기능 가져오기
try:
    from . import R8_weight_transfer_core
    TRANSFER_CORE_AVAILABLE = True
except ImportError:
    TRANSFER_CORE_AVAILABLE = False
    print("Warning: R8_weight_transfer_core를 사용할 수 없습니다. 기본 기능만 사용됩니다.")

# PySide 임포트 (Maya 버전에 따라)
try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui

# 분리된 UI 클래스들 임포트
from importlib import reload
try:
    # 상대 임포트 사용
    from .R8_weight_export_ui import SkinWeightExportUI
    from .R8_weight_import_ui import SkinWeightImportUI
    from .R8_weight_info_dialog import WeightInfoDialog
    
    # 리로드를 위한 모듈 임포트
    from . import R8_weight_export_ui as export_ui_module
    from . import R8_weight_import_ui as import_ui_module
    from . import R8_weight_info_dialog as info_dialog_module
    
    # 개발 시 리로드 (선택적)
    reload(export_ui_module)
    reload(import_ui_module)
    reload(info_dialog_module)
    
    # 리로드 후 다시 임포트
    from .R8_weight_export_ui import SkinWeightExportUI
    from .R8_weight_import_ui import SkinWeightImportUI
    from .R8_weight_info_dialog import WeightInfoDialog
    
    UI_MODULES_AVAILABLE = True
    
except ImportError as e:
    print(f"Warning: UI 모듈 임포트 오류: {e}")
    print("기본 UI만 사용됩니다.")
    SkinWeightExportUI = None
    SkinWeightImportUI = None
    WeightInfoDialog = None
    UI_MODULES_AVAILABLE = False


def get_maya_main_window():
    """Maya 메인 윈도우를 반환합니다."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class SkinWeightIOCore:
    """스킨 웨이트 저장/불러오기 핵심 기능 클래스 (OpenMaya2 최적화)"""
    
    @staticmethod
    def get_weightio_folder():
        """WeightIO 폴더 경로를 반환하고 필요시 생성합니다."""
        # 윈도우 내문서 경로 가져오기
        import os
        documents_path = os.path.expanduser("~/Documents")
        maya_scripts_path = os.path.join(documents_path, "maya", "scripts")
        weightio_path = os.path.join(maya_scripts_path, "WeightIO")
        
        # 폴더가 없으면 생성
        if not os.path.exists(weightio_path):
            os.makedirs(weightio_path)
            print(f"WeightIO 폴더가 생성되었습니다: {weightio_path}")
        
        return weightio_path
    
    @staticmethod
    def get_weightio_files():
        """WeightIO 폴더의 웨이트 파일 목록을 반환합니다."""
        weightio_path = SkinWeightIOCore.get_weightio_folder()
        files = []
        
        try:
            for filename in os.listdir(weightio_path):
                if filename.lower().endswith(('.xml', '.json')):
                    file_path = os.path.join(weightio_path, filename)
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    file_mtime = os.path.getmtime(file_path)
                    
                    files.append({
                        'name': filename,
                        'path': file_path,
                        'size': file_size,
                        'modified': file_mtime
                    })
            
            # 수정 시간 기준으로 내림차순 정렬 (최신 파일 먼저)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            print(f"WeightIO 폴더 읽기 오류: {str(e)}")
        
        return files
    
    @staticmethod
    def get_weightio_folders():
        """WeightIO 폴더 내의 하위 폴더 목록을 반환합니다."""
        weightio_path = SkinWeightIOCore.get_weightio_folder()
        folders = []
        
        try:
            for item_name in os.listdir(weightio_path):
                item_path = os.path.join(weightio_path, item_name)
                
                # 폴더인지 확인
                if os.path.isdir(item_path):
                    # 폴더 내 _skinWeights 파일 개수 확인
                    skinweight_files = []
                    try:
                        for filename in os.listdir(item_path):
                            if ("_skinweight" in filename.lower() and 
                                filename.lower().endswith(('.xml', '.json'))):
                                skinweight_files.append(filename)
                    except Exception as e:
                        print(f"WeightIO 폴더 읽기 오류: {str(e)}")

                    # 폴더 수정 시간 가져오기
                    folder_mtime = os.path.getmtime(item_path)
                    
                    folders.append({
                        'name': item_name,
                        'path': item_path,
                        'file_count': len(skinweight_files),
                        'files': skinweight_files,
                        'modified': folder_mtime
                    })
            
            # 수정 시간 기준으로 내림차순 정렬 (최신 폴더 먼저)
            folders.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            print(f"WeightIO 폴더 읽기 오류: {str(e)}")
        
        return folders
    
    @staticmethod
    def get_selected_mesh():
        """선택된 메시를 반환합니다."""
        selection = cmds.ls(selection=True, type="transform")
        if not selection:
            raise ValueError("메시가 선택되지 않았습니다. 스킨이 적용된 메시를 선택해주세요.")
        
        # 선택된 객체의 shape 노드가 있는지 확인
        shapes = cmds.listRelatives(selection[0], shapes=True, type="mesh")
        if not shapes:
            raise ValueError("선택된 객체는 메시가 아닙니다.")
        
        return selection[0], shapes[0]
    
    @staticmethod
    def get_skin_cluster(mesh):
        """메시에 연결된 스킨 클러스터를 찾습니다."""
        if TRANSFER_CORE_AVAILABLE:
            return R8_weight_transfer_core.get_skin_cluster(mesh)
        
        # 기본 구현
        history = cmds.listHistory(mesh, pruneDagObjects=True)
        skin_clusters = cmds.ls(history, type='skinCluster')
        return skin_clusters[0] if skin_clusters else None
    
    @staticmethod
    def optimize_maya_performance():
        """Maya 성능 최적화 설정을 적용합니다."""
        # 뷰포트 업데이트 중지
        cmds.refresh(suspend=True)
        
        # 자동 키프레임 비활성화
        auto_key_state = cmds.autoKeyframe(query=True, state=True)
        cmds.autoKeyframe(state=False)
        
        # 평가 모드를 DG로 변경 (더 빠른 스킨 웨이트 처리)
        evaluation_mode = cmds.evaluationManager(query=True, mode=True)[0]
        cmds.evaluationManager(mode='off')
        
        return {
            'auto_key_state': auto_key_state,
            'evaluation_mode': evaluation_mode
        }
    
    @staticmethod
    def restore_maya_performance(state_dict):
        """Maya 성능 설정을 복원합니다."""
        # 뷰포트 업데이트 재개
        cmds.refresh(suspend=False)
        
        # 자동 키프레임 복원
        cmds.autoKeyframe(state=state_dict['auto_key_state'])
        
        # 평가 모드 복원
        cmds.evaluationManager(mode=state_dict['evaluation_mode'])
    
    @staticmethod
    def batch_import_weights_from_xml(xml_path=None, mesh_name=None, progress_callback=None, batch_size=5000, joint_remap_dict=None):
        """배치 처리를 통한 고성능 XML 웨이트 불러오기"""
        start_time = time.time()
        
        # Maya 성능 최적화
        maya_state = SkinWeightIOCore.optimize_maya_performance()
        
        # 언도 비활성화
        undo_state = cmds.undoInfo(query=True, state=True)
        cmds.undoInfo(state=False)
        
        try:
            if progress_callback:
                progress_callback(0, "고성능 XML 불러오기 시작...")
            
            # 파일 경로가 지정되지 않은 경우 파일 선택 다이얼로그 열기
            if not xml_path:
                file_filter = "XML Files (*.xml);;All Files (*.*)"
                xml_path = cmds.fileDialog2(fileFilter=file_filter, dialogStyle=2, fileMode=1)
                if not xml_path:
                    return False
                xml_path = xml_path[0]
            
            if progress_callback:
                progress_callback(5, "XML 파일 파싱 중...")
            
            # XML 파일 파싱
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 메시 이름 확인
            target_mesh = mesh_name if mesh_name else root.get("mesh")
            if not cmds.objExists(target_mesh):
                raise ValueError(f"메시 '{target_mesh}'를 찾을 수 없습니다.")
            
            # 메시의 shape 노드 가져오기
            shapes = cmds.listRelatives(target_mesh, shapes=True, type="mesh")
            if not shapes:
                raise ValueError(f"{target_mesh}는 메시가 아닙니다.")
            
            mesh_shape = shapes[0]
            
            # 스킨 클러스터 확인
            skin_cluster = SkinWeightIOCore.get_skin_cluster(mesh_shape)
            if not skin_cluster:
                raise ValueError(f"{mesh_shape}에 스킨 클러스터가 없습니다.")
            
            if progress_callback:
                progress_callback(10, "OpenMaya2 API 초기화 중...")
            
            # OpenMaya2 API 설정
            sel = om2.MSelectionList()
            sel.add(target_mesh)
            sel.add(skin_cluster)
            
            mesh_dag = sel.getDagPath(0)
            skin_obj = sel.getDependNode(1)
            skin_fn = om2Anim.MFnSkinCluster(skin_obj)
            
            # 인플루언스 정보 가져오기
            current_influences = skin_fn.influenceObjects()
            current_influence_names = [current_influences[i].partialPathName() for i in range(len(current_influences))]
            
            # XML 인플루언스 매핑 (조인트 리매핑 적용)
            influences_elem = root.find("Influences")
            influence_index_map = {}
            for inf_elem in influences_elem.findall("Influence"):
                xml_index = int(inf_elem.get("index"))
                joint_name = inf_elem.get("name")
                
                # 조인트 리매핑 적용
                if joint_remap_dict and joint_name in joint_remap_dict:
                    joint_name = joint_remap_dict[joint_name]
                
                if joint_name in current_influence_names:
                    maya_index = current_influence_names.index(joint_name)
                    influence_index_map[xml_index] = maya_index
            
            # 메시 정보
            vertex_count = cmds.polyEvaluate(target_mesh, vertex=True)
            influence_count = len(current_influence_names)
            
            if progress_callback:
                progress_callback(15, f"배치 처리 준비 중... (배치 크기: {batch_size})")
            
            # 정규화 일시 중지
            cmds.setAttr(f"{skin_cluster}.normalizeWeights", 0)
            
            # 웨이트 데이터 파싱
            weights_elem = root.find("Weights")
            vertex_elements = weights_elem.findall("Vertex")
            total_vertices = len(vertex_elements)
            
            # 배치별로 처리
            for batch_start in range(0, total_vertices, batch_size):
                batch_end = min(batch_start + batch_size, total_vertices)
                batch_vertices = vertex_elements[batch_start:batch_end]
                
                if progress_callback:
                    percent = 15 + int((batch_start / total_vertices) * 70)
                    progress_callback(percent, f"배치 {batch_start//batch_size + 1} 처리 중... ({batch_start}-{batch_end}/{total_vertices})")
                
                # 배치용 웨이트 배열 생성
                batch_size_actual = len(batch_vertices)
                
                # 배열 크기 미리 계산
                total_batch_weights = batch_size_actual * influence_count
                
                # Python 리스트로 먼저 생성
                batch_weights_list = [0.0] * total_batch_weights
                
                batch_vertex_ids = []
                
                # 배치 내 버텍스 처리
                for local_idx, vertex_elem in enumerate(batch_vertices):
                    vertex_id = int(vertex_elem.get("id"))
                    batch_vertex_ids.append(vertex_id)
                    
                    # 웨이트 설정
                    for weight_elem in vertex_elem.findall("Weight"):
                        xml_inf_index = int(weight_elem.get("influence"))
                        weight_value = float(weight_elem.get("value"))
                        
                        if xml_inf_index in influence_index_map:
                            maya_inf_index = influence_index_map[xml_inf_index]
                            if 0 <= maya_inf_index < influence_count:
                                array_index = local_idx * influence_count + maya_inf_index
                                if 0 <= array_index < total_batch_weights:
                                    batch_weights_list[array_index] = weight_value
                
                # Python 리스트를 MDoubleArray로 변환
                batch_weights = om2.MDoubleArray(batch_weights_list)
                
                # 배치 컴포넌트 생성
                fn_comp = om2.MFnSingleIndexedComponent()
                batch_comp = fn_comp.create(om2.MFn.kMeshVertComponent)
                for vertex_id in batch_vertex_ids:
                    fn_comp.addElement(vertex_id)
                
                # 배치 웨이트 적용
                # 인플루언스 인덱스 배열 생성
                influence_indices = om2.MIntArray()
                for i in range(influence_count):
                    influence_indices.append(i)
                
                # 배치 웨이트 적용 - 올바른 매개변수 순서
                skin_fn.setWeights(mesh_dag, batch_comp, influence_indices, batch_weights, False)
            
            # 정규화 활성화
            if progress_callback:
                progress_callback(90, "스킨 웨이트 정규화 중...")
            
            cmds.setAttr(f"{skin_cluster}.normalizeWeights", 1)
            cmds.skinCluster(skin_cluster, edit=True, forceNormalizeWeights=True)
            
            if progress_callback:
                progress_callback(100, "배치 불러오기 완료!")
            
            end_time = time.time()
            remap_info = f" (조인트 리매핑: {len(joint_remap_dict)}개)" if joint_remap_dict else ""
            print(f"고성능 배치 처리로 스킨 웨이트가 성공적으로 불러와졌습니다: {xml_path}{remap_info}")
            print(f"실행 시간: {end_time - start_time:.2f}초")
            print(f"배치 크기: {batch_size}, 총 배치 수: {(total_vertices + batch_size - 1) // batch_size}")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"오류: {str(e)}")
            raise e
        finally:
            # Maya 설정 복원
            SkinWeightIOCore.restore_maya_performance(maya_state)
            cmds.undoInfo(state=undo_state)
    
    @staticmethod
    def export_weights_to_xml(mesh_name, export_path="", progress_callback=None):
        """OpenMaya2 API를 사용하여 스킨 웨이트를 XML 파일로 저장합니다."""
        start_time = time.time()
        
        # 언도 비활성화
        undo_state = cmds.undoInfo(query=True, state=True)
        cmds.undoInfo(state=False)
        
        try:
            mesh_transform, mesh_shape = SkinWeightIOCore.get_selected_mesh()
            skin_cluster = SkinWeightIOCore.get_skin_cluster(mesh_shape)
            
            if not skin_cluster:
                raise ValueError(f"{mesh_shape}에 스킨 클러스터가 없습니다.")
            
            if progress_callback:
                progress_callback(5, "OpenMaya2 API 초기화 중...")
            
            # Maya API 2.0 사용하여 효율적으로 데이터 추출
            sel = om2.MSelectionList()
            sel.add(mesh_transform)
            sel.add(skin_cluster)
            
            mesh_dag = sel.getDagPath(0)
            skin_obj = sel.getDependNode(1)
            skin_fn = om2Anim.MFnSkinCluster(skin_obj)
            
            # 인플루언스 정보 가져오기
            influences = skin_fn.influenceObjects()
            influence_names = [influences[i].partialPathName() for i in range(len(influences))]
            
            if progress_callback:
                progress_callback(15, f"인플루언스 {len(influence_names)}개 확인됨...")
            
            # 버텍스 개수 가져오기
            vertex_count = cmds.polyEvaluate(mesh_transform, vertex=True)
            
            # 모든 버텍스에 대한 컴포넌트 생성
            fn_comp = om2.MFnSingleIndexedComponent()
            full_comp = fn_comp.create(om2.MFn.kMeshVertComponent)
            for i in range(vertex_count):
                fn_comp.addElement(i)
            
            if progress_callback:
                progress_callback(25, f"버텍스 웨이트 데이터 로딩 중... (총 {vertex_count}개)")
            
            # 모든 웨이트 데이터를 한 번에 가져오기
            weights, influence_count = skin_fn.getWeights(mesh_dag, full_comp)
            
            if progress_callback:
                progress_callback(40, "XML 구조 생성 중...")
            
            # XML 루트 요소 생성
            root = ET.Element("SkinWeights")
            root.set("mesh", mesh_transform)
            root.set("skinCluster", skin_cluster)
            root.set("vertexCount", str(vertex_count))
            
            # 인플루언스 정보 추가
            influences_elem = ET.SubElement(root, "Influences")
            for i, influence in enumerate(influence_names):
                inf_elem = ET.SubElement(influences_elem, "Influence")
                inf_elem.set("index", str(i))
                inf_elem.set("name", influence)
            
            # 웨이트 데이터 추가
            weights_elem = ET.SubElement(root, "Weights")
            
            # 웨이트를 2차원 배열로 재구성
            influence_per_vertex = len(influence_names)
            
            for vertex_id in range(vertex_count):
                # 진행 상황 업데이트
                if progress_callback and vertex_id % 500 == 0:
                    percent = 40 + int((vertex_id / vertex_count) * 50)
                    progress_callback(percent, f"XML 웨이트 데이터 생성 중... ({vertex_id}/{vertex_count})")
                
                # 해당 버텍스의 웨이트 추출
                start_idx = vertex_id * influence_per_vertex
                vertex_weights = weights[start_idx:start_idx + influence_per_vertex]
                
                # 0이 아닌 웨이트만 저장
                vertex_elem = ET.SubElement(weights_elem, "Vertex")
                vertex_elem.set("id", str(vertex_id))
                
                has_weights = False
                for inf_idx, weight in enumerate(vertex_weights):
                    if weight > 0.0001:  # 매우 작은 값 무시
                        weight_elem = ET.SubElement(vertex_elem, "Weight")
                        weight_elem.set("influence", str(inf_idx))
                        weight_elem.set("value", str(weight))
                        has_weights = True
                
                # 웨이트가 없는 버텍스는 제거
                if not has_weights:
                    weights_elem.remove(vertex_elem)
            
            # 파일 경로 설정
            if not export_path:
                weightio_folder = SkinWeightIOCore.get_weightio_folder()
                export_path = os.path.join(weightio_folder, f"{mesh_transform}_skinWeights.xml")
            
            if progress_callback:
                progress_callback(90, "XML 파일 저장 중...")
            
            # XML 파일로 저장
            tree = ET.ElementTree(root)
            tree.write(export_path, encoding='utf-8', xml_declaration=True)
            
            if progress_callback:
                progress_callback(100, "내보내기 완료!")
            
            end_time = time.time()
            print(f"스킨 웨이트가 성공적으로 저장되었습니다: {export_path}")
            print(f"실행 시간: {end_time - start_time:.2f}초")
            
            return export_path
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"오류: {str(e)}")
            raise e
        finally:
            cmds.undoInfo(state=undo_state)
    
    @staticmethod
    def export_weights_to_json(mesh_name, export_path="", progress_callback=None):
        """OpenMaya2 API를 사용하여 스킨 웨이트를 JSON 파일로 저장합니다."""
        start_time = time.time()
        
        # 언도 비활성화
        undo_state = cmds.undoInfo(query=True, state=True)
        cmds.undoInfo(state=False)
        
        try:
            mesh_transform, mesh_shape = SkinWeightIOCore.get_selected_mesh()
            skin_cluster = SkinWeightIOCore.get_skin_cluster(mesh_shape)
            
            if not skin_cluster:
                raise ValueError(f"{mesh_shape}에 스킨 클러스터가 없습니다.")
            
            if progress_callback:
                progress_callback(5, "OpenMaya2 API 초기화 중...")
            
            # Maya API 2.0 사용
            sel = om2.MSelectionList()
            sel.add(mesh_transform)
            sel.add(skin_cluster)
            
            mesh_dag = sel.getDagPath(0)
            skin_obj = sel.getDependNode(1)
            skin_fn = om2Anim.MFnSkinCluster(skin_obj)
            
            # 인플루언스 정보 가져오기
            influences = skin_fn.influenceObjects()
            influence_names = [influences[i].partialPathName() for i in range(len(influences))]
            
            if progress_callback:
                progress_callback(15, f"인플루언스 {len(influence_names)}개 확인됨...")
            
            # 버텍스 개수 가져오기
            vertex_count = cmds.polyEvaluate(mesh_transform, vertex=True)
            
            # 모든 버텍스에 대한 컴포넌트 생성
            fn_comp = om2.MFnSingleIndexedComponent()
            full_comp = fn_comp.create(om2.MFn.kMeshVertComponent)
            for i in range(vertex_count):
                fn_comp.addElement(i)
            
            if progress_callback:
                progress_callback(25, f"버텍스 웨이트 데이터 로딩 중... (총 {vertex_count}개)")
            
            # 모든 웨이트 데이터를 한 번에 가져오기
            weights, influence_count = skin_fn.getWeights(mesh_dag, full_comp)
            
            if progress_callback:
                progress_callback(40, "JSON 데이터 구조 생성 중...")
            
            # JSON 데이터 구조 생성
            weight_data = {
                "mesh_name": mesh_transform,
                "skin_cluster": skin_cluster,
                "influences": influence_names,
                "weights": {}
            }
            
            # 웨이트를 2차원 배열로 재구성
            influence_per_vertex = len(influence_names)
            
            for vertex_id in range(vertex_count):
                # 진행 상황 업데이트
                if progress_callback and vertex_id % 500 == 0:
                    percent = 40 + int((vertex_id / vertex_count) * 50)
                    progress_callback(percent, f"JSON 웨이트 데이터 생성 중... ({vertex_id}/{vertex_count})")
                
                # 해당 버텍스의 웨이트 추출
                start_idx = vertex_id * influence_per_vertex
                vertex_weights = weights[start_idx:start_idx + influence_per_vertex]
                
                # 0이 아닌 웨이트만 저장
                vertex_weight_dict = {}
                for inf_idx, weight in enumerate(vertex_weights):
                    if weight > 0.0001:  # 매우 작은 값 무시
                        vertex_weight_dict[influence_names[inf_idx]] = weight
                
                if vertex_weight_dict:
                    weight_data["weights"][vertex_id] = vertex_weight_dict
            
            # 파일 경로 설정
            if not export_path:
                weightio_folder = SkinWeightIOCore.get_weightio_folder()
                export_path = os.path.join(weightio_folder, f"{mesh_transform}_skinWeights.json")
            
            if progress_callback:
                progress_callback(90, "JSON 파일 저장 중...")
            
            # JSON 파일로 저장
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(weight_data, f, indent=2, ensure_ascii=False)
            
            if progress_callback:
                progress_callback(100, "내보내기 완료!")
            
            end_time = time.time()
            print(f"스킨 웨이트가 성공적으로 저장되었습니다: {export_path}")
            print(f"실행 시간: {end_time - start_time:.2f}초")
            
            return export_path
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"오류: {str(e)}")
            raise e
        finally:
            cmds.undoInfo(state=undo_state)
    
    @staticmethod
    def import_weights_from_xml(xml_path=None, mesh_name=None, progress_callback=None, joint_remap_dict=None):
        """XML 파일에서 스킨 웨이트를 불러와 적용합니다. (OpenMaya2 최적화)"""
        start_time = time.time()
        
        # 언도 비활성화
        undo_state = cmds.undoInfo(query=True, state=True)
        cmds.undoInfo(state=False)
        
        # 평가 모드 변경
        evaluation_mode = cmds.evaluationManager(query=True, mode=True)[0]
        cmds.evaluationManager(mode='off')
        
        try:
            if progress_callback:
                progress_callback(0, "XML 파일 불러오기 준비 중...")
            
            # 파일 경로가 지정되지 않은 경우 파일 선택 다이얼로그 열기
            if not xml_path:
                file_filter = "XML Files (*.xml);;All Files (*.*)"
                xml_path = cmds.fileDialog2(fileFilter=file_filter, dialogStyle=2, fileMode=1)
                if not xml_path:
                    return False
                xml_path = xml_path[0]
            
            if progress_callback:
                progress_callback(5, "XML 파일 파싱 중...")
            
            # XML 파일 파싱
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 메시 이름 확인
            target_mesh = mesh_name if mesh_name else root.get("mesh")
            if not cmds.objExists(target_mesh):
                raise ValueError(f"메시 '{target_mesh}'를 찾을 수 없습니다.")
            
            # 메시의 shape 노드 가져오기
            shapes = cmds.listRelatives(target_mesh, shapes=True, type="mesh")
            if not shapes:
                raise ValueError(f"{target_mesh}는 메시가 아닙니다.")
            
            mesh_shape = shapes[0]
            
            if progress_callback:
                progress_callback(10, "인플루언스 정보 로딩 중...")
            
            # 인플루언스 정보 파싱 (조인트 리매핑 적용)
            influences_elem = root.find("Influences")
            influence_map = {}
            influence_names = []
            for inf_elem in influences_elem.findall("Influence"):
                index = int(inf_elem.get("index"))
                name = inf_elem.get("name")
                
                # 조인트 리매핑 적용
                if joint_remap_dict and name in joint_remap_dict:
                    name = joint_remap_dict[name]
                
                influence_map[index] = name
                influence_names.append(name)
            
            if progress_callback:
                progress_callback(15, "스킨 클러스터 확인 중...")
            
            # 스킨 클러스터 확인 또는 생성
            skin_cluster = SkinWeightIOCore.get_skin_cluster(mesh_shape)
            
            if not skin_cluster:
                # 스킨 클러스터가 없으면 생성
                if progress_callback:
                    progress_callback(20, "스킨 클러스터 생성 중...")
                
                joints = list(influence_map.values())
                existing_joints = [j for j in joints if cmds.objExists(j)]
                
                if not existing_joints:
                    raise ValueError("인플루언스 조인트를 찾을 수 없습니다.")
                
                cmds.select(existing_joints + [target_mesh], r=True)
                skin_cluster = cmds.skinCluster(
                    toSelectedBones=True,
                    bindMethod=0,
                    skinMethod=0,
                    normalizeWeights=1,
                    maximumInfluences=4,
                    dropoffRate=4.0
                )[0]
            else:
                # 기존 스킨 클러스터에 필요한 조인트 추가
                current_influences = cmds.skinCluster(skin_cluster, query=True, influence=True)
                for joint in influence_map.values():
                    if joint not in current_influences and cmds.objExists(joint):
                        cmds.skinCluster(skin_cluster, edit=True, addInfluence=joint, weight=0)
            
            if progress_callback:
                progress_callback(25, "OpenMaya2 API 초기화 중...")
            
            # OpenMaya2 API 설정
            sel = om2.MSelectionList()
            sel.add(target_mesh)
            sel.add(skin_cluster)
            
            mesh_dag = sel.getDagPath(0)
            skin_obj = sel.getDependNode(1)
            skin_fn = om2Anim.MFnSkinCluster(skin_obj)
            
            # 현재 스킨 클러스터의 인플루언스 정보 가져오기
            current_influences = skin_fn.influenceObjects()
            current_influence_names = [current_influences[i].partialPathName() for i in range(len(current_influences))]
            
            # 인플루언스 인덱스 매핑 생성
            influence_index_map = {}
            for xml_index, joint_name in influence_map.items():
                if joint_name in current_influence_names:
                    maya_index = current_influence_names.index(joint_name)
                    influence_index_map[xml_index] = maya_index
            
            # 메시의 버텍스 개수 확인
            vertex_count = cmds.polyEvaluate(target_mesh, vertex=True)
            
            if progress_callback:
                progress_callback(30, "웨이트 데이터 구조 준비 중...")
            
            # 웨이트 배열 초기화 (vertex_count x influence_count)
            influence_count = len(current_influence_names)
            
            # MDoubleArray 생성 - 안전한 방법으로 초기화
            total_weights = vertex_count * influence_count
            
            # Python 리스트로 먼저 생성
            weights_list = [0.0] * total_weights
            
            # XML에서 웨이트 데이터 파싱
            weights_elem = root.find("Weights")
            vertex_elements = weights_elem.findall("Vertex")
            total_vertices = len(vertex_elements)
            
            if progress_callback:
                progress_callback(35, f"웨이트 데이터 파싱 중... (총 {total_vertices}개 버텍스)")
            
            # 웨이트 데이터를 배열에 설정
            for i, vertex_elem in enumerate(vertex_elements):
                if progress_callback and i % 1000 == 0:
                    percent = 35 + int((i / total_vertices) * 40)
                    progress_callback(percent, f"웨이트 데이터 파싱 중... ({i}/{total_vertices})")
                
                vertex_id = int(vertex_elem.get("id"))
                
                # 버텍스 ID가 유효한 범위인지 확인
                if vertex_id >= vertex_count:
                    continue
                
                # 해당 버텍스의 웨이트 정보 수집
                vertex_weights = [0.0] * influence_count
                total_weight = 0.0
                
                for weight_elem in vertex_elem.findall("Weight"):
                    xml_inf_index = int(weight_elem.get("influence"))
                    weight_value = float(weight_elem.get("value"))
                    
                    # XML 인덱스를 Maya 인덱스로 변환
                    if xml_inf_index in influence_index_map:
                        maya_inf_index = influence_index_map[xml_inf_index]
                        if 0 <= maya_inf_index < influence_count:
                            vertex_weights[maya_inf_index] = weight_value
                            total_weight += weight_value
                
                # 웨이트 정규화 (필요한 경우)
                if total_weight > 0.0001:
                    for j in range(influence_count):
                        if vertex_weights[j] > 0.0001:
                            vertex_weights[j] = vertex_weights[j] / total_weight
                
                # 배열에 웨이트 설정 - 안전한 인덱스 계산
                for j in range(influence_count):
                    array_index = vertex_id * influence_count + j
                    if 0 <= array_index < total_weights:
                        weights_list[array_index] = vertex_weights[j]
            
            if progress_callback:
                progress_callback(75, "OpenMaya2 API로 웨이트 적용 중...")
            
            # 정규화 일시 중지
            cmds.setAttr(f"{skin_cluster}.normalizeWeights", 0)
            
            # 모든 버텍스에 대한 컴포넌트 생성
            fn_comp = om2.MFnSingleIndexedComponent()
            full_comp = fn_comp.create(om2.MFn.kMeshVertComponent)
            for i in range(vertex_count):
                fn_comp.addElement(i)
            
            # 인플루언스 인덱스 배열 생성
            influence_indices = om2.MIntArray()
            for i in range(influence_count):
                influence_indices.append(i)
            
            # OpenMaya2 API를 사용하여 모든 웨이트를 한 번에 설정 - 올바른 매개변수 순서
            skin_fn.setWeights(mesh_dag, full_comp, influence_indices, om2.MDoubleArray(weights_list), False)
            
            # 정규화 활성화
            if progress_callback:
                progress_callback(95, "스킨 웨이트 정규화 중...")
            
            cmds.setAttr(f"{skin_cluster}.normalizeWeights", 1)
            cmds.skinCluster(skin_cluster, edit=True, forceNormalizeWeights=True)
            
            if progress_callback:
                progress_callback(100, "불러오기 완료!")
            
            end_time = time.time()
            remap_info = f" (조인트 리매핑: {len(joint_remap_dict)}개)" if joint_remap_dict else ""
            print(f"스킨 웨이트가 성공적으로 불러와졌습니다: {xml_path}{remap_info}")
            print(f"실행 시간: {end_time - start_time:.2f}초")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"오류: {str(e)}")
            raise e
        finally:
            cmds.evaluationManager(mode=evaluation_mode)
            cmds.undoInfo(state=undo_state)

    @staticmethod
    def import_weights_from_json(json_path=None, mesh_name=None, progress_callback=None, joint_remap_dict=None):
        """JSON 파일에서 스킨 웨이트를 불러와 적용합니다. (OpenMaya2 최적화)"""
        start_time = time.time()
        
        # 언도 비활성화
        undo_state = cmds.undoInfo(query=True, state=True)
        cmds.undoInfo(state=False)
        
        # 평가 모드 변경
        evaluation_mode = cmds.evaluationManager(query=True, mode=True)[0]
        cmds.evaluationManager(mode='off')
        
        try:
            if progress_callback:
                progress_callback(0, "JSON 파일 불러오기 준비 중...")
            
            # 파일 경로가 지정되지 않은 경우 파일 선택 다이얼로그 열기
            if not json_path:
                file_filter = "JSON Files (*.json);;All Files (*.*)"
                json_path = cmds.fileDialog2(fileFilter=file_filter, dialogStyle=2, fileMode=1)
                if not json_path:
                    return False
                json_path = json_path[0]
            
            if progress_callback:
                progress_callback(5, "JSON 파일 파싱 중...")
            
            # JSON 파일 파싱
            with open(json_path, 'r', encoding='utf-8') as f:
                weight_data = json.load(f)
            
            # 메시 이름 확인
            target_mesh = mesh_name if mesh_name else weight_data.get("mesh_name")
            if not target_mesh or not cmds.objExists(target_mesh):
                raise ValueError(f"메시 '{target_mesh}'를 찾을 수 없습니다.")
            
            # 메시의 shape 노드 가져오기
            shapes = cmds.listRelatives(target_mesh, shapes=True, type="mesh")
            if not shapes:
                raise ValueError(f"{target_mesh}는 메시가 아닙니다.")
            
            mesh_shape = shapes[0]
            
            if progress_callback:
                progress_callback(10, "인플루언스 정보 로딩 중...")
            
            # 인플루언스 정보 파싱 (조인트 리매핑 적용)
            influence_names = weight_data.get("influences", [])
            if joint_remap_dict:
                # 조인트 리매핑 적용
                remapped_influences = []
                for influence in influence_names:
                    if influence in joint_remap_dict:
                        remapped_influences.append(joint_remap_dict[influence])
                    else:
                        remapped_influences.append(influence)
                influence_names = remapped_influences
            
            if progress_callback:
                progress_callback(15, "스킨 클러스터 확인 중...")
            
            # 스킨 클러스터 확인 또는 생성
            skin_cluster = SkinWeightIOCore.get_skin_cluster(mesh_shape)
            
            if not skin_cluster:
                # 스킨 클러스터가 없으면 생성
                if progress_callback:
                    progress_callback(20, "스킨 클러스터 생성 중...")
                
                existing_joints = [j for j in influence_names if cmds.objExists(j)]
                
                if not existing_joints:
                    raise ValueError("인플루언스 조인트를 찾을 수 없습니다.")
                
                cmds.select(existing_joints + [target_mesh], r=True)
                skin_cluster = cmds.skinCluster(
                    toSelectedBones=True,
                    bindMethod=0,
                    skinMethod=0,
                    normalizeWeights=1,
                    maximumInfluences=4,
                    dropoffRate=4.0
                )[0]
            else:
                # 기존 스킨 클러스터에 필요한 조인트 추가
                current_influences = cmds.skinCluster(skin_cluster, query=True, influence=True)
                for joint in influence_names:
                    if joint not in current_influences and cmds.objExists(joint):
                        cmds.skinCluster(skin_cluster, edit=True, addInfluence=joint, weight=0)
            
            if progress_callback:
                progress_callback(25, "OpenMaya2 API 초기화 중...")
            
            # OpenMaya2 API 설정
            sel = om2.MSelectionList()
            sel.add(target_mesh)
            sel.add(skin_cluster)
            
            mesh_dag = sel.getDagPath(0)
            skin_obj = sel.getDependNode(1)
            skin_fn = om2Anim.MFnSkinCluster(skin_obj)
            
            # 현재 스킨 클러스터의 인플루언스 정보 가져오기
            current_influences = skin_fn.influenceObjects()
            current_influence_names = [current_influences[i].partialPathName() for i in range(len(current_influences))]
            
            # 메시의 버텍스 개수 확인
            vertex_count = cmds.polyEvaluate(target_mesh, vertex=True)
            
            if progress_callback:
                progress_callback(30, "웨이트 데이터 구조 준비 중...")
            
            # 웨이트 배열 초기화 (vertex_count x influence_count)
            influence_count = len(current_influence_names)
            total_weights = vertex_count * influence_count
            
            # Python 리스트로 먼저 생성
            weights_list = [0.0] * total_weights
            
            # JSON에서 웨이트 데이터 파싱
            weights_data = weight_data.get("weights", {})
            total_vertices = len(weights_data)
            
            if progress_callback:
                progress_callback(35, f"웨이트 데이터 파싱 중... (총 {total_vertices}개 버텍스)")
            
            # 웨이트 데이터를 배열에 설정
            for i, (vertex_id_str, vertex_weights) in enumerate(weights_data.items()):
                if progress_callback and i % 1000 == 0:
                    percent = 35 + int((i / total_vertices) * 40)
                    progress_callback(percent, f"웨이트 데이터 파싱 중... ({i}/{total_vertices})")
                
                vertex_id = int(vertex_id_str)
                
                # 버텍스 ID가 유효한 범위인지 확인
                if vertex_id >= vertex_count:
                    continue
                
                # 해당 버텍스의 웨이트 정보 수집
                vertex_weight_values = [0.0] * influence_count
                total_weight = 0.0
                
                for joint_name, weight_value in vertex_weights.items():
                    # 조인트 리매핑 적용
                    if joint_remap_dict and joint_name in joint_remap_dict:
                        joint_name = joint_remap_dict[joint_name]
                    
                    if joint_name in current_influence_names:
                        maya_inf_index = current_influence_names.index(joint_name)
                        if 0 <= maya_inf_index < influence_count:
                            vertex_weight_values[maya_inf_index] = float(weight_value)
                            total_weight += float(weight_value)
                
                # 웨이트 정규화 (필요한 경우)
                if total_weight > 0.0001:
                    for j in range(influence_count):
                        if vertex_weight_values[j] > 0.0001:
                            vertex_weight_values[j] = vertex_weight_values[j] / total_weight
                
                # 배열에 웨이트 설정
                for j in range(influence_count):
                    array_index = vertex_id * influence_count + j
                    if 0 <= array_index < total_weights:
                        weights_list[array_index] = vertex_weight_values[j]
            
            if progress_callback:
                progress_callback(75, "OpenMaya2 API로 웨이트 적용 중...")
            
            # 정규화 일시 중지
            cmds.setAttr(f"{skin_cluster}.normalizeWeights", 0)
            
            # 모든 버텍스에 대한 컴포넌트 생성
            fn_comp = om2.MFnSingleIndexedComponent()
            full_comp = fn_comp.create(om2.MFn.kMeshVertComponent)
            for i in range(vertex_count):
                fn_comp.addElement(i)
            
            # 인플루언스 인덱스 배열 생성
            influence_indices = om2.MIntArray()
            for i in range(influence_count):
                influence_indices.append(i)
            
            # OpenMaya2 API를 사용하여 모든 웨이트를 한 번에 설정
            skin_fn.setWeights(mesh_dag, full_comp, influence_indices, om2.MDoubleArray(weights_list), False)
            
            # 정규화 활성화
            if progress_callback:
                progress_callback(95, "스킨 웨이트 정규화 중...")
            
            cmds.setAttr(f"{skin_cluster}.normalizeWeights", 1)
            cmds.skinCluster(skin_cluster, edit=True, forceNormalizeWeights=True)
            
            if progress_callback:
                progress_callback(100, "불러오기 완료!")
            
            end_time = time.time()
            remap_info = f" (조인트 리매핑: {len(joint_remap_dict)}개)" if joint_remap_dict else ""
            print(f"스킨 웨이트가 성공적으로 불러와졌습니다: {json_path}{remap_info}")
            print(f"실행 시간: {end_time - start_time:.2f}초")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"오류: {str(e)}")
            raise e
        finally:
            cmds.evaluationManager(mode=evaluation_mode)
            cmds.undoInfo(state=undo_state)


class SkinWeightIOUI(QtWidgets.QDialog):
    """스킨 웨이트 저장/불러오기 통합 UI 클래스 (탭 기반)"""
    
    def __init__(self, parent=get_maya_main_window()):
        super(SkinWeightIOUI, self).__init__(parent)
        
        # 윈도우 설정
        self.setWindowTitle("Skin Weight IO")
        self.resize(600, 650)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        # 핵심 기능 클래스 인스턴스 생성
        self.core = SkinWeightIOCore()
        
        # UI 구성
        self.create_widgets()
        self.create_layouts()
        self.create_connections()
    
    def create_widgets(self):
        """UI 위젯을 생성합니다."""
        # 메인 탭 위젯
        self.tab_widget = QtWidgets.QTabWidget()
        
        # UI 모듈들이 올바르게 임포트되었는지 확인
        if not UI_MODULES_AVAILABLE or SkinWeightExportUI is None or SkinWeightImportUI is None:
            # 기본 UI 생성 (임포트 실패 시)
            self.create_basic_ui()
        else:
            # === 익스포트 탭 ===
            self.export_ui = SkinWeightExportUI(self.core, self)
            self.tab_widget.addTab(self.export_ui, "Export")
            
            # === 임포트 탭 ===
            self.import_ui = SkinWeightImportUI(self.core, self)
            self.tab_widget.addTab(self.import_ui, "Import")
        
        # === 공통 진행 상황 표시 ===
        self.progress_group = QtWidgets.QGroupBox("Progress")
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_label = QtWidgets.QLabel("Waiting...")
        
        # 초기 프로그레스 바 숨기기
        self.progress_group.setVisible(False)
    
    def create_basic_ui(self):
        """기본 UI를 생성합니다 (모듈 임포트 실패 시)."""
        # 기본 익스포트 탭
        export_tab = QtWidgets.QWidget()
        export_layout = QtWidgets.QVBoxLayout(export_tab)
        
        export_label = QtWidgets.QLabel("기본 익스포트 기능")
        export_xml_btn = QtWidgets.QPushButton("XML로 내보내기")
        export_json_btn = QtWidgets.QPushButton("JSON으로 내보내기")
        
        export_layout.addWidget(export_label)
        export_layout.addWidget(export_xml_btn)
        export_layout.addWidget(export_json_btn)
        export_layout.addStretch()
        
        # 기본 임포트 탭
        import_tab = QtWidgets.QWidget()
        import_layout = QtWidgets.QVBoxLayout(import_tab)
        
        import_label = QtWidgets.QLabel("기본 임포트 기능")
        import_xml_btn = QtWidgets.QPushButton("XML에서 불러오기")
        import_json_btn = QtWidgets.QPushButton("JSON에서 불러오기")
        
        import_layout.addWidget(import_label)
        import_layout.addWidget(import_xml_btn)
        import_layout.addWidget(import_json_btn)
        import_layout.addStretch()
        
        # 탭에 추가
        self.tab_widget.addTab(export_tab, "Export")
        self.tab_widget.addTab(import_tab, "Import")
        
        # 기본 기능 연결
        export_xml_btn.clicked.connect(self.basic_export_xml)
        export_json_btn.clicked.connect(self.basic_export_json)
        import_xml_btn.clicked.connect(self.basic_import_xml)
        import_json_btn.clicked.connect(self.basic_import_json)
    
    def basic_export_xml(self):
        """기본 XML 내보내기"""
        try:
            result = quick_export_xml()
            if result:
                QtWidgets.QMessageBox.information(self, "성공", f"XML 파일이 저장되었습니다:\n{result}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"내보내기 오류: {str(e)}")
    
    def basic_export_json(self):
        """기본 JSON 내보내기"""
        try:
            result = quick_export_json()
            if result:
                QtWidgets.QMessageBox.information(self, "성공", f"JSON 파일이 저장되었습니다:\n{result}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"내보내기 오류: {str(e)}")
    
    def basic_import_xml(self):
        """기본 XML 불러오기"""
        try:
            result = quick_import_xml()
            if result:
                QtWidgets.QMessageBox.information(self, "성공", "XML 파일이 성공적으로 불러와졌습니다.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"불러오기 오류: {str(e)}")
    
    def basic_import_json(self):
        """기본 JSON 불러오기"""
        try:
            result = quick_import_json()
            if result:
                QtWidgets.QMessageBox.information(self, "성공", "JSON 파일이 성공적으로 불러와졌습니다.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"불러오기 오류: {str(e)}")
    
    def create_layouts(self):
        """레이아웃을 생성합니다."""
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # 메인 탭 추가
        main_layout.addWidget(self.tab_widget)
        
        # 진행 상황 레이아웃
        progress_layout = QtWidgets.QVBoxLayout(self.progress_group)
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(self.progress_group)
    
    def create_connections(self):
        """시그널과 슬롯을 연결합니다."""
        pass  # 개별 UI 클래스에서 자체 연결 관리
    
    def update_progress(self, value, message=""):
        """진행 상황을 업데이트합니다."""
        # 프로그레스 바 표시
        self.progress_group.setVisible(True)
        
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        QtWidgets.QApplication.processEvents()
        
        # 100% 완료 시 3초 후 자동으로 초기화
        if value == 100:
            QtCore.QTimer.singleShot(3000, self.reset_progress_bar)
    
    def reset_progress_bar(self):
        """프로그레스 바를 초기 상태로 리셋하고 숨깁니다."""
        self.progress_bar.setValue(0)
        self.progress_label.setText("Waiting...")
        # 프로그레스 바 숨기기
        self.progress_group.setVisible(False)


def show_ui():
    """UI 표시 함수"""
    global skin_weight_io_window
    try:
        skin_weight_io_window.close()
        skin_weight_io_window.deleteLater()
    except:
        pass
    
    skin_weight_io_window = SkinWeightIOUI()
    skin_weight_io_window.show()


# 메인 실행 함수들 (스크립트로 직접 호출 가능)
def quick_export_xml(mesh_name=None):
    """빠른 XML 내보내기"""
    try:
        if not mesh_name:
            mesh_name, _ = SkinWeightIOCore.get_selected_mesh()
        return SkinWeightIOCore.export_weights_to_xml(mesh_name)
    except Exception as e:
        cmds.warning(f"XML 내보내기 오류: {str(e)}")
        return None


def quick_export_json(mesh_name=None):
    """빠른 JSON 내보내기"""
    try:
        if not mesh_name:
            mesh_name, _ = SkinWeightIOCore.get_selected_mesh()
        return SkinWeightIOCore.export_weights_to_json(mesh_name)
    except Exception as e:
        cmds.warning(f"JSON 내보내기 오류: {str(e)}")
        return None


def quick_import_xml(xml_path=None, mesh_name=None, use_batch=False, batch_size=5000):
    """빠른 XML 불러오기 (고성능 옵션 포함)"""
    try:
        if use_batch:
            return SkinWeightIOCore.batch_import_weights_from_xml(xml_path, mesh_name, None, batch_size)
        else:
            return SkinWeightIOCore.import_weights_from_xml(xml_path, mesh_name)
    except Exception as e:
        cmds.warning(f"XML 불러오기 오류: {str(e)}")
        return False


def quick_import_json(json_path=None, mesh_name=None):
    """빠른 JSON 불러오기 (고성능 최적화)"""
    try:
        return SkinWeightIOCore.import_weights_from_json(json_path, mesh_name)
    except Exception as e:
        cmds.warning(f"JSON 불러오기 오류: {str(e)}")
        return False


def quick_batch_import_xml(xml_path=None, mesh_name=None, batch_size=5000):
    """빠른 배치 XML 불러오기"""
    try:
        return SkinWeightIOCore.batch_import_weights_from_xml(xml_path, mesh_name, None, batch_size)
    except Exception as e:
        cmds.warning(f"배치 XML 불러오기 오류: {str(e)}")
        return False


if __name__ == "__main__":
    show_ui()
