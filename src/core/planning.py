# src/core/planning.py

from datetime import datetime, timedelta
from typing import List, Dict, Callable, Optional

class Plan:
    def __init__(self, description: str, start_time: datetime, duration_minutes: int):
        self.description = description
        self.start_time = start_time
        self.end_time = start_time + timedelta(minutes=duration_minutes)
        self.status = "planned"
        
    def is_active(self, current_time: datetime) -> bool:
        return self.start_time <= current_time < self.end_time
    
    def __repr__(self):
        return f"[{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}] {self.description}"

class AdvancedPlanningSystem:
    def __init__(self, agent_name: str, llm, get_memories: Callable):
        self.agent_name = agent_name
        self.llm = llm
        self.get_memories = get_memories
        self.daily_plan: List[Plan] = []
        self.hourly_plan: List[Plan] = []
    
    def generate_daily_plan(self, current_time: datetime, agent_traits: str):
        """Daily Plan 생성 (대화 중심으로)"""
        
        recent_memories = self.get_memories("최근 일정과 중요한 일", 10)
        memory_context = "\n".join([f"- {m}" for m in recent_memories])
        
        prompt = f"""당신은 {self.agent_name}입니다.

    성격: {agent_traits}

    최근 기억:
    {memory_context}

    현재: {current_time.strftime('%Y-%m-%d %H:%M')}

    **중요한 규칙:**
    1. 다른 사람들과의 만남/대화를 반드시 포함할 것
    2. 구체적인 사람 이름을 명시할 것 (예: "김민준과 이야기")
    3. 너무 세부적이지 않게 (큰 틀만)
    4. 5-7개 활동

    **특히 중요:** 기억에 있는 중요한 관계/문제는 반드시 계획에 포함!

    형식:
    HH:MM | 분 | 활동

    좋은 예:
    09:00 | 60 | 출근 후 주방 청소
    10:00 | 30 | 김민준 찾아가서 인사하기
    10:30 | 60 | 김민준과 급여 문제 진지하게 논의
    12:00 | 120 | 점심 손님 응대

    나쁜 예 (이렇게 하지 마세요):
    09:00 | 5 | 주방 바닥 쓰레기 줍기
    09:05 | 10 | 조리대 위 기름기 제거
    09:15 | 5 | 냉장고 재료 확인
    ..."""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            plans = []
            for line in content.strip().split('\n'):
                if '|' not in line:
                    continue
                    
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    try:
                        time_str = parts[0]
                        duration = int(parts[1])
                        desc = parts[2]
                        
                        hour, minute = map(int, time_str.split(':'))
                        plan_time = current_time.replace(hour=hour, minute=minute, second=0)
                        
                        plans.append(Plan(desc, plan_time, duration))
                    except:
                        continue
            
            self.daily_plan = plans
            
            if plans:
                print(f"\n📅 [{self.agent_name}] Daily Plan:")
                for p in plans:
                    print(f"   {p}")
            
            return plans
            
        except Exception as e:
            print(f"⚠️ Daily plan 실패: {e}")
            return []
    def generate_hourly_plan(self, current_time: datetime, current_task: str):
        """Hourly Plan 생성"""
        relevant_memories = self.get_memories(current_task, 5)
        memory_context = "\n".join([f"- {m}" for m in relevant_memories])
        
        prompt = f"""당신은 {self.agent_name}입니다.

현재 작업: {current_task}

관련 기억:
{memory_context}

이 작업을 3-5단계로 나누세요.

형식:
+분 | 구체적 행동

예시:
+5 | 냉장고에서 재료 꺼내기
+15 | 야채 손질"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            plans = []
            offset = 0
            
            for line in content.strip().split('\n'):
                if '|' not in line:
                    continue
                
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    try:
                        duration_str = parts[0].replace('+', '').strip()
                        duration = int(duration_str)
                        desc = parts[1]
                        
                        plan_time = current_time + timedelta(minutes=offset)
                        plans.append(Plan(desc, plan_time, duration))
                        
                        offset += duration
                    except:
                        continue
            
            self.hourly_plan = plans
            return plans
            
        except Exception as e:
            print(f"⚠️ Hourly plan 실패: {e}")
            return []
    
    def get_current_action(self, current_time: datetime) -> str:
        """현재 행동"""
        for plan in self.hourly_plan:
            if plan.is_active(current_time):
                return plan.description
        
        for plan in self.daily_plan:
            if plan.is_active(current_time):
                self.generate_hourly_plan(current_time, plan.description)
                for p in self.hourly_plan:
                    if p.is_active(current_time):
                        return p.description
                return plan.description
        
        return "자유 시간"
    
    # src/core/planning.py
    
    def decide_action(self, observation: str, current_plan: str, 
                    people_nearby: List[str], current_time: datetime) -> Dict[str, str]:
        """행동 결정 (개선)"""
        
        relevant_memories = self.get_memories(observation, 8)
        memory_context = "\n".join([f"- {m}" for m in relevant_memories])
        
        # [추가] 긴급 기억 확인
        urgent_memories = [m for m in relevant_memories if "[긴급]" in m]
        urgent_context = ""
        if urgent_memories:
            urgent_context = f"\n\n⚠️ 긴급 사항:\n" + "\n".join([f"- {m}" for m in urgent_memories])
        
        prompt = f"""당신은 {self.agent_name}입니다.

    **현재 상황:**
    {observation}

    **현재 계획:** {current_plan}

    **주변 사람:** {', '.join(people_nearby) if people_nearby else '없음'}

    **관련 기억:**
    {memory_context}
    {urgent_context}

    **행동을 결정하세요.**

    **중요:**
    - 주변에 중요한 사람이 있으면 대화를 우선시하세요!
    - [긴급] 표시가 있는 기억은 최우선!
    - 같은 행동을 반복하지 마세요

    **형식:**
    THOUGHT: [생각]
    ACTION_TYPE: [MOVE | CHAT | ACTION | WAIT]
    TARGET: [구체적 대상]

    **예시:**
    주변: 신혁수
    기억: 급여 문제 해결 필요

    THOUGHT: 사장님이 바로 옆에 있다. 지금 급여 이야기를 해야 한다.
    ACTION_TYPE: CHAT
    TARGET: 신혁수"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            result = {
                "thought": "",
                "action_type": "WAIT",
                "target": current_plan
            }
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('THOUGHT:'):
                    result["thought"] = line.replace('THOUGHT:', '').strip()
                elif line.startswith('ACTION_TYPE:'):
                    result["action_type"] = line.replace('ACTION_TYPE:', '').strip()
                elif line.startswith('TARGET:'):
                    result["target"] = line.replace('TARGET:', '').strip()
            
            return result
            
        except Exception as e:
            print(f"⚠️ 행동 결정 실패: {e}")
            return {
                "thought": "오류",
                "action_type": "CHAT" if people_nearby else "ACTION",
                "target": people_nearby[0] if people_nearby else current_plan
            }