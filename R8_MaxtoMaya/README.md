# R8_MaxtoMaya - 애니메이션 FBX 배치 처리 도구

Maya에서 3ds Max FBX 애니메이션 파일들을 배치로 처리하는 통합 도구입니다.

## 주요 기능

1. **FBX 파일 배치 임포트**: 여러 FBX 파일을 한 번에 레퍼런스로 불러오기
2. **스켈레톤 매칭**: 리그와 애니메이션 스켈레톤 자동 매칭
3. **컨트롤 베이킹**: FK 컨트롤에 애니메이션 베이킹
4. **백그라운드 처리**: Maya Standalone을 사용한 백그라운드 배치 처리
5. **자동 저장**: 처리된 파일을 지정된 폴더에 자동 저장
6. **레퍼런스 관리**: 레퍼런스 에디터 연동 및 레퍼런스 제거 기능
7. **방향 설정**: FrontX/FrontZ 축 방향 자동 조정
8. **씬 정리**: 레퍼런스 제거 후 자동 씬 최적화

## 파일 구조

- `R8_ani_fbx_importer.py`: 메인 UI 및 파일 관리 (1048줄)
- `R8_ani_skeleton_match.py`: 스켈레톤 매칭 및 베이킹 로직 (278줄)
- `R8_ani_batch_process.py`: 백그라운드 배치 처리 매니저 (896줄)
- `R8_ani_reference_remove.py`: 레퍼런스 제거 및 씬 정리 (227줄)
- `__init__.py`: 패키지 초기화 파일

## 버전 정보

- **현재 버전**: 2024.1
- **지원 Maya 버전**: 2022, 2023, 2024, 2025
- **UI 프레임워크**: PySide2/PySide6 자동 호환
- **작성자**: R8 Studio

## 사용법

### 1. UI 실행

```python
# 방법 1: 패키지 레벨 함수 사용 (권장)
import R8_MaxtoMaya
R8_MaxtoMaya.show_main_ui()

# 방법 2: 직접 모듈 임포트
import R8_MaxtoMaya.R8_ani_fbx_importer as R8_ani_fbx_importer
from importlib import reload
reload(R8_ani_fbx_importer)
R8_ani_fbx_importer.show_ui()
```

### 2. 기본 설정

#### 필수 설정
1. **Maya Rig File**: 기본 리그 파일 경로 설정 (.ma 또는 .mb 파일)
2. **Anim Location**: FBX 애니메이션 파일들이 있는 폴더 선택
3. **Save Path**: 처리된 파일을 저장할 폴더 선택

#### 방향 설정
- **FrontX**: 캐릭터의 정면이 X축 방향일 때 선택
- **FrontZ**: 캐릭터의 정면이 Z축 방향일 때 선택 (기본값)

### 3. 배치 처리 (자동 처리)

1. 파일 리스트에서 처리할 FBX 파일들을 선택 (선택하지 않으면 모든 파일 처리)
2. **"Batch Process"** 버튼 클릭
3. 백그라운드에서 자동으로 처리됨:
   - 리그 파일 로드
   - FBX 파일 레퍼런스 로드
   - 스켈레톤 매칭 및 바인드 포즈 설정
   - FK 컨트롤 베이킹
   - 마야 파일(.ma)로 저장

### 4. 수동 처리 (개별 파일)

#### 파일 로드
1. 파일을 더블클릭하여 Reference/Import 선택 다이얼로그 표시
2. **"Reference Selected"** 버튼으로 선택된 파일들을 레퍼런스로 로드

#### 단계별 처리
1. **"1. Skeleton Match"**: 스켈레톤 매칭 및 컨스트레인 설정
2. **"2. FK Control Bake"**: FK 컨트롤에 애니메이션 베이킹
3. **"3. Save Scene As"**: 처리된 씬을 마야 파일로 저장

#### 추가 기능
- **"Reference Editor"**: Maya 레퍼런스 에디터 열기
- **"Delete Controller Connection"**: 컨트롤러 컨스트레인 연결 제거
- **"Open Maya"**: 저장 폴더에서 마야 파일 열기

### 5. 레퍼런스 관리

#### 레퍼런스 제거 기능
```python
import R8_MaxtoMaya.R8_ani_reference_remove as ref_remove

# 모든 레퍼런스 제거
ref_remove.remove_all_animation_references()

# 현재 레퍼런스 목록 조회
reference_list = ref_remove.list_current_references()

# 레퍼런스 통계 정보 조회
stats = ref_remove.get_reference_statistics()
print(f"총 레퍼런스: {stats['total_references']}개")
print(f"로드된 레퍼런스: {stats['loaded_references']}개")

# 씬 정리
ref_remove.cleanup_scene()
ref_remove.cleanup_unused_nodes()
```

