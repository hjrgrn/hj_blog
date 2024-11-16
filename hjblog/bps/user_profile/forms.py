from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, Regexp, ValidationError

from hjblog.db import get_db

DATA_REQUIRED = "This field is required."


class ChangeName(FlaskForm):
    def validate_username(self, to_validate):
        db = get_db()
        name = db.execute(
            "SELECT id FROM users WHERE (username = ?)", (to_validate.data,)
        ).fetchone()
        if name:
            raise ValidationError(
                f"Username {to_validate.data} has already been taken!"
            )

    username = StringField(
        label="Username",
        validators=[
            Length(
                max=59, min=4, message="This field mut be between 4 and 59 characters."
            ),
            DataRequired(message=DATA_REQUIRED),
        ],
    )

    submit = SubmitField()

class ChangeCity(FlaskForm):
    city = StringField(
        label="City",
        validators=[
            Length(
                min=1,
                max=169,
                message="The city name needs to be in between 1 and 169 characters.",
            ),
            # TODO: we need to refine this, include wierd char like Å
            Regexp(regex=r"[a-zA-Z\s]{1,169}", message="Unsupported characters."),
            Optional()
        ],
    )

    submit = SubmitField()


class ChangeEmail(FlaskForm):
    def validate_email(self, to_validate):
        db = get_db()
        name = db.execute(
            "SELECT id FROM users WHERE (email = ?)", (to_validate.data,)
        ).fetchone()
        if name:
            raise ValidationError(f"Email {to_validate.data} has already been taken!")

    email = StringField(
        label="Email",
        validators=[
            Length(
                max=200,
                min=7,
                message="This field mut be between 7 and 200 characters.",
            ),
            DataRequired(message=DATA_REQUIRED),
        ],
    )

    submit = SubmitField()


class ChangePassword(FlaskForm):
    password = PasswordField(
        label="Password",
        validators=[
            Length(
                max=200,
                min=3,
                message="This field mut be between 3 and 200 characters.",
            ),
            DataRequired(message=DATA_REQUIRED),
        ],
    )

    confirm = PasswordField(
        label="Confirm Password",
        validators=[
            Length(
                max=200,
                min=3,
                message="This field mut be between 3 and 200 characters.",
            ),
            EqualTo("password", message="You typed in two different passwords."),
            DataRequired(message=DATA_REQUIRED),
        ],
    )

    submit = SubmitField()
