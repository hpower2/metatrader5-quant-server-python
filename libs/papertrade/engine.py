from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel
from sqlalchemy import select

from libs.common.config import QuantSettings, get_settings
from libs.mt5_adapter import MT5ApiClient
from libs.storage.db import db_session
from libs.storage.models import PaperAccount, PaperFill, PaperPosition


class PaperSignal(Protocol):
    account_name: str
    symbol: str
    side: int
    quantity: float


class PaperOrderRequest(BaseModel):
    account_name: str
    symbol: str
    side: int
    quantity: float
    stop_loss: float | None = None
    take_profit: float | None = None


class ExecutionProvider(Protocol):
    def submit_signal(self, request: PaperOrderRequest) -> dict:
        ...

    def get_status(self, account_name: str) -> dict:
        ...


class PaperExecutionProvider:
    def __init__(self, settings: QuantSettings | None = None) -> None:
        self.settings = settings or get_settings()

    def submit_signal(self, request: PaperOrderRequest) -> dict:
        with MT5ApiClient(self.settings) as client, db_session() as session:
            tick = client.get_symbol_tick(request.symbol)
            account = self._get_or_create_account(session, request.account_name)
            open_positions = list(
                session.scalars(
                    select(PaperPosition).where(
                        PaperPosition.account_id == account.id,
                        PaperPosition.symbol == request.symbol,
                        PaperPosition.status == "open",
                    )
                )
            )

            for position in open_positions:
                if request.side == 0 or int(position.side) != request.side:
                    close_price = tick.bid if int(position.side) > 0 else tick.ask
                    pnl = (close_price - position.entry_price) * position.quantity * int(position.side)
                    position.current_price = close_price
                    position.realized_pnl += pnl
                    position.unrealized_pnl = 0.0
                    position.status = "closed"
                    position.closed_at = datetime.now(tz=UTC)
                    account.cash = Decimal(account.cash) + Decimal(pnl)
                    session.add(
                        PaperFill(
                            account_id=account.id,
                            position_id=position.id,
                            symbol=position.symbol,
                            side="close",
                            quantity=position.quantity,
                            price=close_price,
                            fees=0.0,
                            slippage_bps=self.settings.paper_default_slippage_bps,
                            event_time=datetime.now(tz=UTC),
                            fill_metadata={"reason": "signal_close"},
                        )
                    )

            if request.side != 0:
                open_price = tick.ask if request.side > 0 else tick.bid
                position = PaperPosition(
                    account_id=account.id,
                    symbol=request.symbol,
                    side=str(request.side),
                    quantity=request.quantity,
                    entry_price=open_price,
                    current_price=open_price,
                    stop_loss=request.stop_loss,
                    take_profit=request.take_profit,
                )
                session.add(position)
                session.flush()
                session.add(
                    PaperFill(
                        account_id=account.id,
                        position_id=position.id,
                        symbol=request.symbol,
                        side="open",
                        quantity=request.quantity,
                        price=open_price,
                        fees=0.0,
                        slippage_bps=self.settings.paper_default_slippage_bps,
                        event_time=datetime.now(tz=UTC),
                        fill_metadata={"reason": "signal_open"},
                    )
                )

            for position in session.scalars(
                select(PaperPosition).where(PaperPosition.account_id == account.id, PaperPosition.status == "open")
            ):
                market_price = tick.bid if int(position.side) > 0 else tick.ask
                position.current_price = market_price
                position.unrealized_pnl = (market_price - position.entry_price) * position.quantity * int(position.side)
                session.add(position)

            account.last_mark_to_market_at = datetime.now(tz=UTC)
            session.add(account)
            session.flush()
            return self._serialize_status(session, account)

    def get_status(self, account_name: str) -> dict:
        with MT5ApiClient(self.settings) as client, db_session() as session:
            account = self._get_or_create_account(session, account_name)
            positions = list(
                session.scalars(
                    select(PaperPosition).where(PaperPosition.account_id == account.id).order_by(PaperPosition.opened_at.desc())
                )
            )
            open_positions = [position for position in positions if position.status == "open"]
            for position in open_positions:
                tick = client.get_symbol_tick(position.symbol)
                market_price = tick.bid if int(position.side) > 0 else tick.ask
                position.current_price = market_price
                position.unrealized_pnl = (market_price - position.entry_price) * position.quantity * int(position.side)
                session.add(position)
            account.last_mark_to_market_at = datetime.now(tz=UTC)
            session.add(account)
            session.flush()
            return self._serialize_status(session, account)

    def _get_or_create_account(self, session, account_name: str) -> PaperAccount:
        account = session.scalar(select(PaperAccount).where(PaperAccount.name == account_name))
        if account is not None:
            return account
        account = PaperAccount(
            name=account_name,
            currency="USD",
            cash=Decimal(str(self.settings.paper_initial_cash)),
            equity=Decimal(str(self.settings.paper_initial_cash)),
        )
        session.add(account)
        session.flush()
        return account

    def _serialize_status(self, session, account: PaperAccount) -> dict:
        positions = list(
            session.scalars(
                select(PaperPosition).where(PaperPosition.account_id == account.id).order_by(PaperPosition.opened_at.desc())
            )
        )
        fills = list(
            session.scalars(
                select(PaperFill).where(PaperFill.account_id == account.id).order_by(PaperFill.event_time.desc()).limit(50)
            )
        )
        open_positions = [position for position in positions if position.status == "open"]
        account.equity = Decimal(account.cash) + Decimal(
            sum(position.realized_pnl + position.unrealized_pnl for position in open_positions)
        )
        session.add(account)
        return {
            "account": {
                "name": account.name,
                "currency": account.currency,
                "cash": float(account.cash),
                "equity": float(account.equity),
                "status": account.status,
                "last_mark_to_market_at": account.last_mark_to_market_at,
            },
            "open_positions": [
                {
                    "id": position.id,
                    "symbol": position.symbol,
                    "side": position.side,
                    "quantity": position.quantity,
                    "entry_price": position.entry_price,
                    "current_price": position.current_price,
                    "realized_pnl": position.realized_pnl,
                    "unrealized_pnl": position.unrealized_pnl,
                    "opened_at": position.opened_at,
                }
                for position in open_positions
            ],
            "recent_fills": [
                {
                    "id": fill.id,
                    "symbol": fill.symbol,
                    "side": fill.side,
                    "quantity": fill.quantity,
                    "price": fill.price,
                    "event_time": fill.event_time,
                }
                for fill in fills
            ],
        }
