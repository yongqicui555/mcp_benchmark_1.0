"""
독립유공자 공훈록 MCP 서버 - 설정 모듈

이 모듈은 서버의 기본 설정과 초기화를 담당합니다.
"""

import os
import logging
from dotenv import load_dotenv
from mcp.server import Server

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gonghun_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gonghun-server")

# API 설정
BASE_URL = os.getenv("BASE_URL", "https://e-gonghun.mpva.go.kr/opnAPI")

# 코드 정의
SEX_CODES = {
    "0": "여",
    "1": "남"
}

HUNKUK_CODES = {
    "PSG00002": "대한민국장",
    "PSG00003": "대통령장",
    "PSG00004": "독립장",
    "PSG00005": "애국장",
    "PSG00006": "애족장",
    "PSG00007": "건국포장",
    "PSG00008": "대통령표창"
}

WORKOUT_AFFIL_CODES = {
    "UGC00002": "의병",
    "UGC00003": "3.1운동",
    "UGC00004": "문화운동",
    "UGC00005": "국내항일",
    "UGC00006": "의열투쟁",
    "UGC00007": "학생운동",
    "UGC00008": "광복군",
    "UGC00009": "계몽운동",
    "UGC00010": "임시정부",
    "UGC00011": "일본방면",
    "UGC00012": "만주방면",
    "UGC00013": "중국방면",
    "UGC00014": "노령방면",
    "UGC00015": "미주방면",
    "UGC00017": "인도네시아방면",
    "UGC00023": "독립운동지원",
    "UGC00024": "구주방면"
}

# MCP 서버 인스턴스 생성
app = Server("gonghun-server")