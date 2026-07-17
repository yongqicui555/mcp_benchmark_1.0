"""
독립유공자 공훈록 MCP 서버 - 유틸리티 모듈

이 모듈은 다양한 유틸리티 함수들을 제공합니다.
"""

import xml.etree.ElementTree as ET
import json
from typing import Dict, Any, Tuple, List, Optional, Union
from .config import logger, SEX_CODES, HUNKUK_CODES, WORKOUT_AFFIL_CODES

def parse_xml_response(response_text: str) -> Dict[str, Any]:
    """
    XML 응답을 파싱하여 딕셔너리로 변환합니다.
    
    Args:
        response_text: XML 형식의 응답 문자열
        
    Returns:
        파싱된 결과를 담은 딕셔너리
    """
    try:
        root = ET.fromstring(response_text)
        
        # 총 개수 및 페이지 정보 파싱
        total_count = root.find("TOTAL_COUNT")
        page_count = root.find("PAGE_COUNT")
        page_index = root.find("PAGE_INDEX")
        count_per_page = root.find("COUNT_PER_PAGE")
        item_count = root.find("ITEM_COUNT")
        
        result = {
            "totalCount": int(total_count.text) if total_count is not None else 0,
            "pageCount": int(page_count.text) if page_count is not None else 0,
            "pageIndex": int(page_index.text) if page_index is not None else 0,
            "countPerPage": int(count_per_page.text) if count_per_page is not None else 0,
            "itemCount": int(item_count.text) if item_count is not None else 0,
            "items": []
        }
        
        # 아이템 파싱
        items_elem = root.find("ITEMS")
        if items_elem is None:
            return result
            
        for item_elem in items_elem.findall("ITEM"):
            item = {}
            for elem in item_elem:
                if elem.tag == "REFERENCES":
                    # 참고문헌 파싱
                    references = []
                    for ref_elem in elem.findall("REFERENCE"):
                        ref = {}
                        book_name = ref_elem.find("BOOK_NAME")
                        if book_name is not None:
                            ref["bookName"] = book_name.text
                        
                        links = []
                        links_elem = ref_elem.find("LINKS")
                        if links_elem is not None:
                            for link_elem in links_elem.findall("LINK"):
                                link = {}
                                name = link_elem.find("NAME")
                                url = link_elem.find("URL")
                                if name is not None:
                                    link["name"] = name.text
                                if url is not None:
                                    link["url"] = url.text
                                links.append(link)
                        
                        ref["links"] = links
                        references.append(ref)
                    
                    item["references"] = references
                else:
                    # 일반 태그 파싱
                    tag_name = elem.tag.lower()
                    item[tag_name] = elem.text if elem.text is not None else ""
            
            # 코드값을 텍스트로 변환
            if "sex" in item:
                item["sexText"] = SEX_CODES.get(item["sex"], "")
            
            if "hunkuk" in item:
                item["hunkukText"] = HUNKUK_CODES.get(item["hunkuk"], "")
            
            if "workout_affil" in item:
                item["workoutAffilText"] = WORKOUT_AFFIL_CODES.get(item["workout_affil"], "")
            
            result["items"].append(item)
        
        return result
    except ET.ParseError as e:
        logger.error(f"XML 파싱 오류: {str(e)}")
        return {
            "error": True,
            "message": f"XML 파싱 오류: {str(e)}",
            "items": []
        }
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}")
        return {
            "error": True,
            "message": f"예상치 못한 오류: {str(e)}",
            "items": []
        }

def parse_resource_uri(uri_str: str) -> Tuple[str, List[str]]:
    """
    리소스 URI를 파싱하여 리소스 타입과 경로 파라미터를 반환합니다.
    
    Args:
        uri_str: 리소스 URI 문자열
        
    Returns:
        리소스 타입과 경로 파라미터의 튜플
        
    Raises:
        ValueError: URI 형식이 올바르지 않은 경우
    """
    if not uri_str.startswith("gonghun://"):
        raise ValueError(f"지원하지 않는 리소스 URI 형식: {uri_str}")
    
    # gonghun:// 제거
    path = uri_str.replace("gonghun://", "")
    
    # 첫 번째 '/'까지의 부분이 리소스 타입
    parts = path.split('/', 1)
    if len(parts) < 2:
        raise ValueError(f"잘못된 리소스 URI 형식: {uri_str}")
    
    resource_type = parts[0]
    params = parts[1].split('/')
    
    return resource_type, params

def format_response(data: Dict[str, Any]) -> str:
    """
    응답 데이터를 형식화된 JSON 문자열로 변환합니다.
    
    Args:
        data: 응답 데이터
        
    Returns:
        형식화된 JSON 문자열
    """
    return json.dumps(data, ensure_ascii=False, indent=2)

def create_error_response(message: str) -> Dict[str, Any]:
    """
    오류 응답을 생성합니다.
    
    Args:
        message: 오류 메시지
        
    Returns:
        오류 응답 데이터
    """
    return {
        "error": True,
        "message": message
    }

def build_query_params(
    nPageIndex: Optional[int] = 1,
    nCountPerPage: Optional[int] = 10,
    type: Optional[str] = "JSON",
    mngNo: Optional[str] = None,
    nameKo: Optional[str] = None,
    nameCh: Optional[str] = None,
    diffName: Optional[str] = None,
    birthday: Optional[str] = None,
    lastday: Optional[str] = None,
    sex: Optional[str] = None,
    registerLargeDiv: Optional[str] = None,
    registerMidDiv: Optional[str] = None,
    judgeYear: Optional[str] = None,
    hunkuk: Optional[str] = None,
    workoutAffil: Optional[str] = None,
    achivement: Optional[str] = None,
    achivement_ko: Optional[str] = None
) -> Dict[str, Union[str, int]]:
    """
    쿼리 파라미터를 구성합니다.
    
    Args:
        nPageIndex: 페이지 번호
        nCountPerPage: 페이지 당 데이터 건수
        type: 응답 형식 (JSON/XML)
        mngNo: 관리번호
        nameKo: 성명(한글)
        nameCh: 성명(한자)
        diffName: 이명
        birthday: 생년월일
        lastday: 사망년월일
        sex: 성별
        registerLargeDiv: 본적대분류
        registerMidDiv: 본적중분류
        judgeYear: 포상년도
        hunkuk: 훈격
        workoutAffil: 운동계열
        achivement: 공훈록/공적개요
        achivement_ko: 공적개요 국한문병기
        
    Returns:
        구성된 쿼리 파라미터
    """
    params = {
        "nPageIndex": nPageIndex,
        "nCountPerPage": nCountPerPage,
        "type": type
    }
    
    # 선택적 파라미터 추가
    if mngNo:
        params["mngNo"] = mngNo
    if nameKo:
        params["nameKo"] = nameKo
    if nameCh:
        params["nameCh"] = nameCh
    if diffName:
        params["diffName"] = diffName
    if birthday:
        params["birthday"] = birthday
    if lastday:
        params["lastday"] = lastday
    if sex:
        params["sex"] = sex
    if registerLargeDiv:
        params["registerLargeDiv"] = registerLargeDiv
    if registerMidDiv:
        params["registerMidDiv"] = registerMidDiv
    if judgeYear:
        params["judgeYear"] = judgeYear
    if hunkuk:
        params["hunkuk"] = hunkuk
    if workoutAffil:
        params["workoutAffil"] = workoutAffil
    if achivement:
        params["achivement"] = achivement
    if achivement_ko:
        params["achivement_ko"] = achivement_ko
        
    return params