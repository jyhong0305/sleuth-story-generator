# src/story_murder_mystery.py (새 파일!)

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from core.enhanced_agent_v2 import PaperBasedAgent
from core.maze import Maze

def run_mystery_simulation():
    """미술관 미스터리 시뮬레이션"""
    
    print("=" * 80)
    print("🎨 심야 미술관의 비밀 - 4인 추리 스토리")
    print("=" * 80)
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.8)
    embeddings = OpenAIEmbeddings()
    maze = Maze("화이트갤러리")
    
    agents = []
    start_time = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
    
    # === 1. 박서연 (큐레이터) ===
    print("\n📦 에이전트 생성...")
    print("   → 박서연 (큐레이터)...")
    
    park = PaperBasedAgent(
        name="박서연",
        age=32,
        traits="완벽주의자, 예술에 열정적, 최근 스트레스 많음",
        status="화이트갤러리 수석 큐레이터",
        llm=llm,
        embeddings=embeddings,
        maze=maze
    )
    park.set_location("화이트갤러리/2층/사무실")
    
    park.memory.add_memory("나는 화이트갤러리의 수석 큐레이터다", start_time)
    park.memory.add_memory("최근 고가 작품 도난 사건이 발생했다", start_time)
    park.memory.add_memory("오늘 보험 조사관이 방문한다", start_time)
    park.memory.add_memory("과거에 위작을 진품으로 전시한 적이 있다는 비밀이 있다", start_time)
    
    park.generate_daily_plan(start_time)
    agents.append(park)
    
    # === 2. 이준호 (경비원) ===
    print("   → 이준호 (경비원)...")
    
    lee = PaperBasedAgent(
        name="이준호",
        age=28,
        traits="성실하지만 돈이 절실함, 야간 근무 중 이상한 소리 들음",
        status="화이트갤러리 경비원",
        llm=llm,
        embeddings=embeddings,
        maze=maze
    )
    lee.set_location("화이트갤러리/1층/로비")
    
    lee.memory.add_memory("나는 화이트갤러리 경비원이다", start_time)
    lee.memory.add_memory("불법 도박 빚이 5천만원이나 있다", start_time)
    lee.memory.add_memory("어젯밤 3층에서 이상한 소리를 들었다", start_time)
    lee.memory.add_memory("돈이 절실하게 필요하다", start_time)
    
    lee.generate_daily_plan(start_time)
    agents.append(lee)
    
    # === 3. 최유진 (보험 조사관) ===
    print("   → 최유진 (보험 조사관)...")
    
    choi = PaperBasedAgent(
        name="최유진",
        age=45,
        traits="예리하고 의심 많음, 과거 미술품 밀매 연루",
        status="보험회사 조사관",
        llm=llm,
        embeddings=embeddings,
        maze=maze
    )
    choi.set_location("화이트갤러리/1층/로비")
    
    choi.memory.add_memory("나는 보험 조사관이다", start_time)
    choi.memory.add_memory("도난 작품 조사차 화이트갤러리에 왔다", start_time)
    choi.memory.add_memory("과거 미술품 밀매에 연루된 적이 있다", start_time)
    choi.memory.add_memory("이 미술관에 뭔가 수상한 점이 있다", start_time)
    
    choi.generate_daily_plan(start_time)
    agents.append(choi)
    
    # === 4. 한지우 (도슨트) ===
    print("   → 한지우 (신입 도슨트)...")
    
    han = PaperBasedAgent(
        name="한지우",
        age=25,
        traits="순수하지만 관찰력 뛰어남, 박서연 존경",
        status="화이트갤러리 신입 도슨트",
        llm=llm,
        embeddings=embeddings,
        maze=maze
    )
    han.set_location("화이트갤러리/1층/전시실A")
    
    han.memory.add_memory("나는 신입 도슨트다", start_time)
    han.memory.add_memory("박서연 선배를 존경하고 있다", start_time)
    han.memory.add_memory("실은 재벌가 딸이지만 신분을 숨기고 있다", start_time)
    han.memory.add_memory("오늘 미술관에 이상한 분위기가 감돈다", start_time)
    
    han.generate_daily_plan(start_time)
    agents.append(han)
    
    # === 시뮬레이션 시작 ===
    print("\n" + "=" * 80)
    print(f"⏰ 시작: 2024년 12월 15일 {start_time.strftime('%H:%M')}")
    print(f"📍 장소: 화이트갤러리 미술관")
    print(f"👥 등장인물: {len(agents)}명")
    print("=" * 80)
    
    current_time = start_time
    end_time = start_time + timedelta(hours=6)  # 6시간 (18:00 ~ 24:00)
    step = 0
    
    # 이벤트 타임라인
    event_19 = start_time + timedelta(hours=1)   # 19:00 정전
    event_20 = start_time + timedelta(hours=2)   # 20:00 비명
    event_21 = start_time + timedelta(hours=3)   # 21:00 작품 실종
    
    while current_time < end_time:
        step += 1
        print(f"\n{'=' * 80}")
        print(f"⏰ Step {step}: {current_time.strftime('%H:%M')}")
        print(f"{'=' * 80}")
        
        # === 이벤트 1: 정전 (19:00) ===
        if current_time == event_19:
            print("\n⚡⚡⚡ [사건 발생] 갑작스러운 정전! ⚡⚡⚡")
            for agent in agents:
                agent.memory.add_memory(
                    "[긴급] 갑자기 불이 꺼졌다! 정전이 발생했다!",
                    current_time,
                    node_type="observation"
                )
            print("   🔦 모든 인물이 정전을 경험함")
        
        # === 이벤트 2: 비명 (20:00) ===
        if current_time == event_20:
            print("\n😱😱😱 [사건 발생] 3층 VIP실에서 비명 소리! 😱😱😱")
            for agent in agents:
                agent.memory.add_memory(
                    "[긴급] 3층 VIP실에서 비명 소리가 들렸다! 무슨 일인가?",
                    current_time,
                    node_type="observation"
                )
            # 모두 3층으로 유도
            park.set_location("화이트갤러리/3층/VIP실")
            lee.set_location("화이트갤러리/3층/VIP실")
            print("   📍 경비원과 큐레이터가 VIP실로 달려감")
        
        # === 이벤트 3: 작품 실종 (21:00) ===
        if current_time == event_21:
            print("\n🚨🚨🚨 [사건 발생] VIP실의 고가 조각품이 사라졌다! 🚨🚨🚨")
            for agent in agents:
                agent.memory.add_memory(
                    "[긴급] VIP실의 1억원짜리 조각품이 사라졌다! 누가 가져갔나?",
                    current_time,
                    node_type="observation"
                )
            # 모두 VIP실로
            for agent in agents:
                agent.set_location("화이트갤러리/3층/VIP실")
            print("   🔍 모든 인물이 VIP실에 모임")
        
        # 에이전트 행동
        for agent in agents:
            if agent.state != "CHATTING" or step % 2 == 0:
                try:
                    agent.autonomous_act(current_time, agents)
                except Exception as e:
                    print(f"❌ {agent.name}: {e}")
        
        current_time += timedelta(minutes=10)  # 10분 단위
    
    # === 결과 출력 ===
    print("\n" + "=" * 80)
    print("📊 시뮬레이션 결과 - 6시간 요약")
    print("=" * 80)
    
    for agent in agents:
        print(f"\n[{agent.name}]")
        print(f"  총 기억: {len(agent.memory.memory_stream)}개")
        
        obs = len([n for n in agent.memory.memory_stream if n.node_type == "observation"])
        thoughts = len([n for n in agent.memory.memory_stream if n.node_type == "thought"])
        chats = len([n for n in agent.memory.memory_stream if n.node_type == "chat"])
        
        print(f"    관찰: {obs}, 생각: {thoughts}, 대화: {chats}")
        
        # 대화 기록
        chat_memories = [m for m in agent.memory.memory_stream if m.node_type == "chat"]
        if chat_memories:
            print(f"\n  주요 대화:")
            for chat in chat_memories[-2:]:
                lines = chat.description.split('\n')[:3]
                for line in lines:
                    print(f"    {line[:80]}...")
        
        # Reflection
        reflections = [m for m in agent.memory.memory_stream if m.node_type == "thought" and "[깨달음]" in m.description]
        if reflections:
            print(f"\n  깨달음:")
            for ref in reflections[-2:]:
                print(f"    💡 {ref.description.replace('[깨달음]', '').strip()[:100]}...")

if __name__ == "__main__":
    run_mystery_simulation()