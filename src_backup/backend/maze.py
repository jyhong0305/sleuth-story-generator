# backend/maze.py (새 파일)

from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass

@dataclass
class Location:
    """단일 위치"""
    name: str
    x: int
    y: int
    parent: Optional[str] = None  # 상위 장소 (예: "주방"의 parent는 "횟집")
    accessible_from: List[str] = None  # 이동 가능한 장소들
    
    def __post_init__(self):
        if self.accessible_from is None:
            self.accessible_from = []

class Maze:
    """공간 시스템 - 에이전트 위치 관리"""
    
    def __init__(self, world_name: str = "신혁수_횟집"):
        self.world_name = world_name
        self.locations: Dict[str, Location] = {}
        self.agent_locations: Dict[str, str] = {}  # {agent_name: location_name}
        
        # 기본 맵 초기화
        self._init_default_map()
    
    def _init_default_map(self):
        """기본 횟집 맵 생성"""
        # 최상위 장소
        self.add_location("신혁수_횟집", 0, 0)
        
        # 주요 공간
        self.add_location("신혁수_횟집/주방", 0, 1, parent="신혁수_횟집")
        self.add_location("신혁수_횟집/홀", 1, 1, parent="신혁수_횟집")
        self.add_location("거리/골목길", 2, 0)
        
        # 주방 내부
        self.add_location("신혁수_횟집/주방/조리대", 0, 2, parent="신혁수_횟집/주방")
        self.add_location("신혁수_횟집/주방/냉장고", -1, 2, parent="신혁수_횟집/주방")
        self.add_location("신혁수_횟집/주방/싱크대", 0, 3, parent="신혁수_횟집/주방")
        
        # 홀 내부
        self.add_location("신혁수_횟집/홀/카운터", 1, 2, parent="신혁수_횟집/홀")
        self.add_location("신혁수_횟집/홀/테이블1", 2, 2, parent="신혁수_횟집/홀")
        self.add_location("신혁수_횟집/홀/테이블2", 2, 3, parent="신혁수_횟집/홀")
        
        # 이동 가능 연결 설정
        self._setup_connections()
    
    def _setup_connections(self):
        """장소 간 이동 가능 관계 설정"""
        connections = {
            "신혁수_횟집/주방": ["신혁수_횟집/홀", "신혁수_횟집/주방/조리대", "신혁수_횟집/주방/냉장고", "신혁수_횟집/주방/싱크대"],
            "신혁수_횟집/홀": ["신혁수_횟집/주방", "거리/골목길", "신혁수_횟집/홀/카운터", "신혁수_횟집/홀/테이블1", "신혁수_횟집/홀/테이블2"],
            "거리/골목길": ["신혁수_횟집/홀"],
            
            # 세부 위치들은 부모로 돌아갈 수 있음
            "신혁수_횟집/주방/조리대": ["신혁수_횟집/주방"],
            "신혁수_횟집/주방/냉장고": ["신혁수_횟집/주방"],
            "신혁수_횟집/주방/싱크대": ["신혁수_횟집/주방"],
            "신혁수_횟집/홀/카운터": ["신혁수_횟집/홀"],
            "신혁수_횟집/홀/테이블1": ["신혁수_횟집/홀"],
            "신혁수_횟집/홀/테이블2": ["신혁수_횟집/홀"],
        }
        
        for loc_name, accessible in connections.items():
            if loc_name in self.locations:
                self.locations[loc_name].accessible_from = accessible
    
    def add_location(self, name: str, x: int, y: int, parent: str = None):
        """새 위치 추가"""
        self.locations[name] = Location(name, x, y, parent)
    
    def set_agent_location(self, agent_name: str, location_name: str):
        """에이전트 위치 설정"""
        if location_name not in self.locations:
            print(f"⚠️ 알 수 없는 위치: {location_name}")
            # 비슷한 이름 찾기 (간단한 매칭)
            for loc in self.locations.keys():
                if location_name in loc or loc in location_name:
                    print(f"   → {loc}(으)로 이동합니다")
                    location_name = loc
                    break
        
        self.agent_locations[agent_name] = location_name
        print(f"📍 [{agent_name}] {location_name}")
    
    def get_agent_location(self, agent_name: str) -> Optional[str]:
        """에이전트 현재 위치"""
        return self.agent_locations.get(agent_name)
    
    def get_agents_at_location(self, location_name: str) -> List[str]:
        """특정 위치에 있는 에이전트들"""
        return [
            agent for agent, loc in self.agent_locations.items()
            if loc == location_name
        ]
    
    def get_surroundings(self, agent_name: str) -> Dict:
        """에이전트 주변 정보 (perceive 용)"""
        location = self.agent_locations.get(agent_name)
        if not location:
            return {"location": "알 수 없음", "objects": [], "people": []}
        
        loc_obj = self.locations.get(location)
        
        # 같은 위치의 다른 에이전트들
        people = [
            other for other in self.agent_locations
            if other != agent_name and self.agent_locations[other] == location
        ]
        
        # 주변 오브젝트 (장소 이름에서 추출)
        objects = []
        if loc_obj:
            # 하위 장소들을 오브젝트로 간주
            objects = [
                loc.name.split('/')[-1] 
                for loc in self.locations.values()
                if loc.parent == location
            ]
        
        return {
            "location": location,
            "objects": objects,
            "people": people,
            "accessible": loc_obj.accessible_from if loc_obj else []
        }
    
    def can_move(self, from_loc: str, to_loc: str) -> bool:
        """이동 가능 여부"""
        if from_loc not in self.locations or to_loc not in self.locations:
            return False
        
        from_obj = self.locations[from_loc]
        return to_loc in from_obj.accessible_from
    
    def find_path(self, from_loc: str, to_loc: str) -> List[str]:
        """
        A* 알고리즘으로 경로 찾기
        (간단한 BFS로 구현 - 실제 논문은 A*)
        """
        if from_loc == to_loc:
            return [from_loc]
        
        from collections import deque
        
        queue = deque([(from_loc, [from_loc])])
        visited = {from_loc}
        
        while queue:
            current, path = queue.popleft()
            
            if current not in self.locations:
                continue
            
            for next_loc in self.locations[current].accessible_from:
                if next_loc in visited:
                    continue
                
                new_path = path + [next_loc]
                
                if next_loc == to_loc:
                    return new_path
                
                visited.add(next_loc)
                queue.append((next_loc, new_path))
        
        return []  # 경로 없음
    
    def save_to_file(self, filepath: str):
        """맵 저장"""
        data = {
            "world_name": self.world_name,
            "locations": {
                name: {
                    "x": loc.x,
                    "y": loc.y,
                    "parent": loc.parent,
                    "accessible": loc.accessible_from
                }
                for name, loc in self.locations.items()
            }
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)