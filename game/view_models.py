import json
from django.utils import timezone

class LeagueCategoryMapper():
    def __init__(self, obj):
        self.obj = obj

    def as_dict(self):
        data = {
            'name': self.obj.name,
            'players': [player.username for player in self.obj.players.all()],
            'details': self.obj.details,
            'host': self.obj.host.username,
            'start_at': self.obj.start_at.strftime("%Y/%m/%d %H:%M"),
            'finish_at': self.obj.finish_at.strftime("%Y/%m/%d %H:%M"),
            'can_participate': True if self.obj.start_at <= timezone.now() and timezone.now() <= self.obj.finish_at else False,
        }
        return data

class GameMapper():
    def __init__(self, obj):
        self.obj = obj

    def as_dict(self):
        result = json.loads(self.obj.result)
        data = {
            'league': self.obj.league.name,
            'player1': self.obj.player1.username,
            'player2': self.obj.player2.username,
            'start_at': self.obj.start_at.strftime("%Y/%m/%d %H:%M:%S"),
            'result1': result['player1'],
            'result2': result['player2'],
            'thema': result['thema'],
        }
        return data
