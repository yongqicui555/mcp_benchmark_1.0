"""
독립유공자 공훈록 MCP 서버 - 도구 모듈

이 모듈은 MCP 서버의 도구 처리를 담당합니다.
"""

import json
import logging
from typing import List, Any, Union, Dict, Optional
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource, EmptyResult, LoggingLevel

from .config import logger, app, HUNKUK_CODES, WORKOUT_AFFIL_CODES
from .api import fetch_merit_list, fetch_public_report
from .cache import cache_manager
from .utils import format_response, create_error_response

@app.list_tools()
async def list_tools() -> List[Tool]:
    """
    사용 가능한 독립유공자 공훈록 관련 도구들을 나열합니다.
    
    Returns:
        도구 목록
    """
    try:
        return [
            Tool(
                name="get_merit_list",
                description="독립유공자 공훈록 목록을 조회합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_index": {
                            "type": "integer",
                            "description": "페이지 번호",
                            "default": 1
                        },
                        "count_per_page": {
                            "type": "integer",
                            "description": "페이지 당 데이터 건수 (최대 50건)",
                            "default": 10,
                            "maximum": 50
                        },
                        "mng_no": {
                            "type": "string",
                            "description": "관리번호"
                        },
                        "name_ko": {
                            "type": "string",
                            "description": "성명(한글)"
                        },
                        "name_ch": {
                            "type": "string",
                            "description": "성명(한자)"
                        },
                        "diff_name": {
                            "type": "string",
                            "description": "이명"
                        },
                        "birthday": {
                            "type": "string",
                            "description": "생년월일 (YYYYMMDD, 년(1945), 년월(194501), 년월일(19450101))"
                        },
                        "lastday": {
                            "type": "string",
                            "description": "사망년월일 (YYYYMMDD, 년(1945), 년월(194501), 년월일(19450101))"
                        },
                        "sex": {
                            "type": "string",
                            "description": "성별 (0: 여, 1: 남)",
                            "enum": ["0", "1"]
                        },
                        "register_large_div": {
                            "type": "string",
                            "description": "본적대분류"
                        },
                        "register_mid_div": {
                            "type": "string",
                            "description": "본적중분류"
                        },
                        "judge_year": {
                            "type": "string",
                            "description": "포상년도"
                        },
                        "hunkuk": {
                            "type": "string",
                            "description": "훈격",
                            "enum": list(HUNKUK_CODES.keys())
                        },
                        "workout_affil": {
                            "type": "string",
                            "description": "운동계열",
                            "enum": list(WORKOUT_AFFIL_CODES.keys())
                        },
                        "achivement": {
                            "type": "string",
                            "description": "공훈록"
                        }
                    }
                }
            ),
            Tool(
                name="get_public_report",
                description="독립유공자 공적조서를 조회합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_index": {
                            "type": "integer",
                            "description": "페이지 번호",
                            "default": 1
                        },
                        "count_per_page": {
                            "type": "integer",
                            "description": "페이지 당 데이터 건수 (최대 50건)",
                            "default": 10,
                            "maximum": 50
                        },
                        "mng_no": {
                            "type": "string",
                            "description": "관리번호"
                        },
                        "name_ko": {
                            "type": "string",
                            "description": "성명(한글)"
                        },
                        "name_ch": {
                            "type": "string",
                            "description": "성명(한자)"
                        },
                        "diff_name": {
                            "type": "string",
                            "description": "이명"
                        },
                        "birthday": {
                            "type": "string",
                            "description": "생년월일 (YYYYMMDD, 년(1945), 년월(194501), 년월일(19450101))"
                        },
                        "lastday": {
                            "type": "string",
                            "description": "사망년월일 (YYYYMMDD, 년(1945), 년월(194501), 년월일(19450101))"
                        },
                        "sex": {
                            "type": "string",
                            "description": "성별 (0: 여, 1: 남)",
                            "enum": ["0", "1"]
                        },
                        "register_large_div": {
                            "type": "string",
                            "description": "본적대분류"
                        },
                        "register_mid_div": {
                            "type": "string",
                            "description": "본적중분류"
                        },
                        "judge_year": {
                            "type": "string",
                            "description": "포상년도"
                        },
                        "hunkuk": {
                            "type": "string",
                            "description": "훈격",
                            "enum": list(HUNKUK_CODES.keys())
                        },
                        "workout_affil": {
                            "type": "string",
                            "description": "운동계열",
                            "enum": list(WORKOUT_AFFIL_CODES.keys())
                        },
                        "achivement": {
                            "type": "string",
                            "description": "공적개요"
                        },
                        "achivement_ko": {
                            "type": "string",
                            "description": "공적개요 국한문병기"
                        }
                    }
                }
            ),
            Tool(
                name="get_hunkuk_codes",
                description="훈격 코드 정보를 조회합니다",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="get_workout_affil_codes",
                description="운동계열 코드 정보를 조회합니다",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="clear_cache",
                description="캐시된 데이터를 모두 초기화합니다",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    except Exception as e:
        logger.error(f"도구 목록 생성 중 오류 발생: {str(e)}")
        # 최소한의 기본 도구라도 반환
        return [
            Tool(
                name="get_merit_list",
                description="독립유공자 공훈록 목록을 조회합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_index": {
                            "type": "integer",
                            "description": "페이지 번호",
                            "default": 1
                        },
                        "count_per_page": {
                            "type": "integer",
                            "description": "페이지 당 데이터 건수 (최대 50건)",
                            "default": 10
                        }
                    }
                }
            )
        ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[Union[TextContent, ImageContent, EmbeddedResource]]:
    """
    독립유공자 공훈록 관련 도구를 호출합니다.
    
    Args:
        name: 도구 이름
        arguments: 도구 인수
        
    Returns:
        도구 실행 결과
    """
    try:
        logger.info(f"도구 호출: {name}, 인수: {arguments}")
        
        if name == "get_merit_list":
            # 공훈록 목록 조회
            if not isinstance(arguments, dict):
                arguments = {}
            
            data = await fetch_merit_list(
                page_index=arguments.get("page_index", 1),
                count_per_page=min(arguments.get("count_per_page", 10), 50),
                response_type="JSON",
                mng_no=arguments.get("mng_no"),
                name_ko=arguments.get("name_ko"),
                name_ch=arguments.get("name_ch"),
                diff_name=arguments.get("diff_name"),
                birthday=arguments.get("birthday"),
                lastday=arguments.get("lastday"),
                sex=arguments.get("sex"),
                register_large_div=arguments.get("register_large_div"),
                register_mid_div=arguments.get("register_mid_div"),
                judge_year=arguments.get("judge_year"),
                hunkuk=arguments.get("hunkuk"),
                workout_affil=arguments.get("workout_affil"),
                achivement=arguments.get("achivement")
            )
            
            result_json = format_response(data)
            logger.debug(f"공훈록 목록 조회 결과: {result_json}")
            
            return [
                TextContent(
                    type="text",
                    text=result_json
                )
            ]
        
        elif name == "get_public_report":
            # 공적조서 조회
            if not isinstance(arguments, dict):
                arguments = {}
            
            data = await fetch_public_report(
                page_index=arguments.get("page_index", 1),
                count_per_page=min(arguments.get("count_per_page", 10), 50),
                response_type="JSON",
                mng_no=arguments.get("mng_no"),
                name_ko=arguments.get("name_ko"),
                name_ch=arguments.get("name_ch"),
                diff_name=arguments.get("diff_name"),
                birthday=arguments.get("birthday"),
                lastday=arguments.get("lastday"),
                sex=arguments.get("sex"),
                register_large_div=arguments.get("register_large_div"),
                register_mid_div=arguments.get("register_mid_div"),
                judge_year=arguments.get("judge_year"),
                hunkuk=arguments.get("hunkuk"),
                workout_affil=arguments.get("workout_affil"),
                achivement=arguments.get("achivement"),
                achivement_ko=arguments.get("achivement_ko")
            )
            
            result_json = format_response(data)
            logger.debug(f"공적조서 조회 결과: {result_json}")
            
            return [
                TextContent(
                    type="text",
                    text=result_json
                )
            ]
            
        elif name == "get_hunkuk_codes":
            # 훈격 코드 정보 조회
            result_json = format_response(HUNKUK_CODES)
            return [
                TextContent(
                    type="text",
                    text=result_json
                )
            ]
            
        elif name == "get_workout_affil_codes":
            # 운동계열 코드 정보 조회
            result_json = format_response(WORKOUT_AFFIL_CODES)
            return [
                TextContent(
                    type="text",
                    text=result_json
                )
            ]
            
        elif name == "clear_cache":
            # 캐시 초기화
            cache_manager.clear()
            return [
                TextContent(
                    type="text",
                    text=format_response({
                        "success": True,
                        "message": "캐시가 성공적으로 초기화되었습니다."
                    })
                )
            ]
        else:
            raise ValueError(f"지원하지 않는 도구: {name}")
    except ValueError as e:
        logger.error(f"도구 인수 오류: {str(e)}")
        return [
            TextContent(
                type="text",
                text=format_response(create_error_response(str(e)))
            )
        ]
    except RuntimeError as e:
        logger.error(f"도구 실행 오류: {str(e)}")
        return [
            TextContent(
                type="text",
                text=format_response(create_error_response(str(e)))
            )
        ]
    except Exception as e:
        logger.error(f"도구 호출 중 예상치 못한 오류: {str(e)}")
        return [
            TextContent(
                type="text",
                text=format_response(create_error_response(f"도구 실행 중 오류가 발생했습니다: {str(e)}"))
            )
        ]

@app.set_logging_level()
async def set_logging_level(level: LoggingLevel) -> EmptyResult:
    """로깅 레벨을 설정합니다.
    
    Args:
        level: 설정할 로깅 레벨
        
    Returns:
        빈 결과
    """

    try:
        level_str = level.upper()
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        
        if level_str in level_map:
            logger.setLevel(level_map[level_str])
            logger.info(f"로그 레벨이 {level_str}로 설정되었습니다")
            
            if hasattr(app, "request_context") and app.request_context and hasattr(app.request_context, "session"):
                await app.request_context.session.send_log_message(
                    level="info",
                    data=f"로그 레벨이 {level_str}로 설정되었습니다",
                    logger="gonghun-server"
                )
        else:
            logger.warning(f"알 수 없는 로그 레벨: {level_str}")
            if hasattr(app, "request_context") and app.request_context and hasattr(app.request_context, "session"):
                await app.request_context.session.send_log_message(
                    level="warning",
                    data=f"알 수 없는 로그 레벨: {level_str}",
                    logger="gonghun-server"
                )
    except Exception as e:
        logger.error(f"로깅 레벨 설정 중 오류 발생: {str(e)}")
    
    return EmptyResult()