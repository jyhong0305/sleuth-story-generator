# backend/plan.py (새 파일)

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from backend.memory import MemoryStream

class Plan:
    """단일 계획 객체"""
    def __init__(self, description: str, start_time: datetime, duration_minutes: int):
        self.description = description
        self.start_time = start_time
        self.end_time = start_time + timedelta(minutes=duration_minutes)
        self.status = "planned"  # planned / in_progress / completed / cancelled
        
    def is_active(self, current_time: datetime) -> bool:
        """현재 시각에 실행 중인가?"""
        return self.start_time <= current_time < self.end_time
    
    def __repr__(self):
        return f"[{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}] {self.description}"

class PlanningSystem:
    """논문의 계층적 Planning 구현"""
    
    def __init__(self, memory_stream: MemoryStream):
        self.memory_stream = memory_stream
        self.daily_plan: List[Plan] = []
        self.hourly_plan: List[Plan] = []
        self.current_action: Optional[str] = None
        
    def generate_daily_plan(self, current_time: datetime, agent_trait: str) -> List[Plan]:
        """
        [Layer 1] 하루 전체 계획 생성
        
        Args:
            current_time: 현재 시각
            agent_trait: 에이전트 특성 ("횟집 종업원", "탐정" 등)
        """
        # 최근 기억 + 성격 기반으로 계획 생성
        recent_memories = self.memory_stream.get_recent_memories(current_time, hours=48)
        
        prompt = f"""You are planning the day for {self.memory_stream.agent_name}, who is a {agent_trait}.

Current time: {current_time.strftime('%Y-%m-%d %H:%M')}

Recent context:
{recent_memories}

Generate a realistic daily schedule with 5-8 activities. Consider:
1. Work duties and responsibilities
2. Personal needs (meals, rest)
3. Social interactions
4. Recent events and their impact

Format each activity as:
HH:MM | Duration(minutes) | Activity description

Example:
09:00 | 60 | 출근해서 주방 청소하기
10:00 | 120 | 점심 준비 시작
"""

        try:
            response = self.memory_stream.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400
            )
            
            # 파싱: "HH:MM | Duration | Description" 형식
            plans = []
            for line in response.choices[0].message.content.strip().split('\n'):
                if '|' not in line:
                    continue
                    
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    try:
                        time_str = parts[0]
                        duration = int(parts[1])
                        desc = parts[2]
                        
                        # 시간 파싱
                        hour, minute = map(int, time_str.split(':'))
                        plan_time = current_time.replace(hour=hour, minute=minute, second=0)
                        
                        plans.append(Plan(desc, plan_time, duration))
                    except:
                        continue
            
            self.daily_plan = plans
            
            # 계획을 기억으로 저장
            plan_summary = "\n".join([str(p) for p in plans])
            self.memory_stream.add_memory(
                f"오늘의 계획:\n{plan_summary}",
                current_time,
                mem_type="plan"
            )
            
            return plans
            
        except Exception as e:
            print(f"⚠️ Daily plan 생성 실패: {e}")
            return []
    
    def generate_hourly_plan(self, current_time: datetime, current_daily_task: str) -> List[Plan]:
        """
        [Layer 2] 현재 시간대 세부 계획
        
        Args:
            current_daily_task: 현재 진행 중인 daily plan의 description
        """
        # 관련 기억 검색
        relevant_memories = self.memory_stream.retrieve(
            query=current_daily_task,
            current_time=current_time,
            top_k=5
        )
        memory_context = "\n".join([f"- {m.content}" for m in relevant_memories])
        
        prompt = f"""Break down this task into 3-5 concrete sub-tasks for {self.memory_stream.agent_name}:

Main task: {current_daily_task}
Current time: {current_time.strftime('%H:%M')}

Relevant context:
{memory_context}

Generate a step-by-step breakdown. Each step should take 5-20 minutes.

Format:
+5 | First step
+10 | Second step (5분 후 시작, 10분 소요)
+15 | Third step

Be specific and realistic."""

        try:
            response = self.memory_stream.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=300
            )
            
            # 파싱: "+Duration | Description"
            plans = []
            offset_minutes = 0
            
            for line in response.choices[0].message.content.strip().split('\n'):
                if '|' not in line:
                    continue
                
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    try:
                        duration_str = parts[0].replace('+', '').strip()
                        duration = int(duration_str)
                        desc = parts[1]
                        
                        plan_time = current_time + timedelta(minutes=offset_minutes)
                        plans.append(Plan(desc, plan_time, duration))
                        
                        offset_minutes += duration
                    except:
                        continue
            
            self.hourly_plan = plans
            return plans
            
        except Exception as e:
            print(f"⚠️ Hourly plan 생성 실패: {e}")
            return []
    
    def get_current_action(self, current_time: datetime) -> Optional[str]:
        """현재 할 행동 결정 (개선)"""
        
        # 1. 먼저 Daily plan에서 현재 활성화된 계획 찾기
        active_daily = None
        for plan in self.daily_plan:
            if plan.is_active(current_time):
                active_daily = plan
                break
        
        if not active_daily:
            return "대기 중"
        
        # 2. Hourly plan이 없거나 시간이 지났으면 새로 생성
        needs_new_hourly = True
        if self.hourly_plan:
            for plan in self.hourly_plan:
                if plan.is_active(current_time):
                    needs_new_hourly = False
                    return plan.description
        
        if needs_new_hourly:
            print(f"   🔄 새로운 hourly plan 생성: {active_daily.description}")
            self.generate_hourly_plan(current_time, active_daily.description)
            
            # 방금 생성된 plan 중 활성화된 것 찾기
            for plan in self.hourly_plan:
                if plan.is_active(current_time):
                    return plan.description
        
        return active_daily.description
    
    def react_to_observation(self, 
                            observation: str, 
                            current_time: datetime,
                            people_nearby: List[str],
                            current_plan: str = None) -> Dict[str, str]:  # ← 파라미터 추가
        """
        [핵심] 관찰 + 기억 + 계획을 종합해서 행동 결정
        """
        # 1. 관련 기억 검색
        relevant_memories = self.memory_stream.retrieve(
            query=observation,
            current_time=current_time,
            top_k=8
        )
        memory_context = "\n".join([f"- {m.content}" for m in relevant_memories])
        
        # 2. 현재 계획 (전달받은 것 사용)
        if not current_plan:
            current_plan = self.get_current_action(current_time)
        
        # 3. LLM에게 행동 결정 요청
        prompt = f"""You are {self.memory_stream.agent_name}.

Current situation:
{observation}

Your current plan: {current_plan}  ← 이제 제대로 전달됨!

Relevant memories:
{memory_context}

People nearby: {', '.join(people_nearby) if people_nearby else 'None'}

Decide what to do next. Consider:
1. **Your current plan** - Should you stick to it or change?
2. The people around you - Any important interactions?
3. Your memories and past experiences
4. If you've been doing the same thing too long, consider moving or changing activity

Respond in this exact format:
THOUGHT: [Your reasoning process]
ACTION_TYPE: [MOVE | CHAT | ACTION | WAIT]
TARGET: [Where to go / Who to talk to / What to do / What to wait for]

Example:
THOUGHT: 현재 계획은 청소지만, 사장님이 보이니 급여 이야기를 꺼내야겠다.
ACTION_TYPE: CHAT
TARGET: 신혁수
"""

        try:
            response = self.memory_stream.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=200
            )
            
            # 파싱
            text = response.choices[0].message.content.strip()
            result = {
                "thought": "",
                "action_type": "WAIT",
                "target": "현재 위치에서 대기"
            }
            
            for line in text.split('\n'):
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
                "thought": "오류 발생",
                "action_type": "WAIT",
                "target": current_plan if current_plan else "대기"
            }