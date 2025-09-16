'''
Maya Standalone Mannequin IK Delete Function
Mannequin IK 요소를 삭제하는 Maya Standalone 스크립트

사용법:
import R8_MaxtoMaya.R8_maya_standalone_func as standalone_func
standalone_func.mannequin_ik_delete()
'''

def mannequin_ik_delete():
    """Mannequin IK 요소 삭제"""
    from maya import cmds
    try:
        # Mannequin IK 요소 목록
        ik_elements = ['ik_foot_root', 'ik_hand_root', 'interaction', 'center_of_mass']
        deleted_count = 0
        for ik in ik_elements:
            try:
                if cmds.objExists(ik):
                    cmds.delete(ik)
                    print(f"삭제됨: {ik}")
                    deleted_count += 1
                else:
                    print(f"존재하지 않음: {ik}")
            except Exception as delete_error:
                print(f"삭제 실패: {ik} - {delete_error}")
        
        print("=" * 50)
        print(f"삭제 작업 완료: {deleted_count}개 요소 삭제됨")
        print("=" * 50)
        
    except Exception as e:
        print(f"Mannequin IK 삭제 중 오류: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    mannequin_ik_delete()


