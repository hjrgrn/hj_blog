from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    Regexp,
    ValidationError,
)
from hjblog.db import get_db


class RegisterForm(FlaskForm):
    """RegisterForm"""

    def validate_username(self, user_to_validate: StringField):
        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE (username = ?)", (user_to_validate.data,)
        ).fetchone()
        if user:
            raise ValidationError(
                f"The username {user_to_validate.data} has already been taken!"
            )

    def validate_email(self, email_to_validate: StringField):
        db = get_db()
        email = db.execute(
            "SELECT id FROM users WHERE (email = ?)", (email_to_validate.data,)
        ).fetchone()
        if email:
            raise ValidationError(
                f"The email {email_to_validate.data} is already registered."
            )

    username = StringField(
        label="Username",
        validators=[
            Length(
                min=3,
                max=60,
                message="Username has to be more then 3 characters long and less then 61 characters long.",
            ),
            DataRequired(message="Username is required."),
        ],
    )
    email = StringField(
        label="Email",
        validators=[
            Email(message="Your email is invalid."),
            Length(
                min=4,
                max=200,
                message="Your email has to be less the 201 characters and more then 4 characters long.",
            ),
            DataRequired(message="Email is required."),
        ],
    )
    password = PasswordField(
        label="Password",
        validators=[
            Length(
                min=3,
                max=200,
                message="Your password has to be less the 201 characters and more then 3 characters long.",
            ),
            DataRequired(message="Password is required."),
        ],
    )
    confirm_pass = PasswordField(
        label="Confirm Password",
        validators=[
            EqualTo("password", message="You typed in two different passwords."),
            Length(
                min=3,
                max=200,
                message="Your password has to be less the 201 characters and more then 3 characters long.",
            ),
            DataRequired(message="Insert your password again."),
        ],
    )
    city = StringField(
        label="City(optional)",
        validators=[
            Length(
                min=1,
                max=169,
                message="Longest city name has to be shorter then 169 characters.",
            ),
            Regexp(regex=r"[a-zA-Z\s]{1,169}", message="Unsupported characters."),
            Optional(),
        ],
    )
    submit = SubmitField(label="Register")


class LogInForm(FlaskForm):
    username = StringField(
        label="Username",
        validators=[
            Length(
                min=3,
                max=60,
                message="Username has to be more then 3 characters long and less then 61 characters long.",
            ),
            DataRequired(message="Username is required."),
        ],
    )
    submit = SubmitField(label="Sign in")


class VerifyForm(FlaskForm):
    password = PasswordField(
        label="Password",
        validators=[
            DataRequired(message="This field is required."),
            Length(
                max=200,
                min=3,
                message="This field mut be between 3 and 200 characters.",
            ),
        ],
    )

    submit = SubmitField()


class VerifyForm2FA(FlaskForm):
    password = PasswordField(
        label="Password",
        validators=[
            DataRequired(message="This field is required."),
            Length(
                max=200,
                min=3,
                message="This field mut be between 3 and 200 characters.",
            ),
        ],
    )

    totp = StringField(
        label="Token",
        validators=[
            DataRequired(message="This field is required."),
            Length(max=6, min=6, message="The totp needs to be 6 characters long."),
        ],
    )

    submit = SubmitField()
