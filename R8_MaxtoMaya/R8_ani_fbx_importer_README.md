# R8 Animation FBX Importer

Maya용 FBX 애니메이션 임포터 도구입니다. 3ds Max에서 익스포트한 애니메이션 FBX 파일을 Maya 리그에 적용하는 배치 처리 기능을 제공합니다.

## 주요 기능

### 🎯 핵심 기능
- **FBX 파일 배치 처리**: 여러 FBX 파일을 순차적으로 자동 처리
- **스켈레톤 매칭**: 3ds Max와 Maya 간의 스켈레톤 자동 매칭
- **애니메이션 베이킹**: FK 컨트롤에 애니메이션 베이킹
- **자동 저장**: 처리된 파일을 Maya 파일(.ma/.mb)로 자동 저장

### 📁 파일 관리
- FBX 파일 목록 관리 및 선택
- 리그 파일 지정 및 로드
- 저장 경로 설정 및 관리
- 설정값 JSON 파일로 자동 저장

### 🔧 처리 옵션
- **Front Axis 설정**: FrontX 또는 FrontZ 선택
- **선택적 삭제**: Constraint, Animation Keys, Reference 파일 개별 선택
- **레퍼런스/임포트**: 파일 로드 방식 선택

## 설치 및 요구사항

### 필수 요구사항
- Autodesk Maya 2020 이상
- PySide2 또는 PySide6 (Maya 버전에 따라 자동 선택)
- Python 3.x

### 의존 모듈
- `R8_ani_skeleton_match`: 스켈레톤 매칭 및 베이킹 기능
- `R8_ani_batch_process`: 배치 처리 백그라운드 실행
- `R8_ani_reference_remove`: 레퍼런스 파일 제거 기능

## 사용법

### 1. 기본 설정

```python
# Maya Script Editor에서 실행
import R8_MaxtoMaya.R8_ani_fbx_importer as fbx_importer
fbx_importer.show_ui()
```

### 2. UI 구성 요소

#### 파일 설정
- **Maya Rig File**: 애니메이션을 적용할 Maya 리그 파일 선택
- **Anim Location**: FBX 애니메이션 파일들이 있는 폴더 또는 개별 파일 선택
- **Save Path**: 처리된 파일을 저장할 폴더 경로

#### 처리 옵션
- **FrontX/FrontZ**: 3ds Max와 Maya 간의 축 방향 설정
- **Process Steps**: 개별 처리 단계 실행 (접기/펼치기 가능)
  - Skeleton Match
  - FK Control Bake
  - Save Scene As

#### 삭제 옵션
- **Constraint**: 제약 노드 삭제
- **Keys**: 애니메이션 키 삭제
- **Reference**: 레퍼런스 파일 제거

### 3. 배치 처리 워크플로우

1. **리그 파일 설정**: Maya 리그 파일(.ma/.mb) 선택
2. **FBX 파일 선택**: 처리할 애니메이션 FBX 파일들 선택
3. **저장 경로 설정**: 결과 파일을 저장할 폴더 선택
4. **옵션 설정**: Front Axis 및 기타 옵션 설정
5. **배치 처리 실행**: "Batch Process" 버튼 클릭

## 파일 구조

```
R8_MaxtoMaya/
├── R8_ani_fbx_importer.py          # 메인 UI 스크립트
├── R8_ani_skeleton_match.py        # 스켈레톤 매칭 모듈
├── R8_ani_batch_process.py         # 배치 처리 모듈
└── R8_ani_reference_remove.py     # 레퍼런스 제거 모듈
```

## 주요 클래스 및 함수

### FbxImporterUI 클래스
메인 UI 클래스로 다음 기능들을 제공합니다:

#### 주요 메서드
- `create_widgets()`: UI 위젯 생성
- `create_layouts()`: 레이아웃 구성
- `create_connections()`: 시그널/슬롯 연결
- `batch_process()`: 배치 처리 실행
- `skeleton_match_func()`: 스켈레톤 매칭 실행
- `control_bake_func()`: 컨트롤 베이킹 실행

