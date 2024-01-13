"""Services for teams."""

import logging
import re 

from sentry_sdk import capture_exception
from sqlalchemy import func, text, and_
from sqlalchemy.exc import MultipleResultsFound

from src import db
from src.models.teams import Teams
from src.models.user_teams_mapping import UserTeamsMapping
from src.services import user_services, migration_services


# Create module log
_logger = logging.getLogger(__name__)

def create_teams(org_name, owner=None):
    """Create teams.

    :param str org_name: Name of teams
    :return bool, UUID: True, teams_id
    """
    try:
        new_org = Teams(teams_name=org_name, teams_code=get_teams_code_from_name(org_name), owner=owner)
        db.session.add(new_org)
        db.session.flush()
        return True, str(new_org.teams_id), None
    except MultipleResultsFound as err:
        _logger.exception(err)
        return False, None, "Duplicate teams code"
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def create_schema(org_id):
    """Create schema from teams id.

    :param str org_id: Teams ID
    :return None:
    """
    db.session.execute(
        'CREATE SCHEMA IF NOT EXISTS "cs_' + str(org_id) + '"')


def drop_schema(org_id):
    """Drop schema by teams id.

    :param str org_id: Teams ID
    :return None:
    """
    db.session.execute(
        'DROP SCHEMA IF EXISTS "cs_' + str(org_id) + '" CASCADE ')


def get_teams(teams_id):
    """
    To fetch an teams with the given id

    :param str teams_id: id to check in DB

    :return: Teams row from table
    """
    try:
        teams = (Teams.query.filter(
            Teams.teams_id == teams_id).first())
        return teams
    except Exception as err:
        capture_exception(err)
        return None


def check_is_default_org(teams_id, user_id):
    mapping = UserTeamsMapping.query.filter_by(teams_id=teams_id, user_id=user_id, is_default=True).first()
    return mapping


def update_query(query, model, filters=None, throw_error=True):
    """
    Update query based on filters and model
    """
    if filters:
        for key, value in filters.items():
            field = getattr(model, key, None)
            if field:
                if type(value) == str:
                    if value == "null":
                        query = query.filter(field.is_(None))
                    else:
                        value = [value.lower()]
                        if key == "organization_code":
                            query = query.filter(func.lower(field).in_(value))
                        else:
                            query = query.filter(field.in_(value))
            elif throw_error:
                return False, {"Message": "Invalid key sent for filtering"}
    return True, query


def fetch_teams(
    page=0, per_page=20, sort_by="teams_name",
    sort_order="asc", filters=None):
    """Fetch teams data based on sort and filters.

    :param int page: Page number to fetch
    :param int per_page: Page size of result
    :param str sort_by: Attribute to sort results by
    :param str sort_order: 'asc' to sort ascending and 'desc' for descending
    :param dict filters: Filters for fetching results. eg: {"owner": "xyz"}
    """
    # Check if sort_by key is valid
    column = getattr(Teams, sort_by, None)
    if not column:
        return False, {"Message": "Invalid sort_by Key provided"}
    sorting_order = sort_by + " " + sort_order
    try:
        query = Teams.query
        # Apply filters
        status, query = update_query(
            query, Teams, filters=filters)
        if not status:
            return False, query
        # Apply sorting
        if sorting_order:
            query = query.order_by(text(sorting_order))
        # Apply pagination
        if per_page:
            query = query.limit(per_page)
        if page:
            query = query.offset(per_page*(page-1))
        result = query.all()
        # Formatting the result
        formatted_result = format_result(result)
        db.session.flush()
    except Exception as err:
        _logger.exception(err)
        db.session.rollback()
        capture_exception(err)
        return False, {"Message": str(err)}
    return True, formatted_result


