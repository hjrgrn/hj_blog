from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import Length, DataRequired, Regexp


class NewPost(FlaskForm):

    title = StringField(
        label="Title",
        validators=[
            Length(
                min=1, max=59, message="Title has to be less the 59 characters long."
            ),
            DataRequired(message="Title field is required."),
        ],
    )
    content = TextAreaField(
        label="Content",
        validators=[
            Length(
                min=1,
                max=1999,
                message="The post should be less then 2000 characters long.",
            ),
            DataRequired(message="Content field is required."),
        ],
    )
    submit = SubmitField(label="Post")


class CommentPost(FlaskForm):

    content = TextAreaField(
        label="Content",
        validators=[
            Length(
                min=1, max=399, message="The comment has to be less the 400 characters."
            ),
            DataRequired(message="Content field is required."),
        ],
    )
    submit = SubmitField(label="Comment")


class QueryMeteoAPI(FlaskForm):

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
            DataRequired(message="You need to provide a city name."),
        ],
    )
    latitude = StringField(
        label="Latitude",
        validators=[
            Regexp(
                regex=r"(^[-]{0,1}[0-9]{1,2}\.[0-9]{1,6}$)|(^[0]{0}$)",
                message="You need to provide a negative or positive float in the Latitude field",
            ),
        ],
    )
    longitude = StringField(
        label="Longitude",
        validators=[
            Regexp(
                regex=r"(^[0-9]{1,3}\.[0-9]{1,6}$)|(^[0]{0}$)",
                message="You need to provide a positive float in the Longitude field",
            ),
        ],
    )
    submit = SubmitField(label="Query")
