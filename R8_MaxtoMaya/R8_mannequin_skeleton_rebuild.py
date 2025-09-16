import os
from maya import cmds

def import_mannequin_skeleton(skeleton_path=None):
    """
    Mannequin 스켈레톤을 Maya 씬에 임포트합니다.
    
    Args:
        skeleton_path (str): 임포트할 스켈레톤 파일의 경로
        
    Returns:
        bool: 임포트 성공 시 True, 실패 시 False
    """
    try:
        # 파일 존재 여부 확인
        if not os.path.exists(skeleton_path):
            cmds.warning(f"스켈레톤 파일을 찾을 수 없습니다: {skeleton_path}")
            return False
        
        # 기존 IK 핸들러 삭제
        if cmds.objExists('ik_hand_root'):
            cmds.delete('ik_hand_root')
        if cmds.objExists('ik_foot_root'):
            cmds.delete('ik_foot_root')
            
        # 파일 임포트 (현재 씬에 추가)
        cmds.file(skeleton_path, i=True, type="mayaAscii", ignoreVersion=True)
        
        # 선택 해제
        cmds.select(clear=True)
        
        print(f"스켈레톤 임포트 완료: {skeleton_path}")
        return True
        
    except Exception as e:
        cmds.error(f"스켈레톤 임포트 중 오류 발생: {str(e)}")
        return False


def mannequin_joint_constraint(as_joint, ue_joint, mo, offset):
    """
    Mannequin 조인트에 컨스트레인트를 적용합니다.
    
    Args:
        as_joint (str): 소스 조인트 이름 (Advanced Skeleton)
        ue_joint (str): 타겟 조인트 이름 (Unreal Engine Mannequin)
        mo (list): [포인트 컨스트레인트 MO, 오리엔트 컨스트레인트 MO] 플래그
        offset (list): [X, Y, Z] 오프셋 값
    """
    xyz = ['x', 'y', 'z']
    XYZ = ['X', 'Y', 'Z']
    
    if not (cmds.objExists(as_joint) and cmds.objExists(ue_joint)):
        cmds.warning(f"조인트를 찾을 수 없습니다: {as_joint} 또는 {ue_joint}")
        return
    
    try:
        # 포인트 컨스트레인트 적용
        if mo[0]:
            cmds.pointConstraint(as_joint, ue_joint, mo=True)
        else:
            cmds.pointConstraint(as_joint, ue_joint, mo=False)

        # 오리엔트 컨스트레인트 적용
        if mo[1]:
            cmds.orientConstraint(as_joint, ue_joint, mo=True)
        else:
            o_const = cmds.orientConstraint(as_joint, ue_joint)
            cmds.setAttr(f'{o_const[0]}.offset', offset[0], offset[1], offset[2], type='float3')

        # 360도 오프셋 문제 방지
        constraint_name = f'{ue_joint}_orientConstraint1'
        if cmds.objExists(constraint_name):
            for y in range(len(XYZ)):
                ue_joint_rot = cmds.getAttr(f'{ue_joint}.r{xyz[y]}')
                ue_joint_offset = cmds.getAttr(f'{constraint_name}.offset{XYZ[y]}')

                if ue_joint_rot > 180 and ue_joint_offset > 179:
                    cmds.setAttr(f'{constraint_name}.offset{XYZ[y]}', ue_joint_offset - 360)
                if ue_joint_rot < -180 and ue_joint_offset < -179:
                    cmds.setAttr(f'{constraint_name}.offset{XYZ[y]}', ue_joint_offset + 360)
        
        # 기존 컨스트레인트 삭제 후 새로운 컨스트레인트 적용
        cmds.delete(ue_joint, cn=True)
        joint_freeze(ue_joint)
        cmds.parentConstraint(as_joint, ue_joint, mo=True)  
        cmds.scaleConstraint(as_joint, ue_joint, mo=True)
        
    except Exception as e:
        cmds.warning(f"컨스트레인트 적용 중 오류 발생: {as_joint} -> {ue_joint}, 오류: {str(e)}")


