# src/core/maze.py

from typing import Dict, List, Optional
from collections import deque

class Location:
    """단일 위치"""
    def __init__(self, name: str, x: int, y: int, parent: Optional[str] = None):
        self.name = name
        self.x = x
        self.y = y
        self.parent = parent
        self.accessible_from: List[str] = []
        self.objects: List[str] = []

class Maze:
    """공간 시스템"""
    
    def __init__(self, world_name: str = "신혁수_횟집"):
        self.world_name = world_name
        self.locations: Dict[str, Location] = {}
        self.agent_locations: Dict[str, str] = {}
        self._init_default_map()
    
    def _init_default_map(self):
        """횟집 맵 생성"""
        # 최상위
        self.add_location("신혁수_횟집", 0, 0)
        
        # 주요 공간
        self.add_location("신혁수_횟집/주방", 0, 1, parent="신혁수_횟집")
        self.add_location("신혁수_횟집/홀", 1, 1, parent="신혁수_횟집")
        self.add_location("거리/골목길", 2, 0)
        
        # 주방 세부
        kitchen = self.add_location("신혁수_횟집/주방/조리대", 0, 2, parent="신혁수_횟집/주방")
        kitchen.objects = ["칼", "도마", "조미료"]
        
        fridge = self.add_location("신혁수_횟집/주방/냉장고", -1, 2, parent="신혁수_횟집/주방")
        fridge.objects = ["생선", "야채", "음료수"]
        
        sink = self.add_location("신혁수_횟집/주방/싱크대", 0, 3, parent="신혁수_횟집/주방")
        sink.objects = ["설거지", "수세미"]
        
        # 홀 세부
        counter = self.add_location("신혁수_횟집/홀/카운터", 1, 2, parent="신혁수_횟집/홀")
        counter.objects = ["계산기", "메뉴판", "전화기"]
        
        table1 = self.add_location("신혁수_횟집/홀/테이블1", 2, 2, parent="신혁수_횟집/홀")
        table1.objects = ["의자 4개", "물컵", "냅킨"]
        
        table2 = self.add_location("신혁수_횟집/홀/테이블2", 2, 3, parent="신혁수_횟집/홀")
        table2.objects = ["의자 4개", "꽃병"]
        
        self._setup_connections()
    
    def _setup_connections(self):
        """이동 가능 관계"""
        connections = {
            "신혁수_횟집/주방": [
                "신혁수_횟집/홀",
                "신혁수_횟집/주방/조리대",
                "신혁수_횟집/주방/냉장고",
                "신혁수_횟집/주방/싱크대"
            ],
            "신혁수_횟집/홀": [
                "신혁수_횟집/주방",
                "거리/골목길",
                "신혁수_횟집/홀/카운터",
                "신혁수_횟집/홀/테이블1",
                "신혁수_횟집/홀/테이블2"
            ],
            "거리/골목길": ["신혁수_횟집/홀"],
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
    
    def add_location(self, name: str, x: int, y: int, parent: str = None) -> Location:
        loc = Location(name, x, y, parent)
        self.locations[name] = loc
        return loc
    
    def normalize_location(self, location: str) -> str:
        """위치 이름 정규화"""
        if location in self.locations:
            return location
        
        mapping = {
            "주방": "신혁수_횟집/주방",
            "홀": "신혁수_횟집/홀",
            "카운터": "신혁수_횟집/홀/카운터",
            "조리대": "신혁수_횟집/주방/조리대",
            "냉장고": "신혁수_횟집/주방/냉장고",
            "싱크대": "신혁수_횟집/주방/싱크대",
            "테이블": "신혁수_횟집/홀/테이블1",
            "테이블1": "신혁수_횟집/홀/테이블1",
            "테이블2": "신혁수_횟집/홀/테이블2",
            "밖": "거리/골목길",
            "골목": "거리/골목길",
            "골목길": "거리/골목길",
        }
        
        if location in mapping:
            return mapping[location]
        
        for short, full in mapping.items():
            if short in location.lower():
                return full
        
        print(f"   ⚠️  '{location}' → 홀로 해석")
        return "신혁수_횟집/홀"
    
    def set_agent_location(self, agent_name: str, location: str):
        self.agent_locations[agent_name] = location
    
    def get_agent_location(self, agent_name: str) -> Optional[str]:
        return self.agent_locations.get(agent_name)
    
    def get_agents_at_location(self, location: str) -> List[str]:
        return [
            agent for agent, loc in self.agent_locations.items()
            if loc == location
        ]
    
    def get_surroundings(self, agent_name: str) -> Dict:
        """주변 정보"""
        location = self.agent_locations.get(agent_name)
        if not location:
            return {"location": "알 수 없음", "objects": [], "people": []}
        
        loc_obj = self.locations.get(location)
        
        people = [
            other for other in self.agent_locations
            if other != agent_name and self.agent_locations[other] == location
        ]
        
        objects = loc_obj.objects.copy() if loc_obj else []
        
        return {
            "location": location,
            "objects": objects,
            "people": people,
            "accessible": loc_obj.accessible_from if loc_obj else []
        }
    
    def find_path(self, from_loc: str, to_loc: str) -> List[str]:
        """경로 탐색 (BFS)"""
        if from_loc == to_loc:
            return [from_loc]
        
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
        
        return []