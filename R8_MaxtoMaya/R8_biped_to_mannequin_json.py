import json
import os
from maya import cmds

def get_biped_to_mannequin_mapping():
    """
    Biped 조인트를 언리얼 엔진 마네퀸 스켈레톤 이름으로 매핑하는 딕셔너리 반환
    
    Returns:
        dict: 언리얼 마네퀸 이름 매핑 -> Biped 조인트 이름 
    """
    biped_to_mannequin = { 
        'pelvis'             : 'Bip001FBXASC032Pelvis',
        'spine_01'           : 'Bip001FBXASC032Spine',
        'spine_02'           : '',
        'spine_03'           : 'Bip001FBXASC032Spine1',
        'spine_04'           : '',
        'spine_05'           : 'Bip001FBXASC032Spine2',
        'neck_01'            : 'Bip001FBXASC032Neck',
        'neck_02'            : '',
        'head'               : 'Bip001FBXASC032Head',
        'clavicle_l'         : 'Bip001FBXASC032LFBXASC032Clavicle',
        'upperarm_l'         : 'Bip001FBXASC032LFBXASC032UpperArm',
        'lowerarm_l'         : 'Bip001FBXASC032LFBXASC032Forearm',
        'hand_l'             : 'Bip001FBXASC032LFBXASC032Hand',
        'thumb_01_l'         : 'Bip001FBXASC032LFBXASC032Finger0',
        'thumb_02_l'         : 'Bip001FBXASC032LFBXASC032Finger01',
        'thumb_03_l'         : 'Bip001FBXASC032LFBXASC032Finger02',
        'index_01_l'         : 'Bip001FBXASC032LFBXASC032Finger1',
        'index_02_l'         : 'Bip001FBXASC032LFBXASC032Finger11',
        'index_03_l'         : 'Bip001FBXASC032LFBXASC032Finger12',
        'middle_01_l'        : 'Bip001FBXASC032LFBXASC032Finger2',
        'middle_02_l'        : 'Bip001FBXASC032LFBXASC032Finger21',
        'middle_03_l'        : 'Bip001FBXASC032LFBXASC032Finger22',
        'ring_01_l'          : 'Bip001FBXASC032LFBXASC032Finger3',
        'ring_02_l'          : 'Bip001FBXASC032LFBXASC032Finger31',
        'ring_03_l'          : 'Bip001FBXASC032LFBXASC032Finger32',
        'pinky_01_l'         : 'Bip001FBXASC032LFBXASC032Finger4',
        'pinky_02_l'         : 'Bip001FBXASC032LFBXASC032Finger41',
        'pinky_03_l'         : 'Bip001FBXASC032LFBXASC032Finger42',
        'clavicle_r'         : 'Bip001FBXASC032RFBXASC032Clavicle',
        'upperarm_r'         : 'Bip001FBXASC032RFBXASC032UpperArm',
        'lowerarm_r'         : 'Bip001FBXASC032RFBXASC032Forearm',
        'hand_r'             : 'Bip001FBXASC032RFBXASC032Hand',
        'thumb_01_r'         : 'Bip001FBXASC032RFBXASC032Finger0',
        'thumb_02_r'         : 'Bip001FBXASC032RFBXASC032Finger01',
        'thumb_03_r'         : 'Bip001FBXASC032RFBXASC032Finger02',
        'index_01_r'         : 'Bip001FBXASC032RFBXASC032Finger1',
        'index_02_r'         : 'Bip001FBXASC032RFBXASC032Finger11',
        'index_03_r'         : 'Bip001FBXASC032RFBXASC032Finger12',
        'middle_01_r'        : 'Bip001FBXASC032RFBXASC032Finger2',
        'middle_02_r'        : 'Bip001FBXASC032RFBXASC032Finger21',
        'middle_03_r'        : 'Bip001FBXASC032RFBXASC032Finger22',
        'ring_01_r'          : 'Bip001FBXASC032RFBXASC032Finger3',
        'ring_02_r'          : 'Bip001FBXASC032RFBXASC032Finger31',
        'ring_03_r'          : 'Bip001FBXASC032RFBXASC032Finger32',
        'pinky_01_r'         : 'Bip001FBXASC032RFBXASC032Finger4',
        'pinky_02_r'         : 'Bip001FBXASC032RFBXASC032Finger41',
        'pinky_03_r'         : 'Bip001FBXASC032RFBXASC032Finger42',
        'thigh_l'            : 'Bip001FBXASC032LFBXASC032Thigh',
        'calf_l'             : 'Bip001FBXASC032LFBXASC032Calf',
        'foot_l'             : 'Bip001FBXASC032LFBXASC032Foot',
        'ball_l'             : 'Bip001FBXASC032LFBXASC032Toe0',
        'thigh_r'            : 'Bip001FBXASC032RFBXASC032Thigh',
        'calf_r'             : 'Bip001FBXASC032RFBXASC032Calf',
        'foot_r'             : 'Bip001FBXASC032RFBXASC032Foot',
        'ball_r'             : 'Bip001FBXASC032RFBXASC032Toe0'
    }
    
    return biped_to_mannequin

