# AI 인테리어 이미지 생성 API - 배포 가이드

## 개요

이 API는 단일 원룸 이미지를 입력받아 5가지 스타일(미니멀리스트, 스칸디나비안, 모던, 빈티지, 인더스트리얼)로 변환된 이미지를 15초 이내에 생성합니다.

## 핵심 기능

- 이미지 1개 업로드 → 5개 스타일 이미지 병렬 생성
- 15초 이내 처리 (타임아웃 설정)
- Docker 컨테이너 기반 배포
- RESTful API 제공

---

## 사전 요구사항

### 1. 시스템 요구사항
```
- Docker 20.10 이상
- Docker Compose 2.0 이상
- 메모리: 최소 2GB (권장 4GB)
- CPU: 최소 2 Core (권장 4 Core)
```

### 2. API 키
```
- Google Gemini API 키 필요
- 발급: https://aistudio.google.com/app/apikey
```

---

## 빠른 시작

### 1. 저장소 클론
```bash
git clone <repository-url>
cd backend
```

### 2. 환경변수 설정
```bash
# .env 파일 생성
cat > .env << EOF
GEMINI_API_KEY=your_gemini_api_key_here
EOF
```

### 3. Docker 빌드 및 실행
```bash
# 빌드
docker-compose build

# 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 4. API 동작 확인
```bash
# Health Check
curl http://localhost:8000/health

# 예상 응답:
# {"status":"healthy","gemini_api_key_configured":true}
```

---

## API 사용법

### 엔드포인트: POST /api/get_styled_images

#### 요청
```bash
curl -X POST http://localhost:8000/api/get_styled_images \
  -F "file=@room.jpg" \
  -o response.json
```

#### 응답 예시
```json
{
  "success": true,
  "original_image": "abc123.jpg",
  "processing_time": 12.45,
  "results": [
    {
      "style_id": "minimalist",
      "style_name": "미니멀리스트",
      "generated_image": "generated_xyz1.png",
      "analysis": "현재 방 분석: ...",
      "success": true
    },
    {
      "style_id": "scandinavian",
      "style_name": "스칸디나비안",
      "generated_image": "generated_xyz2.png",
      "analysis": "...",
      "success": true
    },
    ...
  ]
}
```

#### 생성된 이미지 다운로드
```bash
# 원본 이미지
curl http://localhost:8000/api/images/abc123.jpg -o original.jpg

# 생성된 이미지
curl http://localhost:8000/api/images/generated_xyz1.png -o minimalist.png
```

---

## 테스트

### 1. 테스트 이미지 준비
```bash
# 테스트 디렉토리 생성
mkdir -p test_images

# 테스트용 이미지 10개를 test_images/ 디렉토리에 넣기
```

### 2. 자동 테스트 실행
```bash
# 필요한 패키지 설치
pip install requests

# 테스트 실행
python test_api.py --endpoint http://localhost:8000 --images test_images

# 결과 확인
cat evaluation_report.md
```

### 3. 평가 기준
```
성능 요구사항:
- 15초 이내 5개 스타일 모두 생성

안정성 요구사항:
- 전체 성공률 95% 이상
- 스타일별 성공률 90% 이상
```

---

## 프로덕션 배포

### 1. 서버 준비 (Ubuntu 22.04 기준)

#### Docker 설치
```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo apt-get update
sudo apt-get install docker-compose-plugin

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
newgrp docker
```

#### 방화벽 설정
```bash
# UFW 사용 시
sudo ufw allow 8000/tcp
sudo ufw reload
```

### 2. 코드 배포
```bash
# 서버에 코드 복사
scp -r backend/ user@your-server:/home/user/

# 서버에 접속
ssh user@your-server

# 디렉토리 이동
cd /home/user/backend

# 환경변수 설정
nano .env
# GEMINI_API_KEY=your_key_here 입력 후 저장

