from django.db import models
from django.conf import settings
import uuid
from django.urls import reverse
from django.utils import timezone
import json


class LeagueCategory(models.Model):
    name = models.CharField(max_length=50, verbose_name='リーグカテゴリ', unique=True)
    players = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name='参加者', blank=True)
    details = models.TextField(verbose_name='詳細', blank=True)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='league_category', verbose_name='主催者')
    start_at = models.DateTimeField(verbose_name='開始日時', default=timezone.now)
    finish_at = models.DateTimeField(verbose_name='終了日時', default=timezone.now)


    def __str__(self):
        return self.name

class ResultTable(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='player', related_name='result_table')
    league = models.ForeignKey(LeagueCategory, on_delete=models.CASCADE, verbose_name='リーグカテゴリ', related_name='result_table')
    dp = models.PositiveIntegerField(verbose_name='dp', default=0)
    win = models.PositiveIntegerField(verbose_name='勝ち数', default=0)
    loose = models.PositiveIntegerField(verbose_name='負け数', default=0)
    game_num = models.PositiveIntegerField(verbose_name='試合数', default=0)
    rank = models.PositiveIntegerField(verbose_name='順位', default=1)

    def __str__(self):
        return "{} - {}".format(self.player, self.league)

    def get_absolute_url(self):
        return reverse('game:search_for_opponent', kwargs={"league_name": self.league.name})


class WaitingPlayer(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='player', related_name='waiting_player')
    league = models.ForeignKey(LeagueCategory, on_delete=models.CASCADE, verbose_name='リーグカテゴリ', related_name='waiting_player')
    dp = models.PositiveIntegerField(verbose_name='dp', default=0)

    def __str__(self):
        return "{} - {}".format(self.player, self.league)


def default_result():
    result = {
        'player1': '',
        'player2': '',
        'thema': ''
    }
    return json.dumps(result)

class Game(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4
    )
    league = models.ForeignKey(LeagueCategory, on_delete=models.CASCADE, related_name='game', verbose_name='リーグカテゴリ')
    room = models.CharField(max_length=200, verbose_name='room名', unique=True)
    player1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='game_player1', verbose_name='player1')
    player2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='game_player2', verbose_name='player2')
    result = models.JSONField(verbose_name='試合結果', default=default_result)
    start_at = models.DateTimeField(verbose_name='開始日時', default=timezone.now)
    submitted_players = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name='結果提出者')

    def __str__(self):
        return "{} vs {} at {}".format(self.player1, self.player2, self.start_at.strftime("%Y/%m/%d %H:%M:%S"))


class ChatMessage(models.Model):
    content = models.TextField(verbose_name='チャットメッセージ', max_length=200)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='chat_message', verbose_name='試合')
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='chat_message', verbose_name='投稿者')
    timestamp = models.DateTimeField(verbose_name='投稿時刻', default=timezone.now)

    def __str__(self):
        return "{} by {} ({})".format(self.content[:10], self.posted_by, self.game)


