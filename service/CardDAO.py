import os
import random
import sqlite3
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
        self.readCardsFromDB()
        self.handSize = 6
        self.pileSize = 6

    def getNthCard(self, index: int) -> Card:
        return self.cards[index]

    def getPile(self) -> List[Card]:
        result: List[Card] = []
        for i in self.order[:self.pileSize]:
            result.append(self.cards[i])
        return result

    def getHands(self, players: List[str]) -> dict[str, List[Card]]:
        result: dict[str, List[Card]] = defaultdict(list)
        for i in range(len(players)):
            for j in range(self.handSize):
                result[players[i]].append(self.cards[self.order[self.pileSize + (self.handSize * i) + j]])
        return dict(result)

    def setOrder(self):
        sequence = list(range(40))
        random.shuffle(sequence)
        self.order = sequence

    def readCardsFromDB(self):
        self.cards = []
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, "DBs", "CARDDB.sqlite")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM CARDS")
        cursor.execute("SELECT id, name, description, year, month, day FROM cards")
        for row in cursor.fetchall():
            index, title, descr, y, m, d = row

            # Determine if this is an event or period based on index
            # (assuming first 75 are events as in your original code)
            card_type = "EVENT"
            # Create Card object using the data from the database
            card = Card(
                index=index,
                type=card_type,
                s_year=y,
                s_month=m,
                s_day=d,
                e_year=y,
                e_month=m,
                e_day=d,
                title=title,
                descr=descr
            )

            self.cards.append(card)

        # Close the database connection
        conn.close()
