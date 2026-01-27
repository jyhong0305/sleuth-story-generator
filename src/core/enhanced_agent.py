# src/core/enhanced_agent.py

from datetime import datetime
from typing import List, Optional
from langchain_experimental.generative_agents import GenerativeAgent
from .planning import AdvancedPlanningSystem
from .maze import Maze
from .interaction import InteractionManager

class EnhancedGenerativeAgent(GenerativeAgent):
    def __init__(self, name: str, age: int, traits: str, status: str, 
                 memory, llm, maze: Maze):
        super().__init__(name=name, age=age, traits=traits, status=status, memory=memory, llm=llm)
        
        self.planning = AdvancedPlanningSystem(name, llm, self._get_relevant_memories)
        self.maze = maze
        self.current_location = None
        self.interaction = InteractionManager(name, llm, self._get_relevant_memories)
        
        self.state = "IDLE"
        self.chat_partner: Optional['EnhancedGenerativeAgent'] = None
        self.conversation_history = []
        self.last_actions = []
    
    def _get_relevant_memories(self, query: str, k: int = 10) -> List[str]:
        """LangChain 메모리 활용"""
        docs = self.memory.memory_retriever.get_relevant_documents(query)[:k]
        return [doc.page_content for doc in docs]
    
    def set_location(self, location: str):
        self.current_location = location
        self.maze.set_agent_location(self.name, location)
    
    def perceive(self, current_time: datetime) -> str:
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
    
    def autonomous_act(self, current_time: datetime, all_agents: List['EnhancedGenerativeAgent']):
        """자율 행동"""
        
        if self.state == "CHATTING":
            return self._continue_conversation(current_time)
        
        observation = self.perceive(current_time)
        surroundings = self.maze.get_surroundings(self.name)
        people_nearby = surroundings['people']
        
        self.memory.add_memory(observation, now=current_time)
        
        current_plan = self.planning.get_current_action(current_time)
        
        # 반복 방지
        self.last_actions.append(current_plan)
        if len(self.last_actions) > 3:
            self.last_actions.pop(0)
            if len(set(self.last_actions)) == 1:
                observation += " 같은 일만 반복 중. 다른 행동 필요."
        
        decision = self.planning.decide_action(observation, current_plan, people_nearby, current_time)
        
        action_type = decision['action_type']
        target = decision['target']
        thought = decision['thought']
        
        print(f"\n🤖 [{self.name}] 💭 {thought}")
        print(f"   📍 {self.current_location}")
        print(f"   📋 {current_plan}")
        print(f"   ➡️  {action_type}: {target}")
        
        result = None
        
        if action_type == "MOVE":
            result = self._execute_move(target, current_time)
        elif action_type == "CHAT":
            result = self._execute_chat(target, all_agents, current_time)
        elif action_type == "ACTION":
            result = self._execute_action(target, current_time)
        elif action_type == "WAIT":
            result = self._execute_wait(target, current_time)
        
        if result:
            self.memory.add_memory(f"{current_time.strftime('%H:%M')} - {result}", now=current_time)
        
        return result
    
    def _execute_move(self, target: str, current_time: datetime) -> str:
        normalized = self.maze.normalize_location(target)
        
        person_loc = self.maze.get_agent_location(target)
        if person_loc:
            normalized = person_loc
            print(f"   📍 {target} → {normalized}")
        
        old_loc = self.current_location
        self.set_location(normalized)
        
        return f"{old_loc}에서 {normalized}로 이동"
    
    def _execute_chat(self, target_name: str, all_agents: List['EnhancedGenerativeAgent'], 
                     current_time: datetime) -> str:
        target_agent = None
        for agent in all_agents:
            if agent.name == target_name:
                target_agent = agent
                break
        
        if not target_agent:
            return f"{target_name} 없음"
        
        if self.current_location != target_agent.current_location:
            print(f"   ⚠️  {target_name} 다른 곳")
            return self._execute_move(target_name, current_time)
        
        if target_agent.state == "CHATTING":
            return f"{target_name} 대화 중"
        
        should_talk = self.interaction.should_start_conversation(
            target_name, self.planning.get_current_action(current_time), current_time
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
    
    def _execute_action(self, action: str, current_time: datetime) -> str:
        return f"{action}"
    
    def _execute_wait(self, reason: str, current_time: datetime) -> str:
        return f"{reason}"
    
    def _continue_conversation(self, current_time: datetime) -> str:
        if not self.chat_partner:
            self.state = "IDLE"
            return "대화 상대 없음"
        
        if self.current_location != self.chat_partner.current_location:
            print(f"   👋 [{self.name}] 상대 사라짐")
            self._end_conversation(current_time)
            return "상대 사라짐"
        
        utterance = self.interaction.generate_utterance(
            self.chat_partner.name, self.conversation_history, current_time
        )
        
        wants_to_end = "[END]" in utterance
        utterance = utterance.replace("[END]", "").strip()
        
        full_line = f"{self.name}: {utterance}"
        print(f"      💬 {full_line}")
        
        self.conversation_history.append(full_line)
        
        if wants_to_end:
            print(f"      👋 대화 종료")
            self._end_conversation(current_time)
            return "대화 종료"
        
        return f"대화: {utterance}"
    
    def _end_conversation(self, current_time: datetime):
        if self.conversation_history:
            full_dialogue = "\n".join(self.conversation_history)
            self.memory.add_memory(f"{self.chat_partner.name}와 대화:\n{full_dialogue}", now=current_time)
        
        if self.chat_partner:
            self.chat_partner.state = "IDLE"
            self.chat_partner.chat_partner = None
            self.chat_partner.conversation_history = []
        
        self.state = "IDLE"
        self.chat_partner = None
        self.conversation_history = []
    
    def generate_daily_plan(self, current_time: datetime):
        self.planning.generate_daily_plan(current_time, self.traits)