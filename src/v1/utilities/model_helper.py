def copy_entity_row(model, row, *model_args):
    # Make a copy of the original object
    new_row = model(*model_args)

    # Assign the attributes of the original object to the new object
    for attr in row.__table__.columns.keys():
        setattr(new_row, attr, getattr(row, attr))

    return new_row