def get_scene_joints_mapping():
    """
    현재 씬에서 실제로 존재하는 조인트들만 필터링하여 매핑 반환
    create_skeleton_button으로 생성된 추가 마네퀸 조인트들도 포함
    
    Returns:
        dict: 씬에 존재하는 조인트들의 매핑 (바이패드 조인트 -> 마네퀸 조인트)
    """
    full_mapping = get_biped_to_mannequin_mapping()
    scene_mapping = {}
    
    # 1. 기본 biped to mannequin 매핑 처리 (키와 밸류 순서 바꿈)
    for mannequin_joint, biped_joint in full_mapping.items():
        # 마네퀸 조인트가 씬에 존재하는지 확인
        if cmds.objExists(mannequin_joint):
            # biped 조인트가 문자열인지 확인 (리스트가 아닌 경우)
            if isinstance(biped_joint, str):
                # 콤마로 구분된 경우 처리
                if ',' in biped_joint:
                    biped_joints = biped_joint.split(',')
                    # 모든 biped 조인트가 존재하는지 확인
                    if all(cmds.objExists(bj.strip()) for bj in biped_joints):
                        scene_mapping[biped_joint] = mannequin_joint  # 키와 밸류 순서 바꿈
                else:
                    # 단일 biped 조인트가 존재하는지 확인
                    if cmds.objExists(biped_joint):
                        scene_mapping[biped_joint] = mannequin_joint  # 키와 밸류 순서 바꿈
    
    # 2. create_skeleton_button으로 생성된 추가 마네퀸 조인트들 찾기
    # 씬의 모든 조인트를 검색하여 '_jnt' 또는 '_ue' 접미사를 가진 조인트들 찾기
    all_joints = cmds.ls(type='joint')
    
    for joint in all_joints:
        original_biped_name = None
        
        # '_jnt'로 끝나는 조인트 확인
        if joint.endswith('_jnt'):
            # 원본 biped 조인트 이름 추출 (접미사 제거)
            original_biped_name = joint[:-4]  # '_jnt' 제거
        
        # '_ue'로 끝나는 조인트 확인 (Add Sub Skeleton에서 생성된 조인트)
        elif joint.endswith('_ue'):
            # 원본 biped 조인트 이름 추출 (접미사 제거)
            original_biped_name = joint[:-3]  # '_ue' 제거
        
        # 'ue'가 포함된 조인트 확인 (로케이터 이름에서 'loc'를 'ue'로 바꾼 경우)
        elif 'ue' in joint and 'loc' not in joint:
            # 이 조인트에 연결된 parentConstraint나 scaleConstraint를 통해 원본 찾기
            try:
                # parentConstraint 연결 확인
                constraints = cmds.listConnections(joint, type='parentConstraint', source=True, destination=False)
                if constraints:
                    # constraint의 타겟을 확인
                    for constraint in constraints:
                        target_list = cmds.parentConstraint(constraint, query=True, targetList=True)
                        if target_list:
                            # 타겟이 로케이터인지 확인하고, 그 로케이터가 어떤 biped 조인트와 연결되어 있는지 확인
                            locator = target_list[0]
                            if cmds.objExists(locator):
                                # 로케이터에 연결된 조인트 찾기 (로케이터 -> biped 조인트)
                                locator_constraints = cmds.listConnections(locator, type='parentConstraint', source=False, destination=True)
                                if locator_constraints:
                                    # constraint의 소스를 확인하여 원본 biped 조인트 찾기
                                    for loc_constraint in locator_constraints:
                                        source_list = cmds.parentConstraint(loc_constraint, query=True, targetList=True)
                                        if source_list:
                                            for source_joint in source_list:
                                                if cmds.objExists(source_joint) and cmds.nodeType(source_joint) == 'joint':
                                                    original_biped_name = source_joint
                                                    break
                                    if original_biped_name:
                                        break
                            if original_biped_name:
                                break
                
                # 위의 방법으로 찾지 못한 경우, 이름 패턴으로 추측
                if not original_biped_name:
                    # 'ue'를 제거하여 원본 이름 추측
                    potential_original = joint.replace('ue', '')
                    if cmds.objExists(potential_original) and cmds.nodeType(potential_original) == 'joint':
                        original_biped_name = potential_original
                    else:
                        # 'ue'를 'loc'로 바꿔서 로케이터 이름 추측하고, 그 로케이터와 연결된 조인트 찾기
                        potential_locator = joint.replace('ue', 'loc')
                        if cmds.objExists(potential_locator):
                            loc_constraints = cmds.listConnections(potential_locator, type='parentConstraint', source=False, destination=True)
                            if loc_constraints:
                                for loc_constraint in loc_constraints:
                                    source_list = cmds.parentConstraint(loc_constraint, query=True, targetList=True)
                                    if source_list:
                                        for source_joint in source_list:
                                            if cmds.objExists(source_joint) and cmds.nodeType(source_joint) == 'joint':
                                                original_biped_name = source_joint
                                                break
                                    if original_biped_name:
                                        break
                            if original_biped_name:
                                break
                                
            except Exception as e:
                print(f"조인트 {joint}의 원본 찾기 중 오류: {e}")
                continue
        
        # 원본 biped 조인트가 발견되고 실제로 존재하는지 확인
        if original_biped_name and cmds.objExists(original_biped_name):
            # 이미 매핑에 포함되지 않은 경우에만 추가 (키와 밸류 순서 바꿈)
            if original_biped_name not in scene_mapping:
                scene_mapping[original_biped_name] = joint  # 키와 밸류 순서 바꿈
                print(f"추가 마네퀸 조인트 매핑 발견: {original_biped_name} -> {joint}")
    
    return scene_mapping

