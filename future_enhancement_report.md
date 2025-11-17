# AI 인테리어 디자인 시스템 향후 고도화 방안

## 1. 개요

### 1.1 고도화 목적
현재 시스템은 기본적인 이미지 분석 및 스타일 적용 기능을 제공하고 있으나, 다음과 같은 고도화를 통해 사용자 경험과 비즈니스 가치를 향상시킬 수 있습니다.

### 1.2 고도화 방향
1. **지식 기반 강화**: RAG를 통한 전문 인테리어 지식 활용
2. **복잡한 워크플로우**: LangGraph를 통한 다단계 의사결정 프로세스
3. **개발 생산성**: LangChain을 통한 체계적인 LLM 애플리케이션 개발
4. **데이터 수집**: 크롤링을 통한 인테리어 트렌드 및 제품 정보 수집
5. **개인화**: 사용자 선호도 학습 및 맞춤형 제안
6. **비즈니스 모델**: 제품 추천 및 판매 연계

---

## 2. RAG (Retrieval-Augmented Generation) 도입

### 2.1 RAG 개념
Retrieval-Augmented Generation은 외부 지식 베이스에서 관련 정보를 검색하여 LLM의 응답 품질을 향상시키는 기법입니다.

### 2.2 적용 시나리오

#### 2.2.1 인테리어 전문 지식 베이스 구축
```
[지식 베이스 구성]
1. 인테리어 디자인 원칙 문서
2. 공간별 가구 배치 가이드
3. 색상 조합 이론
4. 스타일별 특징 및 사례
5. 재료/마감 정보
6. 조명 설계 원칙
7. 동선 설계 이론
```

#### 2.2.2 RAG 워크플로우
```
[사용자 요청]
   |
   v
[이미지 분석 + 텍스트 쿼리 생성]
   |
   v
[Vector DB 검색]
   - 관련 인테리어 원칙 검색
   - 유사 사례 검색
   - 스타일 가이드 검색
   |
   v
[검색 결과 + 이미지 → Gemini]
   |
   v
[전문성 강화된 분석 및 제안]
```

### 2.3 구현 방안

#### 2.3.1 Vector Database 선택
```
옵션 1: ChromaDB
- 장점: 경량, 로컬 실행 가능, Python 친화적
- 단점: 대규모 데이터 처리 제한

옵션 2: Pinecone
- 장점: 클라우드 기반, 확장성 우수, 빠른 검색
- 단점: 유료 서비스

옵션 3: Weaviate
- 장점: 오픈소스, 멀티모달 지원, 확장 가능
- 단점: 설정 복잡도 높음

추천: 초기에는 ChromaDB, 확장 시 Pinecone
```

#### 2.3.2 임베딩 모델
```python
# OpenAI Embeddings
from langchain.embeddings import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# 또는 Google Embeddings
from langchain.embeddings import GoogleGenerativeAIEmbeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
```

#### 2.3.3 문서 수집 및 인덱싱
```python
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

# 1. 문서 로드
loader = DirectoryLoader('./interior_knowledge/', glob="**/*.md")
documents = loader.load()

# 2. 청킹
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(documents)

# 3. 벡터 저장소 생성
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
```

#### 2.3.4 검색 및 응답 생성
```python
async def analyze_room_with_rag(image_path: str, style: str):
    # 1. 쿼리 생성
    query = f"{style} 스타일 인테리어 원칙 및 가구 배치 가이드"

    # 2. 관련 문서 검색 (Top-K)
    relevant_docs = vectorstore.similarity_search(query, k=5)

    # 3. 컨텍스트 구성
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    # 4. 강화된 프롬프트
    prompt = f"""
    You are an interior design expert. Use the following knowledge:

    {context}

    Analyze this room and provide improvements based on {style} style.
    """

    # 5. Gemini 호출
    response = model.generate_content([prompt, image])
    return response
```

