# src/core/paper_memory.py

from datetime import datetime, timedelta
from typing import List, Optional, Dict
import numpy as np
from dataclasses import dataclass
import uuid

@dataclass
class ConceptNode:
    """[논문] 기억의 기본 단위"""
    node_id: str
    node_type: str
    description: str
    created: datetime
    last_accessed: datetime
    importance: int
    embedding: np.ndarray
    access_count: int = 0
    
    @classmethod
    def create(cls, node_type: str, description: str, created: datetime,
               importance: int, embedding: np.ndarray):
        return cls(
            node_id=str(uuid.uuid4()),
            node_type=node_type,
            description=description,
            created=created,
            last_accessed=created,
            importance=importance,
            embedding=embedding,
            access_count=0
        )

class PaperMemorySystem:
    """[논문 완전 구현] Memory Stream + Retrieval + Reflection"""
    
    def __init__(self, agent_name: str, llm, embeddings_model):
        self.agent_name = agent_name
        self.llm = llm
        self.embeddings = embeddings_model
        
        self.memory_stream: List[ConceptNode] = []
        
        # [논문] 검색 공식 가중치
        self.alpha_recency = 1.0
        self.beta_importance = 1.0
        self.gamma_relevance = 1.0
        self.decay_rate = 0.99
        
        # [논문] Reflection 설정
        self.importance_accumulator = 0
        self.reflection_threshold = 50  # 낮춤
        self.last_reflection_time = None
        self.reflection_cooldown_minutes = 15
    
    def add_memory(self, description: str, now: datetime, 
                   node_type: str = "observation") -> ConceptNode:
        """[수정] 파라미터 이름 'now'로 통일"""
        
        # 중요도 평가
        importance = self._evaluate_importance(description)
        
        # 임베딩
        embedding = self._get_embedding(description)
        
        # 노드 생성
        node = ConceptNode.create(
            node_type=node_type,
            description=description,
            created=now,
            importance=importance,
            embedding=embedding
        )
        
        self.memory_stream.append(node)
        
        # Reflection 트리거
        self.importance_accumulator += importance
        
        if self._should_reflect(now):
            self._trigger_reflection(now)
        
        return node
    
    def _evaluate_importance(self, description: str) -> int:
        """[논문] LLM 중요도 평가"""
        prompt = f"""On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following piece of memory.

Memory: {description}

Rating: <fill in>"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            import re
            match = re.search(r'\d+', content)
            if match:
                score = int(match.group())
                return max(1, min(10, score))
            return 5
        except:
            return 5
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """임베딩 생성"""
        try:
            result = self.embeddings.embed_query(text)
            return np.array(result)
        except:
            return np.zeros(1536)
    
    def retrieve(self, query: str, now: datetime, top_k: int = 10) -> List[ConceptNode]:
        """[논문] 검색 공식"""
        
        if not self.memory_stream:
            return []
        
        query_embedding = self._get_embedding(query)
        
        scored_nodes = []
        for node in self.memory_stream:
            # Recency
            hours_ago = (now - node.last_accessed).total_seconds() / 3600
            recency = self.decay_rate ** hours_ago
            
            # Importance
            importance = node.importance / 10.0
            
            # Relevance
            relevance = self._cosine_similarity(query_embedding, node.embedding)
            
            # 최종 점수
            score = (
                self.alpha_recency * recency +
                self.beta_importance * importance +
                self.gamma_relevance * relevance
            )
            
            scored_nodes.append((score, node))
        
        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        top_nodes = [node for _, node in scored_nodes[:top_k]]
        
        # 접근 시각 업데이트
        for node in top_nodes:
            node.last_accessed = now
            node.access_count += 1
        
        return top_nodes
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도"""
        if vec1 is None or vec2 is None:
            return 0.0
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return np.dot(vec1, vec2) / (norm1 * norm2)
    
    def _should_reflect(self, now: datetime) -> bool:
        """Reflection 발동 여부 (쿨다운)"""
        
        if self.importance_accumulator < self.reflection_threshold:
            return False
        
        if self.last_reflection_time:
            minutes_passed = (now - self.last_reflection_time).total_seconds() / 60
            if minutes_passed < self.reflection_cooldown_minutes:
                return False
        
        return True
    
    def _trigger_reflection(self, now: datetime):
        """[논문] Reflection 2단계"""
        print(f"\n🧠 [{self.agent_name}] Reflection 트리거!")
        
        # 즉시 카운터 초기화
        self.importance_accumulator = 0
        self.last_reflection_time = now
        
        # 최근 기억
        recent = self.memory_stream[-100:]
        if len(recent) < 10:
            return
        
        # 1단계: 질문 생성
        questions = self._generate_reflection_questions(recent)
        
        # 2단계: 인사이트
        insights = []
        for question in questions[:2]:
            insight = self._generate_insight(question, now)
            if insight:
                insights.append(insight)
        
        # 저장 (importance=0)
        for insight in insights:
            node = ConceptNode.create(
                node_type="thought",
                description=f"[깨달음] {insight}",
                created=now,
                importance=0,
                embedding=self._get_embedding(insight)
            )
            self.memory_stream.append(node)
            print(f"   💡 {insight}")
    
    def _generate_reflection_questions(self, recent_memories: List[ConceptNode]) -> List[str]:
        """질문 생성"""
        memory_texts = "\n".join([
            f"{i+1}. {node.description}"
            for i, node in enumerate(recent_memories[:20])
        ])
        
        prompt = f"""Given only the information above, what are 2 most salient high-level questions we can answer about {self.agent_name}?

{memory_texts}

Questions:"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            questions = [
                line.strip().lstrip('123456789.-) ')
                for line in content.split('\n')
                if line.strip() and len(line.strip()) > 10
            ]
            return questions[:2]
        except Exception as e:
            print(f"   ⚠️ 질문 생성 실패: {e}")
            return []
    
    def _generate_insight(self, question: str, now: datetime) -> Optional[str]:
        """인사이트 생성"""
        relevant = self.retrieve(question, now, top_k=5)
        
        if not relevant:
            return None
        
        statements = "\n".join([
            f"{i+1}. {node.description}"
            for i, node in enumerate(relevant)
        ])
        
        prompt = f"""Based on these statements about {self.agent_name}:
{statements}

What is ONE high-level insight? (Keep it concise, one sentence)

Insight:"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            if lines:
                return lines[0].lstrip('123456789.-) ')[:200]
            return None
        except Exception as e:
            print(f"   ⚠️ 인사이트 생성 실패: {e}")
            return None
    
    def get_memory_descriptions(self, top_k: int = 10) -> List[str]:
        """최근 기억 텍스트"""
        recent = self.memory_stream[-top_k:]
        return [node.description for node in recent]