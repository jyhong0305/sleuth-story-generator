# src/core/enhanced_agent_v2.py

from datetime import datetime
from typing import List, Optional
from .planning import AdvancedPlanningSystem
from .maze import Maze
from .interaction import InteractionManager
from .paper_memory import PaperMemorySystem

class PaperBasedAgent:
    """[논문 완전 구현] Agent"""
    
    def __init__(self, name: str, age: int, traits: str, status: str,
                 llm, embeddings, maze: Maze):
        self.name = name
        self.age = age
        self.traits = traits
        self.status = status
        
        # Memory
        self.memory = PaperMemorySystem(name, llm, embeddings)
        
        # Planning, Maze, Interaction
        self.planning = AdvancedPlanningSystem(
            name, llm, self._get_relevant_memories
        )
        self.maze = maze
        self.current_location = None
        self.interaction = InteractionManager(
            name, llm, self._get_relevant_memories
        )
        
        self.state = "IDLE"
        self.chat_partner: Optional['PaperBasedAgent'] = None
        self.conversation_history = []
        self.last_actions = []
    
    def _get_relevant_memories(self, query: str, k: int = 10) -> List[str]:
        """Planning/Interaction이 사용"""
        now = datetime.now()
        nodes = self.memory.retrieve(query, now, top_k=k)
        return [node.description for node in nodes]
    
    def set_location(self, location: str):
        self.current_location = location
        self.maze.set_agent_location(self.name, location)
    
    def perceive(self, now: datetime) -> str:
        """주변 관찰"""
        surroundings = self.maze.get_surroundings(self.name)
        
        obs = f"현재 {surroundings['location']}에 있다. "
        
        if surroundings['objects']:
            obs += f"주변: {', '.join(surroundings['objects'][:3])}. "
        
        if surroundings['people']:
            obs += f"함께 있음: {', '.join(surroundings['people'])}."
        else:
            obs += "혼자 있음."
        
        return obs
    
    def autonomous_act(self, now: datetime, all_agents: List['PaperBasedAgent']):
        """[수정] 파라미터 이름 'now'로 통일"""
        
        if self.state == "CHATTING":
            return self._continue_conversation(now)
        
        observation = self.perceive(now)
        surroundings = self.maze.get_surroundings(self.name)
        people_nearby = surroundings['people']
        
        # 기억 저장
        self.memory.add_memory(observation, now, node_type="observation")
        
        current_plan = self.planning.get_current_action(now)
        
        # 반복 방지
        self.last_actions.append(current_plan)
        if len(self.last_actions) > 3:
            self.last_actions.pop(0)
            if len(set(self.last_actions)) == 1:
                observation += " 같은 일 반복. 변화 필요."
        
        decision = self.planning.decide_action(
            observation, current_plan, people_nearby, now
        )
        
        action_type = decision['action_type']
        target = decision['target']
        thought = decision['thought']
        
        print(f"\n🤖 [{self.name}] 💭 {thought}")
        print(f"   📍 {self.current_location}")
        print(f"   📋 {current_plan}")
        print(f"   ➡️  {action_type}: {target}")
        
        result = None
        
        if action_type == "MOVE":
            result = self._execute_move(target, now)
        elif action_type == "CHAT":
            result = self._execute_chat(target, all_agents, now)
        elif action_type == "ACTION":
            result = self._execute_action(target, now)
        elif action_type == "WAIT":
            result = self._execute_wait(target, now)
        
        if result:
            self.memory.add_memory(
                f"{now.strftime('%H:%M')} - {result}",
                now,
                node_type="observation"
            )
        
        return result
    
    def _execute_move(self, target: str, now: datetime) -> str:
        """이동"""
        normalized = self.maze.normalize_location(target)
        
        person_loc = self.maze.get_agent_location(target)
        if person_loc:
            normalized = person_loc
            print(f"   📍 {target} → {normalized}")
        
        old_loc = self.current_location
        self.set_location(normalized)
        
        return f"{old_loc}에서 {normalized}로 이동"
    
    def _execute_chat(self, target_name: str, all_agents: List['PaperBasedAgent'], 
                     now: datetime) -> str:
        """대화 시작"""
        target_agent = None
        for agent in all_agents:
            if agent.name == target_name:
                target_agent = agent
                break
        
        if not target_agent:
            return f"{target_name} 없음"
        
        if self.current_location != target_agent.current_location:
            print(f"   ⚠️  {target_name} 다른 곳")
            return self._execute_move(target_name, now)
        
        if target_agent.state == "CHATTING":
            return f"{target_name} 대화 중"
        
        should_talk = self.interaction.should_start_conversation(
            target_name, self.planning.get_current_action(now), now
        )
        
        if not should_talk:
            print(f"   💭 대화 보류")
            return "대화 보류"
        
        print(f"   💬 [{self.name}] → [{target_name}] 대화 시작")
        
        self.state = "CHATTING"
        self.chat_partner = target_agent
        self.conversation_history = []
        
        target_agent.state = "CHATTING"
        target_agent.chat_partner = self
        target_agent.conversation_history = self.conversation_history
        
        return f"{target_name}와 대화 시작"
    
    def _execute_action(self, action: str, now: datetime) -> str:
        """행동"""
        return f"{action}"
    
    def _execute_wait(self, reason: str, now: datetime) -> str:
        """대기"""
        return f"{reason}"
    
    # src/core/enhanced_agent_v2.py에서 수정할 부분

    def _continue_conversation(self, now: datetime) -> str:
        """대화 진행 (수정)"""
        if not self.chat_partner:
            self.state = "IDLE"
            return "대화 상대 없음"
        
        if self.current_location != self.chat_partner.current_location:
            print(f"   👋 [{self.name}] 상대 사라짐")
            self._end_conversation(now)
            return "상대 사라짐"
        
        utterance = self.interaction.generate_utterance(
            self.chat_partner.name, self.conversation_history, now
        )
        
        wants_to_end = "[END]" in utterance
        utterance = utterance.replace("[END]", "").strip()
        
        full_line = f"{self.name}: {utterance}"
        print(f"      💬 {full_line}")
        
        self.conversation_history.append(full_line)
        
        turn_count = len(self.conversation_history)
        
        # [수정] 대화 종료 조건 - 더 길게!
        if wants_to_end and turn_count >= 5:  # 최소 5턴
            print(f"      👋 대화 종료 ({turn_count}턴)")
            self._end_conversation(now)
            return "대화 종료"
        elif turn_count >= 12:  # 최대 12턴
            print(f"      👋 대화 종료 (최대 턴)")
            self._end_conversation(now)
            return "대화 종료"
        
        return f"대화: {utterance}"
        
    def _end_conversation(self, now: datetime):
        """대화 종료"""
        if self.conversation_history:
            full_dialogue = "\n".join(self.conversation_history)
            self.memory.add_memory(
                f"{self.chat_partner.name}와 대화:\n{full_dialogue}",
                now,
                node_type="chat"
            )
        
        if self.chat_partner:
            partner_memory = self.chat_partner.memory
            if self.conversation_history:
                full_dialogue = "\n".join(self.conversation_history)
                partner_memory.add_memory(
                    f"{self.name}와 대화:\n{full_dialogue}",
                    now,
                    node_type="chat"
                )
            
            self.chat_partner.state = "IDLE"
            self.chat_partner.chat_partner = None
            self.chat_partner.conversation_history = []
        
        self.state = "IDLE"
        self.chat_partner = None
        self.conversation_history = []
    
    def generate_daily_plan(self, now: datetime):
        self.planning.generate_daily_plan(now, self.traits)