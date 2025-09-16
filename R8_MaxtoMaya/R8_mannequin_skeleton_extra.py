import maya.cmds as cmds

advance_to_mannequin_mapping = {'Root_M': 'pelvis',
                                'Spine1_M': 'spine_01',
                                'Spine2_M': 'spine_02',
                                'Spine3_M': 'spine_03',
                                'Spine4_M': 'spine_04',
                                'Chest_M': 'spine_05',
                                'Neck1_M': 'neck_01',
                                'Neck2_M': 'neck_02',
                                'Head_M': 'head',
                                'Scapula_L': 'clavicle_l',
                                'Shoulder_L': 'upperarm_l',
                                'ShoulderPart1_L': 'upperarm_twist_01_l',
                                'ShoulderPart2_L': 'upperarm_twist_01_l',
                                'Elbow_L': 'lowerarm_l',
                                'ElbowPart1_L': 'lowerarm_twist_02_l',
                                'ElbowPart2_L': 'lowerarm_twist_01_l',
                                'Wrist_L': 'hand_l',
                                'ThumbFinger1_L': 'thumb_01_l',
                                'ThumbFinger2_L': 'thumb_02_l',
                                'ThumbFinger3_L': 'thumb_03_l',
                                'IndexFinger0_L': 'index_metacarpal_l',
                                'IndexFinger1_L': 'index_01_l',
                                'IndexFinger2_L': 'index_02_l',
                                'IndexFinger3_L': 'index_03_l',
                                'MiddleFinger0_L': 'middle_metacarpal_l',    
                                'MiddleFinger1_L': 'middle_01_l',
                                'MiddleFinger2_L': 'middle_02_l',
                                'MiddleFinger3_L': 'middle_03_l',
                                'RingFinger0_L': 'ring_metacarpal_l',
                                'RingFinger1_L': 'ring_01_l',
                                'RingFinger2_L': 'ring_02_l',
                                'RingFinger3_L': 'ring_03_l',
                                'PinkyFinger0_L': 'pinky_metacarpal_l',
                                'PinkyFinger1_L': 'pinky_01_l',
                                'PinkyFinger2_L': 'pinky_02_l',
                                'PinkyFinger3_L': 'pinky_03_l',
                                'Scapula_R': 'clavicle_r',
                                'Shoulder_R': 'upperarm_r',
                                'ShoulderPart1_R': 'upperarm_twist_01_r',
                                'ShoulderPart2_R': 'upperarm_twist_01_r',
                                'Elbow_R': 'lowerarm_r',
                                'ElbowPart1_R': 'lowerarm_twist_02_r',
                                'ElbowPart2_R': 'lowerarm_twist_01_r',
                                'Wrist_R': 'hand_r',
                                'ThumbFinger1_R': 'thumb_01_r',
                                'ThumbFinger2_R': 'thumb_02_r',
                                'ThumbFinger3_R': 'thumb_03_r',
                                'IndexFinger0_R': 'index_metacarpal_r',
                                'IndexFinger1_R': 'index_01_r',
                                'IndexFinger2_R': 'index_02_r',
                                'IndexFinger3_R': 'index_03_r',
                                'MiddleFinger0_R': 'middle_metacarpal_r',
                                'MiddleFinger1_R': 'middle_01_r',
                                'MiddleFinger2_R': 'middle_02_r',
                                'MiddleFinger3_R': 'middle_03_r',
                                'RingFinger0_R': 'ring_metacarpal_r',
                                'RingFinger1_R': 'ring_01_r',
                                'RingFinger2_R': 'ring_02_r',
                                'RingFinger3_R': 'ring_03_r',
                                'PinkyFinger0_R': 'pinky_metacarpal_r',
                                'PinkyFinger1_R': 'pinky_01_r',
                                'PinkyFinger2_R': 'pinky_02_r',
                                'PinkyFinger3_R': 'pinky_03_r',
                                'Hip_L': 'thigh_l',
                                'HipPart1_L': 'thigh_twist_01_l',
                                'HipPart2_L': 'thigh_twist_02_l',
                                'Knee_L': 'calf_l',
                                'KneePart1_L': 'calf_twist_02_l',
                                'KneePart2_L': 'calf_twist_01_l',
                                'Ankle_L': 'foot_l',
                                'Toes_L': 'toe_l',
                                'Hip_R': 'thigh_r',
                                'HipPart1_R': 'thigh_twist_01_r',
                                'HipPart2_R': 'thigh_twist_02_r',
                                'Knee_R': 'calf_r',
                                'KneePart1_R': 'calf_twist_02_r',
                                'KneePart2_R': 'calf_twist_01_r',
                                'Ankle_R': 'foot_r',
                                'Toes_R': 'toe_r'}
    
    
