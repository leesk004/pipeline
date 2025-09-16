"""
웨이트 트랜스퍼 유틸리티 함수들
다른 모듈에서 쉽게 재활용할 수 있는 편의 함수들을 제공
"""

import maya.cmds as cmds
import json
import os

try:
    from R8_MaxtoMaya import R8_weight_transfer_core
    from importlib import reload
    reload(R8_weight_transfer_core)
except ImportError:
    try:
        import R8_weight_transfer_core
        from importlib import reload
        reload(R8_weight_transfer_core)
    except ImportError as e:
        print(f"R8_weight_transfer_core 모듈을 찾을 수 없습니다: {e}")
        R8_weight_transfer_core = None

def create_mapping_from_selection():
    """
    선택된 조인트들로부터 웨이트 트랜스퍼 매핑을 생성하는 편의 함수
    
    Returns:
        dict: {기존조인트: 새조인트} 형태의 매핑 딕셔너리
    """
    selection = cmds.ls(sl=True, type='joint')
    if len(selection) < 2:
        cmds.warning("최소 2개의 조인트를 선택해주세요.")
        return {}
    
    # 선택된 조인트를 절반으로 나누어 매핑 생성
    mid_point = len(selection) // 2
    old_joints = selection[:mid_point]
    new_joints = selection[mid_point:]
    
    mapping = {}
    for i in range(min(len(old_joints), len(new_joints))):
        mapping[old_joints[i]] = new_joints[i]
    
    print(f"생성된 매핑: {len(mapping)}개")
    return mapping

def create_mapping_from_name_pattern(old_pattern, new_pattern):
    """
    이름 패턴을 기반으로 매핑을 생성하는 함수
    
    Args:
        old_pattern (str): 기존 조인트 이름 패턴 (예: "Bip*")
        new_pattern (str): 새 조인트 이름 패턴 (예: "mixamorig:*")
    
    Returns:
        dict: 매핑 딕셔너리
    """
    old_joints = cmds.ls(old_pattern, type='joint')
    mapping = {}
    
    for old_joint in old_joints:
        # 패턴에서 와일드카드 부분 추출
        if '*' in old_pattern:
            prefix = old_pattern.split('*')[0]
            suffix = old_pattern.split('*')[-1] if old_pattern.count('*') == 1 else ""
            
            # 기존 조인트에서 패턴 부분 추출
            joint_core = old_joint
            if prefix:
                joint_core = joint_core.replace(prefix, "", 1)
            if suffix:
                joint_core = joint_core.replace(suffix, "")
            
            # 새 조인트 이름 생성
            new_joint = new_pattern.replace('*', joint_core)
            
            if cmds.objExists(new_joint):
                mapping[old_joint] = new_joint
    
    print(f"패턴 매핑 생성: {len(mapping)}개")
    return mapping

def quick_transfer(mesh, old_joint, new_joint):
    """
    빠른 단일 조인트 웨이트 트랜스퍼 함수
    
    Args:
        mesh (str): 메시 이름
        old_joint (str): 기존 조인트
        new_joint (str): 새 조인트
    
    Returns:
        dict: 전송 결과
    """
    if not R8_weight_transfer_core:
        cmds.error("웨이트 트랜스퍼 핵심 모듈을 사용할 수 없습니다.")
        return {"success": False, "error": "Core module not available"}
    
    mapping = {old_joint: new_joint}
    return R8_weight_transfer_core.transfer_weights_to_mapped_joints(mesh, mapping)

def batch_transfer(mesh, joint_mappings_list, progress_callback=None):
    """
    여러 매핑을 순차적으로 처리하는 배치 함수
    
    Args:
        mesh (str): 메시 이름
        joint_mappings_list (list): 매핑 딕셔너리들의 리스트
        progress_callback (callable): 진행 상황 콜백
    
    Returns:
        list: 각 매핑의 결과 리스트
    """
    if not R8_weight_transfer_core:
        cmds.error("웨이트 트랜스퍼 핵심 모듈을 사용할 수 없습니다.")
        return []
    
    results = []
    total_mappings = len(joint_mappings_list)
    
    for i, mapping in enumerate(joint_mappings_list):
        if progress_callback:
            progress = int((i / total_mappings) * 100)
            progress_callback(progress, f"매핑 {i+1}/{total_mappings} 처리 중...")
        
        print(f"Processing mapping {i+1}/{total_mappings}")
        result = R8_weight_transfer_core.transfer_weights_to_mapped_joints(mesh, mapping)
        results.append(result)
    
    if progress_callback:
        progress_callback(100, "배치 처리 완료")
    
    return results

def transfer_from_json_file(mesh, json_file_path, progress_callback=None):
    """
    JSON 파일에서 매핑을 로드하여 웨이트 트랜스퍼 실행
    
    Args:
        mesh (str): 메시 이름
        json_file_path (str): JSON 파일 경로
        progress_callback (callable): 진행 상황 콜백
    
    Returns:
        dict: 전송 결과
    """
    if not R8_weight_transfer_core:
        cmds.error("웨이트 트랜스퍼 핵심 모듈을 사용할 수 없습니다.")
        return {"success": False, "error": "Core module not available"}
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            joint_mapping = json.load(f)
        
        if not isinstance(joint_mapping, dict):
            return {"success": False, "error": "Invalid JSON format"}
        
        print(f"JSON에서 {len(joint_mapping)}개 매핑 로드됨: {json_file_path}")
        return R8_weight_transfer_core.transfer_weights_to_mapped_joints(
            mesh, joint_mapping, progress_callback
        )
        
    except Exception as e:
        error_msg = f"JSON 파일 처리 중 오류: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}

