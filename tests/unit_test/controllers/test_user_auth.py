"""Test for /user API."""

import json
import unittest
from unittest import mock


class MockUpdateQuery:
    """Mock class for query returned from 'update_query' function."""

    return_map_model = True

    @classmethod
    def order_by(cls, *args):
        """Mock method for order_by()."""
        return MockUpdateQuery

    @classmethod
    def count(cls):
        """Mock method for count()."""
        return 1

    @classmethod
    def limit(cls, *args):
        """Mock method for limit()."""
        return MockUpdateQuery

    @classmethod
    def offset(cls, *args):
        """Mock method for offset()."""
        return MockUpdateQuery

    @classmethod
    def with_entities(cls, *args):
        """Mock method for with_entities()."""
        MockWithEntities.return_map = True
        return MockAll


def mock_update_query(*args, **kwargs):
    """Mock function for 'update_query' function."""
    filters = kwargs["filters"]
    flag = False
    for key in filters:
        if not hasattr(MockMap, key):
            raise Exception("Invalid key sent for filtering")
        attr_value = getattr(MockMap, key)
        if str(attr_value) != str(filters[key]):
            flag = True
    if flag:
        MockUpdateQuery.return_map_model = False
        return True, MockUpdateQuery
    else:
        MockUpdateQuery.return_map_model = True
        return True, MockUpdateQuery


class MockAll:
    """Mock class for query.with_entities().all()."""

    @classmethod
    def all(cls):
        """Mock function to evaluate the query."""
        if MockWithEntities.return_map:
            return []
        if MockWithEntities.return_waypoint:
            return []


class MockFirst:
    """Mock class for query first attribute."""

    return_none = True
    return_map = False
    return_map_image = False
    return_map_image_value = None

    @classmethod
    def first(cls):
        """Mock method to evaluate the query."""
        if MockFirst.return_none:
            MockFirst.return_none = False
            return None
        if MockFirst.return_map:
            return MockMap
        if MockFirst.return_map_image:
            return [MockFirst.return_map_image_value]


class MockMapQuery:
    """Mock class for map query statements."""

    @classmethod
    def filter(cls, *args):
        """Mock function for query.filter()."""
        if args[0] is True:
            MockFirst.return_none = False
            MockFirst.return_map = True
        if args[0] is False:
            MockFirst.return_none = True
        return MockFirst

    @classmethod
    def filter_by(cls, *args, **kwargs):
        """Mock function for query.filter_by()."""
        if kwargs["map_id"] == MockMap.map_id:
            MockFirst.return_none = False
            MockWithEntities.return_map_image = True
            return MockWithEntities
        else:
            raise Exception


class MockWaypointQuery:
    """Mock class for waypoint query statements."""

    @classmethod
    def filter(cls, *args):
        """Mock function for query.filter()."""
        if args[0] is True:
            MockFirst.return_none = False
            MockWithEntities.return_waypoint = True
            return MockWithEntities
        if args[0] is False:
            MockFirst.return_none = True
        return MockWithEntities


class MockWithEntities:
    """Mock class with entities."""

    return_waypoint = False
    return_map = False
    return_map_image = False
    return_none = False

    @classmethod
    def with_entities(cls, *args):
        """Mock function for filter_by().with_entities()."""
        if MockWithEntities.return_map and not MockWithEntities.return_none:
            return MockFirst
        if MockWithEntities.return_map_image and not MockWithEntities.return_none:
            MockFirst.return_map_image = True
            MockFirst.return_map = False
            MockFirst.return_map_image_value = args[0]
            return MockFirst
        if MockWithEntities.return_waypoint and not MockWithEntities.return_none:
            return MockAll
        else:
            return None


class MockUser:
    """Mock class for Map table."""

    email = "example.com"

    # Constructor initializing values
    def __init__(self, email):
        self.email = email

    def repr_name(self):
        """Custom representation of map."""
        return {"email": self.email}

    query = MockMapQuery


# def reset_table_class(valid_data, table):
#     """Function to set attribute of the class.
#
#     :param valid_data: dict of values with attributes as keys
#     :param table: Mock table class"""
#     for data in valid_data:
#         setattr(table, data, valid_data[data])


class TestUser(unittest.TestCase):
    """Unit testing for v1 controllers - /user."""

    tester = None

    @classmethod
    @mock.patch('sentry_sdk.init', return_value = True)
    def setUpClass(cls, mock_sentry):
        from src import app
        """Setting up the variable for app.test_client for CRUD operations."""
        cls.tester = app.test_client(cls)

    @classmethod
    def tearDownClass(cls):
        cls.tester = None

    def setUp(self):
        """Resetting the class variable to None"""
        # reset_table_class(valid_map_get_data, MockMap)
        pass

    @mock.patch("src.v1.services.user_services.Map", MockUser)
    @mock.patch("src.v1.controllers.map.send_file", return_value=True)
    @mock.patch("src.v1.services.user_services.db.session.add", return_value=True)
    @mock.patch("src.v1.services.user_services.db.session.flush", return_value=True)
    def test_login_ok(self, mock_db_flush, mock_db_add, mock_send_file):
        """Test for GET /map api route with valid map_id.

        asserts Equal with the status code 200
        asserts Equal with the valid_agent_data
        """

        response = self.tester.post("/user/v1/auth/code",
                                    json={"email": "example.com"})
        statuscode = response.status_code
        response_json = response.data.decode("utf8").replace("'", '"')
        self.assertEqual(statuscode, 200)
