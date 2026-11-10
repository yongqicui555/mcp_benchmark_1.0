FROM python:3.13-slim

WORKDIR /app
COPY . /app

# pip로 의존성 설치
RUN pip install "kubernetes>=32.0.1" "mcp[cli]>=1.6.0" "ruff>=0.11.5" "pyyaml"

CMD ["python", "k8s_pilot.py"]
