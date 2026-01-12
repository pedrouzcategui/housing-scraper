from db import Database
from logging_utils import logger

class Property:
    def __init__(self, mercadolibre_listing_id, title, p_type, price, listing_type, description, area, rooms, bathrooms, id=None):
        self.id = id
        self.mercadolibre_listing_id = mercadolibre_listing_id
        self.title = title
        self.p_type = p_type
        self.price = price
        self.listing_type = listing_type
        self.description = description
        self.area = area
        self.rooms = rooms
        self.bathrooms = bathrooms

    def save(self):
        """Inserts the current property object into the database."""
        sql = """
            INSERT INTO properties (mercadolibre_listing_id, title, type, price, listing_type, description, area, rooms, bathrooms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            self.mercadolibre_listing_id, self.title, self.p_type, self.price, self.listing_type,
            self.description, self.area, self.rooms, self.bathrooms
        )
        try:
            Database.execute_query(sql, params)
            logger.info("Property '%s' saved successfully", self.title)
        except Exception:
            logger.exception(
                "Failed to save property %s", self.mercadolibre_listing_id
            )
            raise

    @staticmethod
    def get_all():
        """Fetches all properties and returns them as Property objects."""
        try:
            rows = Database.execute_query("SELECT * FROM properties")
        except Exception:
            logger.exception("Failed to fetch properties")
            raise
        return [Property(*row[1:], id=row[0]) for row in rows]