def update_teams(data):
    """Update a row in teams table.

    :param update_dict: Dictionary with the following fields:
        uuid teams_id: Unique identifier for teams
        str teams_name: Teams name
        uuid owner: Unique identifier for owner of teams
        datetime created_at: Teams creation time
        datetime updated_at: Organiztion updation time
        boolean is_disabled: Flag for disabled teams
        boolean is_deleted: Flag for deleted teams
    :return bool: True if succesful
    """
    try:
        # Fetch row with teams_id
        teams = Teams.query.filter(
            Teams.teams_id == data["teams_id"]).first()
        if not teams:
            raise Exception('Teams not found')
        # Each value in 'data' is updated in the row, unless they're None
        for attribute in data:
            if data[attribute] is not None:
                setattr(teams, attribute, data[attribute])
        db.session.flush()
        return True, teams.repr_name()
    except Exception as ex:
        capture_exception(ex)
        db.session.rollback()
        raise ex


def update_teams_owner(org_id, cur_user_id, new_user_id):
    """Update ownership of an teams and add the
    neccesary user_teams mapping.

    :param str org_id: teams_id to change
    :param str curr_user_id: user_id of the current owner
    :param str new_user_id: user_id of the new owner
    :return bool: True if succesful
    """
    try:
        teams = get_teams(org_id)
        if teams:
            if str(teams.owner) == cur_user_id:
                # Change owner column in teams row
                teams = Teams.query.filter(
                    Teams.teams_id == org_id).first()
                setattr(teams, 'owner', new_user_id)
                db.session.flush()
                # Update mapping to reflect the owner change
                user_services.create_user_teams_mapping(
                    new_user_id, str(teams.teams_id), False)
            else:
                raise Exception("User is not owner of teams")
        else:
            raise Exception("Teams not found")
    except Exception as err:
        _logger.exception(err)
        db.session.rollback()
        capture_exception(err)
        raise Exception(str(err))
    return True


def get_user_org_list(user_id):
    """
    Get list of teamss for user
    :param user_id: Unique Identifier for user
    :return org_list: List of teamss corresponding to user
    """
    try:
        out_data = {}
        # This only contains teams_ids
        org_list = UserTeamsMapping.query.filter_by(
            user_id=user_id).all()
        org_details = []
        # Getting complete details for each org
        for row in org_list:
            status, details = fetch_teams(
                filters={
                    "teams_id": str(row.teams_id)
                })
            org_details.extend(details)
        out_data['org_list'] = org_details
        return out_data
    except Exception as err:
        _logger.exception(err)
        capture_exception(err)
        return None


def set_user_default_teams(user_id, teams_id):
    """
    Set default teamss for user
    @Author Thinh Le
    :param user_id: Unique Identifier for user
    :param teams_id: Unique Identifier for teams
    """
    try:
        # Query exist mapping teams and user
        exist_mapping = UserTeamsMapping.query.filter_by(user_id=user_id, teams_id=teams_id).first()
        if exist_mapping:
            # exist mapping, set default teams
            exist_mapping.is_default = True
            db.session.add(exist_mapping)
            db.session.flush()
            return True
        # add mapping for default
        new_mapping = UserTeamsMapping(user_id=user_id, teams_id=teams_id, is_default=True)
        db.session.add(new_mapping)
        db.session.flush()
        return True
    except Exception as err:
        _logger.exception(err)
        db.session.rollback()
        capture_exception(err)
        return False


def format_result(result):
    """Formats result for frontend.

    :param list result: List of results fetched from DB
    :return list formatted_result: Formatted list of results
    """
    formatted_result = []
    for row in result:
        formatted_row = {}
        formatted_row['teams_id'] = str(row.teams_id)
        formatted_row['teams_name'] = str(row.teams_name)
        formatted_row['teams_code'] = str(row.teams_code).lower()
        formatted_row['owner'] = str(row.owner)
        formatted_row['created_at'] = str(row.created_at)
        formatted_row['updated_at'] = str(row.updated_at)
        formatted_row['is_disabled'] = row.is_disabled
        formatted_row['is_deleted'] = row.is_deleted
        formatted_result.append(formatted_row)

    return formatted_result