### 2.4 기대 효과
1. **전문성 향상**: 검증된 인테리어 원칙 기반 제안
2. **일관성 향상**: 스타일별 일관된 가이드 제공
3. **설명 가능성**: 제안 근거를 지식 베이스에서 제시
4. **학습 비용 절감**: 프롬프트에 모든 지식을 넣지 않아도 됨

---

## 3. LangGraph를 통한 복잡한 워크플로우 구현

### 3.1 LangGraph 개념
LangGraph는 LLM 기반 애플리케이션에서 복잡한 상태 관리와 의사결정 흐름을 구현하기 위한 프레임워크입니다.

### 3.2 적용 시나리오

#### 3.2.1 다단계 인테리어 설계 워크플로우
```
[이미지 입력]
   |
   v
[1단계: 공간 분석 노드]
   - 방 크기 측정
   - 창문/문 위치 파악
   - 기존 가구 식별
   |
   v
[2단계: 문제 진단 노드]
   - 동선 문제 파악
   - 채광 문제 파악
   - 수납 부족 파악
   |
   v
[3단계: 의사결정 노드]
   문제 심각도에 따라 분기:
   - 경미한 문제 → 소품 추가
   - 중간 문제 → 가구 재배치
   - 심각한 문제 → 구조 변경 제안
   |
   v
[4단계: 스타일 적용 노드]
   선택한 스타일로 솔루션 구체화
   |
   v
[5단계: 제품 추천 노드]
   필요한 가구/소품 제품 추천
   |
   v
[6단계: 이미지 생성 노드]
   최종 이미지 생성
   |
   v
[7단계: 예산 산출 노드]
   추천 제품 기반 예산 계산
```

#### 3.2.2 조건부 워크플로우
```
[스타일 선택]
   |
   v
[조건 검사]
   |
   +-- 미니멀리스트? → [단순화 노드] → [불필요 요소 제거]
   |
   +-- 빈티지? → [앤티크 검색 노드] → [복고풍 소품 추천]
   |
   +-- 인더스트리얼? → [원자재 노출 노드] → [벽돌/금속 적용]
```

### 3.3 구현 방안

#### 3.3.1 LangGraph 설치
```bash
pip install langgraph langchain langchain-core
```

#### 3.3.2 그래프 정의
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# 상태 정의
class InteriorDesignState(TypedDict):
    image_path: str
    style: str
    room_analysis: dict
    issues: list
    solutions: list
    products: list
    budget: float
    generated_image: str
    analysis_text: str

# 노드 함수들
async def analyze_space(state: InteriorDesignState):
    """1단계: 공간 분석"""
    analysis = await gemini_service.analyze_room(state["image_path"])
    return {"room_analysis": analysis}

async def diagnose_issues(state: InteriorDesignState):
    """2단계: 문제 진단"""
    issues = []
    analysis = state["room_analysis"]

    # 규칙 기반 문제 진단
    if "채광 부족" in analysis.get("issues", []):
        issues.append({"type": "lighting", "severity": "high"})

    if "수납 부족" in analysis.get("issues", []):
        issues.append({"type": "storage", "severity": "medium"})

    return {"issues": issues}

async def decide_solution_type(state: InteriorDesignState):
    """3단계: 솔루션 타입 결정"""
    max_severity = max([i["severity"] for i in state["issues"]], default="low")

    if max_severity == "high":
        return "major_renovation"
    elif max_severity == "medium":
        return "furniture_rearrangement"
    else:
        return "minor_decoration"

async def apply_style(state: InteriorDesignState):
    """4단계: 스타일 적용"""
    solutions = []
    style = state["style"]

    for issue in state["issues"]:
        if issue["type"] == "lighting":
            solutions.append(f"{style} 스타일 조명 추가")
        elif issue["type"] == "storage":
            solutions.append(f"{style} 스타일 수납장 추가")

    return {"solutions": solutions}

