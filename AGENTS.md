# AGENTS.md - Daily Price Up Workspace

이 워크스페이스는 서울 및 분당 지역의 부동산 실거래가 정보를 다운로드하고, 이를 바탕으로 유튜브 쇼츠 영상을 자동 생성 및 업로드하는 파이프라인 전용 공간입니다.

## 핵심 파이프라인 요소
- **데이터 소스**: 국토교통부 아파트 실거래가 API
- **데이터베이스**: `/data/apt_trades.db` (SQLite)
- **영상 처리**: PIL(Python Imaging Library) 및 FFmpeg 활용
- **퍼블리싱**: YouTube Data API V3

## 당신의 역할 (Responsibilities)
1. **유지보수**: `scripts/` 폴더 내의 크론 스크립트(`daily_price_check.py`, `upload_youtube.py` 등)가 매일 정상 작동하도록 관리.
2. **에러 추적**: 영상 렌더링 실패나 API 할당량(Quota) 초과 등의 문제를 추적하고 방어 로직 추가.
3. **기능 고도화**: 사용자(총괄 매니저 main)의 지시에 따라 자막 스타일, BGM, 데이터 필터링 기준 등을 수정하고 최적화.

## 작업 원칙
- 스크립트 수정 시 기존 데이터를 파괴하지 않도록 주의합니다 (`trash` > `rm`).
- 테스트 시에는 가급적 프로덕션 DB(`apt_trades.db`)를 건드리지 않거나 롤백 가능한 상태에서 진행합니다.
