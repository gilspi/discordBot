import asyncio
import re
from typing import Union, Optional, Tuple, List

from datetime import datetime, timedelta
from pytz import timezone

import discord
from discord.ext import commands
from discord.ext.commands import errors

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger


class Time:

    def __init__(self,
                 days: Optional[int] = 0,
                 hours: Optional[int] = 0,
                 minutes: Optional[int] = 0,
                 seconds: Union[int, float] = 0.0):
        self.__days = days
        self.__hours = hours
        self.__minutes = minutes
        self.__seconds = seconds
        self.__gmt = timezone('GMT')

    @property
    def days(self):
        return self.__days

    @property
    def hours(self):
        return self.__hours

    @property
    def minutes(self):
        return self.__minutes

    @property
    def seconds(self):
        return self.__seconds

    @property
    def tzinfo(self):
        return self.__gmt


t = Time(1, 1, 1, 1)
print(t.hours)
