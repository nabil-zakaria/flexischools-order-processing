import boto3
import logging
import psycopg2
from psycopg2 import sql

logger = logging.getLogger()
logging.basicConfig()
logger.setLevel(logging.INFO)


class RDS:
    def __init__(self, db_config: dict):
        self.rds = boto3.client("rds")
        self._db_config = db_config
        self._connection = self._connect_to_rds()

    def _connect_to_rds(self) -> psycopg2.extensions.connection:
        """Connects to the RDS DB

        Returns:
            psycopg2.extensions.connection: The connection
        """
        connection = psycopg2.connect(
            dbname=self._db_config["db_name"],
            user=self._db_config["db_user"],
            password=self._db_config["db_password"],
            host=self._db_config["db_host"],
            port=self._db_config.get("db_port", 5500),
        )
        logger.info("Connected to RDS PostgreSQL database successfully!")
        return connection

    def confirm_table_exists(self, table_name: str) -> bool:
        """Confirms whether the table with table_name exists

        Args:
            table_name (str): Name of the table to confirm

        Returns:
            dict: True if the table exists, False otherwise
        """
        try:
            with self._connection.cursor() as cursor:
                query = sql.SQL("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = {}
                    );
                """).format(sql.Literal(table_name))

                cursor.execute(query)
                exists = cursor.fetchone()[0]
                return exists
        except Exception as e:
            logger.exception(f"Error checking table existence: {repr(e)}")
            return False

    def create_table(self, table_name: str) -> bool:
        """Creates the table with specified table_name

        Args:
            table_name (str): Name of the table to create

        Returns:
            dict: True if the table was created, False otherwise
        """
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("""
                    CREATE TABLE {} (
                        order_id SERIAL PRIMARY KEY,
                        order_details TEXT NOT NULL
                    );
                """).format(sql.Identifier(table_name))
                )
                self._connection.commit()
                logger.info(f"Table '{table_name}' created successfully.")
                return True
        except Exception as e:
            logger.exception(f"Error creating table '{table_name}': {repr(e)}")
            return False

    def write_to_table(self, table_name: str, column_name: str, value: str) -> bool:
        """Writes the value of order_details into the table

        Args:
            table_name (str): Name of the table to write the value into
            column_name (str): Name of the column to write the value into
            value (str): the value to write into the table

        Returns:
            dict: True if the value was written into the table, False otherwise
        """
        try:
            with self._connection.cursor() as cursor:
                query = sql.SQL("""
                    INSERT INTO {} ({}) 
                    VALUES ({});
                """).format(
                    sql.Identifier(table_name),
                    sql.Identifier(column_name),
                    sql.Placeholder()
                )

                cursor.execute(query, (value,))
                self._connection.commit()
                logger.info(f"Inserted into table: {table_name}, the value: {value}!")
        except Exception as e:
            logger.exception(f"Error occured writing to table: {repr(e)}")