async def recommend_products(state: InteriorDesignState):
    """5단계: 제품 추천"""
    # RAG를 사용하여 제품 DB에서 검색
    products = []
    for solution in state["solutions"]:
        # Vector DB에서 관련 제품 검색
        query = f"{state['style']} {solution}"
        results = product_vectorstore.similarity_search(query, k=3)
        products.extend(results)

    return {"products": products}

async def generate_final_image(state: InteriorDesignState):
    """6단계: 최종 이미지 생성"""
    result = await gemini_service.generate_interior_image(
        state["image_path"],
        state["style"],
        f"Solutions: {', '.join(state['solutions'])}"
    )

    return {
        "generated_image": result["filename"],
        "analysis_text": result["analysis"]
    }

async def calculate_budget(state: InteriorDesignState):
    """7단계: 예산 산출"""
    total = sum([p.get("price", 0) for p in state["products"]])
    return {"budget": total}

# 그래프 구성
workflow = StateGraph(InteriorDesignState)

# 노드 추가
workflow.add_node("analyze", analyze_space)
workflow.add_node("diagnose", diagnose_issues)
workflow.add_node("apply_style", apply_style)
workflow.add_node("recommend_products", recommend_products)
workflow.add_node("generate_image", generate_final_image)
workflow.add_node("calculate_budget", calculate_budget)

# 엣지 정의
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "diagnose")
workflow.add_edge("diagnose", "apply_style")
workflow.add_edge("apply_style", "recommend_products")
workflow.add_edge("recommend_products", "generate_image")
workflow.add_edge("generate_image", "calculate_budget")
workflow.add_edge("calculate_budget", END)

# 컴파일
app = workflow.compile()

# 실행
async def run_design_workflow(image_path: str, style: str):
    result = await app.ainvoke({
        "image_path": image_path,
        "style": style,
        "room_analysis": {},
        "issues": [],
        "solutions": [],
        "products": [],
        "budget": 0.0,
        "generated_image": "",
        "analysis_text": ""
    })
    return result
```

### 3.4 기대 효과
1. **체계적인 프로세스**: 단계별로 명확한 의사결정
2. **재사용성**: 노드 단위로 재사용 가능
3. **디버깅 용이**: 각 단계별 상태 추적 가능
4. **확장성**: 새로운 노드 추가가 용이

---

## 4. LangChain을 통한 체계적 개발

### 4.1 LangChain 개념
LangChain은 LLM 기반 애플리케이션 개발을 위한 종합 프레임워크로, 프롬프트 관리, 체인 구성, 메모리 관리 등을 제공합니다.

### 4.2 적용 시나리오

#### 4.2.1 프롬프트 템플릿 관리
```python
from langchain.prompts import PromptTemplate, ChatPromptTemplate

# 현재 방식: 하드코딩된 프롬프트
# 개선 방식: 템플릿화

analysis_template = ChatPromptTemplate.from_messages([
    ("system", """You are a professional interior designer with expertise in {style} style.
    Analyze the room image and provide detailed insights."""),
    ("user", [
        {"type": "text", "text": "Analyze this room focusing on:\n{focus_areas}"},
        {"type": "image_url", "image_url": "{image_url}"}
    ])
])

# 사용
prompt = analysis_template.format_messages(
    style="minimalist",
    focus_areas="lighting, storage, flow",
    image_url=image_path
)
```

#### 4.2.2 체인 구성
```python
from langchain.chains import LLMChain, SequentialChain

# 분석 체인
analysis_chain = LLMChain(
    llm=gemini_model,
    prompt=analysis_template,
    output_key="analysis"
)

# 제안 체인
suggestion_template = PromptTemplate(
    input_variables=["analysis", "style"],
    template="Based on this analysis:\n{analysis}\n\nProvide {style} style suggestions:"
)

suggestion_chain = LLMChain(
    llm=gemini_model,
    prompt=suggestion_template,
    output_key="suggestions"
)

# 순차 실행
overall_chain = SequentialChain(
    chains=[analysis_chain, suggestion_chain],
    input_variables=["image_url", "style", "focus_areas"],
    output_variables=["analysis", "suggestions"]
)

