import random
from collections import defaultdict
from itertools import permutations
from typing import List

from models.Card import Card


class CardDAO:
    def __init__(self):
        sequence = list(range(40))
        random.shuffle(sequence)
        self.order: List[int] = sequence
        self.setOrder()
        self.cards: List[Card] = []
        self.generateRandomCards()

    def getNthCard(self, index: int) -> Card:
        return self.cards[index]

    def getPile(self) -> List[Card]:
        result: List[Card] = []
        for i in self.order[:6]:
            result.append(self.cards[i])
        return result

    def getHands(self, players: List[str]) -> dict[str, List[Card]]:
        result: dict[str, List[Card]] = defaultdict(list)
        for i in range(len(players)):
            for j in range(6):
                result[players[i]].append(self.cards[5 + (6 * i) + j])
        return dict(result)

    def setOrder(self):
        sequence = list(range(40))
        random.shuffle(sequence)
        self.order = sequence

    def generateRandomCards(self):
        event_titles = ["Event 1", "Event 2", "Event 3", "Event 4", "Event 5"]
        period_titles = ["Period 1", "Period 2", "Period 3", "Period 4", "Period 5"]
        descriptions = ["Description 1", "Description 2", "Description 3", "Description 4", "Description 5"]
        for i in range(100):
            card_type = "EVENT" if i < 75 else "PERIOD"
            index = i + 1

            s_year = random.randint(0, 2025)
            s_month = random.randint(1, 12)
            s_day = random.randint(1, 28)

            if card_type == "PERIOD":
                e_year = random.randint(s_year, 2025)
                e_month = random.randint(1, 12)
                e_day = random.randint(1, 28)
            else:
                e_year = s_year
                e_month = s_month
                e_day = s_day

            title = random.choice(event_titles if card_type == "EVENT" else period_titles)
            descr = random.choice(descriptions)

            card = Card(
                index=index,
                type=card_type,
                s_year=s_year,
                s_month=s_month,
                s_day=s_day,
                e_year=str(e_year),
                e_month=e_month,
                e_day=e_day,
                title=title,
                descr=descr
            )

            self.cards.append(card)
