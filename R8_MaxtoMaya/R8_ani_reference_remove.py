from maya import cmds, mel
from typing import List, Tuple, Optional
import os


def remove_all_animation_references() -> None:
    """
    마야 씬에서 모든 애니메이션 레퍼런스 노드들을 제거하는 함수입니다.
    
    이 함수는 다음과 같은 작업을 수행합니다:
    1. 씬의 모든 레퍼런스 노드를 검색
    2. 시스템 레퍼런스(sharedReferenceNode)는 제외
    3. 로드된 레퍼런스들을 안전하게 제거
    4. 제거 결과를 콘솔에 출력
    
    Returns:
        None
        
    Raises:
        Exception: 레퍼런스 제거 중 오류 발생 시
        
    Examples:
        >>> remove_all_animation_references()
        레퍼런스 제거 중: C:/path/to/animation.fbx
        성공적으로 제거됨: C:/path/to/animation.fbx
        === 레퍼런스 제거 완료 ===
        총 제거된 레퍼런스: 1개
    """
    try:
        # 모든 레퍼런스 노드 가져오기
        reference_nodes = cmds.ls(type='reference')
        
        if not reference_nodes:
            print("씬에 레퍼런스 노드가 없습니다.")
            return
        
        removed_count = 0
        failed_references = []
        
        # 레퍼런스 제거는 역순으로 진행 (의존성 문제 방지)
        for ref_node in reversed(reference_nodes):
            try:
                # 'sharedReferenceNode'는 기본 시스템 레퍼런스이므로 제외
                if ref_node == 'sharedReferenceNode':
                    continue
                
                # 레퍼런스 노드가 여전히 존재하는지 확인
                if not cmds.objExists(ref_node):
                    continue
                
                # 레퍼런스 파일 경로 가져오기 (먼저 시도)
                try:
                    ref_file = cmds.referenceQuery(ref_node, filename=True)
                except:
                    print(f"레퍼런스 파일 경로를 가져올 수 없음: {ref_node}")
                    continue
                
                # 레퍼런스가 로드되어 있는지 확인
                is_loaded = cmds.referenceQuery(ref_node, isLoaded=True)
                
                if is_loaded:
                    print(f"레퍼런스 제거 중: {ref_file}")
                    
                    # 레퍼런스 제거
                    cmds.file(ref_file, removeReference=True)
                    removed_count += 1
                    print(f"성공적으로 제거됨: {ref_file}")
                    
                else:
                    # 언로드된 레퍼런스도 제거 시도
                    print(f"언로드된 레퍼런스 제거 중: {ref_file}")
                    cmds.file(ref_file, removeReference=True)
                    removed_count += 1
                    print(f"성공적으로 제거됨: {ref_file}")
                    
            except Exception as e:
                error_msg = f"레퍼런스 제거 실패 - {ref_node}: {str(e)}"
                print(error_msg)
                failed_references.append((ref_node, str(e)))
                continue
        
        # 결과 출력
        print(f"\n=== 레퍼런스 제거 완료 ===")
        print(f"총 제거된 레퍼런스: {removed_count}개")
        
        if failed_references:
            print(f"제거 실패한 레퍼런스: {len(failed_references)}개")
            for ref_node, error in failed_references:
                print(f"  - {ref_node}: {error}")
        
        # 씬 정리
        cleanup_scene()
        cleanup_unused_nodes()
        
    except Exception as e:
        print(f"스크립트 실행 중 오류 발생: {str(e)}")
        raise


def cleanup_scene() -> None:
    """
    씬을 정리합니다.
    
    사용하지 않는 노드들을 삭제하고 네임스페이스를 정리하여
    씬을 깨끗한 상태로 만듭니다.
    
    Returns:
        None
        
    Raises:
        Exception: 씬 정리 중 오류 발생 시
    """
    try:
        print("\n씬 정리 중...")
        
        # 네임스페이스 정리 (먼저 수행)
        cleanup_namespaces()
        
        # 사용하지 않는 노드들 삭제
        try:
            mel.eval('MLdeleteUnused;')
            print("사용하지 않는 노드들이 삭제되었습니다.")
        except Exception as e:
            print(f"MLdeleteUnused 실행 실패: {str(e)}")
            # 대안으로 직접 사용하지 않는 노드 정리
            cleanup_unused_materials()
        
        print("씬 정리 완료")
        
    except Exception as e:
        print(f"씬 정리 중 오류 발생: {str(e)}")
        raise


