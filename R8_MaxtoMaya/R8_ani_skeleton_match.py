from maya import cmds
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

SKEL_SET = 'Skeleton_Set'
BAKE_CTRL_SET = 'Bake_Control_Set'
contList = []  # 전역 변수 초기화


def joint_segment_scale(root_joint, val=1):
    try:    
        all_joints = cmds.ls(root_joint, dag=True, type='joint')
        for jnt in all_joints:
            cmds.setAttr(f'{jnt}.segmentScaleCompensate', val)
    except Exception as e:
        logger.error(f"조인트 세그먼트 스케일 설정 중 오류: {e}")
        return False
    return True
            
def skeleton_bindpose(selectObjects, prefix):
    """
    선택된 객체들을 바인드 포즈로 설정합니다.
    
    Args:
        selectObjects (list): 설정할 객체 리스트
        prefix (str): 네임스페이스 프리픽스
    """
    if not selectObjects or not prefix:
        logger.warning("객체 리스트 또는 프리픽스가 비어있습니다.")
        return
        
    cmds.playbackOptions(min=-10)
    cmds.currentTime(-10)        
    for obj in selectObjects:
        target_obj = f'{prefix}:{obj}'
        if cmds.objExists(target_obj):
            if obj == 'Root':
                continue
            
            for ax in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                try:
                    # 원본 객체의 속성값 가져오기
                    if cmds.objExists(obj) and cmds.attributeQuery(ax, node=obj, exists=True):
                        tv = cmds.getAttr(f'{obj}.{ax}')
                        # 타겟 객체에 속성이 존재하고 설정 가능한지 확인
                        if cmds.attributeQuery(ax, node=target_obj, exists=True) and not cmds.getAttr(f'{target_obj}.{ax}', lock=True):
                            cmds.setAttr(f'{target_obj}.{ax}', tv)
                            cmds.setKeyframe(f'{target_obj}.{ax}')
                except Exception as e:
                    logger.error(f"속성 {obj}.{ax} 처리 중 오류: {e}")
                    continue
    
def get_colon_prefixes():
    """
    씬 안에 있는 모든 콜론(:) 프리픽스 네임스페이스를 반환합니다.
    
    Returns:
        list: 프리픽스 리스트
    """
    try:
        all_objects = cmds.ls()
        prefixes = set()

        for obj in all_objects:
            name_parts = obj.split(':')
            if len(name_parts) > 1:
                prefixes.add(name_parts[0])

        return sorted(list(prefixes))  # 정렬된 리스트로 반환
    except Exception as e:
        logger.error(f"프리픽스 가져오기 중 오류: {e}")
        return []

def bake_animation(controls, startFrame, endFrame):
    """
    지정된 컨트롤들에 애니메이션을 베이킹합니다.
    
    Args:
        controls (list): 베이킹할 컨트롤 리스트
        startFrame (int): 시작 프레임
        endFrame (int): 끝 프레임
    """
    if not controls:
        logger.warning("베이킹할 컨트롤이 없습니다.")
        return
        
    # 프레임 값 안전 처리
    try:
        startFrame = int(startFrame) if startFrame is not None else 0
        endFrame = int(endFrame) if endFrame is not None else 100
        
        # 존재하는 컨트롤만 필터링
        valid_controls = [ctrl for ctrl in controls if cmds.objExists(ctrl)]
        if not valid_controls:
            logger.warning("유효한 컨트롤이 없습니다.")
            return
            
        logger.info(f"베이킹 실행: 컨트롤 {len(valid_controls)}개, 프레임 {startFrame}-{endFrame}")
        
        cmds.bakeResults(valid_controls, simulation=True, t=(startFrame, endFrame),
                         sampleBy=1, oversamplingRate=1, disableImplicitControl=True,
                         preserveOutsideKeys=True, sparseAnimCurveBake=False, 
                         removeBakedAttributeFromLayer=False,
                         removeBakedAnimFromLayer=False, bakeOnOverrideLayer=False, 
                         minimizeRotation=True, controlPoints=False, shape=True)
        
        logger.info("베이킹 완료")
        
    except Exception as e:
        logger.error(f"베이킹 중 오류 발생: {e}")
        raise