def get_all_joints_under_bip001(select_mesh=None):
    """
    Bip001 조인트 하위에 있는 모든 조인트를 리스트로 가져오는 함수
    Bip001 조인트가 존재하지 않으면 Base 조인트를 사용
    select_mesh가 지정된 경우, 해당 메시(들)의 인플루언스 조인트만 필터링
    
    Args:
        select_mesh (str or list, optional): 인플루언스 조인트를 확인할 메시 이름 또는 메시 리스트
    
    Returns:
        list: Bip001 하위의 조인트 리스트 (select_mesh가 있으면 인플루언스 조인트만)
    """
    # Bip001 조인트가 존재하는지 확인하고, 없으면 Base를 찾음
    root_joint = None
    if cmds.objExists("Bip001"):
        root_joint = "Bip001"
    elif cmds.objExists("Base"):
        root_joint = "Base"
        print("Bip001 조인트를 찾을 수 없어 Base 조인트를 사용합니다.")
    else:
        print("Bip001과 Base 조인트를 모두 찾을 수 없습니다.")
        return []
    
    # Bip001 하위의 모든 조인트 가져오기 (재귀적으로)
    all_joints = cmds.listRelatives(root_joint, allDescendents=True, type="joint") or []
    
    # select_mesh가 지정된 경우 인플루언스 조인트만 필터링
    if select_mesh:
        # 문자열인 경우 리스트로 변환
        if isinstance(select_mesh, str):
            mesh_list = [select_mesh]
        else:
            mesh_list = select_mesh
        
        # 모든 메시의 인플루언스 조인트를 수집
        all_influence_joints = set()
        
        for mesh_name in mesh_list:
            if cmds.objExists(mesh_name):
                try:
                    # 메시의 스킨 클러스터 찾기
                    skin_clusters = cmds.ls(cmds.listHistory(mesh_name), type='skinCluster')
                    
                    if skin_clusters:
                        # 스킨 클러스터의 인플루언스 조인트들 가져오기
                        influence_joints = cmds.skinCluster(skin_clusters[0], query=True, influence=True)
                        all_influence_joints.update(influence_joints)
                        print(f"메시 '{mesh_name}'에서 {len(influence_joints)}개의 인플루언스 조인트를 찾았습니다.")
                    else:
                        print(f"메시 '{mesh_name}'에서 스킨 클러스터를 찾을 수 없습니다.")
                except Exception as e:
                    print(f"메시 '{mesh_name}' 처리 중 오류 발생: {e}")
            else:
                print(f"메시 '{mesh_name}'가 존재하지 않습니다.")
        
        if all_influence_joints:
            # all_joints에서 인플루언스 조인트에 포함된 것만 필터링
            filtered_joints = [joint for joint in all_joints if joint in all_influence_joints]
            
            print(f"총 {len(mesh_list)}개 메시의 인플루언스 조인트 {len(filtered_joints)}개를 찾았습니다.")
            print(f"전체 Bip001 하위 조인트: {len(all_joints)}개")
            
            return filtered_joints
        else:
            print("인플루언스 조인트를 찾을 수 없습니다.")
            print("모든 Bip001 하위 조인트를 반환합니다.")
    
    print(f"Bip001 하위 총 {len(all_joints)}개의 조인트를 찾았습니다.")
    return all_joints