def cleanup_unused_materials() -> None:
    """
    사용하지 않는 머티리얼과 셰이더를 정리합니다.
    
    Returns:
        None
    """
    try:
        print("사용하지 않는 머티리얼 정리 중...")
        
        # 사용하지 않는 셰이딩 노드들 삭제
        unused_shaders = []
        
        # 모든 셰이딩 노드 타입들
        shader_types = ['lambert', 'blinn', 'phong', 'surfaceShader', 'file', 'place2dTexture']
        
        for shader_type in shader_types:
            nodes = cmds.ls(type=shader_type)
            for node in nodes:
                # 기본 머티리얼은 제외
                if node in ['lambert1', 'particleCloud1', 'initialShadingGroup', 'initialParticleSE']:
                    continue
                
                # 연결이 없는 노드들 찾기
                connections = cmds.listConnections(node)
                if not connections:
                    unused_shaders.append(node)
        
        # 사용하지 않는 셰이더 삭제
        if unused_shaders:
            for shader in unused_shaders:
                try:
                    if cmds.objExists(shader):
                        cmds.delete(shader)
                        print(f"사용하지 않는 셰이더 삭제됨: {shader}")
                except Exception as e:
                    print(f"셰이더 삭제 실패 - {shader}: {str(e)}")
        
    except Exception as e:
        print(f"머티리얼 정리 중 오류 발생: {str(e)}")


def cleanup_unused_nodes() -> None:
    """
    사용하지 않는 노드들을 정리합니다.
    
    Returns:
        None
        
    Raises:
        Exception: 노드 정리 중 오류 발생 시
    """
    try:
        print("사용하지 않는 노드들 정리 중...")
        
        # fosterParent 노드들 삭제
        foster_parents = cmds.ls(type="fosterParent")
        if foster_parents:
            for foster_parent in foster_parents:
                try:
                    if cmds.objExists(foster_parent):
                        cmds.delete(foster_parent)
                        print(f"fosterParent 노드 삭제됨: {foster_parent}")
                except Exception as e:
                    print(f"fosterParent 노드 삭제 실패 - {foster_parent}: {str(e)}")
        
        # unknown 노드들 삭제
        unknown_nodes = cmds.ls(type="unknown")
        if unknown_nodes:
            for unknown_node in unknown_nodes:
                try:
                    if cmds.objExists(unknown_node):
                        cmds.delete(unknown_node)
                        print(f"unknown 노드 삭제됨: {unknown_node}")
                except Exception as e:
                    print(f"unknown 노드 삭제 실패 - {unknown_node}: {str(e)}")
        
        # root_grp 노드 삭제
        if cmds.objExists("root_grp"):
            try:
                cmds.delete("root_grp")
                print("root_grp 노드 삭제됨")
            except Exception as e:
                print(f"root_grp 노드 삭제 실패: {str(e)}")
        
        print("사용하지 않는 노드들 정리 완료")
        
    except Exception as e:
        print(f"사용하지 않는 노드들 정리 중 오류 발생: {str(e)}")
        raise


def cleanup_namespaces() -> None:
    """
    사용하지 않는 네임스페이스들을 정리합니다.
    
    Returns:
        None
        
    Raises:
        Exception: 네임스페이스 정리 중 오류 발생 시
    """
    try:
        print("네임스페이스 정리 중...")
        
        # 모든 네임스페이스 가져오기 (기본 네임스페이스 제외)
        try:
            all_namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
        except:
            print("네임스페이스 정보를 가져올 수 없습니다.")
            return
        
        if not all_namespaces:
            print("정리할 네임스페이스가 없습니다.")
            return
        
        # 기본 네임스페이스들 제외
        default_namespaces = ['UI', 'shared']
        namespaces_to_remove = [ns for ns in all_namespaces if ns not in default_namespaces]
        
        removed_ns_count = 0
        
        # 네임스페이스는 계층 구조를 고려하여 자식부터 제거
        namespaces_to_remove.sort(key=lambda x: x.count(':'), reverse=True)
        
        for namespace in namespaces_to_remove:
            try:
                # 네임스페이스가 존재하는지 확인
                if not cmds.namespace(exists=namespace):
                    continue
                
                # 네임스페이스가 비어있는지 확인
                try:
                    namespace_contents = cmds.namespaceInfo(namespace, listNamespace=True)
                except:
                    namespace_contents = None
                
                if not namespace_contents:
                    cmds.namespace(removeNamespace=namespace)
                    print(f"빈 네임스페이스 제거됨: {namespace}")
                    removed_ns_count += 1
                else:
                    print(f"네임스페이스에 내용이 있어 제거하지 않음: {namespace}")
                    
            except Exception as e:
                print(f"네임스페이스 제거 실패 - {namespace}: {str(e)}")
                continue
        
        if removed_ns_count > 0:
            print(f"총 {removed_ns_count}개의 빈 네임스페이스가 제거되었습니다.")
        else:
            print("제거된 네임스페이스가 없습니다.")
            
    except Exception as e:
        print(f"네임스페이스 정리 중 오류 발생: {str(e)}")
        raise


