"""
독립유공자 공훈록 MCP 서버 - API 모듈

이 모듈은 독립유공자 공훈록 API와의 통신을 담당합니다.
"""

import httpx
from typing import Dict, Any, Optional
from .config import logger, BASE_URL
from .cache import cache_manager
from .utils import parse_xml_response, build_query_params

async def fetch_merit_list(
    page_index: int = 1,
    count_per_page: int = 10,
    response_type: str = "JSON",
    mng_no: Optional[str] = None,
    name_ko: Optional[str] = None,
    name_ch: Optional[str] = None,
    diff_name: Optional[str] = None,
    birthday: Optional[str] = None,
    lastday: Optional[str] = None,
    sex: Optional[str] = None,
    register_large_div: Optional[str] = None,
    register_mid_div: Optional[str] = None,
    judge_year: Optional[str] = None,
    hunkuk: Optional[str] = None,
    workout_affil: Optional[str] = None,
    achivement: Optional[str] = None
) -> Dict[str, Any]:
    """
    독립유공자 공훈록 목록을 조회합니다.
    
    Args:
        page_index: 페이지 번호
        count_per_page: 페이지 당 데이터 건수 (최대 50건)
        response_type: 응답 형식 (JSON/XML)
        mng_no: 관리번호
        name_ko: 성명(한글)
        name_ch: 성명(한자)
        diff_name: 이명
        birthday: 생년월일
        lastday: 사망년월일
        sex: 성별
        register_large_div: 본적대분류
        register_mid_div: 본적중분류
        judge_year: 포상년도
        hunkuk: 훈격
        workout_affil: 운동계열
        achivement: 공훈록
        
    Returns:
        공훈록 목록 정보를 담은 딕셔너리
        
    Raises:
        RuntimeError: API 호출 중 오류가 발생한 경우
    """
    # 캐시 키 생성
    cache_params = [
        f"page_{page_index}",
        f"count_{count_per_page}"
    ]
    
    if mng_no:
        cache_params.append(f"mng_{mng_no}")
    if name_ko:
        cache_params.append(f"name_ko_{name_ko}")
    if name_ch:
        cache_params.append(f"name_ch_{name_ch}")
    if diff_name:
        cache_params.append(f"diff_{diff_name}")
    if birthday:
        cache_params.append(f"birth_{birthday}")
    if lastday:
        cache_params.append(f"last_{lastday}")
    if sex:
        cache_params.append(f"sex_{sex}")
    if register_large_div:
        cache_params.append(f"reg_l_{register_large_div}")
    if register_mid_div:
        cache_params.append(f"reg_m_{register_mid_div}")
    if judge_year:
        cache_params.append(f"year_{judge_year}")
    if hunkuk:
        cache_params.append(f"hunkuk_{hunkuk}")
    if workout_affil:
        cache_params.append(f"workout_{workout_affil}")
    if achivement:
        cache_params.append(f"achi_{achivement}")
    
    cache_key = f"merit_list_{'_'.join(cache_params)}"
    
    # 캐시 확인
    cached_data = cache_manager.get(cache_key)
    if cached_data:
        return cached_data

    # API 요청 파라미터 구성
    params = build_query_params(
        nPageIndex=page_index,
        nCountPerPage=count_per_page,
        type=response_type,
        mngNo=mng_no,
        nameKo=name_ko,
        nameCh=name_ch,
        diffName=diff_name,
        birthday=birthday,
        lastday=lastday,
        sex=sex,
        registerLargeDiv=register_large_div,
        registerMidDiv=register_mid_div,
        judgeYear=judge_year,
        hunkuk=hunkuk,
        workoutAffil=workout_affil,
        achivement=achivement
    )
    
    # API 요청
    endpoint = f"{BASE_URL}/contribuMeritList.do"
    logger.info(f"공훈록 목록 요청: {endpoint}, 파라미터: {params}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            
            # 응답 형식에 따라 처리
            if response_type.upper() == "JSON":
                result = response.json()
            else:  # XML
                # XML 응답 파싱
                result = parse_xml_response(response.text)
            
            if "error" not in result:
                # 캐시 저장
                cache_manager.set(cache_key, result)
            
            return result
    except httpx.TimeoutException:
        logger.error("API 요청 시간 초과")
        raise RuntimeError("API 요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP 상태 오류: {e.response.status_code} - {str(e)}")
        raise RuntimeError(f"HTTP 상태 오류: {e.response.status_code}. 요청을 처리할 수 없습니다.")
    except httpx.HTTPError as e:
        logger.error(f"HTTP 요청 오류: {str(e)}")
        raise RuntimeError(f"HTTP 요청 오류: {str(e)}")
    except Exception as e:
        logger.error(f"공훈록 목록 조회 중 오류 발생: {str(e)}")
        raise RuntimeError(f"공훈록 목록 조회 중 오류 발생: {str(e)}")

async def fetch_public_report(
    page_index: int = 1,
    count_per_page: int = 10,
    response_type: str = "JSON",
    mng_no: Optional[str] = None,
    name_ko: Optional[str] = None,
    name_ch: Optional[str] = None,
    diff_name: Optional[str] = None,
    birthday: Optional[str] = None,
    lastday: Optional[str] = None,
    sex: Optional[str] = None,
    register_large_div: Optional[str] = None,
    register_mid_div: Optional[str] = None,
    judge_year: Optional[str] = None,
    hunkuk: Optional[str] = None,
    workout_affil: Optional[str] = None,
    achivement: Optional[str] = None,
    achivement_ko: Optional[str] = None
) -> Dict[str, Any]:
    """
    독립유공자 공적조서를 조회합니다.
    
    Args:
        page_index: 페이지 번호
        count_per_page: 페이지 당 데이터 건수 (최대 50건)
        response_type: 응답 형식 (JSON/XML)
        mng_no: 관리번호
        name_ko: 성명(한글)
        name_ch: 성명(한자)
        diff_name: 이명
        birthday: 생년월일
        lastday: 사망년월일
        sex: 성별
        register_large_div: 본적대분류
        register_mid_div: 본적중분류
        judge_year: 포상년도
        hunkuk: 훈격
        workout_affil: 운동계열
        achivement: 공적개요
        achivement_ko: 공적개요 국한문병기
        
    Returns:
        공적조서 정보를 담은 딕셔너리
        
    Raises:
        RuntimeError: API 호출 중 오류가 발생한 경우
    """
    # 캐시 키 생성
    cache_params = [
        f"page_{page_index}",
        f"count_{count_per_page}"
    ]
    
    if mng_no:
        cache_params.append(f"mng_{mng_no}")
    if name_ko:
        cache_params.append(f"name_ko_{name_ko}")
    if name_ch:
        cache_params.append(f"name_ch_{name_ch}")
    if diff_name:
        cache_params.append(f"diff_{diff_name}")
    if birthday:
        cache_params.append(f"birth_{birthday}")
    if lastday:
        cache_params.append(f"last_{lastday}")
    if sex:
        cache_params.append(f"sex_{sex}")
    if register_large_div:
        cache_params.append(f"reg_l_{register_large_div}")
    if register_mid_div:
        cache_params.append(f"reg_m_{register_mid_div}")
    if judge_year:
        cache_params.append(f"year_{judge_year}")
    if hunkuk:
        cache_params.append(f"hunkuk_{hunkuk}")
    if workout_affil:
        cache_params.append(f"workout_{workout_affil}")
    if achivement:
        cache_params.append(f"achi_{achivement}")
    if achivement_ko:
        cache_params.append(f"achi_ko_{achivement_ko}")
    
    cache_key = f"public_report_{'_'.join(cache_params)}"
    
    # 캐시 확인
    cached_data = cache_manager.get(cache_key)
    if cached_data:
        return cached_data

    # API 요청 파라미터 구성
    params = build_query_params(
        nPageIndex=page_index,
        nCountPerPage=count_per_page,
        type=response_type,
        mngNo=mng_no,
        nameKo=name_ko,
        nameCh=name_ch,
        diffName=diff_name,
        birthday=birthday,
        lastday=lastday,
        sex=sex,
        registerLargeDiv=register_large_div,
        registerMidDiv=register_mid_div,
        judgeYear=judge_year,
        hunkuk=hunkuk,
        workoutAffil=workout_affil,
        achivement=achivement,
        achivement_ko=achivement_ko
    )
    
    # API 요청
    endpoint = f"{BASE_URL}/publicReportList.do"
    logger.info(f"공적조서 요청: {endpoint}, 파라미터: {params}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            
            # 응답 형식에 따라 처리
            if response_type.upper() == "JSON":
                result = response.json()
            else:  # XML
                # XML 응답 파싱
                result = parse_xml_response(response.text)
            
            if "error" not in result:
                # 캐시 저장
                cache_manager.set(cache_key, result)
            
            return result
    except httpx.TimeoutException:
        logger.error("API 요청 시간 초과")
        raise RuntimeError("API 요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP 상태 오류: {e.response.status_code} - {str(e)}")
        raise RuntimeError(f"HTTP 상태 오류: {e.response.status_code}. 요청을 처리할 수 없습니다.")
    except httpx.HTTPError as e:
        logger.error(f"HTTP 요청 오류: {str(e)}")
        raise RuntimeError(f"HTTP 요청 오류: {str(e)}")
    except Exception as e:
        logger.error(f"공적조서 조회 중 오류 발생: {str(e)}")
        raise RuntimeError(f"공적조서 조회 중 오류 발생: {str(e)}")