def remove_bip_joints(joint_list):
    """
    조인트 리스트에서 'Bip' 문자가 포함된 조인트들을 제거하는 함수
    
    Args:
        joint_list (list): 조인트 리스트
        
    Returns:
        list: 'Bip' 문자가 포함되지 않은 조인트들의 리스트
    """
    if not joint_list:
        print("입력된 조인트 리스트가 비어있습니다.")
        return []
    
    # 'Bip' 문자가 포함되지 않은 조인트들만 필터링
    filtered_joints = [joint for joint in joint_list if 'Bip' not in joint]
    
    removed_count = len(joint_list) - len(filtered_joints)
    print(f"'Bip' 문자가 포함된 {removed_count}개의 조인트를 제거했습니다.")
    print(f"필터링 후 {len(filtered_joints)}개의 조인트가 남았습니다.")
    
    return filtered_joints

def create_manequin_skeleton_from_selected(selected_joints=None):
    """
    선택한 조인트 정보들을 기반으로 언리얼 엔진 마네퀸 스켈레톤 구조로 새로운 조인트들을 생성하는 함수
    
    Args:
        selected_joints (list): 조인트 정보 딕셔너리 리스트
    
    Returns:
        list: 생성된 언리얼 스켈레톤 조인트 리스트
    """
    # 조인트 정보가 없으면 빈 리스트 반환
    if not selected_joints:
        print("생성할 조인트 정보가 없습니다.")
        return []
    
    # Undo 블록 시작
    cmds.undoInfo(openChunk=True, chunkName="Create UE Skeleton Joints")
    
    try:
        # 생성된 조인트들을 저장할 리스트
        created_joints = []
        
        print("\n=== 언리얼 스켈레톤 조인트 생성 시작 ===")
        
        # 각 조인트 정보에 대해 처리
        for joint_info in selected_joints:
            if isinstance(joint_info, dict):
                joint_name = joint_info['name']
                world_pos = joint_info['position']
                world_rot = joint_info['rotation']
                
                # 새로운 조인트 생성
                try:
                    cmds.select(clear=True)
                    new_joint = cmds.joint(name=joint_name, position=world_pos)
                    cmds.xform(new_joint, worldSpace=True, rotation=world_rot)
                    
                    created_joints.append(new_joint)
                    
                    print(f"생성됨: {joint_info['original_locator']} -> {new_joint}")
                    
                except Exception as e:
                    print(f"조인트 생성 실패 ({joint_name}): {e}")
            else:
                # 이전 버전 호환성을 위해 문자열 형태도 처리
                joint = joint_info
                world_pos = cmds.xform(joint, query=True, worldSpace=True, translation=True)
                world_rot = cmds.xform(joint, query=True, worldSpace=True, rotation=True)
                
                try:
                    cmds.select(clear=True)
                    new_joint = cmds.joint(name=joint, position=world_pos)
                    cmds.xform(new_joint, worldSpace=True, rotation=world_rot)
                    
                    created_joints.append(new_joint)
                    print(f"생성됨: {joint} -> {new_joint}")
                    
                except Exception as e:
                    print(f"조인트 생성 실패 ({joint}): {e}")
        
        # 생성된 조인트들 선택
        if created_joints:
            cmds.select(created_joints, replace=True)
            cmds.makeIdentity(created_joints, apply=True, t=True, r=True, s=True, n=False, pn=False)
            print("생성된 조인트들이 선택되었습니다.")
        
        return created_joints
        
    except Exception as e:
        print(f"언리얼 스켈레톤 조인트 생성 중 오류 발생: {str(e)}")
        raise
    finally:
        # Undo 블록 종료
        cmds.undoInfo(closeChunk=True)

