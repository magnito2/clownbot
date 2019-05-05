from flask_restful import Resource, abort, fields, reqparse
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import Order
from .. import  user_datastore

parser = reqparse.RequestParser()
parser.add_argument("start_id")
parser.add_argument("end_id")
parser.add_argument("side")
parser.add_argument("start_date", help="This field cannot be empty", required=True)
parser.add_argument("end_date", help="This field cannot be empty", required=True)
parser.add_argument("id")

class OrdersAPI(Resource):

    orders_fields = {
        "id" : fields.Integer(),
        "start_id": fields.Integer(),
        "end_id": fields.Integer(),
        "side": fields.String(),
        "start_date": fields.DateTime(),
        "end_date": fields.DateTime(),
    }
    @jwt_required
    def get(self, order_id = None):
        email = get_jwt_identity()
        user = user_datastore.get_user(email)
        if not user:
            abort(401, message=f"No user found for email {email}")
        if order_id:
            order = Order.query.get(order_id)
            if not Order or not order in user.orders:
                abort(404)
            return order.serialize()
        orders = [order.serialize() for order in user.orders]
        return orders