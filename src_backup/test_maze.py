# test_maze.py

from backend.maze import Maze

print("=" * 60)
print("🗺️  Day 8-9 테스트: Maze 시스템")
print("=" * 60)

# 맵 생성
maze = Maze()

# 에이전트 배치
maze.set_agent_location("김민준", "신혁수_횟집/주방")
maze.set_agent_location("신혁수", "신혁수_횟집/홀")

print("\n=== 주변 환경 감지 ===")
surroundings = maze.get_surroundings("김민준")
print(f"위치: {surroundings['location']}")
print(f"주변 오브젝트: {surroundings['objects']}")
print(f"함께 있는 사람: {surroundings['people']}")
print(f"이동 가능: {surroundings['accessible']}")

print("\n=== 경로 찾기 ===")
path = maze.find_path("신혁수_횟집/주방/냉장고", "신혁수_횟집/홀/테이블1")
print(f"냉장고 → 테이블1 경로:")
for i, step in enumerate(path):
    print(f"  {i+1}. {step}")

print("\n=== 이동 시뮬레이션 ===")
print("김민준이 홀로 이동...")
maze.set_agent_location("김민준", "신혁수_횟집/홀")

surroundings = maze.get_surroundings("김민준")
print(f"새 위치: {surroundings['location']}")
print(f"함께 있는 사람: {surroundings['people']}")  # 신혁수 보여야 함!
