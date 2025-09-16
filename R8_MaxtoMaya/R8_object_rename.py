from maya import cmds

def rename_object(root_obj, search_str='_jnt', replace_str=''):
    """
    지정된 루트 오브젝트와 그 하위 오브젝트들의 이름을 변경하는 함수
    
    Args:
        root_obj (str): 루트 오브젝트 이름
        search_str (str): 찾을 문자열 (기본값: '_jnt')
        replace_str (str): 바꿀 문자열 (기본값: '')
    """
    try:
        # 루트 오브젝트와 그 하위의 모든 오브젝트들을 가져옴
        select_objs = cmds.ls(root_obj, dag=True)
        
        # 각 오브젝트에 대해 이름 변경 처리
        for obj in select_objs:
            # 찾을 문자열이 오브젝트 이름에 포함되어 있는지 확인
            if search_str in obj:
                # 문자열을 바꿔서 오브젝트 이름 변경
                cmds.rename(obj, obj.replace(search_str, replace_str))
    except Exception as e:
        # 오류 발생 시 출력
        print(e)

if __name__ == '__main__':
    rename_object('root')
