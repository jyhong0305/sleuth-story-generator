class Scratch:
    def __init__(self):
        self.curr_address = "Unknown"  # 현재 위치
        self.curr_action = "멍하니 있음" # 현재 행동
        self.daily_plan = []           # 오늘의 할 일 목록
        self.chat_history = []         # 방금 나눈 대화 임시 저장

    def get_summary(self):
        """프롬프트에 넣기 좋게 현재 상태 요약"""
        return f"현재 위치: {self.curr_address}, 현재 행동: {self.curr_action}"