def recreate_hierarchy(original_joints, joint_mapping):
    """
    원본 조인트들의 계층 구조를 새로운 조인트들에 적용하는 함수
    
    Args:
        original_joints (list): 원본 조인트 리스트
        joint_mapping (dict): 원본 -> 새로운 조인트 매핑
    """
    print(f"계층 구조 재생성 시작: {len(original_joints)}개 조인트 처리")
    
    # 계층 구조 재생성을 위해 조인트들을 정렬 (루트부터 처리)
    hierarchy_success_count = 0
    
    for original_joint in original_joints:
        if not cmds.objExists(original_joint):
            print(f"원본 조인트가 존재하지 않음: {original_joint}")
            continue
            
        if original_joint not in joint_mapping:
            print(f"매핑에서 조인트를 찾을 수 없음: {original_joint}")
            continue
            
        new_joint = joint_mapping[original_joint]
        
        if not cmds.objExists(new_joint):
            print(f"새로운 조인트가 존재하지 않음: {new_joint}")
            continue
        
        # 원본 조인트의 부모 찾기
        parent = cmds.listRelatives(original_joint, parent=True, type='joint')
        
        if parent and parent[0] in joint_mapping:
            parent_new_joint = joint_mapping[parent[0]]
            
            # 부모 조인트가 존재하는지 확인
            if cmds.objExists(parent_new_joint):
                try:
                    # 이미 올바른 부모를 가지고 있는지 확인
                    current_parent = cmds.listRelatives(new_joint, parent=True)
                    if current_parent and current_parent[0] == parent_new_joint:
                        print(f"이미 올바른 계층 구조: {new_joint} -> {parent_new_joint}")
                        continue
                    
                    # 새로운 조인트를 해당 부모 하위로 이동
                    cmds.parent(new_joint, parent_new_joint)
                    hierarchy_success_count += 1
                    print(f"계층 구조 설정 성공: {new_joint} -> {parent_new_joint}")
                    
                except Exception as e:
                    print(f"계층 구조 설정 실패 ({new_joint} -> {parent_new_joint}): {e}")
            else:
                print(f"부모 조인트가 존재하지 않음: {parent_new_joint}")
        else:
            if parent:
                print(f"부모 조인트가 매핑에 없음: {parent[0]} (자식: {original_joint})")
            else:
                print(f"루트 조인트: {original_joint} -> {new_joint}")
    
    print(f"계층 구조 재생성 완료: {hierarchy_success_count}개 성공")

def process_advanced_joints(bip_joints):
    """
    bip_joints에서 advanced skeleton 조인트들을 처리하는 함수
    constraint가 연결된 로케이터의 위치 정보와 "loc"를 "jnt"로 바꾼 이름을 반환
    
    Args:
        bip_joints (list): 처리할 조인트 리스트
        
    Returns:
        list: 처리된 조인트 정보 리스트 (딕셔너리 형태: {'name': joint_name, 'position': world_pos, 'rotation': world_rot, 'original_joint': original_joint})
    """
    advance_joints = []
    for jnt in bip_joints:
        # 조인트에 연결된 parentConstraint 찾기
        parent_constraints = cmds.listConnections(jnt, type='parentConstraint', source=False, destination=True)
        if parent_constraints:
            try:
                target_list = cmds.parentConstraint(parent_constraints[0], query=True, targetList=True)
                if target_list:
                    locator_name = target_list[0]
                    
                    # 로케이터가 실제로 존재하는지 확인
                    if cmds.objExists(locator_name):
                        # 로케이터의 월드 위치와 회전 가져오기
                        world_pos = cmds.xform(locator_name, query=True, worldSpace=True, translation=True)
                        world_rot = cmds.xform(locator_name, query=True, worldSpace=True, rotation=True)
                        
                        # 로케이터 이름에서 "loc"를 "ue"로 바꿔서 조인트 이름 생성
                        if locator_name.endswith("_loc"):
                            # "_loc" 접미사를 "_ue"로 바꿈
                            joint_name = locator_name[:-4] + "_ue"
                        elif "loc" in locator_name:
                            # "loc"가 중간에 있는 경우 마지막 "loc"만 "ue"로 바꿈
                            last_loc_index = locator_name.rfind("loc")
                            joint_name = locator_name[:last_loc_index] + "ue" + locator_name[last_loc_index+3:]
                        else:
                            # "loc"가 없는 경우 "_ue" 접미사 추가
                            joint_name = f"{locator_name}_ue"

                        # 이미 존재하는 조인트 이름인지 확인하고 고유한 이름 생성
                        original_joint_name = joint_name
                        counter = 1
                        while cmds.objExists(joint_name):
                            joint_name = f"{original_joint_name}_{counter}"
                            counter += 1
                        
                        # 조인트 정보를 딕셔너리로 저장 (원본 바이패드 조인트 정보 포함)
                        joint_info = {
                            'name': joint_name,
                            'position': world_pos,
                            'rotation': world_rot,
                            'original_locator': locator_name,
                            'original_joint': jnt  # 원본 바이패드 조인트 추가
                        }
                        advance_joints.append(joint_info)
                        print(f"로케이터 발견: {locator_name} -> 조인트 이름: {joint_name} (원본: {jnt})")
                    
            except Exception as e:
                print(f"오류 발생 ({jnt}): {e}")
                
    return advance_joints
    
