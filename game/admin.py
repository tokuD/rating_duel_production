from django.contrib import admin

from . import models


admin.site.register(models.LeagueCategory)
admin.site.register(models.ResultTable)
admin.site.register(models.WaitingPlayer)
admin.site.register(models.Game)
admin.site.register(models.ChatMessage)