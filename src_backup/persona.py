# persona.py 수정사항

from cognitive_modules.conversation import ConversationSystem, Conversation
from typing import Optional

class Persona:
    def __init__(self, name, trait, maze):
        # ... 기존 코드 ...
        
        # [추가] 대화 시스템
        self.conversation_system = ConversationSystem(self.memory)
        self.current_conversation: Optional[Conversation] = None
        
    def _normal_act(self, current_time, force_thought):
        """기존 act 로직"""
        observation, people_here = self.perceive(current_time)
        self.memory.add_memory(observation, current_time)
        
        context_memories = self.memory.retrieve(query=observation, current_time=current_time)
        
        if force_thought:
            observation += f" (강한 충동: {force_thought})"
        
        # Planning 시스템으로 행동 결정
        plan_result = self.memory.planning_system.react_to_observation(
            observation, 
            current_time, 
            people_here
        )
        
        action_type = plan_result.get("action_type")
        target = plan_result.get("target")
        thought = plan_result.get("thought")
        
        print(f"\n🤖 [{self.name}] 생각: {thought}")
        print(f"   결정: {action_type} -> {target}")
        
        final_log = ""
        
        if action_type == "MOVE":
            # 이동 로직
            self.maze.set_agent_location(self.name, target)
            self.scratch.curr_address = target
            final_log = f"{target}으로 이동함."
            
        elif action_type == "CHAT":
            # [개선] 대화 시작 로직
            # target은 대화 상대 이름
            if target in people_here:
                # 대화 시작 여부를 좀 더 신중하게 판단
                current_plan = self.memory.planning_system.get_current_action(current_time)
                should_talk = self.conversation_system.should_initiate_conversation(
                    self.name,
                    target,
                    context_memories,
                    current_plan
                )
                
                if should_talk:
                    final_log = f"CHAT_REQUEST:{target}"
                else:
                    print(f"   💭 [{self.name}] 대화를 보류함")
                    final_log = "대기함"
            else:
                print(f"   ⚠️ [{self.name}] {target}이(가) 근처에 없음")
                final_log = f"{target}을(를) 찾아서 이동 중"
                
        elif action_type == "ACTION":
            final_log = f"행동 수행: {target}"
            
        elif action_type == "WAIT":
            self.scratch.curr_action = target
            final_log = f"{target} 행동을 하며 대기함."
        
        self.memory.add_memory(final_log, current_time, type="action")
        
        return final_log
    
    def _continue_chat(self, current_time):
        """대화 진행"""
        if not self.chat_partner:
            self.state = "IDLE"
            return "오류: 대화 상대 없음"
        
        # 상대방 위치 확인
        my_loc = self.maze.get_agent_location(self.name)
        partner_loc = self.maze.get_agent_location(self.chat_partner.name)
        
        if my_loc != partner_loc:
            print(f"   🏃 [{self.name}] 상대방이 사라져서 대화 종료.")
            self.exit_chat_mode(current_time)
            return "대화 상대가 사라짐"
        
        # [개선] Conversation 객체 사용
        if not self.current_conversation:
            self.current_conversation = Conversation(
                self.name,
                self.chat_partner.name,
                current_time
            )
        
        # 관련 기억 검색
        query = f"{self.chat_partner.name}와의 대화"
        context_memories = self.memory.retrieve(query, current_time=current_time)
        
        # 발언 생성
        utterance = self.conversation_system.generate_utterance(
            self.name,
            self.chat_partner.name,
            self.current_conversation,
            context_memories
        )
        
        # 종료 신호 확인
        if "[대화 종료 원함]" in utterance or "[END]" in utterance:
            utterance = utterance.replace("[대화 종료 원함]", "").replace("[END]", "").strip()
            print(f"      💬 {self.name}: {utterance}")
            print(f"      👋 [{self.name}] 대화 종료 선언.")
            
            self.current_conversation.add_message(self.name, utterance, current_time)
            self.exit_chat_mode(current_time)
            return "CHAT_END"
        
        # 정상 발언
        full_line = f"{self.name}: {utterance}"
        print(f"      💬 {full_line}")
        
        self.current_conversation.add_message(self.name, utterance, current_time)
        self.chat_history.append(full_line)
        
        # 상대방 히스토리에도 동기화
        if self.chat_partner.state == "CHATTING":
            self.chat_partner.chat_history.append(full_line)
            if self.chat_partner.current_conversation:
                self.chat_partner.current_conversation.add_message(self.name, utterance, current_time)
        
        return f"CHATTING:{full_line}"
    
    def exit_chat_mode(self, current_time):
        """대화 종료"""
        print(f"   🔓 [{self.name}] 대화 모드 해제")
        
        if self.current_conversation:
            # 전체 대화를 기억으로 저장
            full_dialogue = self.current_conversation.get_history()
            self.memory.add_memory(
                f"{self.chat_partner.name}와 나눈 대화:\n{full_dialogue}",
                current_time,
                type="chat"
            )
        
        self.state = "IDLE"
        self.chat_partner = None
        self.chat_history = []
        self.current_conversation = None