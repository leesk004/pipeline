from maya import cmds
import re
import logging

# 로깅 설정 - Maya 환경에서 로그 메시지를 출력하기 위한 설정
# INFO 레벨 이상의 로그만 출력하며, 시간, 로그 레벨, 메시지 형식으로 표시
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def helper_bone_vis(root_joint='pelvis', helper_patterns=None, toggle_mode=True, target_visibility=None):
    """
    헬퍼 본의 가시성을 토글하거나 설정하는 함수
    
    Args:
        root_joint (str): 루트 조인트 이름 (기본값: 'pelvis')
        helper_patterns (list): 헬퍼 본 패턴 리스트 (기본값: None - 내장 패턴 사용)
        toggle_mode (bool): True면 토글, False면 target_visibility 값으로 설정
        target_visibility (bool): toggle_mode가 False일 때 설정할 가시성 값
    
    Returns:
        dict: 처리 결과 정보
    """
    # 기본 헬퍼 본 패턴들
    default_patterns = [
        'correctiveRoot',
        'latissimus',
        'clavicle_pec',
        'clavicle_out', 
        'clavicle_scap',
        'twistCor',
        'tricep',
        'bicep',
        'wrist_inner',
        'wrist_outer',
        'ankle_bck',
        'ankle_fwd'
    ]
    
    # 헬퍼 본 패턴 설정
    # 사용자가 custom 패턴을 제공했으면 그것을 사용하고, 없으면 기본 패턴 사용
    patterns = helper_patterns if helper_patterns else default_patterns
    
    # 정규식 패턴 생성 - 여러 패턴을 OR 조건으로 결합
    # 예: 'correctiveRoot|latissimus|clavicle_pec|...' 형태로 생성
    vis_pattern = '|'.join(patterns)
    
    # 함수 실행 결과를 저장할 딕셔너리 초기화
    result = {
        'success': False,           # 전체 작업 성공 여부
        'processed_joints': [],     # 성공적으로 처리된 조인트 목록
        'skipped_joints': [],       # 건너뛴 조인트 목록 (오류나 조건 불만족)
        'errors': []               # 발생한 오류 메시지 목록
    }
    
    try:
        # 루트 조인트 존재 확인
        if not cmds.objExists(root_joint):
            error_msg = f"루트 조인트 '{root_joint}'가 존재하지 않습니다."
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
        
        # 조인트 타입 확인
        if cmds.nodeType(root_joint) != 'joint':
            error_msg = f"'{root_joint}'는 조인트가 아닙니다."
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
        
        # 조인트 계층구조 가져오기
        joint_hierarchy = cmds.ls(root_joint, type='joint', dag=True, long=True)
        
        if not joint_hierarchy:
            error_msg = f"'{root_joint}' 하위에 조인트가 없습니다."
            logger.warning(error_msg)
            result['errors'].append(error_msg)
            return result
        
        logger.info(f"총 {len(joint_hierarchy)}개의 조인트를 검사합니다.")
        
        # 각 조인트 처리
        for jnt in joint_hierarchy:
            try:
                # 짧은 이름으로 패턴 매칭
                short_name = jnt.split('|')[-1]
                
                if re.search(vis_pattern, short_name):
                    # 현재 가시성 상태 확인
                    if not cmds.attributeQuery('visibility', node=jnt, exists=True):
                        result['skipped_joints'].append(f"{short_name} (visibility 속성 없음)")
                        continue
                    
                    current_vis = cmds.getAttr(jnt + '.visibility')
                    
                    # 새로운 가시성 값 결정
                    if toggle_mode:
                        new_vis = not current_vis
                    else:
                        new_vis = target_visibility if target_visibility is not None else current_vis
                    
                    # 가시성 설정
                    if current_vis != new_vis:
                        cmds.setAttr(jnt + '.visibility', new_vis)
                        result['processed_joints'].append({
                            'joint': short_name,
                            'previous': current_vis,
                            'current': new_vis
                        })
                        logger.info(f"'{short_name}' 가시성: {current_vis} -> {new_vis}")
                    else:
                        result['skipped_joints'].append(f"{short_name} (이미 원하는 상태)")
                        
            except Exception as joint_error:
                error_msg = f"조인트 '{jnt}' 처리 중 오류: {str(joint_error)}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                continue
        
        # 결과 요약
        processed_count = len(result['processed_joints'])
        skipped_count = len(result['skipped_joints'])
        error_count = len(result['errors'])
        
        if processed_count > 0:
            result['success'] = True
            logger.info(f"완료: {processed_count}개 처리, {skipped_count}개 건너뜀, {error_count}개 오류")
        else:
            logger.warning("처리된 조인트가 없습니다.")
            
    except Exception as e:
        error_msg = f"전체 처리 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        result['errors'].append(error_msg)
    
    return result

def show_helper_bones(root_joint='pelvis', helper_patterns=None):
    """헬퍼 본을 보이게 설정"""
    return helper_bone_vis(root_joint, helper_patterns, toggle_mode=False, target_visibility=True)

def hide_helper_bones(root_joint='pelvis', helper_patterns=None):
    """헬퍼 본을 숨기게 설정"""
    return helper_bone_vis(root_joint, helper_patterns, toggle_mode=False, target_visibility=False)

def toggle_helper_bones(root_joint='pelvis', helper_patterns=None):
    """헬퍼 본 가시성을 토글"""
    return helper_bone_vis(root_joint, helper_patterns, toggle_mode=True)

def toggle_helper_vis(root_joint):
    result = toggle_helper_bones(root_joint)
    # 결과 출력
    if result['success']:
        print(f"성공적으로 {len(result['processed_joints'])}개의 헬퍼 본을 처리했습니다.")
        for joint_info in result['processed_joints']:
            print(f"  - {joint_info['joint']}: {joint_info['previous']} -> {joint_info['current']}")
    else:
        print("처리 중 문제가 발생했습니다:")
        for error in result['errors']:
            print(f"  - {error}")
            
if __name__ == "__main__":
    toggle_helper_vis('pelvis')
