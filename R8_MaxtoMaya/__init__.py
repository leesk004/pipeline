# R8_MaxtoMaya 패키지 초기화
"""
R8_MaxtoMaya 패키지

Maya에서 3ds Max FBX 애니메이션 파일을 처리하기 위한 통합 도구 모음입니다.

주요 기능:
- FBX 파일 배치 임포트 및 레퍼런스 관리
- 스켈레톤 매칭 및 애니메이션 베이킹
- Maya Standalone을 활용한 백그라운드 배치 처리
- 애니메이션 레퍼런스 자동 제거 및 씬 정리

모듈 구성:
- R8_ani_fbx_importer: FBX 파일 임포트 및 메인 UI 관리 (1048줄)
- R8_ani_skeleton_match: 스켈레톤 매칭 및 애니메이션 베이킹 (278줄)
- R8_ani_batch_process: 배치 처리 및 백그라운드 작업 관리 (896줄)
- R8_ani_reference_remove: 레퍼런스 제거 및 씬 정리 (227줄)

버전: 2024.1
지원 Maya 버전: 2022, 2023, 2024, 2025
UI 프레임워크: PySide2/PySide6 호환

사용법:
    import R8_MaxtoMaya.R8_ani_fbx_importer as importer
    from importlib import reload
    reload(importer)
    importer.show_ui()
"""

from . import R8_ani_fbx_importer
from . import R8_ani_skeleton_match
from . import R8_ani_batch_process
from . import R8_ani_reference_remove

# Weight 관련 모듈들 추가
try:
    from . import R8_weight_skin_IO
    from . import R8_weight_export_ui
    from . import R8_weight_import_ui
    from . import R8_weight_info_dialog
    from . import R8_weight_transfer_core
    WEIGHT_MODULES_AVAILABLE = True
except ImportError:
    WEIGHT_MODULES_AVAILABLE = False

__version__ = "2024.1"
__author__ = "R8 Studio"
__description__ = "Maya FBX Animation Batch Processing Tools"

__all__ = [
    'R8_ani_fbx_importer', 
    'R8_ani_skeleton_match', 
    'R8_ani_batch_process',
    'R8_ani_reference_remove'
]

# Weight 모듈들이 사용 가능한 경우 추가
if WEIGHT_MODULES_AVAILABLE:
    __all__.extend([
        'R8_weight_skin_IO',
        'R8_weight_export_ui',
        'R8_weight_import_ui',
        'R8_weight_info_dialog',
        'R8_weight_transfer_core'
    ])

# 패키지 레벨 함수들
def show_main_ui():
    """메인 FBX 임포터 UI를 표시합니다."""
    from importlib import reload
    reload(R8_ani_fbx_importer)
    return R8_ani_fbx_importer.show_ui()

def get_version():
    """패키지 버전을 반환합니다."""
    return __version__

def get_module_info():
    """모듈 정보를 딕셔너리로 반환합니다."""
    return {
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'modules': __all__
    }