def joint_freeze(joint):
    """
    조인트의 트랜스폼을 프리즈합니다.
    
    Args:
        joint (str or list): 프리즈할 조인트 이름 또는 조인트 리스트
    """
    # 단일 조인트인 경우 리스트로 변환
    if isinstance(joint, str):
        joint = [joint]
    
    for j in joint:
        if cmds.objExists(j):
            try:
                cmds.makeIdentity(j, apply=True, t=0, r=1, s=1, n=0, pn=1)
            except Exception as e:
                cmds.warning(f"조인트 프리즈 실패: {j}, 오류: {str(e)}")
        else:
            cmds.warning(f"조인트를 찾을 수 없습니다: {j}")


def mannequin_joint_match():
    """
    Advanced Skeleton과 Unreal Engine Mannequin 조인트를 매칭합니다.
    
    Returns:
        dict: 매칭 결과와 상세 정보를 포함한 딕셔너리
            - success (bool): 매칭 성공 여부
            - message (str): 결과 메시지
            - error_details (list): 에러 상세 정보 (에러 발생시)
    """
    try:
        # 루트 조인트 매칭
        # Root_M과 pelvis 조인트 중복 확인
        root_m_nodes = cmds.ls('Root_M')
        pelvis_nodes = cmds.ls('pelvis')
        
        print(f"[조인트 검사] Root_M 조인트 발견: {len(root_m_nodes)}개 - {root_m_nodes}")
        print(f"[조인트 검사] pelvis 조인트 발견: {len(pelvis_nodes)}개 - {pelvis_nodes}")
        
        if len(root_m_nodes) > 1:
            error_msg = f"[매칭 에러] Root_M 조인트가 2개 이상 존재합니다 ({len(root_m_nodes)}개)"
            print(error_msg)
            print("[매칭 에러] 발견된 Root_M 조인트 상세 정보:")
            
            error_details = []
            for i, node in enumerate(root_m_nodes, 1):
                full_path = cmds.ls(node, long=True)[0] if cmds.ls(node, long=True) else node
                parent = cmds.listRelatives(node, parent=True)
                parent_info = f" (부모: {parent[0]})" if parent else " (부모: 없음)"
                detail = f"  {i}. {node} -> 전체경로: {full_path}{parent_info}"
                print(detail)
                error_details.append(detail)
            
            print("[매칭 에러] 중복 조인트로 인해 매칭을 중단합니다. 중복 조인트를 제거한 후 다시 시도하세요.")
            cmds.warning(f"Root_M 조인트 중복 오류: {len(root_m_nodes)}개 발견. 매칭 중단.")
            
            return {
                "success": False,
                "message": f"Root_M 조인트 중복 오류: {len(root_m_nodes)}개 발견. 매칭 중단.",
                "error_details": error_details,
                "error_type": "root_m_duplicate"
            }
        
        if len(pelvis_nodes) > 1:
            error_msg = f"[매칭 에러] pelvis 조인트가 2개 이상 존재합니다 ({len(pelvis_nodes)}개)"
            print(error_msg)
            print("[매칭 에러] 발견된 pelvis 조인트 상세 정보:")
            
            error_details = []
            for i, node in enumerate(pelvis_nodes, 1):
                full_path = cmds.ls(node, long=True)[0] if cmds.ls(node, long=True) else node
                parent = cmds.listRelatives(node, parent=True)
                parent_info = f" (부모: {parent[0]})" if parent else " (부모: 없음)"
                detail = f"  {i}. {node} -> 전체경로: {full_path}{parent_info}"
                print(detail)
                error_details.append(detail)
            
            print("[매칭 에러] 중복 조인트로 인해 매칭을 중단합니다. 중복 조인트를 제거한 후 다시 시도하세요.")
            cmds.warning(f"pelvis 조인트 중복 오류: {len(pelvis_nodes)}개 발견. 매칭 중단.")
            
            return {
                "success": False,
                "message": f"pelvis 조인트 중복 오류: {len(pelvis_nodes)}개 발견. 매칭 중단.",
                "error_details": error_details,
                "error_type": "pelvis_duplicate"
            }
        
        if len(root_m_nodes) == 0:
            error_msg = "Root_M 조인트를 찾을 수 없습니다."
            cmds.warning(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error_details": [],
                "error_type": "root_m_not_found"
            }
        if len(pelvis_nodes) == 0:
            error_msg = "pelvis 조인트를 찾을 수 없습니다."
            cmds.warning(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error_details": [],
                "error_type": "pelvis_not_found"
            }
        
        if cmds.objExists('Root_M') and cmds.objExists('pelvis'):
            print("[조인트 매칭] Root_M -> pelvis 트랜스폼 매칭 시작")
            cmds.matchTransform('pelvis', 'Root_M', pos=True)
            print("[조인트 매칭] Root_M -> pelvis 부모 컨스트레인트 적용")
            cmds.parentConstraint('Root_M', 'pelvis', mo=True)
            print("[조인트 매칭] Root_M -> pelvis 매칭 완료")
        
        # IK 핸들러 매칭
        AD_IK = ['Ankle_L', 'Ankle_R', 'Wrist_R', 'Wrist_L']    
        MQ_IK = ['ik_foot_l', 'ik_foot_r', 'ik_hand_gun', 'ik_hand_l']
        for ad, mq in zip(AD_IK, MQ_IK):
            if cmds.objExists(ad) and cmds.objExists(mq):
                cmds.matchTransform(mq, ad, pos=True)
                joint_freeze(mq)
                cmds.parentConstraint(ad, mq, mo=True)
        
        # Spine 조인트 매핑 (Advanced Skeleton -> Mannequin)
        AD_SPINE = ['Spine1_M', 'Spine2_M', 'Spine3_M', 'Spine4_M', 'Chest_M']
        MQ_SPINE = ['spine_01', 'spine_02', 'spine_03', 'spine_04', 'spine_05']
        AD_NECK = ['Neck1_M', 'Neck2_M', 'Head_M']  
        MQ_NECK = ['neck_01', 'neck_02', 'head']

        # Spine 조인트 컨스트레인트 적용
        for ad, mq in zip(AD_SPINE, MQ_SPINE):
            if cmds.objExists(ad) and cmds.objExists(mq):
                mannequin_joint_constraint(ad, mq, [0, 0], [180, 0, 0])
                
        # Neck 조인트 컨스트레인트 적용        
        for ad, mq in zip(AD_NECK, MQ_NECK):
            if cmds.objExists(ad) and cmds.objExists(mq):
                mannequin_joint_constraint(ad, mq, [0, 0], [180, 0, 0])
                    
        # 좌우 대칭 조인트 처리
        for b in range(1, -2, -2):
            if b == 1:
                SIDE = '_R'  # Advanced Skeleton 우측 접미사
                side = '_r'  # Mannequin 우측 접미사
            elif b == -1:
                SIDE = '_L'  # Advanced Skeleton 좌측 접미사
                side = '_l'  # Mannequin 좌측 접미사

            # 팔 조인트 컨스트레인트
            if cmds.objExists('Scapula' + SIDE) and cmds.objExists('clavicle' + side):
                mannequin_joint_constraint('Scapula' + SIDE, 'clavicle' + side, [0, 0], [180.0, 0.0, 180.0])
            if cmds.objExists('Shoulder' + SIDE) and cmds.objExists('upperarm' + side):
                mannequin_joint_constraint('Shoulder' + SIDE, 'upperarm' + side, [0, 0], [180.0, 0.0, 180.0])
            if cmds.objExists('ShoulderPart1' + SIDE) and cmds.objExists('upperarm_twist_01' + side):
                mannequin_joint_constraint('ShoulderPart1' + SIDE, 'upperarm_twist_01' + side, [0, 0], [0.0, -180.0, 0.0])
            if cmds.objExists('ShoulderPart2' + SIDE) and cmds.objExists('upperarm_twist_02' + side):
                mannequin_joint_constraint('ShoulderPart2' + SIDE, 'upperarm_twist_02' + side, [0, 0], [0.0, -180.0, 0.0])
            if cmds.objExists('Elbow' + SIDE) and cmds.objExists('lowerarm' + side):
                mannequin_joint_constraint('Elbow' + SIDE, 'lowerarm' + side, [0, 0], [180.0, 0.0, 180.0])
            if cmds.objExists('ElbowPart2' + SIDE) and cmds.objExists('lowerarm_twist_01' + side):
                mannequin_joint_constraint('ElbowPart2' + SIDE, 'lowerarm_twist_01' + side, [0, 0], [0.0, -180.0, 0.0])  # 언리얼 엔진에서 순서가 바뀜
            if cmds.objExists('ElbowPart1' + SIDE) and cmds.objExists('lowerarm_twist_02' + side):
                mannequin_joint_constraint('ElbowPart1' + SIDE, 'lowerarm_twist_02' + side, [0, 0], [0.0, -180.0, 0.0])
            if cmds.objExists('Wrist' + SIDE) and cmds.objExists('hand' + side):
                mannequin_joint_constraint('Wrist' + SIDE, 'hand' + side, [0, 0], [90.0, 0.0, 180.0])

            # 손가락 조인트 컨스트레인트
            for i in range(0, 4):
                if i == 0:  # metacarpal 조인트 (손바닥 뼈)
                    if cmds.objExists('PinkyFinger' + str(i) + SIDE) and cmds.objExists('pinky_metacarpal' + side):
                        mannequin_joint_constraint('PinkyFinger' + str(i) + SIDE, 'pinky_metacarpal' + side, [0, 0], [90.0, 0.0, 180.0])
                    if cmds.objExists('RingFinger' + str(i) + SIDE) and cmds.objExists('ring_metacarpal' + side):
                        mannequin_joint_constraint('RingFinger' + str(i) + SIDE, 'ring_metacarpal' + side, [0, 0], [90.0, 0.0, 180.0])
                    if cmds.objExists('MiddleFinger' + str(i) + SIDE) and cmds.objExists('middle_metacarpal' + side):
                        mannequin_joint_constraint('MiddleFinger' + str(i) + SIDE, 'middle_metacarpal' + side, [0, 0], [90.0, 0.0, 180.0])
                    if cmds.objExists('IndexFinger' + str(i) + SIDE) and cmds.objExists('index_metacarpal' + side):
                        mannequin_joint_constraint('IndexFinger' + str(i) + SIDE, 'index_metacarpal' + side, [0, 0], [90.0, 0.0, 180.0])
                else:  # 손가락 관절
                    if cmds.objExists('PinkyFinger' + str(i) + SIDE) and cmds.objExists('pinky_0' + str(i) + side):
                        mannequin_joint_constraint('PinkyFinger' + str(i) + SIDE, 'pinky_0' + str(i) + side, [0, 0], [90.0, 0.0, 180.0])
                    if cmds.objExists('RingFinger' + str(i) + SIDE) and cmds.objExists('ring_0' + str(i) + side):
                        mannequin_joint_constraint('RingFinger' + str(i) + SIDE, 'ring_0' + str(i) + side, [0, 0], [90.0, 0.0, 180.0])
                    if cmds.objExists('MiddleFinger' + str(i) + SIDE) and cmds.objExists('middle_0' + str(i) + side):
                        mannequin_joint_constraint('MiddleFinger' + str(i) + SIDE, 'middle_0' + str(i) + side, [0, 0], [90.0, 0.0, 180.0])
                    if cmds.objExists('IndexFinger' + str(i) + SIDE) and cmds.objExists('index_0' + str(i) + side):
                        mannequin_joint_constraint('IndexFinger' + str(i) + SIDE, 'index_0' + str(i) + side, [0, 0], [90.0, 0.0, 180.0])
                    if cmds.objExists('ThumbFinger' + str(i) + SIDE) and cmds.objExists('thumb_0' + str(i) + side):
                        mannequin_joint_constraint('ThumbFinger' + str(i) + SIDE, 'thumb_0' + str(i) + side, [0, 0], [90.0, 0.0, 180.0])

            # 다리 조인트 컨스트레인트
            if cmds.objExists('Hip' + SIDE) and cmds.objExists('thigh' + side):
                mannequin_joint_constraint('Hip' + SIDE, 'thigh' + side, [0, 0], [0.0, 0.0, 0.0])
            if cmds.objExists('HipPart1' + SIDE) and cmds.objExists('thigh_twist_01' + side):
                mannequin_joint_constraint('HipPart1' + SIDE, 'thigh_twist_01' + side, [0, 0], [0.0, 0.0, 0.0])
            if cmds.objExists('HipPart2' + SIDE) and cmds.objExists('thigh_twist_02' + side):
                mannequin_joint_constraint('HipPart2' + SIDE, 'thigh_twist_02' + side, [0, 0], [0.0, 0.0, 0.0])
            if cmds.objExists('Knee' + SIDE) and cmds.objExists('calf' + side):
                mannequin_joint_constraint('Knee' + SIDE, 'calf' + side, [0, 0], [0.0, 0.0, 0.0])
            if cmds.objExists('KneePart2' + SIDE) and cmds.objExists('calf_twist_01' + side):
                mannequin_joint_constraint('KneePart2' + SIDE, 'calf_twist_01' + side, [0, 0], [0.0, 0.0, 0.0])  # 언리얼 엔진에서 순서가 바뀜
            if cmds.objExists('KneePart1' + SIDE) and cmds.objExists('calf_twist_02' + side):
                mannequin_joint_constraint('KneePart1' + SIDE, 'calf_twist_02' + side, [0, 0], [0.0, 0.0, 0.0])
            if cmds.objExists('Ankle' + SIDE) and cmds.objExists('foot' + side):
                mannequin_joint_constraint('Ankle' + SIDE, 'foot' + side, [0, 0], [0.0, 0.0, 0.0])
            if cmds.objExists('Toes' + SIDE) and cmds.objExists('ball' + side):
                mannequin_joint_constraint('Toes' + SIDE, 'ball' + side, [0, 1], [0.0, 0.0, 0.0])
        
        print("Mannequin 조인트 매칭 완료")
        return {
            "success": True,
            "message": "Mannequin 조인트 매칭 완료",
            "error_details": [],
            "error_type": None
        }
        
    except Exception as e:
        error_msg = f"조인트 매칭 중 오류 발생: {str(e)}"
        cmds.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "error_details": [str(e)],
            "error_type": "exception"
        }