#### 파일 관리 메서드
- `set_rig_file()`: 리그 파일 선택
- `set_folder()`: FBX 파일/폴더 선택
- `set_save_folder()`: 저장 폴더 선택
- `load_json()` / `save_json()`: 설정 저장/로드

### 유틸리티 함수
- `get_maya_main_window()`: Maya 메인 윈도우 반환
- `time_change_set()`: 시간 단위를 60fps로 설정
- `open_file_or_folder()`: OS별 파일/폴더 열기

## 설정 파일

애플리케이션 설정은 JSON 파일로 자동 저장됩니다:

```json
{
  "project_folder": "C:/path/to/fbx/files",
  "save_folder": "C:/path/to/save/location", 
  "rig_file": "C:/path/to/rig/file.ma"
}
```

**저장 위치**: Maya 설정 디렉토리 또는 사용자 홈 디렉토리의 `ani_fbx_set.json`

## 배치 처리 상세 과정

각 FBX 파일에 대해 다음 과정이 자동으로 실행됩니다:

1. **새 씬 생성**: 깨끗한 Maya 씬에서 시작
2. **리그 파일 로드**: 지정된 Maya 리그 파일 로드
3. **FBX 레퍼런스**: FBX 파일을 레퍼런스로 로드
4. **스켈레톤 매칭**: 3ds Max와 Maya 스켈레톤 매칭
5. **애니메이션 베이킹**: FK 컨트롤에 애니메이션 베이킹
6. **레퍼런스 제거**: FBX 레퍼런스 정리
7. **파일 저장**: 결과를 Maya 파일로 저장

## 에러 처리 및 로깅

### 로깅 시스템
- 실시간 로그 표시 (타임스탬프 포함)
- 처리 과정의 모든 단계 기록
- 성공/실패 상태 추적

### 안전한 모듈 로딩
의존 모듈이 없을 경우 더미 모듈로 대체하여 UI 실행 유지:

```python
class DummyModule:
    @staticmethod
    def skeleton_control_match(*args, **kwargs):
        print("경고: 모듈이 없어 실행할 수 없습니다.")
```

### 에러 처리
- 파일 경로 검증
- Maya 버전별 PySide 호환성 처리
- Qt 객체 안전한 정리
- 배치 처리 중단 및 복구

## 사용 예시

### 단일 파일 처리
```python
# 1. 리그 파일 로드
fbx_importer.open_rig_file()

# 2. FBX 파일 레퍼런스
fbx_importer.reference_selected_files()

# 3. 스켈레톤 매칭
fbx_importer.skeleton_match_func()

# 4. 베이킹
fbx_importer.control_bake_func()

# 5. 저장
fbx_importer.maya_file_save_func()
```

### 다중 파일 배치 처리
```python
# 모든 설정 완료 후
fbx_importer.batch_process()
```

## 문제 해결

### 일반적인 문제
1. **PySide 모듈 오류**: Maya 버전에 맞는 PySide 설치 확인
2. **의존 모듈 없음**: 모든 R8 모듈이 같은 폴더에 있는지 확인
3. **파일 경로 오류**: 경로에 한글이나 특수문자가 없는지 확인
4. **권한 오류**: 저장 폴더에 쓰기 권한이 있는지 확인

### 디버깅
- Maya Script Editor에서 오류 메시지 확인
- UI 로그 창에서 실시간 처리 상황 모니터링
- JSON 설정 파일 확인 및 수동 수정

## 업데이트 및 확장

### 모듈 리로드
```python
from importlib import reload
reload(R8_ani_skeleton_match)
reload(R8_ani_batch_process)
reload(R8_ani_reference_remove)
```

### 커스터마이징
- UI 스타일 변경: `setStyleSheet()` 메서드 수정
- 새로운 처리 단계 추가: `process_layout`에 버튼 추가
- 파일 필터 변경: `QFileDialog` 필터 수정

## 라이선스

이 도구는 Maya 환경에서의 애니메이션 파이프라인 개선을 위해 개발되었습니다.

## 기여

버그 리포트나 기능 개선 제안은 언제든 환영합니다.

---

*최종 업데이트: 2025년* 