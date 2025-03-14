import os
import random
import sqlite3
from collections import defaultdict
from itertools import permutations
from typing import List

from models.Card import Card


class CardDAO:
    def __init__(self):
        sequence = list(range(196))
        random.shuffle(sequence)
        self.order: List[int] = sequence
        print(self.order)
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
            print(i)
            result.append(self.cards[i])
        return result

    def getHands(self, players: List[str]) -> dict[str, List[Card]]:
        result: dict[str, List[Card]] = defaultdict(list)
        for i in range(len(players)):
            for j in range(self.handSize):
                print(self.order[self.pileSize + (self.handSize * i) + j])
                result[players[i]].append(self.cards[self.order[self.pileSize + (self.handSize * i) + j]])
        return dict(result)

    def setOrder(self):
        sequence = list(range(196))
        random.shuffle(sequence)
        self.order = sequence

    def readCardsFromDB(self):
        self.cards = []
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, "DBs", "CARDDB.sqlite")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM CARDS")
        cursor.execute("SELECT id, name, description, year, month, day, TYPE, END_YEAR, END_MONTH, END_DAY FROM cards")
        for row in cursor.fetchall():
            index, title, descr, s_y, s_m, s_d, eventType, e_y, e_m, e_d = row

            # Determine if this is an event or period based on index
            # (assuming first 75 are events as in your original code)
            # Create Card object using the data from the database
            card = Card(
                index=index,
                type=eventType,
                s_year=s_y,
                s_month=s_m,
                s_day=s_d,
                e_year=e_y if e_y is not None else s_y,
                e_month=e_m if e_m is not None else s_m,
                e_day=e_d if e_d is not None else s_d,
                title=title,
                descr=descr
            )

            self.cards.append(card)

        # Close the database connection
        conn.close()
