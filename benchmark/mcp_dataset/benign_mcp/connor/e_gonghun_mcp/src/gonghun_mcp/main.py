"""
독립유공자 공훈록 MCP 서버 - 메인 모듈

이 모듈은 서버의 메인 실행 함수를 제공합니다.
"""

import asyncio
import os
import logging
import mcp.server.stdio
from .config import logger, app

async def main():
    """
    서버의 메인 실행 함수입니다.
    """
    logger.info("독립유공자 공훈록 MCP 서버를 시작합니다...")
    
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"서버 실행 중 오류 발생: {str(e)}")
        raise
    finally:
        logger.info("독립유공자 공훈록 MCP 서버를 종료합니다.")

def run():
    """
    서버 실행 진입점 함수입니다.
    """
    try:
        # 로그 레벨 설정 (기본값은 INFO)
        logging_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if hasattr(logging, logging_level):
            logger.setLevel(getattr(logging, logging_level))
            logger.info(f"로그 레벨이 {logging_level}로 설정되었습니다.")
        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("사용자에 의해 서버가 중지되었습니다.")
    except Exception as e:
        logger.critical(f"서버 실행 중 치명적인 오류 발생: {str(e)}")
        exit(1)