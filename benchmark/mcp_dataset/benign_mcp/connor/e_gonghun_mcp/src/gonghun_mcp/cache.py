"""
독립유공자 공훈록 MCP 서버 - 캐시 모듈

이 모듈은 API 응답 데이터의 캐싱을 담당합니다.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from .config import logger

class CacheManager:
    """API 응답 데이터를 캐싱하는 클래스"""
    
    def __init__(self, timeout_minutes: int = 30):
        """
        캐시 매니저를 초기화합니다.
        
        Args:
            timeout_minutes: 캐시 만료 시간(분)
        """
        self.timeout = timedelta(minutes=timeout_minutes)
        self.last_cache_time = {}
        self.cache_data = {}
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        캐시에서 데이터를 가져옵니다.
        
        Args:
            key: 캐시 키
            
        Returns:
            캐시된 데이터, 없거나 만료된 경우 None
        """
        now = datetime.now()
        if (key in self.cache_data and
            key in self.last_cache_time and
            now - self.last_cache_time[key] <= self.timeout):
            logger.debug(f"캐시된 데이터를 반환합니다: {key}")
            return self.cache_data[key]
        return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """
        캐시에 데이터를 저장합니다.
        
        Args:
            key: 캐시 키
            data: 저장할 데이터
        """
        self.cache_data[key] = data
        self.last_cache_time[key] = datetime.now()
        logger.debug(f"데이터가 캐시되었습니다: {key}")
    
    def clear(self) -> None:
        """모든 캐시를 초기화합니다."""
        self.last_cache_time.clear()
        self.cache_data.clear()
        logger.info("캐시가 초기화되었습니다.")
    
    def remove(self, key: str) -> None:
        """
        특정 키의 캐시를 제거합니다.
        
        Args:
            key: 제거할 캐시 키
        """
        if key in self.cache_data:
            del self.cache_data[key]
        if key in self.last_cache_time:
            del self.last_cache_time[key]
        logger.debug(f"캐시가 제거되었습니다: {key}")

# 캐시 매니저 인스턴스 생성
cache_manager = CacheManager()