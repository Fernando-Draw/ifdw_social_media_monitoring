from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from random import randint
import re

class SmmonitorProjectTaskHashtags(models.Model):

    _name = 'project.task.hashtags.smmonitor'
    _description = 'Hashtags de Tareas de Social Media Monitoring'
    
    name = fields.Char('Hashtag', required=True, store=True, size=300,
                       help="""Escribe el hashtag tal como quieres que se vea en las RR.SS. sin el símbolo de '#', se admiten tildes,
                       no se admiten espacios, no se admiten puntuaciones, no se admiten símbolos.""")
    color = fields.Integer(string='Color', default=lambda self: randint(1, 11),
                           help="Puedes cambiar el color asociado a este hashtag.")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Un hashtag con el mismo nombre ya existe."),
    ]

    @api.constrains('name')
    def check_hashtag(self):
        for record in self:
            if len(record.name) > 300:
                raise ValidationError("El hashtag no puede tener más de 300 caracteres.")
            if ' ' in record.name:
                raise ValidationError("El hashtag no puede contener espacios.")
            if not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚüÜñÑ]+$', record.name):
                raise ValidationError("El hashtag solo puede contener letras (con o sin acentos), números y la letra 'ñ'.")

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