result = overall_chain({"image_url": path, "style": "modern", "focus_areas": "all"})
```

#### 4.2.3 메모리 관리 (대화형 인터페이스)
```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

memory = ConversationBufferMemory()

conversation = ConversationChain(
    llm=gemini_model,
    memory=memory
)

# 사용자와 대화하며 인테리어 디자인
response1 = conversation.predict(input="이 방을 미니멀하게 바꾸고 싶어요.")
# AI: "좋습니다. 현재 어떤 부분이 가장 마음에 안 드시나요?"

response2 = conversation.predict(input="너무 어수선해요.")
# AI: "이전에 미니멀 스타일을 원하신다고 하셨죠. 불필요한 가구를 제거하고..."
```

### 4.3 구현 방안

#### 4.3.1 LangChain 설치
```bash
pip install langchain langchain-google-genai
```

#### 4.3.2 Gemini 통합
```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-image",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7
)
```

#### 4.3.3 출력 파서
```python
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class RoomAnalysisOutput(BaseModel):
    room_type: str = Field(description="방 타입 (원룸, 투룸 등)")
    size_estimate: str = Field(description="평수 추정")
    strengths: list[str] = Field(description="장점 목록")
    issues: list[str] = Field(description="문제점 목록")

parser = PydanticOutputParser(pydantic_object=RoomAnalysisOutput)

