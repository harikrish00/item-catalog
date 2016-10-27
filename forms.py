from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import Required

class CatalogForm(Form):
    name = StringField('Name:',validators=[Required()])
    submit = SubmitField('Submit')

class ItemForm(Form):
    name = StringField('Name:', validators=[Required()])
    description = TextAreaField('Description:')
    price = StringField('Price:',validators=[Required()])
    submit = SubmitField('Submit')
