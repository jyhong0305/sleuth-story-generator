# test_reflection.py

from datetime import datetime, timedelta
from backend.memory import MemoryStream
from backend.reflect import ReflectionSystem

# 에이전트 생성
memory = MemoryStream("김민준")
reflection = ReflectionSystem(memory)
memory.reflection_system = reflection  # 연결

now = datetime.now()

# 시나리오: 사장님과의 갈등 고조
events = [
    "사장님이 주방에서 나를 째려본다",
    "사장님이 '급여 줄여야겠어'라고 중얼거린다",
    "사장님과 임금 문제로 말다툼을 했다",
    "사장님이 '네가 여기서 일한 게 고맙지도 않아'라고 말했다",
    "사장님이 날카로운 칼로 생선을 매우 거칠게 손질한다",
    "손님이 주문을 했다",  # 일상적 기억 (낮은 importance)
    "사장님이 '이번 달 손님 없으면 문 닫는다'고 한숨을 쉰다",
    "사장님이 나를 보며 '다 네 탓이야'라고 말했다",
]

for i, event in enumerate(events):
    memory.add_memory(event, now + timedelta(minutes=i*10))
    print()  # 가독성

# 수동 Reflection 테스트
print("\n=== 수동 Reflection: 사장님과의 관계 분석 ===")
insights = reflection.generate_reflections(
    current_time=now + timedelta(hours=2),
    focus_query="사장님과의 관계"
)

print("\n최종 깨달음:")
for insight in insights:
    print(f"💡 {insight}")
