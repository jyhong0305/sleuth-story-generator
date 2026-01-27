import openai
import os
from dotenv import load_dotenv

# .env 파일에서 API KEY 로드
load_dotenv() 

# API 키가 없으면 에러가 날 수 있으니 체크
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    # 혹시 .env 설정이 안 되어 있다면 여기에 직접 키를 넣어 테스트해보세요 (보안상 비추천하지만 테스트용으로)
    # api_key = "sk-..." 
    print("⚠️ 경고: OPENAI_API_KEY가 설정되지 않았습니다.")

client = openai.OpenAI(api_key=api_key)

def safe_generate_response(prompt, model="gpt-4o-mini", temperature=0.7):
    """OpenAI API 호출 래퍼 함수"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "You are a helpful roleplay assistant."},
                      {"role": "user", "content": prompt}],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ LLM 호출 에러: {e}")
        return "Error"