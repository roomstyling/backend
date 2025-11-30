"""
API 테스트 및 평가 스크립트

사용법:
    python test_api.py --endpoint http://localhost:8000 --images test_images/

설명:
    - 지정된 디렉토리의 이미지들을 API에 전송
    - 각 이미지당 5개 스타일 결과 생성
    - 처리 시간, 성공률 등을 측정
    - 결과를 evaluation_report.md에 저장
"""

import requests
import os
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import statistics


class APITester:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint.rstrip('/')
        self.api_url = f"{self.endpoint}/api/get_styled_images"
        self.results = []

    def test_single_image(self, image_path: str) -> Dict[str, Any]:
        """단일 이미지 테스트"""
        print(f"\nTesting: {image_path}")

        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}

            start_time = time.time()
            try:
                response = requests.post(self.api_url, files=files, timeout=30)
                elapsed_time = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    return {
                        'image': os.path.basename(image_path),
                        'success': True,
                        'processing_time': elapsed_time,
                        'api_processing_time': data.get('processing_time', 0),
                        'results': data.get('results', []),
                        'error': None
                    }
                else:
                    return {
                        'image': os.path.basename(image_path),
                        'success': False,
                        'processing_time': elapsed_time,
                        'error': f"HTTP {response.status_code}: {response.text}"
                    }
            except Exception as e:
                elapsed_time = time.time() - start_time
                return {
                    'image': os.path.basename(image_path),
                    'success': False,
                    'processing_time': elapsed_time,
                    'error': str(e)
                }

    def test_directory(self, images_dir: str) -> List[Dict[str, Any]]:
        """디렉토리의 모든 이미지 테스트"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        image_files = [
            os.path.join(images_dir, f)
            for f in os.listdir(images_dir)
            if os.path.splitext(f)[1].lower() in image_extensions
        ]

        print(f"Found {len(image_files)} images in {images_dir}")

        results = []
        for image_path in image_files:
            result = self.test_single_image(image_path)
            results.append(result)
            time.sleep(1)  # 서버 부하 방지

        return results

    def generate_report(self, results: List[Dict[str, Any]], output_file: str = "evaluation_report.md"):
        """평가 보고서 생성"""
        # 통계 계산
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r['success'])
        failed_tests = total_tests - successful_tests

        processing_times = [r['processing_time'] for r in results if r['success']]
        api_times = [r['api_processing_time'] for r in results if r['success'] and 'api_processing_time' in r]

        # 스타일별 성공률
        style_stats = {}
        for result in results:
            if result['success'] and 'results' in result:
                for style_result in result['results']:
                    style_name = style_result['style_name']
                    if style_name not in style_stats:
                        style_stats[style_name] = {'success': 0, 'total': 0}

                    style_stats[style_name]['total'] += 1
                    if style_result.get('success', False):
                        style_stats[style_name]['success'] += 1

        # 보고서 작성
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# AI 인테리어 이미지 생성 API 평가 보고서\n\n")

            # 1. 전체 요약
            f.write("## 1. 전체 요약\n\n")
            f.write(f"- 테스트 날짜: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- API 엔드포인트: {self.api_url}\n")
            f.write(f"- 총 테스트 수: {total_tests}\n")
            f.write(f"- 성공: {successful_tests} ({successful_tests/total_tests*100:.1f}%)\n")
            f.write(f"- 실패: {failed_tests} ({failed_tests/total_tests*100:.1f}%)\n\n")

            # 2. 성능 지표
            f.write("## 2. 성능 지표\n\n")
            if processing_times:
                f.write("### 처리 시간 (총 요청-응답 시간)\n\n")
                f.write(f"- 평균: {statistics.mean(processing_times):.2f}초\n")
                f.write(f"- 최소: {min(processing_times):.2f}초\n")
                f.write(f"- 최대: {max(processing_times):.2f}초\n")
                f.write(f"- 중앙값: {statistics.median(processing_times):.2f}초\n\n")

            if api_times:
                f.write("### API 내부 처리 시간\n\n")
                f.write(f"- 평균: {statistics.mean(api_times):.2f}초\n")
                f.write(f"- 최소: {min(api_times):.2f}초\n")
                f.write(f"- 최대: {max(api_times):.2f}초\n")
                f.write(f"- 중앙값: {statistics.median(api_times):.2f}초\n\n")

                # 15초 제약 체크
                within_15s = sum(1 for t in api_times if t <= 15.0)
                f.write(f"- 15초 이내 처리: {within_15s}/{len(api_times)} ({within_15s/len(api_times)*100:.1f}%)\n\n")

            # 3. 스타일별 성공률
            f.write("## 3. 스타일별 성공률\n\n")
            f.write("| 스타일 | 성공 | 실패 | 성공률 |\n")
            f.write("|--------|------|------|--------|\n")
            for style_name, stats in sorted(style_stats.items()):
                success = stats['success']
                total = stats['total']
                success_rate = (success / total * 100) if total > 0 else 0
                failed = total - success
                f.write(f"| {style_name} | {success} | {failed} | {success_rate:.1f}% |\n")
            f.write("\n")

            # 4. 개별 테스트 결과
            f.write("## 4. 개별 테스트 결과\n\n")
            for idx, result in enumerate(results, 1):
                f.write(f"### 테스트 {idx}: {result['image']}\n\n")
                f.write(f"- 상태: {'성공' if result['success'] else '실패'}\n")
                f.write(f"- 처리 시간: {result['processing_time']:.2f}초\n")

                if result['success'] and 'results' in result:
                    f.write(f"- API 처리 시간: {result.get('api_processing_time', 0):.2f}초\n")
                    f.write(f"- 생성된 스타일 수: {len(result['results'])}\n\n")

                    f.write("#### 스타일별 결과:\n\n")
                    for style_result in result['results']:
                        status = "성공" if style_result.get('success', False) else "실패"
                        f.write(f"- **{style_result['style_name']}**: {status}\n")
                        if not style_result.get('success', False) and 'error' in style_result:
                            f.write(f"  - 오류: {style_result['error']}\n")
                        if style_result.get('generated_image'):
                            f.write(f"  - 이미지: {style_result['generated_image']}\n")
                    f.write("\n")
                else:
                    f.write(f"- 오류: {result.get('error', 'Unknown error')}\n\n")

            # 5. 평가 기준
            f.write("## 5. 평가 기준\n\n")
            f.write("### 5.1 성능 요구사항\n\n")
            f.write("- 15초 이내 5개 스타일 모두 생성: ")
            if api_times:
                meets_requirement = all(t <= 15.0 for t in api_times)
                f.write(f"{'충족' if meets_requirement else '미충족'}\n\n")
            else:
                f.write("측정 불가\n\n")

            f.write("### 5.2 안정성 요구사항\n\n")
            f.write(f"- 전체 성공률 95% 이상: {'충족' if (successful_tests/total_tests) >= 0.95 else '미충족'}\n")
            f.write(f"- 스타일별 성공률 90% 이상: ")
            all_styles_ok = all(
                (stats['success'] / stats['total']) >= 0.9
                for stats in style_stats.values()
                if stats['total'] > 0
            )
            f.write(f"{'충족' if all_styles_ok else '미충족'}\n\n")

            # 6. 결론
            f.write("## 6. 결론 및 권장사항\n\n")
            if api_times and statistics.mean(api_times) <= 15.0 and (successful_tests/total_tests) >= 0.95:
                f.write("전반적으로 성능 및 안정성 요구사항을 충족합니다.\n\n")
            else:
                f.write("일부 요구사항을 충족하지 못했습니다. 개선이 필요합니다.\n\n")

            if api_times and max(api_times) > 15.0:
                f.write("- 일부 요청이 15초를 초과했습니다. Gemini API 병렬 처리 최적화가 필요합니다.\n")

            if failed_tests > 0:
                f.write(f"- {failed_tests}개의 요청이 실패했습니다. 에러 핸들링 강화가 필요합니다.\n")

        print(f"\n평가 보고서가 {output_file}에 저장되었습니다.")


def main():
    parser = argparse.ArgumentParser(description='AI 인테리어 이미지 생성 API 테스트')
    parser.add_argument('--endpoint', default='http://localhost:8000', help='API 엔드포인트 URL')
    parser.add_argument('--images', default='test_images', help='테스트 이미지 디렉토리')
    parser.add_argument('--output', default='evaluation_report.md', help='평가 보고서 출력 파일')

    args = parser.parse_args()

    # 이미지 디렉토리 확인
    if not os.path.exists(args.images):
        print(f"오류: 이미지 디렉토리 '{args.images}'를 찾을 수 없습니다.")
        print(f"테스트 이미지를 {args.images} 디렉토리에 넣어주세요.")
        return

    # 테스트 실행
    tester = APITester(args.endpoint)
    results = tester.test_directory(args.images)

    # 보고서 생성
    tester.generate_report(results, args.output)

    # 결과 요약 출력
    successful = sum(1 for r in results if r['success'])
    print(f"\n총 {len(results)}개 이미지 테스트 완료")
    print(f"성공: {successful}, 실패: {len(results) - successful}")


if __name__ == "__main__":
    main()
