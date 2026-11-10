"""
독립유공자 공훈록 MCP 서버

이 패키지는 국가보훈처에서 제공하는 OpenAPI를 이용하여
독립유공자 공훈록 및 공적조서 정보를 조회하는 MCP 서버를 제공합니다.

사용 가능한 리소스:
1. gonghun://merit/all - 독립유공자 공훈록 전체 목록 조회
2. gonghun://report/all - 독립유공자 공적조서 전체 목록 조회
3. gonghun://code/hunkuk - 훈격 코드 정보 조회
4. gonghun://code/workout - 운동계열 코드 정보 조회

사용 가능한 도구:
1. get_merit_list - 독립유공자 공훈록 목록 조회
2. get_public_report - 독립유공자 공적조서 조회
3. get_hunkuk_codes - 훈격 코드 정보 조회
4. get_workout_affil_codes - 운동계열 코드 정보 조회
5. clear_cache - 캐시 초기화
"""

# 버전 정보
__version__ = '0.1.0'

# 모듈 가져오기
from . import config
from . import cache
from . import utils
from . import api
from . import tools
from . import main
from . import server

# 메인 실행 함수 노출
from .main import run

# 서버 인스턴스 노출
app = config.app

# 캐시 매니저 노출
cache_manager = cache.cache_manager

# 로거 노출
logger = config.logger

# API 함수 노출
fetch_merit_list = api.fetch_merit_list
fetch_public_report = api.fetch_public_report

# 유틸리티 함수 노출
parse_xml_response = utils.parse_xml_response
parse_resource_uri = utils.parse_resource_uri
format_response = utils.format_response
create_error_response = utils.create_error_response
build_query_params = utils.build_query_params

# 스크립트로 직접 실행될 때의 진입점
if __name__ == "__main__":
    run()