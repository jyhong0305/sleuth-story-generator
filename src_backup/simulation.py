# src/simulation.py (새 파일)

from datetime import datetime, timedelta
from typing import List, Dict
import time

from backend.memory import MemoryStream
from backend.reflect import ReflectionSystem
from cognitive_modules.plan import PlanningSystem
from backend.maze import Maze
from cognitive_modules.conversation import ConversationSystem, Conversation

class Agent:
    """완전 통합된 에이전트"""
    
    def __init__(self, name: str, trait: str, maze: Maze, start_location: str):
        self.name = name
        self.trait = trait
        self.maze = maze
        self.last_location = start_location
        self.idle_count = 0  # [추가] 같은 곳에 너무 오래 있으면 강제 이동

        # 모든 시스템 초기화
        self.memory = MemoryStream(name)
        self.memory.reflection_system = ReflectionSystem(self.memory)
        self.memory.planning_system = PlanningSystem(self.memory)
        self.conversation_system = ConversationSystem(self.memory)
        
        # 상태
        self.state = "IDLE"  # IDLE, CHATTING, MOVING
        self.chat_partner: 'Agent' = None
        self.current_conversation: Conversation = None
        
        # 초기 위치
        self.maze.set_agent_location(name, start_location)
        
        # 초기 기억
        self.memory.add_memory(f"나는 {trait}이다", datetime.now())
    
    def perceive(self, current_time: datetime) -> str:
        """주변 환경 관찰"""
        surroundings = self.maze.get_surroundings(self.name)
        
        obs = f"{surroundings['location']}에 있다. "
        
        if surroundings['objects']:
            obs += f"주변에 {', '.join(surroundings['objects'])}이(가) 있다. "
        
        if surroundings['people']:
            obs += f"{', '.join(surroundings['people'])}이(가) 함께 있다."
        
        return obs
    
    def act(self, current_time: datetime, all_agents: List['Agent']):
        """행동 결정 및 수행"""
        
        if self.state == "CHATTING":
            return self._continue_conversation(current_time)
        
        # 일반 행동
        observation = self.perceive(current_time)
        self.memory.add_memory(observation, current_time)
        
        surroundings = self.maze.get_surroundings(self.name)
        people_nearby = surroundings['people']
        
        # 같은 장소에 오래 있으면 강제 이동
        current_loc = self.maze.get_agent_location(self.name)
        if current_loc == self.last_location:
            self.idle_count += 1
        else:
            self.idle_count = 0
            self.last_location = current_loc
        
        # 3번 이상 같은 곳이면 강제로 다른 행동 유도
        if self.idle_count >= 3:
            print(f"   ⚡ [{self.name}] 너무 오래 한 곳에 있음 → 강제 이동")
            observation += " 너무 오래 같은 일만 하고 있다. 다른 곳으로 이동하거나 다른 일을 해야 한다."
            self.idle_count = 0

        # 행동 결정
        context = self.memory.retrieve(observation, current_time, top_k=8)
        current_plan = self.memory.planning_system.get_current_action(current_time)
        
        # [수정] current_plan을 명시적으로 전달!
        decision = self.memory.planning_system.react_to_observation(
            observation,
            current_time,
            people_nearby,
            current_plan=current_plan  # ← 이제 전달됨!
        )
        
        action_type = decision['action_type']
        target = decision['target']
        thought = decision['thought']
        
        print(f"\n🤖 [{self.name}] 💭 {thought}")
        print(f"   ➡️  {action_type}: {target}")
        
        # 행동 수행
        if action_type == "MOVE":
            self._move_to(target, current_time)
            
        elif action_type == "CHAT":
            self._initiate_chat(target, all_agents, current_time, context)
            
        elif action_type == "ACTION":
            self._perform_action(target, current_time)
            
        elif action_type == "WAIT":
            self._wait(target, current_time)
    
    def _move_to(self, target: str, current_time: datetime):
        """이동"""
        # 위치 보정
        location_map = {
            "주방": "신혁수_횟집/주방",
            "홀": "신혁수_횟집/홀",
            "카운터": "신혁수_횟집/홀/카운터",
            "조리대": "신혁수_횟집/주방/조리대",
            "밖": "거리/골목길",
            "골목": "거리/골목길"
        }
        
        target = location_map.get(target, target)
        
        # 사람 이름이면 그 사람 위치로
        person_loc = self.maze.get_agent_location(target)
        if person_loc:
            target = person_loc
        
        self.maze.set_agent_location(self.name, target)
        self.memory.add_memory(f"{target}(으)로 이동했다", current_time, mem_type="action")
    
    def _initiate_chat(self, target_name: str, all_agents: List['Agent'], 
                       current_time: datetime, context_memories: List):
        """대화 시작 시도"""
        # 대상 찾기
        target_agent = None
        for agent in all_agents:
            if agent.name == target_name:
                target_agent = agent
                break
        
        if not target_agent:
            print(f"   ⚠️  {target_name}을(를) 찾을 수 없음")
            return
        
        # 같은 위치인지 확인
        my_loc = self.maze.get_agent_location(self.name)
        target_loc = self.maze.get_agent_location(target_name)
        
        if my_loc != target_loc:
            print(f"   ⚠️  {target_name}이(가) 다른 곳에 있음")
            return
        
        # 상대가 대화 가능한지
        if target_agent.state == "CHATTING":
            print(f"   ⚠️  {target_name}이(가) 다른 사람과 대화 중")
            return
        
        # 대화 시작 여부 판단
        current_plan = self.memory.planning_system.get_current_action(current_time)
        should_talk = self.conversation_system.should_initiate_conversation(
            self.name,
            target_name,
            context_memories,
            current_plan
        )
        
        if not should_talk:
            print(f"   💭 대화를 보류함")
            return
        
        # 대화 시작!
        print(f"   💬 [{self.name}] → [{target_name}] 대화 시작")
        
        self.state = "CHATTING"
        self.chat_partner = target_agent
        self.current_conversation = Conversation(self.name, target_name, current_time)
        
        target_agent.state = "CHATTING"
        target_agent.chat_partner = self
        target_agent.current_conversation = self.current_conversation
    
    def _continue_conversation(self, current_time: datetime):
        """대화 진행"""
        if not self.chat_partner or not self.current_conversation:
            self.state = "IDLE"
            return
        
        # 위치 확인
        my_loc = self.maze.get_agent_location(self.name)
        partner_loc = self.maze.get_agent_location(self.chat_partner.name)
        
        if my_loc != partner_loc:
            print(f"   👋 [{self.name}] 대화 상대가 사라짐")
            self._end_conversation(current_time)
            return
        
        # 발언 생성
        context = self.memory.retrieve(
            f"{self.chat_partner.name}와의 대화",
            current_time,
            top_k=5
        )
        
        utterance = self.conversation_system.generate_utterance(
            self.name,
            self.chat_partner.name,
            self.current_conversation,
            context
        )
        
        # 종료 신호
        wants_to_end = "[대화 종료 원함]" in utterance or "[END]" in utterance
        utterance = utterance.replace("[대화 종료 원함]", "").replace("[END]", "").strip()
        
        print(f"      💬 {self.name}: {utterance}")
        
        self.current_conversation.add_message(self.name, utterance, current_time)
        
        if wants_to_end:
            print(f"      👋 [{self.name}] 대화 종료 제안")
            self._end_conversation(current_time)
    
    def _end_conversation(self, current_time: datetime):
        """대화 종료"""
        if not self.current_conversation:
            return
        
        # 대화 기록 저장
        full_dialogue = self.current_conversation.get_history()
        self.memory.add_memory(
            f"{self.chat_partner.name}와 나눈 대화:\n{full_dialogue}",
            current_time,
            mem_type="chat"
        )
        
        # 상대도 종료
        if self.chat_partner:
            partner_name = self.chat_partner.name
            self.chat_partner.state = "IDLE"
            self.chat_partner.chat_partner = None
            self.chat_partner.current_conversation = None
            print(f"   🔓 [{partner_name}] 대화 모드 해제")
        
        self.state = "IDLE"
        self.chat_partner = None
        self.current_conversation = None
    
    def _perform_action(self, action: str, current_time: datetime):
        """행동 수행"""
        self.memory.add_memory(f"{action}을(를) 한다", current_time, mem_type="action")
    
    def _wait(self, reason: str, current_time: datetime):
        """대기"""
        pass  # 아무것도 안 함

