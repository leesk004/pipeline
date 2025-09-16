"""
웨이트 트랜스퍼 핵심 기능 모듈
다른 UI에서 재활용할 수 있도록 분리된 모듈
"""

import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as om2Anim
import maya.cmds as cmds

def get_skin_cluster(mesh):
    """메시의 스킨 클러스터를 찾아 반환"""
    history = cmds.listHistory(mesh, pruneDagObjects=True)
    skin_clusters = cmds.ls(history, type='skinCluster')
    return skin_clusters[0] if skin_clusters else None

def get_short_name(full_name):
    """전체 경로에서 짧은 이름만 추출"""
    return full_name.split('|')[-1]

def add_joints_to_skin_cluster(mesh_name, new_joints):
    """새 조인트들을 스킨 클러스터에 추가하는 함수"""
    try:
        # 기존 스킨 클러스터 확인
        history = cmds.listHistory(mesh_name, pruneDagObjects=True)
        skin_clusters = cmds.ls(history, type='skinCluster')
        
        if skin_clusters:
            # 기존 스킨 클러스터에 조인트 추가
            skin_cluster = skin_clusters[0]
            print(f"기존 스킨 클러스터 발견: {skin_cluster}")
            
            # 이미 바인딩된 조인트들 확인
            existing_influences = cmds.skinCluster(skin_cluster, query=True, influence=True)
            joints_to_add = []
            
            for joint in new_joints:
                if joint not in existing_influences:
                    joints_to_add.append(joint)
            
            if joints_to_add:
                cmds.select(joints_to_add, mesh_name, r=True)
                cmds.skinCluster(skin_cluster, edit=True, addInfluence=joints_to_add, weight=0.0)
                print(f"조인트 추가됨: {joints_to_add}")
            else:
                print("모든 새 조인트가 이미 스킨 클러스터에 바인딩되어 있습니다.")
            
        else:
            # 새 스킨 클러스터 생성
            print("기존 스킨 클러스터가 없어 새로 생성합니다.")
            cmds.select(new_joints, mesh_name, r=True)
            skin_cluster = cmds.skinCluster(
                toSelectedBones=True,
                bindMethod=0,
                skinMethod=0,
                normalizeWeights=1,
                maximumInfluences=4,
                dropoffRate=4.0
            )[0]
            print(f"새 스킨 클러스터 생성됨: {skin_cluster}")
        
        cmds.select(clear=True)
        
    except Exception as e:
        print(f"조인트 추가 중 오류: {str(e)}")
        raise e

