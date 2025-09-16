# 웨이트 트랜스퍼 통합 기능

이 모듈은 Maya에서 스켈레톤 조인트 간의 웨이트를 효율적으로 전송하는 기능을 제공합니다. 모듈화된 구조로 설계되어 다양한 방식으로 재활용할 수 있습니다.

## 📁 파일 구조

```
R8_MaxtoMaya/
├── R8_weight_transfer_core.py      # 핵심 웨이트 트랜스퍼 기능
├── R8_weight_transfer_func.py      # 독립적인 웨이트 트랜스퍼 UI
├── R8_weight_transfer_utils.py     # 편의 함수들
├── R8_mannequin_skeleton_ui.py     # 마네퀸 스켈레톤 UI (웨이트 트랜스퍼 통합)
└── test_weight_transfer_integration.py  # 테스트 스크립트
```

## 🚀 주요 기능

### 1. 핵심 기능 (R8_weight_transfer_core.py)
- **transfer_weights_to_mapped_joints()**: 메인 웨이트 트랜스퍼 함수
- **validate_joint_mapping()**: 조인트 매핑 검증
- **add_joints_to_skin_cluster()**: 새 조인트를 스킨 클러스터에 추가
- **get_skin_cluster()**: 메시의 스킨 클러스터 찾기

### 2. 편의 함수들 (R8_weight_transfer_utils.py)
- **create_mapping_from_selection()**: 선택된 조인트로 매핑 생성
- **create_mapping_from_name_pattern()**: 이름 패턴 기반 매핑 생성
- **quick_transfer()**: 빠른 단일 조인트 웨이트 트랜스퍼
- **transfer_from_json_file()**: JSON 파일에서 매핑 로드하여 트랜스퍼
- **save_mapping_to_json()** / **load_mapping_from_json()**: JSON 저장/로드

### 3. UI 기능
- **독립적인 웨이트 트랜스퍼 UI**: 전용 인터페이스
- **마네퀸 스켈레톤 UI 통합**: 기존 워크플로우에 통합된 기능

## 💡 사용 방법

### 방법 1: 독립적인 웨이트 트랜스퍼 UI 사용

```python
# UI 열기
from R8_MaxtoMaya import R8_weight_transfer_func
R8_weight_transfer_func.show_weight_transfer_ui()
```

**UI 사용 단계:**
1. "Select Mesh" 버튼으로 스킨 메시 선택
2. "Skin Joints" 버튼으로 현재 스킨 조인트 로드
3. "Load New Joints" 버튼으로 새 조인트 선택
4. 필요시 JSON으로 매핑 저장/로드
5. "Weight Transfer" 버튼으로 실행

### 방법 2: 마네퀸 스켈레톤 UI에서 통합 기능 사용

```python
# 마네퀸 스켈레톤 UI 열기
from R8_MaxtoMaya import R8_mannequin_skeleton_ui
R8_mannequin_skeleton_ui.show_ui()
```

**통합 워크플로우:**
1. "1. Mannequin Skeleton" - 마네퀸 스켈레톤 생성
2. "2. Add Sub Skeleton" - 서브 스켈레톤 추가
3. "Biped to Mannequin" - 조인트 매핑 생성
4. "3. Weight Transfer" - 웨이트 트랜스퍼 실행

### 방법 3: 유틸리티 함수 직접 사용

```python
from R8_MaxtoMaya import R8_weight_transfer_utils as utils

# 선택된 조인트로 매핑 생성
cmds.select(["old_joint1", "old_joint2", "new_joint1", "new_joint2"])
mapping = utils.create_mapping_from_selection()

# 빠른 웨이트 트랜스퍼
result = utils.quick_transfer("pCube1", "old_joint", "new_joint")

# JSON 파일 사용
utils.save_mapping_to_json(mapping, "my_mapping.json")
result = utils.transfer_from_json_file("pCube1", "my_mapping.json")
```

### 방법 4: 핵심 기능 직접 사용

