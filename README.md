# AI 인테리어 이미지 생성 API

원룸 사진 1개를 입력하면 5가지 스타일(미니멀리스트, 스칸디나비안, 모던, 빈티지, 인더스트리얼)로 변환된 이미지를 15초 이내에 생성하는 AI 기반 API입니다.

## 주요 기능

- 단일 이미지 업로드로 5개 스타일 동시 생성 (병렬 처리)
- 15초 이내 모든 스타일 이미지 생성 (타임아웃 설정)
- 원본 분석 후 선택적 개선 (Analysis-First Approach)
- 한국어 분석 텍스트 제공
- Docker 컨테이너 기반 배포
- RESTful API 제공

## 기술 스택

- Backend: FastAPI (Python 3.11)
- AI: Google Gemini 2.5 Flash Image
- Container: Docker, Docker Compose
- Image Processing: PIL (Pillow)

## 빠른 시작

### 1. 사전 요구사항
```bash
- Docker & Docker Compose 설치
- Google Gemini API 키 발급 (https://aistudio.google.com/app/apikey)
```

### 2. 설치 및 실행
```bash
# 저장소 클론
git clone <repository-url>
cd backend

# 환경변수 설정
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Docker 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3. API 테스트
```bash
# Health Check
curl http://localhost:8000/health

# 이미지 생성
curl -X POST http://localhost:8000/api/get_styled_images \
  -F "file=@test_room.jpg" \
  -o response.json

# 결과 확인
cat response.json
```

## API 엔드포인트

### POST /api/get_styled_images (핵심 엔드포인트)

이미지 1개를 업로드하여 5개 스타일 이미지 생성

**요청:**
```bash
curl -X POST http://localhost:8000/api/get_styled_images \
  -F "file=@room.jpg"
```

**응답:**
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
      "analysis": "현재 방 분석:\n- 잘되어 있는 점: ...\n개선 내용: ...",
      "success": true
    },
    ...
  ]
}
```

### GET /api/images/{filename}

생성된 이미지 다운로드

```bash
curl http://localhost:8000/api/images/generated_xyz1.png -o result.png
```

### GET /api/styles

사용 가능한 스타일 목록 조회

```bash
curl http://localhost:8000/api/styles
```

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── routes/
│   │   └── design.py        # API 엔드포인트 (병렬 처리 로직)
│   ├── services/
│   │   └── gemini_service.py  # Gemini API 통합
│   └── models/
│       └── schemas.py       # Pydantic 데이터 모델
├── templates/               # HTML 템플릿
├── static/                  # 정적 파일
├── uploads/                 # 업로드/생성 이미지 저장소
├── test_images/             # 테스트용 이미지
├── Dockerfile               # Docker 이미지 빌드
├── docker-compose.yml       # Docker Compose 설정
├── test_api.py              # API 테스트 스크립트
├── DEPLOYMENT_GUIDE.md      # 상세 배포 가이드
├── EVALUATION_TEMPLATE.md   # 품질 평가표
└── requirements.txt         # Python 의존성
```

## 테스트

### 자동 테스트 실행

```bash
# 테스트 이미지 준비 (test_images/ 디렉토리에 10개 이미지 넣기)
ls test_images/

# 테스트 실행
pip install requests
python test_api.py --endpoint http://localhost:8000 --images test_images

# 평가 보고서 확인
cat evaluation_report.md
```

### 평가 기준
- 성능: 15초 이내 5개 스타일 모두 생성
- 안정성: 전체 성공률 95% 이상
- 품질: 스타일별 성공률 90% 이상

## 배포

상세한 배포 가이드는 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)를 참조하세요.

### 프로덕션 배포 요약

```bash
# 서버에서
git clone <repository-url>
cd backend

# 환경변수 설정
nano .env  # GEMINI_API_KEY 입력

# 실행
docker-compose up -d

# Nginx 리버스 프록시 (선택)
# DEPLOYMENT_GUIDE.md 참조
```

## 성능 최적화

### 병렬 처리
- `asyncio.gather`를 사용한 5개 스타일 동시 생성
- 15초 타임아웃 설정

### Docker 최적화
- 멀티스테이지 빌드로 이미지 크기 최소화
- 런타임 의존성만 포함

## 개발 로드맵

### 현재 버전 (v1.0 - MVP)
- 기본 이미지 생성 기능
- 5개 스타일 지원
- Docker 배포

### 향후 계획 (v2.0)
- 사용자 인증 시스템
- 결제 시스템 통합
- 데이터베이스 (PostgreSQL)
- 이미지 품질 자동 평가
- 사용자 피드백 시스템

## 기술 문서

- [시스템 플로우 보고서](system_flow_report.md)
- [향후 고도화 방안](future_enhancement_report.md)
- [배포 가이드](DEPLOYMENT_GUIDE.md)
- [평가 템플릿](EVALUATION_TEMPLATE.md)

## 라이선스

MIT License

## 문의

이슈 발생 시 GitHub Issues를 통해 문의해주세요.