def transfer_weights_api(mesh, skin_cluster, joint_mapping, progress_callback=None):
    """OpenMaya 2.0 API를 사용한 효율적인 웨이트 전송"""
    
    # 진행 상황 업데이트 (5%)
    if progress_callback:
        progress_callback(5, "메시 및 스킨 클러스터 정보 가져오는 중...")
    
    # Maya API를 위한 Selection list 생성하여 메시와 스킨 클러스터 추가
    sel = om2.MSelectionList()
    sel.add(mesh)
    sel.add(skin_cluster)
    
    # 메시의 DAG 경로와 스킨 클러스터 오브젝트 얻기
    mesh_dag = sel.getDagPath(0)
    skin_obj = sel.getDependNode(1)
    
    # 스킨 클러스터 함수 세트 생성
    skin_fn = om2Anim.MFnSkinCluster(skin_obj)
    
    # 진행 상황 업데이트 (10%)
    if progress_callback:
        progress_callback(10, "인플루언스 정보 분석 중...")
    
    # 스킨 클러스터의 모든 인플루언스(조인트) 정보 가져오기
    influences = skin_fn.influenceObjects()
    influence_names = [influences[i].partialPathName() for i in range(len(influences))]
    
    # 디버그 출력: 현재 스킨 클러스터의 조인트들과 요청된 매핑 출력
    print(f"\nInfluences in skin cluster: {influence_names}")
    print(f"Joint mapping requested: {joint_mapping}")
    
    # 진행 상황 업데이트 (15%)
    if progress_callback:
        progress_callback(15, "조인트 이름 매핑 테이블 생성 중...")
    
    # 조인트 이름과 인덱스를 매핑하는 딕셔너리 생성 (전체 경로명과 짧은 이름 모두 고려)
    influence_index_map = {}
    for idx, name in enumerate(influence_names):
        # 전체 경로명으로 매핑
        influence_index_map[name] = idx
        # 짧은 이름(마지막 부분)으로도 매핑 추가
        short_name = get_short_name(name)
        influence_index_map[short_name] = idx
    
    # 진행 상황 업데이트 (20%)
    if progress_callback:
        progress_callback(20, "조인트 매핑 인덱스 생성 중...")
    
    # 기존 조인트와 새 조인트의 인덱스 매핑 딕셔너리 생성
    index_mapping = {}
    for old_joint, new_joint in joint_mapping.items():
        old_idx = None  # 기존 조인트의 인덱스
        new_idx = None  # 새 조인트의 인덱스
        
        # 기존 조인트 인덱스 찾기 (전체 경로나 짧은 이름으로)
        if old_joint in influence_index_map:
            old_idx = influence_index_map[old_joint]
        elif get_short_name(old_joint) in influence_index_map:
            old_idx = influence_index_map[get_short_name(old_joint)]
        
        # 새 조인트 인덱스 찾기 (전체 경로나 짧은 이름으로)    
        if new_joint in influence_index_map:
            new_idx = influence_index_map[new_joint]
        elif get_short_name(new_joint) in influence_index_map:
            new_idx = influence_index_map[get_short_name(new_joint)]
        
        # 양쪽 조인트 모두 찾은 경우만 매핑에 추가
        if old_idx is not None and new_idx is not None:
            index_mapping[old_idx] = new_idx
            print(f"Mapping: {old_joint}(idx:{old_idx}) -> {new_joint}(idx:{new_idx})")
        else:
            # 찾지 못한 조인트에 대한 경고 출력
            if old_idx is None:
                print(f"Warning: {old_joint} not found in influences")
            if new_idx is None:
                print(f"Warning: {new_joint} not found in influences")
    
    # 유효한 매핑이 없는 경우 경고하고 종료
    if not index_mapping:
        cmds.warning("No valid joint mappings found in skin cluster!")
        return
    
    # 진행 상황 업데이트 (25%)
    if progress_callback:
        progress_callback(25, f"버텍스 정보 수집 중... (유효한 매핑: {len(index_mapping)}개)")
    
    # 메시의 전체 버텍스 개수 가져오기
    vertex_count = cmds.polyEvaluate(mesh, vertex=True)
    
    # 모든 버텍스에 대한 컴포넌트 생성
    fn_comp = om2.MFnSingleIndexedComponent()
    full_comp = fn_comp.create(om2.MFn.kMeshVertComponent)
    # 모든 버텍스 인덱스를 컴포넌트에 추가
    for i in range(vertex_count):
        fn_comp.addElement(i)
    
    # 진행 상황 업데이트 (30%)
    if progress_callback:
        progress_callback(30, f"버텍스 웨이트 데이터 로딩 중... (총 {vertex_count}개 버텍스)")
    
    # 스킨 클러스터에서 모든 버텍스의 웨이트 데이터를 한 번에 가져오기
    weights, influence_count = skin_fn.getWeights(mesh_dag, full_comp)
    
    # 진행 상황 업데이트 (40%)
    if progress_callback:
        progress_callback(40, "웨이트 데이터 2차원 배열로 재구성 중...")
    
    # 1차원 웨이트 배열을 2차원 배열로 재구성 (버텍스별로 정리)
    influence_per_vertex = len(influence_names)  # 버텍스당 인플루언스 개수
    weights_2d = []
    
    # 각 버텍스의 웨이트를 개별 리스트로 분리
    for i in range(0, len(weights), influence_per_vertex):
        vertex_weights = weights[i:i + influence_per_vertex]
        weights_2d.append(list(vertex_weights))
    
    # 실제로 웨이트 전송이 일어난 횟수를 카운트하는 변수
    transfer_count = 0
    
    # 진행 상황 업데이트 (50%)
    if progress_callback:
        progress_callback(50, f"웨이트 전송 시작... ({len(index_mapping)}개 매핑 처리)")
    
    # 각 버텍스의 웨이트를 수정하여 매핑된 조인트로 전송
    for vertex_idx in range(vertex_count):
        vertex_weights = weights_2d[vertex_idx]  # 현재 버텍스의 웨이트 배열
        
        # 매핑된 각 조인트 쌍에 대해 웨이트 전송 수행
        for old_idx, new_idx in index_mapping.items():
            # 인덱스가 유효한 범위 내에 있는지 확인
            if old_idx < len(vertex_weights) and new_idx < len(vertex_weights):
                old_weight = vertex_weights[old_idx]  # 기존 조인트의 웨이트
                if old_weight > 0.0:  # 실제로 웨이트가 있는 경우만 처리
                    # 기존 조인트의 웨이트를 새 조인트의 웨이트에 더하기
                    vertex_weights[new_idx] += old_weight
                    # 기존 조인트의 웨이트를 0으로 초기화
                    vertex_weights[old_idx] = 0.0
                    transfer_count += 1  # 전송 횟수 증가
        
        # 수정된 웨이트를 다시 저장
        weights_2d[vertex_idx] = vertex_weights
        
        # 더 자주 진행률 업데이트 (50~75% 구간을 더 세밀하게)
        if progress_callback:
            # 10% 단위로 업데이트하거나 최소 100개 버텍스마다 업데이트
            update_interval = max(1, min(vertex_count // 10, 100))
            if vertex_idx % update_interval == 0 or vertex_idx == vertex_count - 1:
                progress = 50 + (vertex_idx * 25) // vertex_count
                remaining_vertices = vertex_count - vertex_idx - 1
                progress_callback(progress, f"웨이트 전송 중... ({vertex_idx + 1}/{vertex_count}, 남은 버텍스: {remaining_vertices})")
    
    # 전송 완료 정보 출력
    print(f"Transferred weights for {transfer_count} vertex-joint pairs")
    
    # 진행 상황 업데이트 (80%)
    if progress_callback:
        progress_callback(80, f"웨이트 데이터 1차원 배열로 변환 중... (전송된 웨이트: {transfer_count}개)")
    
    # 2차원 웨이트 배열을 다시 1차원 배열로 변환 (Maya API에 전달하기 위해)
    new_weights = []
    for vertex_weights in weights_2d:
        new_weights.extend(vertex_weights)  # 각 버텍스의 웨이트를 순서대로 추가
    
    # 진행 상황 업데이트 (85%)
    if progress_callback:
        progress_callback(85, "인플루언스 인덱스 배열 생성 중...")
    
    # 모든 인플루언스의 인덱스 배열 생성
    influence_indices = om2.MIntArray()
    for i in range(len(influence_names)):
        influence_indices.append(i)
    
    # 진행 상황 업데이트 (90%)
    if progress_callback:
        progress_callback(90, "스킨 클러스터에 새 웨이트 데이터 적용 중...")
    
    # 스킨 클러스터에 새로운 웨이트 데이터 설정
    # normalize=True로 설정하여 웨이트 합이 1이 되도록 자동 정규화
    skin_fn.setWeights(
        mesh_dag,
        full_comp,
        influence_indices,
        om2.MDoubleArray(new_weights),
        normalize=True
    )
    
    # 최종 진행 상황 업데이트 (100%)
    if progress_callback:
        progress_callback(100, f"웨이트 정규화 및 전송 완료! (총 {transfer_count}개 웨이트 전송됨)")

def transfer_weights_to_mapped_joints(mesh, joint_mapping, progress_callback=None):
    """
    기존 조인트의 웨이트를 맵핑된 새 조인트로 전송하는 함수
    
    Args:
        mesh (str): 스킨 클러스터가 있는 메시 이름
        joint_mapping (dict): {기존조인트: 새조인트} 형태의 맵핑 딕셔너리
        progress_callback (callable): 진행 상황 콜백 함수
    
    Returns:
        dict: 전송 결과 정보
        
    Example:
        joint_mapping = {
            'joint1': 'new_joint1',
            'joint2': 'new_joint2'
        }
        result = transfer_weights_to_mapped_joints('pCube1', joint_mapping)
    """
    
    if progress_callback:
        progress_callback(0, "스킨 클러스터 찾는 중...")
    
    # 메시의 스킨 클러스터 찾기
    skin_cluster = get_skin_cluster(mesh)
    if not skin_cluster:
        error_msg = f"No skin cluster found on {mesh}"
        cmds.error(error_msg)
        return {"success": False, "error": error_msg}
    
    if progress_callback:
        progress_callback(10, "현재 조인트 정보 가져오는 중...")
    
    # 현재 바인딩된 조인트 리스트 가져오기
    current_influences = cmds.skinCluster(skin_cluster, query=True, influence=True)
    print(f"Current influences: {current_influences}")
    
    if progress_callback:
        progress_callback(20, "웨이트 데이터 처리 시작...")
    
    try:
        # OpenMaya 2.0 API를 사용한 웨이트 전송
        transfer_weights_api(mesh, skin_cluster, joint_mapping, progress_callback)
        
        if progress_callback:
            progress_callback(100, "웨이트 트랜스퍼 완료!")
        
        print(f"Weight transfer completed for {mesh}")
        return {
            "success": True, 
            "mesh": mesh,
            "skin_cluster": skin_cluster,
            "mappings_processed": len(joint_mapping)
        }
        
    except Exception as e:
        error_msg = f"Weight transfer failed: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}

def validate_joint_mapping(joint_mapping, mesh=None):
    """
    조인트 매핑의 유효성을 검사하는 함수
    
    Args:
        joint_mapping (dict): {기존조인트: 새조인트} 형태의 맵핑 딕셔너리
        mesh (str, optional): 스킨 클러스터가 있는 메시 이름
    
    Returns:
        dict: 검증 결과
    """
    result = {
        "valid_mappings": {},
        "missing_old_joints": [],
        "missing_new_joints": [],
        "new_joints_to_add": []
    }
    
    # 메시가 지정된 경우 스킨 클러스터의 조인트들 확인
    skin_influences = []
    if mesh:
        skin_cluster = get_skin_cluster(mesh)
        if skin_cluster:
            skin_influences = cmds.skinCluster(skin_cluster, query=True, influence=True)
    
    for old_joint, new_joint in joint_mapping.items():
        # 기존 조인트 존재 확인
        if not cmds.objExists(old_joint):
            result["missing_old_joints"].append(old_joint)
            continue
        
        # 새 조인트 존재 확인
        if not cmds.objExists(new_joint):
            result["missing_new_joints"].append(new_joint)
            continue
        
        # 유효한 매핑에 추가
        result["valid_mappings"][old_joint] = new_joint
        
        # 새 조인트가 스킨 클러스터에 없는 경우 추가 목록에 포함
        if mesh and skin_influences and new_joint not in skin_influences:
            if cmds.objectType(new_joint) == 'joint':
                result["new_joints_to_add"].append(new_joint)
    
    return result 