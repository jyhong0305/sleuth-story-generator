# test_planning.py

from datetime import datetime
from backend.memory import MemoryStream
from backend.reflect import ReflectionSystem
from cognitive_modules.plan import PlanningSystem

# 에이전트 생성
memory = MemoryStream("김민준")
reflection = ReflectionSystem(memory)
memory.reflection_system = reflection

planning = PlanningSystem(memory)

now = datetime.now().replace(hour=8, minute=0)  # 오전 8시로 설정

# 초기 기억 추가
memory.add_memory("나는 신혁수 횟집의 종업원이다", now)
memory.add_memory("사장님과 최근 급여 문제로 갈등이 있다", now)

print("=" * 60)
print("📅 Day 5 테스트: Daily Planning")
print("=" * 60)

# Daily Plan 생성
daily_plans = planning.generate_daily_plan(now, "횟집 종업원")

print("\n오늘의 계획:")
for plan in daily_plans:
    print(f"  {plan}")

print("\n" + "=" * 60)
print("⏰ Day 6 테스트: Hourly Planning")
print("=" * 60)

# 현재 시간을 11:00으로 변경
now_11am = now.replace(hour=11, minute=0)

# 11시에 해당하는 daily task 찾기
current_daily_task = None
for plan in daily_plans:
    if plan.is_active(now_11am):
        current_daily_task = plan.description
        break

if current_daily_task:
    print(f"\n현재 진행 중: {current_daily_task}")
    hourly_plans = planning.generate_hourly_plan(now_11am, current_daily_task)
    
    print("\n세부 계획:")
    for plan in hourly_plans:
        print(f"  {plan}")

print("\n" + "=" * 60)
print("🎬 Day 7 테스트: Action Decision")
print("=" * 60)

# 특정 상황에서 행동 결정
observation = "주방에 있다. 사장님이 화난 얼굴로 다가오고 있다."
decision = planning.react_to_observation(
    observation,
    now_11am,
    people_nearby=["신혁수(사장님)"]
)

print(f"\n관찰: {observation}")
print(f"생각: {decision['thought']}")
print(f"행동: {decision['action_type']} → {decision['target']}")
