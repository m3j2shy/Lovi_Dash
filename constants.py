# 네비게이션 링크 정보
NAV_LINKS = [
    {"icon": "🏠", "label": "홈", "href": "/"},
    {"icon": "📊", "label": "트래픽", "href": "/traffic"},
    {"icon": "👥", "label": "사용자 분석", "href": "/user-analysis"},
    {"icon": "🔍", "label": "인기 키워드", "href": "/popular-keywords"},
    {"icon": "🛣️", "label": "유입 출처", "href": "/referrer"},
    {"icon": "🌍", "label": "지역", "href": "/region"},
    {"icon": "⚙️", "label": "관리", "href": "/management"},
    {"icon": "ℹ️", "label": "기타 페이지", "href": "/about"},
]

# 페이지 모듈 매핑
PAGE_MODULES = {
    "/": "home",
    "/traffic": "traffic",
    "/user-analysis": "user_analysis",
    "/popular-keywords": "popular_keywords",
    "/referrer": "referrer",
    "/region": "region",
    "/management": "management",
    "/about": "about"
} 