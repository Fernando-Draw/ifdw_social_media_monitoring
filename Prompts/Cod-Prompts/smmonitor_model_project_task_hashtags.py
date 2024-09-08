Nombre de archvio:
smmonitor_model_project_task_hashtags.py
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from random import randint

class SmmonitorProjectTaskHashtags(models.Model):

    _name = 'project.task.hashtags.smmonitor'
    _description = 'Hashtags de Tareas de Social Media Monitoring'
    
    name = fields.Char('Hashtag', required=True, store=True, size=300)
    color = fields.Integer(string='Color', default=lambda self: randint(1, 11),
                           help="Color asociado a este hashtag.")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Un hashtag con el mismo nombre ya existe."),
    ]

    @api.constrains('name')
    def _check_hashtag_length(self):
        for record in self:
            if len(record.name) > 300:
                raise exceptions.ValidationError("El hashtag no puede tener más de 300 caracteres.")

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if 'smmonitor_hashtag_ids' in self.env.context:
            hashtag_ids = self._name_search('')
            domain = ['&', ('id', 'in', hashtag_ids), ('id', 'in', self.env.context['smmonitor_hashtag_ids'])]
            return self.arrange_hashtag_list_by_id(super().search_read(domain=domain, fields=fields, offset=offset, limit=limit), hashtag_ids)
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
    
    #def arrange_hashtag_list_by_id(self, hashtag_list, hashtag_ids):
    # Ordena la lista de hashtags según su identificador
    #return sorted(hashtag_list, key=lambda x: x['id'])