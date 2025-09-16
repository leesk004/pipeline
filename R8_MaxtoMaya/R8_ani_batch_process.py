'''
Maya Standalone Animation Batch Process Script
이 스크립트는 Maya Standalone을 사용하여 애니메이션 파일들을 배치 처리합니다.
'''
import os
import time
import subprocess
import tempfile
from maya import cmds, mel
import maya.OpenMayaUI as omui

# Maya 버전에 따른 PySide 모듈 임포트 개선
maya_version = mel.eval('getApplicationVersionAsFloat()')
try:
    if maya_version >= 2025.0:
        from PySide6 import QtWidgets, QtCore
        from shiboken6 import wrapInstance
    else:
        from PySide2 import QtWidgets, QtCore
        from shiboken2 import wrapInstance
except ImportError as e:
    print(f"PySide 모듈 임포트 오류: {e}")
    try:
        from PySide2 import QtWidgets, QtCore
        from shiboken2 import wrapInstance
    except ImportError:
        try:
            from PySide6 import QtWidgets, QtCore
            from shiboken6 import wrapInstance
        except ImportError:
            raise ImportError("PySide2 또는 PySide6를 찾을 수 없습니다.")

# Maya 실행 파일 경로 자동 감지
def get_maya_exe_path():
    """Maya 실행 파일 경로를 자동으로 감지합니다."""
    # 환경 변수에서 Maya 경로 확인
    maya_location = os.environ.get('MAYA_LOCATION')
    if maya_location:
        maya_exe = os.path.join(maya_location, 'bin', 'maya.exe')
        if os.path.exists(maya_exe):
            return maya_exe
    
    # 일반적인 Maya 설치 경로들 확인
    common_paths = [
        r'C:\Program Files\Autodesk\Maya2024\bin\maya.exe',
        r'C:\Program Files\Autodesk\Maya2023\bin\maya.exe',
        r'C:\Program Files\Autodesk\Maya2022\bin\maya.exe',
        r'C:\Program Files\Autodesk\Maya2025\bin\maya.exe',
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # Maya가 설치된 모든 버전 찾기
    autodesk_path = r'C:\Program Files\Autodesk'
    if os.path.exists(autodesk_path):
        for folder in os.listdir(autodesk_path):
            if folder.startswith('Maya'):
                maya_exe = os.path.join(autodesk_path, folder, 'bin', 'maya.exe')
                if os.path.exists(maya_exe):
                    return maya_exe
    
    # 기본값 반환
    return r'C:\Program Files\Autodesk\Maya2025\bin\maya.exe'

def get_mayapy_path(maya_exe):
    """Maya 실행 파일 경로로부터 mayapy 경로를 구합니다."""
    maya_dir = os.path.dirname(maya_exe)
    mayapy_path = os.path.join(maya_dir, 'mayapy.exe')
    if os.path.exists(mayapy_path):
        return mayapy_path
    else:
        # Maya 2025 이상에서는 Python이 별도 폴더에 있을 수 있음
        python_dir = os.path.join(os.path.dirname(maya_dir), 'Python', 'Scripts')
        mayapy_path = os.path.join(python_dir, 'mayapy.exe')
        if os.path.exists(mayapy_path):
            return mayapy_path
    return None

# Maya 실행 파일 경로
MAYA_EXE = get_maya_exe_path()

def get_maya_main_window():
    """Maya 메인 윈도우를 반환합니다."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

def time_change_set():
    """시간 단위를 60fps로 설정합니다."""
    cmds.currentUnit(time='ntscf')

class BatchProcessManager:
    """배치 프로세스 관리 클래스"""
    
    def __init__(self):
        self.current_export_info = None
        self.check_export_timer = None
        self.file_queue = []
        self.current_index = 0
        self.progress_callback = None
        self.file_result_callback = None
        self.current_process = None  # 현재 실행 중인 프로세스
        self.is_cancelled = False    # 취소 플래그
        
    def cancel_batch_process(self):
        """배치 프로세스를 취소합니다."""
        print("배치 프로세스 취소 요청...")
        self.is_cancelled = True
        
        # 타이머 중지
        if self.check_export_timer:
            self.check_export_timer.stop()
            self.check_export_timer = None
            print("프로세스 모니터링 타이머 중지됨")
        
        # 현재 실행 중인 프로세스 종료
        if self.current_process:
            try:
                # Windows에서 프로세스 트리 전체 종료
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.current_process.pid)], 
                             capture_output=True, text=True, timeout=10)
                print(f"프로세스 (PID: {self.current_process.pid}) 강제 종료됨")
                self.current_process = None
            except Exception as e:
                print(f"프로세스 종료 중 오류: {e}")
        
        # 임시 파일 정리
        if self.current_export_info:
            try:
                temp_script = self.current_export_info.get('temp_script')
                status_file = self.current_export_info.get('status_file')
                
                if temp_script and os.path.exists(temp_script):
                    os.remove(temp_script)
                    print(f"임시 스크립트 파일 삭제: {temp_script}")
                
                if status_file and os.path.exists(status_file):
                    os.remove(status_file)
                    print(f"상태 파일 삭제: {status_file}")
                    
            except Exception as e:
                print(f"임시 파일 정리 중 오류: {e}")
        
        # 상태 초기화
        self.current_export_info = None
        self.file_queue = []
        self.current_index = 0
        
        # 취소 콜백 호출
        if self.progress_callback:
            self.progress_callback("배치 처리가 취소되었습니다.", 0, 0)
        
        print("배치 프로세스 취소 완료")
        
    def start_batch_process(self, rig_file, fbx_files, fbx_folder, save_folder, frontX_v, progress_callback=None, file_result_callback=None):
        """배치 프로세스를 시작합니다."""
        # 취소 플래그 초기화
        self.is_cancelled = False
        
        # 입력 값 검증
        if not os.path.exists(rig_file):
            error_msg = f"리그 파일이 존재하지 않습니다: {rig_file}"
            print(error_msg)
            if progress_callback:
                progress_callback(error_msg, 0, 0)
            return False
            
        if not os.path.exists(fbx_folder):
            error_msg = f"FBX 폴더가 존재하지 않습니다: {fbx_folder}"
            print(error_msg)
            if progress_callback:
                progress_callback(error_msg, 0, 0)
            return False
        
        # mayapy 경로 확인
        mayapy_path = get_mayapy_path(MAYA_EXE)
        if not mayapy_path or not os.path.exists(mayapy_path):
            error_msg = f"mayapy.exe를 찾을 수 없습니다. Maya가 올바르게 설치되어 있는지 확인하세요."
            print(error_msg)
            if progress_callback:
                progress_callback(error_msg, 0, 0)
            return False
        
        self.file_queue = fbx_files
        self.current_index = 0
        self.rig_file = rig_file
        self.fbx_folder = fbx_folder
        self.save_folder = save_folder
        self.frontX_v = frontX_v
        self.progress_callback = progress_callback
        self.file_result_callback = file_result_callback
        
        print(f"배치 프로세스 시작: {len(fbx_files)}개 파일")
        print(f"리그 파일: {rig_file}")
        print(f"FBX 폴더: {fbx_folder}")
        print(f"저장 폴더: {save_folder}")
        print(f"FrontX 모드: {frontX_v}")
        print(f"mayapy 경로: {mayapy_path}")
        print("=" * 50)
        
        # 첫 번째 파일 처리 시작
        self.process_next_file()
        return True
    
    def process_next_file(self):
        """다음 파일을 처리합니다."""
        # 취소 상태 확인
        if self.is_cancelled:
            print("배치 처리가 취소되어 중단됩니다.")
            return
            
        if self.current_index >= len(self.file_queue):
            # 모든 파일 처리 완료
            print("=" * 50)
            print("모든 파일 처리 완료!")
            if self.progress_callback:
                self.progress_callback("모든 파일 처리 완료", self.current_index, len(self.file_queue))
            return
        
        current_file = self.file_queue[self.current_index]
        print(f"\n[{self.current_index + 1}/{len(self.file_queue)}] 처리 시작: {current_file}")
        
        if self.progress_callback:
            self.progress_callback(f"처리 중: {current_file}", self.current_index, len(self.file_queue))
        
        # 백그라운드 프로세스 시작
        self.background_process(current_file)
    
    def background_process(self, fbx_file):
        """Maya standalone을 사용하여 배치 처리"""
        # 취소 상태 확인
        if self.is_cancelled:
            print("배치 처리가 취소되어 백그라운드 처리를 중단합니다.")
            return False
            
        try:
            # FBX 파일 존재 확인
            fbx_path = os.path.join(self.fbx_folder, fbx_file)
            if not os.path.exists(fbx_path):
                error_msg = f"FBX 파일이 존재하지 않습니다: {fbx_path}"
                print(error_msg)
                if self.file_result_callback:
                    self.file_result_callback(fbx_file, False)
                self.current_index += 1
                QtCore.QTimer.singleShot(500, self.process_next_file)
                return False
            
            # 모든 경로 정규화
            maya_exe = MAYA_EXE.replace('\\', '/')
            rig_file = self.rig_file.replace('\\', '/')
            fbx_path = fbx_path.replace('\\', '/')
            save_folder = self.save_folder.replace('\\', '/')
            
            # 처리 상태 추적을 위한 상태 파일 경로
            timestamp = int(time.time())
            basename = os.path.basename(fbx_file).replace('.', '_')
            status_file = os.path.join(tempfile.gettempdir(), f'maya_batch_status_{basename}_{timestamp}.txt')
            
            # 저장 폴더 생성
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)
            
            # 출력 파일 경로
            output_file = os.path.join(save_folder, f"{os.path.splitext(fbx_file)[0]}.ma")
            
            print(f"백그라운드 처리 시작:")
            print(f"  - FBX 파일: {fbx_file}")
            print(f"  - 리그 파일: {rig_file}")
            print(f"  - 출력 파일: {output_file}")
            
            # 취소 상태 다시 확인
            if self.is_cancelled:
                print("배치 처리가 취소되어 프로세스 시작을 중단합니다.")
                return False
            
            # 각 파일마다 고유한 임시 스크립트 파일 생성
            temp_script = os.path.join(tempfile.gettempdir(), f'maya_batch_{basename}_{timestamp}.py')
            
            with open(temp_script, 'w', encoding='utf-8') as f:
                f.write(f'''
import maya.standalone
maya.standalone.initialize(name='python')

from maya import cmds, mel
import os
import sys
import time

def main():
    try:
        def joint_segment_scale(root_joint, val=1):
            try:    
                all_joints = cmds.ls(root_joint, dag=True, type='joint')
                for jnt in all_joints:
                    cmds.setAttr(f'{{jnt}}.segmentScaleCompensate', val)
            except Exception as e:
                print(f"조인트 세그먼트 스케일 설정 중 오류: {{e}}")
                return False
            return True
        
        def get_colon_prefixes():
            all_objects = cmds.ls()
            prefixes = set()
            for obj in all_objects:
                name_parts = obj.split(':')
                if len(name_parts) > 1:
                    prefixes.add(name_parts[0])
            return prefixes
        
        def skeleton_bindpose(selectObjects, prefix):
            print(f"skeleton_bindpose 실행 - 대상 오브젝트: {{len(selectObjects)}}개")
            cmds.playbackOptions(min=-10)
            cmds.currentTime(-10)        
            for obj in selectObjects:
                if cmds.objExists(f'{{prefix}}:{{obj}}'):
                    if obj == 'Root': 
                        continue
                    tg_obj = f'{{prefix}}:{{obj}}'
                    for ax in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                        try:
                            tv = cmds.getAttr(f'{{obj}}.{{ax}}')
                            cmds.setAttr(f'{{tg_obj}}.{{ax}}', tv)
                            cmds.setKeyframe(f'{{tg_obj}}.{{ax}}')
                        except Exception as e:
                            print(f"속성 설정 실패: {{obj}}.{{ax}} - {{e}}")
                            continue
        
        def joint_Exists(joints, pre_):
            joint_list = []
            if not joints:
                return joint_list
                
            for jnt in joints:
                if cmds.objExists(f'{{pre_}}:{{jnt}}'):
                    joint_list.append(jnt)
            return joint_list
        
        def ik_fk_control_blend(attrName='FKIKBlend'):
            """
            마야 씬에서 FKIKBlend 속성을 가진 컨트롤러들을 찾습니다.
            Args:
                attrName (str): 찾을 속성 이름 (기본값: 'FKIKBlend')
                
            Returns:
                list: FKIKBlend 속성을 가진 컨트롤러 리스트
            """
            controllers_with_fkik = []
            
            # 씬의 모든 객체를 검색
            all_objects = cmds.ls(type='transform')
            
            for obj in all_objects:
                # 객체에 지정된 속성이 존재하는지 확인
                if cmds.attributeQuery(attrName, node=obj, exists=True):
                    controllers_with_fkik.append(obj)
            
            if controllers_with_fkik:
                print(f"{{attrName}} 속성을 가진 컨트롤러들: {{controllers_with_fkik}}")
            else:
                print(f"{{attrName}} 속성을 가진 컨트롤러를 찾을 수 없습니다.")
            
            return controllers_with_fkik
        
        def bake_animation(controls, startFrame, endFrame):
            # 프레임 값 안전 처리
            try:
                startFrame = int(startFrame) if startFrame is not None else 0
                endFrame = int(endFrame) if endFrame is not None else 100
                
                if not controls:
                    print("베이킹할 컨트롤이 없습니다.")
                    return
                    
                print(f"베이킹 실행: 컨트롤 {{len(controls)}}개, 프레임 {{startFrame}}-{{endFrame}}")
                
                cmds.bakeResults(controls, simulation=True, t=(startFrame, endFrame),
                               sampleBy=1, oversamplingRate=1, disableImplicitControl=True,
                               preserveOutsideKeys=True, sparseAnimCurveBake=False, 
                               removeBakedAttributeFromLayer=False,
                               removeBakedAnimFromLayer=False, bakeOnOverrideLayer=False, 
                               minimizeRotation=True, controlPoints=False, shape=True)
                
                print("베이킹 완료")
                
            except Exception as e:
                print(f"베이킹 중 오류 발생: {{e}}")
                raise
        
        def main_controller_move(prefix):
            """
            루트 조인트의 위치를 확인 MainExtra2 값을 이동합니다.
            
            Args:
                prefix (str): 네임스페이스 프리픽스
            """
            if cmds.objExists(f'{{prefix}}:Root'):
                root_transX = cmds.getAttr(f'{{prefix}}:Root.tx')
                root_transY = cmds.getAttr(f'{{prefix}}:Root.ty')
                root_transZ = cmds.getAttr(f'{{prefix}}:Root.tz')
                if root_transX or root_transY or root_transZ:
                    if cmds.objExists('MainExtra2'):
                        cmds.move(root_transX, root_transY, root_transZ, 'MainExtra2')
        
        def skeleton_control_match(frontAxis='frontX'):
            nonlocal contList
            
            # 현재 타임라인의 시작 프레임과 마지막 프레임 가져오기
            current_start_frame = cmds.playbackOptions(query=True, minTime=True)
            current_end_frame = cmds.playbackOptions(query=True, maxTime=True)
            
            try:
                # 상수 정의
                SKEL_SET = 'Skeleton_Set'
                BAKE_CTRL_SET = 'Bake_Control_Set'
                
                # IK/FK 컨트롤러 처리
                ik_fk_contols = ik_fk_control_blend()
                if ik_fk_contols:
                    print(f"IK/FK 컨트롤러들: {{ik_fk_contols}}")
                    for cont in ik_fk_contols:
                        try:
                            cmds.setAttr(cont + '.FKIKBlend', 0)
                            print(f"{{cont}}.FKIKBlend를 0으로 설정")
                        except Exception as e:
                            print(f"{{cont}}.FKIKBlend 설정 실패: {{e}}")
                else:
                    print("IK/FK 컨트롤러를 찾을 수 없습니다.")
                
                contList = []  # 함수 시작 시 초기화
                
                # 모든 콜론 프리픽스를 가져옵니다.
                prefixes = list(get_colon_prefixes())
                if not prefixes:
                    print("오류: 네임스페이스를 찾을 수 없습니다.")
                    return False
                    
                # FBX 파일의 네임스페이스 찾기 (file_name과 일치하는 것)
                target_prefix = None
                for prefix in prefixes:
                    if prefix == file_name:
                        target_prefix = prefix
                        break
                
                if not target_prefix:
                    print(f"오류: FBX 네임스페이스 '{{file_name}}'를 찾을 수 없습니다.")
                    print(f"사용 가능한 네임스페이스: {{prefixes}}")
                    # 첫 번째 네임스페이스 사용 (fallback)
                    target_prefix = prefixes[0]
                    print(f"첫 번째 네임스페이스를 사용합니다: {{target_prefix}}")
                    
                print(f"사용할 네임스페이스: {{target_prefix}}")
                
                # main_controller_move 실행
                main_controller_move(target_prefix)
                
                try:
                    set_node = SKEL_SET
                    if not cmds.objExists(set_node):
                        print(f"경고: {{set_node}} 세트가 존재하지 않습니다.")
                        return False
                        
                    members = cmds.sets(set_node, q=True) 
                    if not members:
                        print(f"경고: {{set_node}} 세트가 비어있습니다.")
                        return False
                        
                    print(f"Skeleton_Set 멤버: {{members}}")
                    selectObjects = joint_Exists(members, target_prefix)
                    print(f"존재하는 조인트: {{selectObjects}}")
                    
                    if not selectObjects:
                        print("오류: 매칭되는 조인트가 없습니다.")
                        return False
                    
                    cmds.select(clear=True)
                    
                    # root_grp 생성 및 설정
                    if not cmds.objExists('root_grp'):
                        cmds.group(em=True, name='root_grp')
                        
                    root_joint = f'{{target_prefix}}:Root'
                    if cmds.objExists(root_joint):
                        if not cmds.listRelatives(root_joint, p=True):
                            cmds.parent(root_joint, 'root_grp')
                            print(f"{{root_joint}}를 root_grp에 부모 설정")
                    else:
                        print(f"경고: {{target_prefix}}:Root 객체가 존재하지 않습니다.")
                    
                    # 방향 설정
                    if frontAxis == 'frontX':
                        if cmds.objExists('MainExtra2'):
                            cmds.setAttr('MainExtra2.rotateY', 90)
                        cmds.setAttr('root_grp.rotateY', 0)
                        print("FrontX 모드로 설정")
                    else:
                        if cmds.objExists('MainExtra2'):
                            cmds.setAttr('MainExtra2.rotateY', 0)
                        cmds.setAttr('root_grp.rotateY', -90)   
                        print("FrontZ 모드로 설정")
                         
                    # skeleton_bindpose 실행
                    skeleton_bindpose(selectObjects, target_prefix)  
                    if cmds.objExists(f'{{target_prefix}}:Root'):
                        joint_segment_scale(f'{{target_prefix}}:Root', val=1)    
                
                except Exception as e:
                    print(f'skeleton_control_match 오류: {{e}}')
                    return False

                # 컨트롤 매칭 부분
                contList = []
                aniJointList = []

                print("컨트롤 매칭 시작...")
                for obj in selectObjects:
                    try:
                        if cmds.objExists(obj):
                            parent_constraints = cmds.listConnections(obj, type='parentConstraint')
                            if not parent_constraints:
                                continue
                            
                            target_loc = cmds.parentConstraint(parent_constraints[0], query=True, targetList=True)
                            
                            if target_loc and len(target_loc) > 0:
                                # rotate 속성 연결 확인
                                try:
                                    rotate_connections = cmds.listConnections(target_loc[0] + '.rotate')
                                    rotate_locator = None  # 초기화
                                    
                                    if rotate_connections:
                                        for cont in rotate_connections:
                                            cont_shape = cmds.listRelatives(cont, children=True)
                                            if cont_shape:
                                                # 수정: 리스트가 반환될 수 있으므로 첫 번째 요소 확인
                                                if isinstance(cont_shape, list) and len(cont_shape) > 0:
                                                    if cmds.nodeType(cont_shape[0]) == 'locator':
                                                        rotate_locator = cont
                                                        break
                                                elif cmds.nodeType(cont_shape) == 'locator':
                                                    rotate_locator = cont
                                                    break
                                    
                                        if rotate_locator:
                                            aniJoint = f'{{target_prefix}}:{{obj}}'
                                            if cmds.objExists(aniJoint):
                                                aniJointList.append(aniJoint)    
                                            locCon = rotate_locator  # 수정: rotate_locator 사용
                                            parent_grp = cmds.listRelatives(f'{{locCon}}_grp', parent=True)
                                            if parent_grp:
                                                contList.append(parent_grp[0])
                                except Exception as e:
                                    print(f"객체 {{obj}}의 rotate 연결 확인 중 오류: {{e}}")
                                    continue
                    except Exception as e:
                        print(f"오브젝트 {{obj}} 처리 중 오류: {{e}}")
                        continue
                             
                print(f"찾은 컨트롤: {{len(contList)}}개")
                print(f"애니메이션 조인트: {{len(aniJointList)}}개")
                
                if not contList:
                    print("경고: 컨트롤을 찾을 수 없습니다.")
                    return False
                    
                # 컨트롤 세트 생성
                set_name = 'Bake_Control_Set'
                if cmds.objExists(set_name):
                    cmds.delete(set_name)
                cmds.sets(contList, name=set_name)  
                cmds.select(clear=True)  
                
                # 컨트롤과 조인트 연결
                for j, c in zip(aniJointList, contList):
                    print(f"처리 중: {{j}} -> {{c}}")
                    try:
                        if not cmds.objExists(c):
                            print(f"경고: 컨트롤러 {{c}}가 존재하지 않습니다. 건너뜁니다.")
                            continue
                        
                        # 기존 로케이터와 그룹이 있는지 확인하고 삭제
                        ctl_loc_name = f'{{c}}_ctl'
                        ctl_grp_name = f'{{ctl_loc_name}}_grp'
                        
                        # 기존 컨스트레인 조인트 삭제
                        if cmds.objExists('RootX_M'):
                            existing_constraints = cmds.listConnections('RootX_M', type='constraint', source=True)
                            if existing_constraints:
                                # 조인트 타입만 필터링
                                joint_constraints = []
                                for constraint in existing_constraints:
                                    if cmds.objExists(constraint):
                                        # 컨스트레인의 타겟을 확인하여 조인트인지 검사
                                        targets = cmds.listConnections(constraint, source=True, destination=False)
                                        if targets:
                                            for target in targets:
                                                if cmds.nodeType(target) == 'joint':
                                                    joint_constraints.append(constraint)
                                                    break
                                existing_constraints = joint_constraints
                                # 컨스트레인 삭제
                                if existing_constraints:
                                    for constraint in existing_constraints:
                                        try:
                                            print(f'기존 컨스트레인 {{constraint}} 확인됨 (삭제하지 않음)')
                                            # cmds.delete(constraint)  # 실제로는 삭제하지 않음
                                        except Exception as e:
                                            print(f"기존 컨스트레인 {{constraint}} 처리 중 오류: {{e}}")
                        
                        # 기존 로케이터 그룹 삭제 (조인트의 자식으로 있는 경우)
                        joint_children = cmds.listRelatives(j, children=True, type='transform')
                        if joint_children:
                            for child in joint_children:
                                if child.endswith('_ctl_grp'):
                                    try:
                                        cmds.delete(child)
                                        print(f"기존 로케이터 그룹 {{child}} 삭제됨")
                                    except Exception as e:
                                        print(f"기존 로케이터 그룹 {{child}} 삭제 중 오류: {{e}}")
                        
                        # 씬에서 기존 로케이터와 그룹 삭제
                        if cmds.objExists(ctl_grp_name):
                            try:
                                cmds.delete(ctl_grp_name)
                                print(f"기존 로케이터 그룹 {{ctl_grp_name}} 삭제됨")
                            except Exception as e:
                                print(f"기존 로케이터 그룹 {{ctl_grp_name}} 삭제 중 오류: {{e}}")
                        
                        if cmds.objExists(ctl_loc_name):
                            try:
                                cmds.delete(ctl_loc_name)
                                print(f"기존 로케이터 {{ctl_loc_name}} 삭제됨")
                            except Exception as e:
                                print(f"기존 로케이터 {{ctl_loc_name}} 삭제 중 오류: {{e}}")
                            
                        c_ro = cmds.getAttr(f'{{c}}.rotateOrder')
                        ctlLoc = cmds.spaceLocator(p=(0, 0, 0), name=f'{{c}}_ctl')
                        cmds.setAttr(f'{{ctlLoc[0]}}.rotateOrder', c_ro)
                        ctlLocGrp = cmds.group(em=True, name=f'{{ctlLoc[0]}}_grp')
                        cmds.parent(ctlLoc, ctlLocGrp)
                        cmds.delete(cmds.pointConstraint(c, ctlLocGrp, mo=False))
                        cmds.delete(cmds.orientConstraint(c, ctlLocGrp, mo=False))
                        cmds.parent(ctlLocGrp, j)
                        cmds.select(clear=True)
                        
                        # 속성 존재 여부 확인 후 컨스트레인 생성
                        try:
                            if cmds.attributeQuery('tx', node=c, exists=True) and cmds.getAttr(c + '.tx', keyable=True):
                                cmds.parentConstraint(ctlLoc, c, mo=True)
                                print(f"Parent constraint 생성됨: {{ctlLoc}} -> {{c}}")
                        except Exception as e:
                            print(f"Parent constraint 생성 실패: {{e}}")
                            
                        try:          
                            if cmds.attributeQuery('sx', node=c, exists=True) and cmds.getAttr(c + '.sx', keyable=True):
                                cmds.scaleConstraint(ctlLoc, c, mo=True)
                                print(f"Scale constraint 생성됨: {{ctlLoc}} -> {{c}}")
                        except Exception as e:
                            print(f"Scale constraint 생성 실패: {{e}}")
                            
                    except Exception as e:
                        print(f"컨트롤러 {{c}} 처리 중 오류 발생: {{str(e)}}")
                        continue
                
                # 현재 타임라인 프레임 범위를 다시 적용
                cmds.playbackOptions(minTime=current_start_frame, maxTime=current_end_frame)
                
                return True
            
            except Exception as e:
                print(f"skeleton_control_match 실행 중 오류 발생: {{e}}")
                # 현재 타임라인 프레임 범위를 다시 적용 (finally 블록 대신)
                try:
                    cmds.playbackOptions(minTime=current_start_frame, maxTime=current_end_frame)
                except:
                    pass
                return False
        
        def control_bake():
            nonlocal contList
            print("control_bake 실행...")
            
            try:
                # Bake_Control_Set에서 컨트롤 리스트 가져오기
                if cmds.objExists('Bake_Control_Set'):
                    bake_controls = cmds.sets('Bake_Control_Set', q=True)
                    if bake_controls:
                        contList = bake_controls
                        print(f"Bake_Control_Set에서 {{len(contList)}}개 컨트롤을 가져왔습니다.")
                    else:
                        print("'Bake_Control_Set' 세트가 비어있습니다.")
                        return False
                else:
                    print("'Bake_Control_Set' 세트가 존재하지 않습니다.")
                    return False
                
                if not contList:
                    print("경고: 베이킹할 컨트롤이 없습니다.")
                    return False
                    
                # 타임라인 범위 가져오기
                startFrame = cmds.playbackOptions(q=True, minTime=True)
                endFrame = cmds.playbackOptions(q=True, maxTime=True)
                
                print(f"컨트롤 베이킹 시작: {{len(contList)}}개 컨트롤")
                print(f"프레임 범위: {{startFrame}} - {{endFrame}}")
                
                bake_animation(contList, startFrame, endFrame)
                return True
                
            except Exception as e:
                print(f"컨트롤 베이킹 중 오류 발생: {{e}}")
                return False
        
        def remove_references_direct():
            """직접 구현된 레퍼런스 제거 함수"""
            print("\\n=== 직접 레퍼런스 제거 실행 ===")
            try:
                # 모든 레퍼런스 노드 찾기
                reference_nodes = cmds.ls(type='reference')
                
                if not reference_nodes:
                    print("씬에 레퍼런스 노드가 없습니다.")
                    return True
                
                removed_count = 0
                
                for ref_node in reference_nodes:
                    try:
                        # 'sharedReferenceNode'는 기본 시스템 레퍼런스이므로 제외
                        if ref_node == 'sharedReferenceNode':
                            continue
                        
                        # 레퍼런스가 로드되어 있는지 확인
                        if cmds.referenceQuery(ref_node, isLoaded=True):
                            # 레퍼런스 파일 경로 가져오기
                            ref_file = cmds.referenceQuery(ref_node, filename=True)
                            print(f"레퍼런스 제거 중: {{os.path.basename(ref_file)}}")
                            
                            # 레퍼런스 제거
                            cmds.file(ref_file, removeReference=True)
                            removed_count += 1
                            print(f"성공적으로 제거됨: {{os.path.basename(ref_file)}}")
                            
                        else:
                            print(f"레퍼런스가 로드되지 않음: {{ref_node}}")
                            
                    except Exception as e:
                        print(f"레퍼런스 제거 실패 - {{ref_node}}: {{str(e)}}")
                        continue
                
                print(f"총 제거된 레퍼런스: {{removed_count}}개")
                
                # 씬 정리
                try:
                    print("사용하지 않는 노드들 정리 중...")
                    
                    # fosterParent 노드들 삭제
                    foster_parents = cmds.ls(type="fosterParent")
                    if foster_parents:
                        for foster_parent in foster_parents:
                            try:
                                if cmds.objExists(foster_parent):
                                    cmds.delete(foster_parent)
                                    print(f"fosterParent 노드 삭제됨: {{foster_parent}}")
                            except Exception as e:
                                print(f"fosterParent 노드 삭제 실패 - {{foster_parent}}: {{str(e)}}")                      
                    # root_grp 노드 삭제
                    if cmds.objExists("root_grp"):
                        try:
                            cmds.delete("root_grp")
                            print("root_grp 노드 삭제됨")
                        except Exception as e:
                            print(f"root_grp 노드 삭제 실패: {{str(e)}}")
                            
                    if cmds.objExists("Root"):
                        try:
                            cmds.delete("Root")
                            print("Root 조인트 삭제됨")
                        except Exception as e:
                            print(f"Root 조인트 삭제 실패: {{str(e)}}")
                
                    print("사용하지 않는 노드들 정리 완료")
                    
                except Exception as e:
                    print(f"사용하지 않는 노드들 정리 중 오류 발생: {{str(e)}}")
                            
                
                return True
                
            except Exception as e:
                print(f"직접 레퍼런스 제거 중 오류: {{e}}")
                return False
        
        # 시간 단위를 60fps로 설정
        cmds.currentUnit(time='ntscf')
        
        # 1. 새로운 씬으로 시작 (기본 씬 생성)
        print("새로운 씬 생성...")
        cmds.file(new=True, force=True)
        
        # 2. 리그 파일 열기
        rig_file = r"{rig_file}"
        print(f"리그 파일 열기: {{rig_file}}")
        cmds.file(rig_file, open=True, force=True)
        
        # 3. 단일 FBX 파일을 레퍼런스로 불러오기
        fbx_file = r"{fbx_path}"
        file_name = os.path.basename(fbx_file).split('.')[0]
        print(f"FBX 레퍼런스 불러오기: {{fbx_file}}")
        print(f"네임스페이스: {{file_name}}")
        
        # FBX 플러그인 로드
        if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
            cmds.loadPlugin('fbxmaya')
        
        # FBX 파일 레퍼런스 로드
        cmds.file(fbx_file, reference=True, namespace=file_name)
        
        # 4. R8_ani_skeleton_match 모듈의 함수들을 직접 구현
        
        # 상수 정의
        SKEL_SET = 'Skeleton_Set'
        BAKE_CTRL_SET = 'Bake_Control_Set'
        contList = []
        
        # 5. 스켈레톤 매칭 및 베이킹 실행
        print("\\n=== 스켈레톤 매칭 시작 ===")
        frontAxis = 'frontX' if {self.frontX_v} else 'frontZ'
        
        if not skeleton_control_match(frontAxis):
            print("스켈레톤 매칭 실패")
            raise Exception("스켈레톤 매칭 실패")
        
        print("\\n=== 컨트롤 베이킹 시작 ===")
        if not control_bake():
            print("컨트롤 베이킹 실패")
            raise Exception("컨트롤 베이킹 실패")
        
        # 6. 레퍼런스 파일 제거 (Maya 파일 저장 전에 실행)
        print("\\n=== 레퍼런스 파일 제거 (저장 전) ===")  
        if not remove_references_direct():
            print("레퍼런스 파일 제거 실패")
            raise Exception("레퍼런스 파일 제거 실패")
        
        # 7. 지정 폴더에 Maya 파일 저장
        output_file = r"{output_file}"
        print(f"\\n=== 파일 저장: {{output_file}} ===")
          
        # 결과 확인 및 상태 파일 작성
        status_file = r"{status_file}"
        
        # 출력 디렉토리 생성
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Maya 파일 저장 (기존 파일이 있으면 덮어쓰기)
        cmds.file(rename=output_file)
        cmds.file(save=True, type='mayaAscii', force=True)
        print(f"파일 저장 완료: {{os.path.basename(output_file)}}")
                
        # 파일 생성 확인
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"성공: Maya 파일 생성됨 ({{file_size}} 바이트)")
            with open(status_file, 'w') as sf:
                sf.write(f"SUCCESS\\n{{output_file}}\\n{{file_size}}")
            return True
        else:
            print(f"실패: Maya 파일이 생성되지 않음")
            with open(status_file, 'w') as sf:
                sf.write(f"FAIL\\n{{output_file}}\\n0")
            return False
            
    except Exception as e:
        import traceback
        print(f"오류 발생: {{e}}")
        print(traceback.format_exc())
        # 상태 파일에 오류 정보 기록
        with open(r"{status_file}", 'w') as sf:
            sf.write(f"ERROR\\n{{e}}")
        return False

success = main()
print(f"처리 결과: {{success}}")
''')
            
            # mayapy를 사용한 독립 실행 명령
            mayapy_path = get_mayapy_path(maya_exe)
            if not mayapy_path:
                error_msg = "mayapy.exe를 찾을 수 없습니다."
                print(error_msg)
                if self.file_result_callback:
                    self.file_result_callback(fbx_file, False)
                self.current_index += 1
                QtCore.QTimer.singleShot(500, self.process_next_file)
                return False
                
            command = f'"{mayapy_path}" "{temp_script}"'
            
            print(f"실행 명령: {command}")
            
            # 취소 상태 확인 - 프로세스 시작 직전
            if self.is_cancelled:
                print("배치 처리가 취소되어 프로세스 실행을 중단합니다.")
                # 임시 스크립트 파일 삭제
                try:
                    if os.path.exists(temp_script):
                        os.remove(temp_script)
                except Exception as e:
                    print(f"임시 스크립트 파일 삭제 중 오류: {e}")
                return False
            
            # 상태 추적을 위한 정보 저장
            self.current_export_info = {
                'fbx_file': fbx_file,
                'output_file': output_file,
                'status_file': status_file,
                'temp_script': temp_script,
                'start_time': time.time()
            }
            
            # subprocess 실행
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            try:
                process = subprocess.Popen(command, shell=True, startupinfo=startupinfo)
                print(f"프로세스 시작됨 (PID: {process.pid})")
            except Exception as e:
                print(f"프로세스 시작 실패: {e}")
                # 임시 파일 정리
                self._cleanup_temp_files(temp_script, status_file)
                if self.file_result_callback:
                    self.file_result_callback(fbx_file, False)
                self.current_index += 1
                QtCore.QTimer.singleShot(500, self.process_next_file)
                return False
            
            # 타이머를 설정하여 주기적으로 처리 상태 확인
            if hasattr(self, 'check_export_timer') and self.check_export_timer:
                self.check_export_timer.stop()
                
            self.check_export_timer = QtCore.QTimer()
            self.check_export_timer.timeout.connect(self.check_process_status)
            self.check_export_timer.start(1000)  # 1초마다 확인
            
            self.current_process = process
            
            return True
        
        except Exception as e:
            print(f"백그라운드 처리 오류: {e}")
            # 취소 상태가 아닌 경우에만 다음 파일 처리
            if not self.is_cancelled:
                if self.file_result_callback:
                    self.file_result_callback(fbx_file, False)
                self.current_index += 1
                QtCore.QTimer.singleShot(500, self.process_next_file)
            return False
    
    def _cleanup_temp_files(self, temp_script, status_file):
        """임시 파일들을 정리합니다."""
        try:
            if temp_script and os.path.exists(temp_script):
                os.remove(temp_script)
                print(f"임시 스크립트 파일 삭제: {temp_script}")
        except Exception as e:
            print(f"임시 스크립트 파일 삭제 중 오류: {e}")
        
        try:
            if status_file and os.path.exists(status_file):
                os.remove(status_file)
                print(f"상태 파일 삭제: {status_file}")
        except Exception as e:
            print(f"상태 파일 삭제 중 오류: {e}")
    
    def check_process_status(self):
        """배치 처리 상태를 주기적으로 확인"""
        # 취소 상태 확인
        if self.is_cancelled:
            print("배치 처리가 취소되어 상태 확인을 중단합니다.")
            if self.check_export_timer:
                self.check_export_timer.stop()
            return
            
        if not hasattr(self, 'current_export_info') or not self.current_export_info:
            if self.check_export_timer:
                self.check_export_timer.stop()
            return
        
        output_file = self.current_export_info['output_file']
        status_file = self.current_export_info['status_file']
        current_fbx_file = self.current_export_info['fbx_file']
        temp_script = self.current_export_info['temp_script']
        
        # 실행 시간이 너무 오래 걸리면 타임아웃
        elapsed_time = time.time() - self.current_export_info['start_time']
        if elapsed_time > 300:  # 5분 타임아웃
            print(f"[타임아웃] {current_fbx_file} - 처리 시간 초과")
            if self.check_export_timer:
                self.check_export_timer.stop()
            
            # 현재 프로세스 종료
            self._terminate_current_process()
            
            # 실패 콜백 호출
            if self.file_result_callback:
                self.file_result_callback(current_fbx_file, False)
            
            # 임시 파일 정리
            self._cleanup_temp_files(temp_script, status_file)
            
            self.current_index += 1
            QtCore.QTimer.singleShot(500, self.process_next_file)
            return
        
        # 상태 파일이 존재하는지 확인
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status_info = f.read().strip().split('\n')
                    status = status_info[0]
                
                # 상태에 따라 처리
                if status == 'SUCCESS':
                    print(f"[성공] {current_fbx_file} - 처리 완료")
                    if len(status_info) > 2:
                        file_size = status_info[2]
                        print(f"  파일 크기: {file_size} 바이트")
                        print(f"  저장 위치: {os.path.basename(output_file)}")
                    
                    # 성공 콜백 호출
                    if self.file_result_callback:
                        self.file_result_callback(current_fbx_file, True)
                    
                    # 처리 완료 후 정리
                    self._complete_file_processing(temp_script, status_file)
                    
                elif status == 'FAIL' or status == 'ERROR':
                    print(f"[실패] {current_fbx_file} - 처리 실패")
                    if len(status_info) > 1:
                        error_msg = status_info[1]
                        print(f"  오류: {error_msg}")
                    
                    # 실패 콜백 호출
                    if self.file_result_callback:
                        self.file_result_callback(current_fbx_file, False)
                    
                    # 처리 완료 후 정리
                    self._complete_file_processing(temp_script, status_file)
                    
            except Exception as e:
                print(f"상태 파일 읽기 오류: {e}")
        
        # 상태 파일이 없지만 출력 파일이 존재하면 성공으로 간주
        elif os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"[성공] {current_fbx_file} - Maya 파일 확인됨")
            print(f"  파일 크기: {os.path.getsize(output_file)} 바이트")
            print(f"  저장 위치: {os.path.basename(output_file)}")
            
            # 성공 콜백 호출
            if self.file_result_callback:
                self.file_result_callback(current_fbx_file, True)
            
            # 처리 완료 후 정리
            self._complete_file_processing(temp_script, status_file)
    
    def _terminate_current_process(self):
        """현재 실행 중인 프로세스를 종료합니다."""
        if self.current_process:
            try:
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.current_process.pid)], 
                             capture_output=True, text=True, timeout=10)
                print(f"프로세스 (PID: {self.current_process.pid}) 강제 종료됨")
                self.current_process = None
            except Exception as e:
                print(f"프로세스 종료 중 오류: {e}")
    
    def _complete_file_processing(self, temp_script, status_file):
        """파일 처리 완료 후 정리 작업을 수행합니다."""
        # 임시 파일 정리
        self._cleanup_temp_files(temp_script, status_file)
        
        # 타이머 중지 및 프로세스 정리
        if self.check_export_timer:
            self.check_export_timer.stop()
        self.current_process = None
        
        # 다음 파일 처리
        self.current_index += 1
        QtCore.QTimer.singleShot(500, self.process_next_file)

# 전역 배치 프로세스 매니저 인스턴스
batch_manager = BatchProcessManager()

def start_batch_process(rig_file, fbx_files, fbx_folder, save_folder, frontX_v, progress_callback=None, file_result_callback=None):
    """배치 프로세스를 시작하는 함수"""
    return batch_manager.start_batch_process(rig_file, fbx_files, fbx_folder, save_folder, frontX_v, progress_callback, file_result_callback)

def cancel_batch_process():
    """배치 프로세스를 취소하는 함수"""
    return batch_manager.cancel_batch_process()

def is_batch_running():
    """배치 프로세스가 실행 중인지 확인하는 함수"""
    if batch_manager.is_cancelled:
        return False
    
    # 현재 프로세스가 실행 중인지 확인
    if batch_manager.current_process is not None:
        # 프로세스가 실제로 실행 중인지 확인
        try:
            if batch_manager.current_process.poll() is None:
                return True
            else:
                # 프로세스가 종료된 경우 정리
                batch_manager.current_process = None
        except Exception as e:
            print(f"프로세스 상태 확인 중 오류: {e}")
            batch_manager.current_process = None
    
    # 타이머가 실행 중인지 확인
    if batch_manager.check_export_timer is not None and batch_manager.check_export_timer.isActive():
        return True
    
    # 대기 중인 파일이 있는지 확인
    if (batch_manager.file_queue and 
        batch_manager.current_index < len(batch_manager.file_queue)):
        return True
    
    return False

def get_batch_status():
    """배치 프로세스의 현재 상태를 반환하는 함수"""
    if batch_manager.is_cancelled:
        return "취소됨"
    elif is_batch_running():
        if batch_manager.file_queue:
            total = len(batch_manager.file_queue)
            current = batch_manager.current_index
            return f"실행 중 ({current}/{total})"
        else:
            return "실행 중"
    else:
        return "대기 중"

if __name__ == '__main__':
    # 테스트용 코드
    print("R8_ani_batch_process 모듈이 로드되었습니다.")
