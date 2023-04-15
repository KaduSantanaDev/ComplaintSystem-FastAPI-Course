from db import database
from models import complaint, RoleType, State, transaction
from services.wise import WiseService

wise = WiseService()
class ComplaintManager:
    @staticmethod
    async def get_complaints(user):
        q = complaint.select()
        if user["role"] == RoleType.complainer:
            q = q.where(complaint.c.complainer_id == user["id"])
        elif user["role"] == RoleType.approver:
            q = q.where(complaint.c.state == State.pending)
        return await database.fetch_all(q)


    @staticmethod
    async def create_complaint(complaint_data, user):
        complaint_data["complainer_id"] = user["id"]
        async with database.transaction() as tconn:
            id_ = await tconn._connection.execute(complaint.insert().values(**complaint_data))
            await ComplaintManager.issue_transaction(tconn, complaint_data["amount"], f"{user['first_name']} {user['last_name']}", user["iban"], id_)
        return await database.fetch_one(complaint.select().where(complaint.c.id == id_))


    @staticmethod
    async def delete_complaint(complaint_id):
        await database.execute(complaint.delete().where(complaint.c.id == complaint_id))


    @staticmethod
    async def approve(complaint_id):
        await database.execute(complaint.update().where(complaint.c.id == complaint_id).values(status=State.approved))


    @staticmethod
    async def reject(id_):
        transaction_data = await database.fetch_one(transaction.select().where(transaction.c.complaint_id == id_))
        wise.cancel_funds(transaction_data["transfer_id"])
        await database.execute(
            complaint.update()
            .where(complaint.c.id == id_)
            .values(status=State.rejected)
        )


    @staticmethod
    async def issue_transaction(tconn, amount, full_name, iban, complaint_id):
        quote_id = wise.create_quote(amount)
        recipient_id = wise.create_recipient_account(full_name, iban)
        transfer_id = wise.create_transfer(recipient_id, quote_id)
        data = {
            "quote_id": quote_id,
            "transfer_id": transfer_id,
            "target_account_id": str(recipient_id),
            "amount": amount,
            "complaint_id": complaint_id
        }
        await tconn._connection.execute(transaction.insert().values(**data))