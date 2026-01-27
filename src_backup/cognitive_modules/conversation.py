# backend/conversation.py (새 파일)

from typing import List, Dict, Optional
from datetime import datetime
from backend.memory import MemoryStream

class Conversation:
    """두 에이전트 간의 대화 세션"""
    
    def __init__(self, agent1_name: str, agent2_name: str, start_time: datetime):
        self.agent1_name = agent1_name
        self.agent2_name = agent2_name
        self.start_time = start_time
        self.messages: List[Dict] = []  # {speaker, content, time}
        self.is_active = True
        
    def add_message(self, speaker: str, content: str, time: datetime):
        """발언 추가"""
        self.messages.append({
            "speaker": speaker,
            "content": content,
            "time": time
        })
    
    def get_history(self, last_n: int = None) -> str:
        """대화 기록 텍스트로 변환"""
        messages = self.messages[-last_n:] if last_n else self.messages
        return "\n".join([f"{m['speaker']}: {m['content']}" for m in messages])
    
    def get_partner(self, agent_name: str) -> str:
        """대화 상대 이름"""
        return self.agent2_name if agent_name == self.agent1_name else self.agent1_name

class ConversationSystem:
    """대화 생성 및 관리"""
    
    def __init__(self, memory_stream: MemoryStream):
        self.memory_stream = memory_stream
    
    def generate_utterance(self,
                          speaker_name: str,
                          listener_name: str,
                          conversation: Conversation,
                          speaker_memories: List,
                          listener_trait: str = "") -> str:
        """
        한 마디 생성
        
        Args:
            speaker_name: 말하는 사람
            listener_name: 듣는 사람
            conversation: 현재 대화 객체
            speaker_memories: 화자의 관련 기억들
            listener_trait: 청자의 특성 (선택)
        """
        # 대화 맥락
        history = conversation.get_history(last_n=6)  # 최근 6발언
        
        # 기억 맥락
        memory_context = "\n".join([
            f"- {m.content}" for m in speaker_memories[:5]
        ])
        
        prompt = f"""You are {speaker_name}, having a conversation with {listener_name}.

Your relevant memories:
{memory_context}

Conversation so far:
{history}

Generate your next response. Consider:
1. Your relationship and past interactions
2. Your current emotional state
3. The conversational flow
4. Keep it natural and concise (1-3 sentences)

Important:
- If you want to end the conversation naturally, include "[END]" at the end
- Stay in character
- Be realistic - not every conversation is long

Response:"""

        try:
            response = self.memory_stream.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=150
            )
            
            utterance = response.choices[0].message.content.strip()
            
            # [END] 제거해서 반환 (시스템에서는 감지용으로만 사용)
            if "[END]" in utterance:
                utterance = utterance.replace("[END]", "").strip()
                utterance += " [대화 종료 원함]"
            
            return utterance
            
        except Exception as e:
            print(f"⚠️ 발언 생성 실패: {e}")
            return "..."
    
    def should_initiate_conversation(self,
                                     agent_name: str,
                                     other_agent_name: str,
                                     agent_memories: List,
                                     current_plan: str) -> bool:
        """
        대화를 시작해야 하는지 판단
        
        Returns:
            True면 대화 시작해야 함
        """
        memory_context = "\n".join([
            f"- {m.content}" for m in agent_memories[:8]
        ])
        
        prompt = f"""You are {agent_name}. You see {other_agent_name} nearby.

Your recent memories:
{memory_context}

Your current plan: {current_plan}

Should you start a conversation with {other_agent_name}?

Consider:
1. Do you have something important to discuss?
2. Is this a good time?
3. Your relationship with them
4. Your current priorities

Answer with ONLY "YES" or "NO" and a brief reason (one sentence).

Format:
DECISION: YES/NO
REASON: [one sentence]"""

        try:
            response = self.memory_stream.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            text = response.choices[0].message.content.strip()
            
            # 파싱
            decision = "NO"
            reason = ""
            for line in text.split('\n'):
                if line.startswith('DECISION:'):
                    decision = line.replace('DECISION:', '').strip()
                elif line.startswith('REASON:'):
                    reason = line.replace('REASON:', '').strip()
            
            if "YES" in decision.upper():
                print(f"   💬 [{agent_name}] 대화 시작 결정: {reason}")
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ 대화 판단 실패: {e}")
            return False