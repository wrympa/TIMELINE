from functools import total_ordering

from pydantic import BaseModel


@total_ordering
class Card(BaseModel):
    index: int = 0
    type: str = "EVENT"
    s_year: int = 0
    s_month: int = 1
    s_day: int = 1
    e_year: int = 0
    e_month: int = 1
    e_day: int = 1
    title: str = ""
    descr: str = ""

    def __lt__(self, other: "Card") -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        if self.e_year != other.s_year:
            return self.e_year < other.s_year
        if self.e_month != other.s_month:
            return self.e_month < other.s_month
        if self.e_day != other.s_day:
            return self.e_day < other.s_day
        return True

    def __le__(self, other: "Card") -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self < other or self == other

    def __eq__(self, other: "Card") -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return (self.e_year == other.s_year and
                self.e_month == other.s_month and
                self.e_day == other.s_day)

    def __gt__(self, other: "Card") -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return not (self < other or self == other)

    def __ge__(self, other: "Card") -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self > other or self == other
