# coding=utf-8
# -*- coding: UTF-8 -*-
from django.contrib.syndication.views import Feed

from subtitles.models import Subtitulo


class LatestSubsFeed(Feed):
    title = "Últimos subtítulos adicionados"
    link = ""
    description = "Últimos subtítulos adicionados"

    def items(self):
        return Subtitulo.objects.order_by('-timestamp')[:10]

    def item_title(self, item):
        return item.nombre

    def item_description(self, item):
        return item.nombre

    def item_link(self, item):
        return "/download/"+str(item.id)