def get_teams_code_from_name(org_name):

    org_code = re.sub(r"[^\w\s]", '_', org_name)
    #Remove whitespaces with underscore
    org_code = re.sub(r"\s+", '_', org_code)

    query = Teams.query.filter(func.lower(Teams.teams_code) == str(org_code).lower()).scalar()
    if query is None or query == 0:
        return org_code
    
    seq = 0
    is_valid_code = False
    while is_valid_code == False:
        seq += 1
        temp_code = org_code + "_" + str(seq)
        query = Teams.query.filter(func.lower(Teams.teams_code) == str(temp_code).lower()).scalar()
        if query is None or query == 0:
            is_valid_code = True
            org_code = temp_code
    org_code = temp_code
    return org_code

def get_teams_id_from_code(org_code):   
    try:
        teams = db.session.query(Teams).filter(func.lower(Teams.teams_code) == str(org_code).lower()).first()
        return teams.teams_id
    except Exception as err:
        _logger.exception(err)
        capture_exception(err)
        return None

def search_user_org_list(
        user_id, page=0, per_page=20, sort_by="teams_id",
        sort_order="asc", filters=None):
    """Used to filter on list of teamss user belongs to"""
    column = getattr(Teams, sort_by, None)
    if not column:
        return False, {"Message": "Invalid sort_by Key provided"}
    sorting_order = sort_by + " " + sort_order
    try:
        query = UserTeamsMapping.query.join(Teams,
                Teams.teams_id == UserTeamsMapping.teams_id).filter(
                UserTeamsMapping.user_id == user_id).with_entities(
                Teams.teams_id, Teams.teams_name, Teams.created_at,
                Teams.updated_at, Teams.teams_code, Teams.is_deleted,
                Teams.is_disabled, Teams.owner)
        # Apply filters
        status, query = update_query(
            query, Teams, filters=filters)
        if not status:
            return False, query
        # Apply sorting
        if sorting_order:
            query = query.order_by(text(sorting_order))
        # Apply pagination
        if per_page:
            query = query.limit(per_page)
        if page:
            query = query.offset(per_page*(page-1))
        result = query.all()
        # Formatting the result
        formatted_result = format_user_org_list_result(result)
        db.session.flush()
    except Exception as err:
        _logger.exception(err)
        db.session.rollback()
        capture_exception(err)
        return False, {"Message": str(err)}
    return True, formatted_result


def format_user_org_list_result(result):
    """Used to format the result of user teams mapping query"""
    formatted_result = []
    for row in result:
        formatted_row = {}
        formatted_row['teams_id'] = str(row.teams_id)
        formatted_row['teams_name'] = str(row.teams_name)
        formatted_row['teams_code'] = str(row.teams_code).lower()
        formatted_row['owner'] = str(row.owner)
        formatted_row['created_at'] = row.created_at.strftime("%d-%m-%Y %H:%M") if row.created_at else None
        formatted_row['updated_at'] = row.updated_at.strftime("%d-%m-%Y %H:%M") if row.updated_at else None
        formatted_row['is_disabled'] = row.is_disabled
        formatted_row['is_deleted'] = row.is_deleted
        formatted_result.append(formatted_row)

    return formatted_result


def rollback_teams_creation(teams_id, user_id):
    """Since organization creating error, let remove resources that created before"""
    try:
        user_services.delete_user_roles_mapping(user_id, teams_id)
        user_services.delete_user_teams_mapping(user_id, teams_id)
        # remove schema
        delete_teams(teams_id)
        drop_schema(teams_id)
        db.session.commit()
    except Exception as ex:
        _logger.exception(ex)


def delete_teams(teams_id):
    """
    Delete user teams

    :param teams_id: Unique identifier for teams

    :return bool: True if successful
    """
    try:
        (Teams.query.filter(
            Teams.teams_id == teams_id)
         .delete())
        db.session.flush()
        return True
    except:
        db.session.rollback()
        raise
