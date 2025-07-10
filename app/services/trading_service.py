from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from app.models import Order, Trade, Position, OrderStatus, OrderSide
from app.schemas import OrderCreate, TradeCreate
from app.services.price_service import price_service
from app.models import Account

logger = logging.getLogger(__name__)


class TradingService:
    def __init__(self):
        pass
    
    async def execute_order(self, db: Session, order: Order) -> bool:
        """Execute an order and update positions"""
        try:
            # Get current price for the instrument
            instrument = order.instrument
            logger.info(f"Executing order {order.id} for {instrument.symbol}")
            
            price_data = await price_service.get_price(instrument.symbol, instrument.instrument_type.value)
            
            if not price_data:
                logger.error(f"Could not get price for {instrument.symbol}")
                order.status = OrderStatus.REJECTED
                db.commit()
                return False
            
            logger.info(f"Got price for {instrument.symbol}: bid={price_data.bid}, ask={price_data.ask}")
            
            # Determine execution price based on order type and side
            if order.order_type.value == "market":
                # Market orders execute at current market price
                if order.side == OrderSide.BUY:
                    execution_price = price_data.ask
                else:  # SELL
                    execution_price = price_data.bid
            else:
                # Limit orders execute at specified price if market allows
                if order.side == OrderSide.BUY and price_data.ask <= order.price:
                    execution_price = order.price
                elif order.side == OrderSide.SELL and price_data.bid >= order.price:
                    execution_price = order.price
                else:
                    # Price not met, order remains pending
                    return True
            
            # Calculate commission (simplified - could be more complex)
            commission = self._calculate_commission(order.quantity, execution_price)
            
            # Create trade record
            trade = Trade(
                order_id=order.id,
                account_id=order.account_id,
                instrument_id=order.instrument_id,
                side=order.side,
                quantity=order.quantity,
                price=execution_price,
                commission=commission,
                realized_pnl=0.0  # Will be calculated when position is closed
            )
            
            db.add(trade)
            
            # Update order status
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.average_fill_price = execution_price
            order.commission = commission
            
            # Update position
            await self._update_position(db, order.account_id, order.instrument_id, 
                                     order.side, order.quantity, execution_price)
            
            # Update account balance
            await self._update_account_balance(db, order.account_id, order.side, 
                                            order.quantity, execution_price, commission)
            
            logger.info(f"Order {order.id} execution completed successfully")
            
            db.commit()
            logger.info(f"Order {order.id} executed successfully at {execution_price}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing order {order.id}: {e}")
            db.rollback()
            order.status = OrderStatus.REJECTED
            db.commit()
            return False
    
    async def _update_position(self, db: Session, account_id: int, instrument_id: int, 
                             side: OrderSide, quantity: float, price: float):
        """Update position after trade execution"""
        # Get or create position
        position = db.query(Position).filter(
            Position.account_id == account_id,
            Position.instrument_id == instrument_id
        ).first()
        
        if not position:
            position = Position(
                account_id=account_id,
                instrument_id=instrument_id,
                quantity=0.0,
                average_price=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0
            )
            db.add(position)
        
        # Calculate new position
        if side == OrderSide.BUY:
            # Buying increases position
            if position.quantity >= 0:
                # Long position or no position
                total_cost = (position.quantity * position.average_price) + (quantity * price)
                position.quantity += quantity
                position.average_price = total_cost / position.quantity if position.quantity > 0 else 0
            else:
                # Short position - closing short
                if abs(position.quantity) <= quantity:
                    # Fully closing short position
                    realized_pnl = (position.average_price - price) * abs(position.quantity)
                    position.realized_pnl += realized_pnl
                    position.quantity += quantity
                    if position.quantity > 0:
                        position.average_price = price
                    else:
                        position.average_price = 0
                else:
                    # Partially closing short position
                    realized_pnl = (position.average_price - price) * quantity
                    position.realized_pnl += realized_pnl
                    position.quantity += quantity
        else:  # SELL
            # Selling decreases position
            if position.quantity <= 0:
                # Short position or no position
                total_cost = (abs(position.quantity) * position.average_price) + (quantity * price)
                position.quantity -= quantity
                position.average_price = total_cost / abs(position.quantity) if position.quantity < 0 else 0
            else:
                # Long position - closing long
                if position.quantity <= quantity:
                    # Fully closing long position
                    realized_pnl = (price - position.average_price) * position.quantity
                    position.realized_pnl += realized_pnl
                    position.quantity -= quantity
                    if position.quantity < 0:
                        position.average_price = price
                    else:
                        position.average_price = 0
                else:
                    # Partially closing long position
                    realized_pnl = (price - position.average_price) * quantity
                    position.realized_pnl += realized_pnl
                    position.quantity -= quantity
        
        # Update unrealized P&L (simplified - would need current price)
        position.unrealized_pnl = 0.0  # Will be updated when price is fetched
    
    async def _update_account_balance(self, db: Session, account_id: int, side: OrderSide, 
                                    quantity: float, price: float, commission: float):
        """Update account balance after trade execution"""
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return
        
        trade_value = quantity * price
        total_cost = trade_value + commission
        
        if side == OrderSide.BUY:
            # Buying reduces balance
            account.balance -= total_cost
        else:  # SELL
            # Selling increases balance
            account.balance += (trade_value - commission)
    
    def _calculate_commission(self, quantity: float, price: float) -> float:
        """Calculate commission for trade (simplified)"""
        # Simple commission model - could be more complex
        trade_value = quantity * price
        commission_rate = 0.001  # 0.1% commission
        return trade_value * commission_rate
    
    async def update_position_pnl(self, db: Session, position: Position):
        """Update unrealized P&L for a position"""
        try:
            # Get current price
            instrument = position.instrument
            price_data = await price_service.get_price(instrument.symbol, instrument.instrument_type.value)
            
            if not price_data:
                return
            
            # Calculate unrealized P&L
            if position.quantity > 0:  # Long position
                current_value = position.quantity * price_data.bid
                cost_basis = position.quantity * position.average_price
                position.unrealized_pnl = current_value - cost_basis
            elif position.quantity < 0:  # Short position
                current_value = abs(position.quantity) * price_data.ask
                cost_basis = abs(position.quantity) * position.average_price
                position.unrealized_pnl = cost_basis - current_value
            else:
                position.unrealized_pnl = 0.0
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating P&L for position {position.id}: {e}")
            db.rollback()


# Global trading service instance
trading_service = TradingService() 