def list_current_references() -> List[Tuple[str, str, bool]]:
    """
    현재 씬의 모든 레퍼런스 목록을 출력하고 반환합니다.
    
    Returns:
        List[Tuple[str, str, bool]]: (레퍼런스 노드명, 파일 경로, 로드 상태) 튜플 리스트
        
    Raises:
        Exception: 레퍼런스 목록 조회 중 오류 발생 시
    """
    try:
        reference_nodes = cmds.ls(type='reference')
        reference_info = []
        
        if not reference_nodes:
            print("씬에 레퍼런스가 없습니다.")
            return reference_info
        
        print("\n=== 현재 씬의 레퍼런스 목록 ===")
        
        for ref_node in reference_nodes:
            if ref_node == 'sharedReferenceNode':
                continue
                
            try:
                # 레퍼런스 노드가 존재하는지 확인
                if not cmds.objExists(ref_node):
                    continue
                
                ref_file = cmds.referenceQuery(ref_node, filename=True)
                is_loaded = cmds.referenceQuery(ref_node, isLoaded=True)
                status = "로드됨" if is_loaded else "언로드됨"
                
                # 파일 존재 여부 확인
                file_exists = os.path.exists(ref_file) if ref_file != "알 수 없음" else False
                existence_status = "존재함" if file_exists else "파일 없음"
                
                reference_info.append((ref_node, ref_file, is_loaded))
                print(f"- {ref_node}: {ref_file} ({status}, {existence_status})")
                
            except Exception as e:
                print(f"- {ref_node}: 정보 가져오기 실패 - {str(e)}")
                reference_info.append((ref_node, "알 수 없음", False))
        
        return reference_info
                
    except Exception as e:
        print(f"레퍼런스 목록 조회 중 오류 발생: {str(e)}")
        raise


def get_reference_statistics() -> dict:
    """
    현재 씬의 레퍼런스 통계 정보를 반환합니다.
    
    Returns:
        dict: 레퍼런스 통계 정보
        
    Raises:
        Exception: 통계 정보 조회 중 오류 발생 시
    """
    try:
        # 출력을 위한 임시 버퍼링 (list_current_references의 출력 억제)
        import sys
        from io import StringIO
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            reference_info = list_current_references()
        finally:
            sys.stdout = old_stdout
        
        stats = {
            'total_references': len(reference_info),
            'loaded_references': sum(1 for _, _, is_loaded in reference_info if is_loaded),
            'unloaded_references': sum(1 for _, _, is_loaded in reference_info if not is_loaded),
            'reference_files': [file_path for _, file_path, _ in reference_info if file_path != "알 수 없음"]
        }
        
        return stats
        
    except Exception as e:
        print(f"레퍼런스 통계 조회 중 오류 발생: {str(e)}")
        raise


def confirm_reference_removal() -> bool:
    """
    레퍼런스 제거 전 사용자 확인을 위한 함수입니다.
    
    Returns:
        bool: 사용자가 확인했으면 True, 그렇지 않으면 False
    """
    try:
        # Maya의 confirmDialog 사용
        result = cmds.confirmDialog(
            title='레퍼런스 제거 확인',
            message='모든 레퍼런스를 제거하시겠습니까?\n\n주의: 이 작업은 되돌릴 수 없습니다!',
            button=['예', '아니오'],
            defaultButton='아니오',
            cancelButton='아니오',
            dismissString='아니오'
        )
        return result == '예'
    except:
        # Maya UI가 없는 경우 (배치 모드 등)
        print("\n모든 레퍼런스를 제거하시겠습니까?")
        print("주의: 이 작업은 되돌릴 수 없습니다!")
        print("계속하려면 'y' 또는 'yes'를 입력하세요.")
        return True  # 스크립트 모드에서는 자동으로 진행


def main() -> None:
    """
    메인 실행 함수
    
    Returns:
        None
    """
    print("=== 마야 애니메이션 레퍼런스 제거 스크립트 ===\n")
    
    # 현재 레퍼런스 목록 출력
    list_current_references()
    
    # 사용자 확인
    if not confirm_reference_removal():
        print("레퍼런스 제거가 취소되었습니다.")
        return
    
    # 레퍼런스 제거 실행
    remove_all_animation_references()


# 스크립트 직접 실행 시
if __name__ == "__main__":
    main()


# 마야에서 함수별로 실행할 수 있도록 개별 함수들도 제공
def execute_remove_references():
    """마야에서 직접 호출할 수 있는 레퍼런스 제거 함수"""
    remove_all_animation_references()


def execute_list_references():
    """마야에서 직접 호출할 수 있는 레퍼런스 목록 조회 함수"""
    return list_current_references()


def execute_cleanup_scene():
    """마야에서 직접 호출할 수 있는 씬 정리 함수"""
    cleanup_scene()
    cleanup_unused_nodes()


def execute_get_statistics():
    """마야에서 직접 호출할 수 있는 통계 조회 함수"""
    return get_reference_statistics()