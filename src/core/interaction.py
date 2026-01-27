# src/core/interaction.py

from datetime import datetime
from typing import List, Callable

class InteractionManager:
    def __init__(self, agent_name: str, llm, get_memories: Callable):
        self.agent_name = agent_name
        self.llm = llm
        self.get_memories = get_memories
    
    def should_start_conversation(self, partner_name: str, current_plan: str, 
                                  current_time: datetime) -> bool:
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
1. 계획에 이 사람과의 상호작용이 포함되어 있는가?
2. 중요한 이야기가 있는가?
3. 지금이 적절한 시기인가?

**반드시 다음 형식으로 대답:**
DECISION: YES 또는 NO
REASON: 한 문장

예시:
DECISION: YES
REASON: 계획에 김민준과 급여 이야기가 있고 지금이 적기다"""

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
                          current_time: datetime) -> str:
        """발언 생성"""
        relevant_memories = self.get_memories(partner_name, 5)
        memory_context = "\n".join([f"- {m}" for m in relevant_memories])
        
        history_text = "\n".join(conversation_history[-6:]) if conversation_history else "(시작)"
        
        prompt = f"""당신은 {self.agent_name}입니다.

대화 상대: {partner_name}

대화 내용:
{history_text}

기억:
{memory_context}

다음 말을 하세요. 1-3문장. 끝내려면 [END] 추가.

예시:
사장님, 급여 이야기 좀 할 수 있을까요?

또는:
알겠습니다. [END]"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            return content.strip()
        except:
            return "..."