if __name__ == '__main__':
    # Maya에서 사용자 문서 폴더 경로를 가져오는 방법
    # cmds.internalVar(userDocumentsDir=True)     # 사용자 문서 폴더 경로
    # cmds.internalVar(userAppDir=True)           # 사용자 애플리케이션 데이터 폴더
    # cmds.internalVar(userScriptDir=True)        # 사용자 스크립트 폴더
    # cmds.internalVar(userShelfDir=True)         # 사용자 셸프 폴더
    # cmds.internalVar(userPresetsDir=True)       # 사용자 프리셋 폴더
    # cmds.internalVar(userPrefDir=True)          # 사용자 환경설정 폴더
    # cmds.internalVar(userTmpDir=True)           # 사용자 임시 폴더
    # cmds.internalVar(userWorkspaceDir=True)     # 사용자 워크스페이스 폴더
    # cmds.internalVar(userBitmapsDir=True)       # 사용자 비트맵 폴더
    # cmds.internalVar(userMarkingMenuDir=True)   # 사용자 마킹 메뉴 폴더
    # cmds.internalVar(userHotkeyDir=True)        # 사용자 핫키 폴더

    SKELETON_PATH = "C:/Users/leesk004/Documents/CustomScripts/maya/R8_MaxtoMaya/R8_Manny_Skeleton.ma" 

    # 스켈레톤 임포트 후 조인트 매칭 실행
    if import_mannequin_skeleton(skeleton_path=SKELETON_PATH):
        mannequin_joint_match()
    else:
        print("스켈레톤 임포트 실패로 인해 조인트 매칭을 건너뜁니다.")
    
    