def save_mapping_to_json(joint_mapping, file_path):
    """
    조인트 매핑을 JSON 파일로 저장
    
    Args:
        joint_mapping (dict): 조인트 매핑 딕셔너리
        file_path (str): 저장할 파일 경로
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(joint_mapping, f, indent=4, ensure_ascii=False)
        
        print(f"매핑이 저장되었습니다: {file_path}")
        return True
        
    except Exception as e:
        print(f"JSON 저장 중 오류: {str(e)}")
        return False

def load_mapping_from_json(file_path):
    """
    JSON 파일에서 조인트 매핑 로드
    
    Args:
        file_path (str): JSON 파일 경로
    
    Returns:
        dict: 조인트 매핑 딕셔너리 또는 빈 딕셔너리
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            joint_mapping = json.load(f)
        
        if not isinstance(joint_mapping, dict):
            print("유효하지 않은 JSON 형식입니다.")
            return {}
        
        print(f"매핑이 로드되었습니다: {file_path} ({len(joint_mapping)}개)")
        return joint_mapping
        
    except Exception as e:
        print(f"JSON 로드 중 오류: {str(e)}")
        return {}

def validate_mesh_for_transfer(mesh):
    """
    메시가 웨이트 트랜스퍼에 적합한지 검증
    
    Args:
        mesh (str): 메시 이름
    
    Returns:
        dict: 검증 결과
    """
    result = {
        "valid": False,
        "mesh_exists": False,
        "has_skin_cluster": False,
        "skin_cluster": None,
        "influences": [],
        "errors": []
    }
    
    # 메시 존재 확인
    if not cmds.objExists(mesh):
        result["errors"].append(f"메시 '{mesh}'가 존재하지 않습니다.")
        return result
    
    result["mesh_exists"] = True
    
    # 메시 타입 확인
    if not cmds.listRelatives(mesh, shapes=True):
        result["errors"].append(f"'{mesh}'는 메시가 아닙니다.")
        return result
    
    # 스킨 클러스터 확인
    if R8_weight_transfer_core:
        skin_cluster = R8_weight_transfer_core.get_skin_cluster(mesh)
        if skin_cluster:
            result["has_skin_cluster"] = True
            result["skin_cluster"] = skin_cluster
            
            # 인플루언스 조인트 확인
            try:
                influences = cmds.skinCluster(skin_cluster, query=True, influence=True)
                result["influences"] = influences or []
                result["valid"] = True
            except:
                result["errors"].append("스킨 클러스터 정보를 읽을 수 없습니다.")
        else:
            result["errors"].append(f"메시 '{mesh}'에 스킨 클러스터가 없습니다.")
    else:
        result["errors"].append("웨이트 트랜스퍼 핵심 모듈을 사용할 수 없습니다.")
    
    return result

def get_skin_cluster_info(mesh):
    """
    메시의 스킨 클러스터 정보를 반환
    
    Args:
        mesh (str): 메시 이름
    
    Returns:
        dict: 스킨 클러스터 정보
    """
    info = {
        "skin_cluster": None,
        "influences": [],
        "vertex_count": 0,
        "max_influences": 0
    }
    
    if not R8_weight_transfer_core:
        return info
    
    skin_cluster = R8_weight_transfer_core.get_skin_cluster(mesh)
    if skin_cluster:
        info["skin_cluster"] = skin_cluster
        
        try:
            influences = cmds.skinCluster(skin_cluster, query=True, influence=True)
            info["influences"] = influences or []
            
            vertex_count = cmds.polyEvaluate(mesh, vertex=True)
            info["vertex_count"] = vertex_count or 0
            
            max_influences = cmds.skinCluster(skin_cluster, query=True, maximumInfluences=True)
            info["max_influences"] = max_influences or 0
            
        except Exception as e:
            print(f"스킨 클러스터 정보 수집 중 오류: {str(e)}")
    
    return info

def print_mapping_summary(joint_mapping):
    """
    조인트 매핑 요약 정보를 출력
    
    Args:
        joint_mapping (dict): 조인트 매핑 딕셔너리
    """
    print(f"\n=== 조인트 매핑 요약 ===")
    print(f"총 매핑 개수: {len(joint_mapping)}")
    
    if R8_weight_transfer_core:
        validation = R8_weight_transfer_core.validate_joint_mapping(joint_mapping)
        print(f"유효한 매핑: {len(validation['valid_mappings'])}")
        print(f"누락된 기존 조인트: {len(validation['missing_old_joints'])}")
        print(f"누락된 새 조인트: {len(validation['missing_new_joints'])}")
        print(f"추가 필요한 새 조인트: {len(validation['new_joints_to_add'])}")
        
        if validation['missing_old_joints']:
            print(f"누락된 기존 조인트: {validation['missing_old_joints'][:5]}...")
        if validation['missing_new_joints']:
            print(f"누락된 새 조인트: {validation['missing_new_joints'][:5]}...")
    
    print("=" * 30)

# 편의 함수들을 위한 별칭
create_mapping = create_mapping_from_selection
transfer_weights = quick_transfer
validate_mapping = lambda mapping: R8_weight_transfer_core.validate_joint_mapping(mapping) if R8_weight_transfer_core else {} 