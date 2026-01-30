# src/core/interaction.py (완전 수정)

from datetime import datetime
from typing import List, Callable

class InteractionManager:
    def __init__(self, agent_name: str, llm, get_memories: Callable):
        self.agent_name = agent_name
        self.llm = llm
        self.get_memories = get_memories
    
    def should_start_conversation(self, partner_name: str, current_plan: str, 
                                  now: datetime) -> bool:
        """대화 시작 여부"""
        relevant_memories = self.get_memories(f"{partner_name}", 10)
        memory_context = "\n".join([f"- {m}" for m in relevant_memories])
        
        prompt = f"""당신은 {self.agent_name}입니다.

**현재 근처에 있는 사람: {partner_name}**

계획: {current_plan}

기억:
{memory_context}

**질문: 지금 {partner_name}와(과) 대화를 시작해야 할까요?**

고려사항:
1. 중요한 이야기가 있는가?
2. 수상한 점을 발견했는가?
3. 도움이 필요한가?
4. [긴급] 표시가 있으면 무조건 YES

형식:
DECISION: YES 또는 NO
REASON: 한 문장"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            if "YES" in content.upper():
                for line in content.split('\n'):
                    if 'REASON' in line:
                        print(f"   💬 대화 결정: {line.split('REASON:')[-1].strip()}")
                return True
            
            return False
            
        except:
            return False
    
    def generate_utterance(self, partner_name: str, conversation_history: List[str],
                          now: datetime) -> str:
        """발언 생성 (자연스럽게)"""
        relevant_memories = self.get_memories(partner_name, 5)
        memory_context = "\n".join([f"- {m}" for m in relevant_memories])
        
        history_text = "\n".join(conversation_history[-6:]) if conversation_history else "(대화 시작)"
        
        # [수정] 대화를 더 길게 유지하도록
        turn_count = len(conversation_history)
        continuation_hint = ""
        
        if turn_count < 4:
            continuation_hint = "\n\n**중요: 대화를 계속 이어가세요. 아직 할 말이 많습니다.**"
        elif turn_count < 8:
            continuation_hint = "\n\n**자연스럽게 대화를 이어가되, 적절한 시점이면 [END]로 종료할 수 있습니다.**"
        
        prompt = f"""당신은 {self.agent_name}입니다.

대화 상대: {partner_name}
대화 턴: {turn_count + 1}번째

대화 내용:
{history_text}

기억:
{memory_context}
{continuation_hint}

다음 말을 하세요. 1-3문장. 자연스럽고 인간답게.

**대화 종료 규칙:**
- 4턴 이하: 절대 [END] 금지
- 5-8턴: 자연스러운 마무리면 [END] 가능
- 9턴 이상: [END] 권장

예시:
(3턴째) 그건 정말 이상하네요. 혹시 다른 사람도 봤나요?
(6턴째) 알겠습니다. 조심하겠습니다. [END]"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            return content.strip()
        except:
            return "..."