import os
import pandas as pd
import pandas_gbq
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# 환경변수 로드
load_dotenv()

def get_bigquery_config() -> Dict[str, Any]:
    """
    BigQuery 설정을 반환하는 함수
    
    Returns:
        Dict[str, Any]: BigQuery 설정 정보
    """
    return {
        'project_id': os.getenv('GCP_PROJECT_ID'),
        'dataset': os.getenv('BIGQUERY_DATASET'),
        'table': os.getenv('BIGQUERY_TABLE')
    }

def load_bigquery_data(query: str, limit: Optional[int] = None) -> Optional[pd.DataFrame]:
    """
    BigQuery에서 데이터를 로드하는 함수
    
    Args:
        query (str): 실행할 SQL 쿼리
        limit (Optional[int]): 결과 제한 수 (기본값: None)
        
    Returns:
        Optional[pd.DataFrame]: 로드된 데이터프레임 또는 에러 발생 시 None
    """
    try:
        config = get_bigquery_config()
        if limit:
            query = f"{query} LIMIT {limit}"
            
        return pandas_gbq.read_gbq(query, project_id=config['project_id'])
    except Exception as e:
        print(f"BigQuery 데이터 로드 중 에러 발생: {e}")
        return None

def get_sample_data(limit: int = 1000) -> Optional[pd.DataFrame]:
    """
    샘플 데이터를 로드하는 함수
    
    Args:
        limit (int): 샘플 데이터 수 (기본값: 1000)
        
    Returns:
        Optional[pd.DataFrame]: 샘플 데이터프레임 또는 에러 발생 시 None
    """
    try:
        config = get_bigquery_config()
        query = f"""
        SELECT * FROM `{config['project_id']}.{config['dataset']}.{config['table']}`
        LIMIT {limit}
        """
        return load_bigquery_data(query)
    except Exception as e:
        print(f"샘플 데이터 로드 중 에러 발생: {e}")
        return None

def create_404_page():
    """
    404 에러 페이지를 생성하는 함수
    
    Returns:
        html.Div: 404 에러 페이지 컴포넌트
    """
    from dash import html, dcc
    
    return html.Div(
        [
            html.H1("404 - 페이지를 찾을 수 없습니다", className="text-center mt-5"),
            html.P("요청하신 페이지가 존재하지 않습니다.", className="text-center"),
            html.Div(
                dcc.Link("홈으로 돌아가기", href="/", className="btn btn-primary"),
                className="text-center mt-3"
            )
        ],
        className="container"
    ) 