def process_bip001_joints(select_mesh=None):
    """
    1, 2번 함수를 순차적으로 실행하는 메인 함수
    
    Args:
        select_mesh (str or list, optional): 인플루언스 조인트를 확인할 메시 이름 또는 메시 리스트
    
    Returns:
        list: 최종 필터링된 조인트 리스트
    """
    print("=== Bip001 조인트 처리 시작 ===")
    
    # 1. Bip001 하위의 모든 조인트 가져오기 (select_mesh 인플루언스 필터링 포함)
    print("\n1단계: Bip001 하위 모든 조인트 가져오기")
    select_joints = get_all_joints_under_bip001(select_mesh)
    
    if not select_joints:
        print("처리할 조인트가 없습니다.")
        return []
    
    # 2. Bip 문자가 포함된 조인트들 제거
    print("\n2단계: 'Bip' 문자가 포함된 조인트들 제거")
    bip_extra_joints = remove_bip_joints(select_joints)
    
    print("\n=== 처리 완료 ===")
    
    # 3. Advanced Skeleton 조인트 가져오기
    advanced_joints = process_advanced_joints(bip_extra_joints)
    
    print("\n=== 처리 완료 ===")
    
    print("최종 조인트 리스트:")
    for i, joint in enumerate(advanced_joints, 1):
        print(f"  {i}. {joint}")
    
    return advanced_joints

def create_unreal_skeleton_complete(select_mesh=None):
    """
    전체 프로세스를 실행하는 통합 함수
    1. Bip001 하위 조인트 가져오기 (select_mesh 인플루언스 필터링 포함)
    2. Bip 문자 포함 조인트 제거
    3. 언리얼 스켈레톤 구조로 새로운 조인트 생성
    
    Args:
        select_mesh (str or list, optional): 인플루언스 조인트를 확인할 메시 이름 또는 메시 리스트
    
    Returns:
        list: 생성된 언리얼 스켈레톤 조인트 리스트
    """
    print("=== 언리얼 스켈레톤 생성 전체 프로세스 시작 ===")
    
    # 1-2단계: 조인트 필터링
    advanced_joints = process_bip001_joints(select_mesh)
    
    # 3단계: 언리얼 스켈레톤 생성
    print("\n3단계: 언리얼 스켈레톤 조인트 생성")
    manequin_joints = create_manequin_skeleton_from_selected(advanced_joints)
    
    print("\n=== 전체 프로세스 완료 ===")
    return advanced_joints, manequin_joints