def joint_exists(joints, prefix):
    """
    주어진 프리픽스를 가진 조인트들이 존재하는지 확인합니다.
    
    Args:
        joints (list): 확인할 조인트 리스트
        prefix (str): 프리픽스
        
    Returns:
        list: 존재하는 조인트 리스트
    """
    joint_list = []
    if not joints or not prefix:
        return joint_list
        
    for jnt in joints:
        full_joint_name = f'{prefix}:{jnt}'
        if cmds.objExists(full_joint_name):
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
    
    try:
        # 씬의 모든 객체를 검색
        all_objects = cmds.ls(type='transform')
        
        for obj in all_objects:
            # 객체에 지정된 속성이 존재하는지 확인
            if cmds.attributeQuery(attrName, node=obj, exists=True):
                controllers_with_fkik.append(obj)
        
        if controllers_with_fkik:
            logger.info(f"{attrName} 속성을 가진 컨트롤러들: {controllers_with_fkik}")
        else:
            logger.info(f"{attrName} 속성을 가진 컨트롤러를 찾을 수 없습니다.")
            
    except Exception as e:
        logger.error(f"IK/FK 컨트롤 검색 중 오류: {e}")
    
    return controllers_with_fkik
    
def main_controller_move(prefix):
    """
    루트 조인트의 위치를 확인하여 MainExtra2 값을 이동합니다.
    
    Args:
        prefix (str): 네임스페이스 프리픽스
    """
    root_joint = f'{prefix}:Root'
    if cmds.objExists(root_joint):
        try:
            root_transX = cmds.getAttr(f'{root_joint}.tx')
            root_transY = cmds.getAttr(f'{root_joint}.ty')
            root_transZ = cmds.getAttr(f'{root_joint}.tz')
            
            if any([root_transX, root_transY, root_transZ]) and cmds.objExists('MainExtra2'):
                cmds.move(root_transX, root_transY, root_transZ, 'MainExtra2')
                logger.info(f"MainExtra2를 ({root_transX}, {root_transY}, {root_transZ})로 이동")
        except Exception as e:
            logger.error(f"MainExtra2 이동 중 오류: {e}")
                
