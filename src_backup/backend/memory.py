import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드 (API 키 관리)
load_dotenv()

class Memory:
    """단일 기억 객체"""
    def __init__(self, content: str, timestamp: datetime, mem_type: str = "observation"):
        self.content = content
        self.timestamp = timestamp
        self.type = mem_type
        
        self.importance = 0.0   # 초기값 0.0 설정
        self.embedding = None   # 1536차원 벡터
        self.access_count = 0   
        self.last_access = timestamp
        self.reflection_system = None  # 나중에 초기화

    def add_memory(self, content: str, timestamp: datetime, mem_type: str = "observation"):
        memory = Memory(content, timestamp, mem_type)
        
        memory.importance = self._evaluate_importance(content)
        memory.embedding = self._get_embedding(content)
        
        self.memories.append(memory)
        print(f"💾 [{self.agent_name}] 기억 저장 (중요도: {memory.importance}): {content}")
        
        # [추가] Reflection 시스템에 알림
        if self.reflection_system:
            self.reflection_system.on_memory_added(memory.importance)
            
            # 임계값 도달 시 자동 Reflection
            if self.reflection_system.should_reflect():
                print(f"\n🧠 [{self.agent_name}] Reflection 트리거!")
                insights = self.reflection_system.generate_reflections(timestamp)
                if insights:
                    print("💡 깨달음:")
                    for insight in insights:
                        print(f"   - {insight}")
        
        return memory

    def to_dict(self):
        """JSON 저장을 위한 딕셔너리 변환"""
        return {
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "type": self.type,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_access": self.last_access.isoformat(),
            # [수정] 임베딩을 저장하지 않으면 불러올 때 다시 돈 내고 계산해야 함
            # 리스트로 변환하여 저장 (파일 용량은 커지지만 로딩 속도/비용 절약)
            "embedding": self.embedding.tolist() if self.embedding is not None else None
        }

    @classmethod
    def from_dict(cls, data):
        """저장된 데이터에서 객체 복원"""
        mem = cls(
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            mem_type=data["type"]
        )
        mem.importance = data["importance"]
        mem.access_count = data["access_count"]
        mem.last_access = datetime.fromisoformat(data["last_access"])
        if data.get("embedding"):
            mem.embedding = np.array(data["embedding"])
        return mem

class MemoryStream:
    """논문 정확 구현: Memory Stream + Retrieval w/ NumPy"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.memories: List[Memory] = []
        
        # [수정] API 키 확인 및 클라이언트 생성
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ 경고: OPENAI_API_KEY가 환경변수에 설정되지 않았습니다.")
        self.client = OpenAI(api_key=api_key)
        
        # 논문 파라미터
        self.alpha = 1.0  # Recency
        self.beta = 1.0   # Importance
        self.gamma = 1.0  # Relevance
        self.decay_rate = 0.995 # 시간당 감쇠율 (논문값 참조)
        
    # 이 부분을 찾아서 type도 받을 수 있게 수정
    def add_memory(self, content: str, timestamp: datetime, mem_type: str = "observation", type: str = None):
        """
        [호환성] type과 mem_type 모두 지원
        """
        # type 파라미터가 주어지면 그걸 사용
        if type is not None:
            mem_type = type
            
        memory = Memory(content, timestamp, mem_type)
        
        memory.importance = self._evaluate_importance(content)
        memory.embedding = self._get_embedding(content)
        
        self.memories.append(memory)
        print(f"💾 [{self.agent_name}] 기억 저장 (중요도: {memory.importance}): {content}")
        
        # Reflection 시스템 트리거
        if self.reflection_system:
            self.reflection_system.on_memory_added(memory.importance)
            
            if self.reflection_system.should_reflect():
                print(f"\n🧠 [{self.agent_name}] Reflection 트리거!")
                insights = self.reflection_system.generate_reflections(timestamp)
                if insights:
                    print("💡 깨달음:")
                    for insight in insights:
                        print(f"   - {insight}")
        
        return memory
    
    def _evaluate_importance(self, content: str) -> int:
        """LLM에게 중요도(1-10) 평가 요청"""
        prompt = f"""
        On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following piece of memory.
        
        Memory: {content}
        
        Rating: <fill in>
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[{"role": "user", "content": prompt}],
                temperature=0, # 일관된 평가를 위해 0 추천
                max_tokens=5
            )
            # 숫자가 아닌 문자가 섞여 있을 수 있으니 추출 로직 보강
            import re
            text = response.choices[0].message.content.strip()
            score = int(re.search(r'\d+', text).group())
            return min(max(score, 1), 10)
        except Exception as e:
            print(f"⚠️ 중요도 평가 실패: {e}")
            return 1 # 기본값
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Embedding API 호출"""
        try:
            text = text.replace("\n", " ")
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=[text]
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            print(f"⚠️ 임베딩 생성 실패: {e}")
            return np.zeros(1536) # 차원수 맞춰서 0벡터 반환
    
    def retrieve(self, query: str, current_time: datetime, top_k: int = 5) -> List[Memory]:
        """[핵심] 3가지 점수 합산 검색"""
        if not self.memories:
            return []
        
        # 쿼리 임베딩
        query_embedding = self._get_embedding(query)
        
        scored_memories = []
        for mem in self.memories:
            # 1. Recency (최신성): 지수 감쇠 적용
            hours_ago = (current_time - mem.last_access).total_seconds() / 3600
            recency = self.decay_rate ** hours_ago
            
            # 2. Importance (중요도): 0~1 정규화
            importance = mem.importance / 10.0
            
            # 3. Relevance (관련성): 코사인 유사도
            relevance = self._cosine_similarity(query_embedding, mem.embedding)
            
            # 총점 계산
            score = (self.alpha * recency) + (self.beta * importance) + (self.gamma * relevance)
            scored_memories.append((score, mem))
        
        # 점수순 정렬
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        # 상위 k개 추출 및 접근 시간 업데이트
        top_memories = []
        for _, mem in scored_memories[:top_k]:
            mem.last_access = current_time # [논문] 검색된 기억은 '최근 접근'으로 갱신됨
            mem.access_count += 1
            top_memories.append(mem)
            
        return top_memories
    
    def _cosine_similarity(self, vec1, vec2):
        if vec1 is None or vec2 is None: return 0
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0: return 0
        return np.dot(vec1, vec2) / (norm1 * norm2)

    # [수정] current_time 인자 추가 (현실 시간과 시뮬레이션 시간 분리)
    def get_recent_memories(self, current_time: datetime, hours: int = 24) -> str:
        """최근 N시간 동안의 기억들을 텍스트로 반환"""
        cutoff = current_time - timedelta(hours=hours)
        recent = [m.content for m in self.memories if m.timestamp > cutoff]
        return "\n".join(recent) if recent else "최근 기억 없음"
    
    def save_to_disk(self, filepath: str):
        data = {
            "agent_name": self.agent_name,
            "memories": [m.to_dict() for m in self.memories]
        }
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def load_from_disk(self, filepath: str):
        """저장된 기억 불러오기"""
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.agent_name = data["agent_name"]
        self.memories = [Memory.from_dict(m_data) for m_data in data["memories"]]
        print(f"📂 [{self.agent_name}] 기억 {len(self.memories)}개 로드 완료")