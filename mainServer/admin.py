from django.contrib import admin
from mainServer import models
from django.db.models.base import ModelBase

abstracts = {"Status"}
for model_name in dir(models):
    model = getattr(models, model_name)
    if (model_name not in abstracts) and isinstance(model, ModelBase):
        admin.site.register(model)


