"""
독립유공자 공훈록 MCP 서버 - 서버 모듈

이 모듈은 MCP 서버의 리소스, 프롬프트, 도구에 대한 핸들러를 정의합니다.
"""

from typing import Dict, Any, List, Optional, Union
from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
from pydantic import AnyUrl

# MCP 독립유공자 도구 - 국가보훈처 공훈록 및 공적조서 데이터를 조회하는 도구입니다.

from .config import app, logger
from .utils import parse_resource_uri
from .api import fetch_merit_list, fetch_public_report

@app.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """
    사용 가능한 독립유공자 공훈록 관련 리소스를 나열합니다.
    이 함수는 MCP가 도구를 초기화할 때 호출되어 이용 가능한 독립유공자 데이터 리소스 목록을 제공합니다.
    
    Returns:
        리소스 목록: 독립유공자 공훈록, 공적조서, 훈격 코드, 운동계열 코드 등의 리소스 정보
    """
    try:
        resources = [
            types.Resource(
                uri=AnyUrl(f"gonghun://merit/all"),
                name="독립유공자 공훈록",
                description="독립유공자 공훈록 정보 - 독립유공자의 기본 정보와 포상 내역을 제공합니다.",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl(f"gonghun://report/all"),
                name="독립유공자 공적조서",
                description="독립유공자 공적조서 정보 - 독립유공자의 상세한 활동 내역과 공적 사항을 제공합니다.",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl(f"gonghun://code/hunkuk"),
                name="훈격 코드 정보",
                description="독립유공자 훈격 코드 정보 - 건국훈장, 건국포장, 대통령표창 등의 훈격 분류 체계를 제공합니다.",
                mimeType="application/json",
            ),
            types.Resource(
                uri=AnyUrl(f"gonghun://code/workout"),
                name="운동계열 코드 정보",
                description="독립유공자 운동계열 코드 정보 - 3.1운동, 의병활동, 광복군, 임시정부 등 독립운동 유형 분류 체계를 제공합니다.",
                mimeType="application/json",
            )
        ]
        return resources
    except Exception as e:
        logger.error(f"리소스 목록 가져오기 오류: {str(e)}")
        return []

@app.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    특정 독립유공자 공훈록 관련 리소스 정보를 읽습니다.
    이 함수는 MCP가 특정 독립유공자 데이터를 요청할 때 호출됩니다.
    
    Args:
        uri: 리소스 URI (예: gonghun://merit/all, gonghun://report/all 등)
        
    Returns:
        리소스 내용: JSON 형식의 독립유공자 데이터
        
    Raises:
        ValueError: 지원하지 않는 URI나 리소스 타입 요청 시 발생
    """
    try:
        # URI 파싱
        resource_type, params = parse_resource_uri(str(uri))
        
        if resource_type == "merit":
            # 공훈록 목록 조회
            data = await fetch_merit_list(
                page_index=1,
                count_per_page=10,
                response_type="JSON"
            )
            return str(data)
        
        elif resource_type == "report":
            # 공적조서 조회
            data = await fetch_public_report(
                page_index=1,
                count_per_page=10,
                response_type="JSON"
            )
            return str(data)
        
        elif resource_type == "code":
            from .config import HUNKUK_CODES, WORKOUT_AFFIL_CODES
            
            if params[0] == "hunkuk":
                # 훈격 코드 정보
                return str(HUNKUK_CODES)
            
            elif params[0] == "workout":
                # 운동계열 코드 정보
                return str(WORKOUT_AFFIL_CODES)
            
            else:
                raise ValueError(f"지원하지 않는 코드 타입: {params[0]}")
        
        else:
            raise ValueError(f"지원하지 않는 리소스 타입: {resource_type}")
    
    except Exception as e:
        logger.error(f"리소스 읽기 오류: {str(e)}")
        raise ValueError(f"리소스 읽기 오류: {str(e)}")

@app.list_prompts()
async def handle_list_prompts() -> List[types.Prompt]:
    """
    사용 가능한 프롬프트를 나열합니다.
    이 함수는 MCP가 사용자에게 제공할 수 있는 프롬프트 템플릿 목록을 정의합니다.
    
    Returns:
        프롬프트 목록: 독립유공자 검색을 위한 프롬프트 템플릿 정보
    """
    return [
        types.Prompt(
            name="search-independence-activist",
            description="이름, 운동계열, 지역 등의 조건으로 독립유공자 정보를 검색합니다",
            arguments=[
                types.PromptArgument(
                    name="name",
                    description="독립유공자 이름 (예: 유관순, 안중근 등)",
                    required=False,
                ),
                types.PromptArgument(
                    name="workout",
                    description="운동계열 (예: 3.1운동, 광복군, 의병활동, 임시정부 등)",
                    required=False,
                ),
                types.PromptArgument(
                    name="region",
                    description="본적 지역 (예: 서울, 평안남도, 경기도 등)",
                    required=False,
                )
            ],
        )
    ]

@app.get_prompt()
async def handle_get_prompt(
    name: str, arguments: Dict[str, str] | None
) -> types.GetPromptResult:
    """
    프롬프트를 생성합니다.
    이 함수는 사용자가 독립유공자 검색 프롬프트를 요청할 때 호출되어 적절한 프롬프트 텍스트를 생성합니다.
    
    Args:
        name: 프롬프트 이름 (예: "search-independence-activist")
        arguments: 프롬프트 인수 (이름, 운동계열, 지역 등의 검색 조건)
        
    Returns:
        프롬프트 결과: 검색 조건에 맞는 독립유공자 정보 조회 프롬프트
        
    Raises:
        ValueError: 지원하지 않는 프롬프트 이름 요청 시 발생
    """
    if name != "search-independence-activist":
        raise ValueError(f"알 수 없는 프롬프트: {name}")

    activist_name = (arguments or {}).get("name", "")
    workout = (arguments or {}).get("workout", "")
    region = (arguments or {}).get("region", "")

    prompt_text = "독립유공자 정보를 조회합니다.\n\n"
    
    if activist_name:
        prompt_text += f"이름: {activist_name}\n"
    if workout:
        prompt_text += f"운동계열: {workout}\n"
    if region:
        prompt_text += f"본적 지역: {region}\n"
    
    prompt_text += "\n위 정보를 바탕으로 독립유공자를 검색하고, 해당 독립유공자의 생애, 주요 독립운동 활동, 공적과 역사적 의의를 상세히 설명해주세요. 가능하면 관련된 다른 독립운동가나 역사적 사건도 함께 언급해주세요."

    return types.GetPromptResult(
        description="독립유공자 정보 검색",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=prompt_text
                ),
            )
        ],
    )