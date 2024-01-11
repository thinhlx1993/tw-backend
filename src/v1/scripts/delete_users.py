from src import db
from src.services import user_services

new_teams_owner = "bb34fc4d-8d63-4c38-b41d-71a314d7cb3a"
users_to_be_deleted = ["user1@gmail.com", "user2@gmail.com",
                       "c1104dc4-98b3-40f4-bd2d-451453a1467a", 
                       "bb34fc4d-8d63-4c38-b41d-71a314d9cb3a",
                       "user3@gmail.com", "user4@gmail.com"]

for user in users_to_be_deleted:
    user = user.strip()

    # Check if user provided is email or user_id, then set user_id,
    # if user not found then skip
    if '@' in user:
        user_details = user_services.check_user_exists(username=user)
        if not user_details:
            print(f"User {user} not found")
            continue
        user_id = str(user_details.user_id)
    else:
        user_details = user_services.check_user_exists(user_id=user)
        if not user_details:
            print(f"User {user} not found")
            continue
        user_id = user

    # Delete user
    try:
        status, data = user_services.delete_user(
            user_id, new_teams_owner)
        if not status:
            print(f"User deletion failed {data['Message']}")
        else:
            db.session.commit()
            print(f"User {user_id} has been deleted")
    except Exception as err:
        print("Failed to delete user " + str(err))

print('finished')