## 기술적 세부사항

### 스켈레톤 매칭 과정
1. 'Skeleton_Set' 세트에서 조인트 목록 가져오기
2. 프리픽스가 있는 애니메이션 조인트와 리그 조인트 매칭
3. 바인드 포즈(-10프레임)에서 초기 포즈 설정
4. 각 컨트롤에 대해 로케이터 생성 및 컨스트레인 연결

### 베이킹 과정
1. 'Bake_Control_Set' 세트의 컨트롤들 대상
2. 타임라인 전체 구간에서 애니메이션 베이킹
3. 회전 최적화 및 키프레임 보존 옵션 적용

### 배치 처리 시스템
- Maya Standalone 프로세스를 별도로 실행
- 임시 스크립트 파일 생성으로 각 파일 독립 처리
- 실시간 진행상황 모니터링
- 처리 완료 후 자동 정리

### 에러 처리 및 안정성
- 모든 주요 함수에 예외 처리 적용
- 타입 힌트를 통한 코드 안정성 향상
- 상세한 로그 출력으로 디버깅 지원
- 백그라운드 프로세스 안전 종료 기능

## 요구사항

- **Maya**: 2022 이상 (2024, 2025 버전 지원)
- **Python UI**: PySide2 또는 PySide6 (자동 감지)
- **운영체제**: Windows 환경 (Maya 실행 파일 자동 감지)
- **필수 세트**: 리그 파일에 'Skeleton_Set' 세트 필요

## 설정 파일

설정은 Maya 사용자 설정 디렉토리의 `ani_fbx_set.json`에 자동으로 저장됩니다:
```json
{
    "project_folder": "애니메이션 FBX 폴더 경로",
    "save_folder": "처리된 파일 저장 폴더 경로",
    "rig_file": "리그 파일 경로",
    "frontX": false,
    "frontZ": true
}
```

## API 참조

### 패키지 레벨 함수
```python
import R8_MaxtoMaya

# 메인 UI 표시
R8_MaxtoMaya.show_main_ui()

# 버전 정보 조회
version = R8_MaxtoMaya.get_version()

# 모듈 정보 조회
info = R8_MaxtoMaya.get_module_info()
```

### 스켈레톤 매칭 함수
```python
import R8_MaxtoMaya.R8_ani_skeleton_match as skel_match

# 스켈레톤 매칭 실행
skel_match.skeleton_control_match(frontAxis='frontZ')

# 컨트롤 베이킹
skel_match.control_bake()

# 제약 노드 삭제
skel_match.delete_constraint(controller_list)
```

### 레퍼런스 관리 함수
```python
import R8_MaxtoMaya.R8_ani_reference_remove as ref_remove

# 모든 레퍼런스 제거
ref_remove.remove_all_animation_references()

# 레퍼런스 목록 조회
references = ref_remove.list_current_references()

# 통계 정보 조회
stats = ref_remove.get_reference_statistics()
```

## 주의사항

1. **리그 요구사항**: 리그 파일에 'Skeleton_Set', 'Bake_Control_Set' 세트가 반드시 있어야 합니다
2. **Maya 설치**: 백그라운드 처리를 위해 Maya Standalone이 설치되어 있어야 합니다
3. **처리 중 주의**: 배치 처리 중에는 Maya를 닫지 마세요 (UI 응답 유지 필요)
4. **파일 경로**: 한글이 포함된 경로는 피하는 것을 권장합니다
5. **메모리 관리**: 대용량 FBX 파일 처리 시 충분한 메모리 확보 필요
6. **백업**: 중요한 파일은 처리 전 백업을 권장합니다

## 문제 해결

### 일반적인 문제
- **스켈레톤 매칭 실패**: 'Skeleton_Set', 'Bake_Control_Set' 세트 확인
- **베이킹 실패**: 타임라인 범위 및 컨트롤 상태 확인
- **배치 처리 중단**: Maya 실행 파일 경로 확인
- **UI 실행 오류**: PySide 모듈 설치 상태 확인

### 로그 확인
배치 처리 시 콘솔 출력으로 상세 진행상황 및 오류 정보를 확인할 수 있습니다.

### 디버깅 모드
```python
# 상세 로그 출력을 위한 디버깅 모드
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 업데이트 내역

### 2024.1
- 타입 힌트 추가로 코드 안정성 향상
- 함수 문서화 개선
- 에러 처리 강화
- 패키지 레벨 편의 함수 추가
- 레퍼런스 통계 기능 추가
- 호환성 함수 추가 (기존 오타 함수명 지원) 