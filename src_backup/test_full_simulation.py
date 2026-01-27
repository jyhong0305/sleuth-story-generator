# test_full_simulation_v2.py

from simulation import Simulation

sim = Simulation("신혁수_횟집_긴장")

# 더 구체적인 초기 기억
김민준 = sim.add_agent(
    name="김민준",
    trait="신혁수 횟집의 종업원",
    start_location="신혁수_횟집/주방",
    initial_memories=[
        "사장님과 3개월째 급여를 못 받고 있다",
        "더 이상 참을 수 없다",
        "오늘 오후 3시에 사장님과 꼭 이야기해야 한다",
        "사장님이 나를 피하는 것 같다",
        "동료들도 같은 상황이다"
    ]
)

신혁수 = sim.add_agent(
    name="신혁수",
    trait="신혁수 횟집의 사장",
    start_location="신혁수_횟집/홀",
    initial_memories=[
        "최근 매출이 50% 감소했다",
        "오늘 은행에서 대출 거절당했다",
        "김민준에게 급여를 3개월째 못 주고 있다",
        "김민준이 화가 많이 난 것 같다",
        "어떻게든 이번 주 안에 돈을 마련해야 한다"
    ]
)

# [추가] 강제 이벤트 주입
print("\n⚡ 10:00 - 김민준이 홀로 이동하도록 유도")
김민준.memory.add_memory(
    "주방 청소를 마쳤다. 사장님께 인사라도 드려야겠다.",
    sim.current_time
)

# 2시간 시뮬레이션
sim.run(duration_minutes=120, speed=3.0)