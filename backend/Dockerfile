FROM python:3.11-slim

# 1. uv 바이너리를 공식 이미지에서 복사하여 설치합니다. (가장 빠르고 권장되는 방법)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 2. 시스템 의존성 패키지 설치
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. 의존성 파일 복사 및 설치 (uv 사용)
# --system 플래그를 사용하면 가상환경 없이 컨테이너 시스템에 바로 설치하여 빌드 속도를 높입니다.
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# 4. 소스 코드 복사 및 실행
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