prompt = PromptTemplate(
    template="Analyze this room.\n{format_instructions}\n",
    input_variables=[],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

chain = prompt | llm | parser
result = chain.invoke({})  # result는 RoomAnalysisOutput 객체
```

### 4.4 기대 효과
1. **코드 재사용성**: 프롬프트 템플릿화로 유지보수 용이
2. **체계적 구조**: 체인 구성으로 복잡한 로직 단순화
3. **타입 안정성**: Pydantic 기반 출력 파싱
4. **대화형 기능**: 메모리 관리로 사용자와 상호작용 가능

---

## 5. 웹 크롤링을 통한 데이터 수집

### 5.1 크롤링 목적
- 최신 인테리어 트렌드 수집
- 제품 정보 및 가격 정보 수집
- 실제 시공 사례 이미지 수집
- 사용자 리뷰 및 평점 수집

### 5.2 크롤링 대상

#### 5.2.1 인테리어 정보 사이트
```
- 오늘의집 (ohouse.co.kr)
  - 사용자 업로드 인테리어 사진
  - 제품 정보 및 가격
  - 스타일별 카테고리

- 집들이 (zipdelli.com)
  - 실제 집들이 사진
  - 평수별, 스타일별 분류

- 핀터레스트 (pinterest.com)
  - 인테리어 아이디어
  - 스타일별 레퍼런스
```

#### 5.2.2 가구/소품 쇼핑몰
```
- 이케아 (ikea.com/kr)
- 한샘 (hanssem.com)
- 까사미아 (casamia.co.kr)
```

### 5.3 구현 방안

#### 5.3.1 크롤링 도구 선택
```python
# 옵션 1: BeautifulSoup (정적 페이지)
from bs4 import BeautifulSoup
import requests

response = requests.get("https://example.com/interior")
soup = BeautifulSoup(response.content, 'html.parser')

# 옵션 2: Selenium (동적 페이지)
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://example.com/interior")
elements = driver.find_elements(By.CLASS_NAME, "product-item")

# 옵션 3: Playwright (현대적, 빠름)
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.goto("https://example.com/interior")
    products = await page.query_selector_all(".product-item")
```

#### 5.3.2 제품 정보 크롤링 예시
```python
import asyncio
from playwright.async_api import async_playwright
import json

async def crawl_furniture_products(style: str):
    """가구 제품 정보 크롤링"""
    products = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 예: 오늘의집 스타일별 검색
        search_url = f"https://ohouse.co.kr/store?search={style}"
        await page.goto(search_url)

        # 제품 목록 추출
        product_cards = await page.query_selector_all(".product-card")

        for card in product_cards:
            try:
                name = await card.query_selector(".product-name")
                price = await card.query_selector(".product-price")
                image = await card.query_selector("img")
                link = await card.query_selector("a")

                product = {
                    "name": await name.inner_text() if name else "",
                    "price": await price.inner_text() if price else "",
                    "image_url": await image.get_attribute("src") if image else "",
                    "product_url": await link.get_attribute("href") if link else "",
                    "style": style
                }
                products.append(product)
            except Exception as e:
                print(f"Error extracting product: {e}")
                continue

        await browser.close()

    return products

# 사용
minimalist_products = await crawl_furniture_products("미니멀리스트")
```

#### 5.3.3 인테리어 사례 이미지 크롤링
```python
async def crawl_interior_images(style: str, count: int = 100):
    """인테리어 사례 이미지 크롤링"""
    images = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Pinterest 검색
        await page.goto(f"https://www.pinterest.com/search/pins/?q={style} interior")

        # 스크롤하며 이미지 로드
        for _ in range(count // 20):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await page.wait_for_timeout(1000)

        # 이미지 URL 추출
        img_elements = await page.query_selector_all("img[src*='pinimg']")

        for img in img_elements[:count]:
            src = await img.get_attribute("src")
            alt = await img.get_attribute("alt")
            images.append({"url": src, "description": alt, "style": style})

        await browser.close()

    return images
```

#### 5.3.4 데이터 저장 및 인덱싱
```python
# 1. 크롤링한 제품 정보를 Vector DB에 저장
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

async def index_products(products: list):
    """제품 정보 벡터화 및 저장"""
    embeddings = OpenAIEmbeddings()

    # 제품 설명 텍스트 생성
    texts = [
        f"{p['name']} - {p['style']} 스타일 - {p['price']}"
        for p in products
    ]

    # 메타데이터
    metadatas = [
        {
            "name": p["name"],
            "price": p["price"],
            "image_url": p["image_url"],
            "product_url": p["product_url"],
            "style": p["style"]
        }
        for p in products
    ]

    # Vector DB에 저장
    vectorstore = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory="./product_db"
    )

    return vectorstore

# 2. 제품 검색
async def search_products(query: str, style: str, k: int = 5):
    """스타일에 맞는 제품 검색"""
    vectorstore = Chroma(
        persist_directory="./product_db",
        embedding_function=OpenAIEmbeddings()
    )

    results = vectorstore.similarity_search(
        query=f"{style} {query}",
        k=k,
        filter={"style": style}
    )

    return results
```

### 5.4 크롤링 스케줄링
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# 매일 새벽 2시에 제품 정보 업데이트
@scheduler.scheduled_job('cron', hour=2)
async def daily_product_update():
    styles = ["미니멀리스트", "스칸디나비안", "모던", "빈티지", "인더스트리얼"]

    for style in styles:
        products = await crawl_furniture_products(style)
        await index_products(products)
        print(f"{style} 스타일 제품 {len(products)}개 업데이트 완료")

scheduler.start()
```

### 5.5 법적 고려사항
```
주의사항:
1. robots.txt 확인 및 준수
2. 과도한 요청 방지 (Rate Limiting)
3. 저작권 침해 주의 (이미지 사용 시 출처 표기)
4. 개인정보 수집 금지
5. 이용약관 위반 확인

권장사항:
- 공개 API 우선 사용
- 크롤링 간격 설정 (예: 3초)
- User-Agent 명시
- 상업적 이용 시 사이트 측과 협의
```

### 5.6 기대 효과
1. **최신 트렌드 반영**: 주기적 크롤링으로 최신 인테리어 트렌드 파악
2. **제품 추천 고도화**: 실제 판매 제품 기반 추천
3. **가격 정보 제공**: 예산 산출 정확도 향상
4. **사례 학습**: 크롤링한 이미지로 AI 모델 파인튜닝 가능

---

## 6. 추가 고도화 방안

### 6.1 사용자 선호도 학습

#### 6.1.1 행동 데이터 수집
```python
class UserInteraction(BaseModel):
    user_id: str
    image_id: str
    style_selected: str
    liked: bool
    saved: bool
    timestamp: datetime

# 사용자 피드백 저장
async def track_user_feedback(interaction: UserInteraction):
    # DB에 저장
    await db.interactions.insert_one(interaction.dict())
```

#### 6.1.2 추천 시스템
```python
from sklearn.metrics.pairwise import cosine_similarity

async def recommend_style(user_id: str):
    """사용자 이력 기반 스타일 추천"""
    # 사용자 과거 선택 조회
    interactions = await db.interactions.find({"user_id": user_id}).to_list(100)

    # 스타일별 선호도 계산
    style_scores = {}
    for interaction in interactions:
        style = interaction["style_selected"]
        weight = 2 if interaction["liked"] else 1
        style_scores[style] = style_scores.get(style, 0) + weight

    # 가장 선호하는 스타일 반환
    recommended_style = max(style_scores, key=style_scores.get)
    return recommended_style
```

### 6.2 AR/VR 통합

#### 6.2.1 3D 모델 생성
```
현재: 2D 이미지 생성
고도화: 3D 인테리어 모델 생성

기술 스택:
- Blender Python API (3D 모델링)
- Three.js (웹 3D 렌더링)
- AR.js (증강 현실)
```

#### 6.2.2 가상 배치
```python
# 사용자가 스마트폰으로 방을 스캔
# → AI가 3D 공간 인식
# → 추천 가구를 AR로 배치
# → 실시간으로 시각화
```

### 6.3 가격 최적화 및 예산 플래너

#### 6.3.1 예산별 옵션 제공
```python
async def generate_budget_options(
    room_analysis: dict,
    style: str,
    budget_range: tuple
):
    """예산별 인테리어 옵션 생성"""
    low, high = budget_range

    options = {
        "economy": await plan_interior(style, max_budget=low),
        "standard": await plan_interior(style, max_budget=(low + high) / 2),
        "premium": await plan_interior(style, max_budget=high)
    }

    return options
```

#### 6.3.2 가성비 분석
```python
async def analyze_value_for_money(products: list):
    """제품 가성비 분석"""
    for product in products:
        # 유사 제품 검색
        similar = await search_similar_products(product["name"])

        # 가격 비교
        prices = [p["price"] for p in similar]
        avg_price = sum(prices) / len(prices)

        # 가성비 점수
        product["value_score"] = avg_price / product["price"]

    return sorted(products, key=lambda x: x["value_score"], reverse=True)
```

### 6.4 멀티모달 입력

#### 6.4.1 텍스트 + 이미지
```python
async def design_with_description(
    image_path: str,
    user_description: str,
    style: str
):
    """사용자 설명 + 이미지 기반 디자인"""
    prompt = f"""
    User description: {user_description}

    Analyze the image and apply {style} style while considering user's preferences.
    """

    result = await gemini.generate_content([prompt, image])
    return result
```

#### 6.4.2 음성 입력
```python
from google.cloud import speech

async def voice_to_design_request(audio_file: str):
    """음성 → 텍스트 → 디자인 요청"""
    # 1. 음성 인식
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(uri=audio_file)
    config = speech.RecognitionConfig(language_code="ko-KR")

    response = client.recognize(config=config, audio=audio)
    text = response.results[0].alternatives[0].transcript

    # 2. 의도 파악
    intent = await extract_design_intent(text)

    # 3. 디자인 생성
    return await generate_design(intent)
```

### 6.5 협업 기능

#### 6.5.1 공유 및 피드백
```python
class DesignProject(BaseModel):
    id: str
    owner_id: str
    collaborators: list[str]
    images: list[str]
    comments: list[dict]

async def share_design(project_id: str, user_ids: list[str]):
    """디자인 프로젝트 공유"""
    project = await db.projects.find_one({"id": project_id})
    project["collaborators"].extend(user_ids)
    await db.projects.update_one({"id": project_id}, {"$set": project})

    # 알림 발송
    for user_id in user_ids:
        await send_notification(user_id, f"New design shared: {project_id}")
```

### 6.6 A/B 테스트 및 분석

#### 6.6.1 프롬프트 A/B 테스트
```python
class PromptVariant(BaseModel):
    id: str
    prompt_template: str
    conversion_rate: float
    avg_rating: float

async def ab_test_prompts(image_path: str, style: str):
    """여러 프롬프트 변형 테스트"""
    variants = await db.prompt_variants.find({"style": style}).to_list(10)

    # 무작위 선택
    selected = random.choice(variants)

    # 결과 생성
    result = await generate_with_prompt(image_path, selected["prompt_template"])

    # 사용 기록
    await db.prompt_usage.insert_one({
        "variant_id": selected["id"],
        "timestamp": datetime.now()
    })

    return result
```

---

## 7. 기술 스택 통합 로드맵

### 7.1 Phase 1: 기반 강화 (1-2개월)
```
목표: RAG 및 LangChain 도입

작업:
1. 인테리어 지식 베이스 구축 (Markdown 문서 수집)
2. ChromaDB 설정 및 임베딩
3. LangChain 기반 프롬프트 템플릿화
4. RAG 기반 분석 API 개발

기대 효과:
- 전문성 30% 향상
- 프롬프트 관리 효율화
```

### 7.2 Phase 2: 워크플로우 고도화 (2-3개월)
```
목표: LangGraph 기반 복잡한 워크플로우 구현

작업:
1. 다단계 디자인 프로세스 그래프 설계
2. 조건부 분기 로직 구현
3. 제품 추천 노드 추가
4. 예산 산출 노드 추가

기대 효과:
- 사용자 경험 개선
- 전환율 20% 향상
```

### 7.3 Phase 3: 데이터 수집 자동화 (3-4개월)
```
목표: 웹 크롤링 및 데이터 파이프라인 구축

작업:
1. Playwright 기반 크롤러 개발
2. 제품 DB 구축 (Vector DB)
3. 스케줄러 설정 (일일 업데이트)
4. 가격 비교 및 추천 시스템

기대 효과:
- 최신 트렌드 반영
- 제품 추천 정확도 50% 향상
```

### 7.4 Phase 4: 개인화 및 고급 기능 (4-6개월)
```
목표: 사용자 맞춤형 경험 제공

작업:
1. 사용자 행동 데이터 수집 및 분석
2. 추천 시스템 구축
3. AR 기능 POC (Proof of Concept)
4. 음성 인터페이스 추가

기대 효과:
- 사용자 만족도 40% 향상
- 재방문율 60% 향상
```

---

## 8. 비용 및 리소스 분석

### 8.1 초기 투자 비용

#### 8.1.1 인프라
```
1. Vector Database (Pinecone)
   - Free Tier: 무료 (1M vectors, 1 index)
   - Starter: $70/월 (5M vectors, 5 indexes)

2. Cloud Storage (이미지 저장)
   - AWS S3: ~$20/월 (100GB, 10,000 requests)
   - Google Cloud Storage: ~$20/월

3. Compute (서버)
   - AWS EC2 t3.medium: ~$30/월
   - 또는 GCP e2-medium: ~$25/월

총 예상 비용: $70-120/월
```

#### 8.1.2 API 비용
```
1. Google Gemini API
   - Gemini 2.5 Flash: $0.15/1M input tokens
   - 이미지 생성: 별도 과금

2. OpenAI API (임베딩)
   - text-embedding-3-large: $0.13/1M tokens

월 예상 API 비용: $100-300 (사용량에 따라)
```

#### 8.1.3 개발 인력
```
1. Backend 개발자: 1명 (3-6개월)
2. AI/ML 엔지니어: 1명 (2-4개월)
3. 인테리어 전문가 (자문): 필요시

총 인건비: 프로젝트 규모에 따라 책정
```

### 8.2 ROI 분석

#### 8.2.1 수익 모델
```
1. 프리미엄 구독
   - 무제한 이미지 생성
   - 고급 분석
   - $9.99/월

2. 제품 판매 수수료
   - 추천 제품 구매 시 5-10% 수수료

3. B2B 라이선스
   - 가구 업체, 건설사 등
   - 맞춤 계약

4. 광고
   - 제품 프로모션
```

#### 8.2.2 손익분기점
```
가정:
- 월 구독자 1,000명 x $9.99 = $9,990
- 제품 판매 수수료: $5,000
- 총 수익: $15,000/월

비용:
- 인프라: $120
- API: $300
- 마케팅: $3,000
- 인건비: $10,000
- 총 비용: $13,420/월

손익분기점: 약 900명 구독자
```

---

## 9. 리스크 및 대응 방안

### 9.1 기술적 리스크

#### 9.1.1 AI 모델 한계
```
리스크: Gemini가 부적절한 이미지 생성
대응:
- Content Safety Filter 적용
- 사용자 신고 기능
- 수동 검토 프로세스
```

#### 9.1.2 성능 저하
```
리스크: 동시 사용자 증가 시 응답 지연
대응:
- 비동기 처리 강화
- 캐싱 전략 (Redis)
- Queue 시스템 (Celery)
- CDN 사용
```

#### 9.1.3 크롤링 차단
```
리스크: 대상 사이트의 크롤링 차단
대응:
- 공식 API 우선 사용
- Rate Limiting 준수
- Proxy/VPN 활용
- 대체 데이터 소스 확보
```

### 9.2 비즈니스 리스크

#### 9.2.1 사용자 이탈
```
리스크: 기대와 다른 결과로 이탈
대응:
- Onboarding 튜토리얼
- 사용 예시 제공
- 피드백 루프 강화
```

#### 9.2.2 경쟁
```
리스크: 유사 서비스 출현
대응:
- 지속적인 기능 고도화
- 사용자 커뮤니티 구축
- 독점적 데이터 확보
```

---

## 10. 결론

### 10.1 고도화 우선순위

#### 높은 우선순위 (즉시 시작)
1. RAG 도입: 전문성 향상, 비용 대비 효과 높음
2. LangChain 적용: 코드 품질 개선, 유지보수성 향상
3. 기본 크롤링: 제품 추천 고도화

#### 중간 우선순위 (3-6개월)
1. LangGraph 워크플로우: 복잡한 프로세스 체계화
2. 사용자 선호도 학습: 개인화 경험
3. 예산 플래너: 실용성 강화

#### 낮은 우선순위 (6개월 이후)
1. AR/VR 기능: 기술적 난이도 높음
2. 음성 인터페이스: Nice-to-have
3. 협업 기능: 사용자 베이스 확보 후

### 10.2 핵심 권장사항

1. **RAG부터 시작**: 가장 빠르게 전문성을 높일 수 있는 방법
2. **점진적 도입**: 한 번에 모든 기술 도입 금지, 단계별 검증
3. **사용자 피드백 중시**: 기술보다 사용자 경험 우선
4. **데이터 자산화**: 크롤링 및 사용자 데이터 축적이 핵심 경쟁력
5. **비용 관리**: API 사용량 모니터링 및 최적화 지속

### 10.3 기대 성과

고도화 완료 시 예상 개선:
- 분석 정확도: 40% 향상
- 사용자 만족도: 50% 향상
- 전환율: 30% 향상
- 운영 효율성: 60% 향상

### 10.4 다음 단계

1. Phase 1 실행 계획 수립 (RAG + LangChain)
2. 인테리어 지식 베이스 초안 작성
3. POC (Proof of Concept) 개발 및 테스트
4. 사용자 베타 테스트 및 피드백 수집
5. 본격 배포 및 모니터링
