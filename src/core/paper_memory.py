# src/core/paper_memory.py

from datetime import datetime
from typing import List, Optional, Dict
import numpy as np
from dataclasses import dataclass
import uuid

@dataclass
class ConceptNode:
    """
    [논문] 기억의 기본 단위
    
    속성:
    - node_id: 고유 식별자
    - node_type: observation | thought | chat
    - description: 자연어 설명
    - created: 생성 시각
    - last_accessed: 마지막 접근 시각
    - importance: 1-10 중요도 (LLM 평가)
    - embedding: 벡터 데이터
    - access_count: 접근 횟수
    """
    node_id: str
    node_type: str  # observation, thought, chat
    description: str
    created: datetime
    last_accessed: datetime
    importance: int  # 1-10
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
    """
    [논문 완전 구현] Memory Stream + Retrieval + Reflection
    """
    
    def __init__(self, agent_name: str, llm, embeddings_model):
        self.agent_name = agent_name
        self.llm = llm
        self.embeddings = embeddings_model
        
        self.memory_stream: List[ConceptNode] = []
        
        # [논문] 검색 공식 가중치
        self.alpha_recency = 1.0
        self.beta_importance = 1.0
        self.gamma_relevance = 1.0
        self.decay_rate = 0.99  # 시간당 감쇠율
        
        # [논문] Reflection 트리거
        self.importance_accumulator = 0
        self.reflection_threshold = 50
    
    def add_memory(self, description: str, current_time: datetime, 
                   node_type: str = "observation") -> ConceptNode:
        """
        [논문] 기억 추가
        1. 중요도 평가 (LLM)
        2. 임베딩 생성
        3. ConceptNode 생성 및 저장
        """
        # 1. 중요도 평가
        importance = self._evaluate_importance(description)
        
        # 2. 임베딩
        embedding = self._get_embedding(description)
        
        # 3. 노드 생성
        node = ConceptNode.create(
            node_type=node_type,
            description=description,
            created=current_time,
            importance=importance,
            embedding=embedding
        )
        
        self.memory_stream.append(node)
        
        # 4. Reflection 트리거 체크
        self.importance_accumulator += importance
        if self.importance_accumulator >= self.reflection_threshold:
            self._trigger_reflection(current_time)
        
        return node
    
    def _evaluate_importance(self, description: str) -> int:
        """
        [논문] LLM으로 중요도 평가 (1-10)
        
        프롬프트: "1점은 매우 평범, 10점은 매우 중요할 때,
                  다음 기억의 중요도를 평가하라"
        """
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
    
    def retrieve(self, query: str, current_time: datetime, top_k: int = 10) -> List[ConceptNode]:
        """
        [논문] 검색 공식
        S = α*Recency + β*Importance + γ*Relevance
        
        - Recency: 지수 감쇠 (decay_rate^hours_ago)
        - Importance: 0-1 정규화
        - Relevance: 코사인 유사도
        """
        if not self.memory_stream:
            return []
        
        query_embedding = self._get_embedding(query)
        
        scored_nodes = []
        for node in self.memory_stream:
            # 1. Recency
            hours_ago = (current_time - node.last_accessed).total_seconds() / 3600
            recency = self.decay_rate ** hours_ago
            
            # 2. Importance (0-1 정규화)
            importance = node.importance / 10.0
            
            # 3. Relevance (코사인 유사도)
            relevance = self._cosine_similarity(query_embedding, node.embedding)
            
            # 최종 점수
            score = (
                self.alpha_recency * recency +
                self.beta_importance * importance +
                self.gamma_relevance * relevance
            )
            
            scored_nodes.append((score, node))
        
        # 정렬 및 상위 k개
        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        top_nodes = [node for _, node in scored_nodes[:top_k]]
        
        # 접근 시각 업데이트
        for node in top_nodes:
            node.last_accessed = current_time
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
    
    def _trigger_reflection(self, current_time: datetime):
        """
        [논문] Reflection 2단계
        
        1단계: 핵심 질문 생성
        2단계: 인사이트 추출
        """
        print(f"\n🧠 [{self.agent_name}] Reflection 트리거!")
        # 카운터 초기화
        self.importance_accumulator = 0
        
        # 최근 100개 기억
        recent = self.memory_stream[-100:]
        if len(recent) < 10:
            return
        
        # 1단계: 핵심 질문 생성
        questions = self._generate_reflection_questions(recent)
        
        # 2단계: 각 질문에 대한 인사이트
        insights = []
        for question in questions:
            insight = self._generate_insight(question, current_time)
            if insight:
                insights.append(insight)
        
        # 인사이트를 기억으로 저장
        for insight in insights:
            self.add_memory(
                f"[깨달음] {insight}",
                current_time,
                node_type="thought"
            )
            print(f"   💡 {insight}")
    
    def _generate_reflection_questions(self, recent_memories: List[ConceptNode]) -> List[str]:
        """[논문 1단계] 핵심 질문 생성"""
        memory_texts = "\n".join([
            f"{i+1}. {node.description}"
            for i, node in enumerate(recent_memories[:30])
        ])
        
        prompt = f"""Given only the information above, what are 3 most salient high-level questions we can answer about the subjects in the statements?

{memory_texts}

Questions:"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            questions = [
                line.strip().lstrip('123456789.-) ')
                for line in content.split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]
            return questions[:3]
        except:
            return []
    
    def _generate_insight(self, question: str, current_time: datetime) -> Optional[str]:
        """[논문 2단계] 인사이트 추출"""
        # 질문 관련 기억 검색
        relevant = self.retrieve(question, current_time, top_k=10)
        
        statements = "\n".join([
            f"{i+1}. {node.description}"
            for i, node in enumerate(relevant)
        ])
        
        prompt = f"""Statements about {self.agent_name}:
{statements}

What high-level insight can you infer from the above statements? (5 insights)

Insights:"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 첫 번째 인사이트만 반환
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            if lines:
                return lines[0].lstrip('123456789.-) ')
            return None
        except:
            return None
    
    def get_memory_descriptions(self, top_k: int = 10) -> List[str]:
        """최근 기억 텍스트 반환"""
        recent = self.memory_stream[-top_k:]
        return [node.description for node in recent]