def export_mapping_to_json(file_path, mapping_data=None):
    """
    조인트 매핑을 JSON 파일로 익스포트
    
    Args:
        file_path (str): 저장할 JSON 파일 경로
        mapping_data (dict): 저장할 매핑 데이터 (None이면 현재 씬 기준으로 생성)
    
    Returns:
        bool: 성공 여부
    """
    try:
        if mapping_data is None:
            mapping_data = get_scene_joints_mapping()
        
        # JSON 파일로 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, indent=4, ensure_ascii=False)
        
        print(f"매핑 데이터가 성공적으로 저장되었습니다: {file_path}")
        return True
        
    except Exception as e:
        print(f"JSON 익스포트 중 오류 발생: {str(e)}")
        return False

def import_mapping_from_json(file_path):
    """
    JSON 파일에서 조인트 매핑을 임포트
    
    Args:
        file_path (str): 불러올 JSON 파일 경로
    
    Returns:
        dict: 매핑 데이터 (실패 시 None)
    """
    try:
        if not os.path.exists(file_path):
            print(f"파일이 존재하지 않습니다: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
        
        print(f"매핑 데이터가 성공적으로 로드되었습니다: {file_path}")
        return mapping_data
        
    except Exception as e:
        print(f"JSON 임포트 중 오류 발생: {str(e)}")
        return None

def apply_bone_mapping(mapping_data):
    """
    매핑 데이터를 기반으로 조인트 매칭 적용
    
    Args:
        mapping_data (dict): 적용할 매핑 데이터 (바이패드 조인트 -> 마네퀸 조인트)
    
    Returns:
        bool: 성공 여부
    """
    try:
        success_count = 0
        fail_count = 0
        
        for biped_joint, mannequin_joint in mapping_data.items():  # 키와 밸류 순서 바꿈
            try:
                if isinstance(biped_joint, str):
                    if ',' in biped_joint:
                        # 콤마로 구분된 여러 조인트 처리
                        biped_joints = [bj.strip() for bj in biped_joint.split(',')]
                        if cmds.objExists(mannequin_joint) and all(cmds.objExists(bj) for bj in biped_joints):
                            # 여러 조인트를 사용한 포인트 컨스트레인트
                            constraint = cmds.pointConstraint(*biped_joints, mannequin_joint, mo=False)
                            if len(biped_joints) == 2:
                                # 가중치 설정 (첫 번째 80%, 두 번째 20%)
                                cmds.setAttr(f'{constraint[0]}.{biped_joints[0]}W0', 0.8)
                                cmds.setAttr(f'{constraint[0]}.{biped_joints[1]}W1', 0.2)
                            cmds.delete(constraint[0])
                            success_count += 1
                    else:
                        # 단일 조인트 처리
                        if cmds.objExists(mannequin_joint) and cmds.objExists(biped_joint):
                            constraint = cmds.pointConstraint(biped_joint, mannequin_joint, mo=False)
                            cmds.delete(constraint[0])
                            success_count += 1
                        else:
                            fail_count += 1
                            
            except Exception as e:
                print(f"조인트 매칭 실패 - {biped_joint}: {str(e)}")
                fail_count += 1
        
        print(f"조인트 매칭 완료 - 성공: {success_count}, 실패: {fail_count}")
        return success_count > 0
        
    except Exception as e:
        print(f"조인트 매칭 적용 중 오류 발생: {str(e)}")
        return False 