def skeleton_control_match(frontAxis='frontX'):
    """
    스켈레톤과 컨트롤을 매칭하고 컨스트레인을 설정합니다.
    
    Args:
        frontAxis (str): 정면 축 방향 ('frontX' 또는 'frontZ')
        
    Returns:
        bool: 성공시 True, 실패시 False
    """
    # Undo 블록 시작
    cmds.undoInfo(openChunk=True)
    # 현재 타임라인의 시작 프레임과 마지막 프레임 가져오기
    current_start_frame = cmds.playbackOptions(query=True, minTime=True)
    current_end_frame = cmds.playbackOptions(query=True, maxTime=True)
    
    try:
        # IK/FK 컨트롤 설정
        ik_fk_controls = ik_fk_control_blend()
        if ik_fk_controls:
            logger.info(f"IK/FK 컨트롤러들: {ik_fk_controls}")
            for cont in ik_fk_controls:
                if cmds.objExists(cont) and cmds.attributeQuery('FKIKBlend', node=cont, exists=True):
                    cmds.setAttr(cont + '.FKIKBlend', 0)
        else:
            logger.info("IK/FK 컨트롤러를 찾을 수 없습니다.")
        
        global contList
        contList = []  # 함수 시작 시 초기화
        
        # 모든 콜론 프리픽스를 가져옵니다.
        prefixes = get_colon_prefixes()
        if not prefixes:
            logger.error("프리픽스가 있는 객체를 찾을 수 없습니다.")
            return False
            
        prefix = prefixes[0]  # 안전하게 첫 번째 요소 접근
        logger.info(f"사용할 프리픽스: {prefix}")
        
        main_controller_move(prefix)
        
        try:
            set_node = SKEL_SET
            if not cmds.objExists(set_node):
                logger.error(f"셋 '{set_node}'이 존재하지 않습니다.")
                return False
                
            members = cmds.sets(set_node, q=True) 
            if not members:
                logger.error(f"셋 '{set_node}'이 비어있습니다.")
                return False
                
            selectObjects = joint_exists(members, prefix)
            if not selectObjects:
                logger.error("매칭되는 조인트를 찾을 수 없습니다.")
                return False
                
            cmds.select(clear=True)
            if not cmds.objExists('root_grp'):
                cmds.group(em=True, name='root_grp')
                
            # Root 객체가 존재하는지 확인
            root_obj = f'{prefix}:Root'
            if cmds.objExists(root_obj):
                if not cmds.listRelatives(root_obj, p=True):
                    cmds.parent(root_obj, 'root_grp')
            else:
                logger.warning(f"{root_obj} 객체가 존재하지 않습니다.")
                
            # 축 방향 설정
            if frontAxis == 'frontX':
                if cmds.objExists('MainExtra2'):
                    cmds.setAttr('MainExtra2.rotateY', 90)
                cmds.setAttr('root_grp.rotateY', 0)
            else:
                if cmds.objExists('MainExtra2'):
                    cmds.setAttr('MainExtra2.rotateY', 0)
                cmds.setAttr('root_grp.rotateY', -90)   
            
            skeleton_bindpose(selectObjects, prefix)
            if cmds.objExists(f'{prefix}:Root'):
                joint_segment_scale(f'{prefix}:Root', val=1)
                
        except Exception as e:
            logger.error(f'셋업 중 오류가 발생했습니다. {e}')
            return False

        aniJointList = []

        for obj in selectObjects:
            try:
                if cmds.objExists(obj):
                    parent_constraints = cmds.listConnections(obj, type='parentConstraint')
                    if not parent_constraints:
                        continue
                    
                    logger.info(f"처리 중인 제약: {parent_constraints[0]}")
                    target_loc = cmds.parentConstraint(parent_constraints[0], query=True, targetList=True)
                    
                    if target_loc:
                        # Check if the rotate attribute is connected
                        try:
                            rotate_connections = cmds.listConnections(target_loc[0] + '.rotate')
                            rotate_locator = None  # 초기화
                            
                            if rotate_connections:
                                for cont in rotate_connections:
                                    if cmds.objExists(cont):
                                        cont_shape = cmds.listRelatives(cont, children=True)
                                        if cont_shape:
                                            # cont_shape가 리스트일 수 있으므로 첫 번째 요소 확인
                                            shape_node = cont_shape[0] if isinstance(cont_shape, list) else cont_shape
                                            if cmds.nodeType(shape_node) == 'locator':
                                                rotate_locator = cont
                                                break  # 찾으면 루프 종료
            
                                if rotate_locator:
                                    aniJoint = f'{prefix}:{obj}'
                                    if cmds.objExists(aniJoint):
                                        aniJointList.append(aniJoint)    
                                    locCon = rotate_locator
                                    grp_name = f'{locCon}_grp'
                                    if cmds.objExists(grp_name):
                                        parent_grp = cmds.listRelatives(grp_name, parent=True)
                                        if parent_grp:
                                            contList.append(parent_grp[0])
                        except Exception as e:
                            logger.error(f"객체 {obj}의 rotate 연결 확인 중 오류: {e}")
                            continue
            except Exception as e:
                logger.error(f"객체 {obj} 처리 중 오류: {e}")
                continue
                    
        if contList:
            # 새로운 셋 생성
            set_name = BAKE_CTRL_SET
            # 기존 'Bake_Control_Set' 이 있으면 지우기
            if cmds.objExists(set_name):
                cmds.delete(set_name)
            cmds.sets(contList, name=set_name)  
            cmds.select(clear=True)  
            
            # Key가 들어간 드라이브 조인트, 드리븐 컨트롤러 컨스트레인 연결     
            for j, c in zip(aniJointList, contList):
                try:
                    if not cmds.objExists(c):
                        logger.warning(f"컨트롤러 {c}가 존재하지 않습니다. 건너뜁니다.")
                        continue
                    
                    # 기존 로케이터와 그룹이 있는지 확인하고 삭제
                    ctl_loc_name = f'{c}_ctl'
                    ctl_grp_name = f'{ctl_loc_name}_grp'
                    
                    # 하드코딩된 'RootX_M' 대신 동적으로 처리하도록 수정 (이 부분은 주석 처리)
                    # 기존 컨스트레인 정리 로직을 개선할 필요가 있음
                    
                    # 기존 로케이터 그룹 삭제 (조인트의 자식으로 있는 경우)
                    if cmds.objExists(j):
                        joint_children = cmds.listRelatives(j, children=True, type='transform')
                        if joint_children:
                            for child in joint_children:
                                if child.endswith('_ctl_grp'):
                                    try:
                                        cmds.delete(child)
                                    except Exception as e:
                                        logger.error(f"기존 로케이터 그룹 {child} 삭제 중 오류: {e}")
                    
                    # 씬에서 기존 로케이터와 그룹 삭제
                    if cmds.objExists(ctl_grp_name):
                        cmds.delete(ctl_grp_name)
                    
                    if cmds.objExists(ctl_loc_name):
                        cmds.delete(ctl_loc_name)
                    
                    # 로테이트 오더 가져오기
                    if cmds.attributeQuery('rotateOrder', node=c, exists=True):
                        c_ro = cmds.getAttr(f'{c}.rotateOrder')
                    else:
                        c_ro = 0  # 기본값
                        
                    ctlLoc = cmds.spaceLocator(p=(0, 0, 0), name=ctl_loc_name)
                    cmds.setAttr(f'{ctlLoc[0]}.rotateOrder', c_ro)
                    ctlLocGrp = cmds.group(em=True, name=ctl_grp_name)
                    cmds.parent(ctlLoc, ctlLocGrp)
                    cmds.delete(cmds.pointConstraint(c, ctlLocGrp, mo=False))
                    cmds.delete(cmds.orientConstraint(c, ctlLocGrp, mo=False))
                    cmds.parent(ctlLocGrp, j)
                    cmds.select(clear=True)
                    
                    # 속성 존재 여부 확인 후 컨스트레인 생성
                    try:
                        if (cmds.attributeQuery('tx', node=c, exists=True) and 
                            cmds.getAttr(c + '.tx', keyable=True) and 
                            not cmds.getAttr(c + '.tx', lock=True)):
                            cmds.parentConstraint(ctlLoc, c, mo=True)
                    except Exception as e:
                        logger.error(f"Parent constraint 생성 실패: {e}")
                        
                    try:          
                        if (cmds.attributeQuery('sx', node=c, exists=True) and 
                            cmds.getAttr(c + '.sx', keyable=True) and 
                            not cmds.getAttr(c + '.sx', lock=True)):
                            cmds.scaleConstraint(ctlLoc, c, mo=True)
                    except Exception as e:
                        logger.error(f"Scale constraint 생성 실패: {e}")
                        
                except Exception as e:
                    logger.error(f"컨트롤러 {c} 처리 중 오류 발생: {str(e)}")
                    continue
        else:
            logger.warning("처리할 컨트롤 리스트가 비어있습니다.")
            return False
    
    except Exception as e:
        logger.error(f"skeleton_control_match 실행 중 오류 발생: {e}")
        raise
    
    finally:
        # 현재 타임라인 프레임 범위를 다시 적용
        cmds.playbackOptions(minTime=current_start_frame, maxTime=current_end_frame)
        # Undo 블록 종료
        cmds.undoInfo(closeChunk=True)
        return True

