from app.models.payments import Payment
from app.extensions import db


class PaymentRepository:

    @staticmethod
    def create(order_id, payment_reference, amount, expires_at):
        payment = Payment(
            order_id=order_id,
            payment_reference=payment_reference,
            amount=amount,
            status='pending',
            expires_at=expires_at,
        )
        db.session.add(payment)
        db.session.commit()
        return payment

    @staticmethod
    def get_by_reference(payment_reference):
        return Payment.query.filter_by(
            payment_reference=payment_reference
        ).first()

    @staticmethod
    def get_by_id(payment_id):
        return Payment.query.filter_by(id=payment_id).first()

    @staticmethod
    def get_latest_for_order(order_id):
        return (
            Payment.query
            .filter_by(order_id=order_id)
            .order_by(Payment.id.desc())
            .first()
        )

    @staticmethod
    def update_from_notification(payment, new_status, payment_method=None,
                                 transaction_time=None, settlement_time=None,
                                 raw_response=None, commit=True):
        payment.status = new_status

        if payment_method is not None:
            payment.payment_method = payment_method
        if transaction_time is not None:
            payment.transaction_time = transaction_time
        if settlement_time is not None:
            payment.settlement_time = settlement_time
        if raw_response is not None:
            payment.raw_response = raw_response

        if commit:
            db.session.commit()
        return payment
