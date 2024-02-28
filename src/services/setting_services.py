from src import db, app
from src.models import Settings


def get_settings_by_user_device(user_id, device_id):
    """Retrieve settings for a specific user and device."""
    settings_record = (
        db.session.query(Settings)
        .filter_by(user_id=user_id, device_id=device_id)
        .first()
    )
    return settings_record.repr_name() if settings_record else None


def create_or_update_settings(user_id, device_id, settings_data):
    """Create or update settings for a specific user and device."""
    settings_record = Settings.query.filter_by(
        user_id=user_id, device_id=device_id
    ).first()

    if settings_record:
        if "hma_access_token" in settings_data:
            del settings_data["hma_access_token"]
        settings_record.settings = settings_data
    else:
        settings_record = Settings(
            user_id=user_id, device_id=device_id, settings=settings_data
        )
        db.session.add(settings_record)

    db.session.flush()
    return settings_record.repr_name()


def delete_settings(user_id, device_id):
    """Delete settings for a specific user and device."""
    settings_record = Settings.query.filter_by(
        user_id=user_id, device_id=device_id
    ).first()
    if settings_record:
        db.session.delete(settings_record)
        db.session.commit()
        return True
    return False
