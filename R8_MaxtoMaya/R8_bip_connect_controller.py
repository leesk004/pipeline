import pymel.core as pm

def create_child_joint_locators(root='Bip001', recursive=True, make_group=True):
    """
    Root 조인트의 자식 조인트들 위에 로케이터를 생성합니다.
    - 이름에 skip_token(기본: 'Base')이 포함된 조인트는 건너뜀.
    - recursive=True면 모든 하위 조인트(자손), False면 바로 아래 자식만 대상.
    - make_group=True면 생성된 로케이터를 Root기반 그룹에 정리.

    Returns: 생성된 로케이터(PyNode) 리스트
    """
    # Root 설정
    if root is None:
        sel = pm.ls(sl=True, type='joint')
        if not sel:
            pm.warning('Root 조인트를 선택하거나 root 인수를 넘겨주세요.')
            return []
        root = sel[0]
    root = pm.PyNode(root)

    # 대상 조인트 수집
    if recursive:
        joints = [j for j in root.listRelatives(ad=True, type='joint')]
    else:
        joints = root.getChildren(type='joint')

    if not joints:
        pm.warning('대상 자식 조인트가 없습니다.')
        return []

    # 그룹 생성(옵션)
    grp = None
    if make_group:
        grp_name = 'bip_constraint_loc_grp'
        grp = pm.createNode('transform', name=grp_name)

    created = []
    for jnt in joints:
        name = jnt.nodeName()
        loc = pm.spaceLocator(name=f'{name}_loc')
        loc_grp = pm.group(empty=True, name=f'{loc}_grp')
        loc_grp.addChild(loc)
        # 조인트의 월드 변환 매트릭스를 그대로 복사하여 위치/회전 매칭
        loc_grp.setMatrix(loc_grp.getMatrix(worldSpace=True), worldSpace=True)

        if grp:
            pm.parent(loc_grp, grp)

        created.append(loc)

    if created:
        pm.select(created)
    else:
        pm.warning('생성된 로케이터가 없습니다.')

    return created   