# backend/reflect.py (새 파일 생성)

from typing import List
from datetime import datetime
from backend.memory import MemoryStream, Memory

class ReflectionSystem:
    """논문의 Reflection 메커니즘 구현"""
    
    def __init__(self, memory_stream: MemoryStream):
        self.memory_stream = memory_stream
        self.reflection_threshold = 100  # importance 합계 임계값
        self.importance_accumulator = 0  # 누적 중요도
        
    def should_reflect(self) -> bool:
        """Reflection 트리거 조건 체크"""
        return self.importance_accumulator >= self.reflection_threshold
    
    def on_memory_added(self, importance: int):
        """새 기억 추가 시 호출 (누적 중요도 갱신)"""
        self.importance_accumulator += importance
    
    def generate_reflections(self, current_time: datetime, focus_query: str = None) -> List[str]:
        """
        [핵심] 최근 기억들을 분석해서 상위 개념(insights) 생성
        
        Args:
            current_time: 현재 시각
            focus_query: 특정 주제에 집중할 경우 (예: "사장님과의 관계")
        """
        # 1. 최근 100개 기억 가져오기
        recent_memories = self.memory_stream.memories[-100:]
        
        if not recent_memories:
            return []
        
        # 2. 만약 focus_query가 있다면, 관련된 기억만 필터링
        if focus_query:
            # Retrieval 사용해서 관련 기억만
            relevant_memories = self.memory_stream.retrieve(
                focus_query, 
                current_time, 
                top_k=30  # 최대 30개
            )
        else:
            # 전체 최근 기억 사용
            relevant_memories = sorted(
                recent_memories, 
                key=lambda m: m.importance, 
                reverse=True
            )[:30]  # 중요도 높은 30개
        
        # 3. 기억들을 텍스트로 정리
        memory_texts = [
            f"- {m.content} (중요도: {m.importance})"
            for m in relevant_memories
        ]
        
        # 4. LLM에게 "패턴 찾기" 요청
        insights = self._ask_llm_for_insights(memory_texts, focus_query)
        
        # 5. 생성된 insights를 다시 기억으로 저장!
        # [논문] Reflection 결과도 Memory Stream에 추가됨 (재귀적 구조)
        for insight in insights:
            self.memory_stream.add_memory(
                content=f"[깨달음] {insight}",
                timestamp=current_time,
                mem_type="reflection"
            )
        
        # 6. 카운터 초기화
        self.importance_accumulator = 0
        
        return insights
    
    def _ask_llm_for_insights(self, memory_texts: List[str], focus: str = None) -> List[str]:
        """LLM에게 패턴/통찰 추출 요청"""
        
        memories_str = "\n".join(memory_texts)
        
        # [논문 프롬프트 참고]
        prompt = f"""Given the following statements about {self.memory_stream.agent_name}, what high-level insights can you infer?

Recent memories:
{memories_str}

{"Focus on: " + focus if focus else ""}

Generate 3-5 high-level insights or patterns. Each insight should:
1. Synthesize multiple memories into a broader conclusion
2. Be more abstract than the individual memories
3. Help understand the agent's situation, relationships, or future behavior

Format: Return ONLY the insights, one per line, without numbering."""

        try:
            response = self.memory_stream.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # 창의성 필요
                max_tokens=300
            )
            
            # 응답을 줄 단위로 분리
            text = response.choices[0].message.content.strip()
            insights = [
                line.strip() 
                for line in text.split('\n') 
                if line.strip() and not line.strip().startswith('#')
            ]
            
            return insights[:5]  # 최대 5개
            
        except Exception as e:
            print(f"⚠️ Reflection 생성 실패: {e}")
            return []