def connect_locators_to_mannequin_joints(advanced_joints):
    """
    로케이터들이 생성된 마네퀸 조인트들을 제어하도록 패런트 컨스트레인트와 스케일 컨스트레인트를 연결하는 함수
    
    Args:
        advanced_joints (list): 어드밴스드 조인트 정보 리스트 (딕셔너리 형태)
    """
    print("\n=== 로케이터-마네퀸 조인트 컨스트레인트 연결 시작 ===")
    
    parent_constraint_count = 0
    scale_constraint_count = 0
    failed_connections = []
    
    for joint_info in advanced_joints:
        if not isinstance(joint_info, dict):
            continue
            
        locator_name = joint_info['original_locator']
        joint_name = joint_info['name']
        
        # 로케이터와 조인트가 모두 존재하는지 확인
        if not cmds.objExists(locator_name):
            print(f"로케이터가 존재하지 않음: {locator_name}")
            failed_connections.append((locator_name, joint_name, "로케이터 없음"))
            continue
            
        if not cmds.objExists(joint_name):
            print(f"마네퀸 조인트가 존재하지 않음: {joint_name}")
            failed_connections.append((locator_name, joint_name, "조인트 없음"))
            continue
        
        try:
            # 패런트 컨스트레인트 연결 (로케이터가 조인트를 제어)
            cmds.parentConstraint(locator_name, joint_name, maintainOffset=False)
            parent_constraint_count += 1
            print(f"패런트 컨스트레인트 연결: {locator_name} -> {joint_name}")
            
            # 스케일 컨스트레인트 연결 (로케이터가 조인트를 제어)
            cmds.scaleConstraint(locator_name, joint_name, maintainOffset=False)
            scale_constraint_count += 1
            print(f"스케일 컨스트레인트 연결: {locator_name} -> {joint_name}")
            
        except Exception as e:
            print(f"컨스트레인트 연결 실패 ({locator_name} -> {joint_name}): {e}")
            failed_connections.append((locator_name, joint_name, str(e)))
    
    print(f"\n=== 컨스트레인트 연결 완료 ===")
    print(f"패런트 컨스트레인트 성공: {parent_constraint_count}개")
    print(f"스케일 컨스트레인트 성공: {scale_constraint_count}개")
    
    if failed_connections:
        print(f"연결 실패: {len(failed_connections)}개")
        for locator, joint, reason in failed_connections:
            print(f"  실패: {locator} -> {joint} ({reason})")
    
    return parent_constraint_count, scale_constraint_count

def create_mannequin_skeleton(select_mesh=None):
    """
    마네퀸 스켈레톤을 생성하는 메인 함수
    
    Args:
        select_mesh (str or list, optional): 인플루언스 조인트를 확인할 메시 이름 또는 메시 리스트
    """
    # Undo 블록 시작
    cmds.undoInfo(openChunk=True, chunkName="Create Mannequin Skeleton")
    
    try:
        ad, ma = create_unreal_skeleton_complete(select_mesh)
        
        # 원본 바이패드 조인트 -> 마네퀸 조인트 매핑 생성
        original_to_mannequin_mapping = {}
        mannequin_to_original_mapping = {}
        
        for i, (advance_joint_info, mannequin_joint) in enumerate(zip(ad, ma)):
            if advance_joint_info and mannequin_joint:
                # advance_joint_info가 딕셔너리인 경우
                if isinstance(advance_joint_info, dict):
                    original_joint = advance_joint_info['original_joint']
                    mannequin_joint_name = advance_joint_info['name']
                    
                    # 실제 생성된 마네퀸 조인트 이름 사용
                    original_to_mannequin_mapping[original_joint] = mannequin_joint
                    mannequin_to_original_mapping[mannequin_joint] = original_joint
                    
                    # 기존 매핑도 유지
                    advance_to_mannequin_mapping[mannequin_joint_name] = mannequin_joint
                else:
                    advance_joint_name = advance_joint_info
                    original_to_mannequin_mapping[advance_joint_name] = mannequin_joint
                    advance_to_mannequin_mapping[advance_joint_name] = mannequin_joint
        
        print(f"\n=== 계층 구조 재생성 시작 ===")
        print(f"매핑된 조인트 수: {len(original_to_mannequin_mapping)}")
        
        # 원본 바이패드 조인트의 계층 구조를 기반으로 마네퀸 조인트 계층 구조 재생성
        recreate_hierarchy(original_to_mannequin_mapping.keys(), original_to_mannequin_mapping)
        
        # 기본 마네퀸 본과 추가 조인트 연결
        connect_to_base_mannequin_skeleton(original_to_mannequin_mapping)
        
        # 로케이터들이 마네퀸 조인트들을 제어하도록 컨스트레인트 연결
        connect_locators_to_mannequin_joints(ad)
        
        print("\n=== 마네퀸 스켈레톤 생성 완료 ===")
        print("- 추가 조인트들이 생성되었습니다")
        print("- 바이패드 계층 구조가 재생성되었습니다") 
        print("- 기본 마네퀸 본과 연결되었습니다")
        print("- 로케이터-마네퀸 조인트 컨스트레인트가 연결되었습니다")
        print("(모든 작업은 Undo 가능)")
        
    except Exception as e:
        print(f"마네퀸 스켈레톤 생성 중 오류 발생: {str(e)}")
        raise
    finally:
        # Undo 블록 종료
        cmds.undoInfo(closeChunk=True)