class Simulation:
    """전체 시뮬레이션 관리"""
    
    def __init__(self, scenario_name: str = "신혁수_횟집"):
        self.scenario_name = scenario_name
        self.maze = Maze()
        self.agents: List[Agent] = []
        self.start_time = datetime.now().replace(hour=9, minute=0, second=0)
        self.current_time = self.start_time
        
    def add_agent(self, name: str, trait: str, start_location: str, 
                  initial_memories: List[str] = None):
        """에이전트 추가"""
        agent = Agent(name, trait, self.maze, start_location)
        
        # 초기 기억 추가
        if initial_memories:
            for mem in initial_memories:
                agent.memory.add_memory(mem, self.current_time)
        
        # Daily plan 생성
        agent.memory.planning_system.generate_daily_plan(self.current_time, trait)
        
        self.agents.append(agent)
        print(f"✅ [{name}] 에이전트 생성 완료")
        
        return agent
    
    def run(self, duration_minutes: int = 120, speed: float = 1.0):
        """
        시뮬레이션 실행
        
        Args:
            duration_minutes: 시뮬레이션 시간 (분)
            speed: 실행 속도 (1.0 = 실시간, 0.1 = 10배속)
        """
        print("\n" + "="*60)
        print(f"🎬 시뮬레이션 시작: {self.scenario_name}")
        print(f"⏰ 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"📊 에이전트: {len(self.agents)}명")
        print("="*60 + "\n")
        
        end_time = self.start_time + timedelta(minutes=duration_minutes)
        
        step = 0
        while self.current_time < end_time:
            step += 1
            print(f"\n{'='*60}")
            print(f"⏰ Step {step}: {self.current_time.strftime('%H:%M')}")
            print(f"{'='*60}")
            
            # 각 에이전트 행동
            for agent in self.agents:
                if agent.state != "CHATTING" or step % 2 == 0:  # 대화 중이면 2턴마다
                    agent.act(self.current_time, self.agents)
            
            # 시간 진행 (5분 단위)
            self.current_time += timedelta(minutes=5)
            
            # 속도 조절
            if speed > 0:
                time.sleep(0.5 / speed)
        
        print("\n" + "="*60)
        print("🏁 시뮬레이션 종료")
        print("="*60)
        
        self._print_summary()
    
    def _print_summary(self):
        """결과 요약"""
        print("\n📊 시뮬레이션 결과 요약\n")
        
        for agent in self.agents:
            print(f"\n[{agent.name}]")
            print(f"  총 기억: {len(agent.memory.memories)}개")
            
            # 주요 깨달음
            reflections = [m for m in agent.memory.memories if m.type == "reflection"]
            if reflections:
                print(f"  주요 깨달음 ({len(reflections)}개):")
                for r in reflections[-3:]:  # 최근 3개
                    print(f"    💡 {r.content}")