# !/usr/bin/env python3.7
# -*- coding: utf-8 -*-
import logging
import os
import time

from flask import Flask
from flask_restplus import Api, Resource, fields, reqparse, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from waitress import serve

app = Flask(__name__)
api = Api(app, doc='/ui', version='1.0', title='Some store API', default="api")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTPLUS_MASK_SWAGGER'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URI")

db = SQLAlchemy(app)

ROOT = "/api/v1"

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    category = db.Column(db.Text)

model = api.model('Product', {
    'id': fields.Integer(readOnly=True),
    'name': fields.String,
    'category': fields.String,
})

productParser = reqparse.RequestParser()
productParser.add_argument('name')
productParser.add_argument('category')

paginationParser = reqparse.RequestParser()
paginationParser.add_argument('page', type=int)
paginationParser.add_argument('per_page', type=int, default=20)


queryParser = reqparse.RequestParser()
queryParser.add_argument('query', help="query for full-text search in labels + categories")
queryParser.add_argument('category', help="limit search to single category")

@api.route(ROOT + '/product/<int:id>')
class ProductEntry(Resource):

    @api.marshal_with(model)
    @api.response(404, 'Product not found.')
    def get(self, id):
        """Returns details of a product."""
        log.info("Requested id=" + str(id))
        data = Product.query.filter(Product.id == id).first()
        if data is None:
            abort(404, message="Product with id=%d not found" % id)
        return data

    @api.expect(productParser, validate=True)
    @api.response(204, 'Product successfully updated.')
    def put(self, id):
        """Updates a product."""
        args = productParser.parse_args()
        product = Product()
        product.id = id
        product.category = args.get('category')
        product.name = args.get('name')
        log.info("Updated id=" + str(id) + " with " + str(args))
        db.session.merge(product)
        db.session.commit()
        return None, 204

    @api.response(204, 'Product successfully deleted.')
    @api.response(404, 'Product not found.')
    def delete(self, id):
        """Deletes product."""
        d = db.session.query(Product).filter(Product.id == id).delete()
        if d == 0:
            log.info("Failed attempt to delete id=" + str(id))
            abort(404, message="Product with id=%d not found" % id)
        log.info("Deleted id=" + str(id))
        db.session.commit()
        return None, 204

    @api.response(201, 'Product successfully created.')
    @api.response(409, 'Id is already taken.')
    @api.expect(productParser, validate=True)
    def post(self, id):
        """Create new product."""
        d = db.session.query(Product).filter(Product.id == id).first()
        if d is not None:
            abort(409, message="Product with id=%d already exists" % id)

        args = productParser.parse_args()
        product = Product()
        product.id = id
        product.category = args.get('category')
        product.name = args.get('name')
        log.info("Created id=" + str(id) + " with " + str(args))
        db.session.add(product)
        db.session.commit()
        return None, 201


@api.route(ROOT + '/products/list')
class ListCategories(Resource):

    @api.expect(paginationParser, queryParser)
    @api.header('X-Total', 'Total count of entries matching filters', type=[int])
    @api.marshal_list_with(model)
    def get(self):
        """Discover products."""
        searchArgs = queryParser.parse_args()
        query = Product.query.order_by(Product.name, Product.id)
        if searchArgs.get('query') is not None:
            query = query.filter(func.to_tsvector(Product.name).match(searchArgs.get('query')))
        if searchArgs.get('category') is not None:
            query = query.filter(Product.category == searchArgs.get('category'))
        pagination = paginationParser.parse_args()
        if pagination.get('page') is not None:
            if pagination['page'] < 1 or pagination['per_page'] < 1:
                abort(400, "Wrong pagination params")
            p = query.paginate(pagination['page'], pagination['per_page'])
            total = p.total
            data = p.items
            log.info("Requested list " + str(searchArgs) + ", " + str(pagination) + " %d of %d items returned" % (len(data), total))
            return data, 200, {'X-Total': total}
        else:
            data = query.all()
            log.info("Requested list " + str(searchArgs) + ", %d items returned" % len(data))
            return data


@api.route(ROOT + '/ping')
class ListCategories(Resource):
    def get(self):
        """Health check."""
        return "pong"

# TO DELETE

deleteProdParser = reqparse.RequestParser()
deleteProdParser.add_argument("login")
deleteProdParser.add_argument("password")

@app.route(ROOT + '/delete_prod')
class ListCategories(Resource):
    def get(self):
        """Clears production database"""
        args = deleteProdParser.parse_args()
        if args.get("login", "") == "root" and args.get("password", "") == "pass":
            db.drop_all()
            return 202
        return 401


if __name__ == '__main__':
    start = time.time()
    while True:
        try:
            db.create_all(app=app)
            break
        except Exception as e:
            if time.time() - start > 10:
                raise Exception("DB is not avaliable for 10s. Aborting.")
    serve(app, host="0.0.0.0", port=80, threads=16)
