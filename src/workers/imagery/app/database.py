import os
from typing import List, Any

import sqlalchemy
from sqlalchemy import create_engine, and_

DATABASE_URL = os.environ["DATABASE_URL"]

metadata = sqlalchemy.MetaData()
Products = sqlalchemy.Table(
    "products",
    metadata,
    sqlalchemy.Column("image_id", sqlalchemy.String),
    sqlalchemy.Column("gender", sqlalchemy.String),
    sqlalchemy.Column("master_category", sqlalchemy.String),
    sqlalchemy.Column("sub_category", sqlalchemy.String),
    sqlalchemy.Column("article_type", sqlalchemy.String),
    sqlalchemy.Column("base_colour", sqlalchemy.String),
    sqlalchemy.Column("season", sqlalchemy.String),
    sqlalchemy.Column("year", sqlalchemy.Integer),
    sqlalchemy.Column("usage", sqlalchemy.String),
    sqlalchemy.Column("display_name", sqlalchemy.String),
)
engine = create_engine(DATABASE_URL)

def filter_products(data_dict: dict) -> List[Any]:
    """
    TODO: run sql query here
    """
    
    with engine.begin() as connection:
        query = Products.select().where(
            and_(Products.c.gender == data_dict["gender"],
            Products.c.sub_category == data_dict["sub_category"],
            Products.c.year >= data_dict["start_year"])
        ).order_by(Products.c.year).limit(data_dict["limit"])

        products = connection.execute(query)

    return [dict(row) for row in products]
