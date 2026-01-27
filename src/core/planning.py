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
        """Daily Plan 생성"""
        recent_memories = self.get_memories("최근 일정과 중요한 일", 10)
        memory_context = "\n".join([f"- {m}" for m in recent_memories])
        
        prompt = f"""당신은 {self.agent_name}입니다.

성격: {agent_traits}

최근 기억:
{memory_context}

현재: {current_time.strftime('%Y-%m-%d %H:%M')}

**중요: 다른 사람들과의 상호작용을 반드시 포함하세요!**

오늘 하루 계획을 세우세요. 5-8개 활동.

규칙:
1. 업무 + 대인관계 균형
2. 특정 사람 이름 명시 (예: "김민준과 대화")
3. 장소 이동 포함
4. 감정적 목표 포함 (예: "급여 문제 해결")

형식:
HH:MM | 분 | 활동 (구체적 사람 이름 포함)

예시:
09:00 | 30 | 주방 청소
09:30 | 30 | 김민준 찾아가서 인사하기
10:00 | 30 | 김민준과 급여 문제 이야기
15:00 | 60 | 홀에서 손님 응대"""

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
                for p in plans[:3]:
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
    
    def decide_action(self, observation: str, current_plan: str, 
                     people_nearby: List[str], current_time: datetime) -> Dict[str, str]:
        """행동 결정"""
        relevant_memories = self.get_memories(observation, 8)
        memory_context = "\n".join([f"- {m}" for m in relevant_memories])
        
        prompt = f"""당신은 {self.agent_name}입니다.

상황: {observation}
계획: {current_plan}
주변: {', '.join(people_nearby) if people_nearby else '없음'}

기억:
{memory_context}

행동을 결정하세요.

형식:
THOUGHT: [생각]
ACTION_TYPE: [MOVE | CHAT | ACTION | WAIT]
TARGET: [장소/사람/행동/이유]

예시:
THOUGHT: 사장님이 보이니 급여 이야기를 해야겠다
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
                "action_type": "ACTION",
                "target": current_plan
            }