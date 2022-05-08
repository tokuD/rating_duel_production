import json, time, random, string, secrets
from unicodedata import name
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views import generic
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import mixins, get_user_model
from django.urls import reverse
from django.contrib import messages

from . import models, forms

class HomeView(generic.TemplateView):
    template_name = 'home.html'


class SearchForOpponentView(mixins.LoginRequiredMixin, generic.TemplateView):
    template_name = 'game/search_for_opponent.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        league = models.LeagueCategory.objects.get(name=self.kwargs.get('league_name'))
        try:
            result = models.ResultTable.objects.get(player=self.request.user, league=league)
        except models.ResultTable.DoesNotExist:
            return HttpResponseRedirect(reverse('game:create_result_table', kwargs={"league_name": league.name}))
        game = models.Game.objects.filter(league=league).filter(Q(player1=self.request.user)|Q(player2=self.request.user)).exclude(submitted_players=self.request.user).distinct()
        if game.exists():
            messages.warning(self.request, "結果を入力してください")
            return HttpResponseRedirect(reverse('game:room', kwargs={"league_name": game[0].league, "room_name": game[0].room}))
        context.update({'league': league, 'result': result})
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('game:search_for_opponent'))


class SearchForOpponentAjaxView(mixins.LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        league_name = self.kwargs.get('league_name')
        self.league = models.LeagueCategory.objects.get(name=league_name)
        self.dp = models.ResultTable.objects.get(player=self.request.user, league=self.league).dp
        models.WaitingPlayer.objects.get_or_create(player=self.request.user, league=self.league, dp=self.dp)
        opponent = self.search_for_opponent(0)
        if opponent == 'matched':
            game = models.Game.objects.filter(player2=self.request.user, league=self.league).order_by('-start_at')[0]
            messages.success(self.request, "対戦相手が決定しました!")
            return JsonResponse({"is_success": True, "roomname": game.room})
        elif opponent:
            with transaction.atomic():
                waiting1 = models.WaitingPlayer.objects.get(player=self.request.user, league=self.league)
                waiting2 = models.WaitingPlayer.objects.get(player=opponent, league=self.league)
                waiting1.delete()
                waiting2.delete()
                while True:
                    roomname = self.generate_room()
                    if not models.Game.objects.filter(room=roomname).exists():
                        break
                game = models.Game.objects.create(
                    room=roomname,
                    player1=self.request.user,
                    player2=opponent,
                    league=self.league
                )
            messages.success(self.request, "対戦相手が決定しました!")
            return JsonResponse({"is_success": True, "roomname": game.room})
        else:
            return JsonResponse({"is_success": False, "roomname": None})

    def search_for_opponent(self, count):
        print('search now...')
        if not models.WaitingPlayer.objects.filter(player=self.request.user, league=self.league).exists():
            return 'matched'
        if count == 20:
            models.WaitingPlayer.objects.filter(player=self.request.user, league=self.league).delete()
            return False
        lowwer_dp, upper_dp = self.dp - 10000, self.dp + 10000
        opponent_candidates = models.WaitingPlayer.objects.filter(league=self.league, dp__gte=lowwer_dp, dp__lte=upper_dp).exclude(player=self.request.user).distinct()
        if not opponent_candidates.exists():
            time.sleep(1)
            return self.search_for_opponent(count+1)
        ind = random.randint(0, opponent_candidates.count()-1)
        opponent = opponent_candidates[ind]
        return opponent.player

    def generate_room(self):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(10))

class RoomView(mixins.LoginRequiredMixin, generic.TemplateView):
    template_name = 'game/room.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_name = self.kwargs.get('room_name')
        self.game = models.Game.objects.get(room=room_name)
        result = json.loads(self.game.result)['player1' if self.request.user == self.game.player1 else 'player2']
        chat_messages = models.ChatMessage.objects.filter(game=self.game).order_by('-timestamp')
        opponent = self.game.player2 if self.request.user == self.game.player1 else self.game.player1
        context.update({"game": self.game, 'chat_messages': chat_messages, 'result': result, 'opponent': opponent})
        return context

    def post(self, request, *args, **kwargs):
        self.game = models.Game.objects.get(room=self.kwargs.get('room_name'))
        self.league = self.game.league
        self.result_table = models.ResultTable.objects.get(player=self.request.user, league=self.league)
        result_num = self.request.POST.get('result')
        if self.request.user in self.game.submitted_players.all():
            #*更新処理
            self.reset_dp(json.loads(self.game.result))
        else:
            #*新規作成
            self.game.submitted_players.add(self.request.user)
        self.update_dp(result_num)
        self.update_result(result_num)
        return HttpResponseRedirect(reverse("game:search_for_opponent", kwargs={"league_name": self.league}))

    def reset_dp(self, results):
        player = 'player1' if self.request.user == self.game.player1 else 'player2'
        result = results[player]
        if 'WIN' == result:
            self.result_table.dp += -1000
            self.result_table.win += -1
        elif 'LOOSE' == result:
            self.result_table.dp += 1000
            self.result_table.loose += -1
        self.result_table.game_num += -1
        self.result_table.save()

    def update_dp(self, result_num):
        if result_num == '0':
            self.result_table.dp += 1000
            self.result_table.win += 1
        elif result_num == '1':
            self.result_table.dp = max(self.result_table.dp-1000, 0)
            self.result_table.loose += 1
        self.result_table.game_num += 1
        self.result_table.save()

    def update_result(self, result_num):
        result = json.loads(self.game.result)
        player = 'player1' if self.request.user == self.game.player1 else 'player2'
        RESULT_CHAR = {'0': 'WIN', '1': 'LOOSE', '2': 'DRAW'}
        result[player] = RESULT_CHAR[result_num]
        self.game.result = json.dumps(result)
        self.game.save()


class CreateResultTableView(mixins.LoginRequiredMixin, generic.CreateView):
    model = models.ResultTable
    template_name = 'game/create_result_table.html'
    form_class = forms.CreateResultTableForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        league_name = self.kwargs.get('league_name')
        league = models.LeagueCategory.objects.get(name=league_name)
        context.update({'league': league})
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.player = self.request.user
        with transaction.atomic():
            self.object.league.players.add(self.request.user)
            self.object.save()
            messages.success(self.request, "{}に参加登録しました。".format(self.object.league))
        return HttpResponseRedirect(self.get_success_url())

class LeagueListView(mixins.LoginRequiredMixin, generic.ListView):
    template_name = 'game/league_list.html'
    model = models.LeagueCategory
    paginate_by = 10


