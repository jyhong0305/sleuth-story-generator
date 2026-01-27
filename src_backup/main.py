from datetime import datetime, timedelta
import json
import os

from backend.maze import Maze
from persona import Persona

# 1. 맵 로드
if not os.path.exists("data"):
    os.makedirs("data")
dummy_map = {
    "신혁수_횟집": { "주방": ["칼", "도마"], "홀": ["TV", "테이블"], "뒷문": ["쓰레기통"] },
    "거리": { "골목길": ["가로등"] }
}
with open("data/world_map.json", "w", encoding='utf-8') as f:
    json.dump(dummy_map, f, ensure_ascii=False)

def run_simulation():
    maze = Maze("data/world_map.json")
    agent_a = Persona("박해진", "알콜중독자, 빚 3억, 욱하는 성격", maze)
    agent_b = Persona("최주연", "이중적인 성격, 열등감, 거짓말쟁이", maze)
    maze.set_agent_location("박해진", "신혁수_횟집/홀")
    maze.set_agent_location("최주연", "신혁수_횟집/홀")
    agents = [agent_a, agent_b]
    
    current_time = datetime(2023, 12, 20, 19, 0)
    end_time = datetime(2023, 12, 20, 19, 40)
    
    while current_time < end_time:
        print(f"\n=== 🕒 {current_time.strftime('%H:%M')} ===")
        
        # [지령]
        god_instruction_park = None
        god_instruction_choi = None
        
        if current_time.hour == 19 and current_time.minute == 10:
             print("⚡ [지령] 소집: 둘 다 '신혁수_횟집/홀'로 이동.")
             god_instruction_park = "최주연과 대화하기 위해 '신혁수_횟집/홀'로 이동해라."
             god_instruction_choi = "박해진을 만나러 '신혁수_횟집/홀'로 이동해라."

        elif current_time.hour == 19 and current_time.minute == 20:
            print("⚡ [지령] 박해진 살인 충동 주입.")
            # 지시를 더 구체적으로 변경
            god_instruction_park = "이성이 마비되었다. 대화하지 마라. ACTION을 선택하고 타겟을 '최주연'이라고 명시하여 칼로 찔러라."

        # 행동 처리
        actions_this_tick = {}
        for agent in agents:
            if not agent.is_alive: continue
            
            instruction = god_instruction_park if agent.name == "박해진" else god_instruction_choi
            log = agent.act(current_time, force_thought=instruction)
            actions_this_tick[agent.name] = log

        # 상호작용 및 사건 처리
        for agent in agents:
            if not agent.is_alive: continue
            log = actions_this_tick.get(agent.name, "")
            
            # 1. 대화 연결
            if log.startswith("CHAT_REQUEST:"):
                target_name = log.split(":")[1].strip()
                target_agent = next((a for a in agents if a.name == target_name), None)
                
                if target_agent and target_agent.is_alive:
                    my_loc = maze.get_agent_location(agent.name)
                    target_loc = maze.get_agent_location(target_name)
                    
                    if my_loc == target_loc:
                        print(f"   🤝 [상호작용 연결] {agent.name} <--> {target_name}")
                        agent.enter_chat_mode(target_agent)
                        target_agent.enter_chat_mode(agent)
                    else:
                        print(f"   ❌ 거리가 멀어 대화 실패.")

            # 2. 살인 판정 (스마트 로직 적용)
            elif log.startswith("행동 수행:"):
                act_content = log.replace("행동 수행:", "").strip()
                violence_keywords = ["죽", "찌르", "살해", "공격", "칼", "술병", "위협", "때리"]
                
                # 폭력 키워드가 감지되면 범인 색출 시작
                if any(word in act_content for word in violence_keywords):
                    target_victim = None
                    
                    # A. 이름으로 찾기 (기존 방식)
                    target_victim = next((a for a in agents if a.name in act_content and a.name != agent.name), None)
                    
                    # B. [NEW] 이름이 없으면? 같은 방에 있는 사람을 자동으로 타겟팅 (문맥 추론)
                    if not target_victim:
                        my_loc = maze.get_agent_location(agent.name)
                        # 나랑 같은 방에 있고, 내가 아닌 사람
                        target_victim = next((a for a in agents if maze.get_agent_location(a.name) == my_loc and a.name != agent.name), None)
                    
                    # 피해자 확정 시 처형
                    if target_victim:
                        print(f"\n   🩸 [충격 이벤트] {agent.name}이(가) '{act_content}' 행동을 하여 {target_victim.name}을(를) 살해했습니다!")
                        target_victim.is_alive = False
                        
                        # 대화 중단 처리
                        if target_victim.state == "CHATTING" and target_victim.chat_partner:
                            partner = target_victim.chat_partner
                            partner.exit_chat_mode(current_time)
                            print(f"      (살인으로 인해 대화가 강제 종료되었습니다.)")
                        
                        target_victim.memory.add_memory(f"{agent.name}에게 살해당함.", current_time, type="event")
                        agent.memory.add_memory(f"{target_victim.name}을(를) 살해함.", current_time, type="event")
                    else:
                        print(f"   ⚠️ [경고] {agent.name}이 폭력적 행동('{act_content}')을 했으나 대상을 찾을 수 없습니다.")

        current_time += timedelta(minutes=10)

if __name__ == "__main__":
    run_simulation()