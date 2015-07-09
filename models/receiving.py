# encoding: utf-8
from decimal import Decimal
from app_provider import AppInfo
from models.util import format_decimal
from models.enum_values import EnumValues
from sqlalchemy import Column, Integer, ForeignKey, Numeric, Text, DateTime, select, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship

db = AppInfo.get_db()


class Receiving(db.Model):
    __tablename__ = 'receiving'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    remark = Column(Text)

    status_id = Column(Integer, ForeignKey('enum_values.id'), nullable=False)
    status = relationship('EnumValues', foreign_keys=[status_id])

    purchase_order_id = Column(Integer, ForeignKey('purchase_order.id'), nullable=False)
    purchase_order = relationship('PurchaseOrder', backref=backref('inventory_transactions',
                                                                   uselist=True, cascade='all, delete-orphan'))

    @staticmethod
    def status_filter():
        return EnumValues.type_filter('RECEIVING_STATUS')

    @hybrid_property
    def transient_po(self):
        """
        This design is to display a readonly field containing current
        Purchase order information in UI but don't allow user to change it.
        :return: Current purchase order instance as a transient property
        """
        return self.purchase_order

    @transient_po.setter
    def transient_po(self, val):
        pass

    @hybrid_property
    def total_amount(self):
        return format_decimal(Decimal(sum(line.total_amount for line in self.lines)))

    @total_amount.expression
    def total_amount(self):
        return (select([func.sum(ReceivingLine.price * ReceivingLine.quantity)])
                .where(self.id == ReceivingLine.receiving_id).label('total_amount'))

    @total_amount.setter
    def total_amount(self, value):
        pass

    @staticmethod
    def filter_by_po_id(po_id):
        return AppInfo.get_db().session.query(Receiving).filter_by(purchase_order_id=po_id).all()

class ReceivingLine(db.Model):
    __tablename = 'receiving_line'
    id = Column(Integer, primary_key=True)
    quantity = Column(Numeric(precision=8, scale=2, decimal_return_scale=2), nullable=False)
    price = Column(Numeric(precision=8, scale=2, decimal_return_scale=2), nullable=False)

    receiving_id = Column(Integer, ForeignKey('receiving.id'), nullable=False)
    receiving = relationship('Receiving', backref=backref('lines', uselist=True, cascade='all, delete-orphan'))

    purchase_order_line_id = Column(Integer, ForeignKey('purchase_order_line.id'), nullable=False)
    purchase_order_line = relationship('PurchaseOrderLine',
                                       backref=backref('inventory_transaction_lines',
                                                       uselist=True, cascade='all, delete-orphan'))

    @hybrid_property
    def product(self):
        return self.purchase_order_line.product

    @product.setter
    def product(self, value):
        pass

    @product.expression
    def product(self):
        return select(self.purchase_order_line.product).label('product_id')

    @hybrid_property
    def total_amount(self):
        if self.quantity is None:
            q = 0
        else:
            q = self.quantity
        return format_decimal(Decimal(self.price * q))

    @total_amount.expression
    def total_amount(self):
        return select([self.price * self.quantity]).label('line_total_amount')

    @total_amount.setter
    def total_amount(self, value):
        pass