def control_bake():
    """
    Bake_Control_Set에 있는 컨트롤들에 애니메이션을 베이킹합니다.
    
    Returns:
        bool: 성공시 True, 실패시 False
    """
    global contList
    
    try:
        # Bake_Control_Set에서 컨트롤 리스트 가져오기
        if cmds.objExists(BAKE_CTRL_SET):
            bake_controls = cmds.sets(BAKE_CTRL_SET, q=True)
            if bake_controls:
                contList = bake_controls
            else:
                logger.error(f"'{BAKE_CTRL_SET}' 세트가 비어있습니다.")
                return False
        else:
            logger.error(f"'{BAKE_CTRL_SET}' 세트가 존재하지 않습니다.")
            return False
        
        if not contList:
            logger.error("베이킹할 컨트롤 리스트가 비어있습니다.")
            return False
        
        # 타임라인 범위 가져오기
        startFrame = cmds.playbackOptions(q=True, minTime=True)
        endFrame = cmds.playbackOptions(q=True, maxTime=True)
        
        bake_animation(contList, startFrame, endFrame)
        return True
        
    except Exception as e:
        logger.error(f"컨트롤 베이킹 중 오류 발생: {e}")
        return False
           
def delete_constraint(controllers):
    """
    지정된 컨트롤러들에 연결된 제약 노드들을 삭제합니다.
    
    Args:
        controllers (list): 제약을 삭제할 컨트롤러 리스트
    """
    if not controllers:
        logger.warning("삭제할 컨트롤러 리스트가 비어있습니다.")
        return
        
    try:
        for cont in controllers:
            if not cmds.objExists(cont):
                logger.warning(f"컨트롤러 {cont}가 존재하지 않습니다.")
                continue
                
            # 객체에 연결된 모든 제약 노드 찾기
            constraints = cmds.listConnections(cont, d=False, s=True, type='constraint')
            if constraints:
                # 중복 제거 및 실제 존재하는 제약만 필터링
                unique_constraints = list(set(constraints))
                valid_constraints = [const for const in unique_constraints if cmds.objExists(const)]
                
                if valid_constraints:
                    for constraint in valid_constraints:
                        try:
                            cmds.delete(constraint)
                        except Exception as e:
                            logger.error(f"제약 {constraint} 삭제 중 오류: {e}")
                    logger.info(f"{cont}에 연결된 제약 노드가 삭제되었습니다.")
                else:
                    logger.info(f"{cont}에 연결된 유효한 제약 노드가 없습니다.")
            else:
                logger.info(f"{cont}에 연결된 제약 노드가 없습니다.")
            
    except Exception as e:
        logger.error(f"제약 노드 삭제 중 오류 발생: {e}")         

