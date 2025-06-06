# 네비게이션 링크 정보
NAV_LINKS = [
    {"icon": "🏠", "label": "홈", "href": "/"},
    {"icon": "📊", "label": "트래픽 분석", "href": "/traffic"},
    {"icon": "👥", "label": "방문자 분석", "href": "/visitor-analysis"},
    {"icon": "🛣️", "label": "유입 경로 분석", "href": "/referrer"},
    {"icon": "🌍", "label": "지역 분석", "href": "/region"},
    {"icon": "⚙️", "label": "상태 코드 분석", "href": "/management"},
    {"icon": "ℹ️", "label": "LOVi 소개", "href": "/about"},
]

# 페이지 모듈 매핑
PAGE_MODULES = {
    "/": "home",
    "/traffic": "traffic",
    "/visitor-analysis": "visitor_analysis",
    "/referrer": "referrer",
    "/region": "region",
    "/management": "management",
    "/about": "about"
} 