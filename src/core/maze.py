# src/core/maze.py (완전 수정)

from typing import Dict, List, Optional
from collections import deque

class Location:
    def __init__(self, name: str, x: int, y: int, parent: Optional[str] = None):
        self.name = name
        self.x = x
        self.y = y
        self.parent = parent
        self.accessible_from: List[str] = []
        self.objects: List[str] = []

class Maze:
    """미술관 공간 시스템"""
    
    def __init__(self, world_name: str = "화이트갤러리"):
        self.world_name = world_name
        self.locations: Dict[str, Location] = {}
        self.agent_locations: Dict[str, str] = {}
        self._init_gallery_map()
    
    def _init_gallery_map(self):
        """미술관 맵 생성"""
        # 1층
        lobby = self.add_location("화이트갤러리/1층/로비", 0, 0)
        lobby.objects = ["안내데스크", "의자", "팜플렛"]
        
        exhibition1 = self.add_location("화이트갤러리/1층/전시실A", 1, 0)
        exhibition1.objects = ["회화작품 10점", "조명", "벤치"]
        
        storage = self.add_location("화이트갤러리/1층/창고", 2, 0)
        storage.objects = ["포장재", "사다리", "청소도구"]
        
        # 2층
        exhibition2 = self.add_location("화이트갤러리/2층/전시실B", 0, 1)
        exhibition2.objects = ["조각품 5점", "스포트라이트"]
        
        office = self.add_location("화이트갤러리/2층/사무실", 1, 1)
        office.objects = ["책상", "컴퓨터", "서류", "금고"]
        
        lounge = self.add_location("화이트갤러리/2층/라운지", 2, 1)
        lounge.objects = ["소파", "커피머신", "잡지"]
        
        # 3층
        vip_room = self.add_location("화이트갤러리/3층/VIP실", 0, 2)
        vip_room.objects = ["고가조각품", "와인", "안락의자"]
        
        rooftop = self.add_location("화이트갤러리/3층/옥상", 1, 2)
        rooftop.objects = ["난간", "환기구", "비상계단"]
        
        # 연결 설정
        connections = {
            "화이트갤러리/1층/로비": ["화이트갤러리/1층/전시실A", "화이트갤러리/2층/전시실B"],
            "화이트갤러리/1층/전시실A": ["화이트갤러리/1층/로비", "화이트갤러리/1층/창고"],
            "화이트갤러리/1층/창고": ["화이트갤러리/1층/전시실A"],
            
            "화이트갤러리/2층/전시실B": ["화이트갤러리/1층/로비", "화이트갤러리/2층/사무실", "화이트갤러리/3층/VIP실"],
            "화이트갤러리/2층/사무실": ["화이트갤러리/2층/전시실B", "화이트갤러리/2층/라운지"],
            "화이트갤러리/2층/라운지": ["화이트갤러리/2층/사무실"],
            
            "화이트갤러리/3층/VIP실": ["화이트갤러리/2층/전시실B", "화이트갤러리/3층/옥상"],
            "화이트갤러리/3층/옥상": ["화이트갤러리/3층/VIP실"],
        }
        
        for loc_name, accessible in connections.items():
            if loc_name in self.locations:
                self.locations[loc_name].accessible_from = accessible
    
    def add_location(self, name: str, x: int, y: int, parent: str = None) -> Location:
        loc = Location(name, x, y, parent)
        self.locations[name] = loc
        return loc
    
    def normalize_location(self, location: str) -> str:
        """위치 정규화"""
        if location in self.locations:
            return location
        
        mapping = {
            "로비": "화이트갤러리/1층/로비",
            "전시실A": "화이트갤러리/1층/전시실A",
            "전시실B": "화이트갤러리/2층/전시실B",
            "창고": "화이트갤러리/1층/창고",
            "사무실": "화이트갤러리/2층/사무실",
            "라운지": "화이트갤러리/2층/라운지",
            "VIP실": "화이트갤러리/3층/VIP실",
            "옥상": "화이트갤러리/3층/옥상",
            "1층": "화이트갤러리/1층/로비",
            "2층": "화이트갤러리/2층/전시실B",
            "3층": "화이트갤러리/3층/VIP실",
        }
        
        if location in mapping:
            return mapping[location]
        
        for short, full in mapping.items():
            if short in location.lower():
                return full
        
        return "화이트갤러리/1층/로비"
    
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