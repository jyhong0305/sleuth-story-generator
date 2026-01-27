# test_memory.py

from datetime import datetime, timedelta
from backend.memory import MemoryStream

# 에이전트 생성
memory = MemoryStream("김민준")

# 기억 추가 (시간 순서대로)
now = datetime.now()
memory.add_memory("신혁수 횟집 주방에서 생선을 손질하고 있다", now)
memory.add_memory("사장님이 날카로운 칼을 들고 있다", now + timedelta(minutes=5))
memory.add_memory("사장님과 돈 문제로 큰 싸움을 했다", now + timedelta(minutes=10))  # 중요!
memory.add_memory("홀에서 손님이 주문을 했다", now + timedelta(minutes=15))

# 검색 테스트
print("\n=== 검색: '사장님' ===")
results = memory.retrieve("사장님", now + timedelta(minutes=20))
for mem in results:
    print(f"- {mem.content} (중요도: {mem.importance})")

print("\n=== 검색: '칼' ===")
results = memory.retrieve("칼", now + timedelta(minutes=20))
for mem in results:
    print(f"- {mem.content} (중요도: {mem.importance})")