def delete_key_control(controllers):
    """
    지정된 컨트롤러들의 키프레임을 삭제하고 기본값으로 리셋합니다.
    
    Args:
        controllers (list): 키프레임을 삭제할 컨트롤러 리스트
    """
    if not controllers:
        logger.warning("키프레임을 삭제할 컨트롤러 리스트가 비어있습니다.")
        return
        
    transform_attrs = ['translateX', 'translateY', 'translateZ', 
                      'rotateX', 'rotateY', 'rotateZ']
    scale_attrs = ['scaleX', 'scaleY', 'scaleZ']
    
    try:
        for cont in controllers:
            if not cmds.objExists(cont):
                logger.warning(f"컨트롤러 {cont}가 존재하지 않습니다.")
                continue
                
            try:
                attributes = cmds.listAttr(cont, keyable=True)
                if not attributes:
                    continue
                    
                # 각 속성에 대해 키프레임 확인 및 삭제
                for attr in attributes:
                    attr_full_name = f'{cont}.{attr}'
                    try:
                        # 키프레임이 있는지 확인
                        keyframes = cmds.keyframe(attr_full_name, query=True)
                        if keyframes:
                            cmds.cutKey(attr_full_name)

                        # 속성이 잠겨있지 않은 경우에만 기본값 설정
                        if not cmds.getAttr(attr_full_name, lock=True):
                            if attr in transform_attrs:
                                cmds.setAttr(attr_full_name, 0)
                            elif attr in scale_attrs:
                                cmds.setAttr(attr_full_name, 1)
                    except Exception as e:
                        logger.error(f"속성 {attr_full_name} 처리 중 오류: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"컨트롤러 {cont} 처리 중 오류: {e}")
                continue
                                        
    except Exception as e:
        logger.error(f"키프레임 삭제 중 오류가 발생했습니다: {e}")
                    
if __name__ == '__main__':
    try:
        if skeleton_control_match():
            control_bake()
            logger.info("스켈레톤 매칭 및 베이킹이 완료되었습니다.")
        else:
            logger.error("스켈레톤 매칭에 실패했습니다.")
    except Exception as e:
        logger.error(f"메인 실행 중 오류 발생: {e}")
