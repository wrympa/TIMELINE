import os
import sys
from copy import copy
from typing import List, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'service')))
from Card import Card
from GameState import GameState
from CardDAO import CardDAO


class GameService:

    def __init__(self, players: List[str]):
        self.over = False
        self.players = players
        self.currentTurn = 0
        self.deck: List[Card] = []
        self.cardDAO = CardDAO()
        self.pile: List[Card] = self.cardDAO.getPile()
        self.hands: dict[str, List[Card]] = self.cardDAO.getHands(self.players)
        self.points: dict[str, int] = {}
        for player in self.players:
            self.points[player] = 0
        self.gameProcessString = ""

    def playEventCard(self, card: Card, index: int):
        print(f"placing at {index}")
        lCard = None
        rCard = None
        print(0, index - 1, len(self.deck))
        if 0 <= (index - 1) < len(self.deck):
            lCard = self.deck[index - 1]
        print(0, index, len(self.deck))
        if 0 <= index < len(self.deck):
            rCard = self.deck[index]

        if lCard is None and rCard is None:
            self.deck.insert(index, card)
            return 100
        elif lCard is not None and rCard is not None:
            if lCard <= card <= rCard:
                self.deck.insert(index, card)
                return 100
        elif lCard is None:
            if card <= rCard:
                self.deck.insert(index, card)
                return 100
        elif rCard is None:
            if lCard <= card:
                self.deck.insert(index, card)
                return 100

        print("ADDING CORRECT WAY")
        new_index = 0
        curr_card = self.deck[new_index]
        while card >= curr_card:
            new_index += 1
            if new_index >= len(self.deck):
                break
            curr_card = self.deck[new_index]
        print("TRUE INDEX", new_index)
        self.deck.insert(new_index, card)
        print("ADDED")
        return -100

    def playPeriodCard(self, card: Card, indexes: List[int]):
        lCard = copy(card)
        rCard = copy(card)
        return self.playEventCard(lCard, indexes[0]) + self.playEventCard(rCard, indexes[1])

    def removeCardFromHand(self, player: str, cardToRemove: Card):
        if player in self.hands:
            try:
                self.hands[player].remove(cardToRemove)
                print(f"Card {cardToRemove} removed from {player}'s hand.")
            except ValueError:
                print(f"Card {cardToRemove} not found in {player}'s hand.")
        else:
            print(f"Player {player} not found.")

    def playCard(self, card: Card, index: List[int]):
        print(card, index)
        self.removeCardFromHand(self.players[self.currentTurn], card)

        if len(self.hands[self.players[self.currentTurn]]) == 0 and len(self.pile) == 0:
            self.over = True

        if len(self.pile) > 0:
            self.hands[self.players[self.currentTurn]].append(self.pile.pop())
        if len(index) == 1:
            print("PLAY AS EVENT")
            return self.playEventCard(card, index[0])
        else:
            print("PLAY AS PERIOD")
            return self.playPeriodCard(card, index)

    def writePoints(self, points: int):
        self.points[self.players[self.currentTurn]] += points

    def resetService(self):
        self.currentTurn = 0
        self.deck = []
        self.pile = []
        self.hands = {}
        self.points = {}
        self.players = []
        self.gameProcessString = ""
        self.cardDAO.setOrder()
        self.over = False

    def getGameState(self) -> GameState:
        currState = GameState(
            deck=[card.index for card in self.deck],
            points=self.points,
            currentTurn=self.players[self.currentTurn],
            hands={player: [card.index for card in cards] for player, cards in self.hands.items()},
            over=self.over,
            pileSize=len(self.pile)
        )
        return currState

    def advance(self):
        print(f"WAS {self.currentTurn}")
        self.currentTurn = (self.currentTurn + 1) % len(self.players)
        print(f"NOW {self.currentTurn}")

    def getCurrentTurnPlayer(self) -> str:
        return self.players[self.currentTurn]

    def processMove(self, player_id, data: dict[str:Any]):
        card = self.hands[player_id][data["cardIndex"]]
        points = self.playCard(card, data["cardPlaces"])
        self.points[player_id] += points