def connect_to_base_mannequin_skeleton(original_to_mannequin_mapping):
    """
    새로 생성된 마네퀸 추가 조인트들을 기본 마네퀸 본 구조에 연결하는 함수
    1. 먼저 추가 마네퀸 조인트들끼리 바이패드 본 구조처럼 계층을 형성
    2. 그 중 최상위 조인트들만 기본 마네퀸 본에 연결
    
    Args:
        original_to_mannequin_mapping (dict): 원본 바이패드 조인트 -> 새로 생성된 마네퀸 조인트 매핑
    """
    print(f"\n=== 추가 마네퀸 조인트 계층 구조 및 기본 본 연결 시작 ===")
    
    # 1단계: 추가 마네퀸 조인트들끼리 계층 구조 형성 (이미 recreate_hierarchy에서 처리됨)
    print("1단계: 추가 마네퀸 조인트 계층 구조는 이미 형성되었습니다.")
    
    # 2단계: 최상위 추가 마네퀸 조인트들 찾기
    root_additional_joints = []
    
    for original_joint, new_mannequin_joint in original_to_mannequin_mapping.items():
        if not cmds.objExists(new_mannequin_joint):
            continue
            
        # 현재 조인트의 부모 확인
        current_parents = cmds.listRelatives(new_mannequin_joint, parent=True)
        
        is_root_additional = True
        
        if current_parents:
            parent_joint = current_parents[0]
            # 부모가 추가 마네퀸 조인트 중 하나인지 확인
            if parent_joint in original_to_mannequin_mapping.values():
                is_root_additional = False
        
        if is_root_additional:
            root_additional_joints.append((original_joint, new_mannequin_joint))
            print(f"최상위 추가 조인트 발견: {new_mannequin_joint}")
    
    print(f"총 {len(root_additional_joints)}개의 최상위 추가 조인트를 찾았습니다.")
    
    # 3단계: 최상위 추가 조인트들만 기본 마네퀸 본에 연결
    connection_success_count = 0
    
    for original_joint, new_mannequin_joint in root_additional_joints:
        # 원본 조인트에서 로케이터 찾기
        locator_name = None
        parent_constraints = cmds.listConnections(original_joint, type='parentConstraint', source=False, destination=True)
        
        if parent_constraints:
            try:
                target_list = cmds.parentConstraint(parent_constraints[0], query=True, targetList=True)
                if target_list:
                    locator_name = target_list[0]
            except Exception as e:
                print(f"로케이터를 찾을 수 없음: {original_joint}")
                continue
        
        if not locator_name or not cmds.objExists(locator_name):
            print(f"로케이터를 찾을 수 없음: {original_joint}")
            continue
            
        print(f"최상위 조인트 처리 중: {new_mannequin_joint} (로케이터: {locator_name})")
        
        # 로케이터의 상위 그룹들을 탐색하여 어드밴스드 스켈레톤 조인트 찾기
        base_mannequin_parent = None
        current_parent = locator_name
        search_depth = 0
        max_search_depth = 10  # 상위 그룹 탐색 깊이
        
        while current_parent and search_depth < max_search_depth:
            # 현재 오브젝트의 부모 찾기
            parents = cmds.listRelatives(current_parent, parent=True, fullPath=False)
            if not parents:
                break
                
            parent_obj = parents[0]
            print(f"  상위 그룹 확인: {parent_obj}")
            
            # 부모가 조인트인지 확인
            if cmds.objectType(parent_obj) == 'joint':
                # 이 조인트가 advance_to_mannequin_mapping 에 있는지 확인
                if parent_obj in advance_to_mannequin_mapping:
                    base_mannequin_parent = advance_to_mannequin_mapping[parent_obj]
                    print(f"  어드밴스드 스켈레톤 조인트 발견: {parent_obj} -> 마네퀸 조인트: {base_mannequin_parent}")
                    break
            
            # 다음 상위로 이동
            current_parent = parent_obj
            search_depth += 1
        
        # 기본 마네퀸 본을 찾았고 실제로 존재하는 경우 연결
        if base_mannequin_parent and cmds.objExists(base_mannequin_parent):
            try:
                # 현재 부모 확인
                current_parent = cmds.listRelatives(new_mannequin_joint, parent=True)
                
                # 이미 올바른 부모를 가지고 있지 않은 경우에만 연결
                if not current_parent or current_parent[0] != base_mannequin_parent:
                    cmds.parent(new_mannequin_joint, base_mannequin_parent)
                    connection_success_count += 1
                    print(f"  기본 마네퀸 본 연결 성공: {new_mannequin_joint} -> {base_mannequin_parent}")
                else:
                    print(f"  이미 연결됨: {new_mannequin_joint} -> {base_mannequin_parent}")
                    
            except Exception as e:
                print(f"  기본 마네퀸 본 연결 실패 ({new_mannequin_joint} -> {base_mannequin_parent}): {e}")
        else:
            # 기본 마네퀸 본을 찾지 못한 경우
            print(f"  기본 마네퀸 본을 찾을 수 없음: {original_joint} (추가 조인트: {new_mannequin_joint})")
            print(f"  로케이터 {locator_name}의 상위 그룹에서 어드밴스드 스켈레톤 조인트를 찾지 못했습니다.")
            
            # pelvis가 존재하면 pelvis에 연결 시도 (폴백)
            if cmds.objExists('pelvis'):
                try:
                    current_parent = cmds.listRelatives(new_mannequin_joint, parent=True)
                    if not current_parent:  # 부모가 없는 경우에만
                        cmds.parent(new_mannequin_joint, 'pelvis')
                        connection_success_count += 1
                        print(f"  폴백으로 pelvis에 연결: {new_mannequin_joint} -> pelvis")
                except Exception as e:
                    print(f"  pelvis 연결 실패 ({new_mannequin_joint}): {e}")
    
    print(f"\n기본 마네퀸 본 연결 완료:")
    print(f"- 최상위 추가 조인트: {len(root_additional_joints)}개")
    print(f"- 기본 본 연결 성공: {connection_success_count}개")
    print("- 추가 조인트들의 내부 계층 구조는 유지됩니다")

# 실행 예시
if __name__ == "__main__":
    create_mannequin_skeleton()
    # 1. 조인트 필터링만 실행
    # filtered_joints = process_bip001_joints()
    
    # 2. 선택된 조인트로 언리얼 스켈레톤 생성만 실행
    # unreal_joints = create_unreal_skeleton_from_selected()