# Docker 실행
docker-compose up -d
```

### 3. Nginx 리버스 프록시 설정 (선택사항)

#### Nginx 설치
```bash
sudo apt-get install nginx
```

#### 설정 파일 생성
```bash
sudo nano /etc/nginx/sites-available/interior-api
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 타임아웃 설정 (이미지 생성 시간 고려)
        proxy_read_timeout 30s;
        proxy_connect_timeout 30s;
    }

    # 파일 업로드 크기 제한
    client_max_body_size 10M;
}
```

#### Nginx 활성화
```bash
sudo ln -s /etc/nginx/sites-available/interior-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. SSL 인증서 설정 (Let's Encrypt)
```bash
# Certbot 설치
sudo apt-get install certbot python3-certbot-nginx

# 인증서 발급
sudo certbot --nginx -d your-domain.com

# 자동 갱신 확인
sudo certbot renew --dry-run
```

---

## 모니터링 및 유지보수

### 1. 로그 확인
```bash
# 실시간 로그
docker-compose logs -f

# 최근 100줄
docker-compose logs --tail=100

# 특정 컨테이너만
docker logs interior-design-api
```

### 2. 컨테이너 상태 확인
```bash
# 실행 중인 컨테이너
docker ps

# 리소스 사용량
docker stats interior-design-api
```

### 3. 재시작
```bash
# 컨테이너 재시작
docker-compose restart

# 완전 재빌드
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 4. 디스크 공간 관리
```bash
# 오래된 이미지 삭제 (uploads 디렉토리)
find uploads/ -type f -mtime +7 -delete

# Docker 정리
docker system prune -a
```

---

## 트러블슈팅

### 1. API가 15초 안에 응답하지 않음

**원인**: Gemini API 속도 저하 또는 네트워크 문제

**해결**:
```bash
# 타임아웃 늘리기 (docker-compose.yml)
# environment 섹션에 추가:
# - API_TIMEOUT=20
```

### 2. 메모리 부족 오류

**원인**: 동시 요청이 많아 메모리 초과

**해결**:
```bash
# Docker 메모리 제한 설정 (docker-compose.yml)
services:
  interior-design-api:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

### 3. Gemini API 키 오류

**원인**: API 키가 잘못되었거나 만료됨

**해결**:
```bash
# .env 파일 확인
cat .env

# 키 재설정
nano .env

# 컨테이너 재시작
docker-compose restart
```

### 4. 이미지 생성 실패

**원인**: Gemini API quota 초과 또는 네트워크 오류

**해결**:
```bash
# API 사용량 확인
# https://aistudio.google.com/app/apikey

# 로그에서 구체적 오류 확인
docker-compose logs | grep ERROR
```

---

## 성능 최적화

### 1. 워커 수 조정
```yaml
# docker-compose.yml 또는 Dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

주의: 워커 수를 늘리면 메모리 사용량이 증가합니다.

### 2. 이미지 크기 제한
```python
# app/routes/design.py 수정
# 파일 크기 제한 추가 (예: 5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
```

### 3. 캐싱 (향후 개선)
- Redis를 사용한 결과 캐싱
- 동일 이미지 재요청 시 캐시된 결과 반환

---

## 보안 고려사항

### 1. 현재 구현 (MVP)
- 인증 없음 (누구나 접근 가능)
- Rate limiting 없음

### 2. 프로덕션 배포 시 필요 사항
```
- API 키 기반 인증
- Rate limiting (예: IP당 시간당 10회)
- CORS 제한
- 파일 크기 제한
- 악성 파일 검사
```

### 3. 추천 도구
```
- FastAPI-Limiter (Rate limiting)
- Firebase Auth (사용자 인증)
- AWS WAF (웹 방화벽)
```

---

## 비용 산정

### Google Gemini API 비용
```
- Gemini 2.5 Flash Image: 약 $0.15/1M tokens
- 이미지 생성: 별도 과금 (정확한 가격은 Google 문서 참조)

예상 비용 (1000 요청 기준):
- 1000 요청 x 5 스타일 = 5000 이미지
- 예상 비용: $10-30 (사용량에 따라 변동)
```

### 서버 비용
```
- AWS EC2 t3.medium: ~$30/월
- DigitalOcean Droplet (2GB): ~$12/월
- Vultr Cloud Compute (2GB): ~$10/월
```

---

## 다음 단계

### MVP 이후 개선 사항
1. 사용자 인증 및 계정 시스템
2. 결제 시스템 통합
3. 사용 기록 및 대시보드
4. 이미지 품질 평가 시스템
5. 사용자 피드백 수집
6. A/B 테스트

### 확장 계획
1. 데이터베이스 추가 (PostgreSQL)
2. 파일 저장소 분리 (S3)
3. CDN 연동
4. 부하 분산 (Load Balancer)
5. 자동 스케일링

---

## 지원

### 문제 발생 시
1. 로그 확인: `docker-compose logs`
2. Health Check: `curl http://localhost:8000/health`
3. 이슈 등록: GitHub Issues

### 유용한 명령어
```bash
# 전체 상태 확인
docker-compose ps

# 컨테이너 내부 접속
docker exec -it interior-design-api /bin/bash

# 디버그 모드로 실행
docker-compose down
docker-compose up

# 포트 확인
netstat -tulpn | grep 8000
```
