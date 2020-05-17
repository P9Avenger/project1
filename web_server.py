from flask import Flask, request, render_template, redirect
import sys
import random
from pony.orm import *

db = Database()


class Product(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    description = Optional(str)
    specifications = Set('Specification')
    manufacturer = Optional('Manufacturer')
    category = Optional('Category')


class Specification(db.Entity):
    id = PrimaryKey(int, auto=True)
    product = Required(Product)
    name = Required(str)
    value = Optional(str)
    description = Optional(str)


class Manufacturer(db.Entity):
    id = PrimaryKey(int, auto=True)
    products = Set(Product)
    name = Required(str)
    description = Optional(str)


class Category(db.Entity):
    id = PrimaryKey(int, auto=True)
    products = Set(Product)
    name = Optional(str)
    description = Optional(str)


db.bind(provider='sqlite', filename="database.db")
db.generate_mapping()


app = Flask(__name__)


@app.route("/")
@app.route("/index")
def index():
    return render_template("main.html")


@app.route("/product_list")
def product_list():
    with db_session:
        lst = list(select((i.id,
                           i.name,
                           i.category.name,
                           i.manufacturer.name,
                           i.description,
                           f"http://localhost:8080/delete/product/{i.id}")
                          for i in Product))

    return render_template("universal_list.html", items=lst,
                           tableheaders=("ID",
                                         "Name",
                                         "Category",
                                         "Manufacturer",
                                         "Description"))


@app.route("/manufacturer_list")
def manufacturer_list():
    with db_session:
        lst = list(select((i.id,
                           i.name,
                           i.description,
                           f"http://localhost:8080/delete/manufacturer/{i.id}")
                          for i in Manufacturer))
    return render_template("universal_list.html", items=lst,
                           tableheaders=("ID",
                                         "Name",
                                         "Description"))


@app.route("/category_list")
def category_list():
    with db_session:
        lst = list(select((i.id,
                           i.name,
                           i.description,
                           f"http://localhost:8080/delete/category/{i.id}") for i in Category))
    return render_template("universal_list.html", items=lst,
                           tableheaders=("ID",
                                         "Name",
                                         "Description"))


@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "GET":
        with db_session:
            manufacturers = list(select(m.name for m in Manufacturer))
            categories = list(select(c.name for c in Category))
        return render_template("product_addition.html",
                               manufacturers=manufacturers,
                               categories=categories)

    elif request.method == "POST":
        id = request.form["ID"]
        name = request.form["name"]
        mname = request.form["manufacturer"]
        cname = request.form["category"]
        description = request.form["description"]

        with db_session:
            pids = select(p.id for p in Product)

            if not id:
                id = 0
            else:
                id = int(id)

            if pids:
                baseid = max(pids)

            if id not in pids:
                pass
            else:
                id = baseid + 1

            cid = select(c.id
                         for c in Category
                         if c.name ==
                         cname).first()

            mid = select(m.id
                         for m in Manufacturer
                         if m.name ==
                         mname).first()

            p = Product(id=id,
                        name=name,
                        category=cid,
                        manufacturer=mid,
                        description=description)
            commit()

        with db_session:
            manufacturers = list(select(m.name for m in Manufacturer))
            categories = list(select(c.name for c in Category))
        return render_template("product_addition.html",
                               manufacturers=manufacturers,
                               categories=categories)


@app.route("/add_manufacturer", methods=["GET", "POST"])
def add_manufacturer():
    if request.method == "GET":
        return render_template("manufacturer_addition.html")

    elif request.method == "POST":
        id = request.form["ID"]
        name = request.form["name"]
        description = request.form["description"]

        with db_session:
            mids = select(m.id for m in Manufacturer)

            if not id:
                id = 0
            else:
                id = int(id)

            if mids:
                baseid = max(mids)

            if id not in mids:
                pass
            else:
                id = baseid + 1

            m = Manufacturer(id=id,
                             name=name,
                             description=description)
            commit()

    return render_template("manufacturer_addition.html")


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "GET":
        return render_template("category_addition.html")

    elif request.method == "POST":
        id = request.form["ID"]
        name = request.form["name"]
        description = request.form["description"]

        with db_session:
            cids = select(c.id for c in Category)

            if not id:
                id = 0
            else:
                id = int(id)

            if cids:
                baseid = max(cids)

            if id not in cids:
                pass
            else:
                id = baseid + 1

            c = Category(id=id,
                         name=name,
                         description=description)
            commit()

    return render_template("category_addition.html")


@app.route("/delete/<type>/<id>")
def delete(type, id):
    id = int(id)
    with db_session:
        if type == "product":
            id_l = list(select(p.id for p in Product))
            if len(id_l) > 0 and (id in id_l):
                Product[id].delete()
            return redirect("/product_list")

        elif type == "manufacturer":
            id = min(list(select(m for m in Product if m.id == id)))
            id_l = list(select(m.id for m in Manufacturer))
            if len(id_l) > 0 and (id in id_l):
                Manufacturer[id].delete()
            return redirect("/manufacturer_list")

        elif type == "category":
            id = min(list(select(c for c in Category if c.id == id)))
            id_l = list(select(c.id for c in Category))
            if len(id_l) > 0 and (id in id_l):
                Category[id].delete()
            return redirect("/category_list")



if __name__ == '__main__':
    app.run(port=8080, host='localhost')
