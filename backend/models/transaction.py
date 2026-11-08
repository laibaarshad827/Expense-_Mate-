from dataclasses import dataclass
from typing import Optional


@dataclass
class Transaction:
    transaction_id: int
    user_id: int
    type: str
    amount: float
    category: str
    transaction_date: str
    note: Optional[str]

    @staticmethod
    def from_row(row) -> "Transaction":
        return Transaction(
            transaction_id=row["transaction_id"], user_id=row["user_id"], type=row["type"],
            amount=row["amount"], category=row["category"],
            transaction_date=row["transaction_date"], note=row["note"],
        )

    def to_record(self) -> dict:
        """The dict shape the screens expect (id/date instead of the DB column names)."""
        return {
            "id": self.transaction_id, "type": self.type, "amount": self.amount,
            "category": self.category, "date": self.transaction_date, "note": self.note,
        }