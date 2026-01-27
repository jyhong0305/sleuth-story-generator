# test_conversation.py (수정)

from datetime import datetime
from backend.memory import MemoryStream
from backend.reflect import ReflectionSystem
from cognitive_modules.conversation import ConversationSystem, Conversation

print("=" * 60)
print("🗣️  Day 10-11 테스트: 대화 시스템")
print("=" * 60)

# 두 에이전트 생성
kim_memory = MemoryStream("김민준")
kim_memory.reflection_system = ReflectionSystem(kim_memory)
kim_conversation = ConversationSystem(kim_memory)

shin_memory = MemoryStream("신혁수")
shin_memory.reflection_system = ReflectionSystem(shin_memory)
shin_conversation = ConversationSystem(shin_memory)

now = datetime.now()

# 배경 기억 추가
print("\n=== 배경 설정 ===")
kim_memory.add_memory("나는 신혁수 횟집의 종업원이다", now)
kim_memory.add_memory("사장님과 3개월째 급여를 못 받고 있다", now)
kim_memory.add_memory("오늘은 꼭 급여 문제를 해결하고 싶다", now)  # 추가!
kim_memory.add_memory("더 이상 참을 수 없는 상황이다", now)  # 추가!

shin_memory.add_memory("나는 신혁수 횟집의 사장이다", now)
shin_memory.add_memory("최근 매출이 급격히 감소해서 걱정이다", now)
shin_memory.add_memory("김민준에게 급여를 지급하지 못하고 있어 미안하다", now)

print("\n=== 대화 시작 판단 ===")
kim_context = kim_memory.retrieve("사장님 급여", now, top_k=5)
kim_plan = "잠시 휴식 중"  # "점심 준비"보다 덜 급한 상황으로 변경

should_talk = kim_conversation.should_initiate_conversation(
    "김민준",
    "신혁수",
    kim_context,
    kim_plan
)

print(f"대화 시작 여부: {should_talk}")

# [수정] should_talk이 False여도 강제로 대화 진행
print("\n=== 대화 진행 (강제 시작) ===")
conv = Conversation("김민준", "신혁수", now)

for turn in range(4):  # 4턴으로 증가
    print(f"\n--- Turn {turn + 1} ---")
    
    # 김민준 발언
    kim_context = kim_memory.retrieve("급여 대화 사장님", now, top_k=5)
    kim_utterance = kim_conversation.generate_utterance(
        "김민준", "신혁수", conv, kim_context
    )
    conv.add_message("김민준", kim_utterance, now)
    print(f"💬 김민준: {kim_utterance}")
    
    # 종료 체크
    if "[대화 종료 원함]" in kim_utterance or "[END]" in kim_utterance:
        print("   → 김민준이 대화 종료 원함")
        break
    
    # 신혁수 응답
    shin_context = shin_memory.retrieve("김민준 급여", now, top_k=5)
    shin_utterance = shin_conversation.generate_utterance(
        "신혁수", "김민준", conv, shin_context
    )
    conv.add_message("신혁수", shin_utterance, now)
    print(f"💬 신혁수: {shin_utterance}")
    
    # 종료 체크
    if "[대화 종료 원함]" in shin_utterance or "[END]" in shin_utterance:
        print("   → 신혁수가 대화 종료 원함")
        break

print("\n" + "=" * 60)
print("📝 최종 대화 기록")
print("=" * 60)
print(conv.get_history())

print("\n" + "=" * 60)
print("🧠 대화 후 Reflection 테스트")
print("=" * 60)

# 대화 내용을 기억으로 저장
full_dialogue = conv.get_history()
kim_memory.add_memory(f"신혁수와 나눈 대화:\n{full_dialogue}", now, type="chat")
shin_memory.add_memory(f"김민준과 나눈 대화:\n{full_dialogue}", now, type="chat")

# Reflection 강제 실행
print("\n[김민준의 회고]")
kim_insights = kim_memory.reflection_system.generate_reflections(
    now, 
    focus_query="신혁수와의 급여 대화"
)
for insight in kim_insights:
    print(f"💡 {insight}")

print("\n[신혁수의 회고]")
shin_insights = shin_memory.reflection_system.generate_reflections(
    now,
    focus_query="김민준과의 급여 대화"
)
for insight in shin_insights:
    print(f"💡 {insight}")