```python
from R8_MaxtoMaya import R8_weight_transfer_core as core

# 조인트 매핑 정의
joint_mapping = {
    "Bip01_Pelvis": "mixamorig:Hips",
    "Bip01_Spine": "mixamorig:Spine",
    "Bip01_L_Thigh": "mixamorig:LeftUpLeg"
}

# 웨이트 트랜스퍼 실행
result = core.transfer_weights_to_mapped_joints("character_mesh", joint_mapping)

if result["success"]:
    print(f"웨이트 트랜스퍼 완료: {result['mappings_processed']}개 매핑 처리됨")
else:
    print(f"오류: {result['error']}")
```

## ⚙️ 고급 사용법

### 패턴 기반 매핑 생성

```python
from R8_MaxtoMaya import R8_weight_transfer_utils as utils

# Biped 조인트를 Mixamo 조인트로 매핑
mapping = utils.create_mapping_from_name_pattern("Bip01_*", "mixamorig:*")
```

### 배치 처리

```python
# 여러 매핑을 순차적으로 처리
mappings_list = [mapping1, mapping2, mapping3]
results = utils.batch_transfer("character_mesh", mappings_list)
```

### 매핑 검증

```python
from R8_MaxtoMaya import R8_weight_transfer_core as core

validation = core.validate_joint_mapping(joint_mapping, "character_mesh")
print(f"유효한 매핑: {len(validation['valid_mappings'])}개")
print(f"누락된 조인트: {len(validation['missing_old_joints'])}개")
```

## 🔧 기능별 상세 설명

### 웨이트 트랜스퍼 과정
1. **스킨 클러스터 확인**: 메시에 스킨 클러스터가 있는지 검사
2. **조인트 검증**: 매핑된 조인트들이 존재하는지 확인
3. **새 조인트 추가**: 필요시 새 조인트를 스킨 클러스터에 추가
4. **웨이트 데이터 추출**: Maya API를 사용하여 현재 웨이트 정보 수집
5. **웨이트 재배치**: 기존 조인트의 웨이트를 새 조인트로 이동
6. **정규화**: 웨이트 합이 1이 되도록 자동 정규화

### JSON 매핑 형식
```json
{
    "Bip01_Pelvis": "mixamorig:Hips",
    "Bip01_Spine": "mixamorig:Spine",
    "Bip01_L_Thigh": "mixamorig:LeftUpLeg",
    "Bip01_R_Thigh": "mixamorig:RightUpLeg"
}
```

## 🧪 테스트

테스트 스크립트를 실행하여 모든 기능이 정상 작동하는지 확인할 수 있습니다:

```python
exec(open("R8_MaxtoMaya/test_weight_transfer_integration.py").read())
```

## ⚠️ 주의사항

1. **백업**: 웨이트 트랜스퍼 전에 씬을 저장해두세요.
2. **조인트 존재**: 매핑에 사용되는 모든 조인트가 씬에 존재해야 합니다.
3. **스킨 클러스터**: 대상 메시에 스킨 클러스터가 있어야 합니다.
4. **Maya 버전**: Maya 2018 이상에서 테스트되었습니다.

## 🔄 모듈 재로드

개발 중 모듈을 수정한 경우 다음과 같이 재로드할 수 있습니다:

```python
from importlib import reload
from R8_MaxtoMaya import R8_weight_transfer_core, R8_weight_transfer_utils

reload(R8_weight_transfer_core)
reload(R8_weight_transfer_utils)
```

## 📞 문제 해결

### 일반적인 문제들

1. **모듈 임포트 오류**
   - Maya의 스크립트 경로에 R8_MaxtoMaya 폴더가 있는지 확인
   - `sys.path.append()` 사용하여 경로 추가

2. **스킨 클러스터를 찾을 수 없음**
   - 메시에 스킨 클러스터가 바인딩되어 있는지 확인
   - 메시 이름이 정확한지 확인

3. **조인트를 찾을 수 없음**
   - 조인트 이름이 정확한지 확인 (네임스페이스 포함)
   - `cmds.ls(type='joint')` 명령으로 조인트 목록 확인

4. **웨이트가 제대로 전송되지 않음**
   - 기존 조인트에 실제 웨이트가 있는지 확인
   - 새 조인트가 스킨 클러스터에 추가되었는지 확인

이 모듈을 사용하면 Maya에서 복잡한 웨이트 트랜스퍼 작업을 간단하고 효율적으로 수행할 수 있습니다! 