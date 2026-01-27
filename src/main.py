# src/main_paper.py

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from core.enhanced_agent_v2 import PaperBasedAgent
from core.maze import Maze

def run_paper_simulation(duration_minutes: int = 60):
    """논문 완전 구현 시뮬레이션"""
    
    print("=" * 80)
    print("🎬 논문 기반 Generative Agents 시뮬레이션")
    print("=" * 80)
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    embeddings = OpenAIEmbeddings()
    maze = Maze()
    
    print("\n📦 에이전트 초기화...")
    agents = []
    
    # 김민준
    print("   → 김민준...")
    kim = PaperBasedAgent(
        name="김민준",
        age=28,
        traits="성실하지만 급여 문제로 스트레스",
        status="신혁수 횟집 종업원",
        llm=llm,
        embeddings=embeddings,
        maze=maze
    )
    kim.set_location("신혁수_횟집/주방")
    
    start_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    kim.memory.add_memory("나는 신혁수 횟집의 종업원이다", start_time)
    kim.memory.add_memory("사장님과 3개월째 급여를 못 받고 있다", start_time)
    kim.memory.add_memory("오늘 오후 사장님과 꼭 이야기해야 한다", start_time)
    
    kim.generate_daily_plan(start_time)
    agents.append(kim)
    
    # 신혁수
    print("   → 신혁수...")
    shin = PaperBasedAgent(
        name="신혁수",
        age=45,
        traits="경영난 스트레스, 직원에게 미안함",
        status="신혁수 횟집 사장",
        llm=llm,
        embeddings=embeddings,
        maze=maze
    )
    shin.set_location("신혁수_횟집/홀")
    
    shin.memory.add_memory("나는 신혁수 횟집의 사장이다", start_time)
    shin.memory.add_memory("최근 매출 50% 감소", start_time)
    shin.memory.add_memory("김민준에게 3개월째 급여 못 줌", start_time)
    shin.memory.add_memory("오늘 대출 거절", start_time)
    
    shin.generate_daily_plan(start_time)
    agents.append(shin)
    
    # 시뮬레이션
    print("\n" + "=" * 80)
    print(f"⏰ 시작: {start_time.strftime('%H:%M')}")
    print(f"⏱️  {duration_minutes}분")
    print("=" * 80)
    
    current_time = start_time
    end_time = start_time + timedelta(minutes=duration_minutes)
    step = 0
    
    #10분 후 강제 만남 유도
    force_meeting_time = start_time + timedelta(minutes=10)

    while current_time < end_time:
        step += 1
        print(f"\n{'=' * 80}")
        print(f"⏰ Step {step}: {current_time.strftime('%H:%M')}")
        print(f"{'=' * 80}")
        
        # [추가] 10분 시점에 강제 기억 주입
        if current_time == force_meeting_time:
            print("\n⚡ [특별 이벤트] 사장님과 직원의 조우")
            
            kim.memory.add_memory(
                "청소를 마치고 사장님께 인사드리러 가야겠다고 생각했다",
                current_time,
                node_type="thought"
            )
            
            shin.memory.add_memory(
                "김민준에게 급여 이야기를 해야 한다는 생각이 들었다",
                current_time,
                node_type="thought"
            )
        

        for agent in agents:
            if agent.state != "CHATTING" or step % 2 == 0:
                try:
                    agent.autonomous_act(current_time, agents)
                except Exception as e:
                    print(f"❌ {agent.name}: {e}")
        
        current_time += timedelta(minutes=5)
    
    # 결과
    print("\n" + "=" * 80)
    print("📊 결과")
    print("=" * 80)
    
    for agent in agents:
        print(f"\n[{agent.name}]")
        print(f"  총 기억: {len(agent.memory.memory_stream)}개")
        
        # 타입별 통계
        obs = len([n for n in agent.memory.memory_stream if n.node_type == "observation"])
        thoughts = len([n for n in agent.memory.memory_stream if n.node_type == "thought"])
        chats = len([n for n in agent.memory.memory_stream if n.node_type == "chat"])
        
        print(f"    관찰: {obs}, 생각: {thoughts}, 대화: {chats}")
        
        # 최근 기억
        recent = agent.memory.memory_stream[-5:]
        print(f"  최근 기억:")
        for node in recent:
            print(f"    [{node.node_type}] {node.description[:60]}...")

if __name__ == "__main__":
    run_paper_simulation(duration_minutes=60)